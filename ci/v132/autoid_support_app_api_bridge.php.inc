    private static function support_center_app_chat_v132($message,$product_id,$device_id,$context) {
        $route='/autoid-support/v2/app/chat';
        $routes=rest_get_server()->get_routes();
        if(!isset($routes[$route])) return ['answer'=>'','available'=>false,'diagnostic'=>'APP_ROUTE_MISSING','status'=>503];

        $token='';
        if(defined('AUTOID_SUPPORT_APP_TOKEN') && AUTOID_SUPPORT_APP_TOKEN) $token=trim((string)AUTOID_SUPPORT_APP_TOKEN);
        if($token==='') {
            $environment=getenv('AUTOID_SUPPORT_APP_TOKEN');
            if(is_string($environment)) $token=trim($environment);
        }
        if(strlen($token)<32) return ['answer'=>'','available'=>true,'diagnostic'=>'APP_TOKEN_MISSING_OR_SHORT','status'=>503];

        $state_key='autoid_sc_app_'.md5(hash('sha256',(string)$device_id));
        $state=get_transient($state_key);
        if(!is_array($state)) $state=[];
        $history=is_array($state['history']??null)?$state['history']:[];
        $history=array_slice($history,-12);

        $model_id=absint($state['model_id']??0);
        if($model_id<=0 && $product_id>0) $model_id=self::support_center_app_model_from_product_v132($product_id);

        $payload=[
            'message'=>$message,
            'model_id'=>$model_id,
            'brand_id'=>absint($state['brand_id']??0),
            'category_id'=>absint($state['category_id']??0),
            'category_name'=>sanitize_text_field((string)($state['category_name']??'')),
            'previous_intent'=>sanitize_key((string)($state['previous_intent']??'')),
            'product_id'=>$product_id ?: absint($state['product_id']??0),
            'session_token'=>sanitize_text_field((string)($state['session_token']??'')),
            'history'=>$history,
        ];

        $had_http_auth=array_key_exists('HTTP_AUTHORIZATION',$_SERVER);
        $old_http_auth=$had_http_auth?$_SERVER['HTTP_AUTHORIZATION']:null;
        $had_redirect_auth=array_key_exists('REDIRECT_HTTP_AUTHORIZATION',$_SERVER);
        $old_redirect_auth=$had_redirect_auth?$_SERVER['REDIRECT_HTTP_AUTHORIZATION']:null;
        $_SERVER['HTTP_AUTHORIZATION']='Bearer '.$token;
        $_SERVER['REDIRECT_HTTP_AUTHORIZATION']='Bearer '.$token;

        try {
            $req=new WP_REST_Request('POST',$route);
            foreach($payload as $key=>$value) $req->set_param($key,$value);
            $req->set_body_params($payload);
            $req->set_header('authorization','Bearer '.$token);
            $req->set_header('accept','application/json');
            $req->set_header('content-type','application/json');
            $req->set_body(wp_json_encode($payload));
            $resp=rest_do_request($req);
        } catch(Throwable $e) {
            $resp=new WP_Error('autoid_support_app_exception','Support App API exception.');
        } finally {
            if($had_http_auth) $_SERVER['HTTP_AUTHORIZATION']=$old_http_auth; else unset($_SERVER['HTTP_AUTHORIZATION']);
            if($had_redirect_auth) $_SERVER['REDIRECT_HTTP_AUTHORIZATION']=$old_redirect_auth; else unset($_SERVER['REDIRECT_HTTP_AUTHORIZATION']);
        }

        if(is_wp_error($resp)) {
            return ['answer'=>'','available'=>true,'diagnostic'=>'APP_WP_'.sanitize_key((string)$resp->get_error_code()),'status'=>502];
        }
        if(!is_object($resp) || !method_exists($resp,'get_status')) return ['answer'=>'','available'=>true,'diagnostic'=>'APP_INVALID_RESPONSE','status'=>502];

        $status=(int)$resp->get_status();
        $envelope=$resp->get_data();
        if($status<200 || $status>=300 || !is_array($envelope) || empty($envelope['ok'])) {
            $code='http_'.$status;
            if(is_array($envelope)) $code=sanitize_key((string)($envelope['code']??($envelope['data']['code']??$code)));
            return ['answer'=>'','available'=>true,'diagnostic'=>'APP_'.$status.'_'.($code?:'error'),'status'=>502];
        }

        $data=is_array($envelope['data']??null)?$envelope['data']:[];
        $answer=trim((string)($data['answer']??''));
        if($answer==='') $answer=self::extract_ai_answer($data);
        if($answer==='') return ['answer'=>'','available'=>true,'diagnostic'=>'APP_200_EMPTY','status'=>502];

        $state['model_id']=absint($data['model_id']??$model_id);
        $state['brand_id']=absint($data['brand_id']??($state['brand_id']??0));
        $state['category_id']=absint($data['category_id']??($state['category_id']??0));
        $state['category_name']=sanitize_text_field((string)($data['category_name']??($state['category_name']??'')));
        $state['previous_intent']=sanitize_key((string)($data['intent']??($data['previous_intent']??($state['previous_intent']??''))));
        $state['session_token']=sanitize_text_field((string)($data['session_token']??($state['session_token']??'')));
        $state['product_id']=$product_id ?: absint($state['product_id']??0);
        $history[]=['role'=>'user','content'=>wp_strip_all_tags((string)$message)];
        $history[]=['role'=>'assistant','content'=>wp_strip_all_tags((string)$answer)];
        $state['history']=array_slice($history,-12);
        set_transient($state_key,$state,2*HOUR_IN_SECONDS);

        return [
            'answer'=>$answer,
            'available'=>true,
            'diagnostic'=>'APP_OK',
            'status'=>200,
            'phase'=>sanitize_key((string)($data['phase']??'')),
            'model_id'=>absint($data['model_id']??0),
            'resolved'=>!empty($data['resolved']),
        ];
    }

    private static function support_center_app_model_from_product_v132($product_id) {
        $product_id=absint($product_id);
        if($product_id<=0 || !class_exists('AutoID_Support_Models')) return 0;
        try {
            foreach((array)AutoID_Support_Models::support_ready_models() as $row) {
                $model_id=absint($row['id']??0);
                $grouped_id=absint($row['grouped_product_id']??0);
                if(!$model_id || !$grouped_id) continue;
                if($grouped_id===$product_id) return $model_id;
                if(function_exists('wc_get_product')) {
                    $grouped=wc_get_product($grouped_id);
                    if($grouped && method_exists($grouped,'get_children')) {
                        $children=array_map('absint',(array)$grouped->get_children());
                        if(in_array($product_id,$children,true)) return $model_id;
                    }
                }
            }
        } catch(Throwable $e) {}
        return 0;
    }
