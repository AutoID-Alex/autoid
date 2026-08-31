from pathlib import Path

p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()
s=s.replace('Version: 1.1.5','Version: 1.1.6',1)
s=s.replace("'bridge_version'=>'1.1.5'","'bridge_version'=>'1.1.6'",1)

route_anchor="        register_rest_route(self::NS, '/me/orders', ['methods'=>'GET','callback'=>[__CLASS__,'me_orders'],'permission_callback'=>[__CLASS__,'auth_permission']]);\n"
if "'/me/profile'" not in s:
    routes=route_anchor+"        register_rest_route(self::NS, '/me/profile', ['methods'=>['GET','POST'],'callback'=>[__CLASS__,'me_profile'],'permission_callback'=>[__CLASS__,'auth_permission']]);\n        register_rest_route(self::NS, '/me/addresses', ['methods'=>['GET','POST'],'callback'=>[__CLASS__,'me_addresses'],'permission_callback'=>[__CLASS__,'auth_permission']]);\n        register_rest_route(self::NS, '/me/payment-methods', ['methods'=>'GET','callback'=>[__CLASS__,'me_payment_methods'],'permission_callback'=>[__CLASS__,'auth_permission']]);\n"
    if route_anchor not in s: raise SystemExit('route anchor missing')
    s=s.replace(route_anchor,routes,1)

settings_anchor="""        register_setting(
            'autoid_mobile_home_group',
            'autoid_mobile_home_skus',
            [
                'type'=>'string',
                'sanitize_callback'=>[__CLASS__, 'sanitize_home_skus'],
                'default'=>'',
            ]
        );
"""
if "'autoid_mobile_google_client_id'" not in s[s.index('public static function admin_init()'):s.index('public static function sanitize_home_skus')]:
    google_setting=settings_anchor+"""        register_setting(
            'autoid_mobile_home_group',
            'autoid_mobile_google_client_id',
            [
                'type'=>'string',
                'sanitize_callback'=>function($value){return sanitize_text_field(trim((string)$value));},
                'default'=>'',
            ]
        );
"""
    if settings_anchor not in s: raise SystemExit('settings anchor missing')
    s=s.replace(settings_anchor,google_setting,1)

render_value="        $value=(string)get_option('autoid_mobile_home_skus','');\n"
if "$google_client_id=(string)get_option('autoid_mobile_google_client_id','');" not in s:
    if render_value not in s: raise SystemExit('render value anchor missing')
    s=s.replace(render_value,render_value+"        $google_client_id=(string)get_option('autoid_mobile_google_client_id','');\n",1)

form_anchor="""                    <tr>
                        <th scope="row"><label for="autoid_mobile_home_skus">SKU-uri produse</label></th>
                        <td>
                            <textarea id="autoid_mobile_home_skus" name="autoid_mobile_home_skus" rows="14" class="large-text code" placeholder="ZT411R&#10;MC333R-GI4HG4EU"><?php echo esc_textarea($value); ?></textarea>
                            <p class="description">Un SKU pe linie. Sunt acceptate și virgulă sau punct și virgulă. Dacă lista este goală, aplicația folosește selecția automată existentă.</p>
                        </td>
                    </tr>
"""
if 'id="autoid_mobile_google_client_id"' not in s:
    google_row=form_anchor+"""                    <tr>
                        <th scope="row"><label for="autoid_mobile_google_client_id">Google Web OAuth Client ID</label></th>
                        <td>
                            <input type="text" id="autoid_mobile_google_client_id" name="autoid_mobile_google_client_id" value="<?php echo esc_attr($google_client_id); ?>" class="large-text code" placeholder="123456789-xxxx.apps.googleusercontent.com" />
                            <p class="description">Client ID de tip <strong>Web application</strong> folosit de Android Credential Manager pentru ID token. În Google Cloud configurează separat și clientul Android pentru package <code>ro.autoid.app</code> + SHA-1/SHA-256 al certificatului aplicației.</p>
                        </td>
                    </tr>
"""
    if form_anchor not in s: raise SystemExit('form anchor missing')
    s=s.replace(form_anchor,google_row,1)

