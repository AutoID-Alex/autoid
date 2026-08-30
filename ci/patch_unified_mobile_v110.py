from pathlib import Path

p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()

s=s.replace('Plugin Name: AutoID Mobile Commerce Bridge','Plugin Name: AutoID Mobile')
s=s.replace('Description: Mobile catalog, product-family, support and search bridge for AutoID. Coexists with AutoID Mobile API auth/order/payment routes.','Description: Unified mobile gateway for the AutoID Android/iOS apps: catalog, search, support, authentication, account, orders, checkout, Google Sign-In and native payment infrastructure.')
s=s.replace('Version: 1.0.6','Version: 1.1.0')
s=s.replace('final class AutoID_Mobile_Commerce_Bridge_106 {','final class AutoID_Mobile_110 {')
s=s.replace('AutoID_Mobile_Commerce_Bridge_106::boot();','AutoID_Mobile_110::boot();')

route_anchor="        register_rest_route(self::NS, '/consultation/request', $public + ['methods'=>'POST','callback'=>[__CLASS__,'consultation_request']]);\n"
extra_routes="""        register_rest_route(self::NS, '/health', $public + ['methods'=>'GET','callback'=>[__CLASS__,'health']]);
        register_rest_route(self::NS, '/auth/login', $public + ['methods'=>'POST','callback'=>[__CLASS__,'auth_login']]);
        register_rest_route(self::NS, '/auth/google', $public + ['methods'=>'POST','callback'=>[__CLASS__,'auth_google']]);
        register_rest_route(self::NS, '/me', ['methods'=>'GET','callback'=>[__CLASS__,'me'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/me/orders', ['methods'=>'GET','callback'=>[__CLASS__,'me_orders'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/payments/intent', ['methods'=>'POST','callback'=>[__CLASS__,'payment_intent'],'permission_callback'=>[__CLASS__,'auth_permission']]);
"""
if extra_routes.strip() not in s:
    s=s.replace(route_anchor,route_anchor+extra_routes)

