    private static function support_center_v2_chat_v131($message,$product_id,$context) {
        $routes=rest_get_server()->get_routes();
        $session_route='/autoid-support/v2/chat/session';
        $chat_route='/autoid-support/v2/chat';
        $has_session=isset($routes[$session_route]);
        $has_chat=isset($routes[$chat_route]);
        if(!$has_chat) return ['answer'=>'','diagnostic'=>'SCV2_CHAT_ROUTE_MISSING','available'=>false];

        $model=self::support_center_v2_model_context_v131($message,$product_id);
        $base=array_merge([
            'channel'=>'android-app',
            'locale'=>determine_locale(),
            'message'=>$message,
            'question'=>$message,
            'query'=>$message,
            'prompt'=>$message,
            'product_id'=>$product_id ?: null,
            'context'=>$context,
        ],$model);

        $session_data=[];
        $session_id='';
        $session_token='';
        $session_nonce='';
        $diagnostic=[];

        if($has_session) {
            $session_payload=$base;
            unset($session_payload['message'],$session_payload['question'],$session_payload['query'],$session_payload['prompt']);
            $session=self::support_center_v2_rest_call_v131($session_route,$session_payload,[]);
            if(!$session['ok']) {
                $diagnostic[]='SESSION_'.$session['status'].'_'.$session['code'];
            } else {
                $session_data=is_array($session['data'])?$session['data']:[];
                $session_id=self::support_center_v2_find_scalar_v131($session_data,['session_id','conversation_id','chat_id','conversation','session','id']);
                $session_token=self::support_center_v2_find_scalar_v131($session_data,['session_token','access_token','token']);
                $session_nonce=self::support_center_v2_find_scalar_v131($session_data,['rest_nonce','nonce','csrf_token','csrf']);
                if($session_id==='') {
                    foreach(['x-autoid-session','x-session-id','x-chat-session'] as $header) {
                        $v=trim((string)($session['headers'][$header]??''));
                        if($v!=='') {$session_id=$v;break;}
                    }
                }
                $diagnostic[]=$session_id!==''?'SESSION_OK':'SESSION_OK_NO_ID';
            }
        } else {
            $diagnostic[]='SESSION_ROUTE_MISSING';
        }

        $chat_payload=$base;
        if($session_id!=='') {
            $chat_payload['session_id']=$session_id;
            $chat_payload['conversation_id']=$session_id;
            $chat_payload['chat_id']=$session_id;
            $chat_payload['session']=$session_id;
        }
        if($session_token!=='') {
            $chat_payload['session_token']=$session_token;
            $chat_payload['token']=$session_token;
        }
        if($session_nonce!=='') {
            $chat_payload['nonce']=$session_nonce;
            $chat_payload['rest_nonce']=$session_nonce;
        }
        if($session_data) $chat_payload['session_context']=$session_data;

        $headers=[];
        if($session_token!=='') $headers['authorization']='Bearer '.$session_token;
        if($session_nonce!=='') $headers['x-wp-nonce']=$session_nonce;
        if($session_id!=='') $headers['x-autoid-session']=$session_id;

        $chat=self::support_center_v2_rest_call_v131($chat_route,$chat_payload,$headers);
        if(!$chat['ok']) {
            $diagnostic[]='CHAT_'.$chat['status'].'_'.$chat['code'];
            return ['answer'=>'','diagnostic'=>implode('|',$diagnostic),'available'=>true];
        }

        $answer=self::extract_ai_answer($chat['data']);
        if($answer==='') {
            $diagnostic[]='CHAT_OK_EMPTY';
            return ['answer'=>'','diagnostic'=>implode('|',$diagnostic),'available'=>true];
        }
        return ['answer'=>$answer,'diagnostic'=>implode('|',$diagnostic),'available'=>true];
    }

    private static function support_center_v2_rest_call_v131($route,$payload,$headers=[]) {
        try {
            $req=new WP_REST_Request('POST',$route);
            foreach((array)$payload as $key=>$value) $req->set_param($key,$value);
            $req->set_body_params((array)$payload);
            $req->set_header('accept','application/json');
            $req->set_header('content-type','application/json');
            $req->set_header('x-autoid-channel','android-app');
            $req->set_header('origin',home_url('/'));
            if(empty($headers['x-wp-nonce'])) $req->set_header('x-wp-nonce',wp_create_nonce('wp_rest'));
            foreach((array)$headers as $key=>$value) if(trim((string)$value)!=='') $req->set_header($key,(string)$value);
            $req->set_body(wp_json_encode($payload));
            $resp=rest_do_request($req);
            if(is_wp_error($resp)) {
                return ['ok'=>false,'status'=>0,'code'=>sanitize_key($resp->get_error_code()),'data'=>[],'headers'=>[]];
            }
            if(!is_object($resp) || !method_exists($resp,'get_status')) return ['ok'=>false,'status'=>0,'code'=>'invalid_response','data'=>[],'headers'=>[]];
            $status=(int)$resp->get_status();
            $data=$resp->get_data();
            $response_headers=[];
            if(method_exists($resp,'get_headers')) foreach((array)$resp->get_headers() as $key=>$value) $response_headers[strtolower((string)$key)]=$value;
            $code='';
            if(is_array($data)) $code=sanitize_key((string)($data['code']??($data['error']['code']??'')));
            if($code==='') $code=$status>=200&&$status<300?'ok':'http_'.$status;
            return ['ok'=>$status>=200&&$status<300,'status'=>$status,'code'=>$code,'data'=>$data,'headers'=>$response_headers];
        } catch(Throwable $e) {
            return ['ok'=>false,'status'=>0,'code'=>'exception','data'=>[],'headers'=>[]];
        }
    }

    private static function support_center_v2_find_scalar_v131($data,$keys) {
        if(!is_array($data)) return '';
        foreach((array)$keys as $key) {
            if(array_key_exists($key,$data) && (is_string($data[$key]) || is_numeric($data[$key]))) {
                $value=trim((string)$data[$key]);
                if($value!=='') return $value;
            }
        }
        foreach($data as $value) {
            if(is_array($value)) {
                $found=self::support_center_v2_find_scalar_v131($value,$keys);
                if($found!=='') return $found;
            }
        }
        return '';
    }

    private static function support_center_v2_model_context_v131($message,$product_id) {
        $out=[];
        $term=false;
        if($product_id>0 && taxonomy_exists('product_tag')) {
            $terms=wp_get_post_terms($product_id,'product_tag');
            if(!is_wp_error($terms) && $terms) {
                $product=wc_get_product($product_id);
                $hay=strtolower(remove_accents((string)($product?$product->get_name():'')));
                foreach($terms as $candidate) {
                    $needle=strtolower(remove_accents((string)$candidate->name));
                    if($needle!=='' && strpos($hay,$needle)!==false) {$term=$candidate;break;}
                }
                if(!$term) $term=reset($terms);
            }
        }
        if(!$term && taxonomy_exists('product_tag')) {
            preg_match_all('/[A-Za-z]{1,12}[A-Za-z0-9._-]*\\d[A-Za-z0-9._-]*/u',(string)$message,$matches);
            foreach(array_unique((array)($matches[0]??[])) as $token) {
                $candidate=get_term_by('slug',sanitize_title($token),'product_tag');
                if(!$candidate) $candidate=get_term_by('name',$token,'product_tag');
                if($candidate && !is_wp_error($candidate)) {$term=$candidate;break;}
            }
        }
        if($term && !is_wp_error($term)) {
            $out['model_term_id']=(int)$term->term_id;
            $out['model_id']=(int)$term->term_id;
            $out['model_slug']=(string)$term->slug;
            $out['model']=(string)$term->name;
            $out['model_name']=(string)$term->name;
        }
        if($product_id>0) {
            $cats=wp_get_post_terms($product_id,'product_cat',['fields'=>'ids']);
            if(!is_wp_error($cats) && $cats) $out['category_id']=(int)reset($cats);
            foreach(['product_brands','product_brand','pwb-brand'] as $taxonomy) {
                if(!taxonomy_exists($taxonomy)) continue;
                $brands=wp_get_post_terms($product_id,$taxonomy,['fields'=>'ids']);
                if(!is_wp_error($brands) && $brands) {$out['brand_term_id']=(int)reset($brands);break;}
            }
        }
        return $out;
    }