methods_anchor="""    public static function me_orders(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        $orders=wc_get_orders(['customer_id'=>$uid,'limit'=>50,'orderby'=>'date','order'=>'DESC']);
        $rows=[];
        foreach($orders as $o){
            $rows[]=['id'=>$o->get_id(),'number'=>$o->get_order_number(),'status'=>$o->get_status(),'status_label'=>wc_get_order_status_name($o->get_status()),'total'=>$o->get_total(),'currency'=>$o->get_currency(),'created_at'=>$o->get_date_created()?$o->get_date_created()->date('c'):null];
        }
        return rest_ensure_response(['orders'=>$rows]);
    }
"""
extra_methods=r'''

    private static function account_address_payload($customer,$type) {
        $prefix=$type==='shipping'?'get_shipping_':'get_billing_';
        $read=function($field) use ($customer,$prefix){$method=$prefix.$field;return method_exists($customer,$method)?(string)$customer->$method():'';};
        return [
            'first_name'=>$read('first_name'),'last_name'=>$read('last_name'),'company'=>$read('company'),
            'address_1'=>$read('address_1'),'address_2'=>$read('address_2'),'city'=>$read('city'),'state'=>$read('state'),
            'postcode'=>$read('postcode'),'country'=>$read('country') ?: 'RO','phone'=>$read('phone'),'email'=>$read('email'),
        ];
    }

    public static function me_profile(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        $customer=new WC_Customer($uid);
        if($r->get_method()==='POST'){
            $b=$r->get_json_params(); if(!is_array($b))$b=[];
            if(array_key_exists('first_name',$b))$customer->set_first_name(sanitize_text_field((string)$b['first_name']));
            if(array_key_exists('last_name',$b))$customer->set_last_name(sanitize_text_field((string)$b['last_name']));
            if(array_key_exists('company',$b))$customer->set_billing_company(sanitize_text_field((string)$b['company']));
            $customer->save();
        }
        return rest_ensure_response(['profile'=>[
            'id'=>$uid,'email'=>$customer->get_email(),'first_name'=>$customer->get_first_name(),'last_name'=>$customer->get_last_name(),'company'=>$customer->get_billing_company(),
        ]]);
    }

    public static function me_addresses(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        $customer=new WC_Customer($uid);
        if($r->get_method()==='POST'){
            $b=$r->get_json_params(); if(!is_array($b))$b=[];
            foreach(['billing','shipping'] as $type){
                $row=is_array($b[$type]??null)?$b[$type]:[];
                foreach(['first_name','last_name','company','address_1','address_2','city','state','postcode','country','phone','email'] as $field){
                    if(!array_key_exists($field,$row))continue;
                    $method='set_'.$type.'_'.$field;
                    if(!method_exists($customer,$method))continue;
                    $value=(string)$row[$field];
                    if($field==='email')$value=sanitize_email($value); elseif($field==='country')$value=strtoupper(sanitize_text_field($value)); else $value=sanitize_text_field($value);
                    $customer->$method($value);
                }
            }
            $customer->save();
        }
        return rest_ensure_response(['billing'=>self::account_address_payload($customer,'billing'),'shipping'=>self::account_address_payload($customer,'shipping')]);
    }

    public static function me_payment_methods(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        $tokens=class_exists('WC_Payment_Tokens')?WC_Payment_Tokens::get_customer_tokens($uid):[];
        $default=class_exists('WC_Payment_Tokens')?WC_Payment_Tokens::get_customer_default_token($uid):null;
        $default_id=$default&&is_object($default)?(int)$default->get_id():0;
        $rows=[];
        foreach((array)$tokens as $token){
            if(!is_object($token)||!method_exists($token,'get_id'))continue;
            $label=method_exists($token,'get_display_name')?(string)$token->get_display_name():(method_exists($token,'get_type')?(string)$token->get_type():'Metodă salvată');
            $rows[]=['id'=>(int)$token->get_id(),'type'=>method_exists($token,'get_type')?(string)$token->get_type():'','label'=>wp_strip_all_tags($label),'is_default'=>(int)$token->get_id()===$default_id];
        }
        return rest_ensure_response(['methods'=>$rows]);
    }
'''
if 'public static function me_profile(' not in s:
    if methods_anchor not in s: raise SystemExit('methods anchor missing')
    s=s.replace(methods_anchor,methods_anchor+extra_methods,1)
p.write_text(s)
print('Patched AutoID Mobile v1.1.6: Google OAuth setting + account profile/address/payment endpoints')