class_end=s.rfind('\n}\n\nAutoID_Mobile_110::boot();')
if class_end<0: raise SystemExit('Unified class end anchor not found')
methods=r'''

    public static function health(WP_REST_Request $r) {
        return rest_ensure_response([
            'ok'=>true,
            'plugin'=>'AutoID Mobile',
            'version'=>'1.1.0',
            'namespace'=>self::NS,
            'woocommerce'=>function_exists('WC'),
            'site'=>home_url('/'),
            'time'=>gmdate('c'),
        ]);
    }

    private static function token_secret() {
        return hash('sha256', wp_salt('auth').'|autoid-mobile-v1');
    }

    private static function b64url_encode($v) {
        return rtrim(strtr(base64_encode($v), '+/', '-_'), '=');
    }

    private static function b64url_decode($v) {
        $v=strtr($v,'-_','+/');
        $pad=strlen($v)%4; if($pad)$v.=str_repeat('=',4-$pad);
        return base64_decode($v,true);
    }

    private static function issue_token($user_id) {
        $payload = wp_json_encode(['uid'=>(int)$user_id,'iat'=>time(),'exp'=>time()+30*DAY_IN_SECONDS,'rnd'=>wp_generate_password(12,false,false)]);
        $body = self::b64url_encode($payload);
        $sig = self::b64url_encode(hash_hmac('sha256',$body,self::token_secret(),true));
        return $body.'.'.$sig;
    }

    private static function bearer_user_id(WP_REST_Request $r) {
        $auth=(string)$r->get_header('authorization');
        if(!preg_match('/^Bearer\s+(.+)$/i',$auth,$m)) return 0;
        $parts=explode('.',$m[1]); if(count($parts)!==2) return 0;
        [$body,$sig]=$parts;
        $expected=self::b64url_encode(hash_hmac('sha256',$body,self::token_secret(),true));
        if(!hash_equals($expected,$sig)) return 0;
        $raw=self::b64url_decode($body); if(!$raw) return 0;
        $data=json_decode($raw,true); if(!is_array($data)||empty($data['uid'])||empty($data['exp'])||time()>(int)$data['exp']) return 0;
        $u=get_user_by('id',absint($data['uid'])); return $u?(int)$u->ID:0;
    }

    public static function auth_permission(WP_REST_Request $r) {
        $uid=self::bearer_user_id($r);
        if(!$uid) return new WP_Error('autoid_auth_required','Autentificare necesară.',['status'=>401]);
        $r->set_param('_autoid_user_id',$uid);
        return true;
    }

    private static function customer_payload($uid) {
        $u=get_user_by('id',$uid); if(!$u) return null;
        $c=class_exists('WC_Customer')?new WC_Customer($uid):null;
        return [
            'id'=>(int)$uid,
            'email'=>$u->user_email,
            'name'=>trim(($c?$c->get_first_name():'').' '.($c?$c->get_last_name():'')) ?: $u->display_name,
            'first_name'=>$c?$c->get_first_name():'',
            'last_name'=>$c?$c->get_last_name():'',
            'company'=>$c?$c->get_billing_company():'',
        ];
    }

    private static function auth_response($uid) {
        return rest_ensure_response([
            'access_token'=>self::issue_token($uid),
            'token_type'=>'Bearer',
            'expires_in'=>30*DAY_IN_SECONDS,
            'customer'=>self::customer_payload($uid),
        ]);
    }

    public static function auth_login(WP_REST_Request $r) {
        $b=$r->get_json_params(); if(!is_array($b))$b=[];
        $login=sanitize_text_field((string)($b['login']??$b['username']??$b['email']??''));
        $password=(string)($b['password']??'');
        if($login===''||$password==='') return new WP_Error('autoid_bad_login','Completează emailul/utilizatorul și parola.',['status'=>400]);
        $user=wp_authenticate($login,$password);
        if(is_wp_error($user) && is_email($login)) {
            $by_email=get_user_by('email',$login);
            if($by_email) $user=wp_authenticate($by_email->user_login,$password);
        }
        if(is_wp_error($user)||!$user) return new WP_Error('autoid_login_failed','Email/utilizator sau parolă incorectă.',['status'=>401]);
        return self::auth_response($user->ID);
    }

    public static function auth_google(WP_REST_Request $r) {
        $b=$r->get_json_params(); if(!is_array($b))$b=[];
        $id_token=trim((string)($b['id_token']??$b['credential']??''));
        if($id_token==='') return new WP_Error('autoid_google_token_missing','Token Google lipsă.',['status'=>400]);
        $res=wp_remote_get('https://oauth2.googleapis.com/tokeninfo?id_token='.rawurlencode($id_token),['timeout'=>10,'redirection'=>2]);
        if(is_wp_error($res)) return new WP_Error('autoid_google_unavailable','Google Sign-In nu a putut fi verificat.',['status'=>502]);
        $code=wp_remote_retrieve_response_code($res); $data=json_decode(wp_remote_retrieve_body($res),true);
        if($code!==200||!is_array($data)||empty($data['email'])||($data['email_verified']??'false')!=='true') return new WP_Error('autoid_google_invalid','Token Google invalid.',['status'=>401]);
        $client_id=trim((string)get_option('autoid_mobile_google_client_id',''));
        if($client_id!=='' && !hash_equals($client_id,(string)($data['aud']??''))) return new WP_Error('autoid_google_audience','Tokenul Google nu aparține aplicației AutoID.',['status'=>401]);
        $email=sanitize_email((string)$data['email']); $user=get_user_by('email',$email);
        if(!$user){
            $login=sanitize_user(strstr($email,'@',true),true); if($login==='')$login='autoid';
            $base=$login;$i=1;while(username_exists($login)){$login=$base.$i;$i++;}
            $uid=wp_create_user($login,wp_generate_password(32,true,true),$email); if(is_wp_error($uid))return $uid;
            $user=get_user_by('id',$uid);
            wp_update_user(['ID'=>$uid,'first_name'=>sanitize_text_field((string)($data['given_name']??'')),'last_name'=>sanitize_text_field((string)($data['family_name']??'')),'display_name'=>sanitize_text_field((string)($data['name']??$email))]);
        }
        update_user_meta($user->ID,'autoid_google_sub',sanitize_text_field((string)($data['sub']??'')));
        return self::auth_response($user->ID);
    }

    public static function me(WP_REST_Request $r) {
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        return rest_ensure_response(['customer'=>self::customer_payload($uid)]);
    }

    public static function me_orders(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        $orders=wc_get_orders(['customer_id'=>$uid,'limit'=>50,'orderby'=>'date','order'=>'DESC']);
        $rows=[];
        foreach($orders as $o){
            $rows[]=['id'=>$o->get_id(),'number'=>$o->get_order_number(),'status'=>$o->get_status(),'status_label'=>wc_get_order_status_name($o->get_status()),'total'=>$o->get_total(),'currency'=>$o->get_currency(),'created_at'=>$o->get_date_created()?$o->get_date_created()->date('c'):null];
        }
        return rest_ensure_response(['orders'=>$rows]);
    }

    private static function stripe_secret() {
        $manual=trim((string)get_option('autoid_mobile_stripe_secret','')); if($manual!=='')return $manual;
        foreach(['woocommerce_stripe_settings','woocommerce_stripe_cc_settings'] as $opt){
            $cfg=get_option($opt,[]); if(!is_array($cfg))continue;
            $test=($cfg['testmode']??'no')==='yes';
            $key=$test?($cfg['test_secret_key']??$cfg['test_sk']??''):($cfg['secret_key']??$cfg['live_secret_key']??$cfg['live_sk']??'');
            if(is_string($key)&&str_starts_with(trim($key),'sk_'))return trim($key);
        }
        return '';
    }

    public static function payment_intent(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        $b=$r->get_json_params(); if(!is_array($b))$b=[]; $oid=absint($b['order_id']??0);
        $order=$oid?wc_get_order($oid):null; if(!$order)return new WP_Error('autoid_order_missing','Comanda nu există.',['status'=>404]);
        if((int)$order->get_customer_id()!==$uid && !current_user_can('manage_woocommerce'))return new WP_Error('autoid_order_forbidden','Comanda nu aparține contului curent.',['status'=>403]);
        if($order->is_paid())return new WP_Error('autoid_order_paid','Comanda este deja plătită.',['status'=>409]);
        $secret=self::stripe_secret(); if($secret==='')return new WP_Error('autoid_stripe_not_configured','Stripe nu este configurat pentru plata nativă.',['status'=>409]);
        $amount=(int)round(((float)$order->get_total())*100); if($amount<50)return new WP_Error('autoid_stripe_amount','Valoare comandă invalidă.',['status'=>400]);
        $response=wp_remote_post('https://api.stripe.com/v1/payment_intents',[
            'timeout'=>15,
            'headers'=>['Authorization'=>'Bearer '.$secret],
            'body'=>[
                'amount'=>$amount,'currency'=>strtolower($order->get_currency()),
                'automatic_payment_methods[enabled]'=>'true',
                'metadata[order_id]'=>$order->get_id(),
                'description'=>'AutoID order #'.$order->get_order_number(),
                'receipt_email'=>$order->get_billing_email(),
            ],
        ]);
        if(is_wp_error($response))return new WP_Error('autoid_stripe_error',$response->get_error_message(),['status'=>502]);
        $code=wp_remote_retrieve_response_code($response);$data=json_decode(wp_remote_retrieve_body($response),true);
        if($code<200||$code>=300||!is_array($data)||empty($data['client_secret']))return new WP_Error('autoid_stripe_error',sanitize_text_field((string)($data['error']['message']??'Stripe nu a creat PaymentIntent.')),['status'=>502]);
        $order->update_meta_data('_autoid_stripe_payment_intent',sanitize_text_field((string)$data['id']));$order->save();
        return rest_ensure_response(['payment_intent_id'=>$data['id'],'client_secret'=>$data['client_secret'],'order_id'=>$order->get_id(),'amount'=>$amount,'currency'=>strtolower($order->get_currency())]);
    }
'''
s=s[:class_end]+methods+s[class_end:]

# Activation: one plugin owns the mobile namespace; deactivate legacy modules after this plugin is activated.
footer='''

register_activation_hook(__FILE__, function(){
    if(!function_exists('deactivate_plugins')) require_once ABSPATH.'wp-admin/includes/plugin.php';
    $self=plugin_basename(__FILE__);
    foreach(['autoid-mobile-api/autoid-mobile-api.php','autoid-mobile-commerce/autoid-mobile-commerce.php'] as $legacy){
        if($legacy!==$self && is_plugin_active($legacy)) deactivate_plugins($legacy,true);
    }
    flush_rewrite_rules(false);
});
'''
s += footer

p.write_text(s)
print('Patched unified AutoID Mobile v1.1.0 with auth, Google Sign-In, account/orders and Stripe PaymentIntent infrastructure')
