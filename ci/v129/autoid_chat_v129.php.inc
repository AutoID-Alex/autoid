    public static function ai_token_v129(WP_REST_Request $r) {
        $device_id=self::chat_device_id_v129($r);
        if(is_wp_error($device_id)) return $device_id;

        $limited=self::chat_rate_limit_v129('issue',$device_id,30,600);
        if(is_wp_error($limited)) return $limited;

        $now=time();
        $payload=[
            'v'=>1,
            'purpose'=>'autoid-mobile-chat',
            'device'=>hash('sha256',$device_id),
            'iat'=>$now,
            'exp'=>$now+600,
            'nonce'=>wp_generate_password(16,false,false),
        ];
        $body=self::b64url_encode(wp_json_encode($payload));
        $signature=self::b64url_encode(hash_hmac('sha256',$body,self::chat_token_secret_v129(),true));

        return rest_ensure_response([
            'token'=>$body.'.'.$signature,
            'expires_at'=>$payload['exp'],
            'expires_in'=>600,
        ]);
    }

    public static function ai_chat(WP_REST_Request $r) {
        $device_id=self::chat_device_id_v129($r);
        if(is_wp_error($device_id)) return $device_id;

        $authorized=self::verify_chat_token_v129($r,$device_id);
        if(is_wp_error($authorized)) return $authorized;

        $limited=self::chat_rate_limit_v129('chat',$device_id,40,300);
        if(is_wp_error($limited)) return $limited;

        $message=trim(sanitize_textarea_field((string)$r->get_param('message')));
        if($message==='') return new WP_Error('autoid_ai_empty','Mesaj gol.',['status'=>400]);
        $message_length=function_exists('mb_strlen') ? mb_strlen($message) : strlen($message);
        if($message_length>2500) return new WP_Error('autoid_ai_too_long','Mesajul este prea lung.',['status'=>400]);

        $product_id=absint($r->get_param('product_id'));
        $context=[
            'channel'=>'android-app',
            'app_version'=>'1.0.30',
            'device'=>substr(hash('sha256',$device_id),0,16),
            'product_id'=>$product_id,
            'support_center'=>self::support_center_info(),
        ];

        $answer=self::support_app_api_v129($message,$product_id,$context);
        if($answer!=='') return rest_ensure_response(['answer'=>$answer,'source'=>'autoid-support-api','support_center'=>$context['support_center']]);

        foreach(['autoid_support_center_mobile_ai','autoid_support_ai_chat','autoid_mobile_ai_chat'] as $hook){
            $filtered=apply_filters($hook,null,$message,$context);
            $answer=self::extract_ai_answer($filtered);
            if($answer!=='') return rest_ensure_response(['answer'=>$answer,'source'=>'autoid-support-center','hook'=>$hook,'support_center'=>$context['support_center']]);
        }
        $answer=self::support_center_rest_ai($message,$product_id,$context);
        if($answer!=='') return rest_ensure_response(['answer'=>$answer,'source'=>'autoid-support-center-rest','support_center'=>$context['support_center']]);
        $answer=self::support_center_ajax_ai($message,$product_id,$context);
        if($answer!=='') return rest_ensure_response(['answer'=>$answer,'source'=>'autoid-support-center-ajax','support_center'=>$context['support_center']]);

        // Compatibility bridge for Support Center builds whose real handler is named
        // ask/query/message/conversation (or lives in a shared AI core file).
        $fallback=self::support_center_compat_v130($message,$product_id,$context);
        if(is_array($fallback) && trim((string)($fallback['answer']??''))!=='') {
            return rest_ensure_response([
                'answer'=>trim((string)$fallback['answer']),
                'source'=>(string)($fallback['source']??'autoid-support-center-compat'),
                'handler'=>(string)($fallback['handler']??''),
                'support_center'=>$context['support_center'],
            ]);
        }

        return new WP_Error('autoid_support_ai_adapter_missing','AutoID Support Center este detectat, dar handler-ul său AI nu a putut fi apelat din aplicația mobilă.',['status'=>503,'support_center'=>$context['support_center'],'bridge'=>'compat-v130']);
    }

    private static function chat_device_id_v129(WP_REST_Request $r) {
        $device_id=trim((string)$r->get_param('device_id'));
        if($device_id==='' || strlen($device_id)>128 || !preg_match('/^[A-Za-z0-9._:-]{16,128}$/',$device_id)) {
            return new WP_Error('autoid_chat_device_invalid','Identificatorul sesiunii de chat este invalid.',['status'=>400]);
        }
        return $device_id;
    }

    private static function chat_token_secret_v129() {
        return hash('sha256',wp_salt('auth').'|autoid-mobile-chat-v1');
    }

    private static function verify_chat_token_v129(WP_REST_Request $r,$device_id) {
        $header=trim((string)$r->get_header('authorization'));
        if(!preg_match('/^Bearer\s+(.+)$/i',$header,$match)) {
            return new WP_Error('autoid_chat_token_missing','Sesiunea de chat lipsește.',['status'=>401]);
        }
        $parts=explode('.',$match[1]);
        if(count($parts)!==2) return new WP_Error('autoid_chat_token_invalid','Sesiunea de chat este invalidă.',['status'=>401]);

        [$body,$signature]=$parts;
        $expected=self::b64url_encode(hash_hmac('sha256',$body,self::chat_token_secret_v129(),true));
        if(!hash_equals($expected,$signature)) return new WP_Error('autoid_chat_token_invalid','Sesiunea de chat este invalidă.',['status'=>401]);

        $payload=json_decode(self::b64url_decode($body),true);
        $valid=is_array($payload)
            && ($payload['purpose']??'')==='autoid-mobile-chat'
            && (int)($payload['iat']??0)<=time()+30
            && (int)($payload['exp']??0)>=time()
            && hash_equals((string)($payload['device']??''),hash('sha256',$device_id));
        if(!$valid) return new WP_Error('autoid_chat_token_expired','Sesiunea de chat a expirat.',['status'=>401]);
        return true;
    }

    private static function chat_rate_limit_v129($bucket,$device_id,$limit,$window) {
        $ip=(string)($_SERVER['REMOTE_ADDR']??'unknown');
        $key='autoid_chat_'.sanitize_key($bucket).'_'.md5(hash('sha256',$device_id.'|'.$ip));
        $now=time();
        $state=get_transient($key);
        if(!is_array($state) || (int)($state['reset']??0)<=$now) $state=['count'=>0,'reset'=>$now+$window];
        if((int)$state['count']>=$limit) {
            return new WP_Error('autoid_chat_rate_limited','Ai trimis prea multe solicitări. Încearcă din nou în câteva minute.',['status'=>429,'retry_after'=>max(1,(int)$state['reset']-$now)]);
        }
        $state['count']=(int)$state['count']+1;
        set_transient($key,$state,max(1,(int)$state['reset']-$now));
        return true;
    }

    private static function support_center_compat_v130($message,$product_id,$context) {
        $answer=self::support_center_filter_scan_v130($message,$context);
        if($answer!=='') return ['answer'=>$answer,'source'=>'autoid-support-center-filter-scan','handler'=>'dynamic-filter'];

        $rest=self::support_center_rest_scan_v130($message,$product_id,$context);
        if(is_array($rest) && trim((string)($rest['answer']??''))!=='') return $rest;

        $ajax=self::support_center_ajax_scan_v130($message,$product_id,$context);
        if(is_array($ajax) && trim((string)($ajax['answer']??''))!=='') return $ajax;
        return [];
    }

    private static function support_center_intent_name_v130($name) {
        $low=strtolower((string)$name);
        foreach(['chat','assistant','ask','query','message','conversation','prompt','answer','respond','help'] as $token) {
            if(strpos($low,$token)!==false) return true;
        }
        return (bool)preg_match('~(^|[\\/_\\-.])ai([\\/_\\-.]|$)~',$low);
    }

    private static function support_center_named_v130($name) {
        $low=strtolower((string)$name);
        return (strpos($low,'autoid')!==false || strpos($low,'support')!==false) && self::support_center_intent_name_v130($low);
    }

    private static function support_center_callback_label_v130($callback) {
        if(is_array($callback) && count($callback)>=2) {
            $owner=is_object($callback[0])?get_class($callback[0]):(string)$callback[0];
            return $owner.'::'.(string)$callback[1];
        }
        if(is_string($callback)) return $callback;
        return '';
    }

    private static function support_center_callback_owned_v130($callback) {
        try {
            if(is_array($callback) && count($callback)>=2) $ref=new ReflectionMethod($callback[0],$callback[1]);
            elseif(is_string($callback) && function_exists($callback)) $ref=new ReflectionFunction($callback);
            elseif($callback instanceof Closure) $ref=new ReflectionFunction($callback);
            else return false;

            $file=wp_normalize_path((string)$ref->getFileName());
            if($file==='') return false;
            $info=self::support_center_info();
            $plugin_file=trim((string)($info['file']??''));
            if($plugin_file!=='') {
                $target=wp_normalize_path(WP_PLUGIN_DIR.'/'.$plugin_file);
                if($file===$target) return true;
                $dir=wp_normalize_path(dirname($target));
                $plugin_root=wp_normalize_path(WP_PLUGIN_DIR);
                if($dir!=='' && $dir!=='.' && $dir!==$plugin_root && strpos($file,trailingslashit($dir))===0) return true;
            }
            $low=strtolower($file);
            return strpos($low,'autoid')!==false && strpos($low,'support')!==false;
        } catch(Throwable $e) {
            return false;
        }
    }

    private static function support_center_filter_scan_v130($message,$context) {
        global $wp_filter;
        foreach(array_keys((array)$wp_filter) as $tag) {
            if(strpos((string)$tag,'wp_ajax_')===0) continue;
            if(!self::support_center_named_v130($tag)) continue;
            if(in_array($tag,['autoid_support_center_mobile_ai','autoid_support_ai_chat','autoid_mobile_ai_chat'],true)) continue;
            $hook=$wp_filter[$tag]??null;
            if(!$hook || !isset($hook->callbacks) || !is_array($hook->callbacks)) continue;
            $owned=false;
            foreach((array)$hook->callbacks as $callbacks) {
                foreach((array)$callbacks as $cb) {
                    if(self::support_center_callback_owned_v130($cb['function']??null)) {$owned=true;break 2;}
                }
            }
            if(!$owned) continue;
            try {
                $filtered=apply_filters($tag,null,$message,$context);
                $answer=self::extract_ai_answer($filtered);
                if($answer!=='') return $answer;
            } catch(Throwable $e) {}
        }
        return '';
    }

    private static function support_center_rest_scan_v130($message,$product_id,$context) {
        $routes=rest_get_server()->get_routes();
        $own='/'.trim(self::NS,'/').'/';
        foreach($routes as $route=>$handlers) {
            if(strpos((string)$route,$own)===0) continue;
            foreach((array)$handlers as $handler) {
                $cb=$handler['callback']??null;
                if(!$cb) continue;
                $label=self::support_center_callback_label_v130($cb);
                $owned=self::support_center_callback_owned_v130($cb);
                $candidate=self::support_center_named_v130($route) || ($owned && (self::support_center_intent_name_v130($route) || self::support_center_intent_name_v130($label)));
                if(!$candidate) continue;

                $payload=[
                    'message'=>$message,'question'=>$message,'query'=>$message,'prompt'=>$message,
                    'context'=>$context,'channel'=>'android-app','product_id'=>$product_id ?: null,
                ];
                try {
                    $req=new WP_REST_Request('POST',$route);
                    foreach($payload as $key=>$value) $req->set_param($key,$value);
                    $req->set_body_params($payload);
                    $req->set_header('content-type','application/json');
                    $req->set_header('accept','application/json');
                    $req->set_header('x-wp-nonce',wp_create_nonce('wp_rest'));
                    $req->set_body(wp_json_encode($payload));
                    $resp=rest_do_request($req);
                    if(is_wp_error($resp) || !is_object($resp) || !method_exists($resp,'is_error') || $resp->is_error()) continue;
                    $answer=self::extract_ai_answer($resp->get_data());
                    if($answer!=='') return ['answer'=>$answer,'source'=>'autoid-support-center-rest-compat','handler'=>(string)$route];
                } catch(Throwable $e) {}
            }
        }
        return [];
    }

    private static function support_center_ajax_scan_v130($message,$product_id,$context) {
        global $wp_filter;
        $actions=[];
        foreach(array_keys((array)$wp_filter) as $tag) {
            if(strpos((string)$tag,'wp_ajax_')!==0) continue;
            $action=preg_replace('/^wp_ajax_(nopriv_)?/','',(string)$tag);
            if($action==='') continue;
            $hook=$wp_filter[$tag]??null;
            if(!$hook || !isset($hook->callbacks) || !is_array($hook->callbacks)) continue;
            $owned=false;$intent_callback=false;
            foreach((array)$hook->callbacks as $callbacks) {
                foreach((array)$callbacks as $cb) {
                    $fn=$cb['function']??null;
                    if(self::support_center_callback_owned_v130($fn)) $owned=true;
                    if(self::support_center_intent_name_v130(self::support_center_callback_label_v130($fn))) $intent_callback=true;
                }
            }
            if(!self::support_center_named_v130($action) && !($owned && ($intent_callback || self::support_center_intent_name_v130($action)))) continue;
            $actions[$action]=true;
        }

        foreach(array_slice(array_keys($actions),0,8) as $action) {
            $nonce=wp_create_nonce($action);
            $payload=[
                'action'=>$action,'message'=>$message,'question'=>$message,'query'=>$message,'prompt'=>$message,
                'context'=>wp_json_encode($context),'channel'=>'android-app','product_id'=>$product_id,
                'nonce'=>$nonce,'_ajax_nonce'=>$nonce,'security'=>$nonce,
            ];

            // First use the real admin-ajax execution context; many front-end handlers
            // depend on DOING_AJAX, wp_send_json() or nopriv registration.
            try {
                $response=wp_safe_remote_post(admin_url('admin-ajax.php'),[
                    'timeout'=>20,'redirection'=>1,
                    'headers'=>['Accept'=>'application/json','User-Agent'=>'AutoID-Mobile-WordPress/1.1.23'],
                    'body'=>$payload,
                ]);
                if(!is_wp_error($response)) {
                    $status=(int)wp_remote_retrieve_response_code($response);
                    $body=trim((string)wp_remote_retrieve_body($response));
                    if($status>=200 && $status<300 && $body!=='' && $body!=='0' && $body!=='-1') {
                        $decoded=json_decode($body,true);
                        $answer=self::extract_ai_answer(is_array($decoded)?$decoded:$body);
                        if($answer!=='') return ['answer'=>$answer,'source'=>'autoid-support-center-ajax-loopback','handler'=>$action];
                    }
                }
            } catch(Throwable $e) {}

            // Fallback for hosts that block loopback requests.
            foreach(['wp_ajax_nopriv_'.$action,'wp_ajax_'.$action] as $tag) {
                if(!isset($wp_filter[$tag])) continue;
                $old_post=$_POST;$old_request=$_REQUEST;
                $_POST=array_merge($_POST,$payload);$_REQUEST=array_merge($_REQUEST,$payload);
                $die_filter=static function($handler){
                    return static function($message='',$title='',$args=[]){throw new RuntimeException('__AUTOID_MOBILE_WP_DIE__');};
                };
                add_filter('wp_die_handler',$die_filter,PHP_INT_MAX);
                ob_start();
                try {do_action($tag);} catch(Throwable $e) {}
                $out=trim((string)ob_get_clean());
                remove_filter('wp_die_handler',$die_filter,PHP_INT_MAX);
                $_POST=$old_post;$_REQUEST=$old_request;
                if($out==='' || $out==='0' || $out==='-1') continue;
                $decoded=json_decode($out,true);
                $answer=self::extract_ai_answer(is_array($decoded)?$decoded:$out);
                if($answer!=='') return ['answer'=>$answer,'source'=>'autoid-support-center-ajax-direct','handler'=>$action];
            }
        }
        return [];
    }

    private static function support_app_api_v129($message,$product_id,$context) {
        $endpoint=defined('AUTOID_SUPPORT_APP_ENDPOINT') ? trim((string)constant('AUTOID_SUPPORT_APP_ENDPOINT')) : trim((string)getenv('AUTOID_SUPPORT_APP_ENDPOINT'));
        $endpoint=trim((string)apply_filters('autoid_mobile_support_app_endpoint',$endpoint,$context));
        $token=defined('AUTOID_SUPPORT_APP_TOKEN') ? trim((string)constant('AUTOID_SUPPORT_APP_TOKEN')) : trim((string)getenv('AUTOID_SUPPORT_APP_TOKEN'));
        if($endpoint==='' || $token==='') return '';

        $own=rest_url(self::NS.'/ai/chat');
        if(untrailingslashit($endpoint)===untrailingslashit($own)) return '';
        if(!wp_http_validate_url($endpoint)) return '';

        $response=wp_safe_remote_post($endpoint,[
            'timeout'=>25,
            'redirection'=>2,
            'headers'=>[
                'Accept'=>'application/json',
                'Content-Type'=>'application/json',
                'Authorization'=>'Bearer '.$token,
                'X-AutoID-App-Token'=>$token,
                'User-Agent'=>'AutoID-Mobile-WordPress/1.1.23',
            ],
            'body'=>wp_json_encode([
                'message'=>$message,
                'product_id'=>$product_id ?: null,
                'context'=>$context,
                'channel'=>'android-app',
            ]),
        ]);
        if(is_wp_error($response)) return '';
        $status=(int)wp_remote_retrieve_response_code($response);
        if($status<200 || $status>=300) return '';
        $decoded=json_decode((string)wp_remote_retrieve_body($response),true);
        return self::extract_ai_answer(is_array($decoded)?$decoded:'');
    }
