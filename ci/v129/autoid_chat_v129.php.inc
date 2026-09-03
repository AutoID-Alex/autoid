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
            'app_version'=>'1.0.29',
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
        return new WP_Error('autoid_support_ai_adapter_missing','AutoID Support Center este detectat, dar handler-ul său AI nu a putut fi apelat din aplicația mobilă.',['status'=>503,'support_center'=>$context['support_center']]);
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
                'User-Agent'=>'AutoID-Mobile-WordPress/1.1.21',
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
