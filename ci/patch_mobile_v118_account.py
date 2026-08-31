from pathlib import Path
p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()
s=s.replace('Version: 1.1.7','Version: 1.1.8',1)
s=s.replace("'bridge_version'=>'1.1.7'","'bridge_version'=>'1.1.8'",1)

route="        register_rest_route(self::NS, '/me/orders', ['methods'=>'GET','callback'=>[__CLASS__,'me_orders'],'permission_callback'=>[__CLASS__,'auth_permission']]);\n"
newroute=route+"        register_rest_route(self::NS, '/me/orders/(?P<id>\\d+)', ['methods'=>'GET','callback'=>[__CLASS__,'me_order_detail'],'permission_callback'=>[__CLASS__,'auth_permission']]);\n"
if "'/me/orders/(?P<id>\\d+)'" not in s:
    if route not in s: raise SystemExit('orders route anchor')
    s=s.replace(route,newroute,1)
old="        register_rest_route(self::NS, '/me/payment-methods', ['methods'=>'GET','callback'=>[__CLASS__,'me_payment_methods'],'permission_callback'=>[__CLASS__,'auth_permission']]);"
new="        register_rest_route(self::NS, '/me/payment-methods', ['methods'=>['GET','POST'],'callback'=>[__CLASS__,'me_payment_methods'],'permission_callback'=>[__CLASS__,'auth_permission']]);"
if old not in s: raise SystemExit('payment route anchor')
s=s.replace(old,new,1)

start=s.index('    public static function me_orders(WP_REST_Request $r) {')
end=s.index('\n\n    private static function account_address_payload',start)
methods=r'''    public static function me_orders(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        $orders=wc_get_orders(['customer_id'=>$uid,'limit'=>50,'orderby'=>'date','order'=>'DESC']);
        $rows=[];
        foreach($orders as $o){$rows[]=['id'=>$o->get_id(),'number'=>$o->get_order_number(),'status'=>$o->get_status(),'status_label'=>wc_get_order_status_name($o->get_status()),'total'=>$o->get_total(),'currency'=>$o->get_currency(),'created_at'=>$o->get_date_created()?$o->get_date_created()->date('c'):null];}
        return rest_ensure_response(['orders'=>$rows]);
    }

    public static function me_order_detail(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        $id=absint($r->get_param('id')); $order=$id?wc_get_order($id):null;
        if(!$order)return new WP_Error('autoid_order_missing','Comanda nu există.',['status'=>404]);
        if((int)$order->get_customer_id()!==$uid)return new WP_Error('autoid_order_forbidden','Comanda nu aparține contului curent.',['status'=>403]);
        $items=[];$subtotal_incl=0.0;
        foreach($order->get_items('line_item') as $item){$product=$item->get_product();$image='';if($product&&$product->get_image_id())$image=(string)wp_get_attachment_image_url($product->get_image_id(),'woocommerce_thumbnail');$subtotal_incl+=(float)$item->get_subtotal()+(float)$item->get_subtotal_tax();$items[]=['product_id'=>$product?(int)$product->get_id():0,'name'=>$item->get_name(),'quantity'=>(int)$item->get_quantity(),'total'=>(string)((float)$item->get_total()+(float)$item->get_total_tax()),'image'=>$image];}
        $ship=[];foreach($order->get_shipping_methods() as $method)$ship[]=$method->get_name();
        $notes=[];if(function_exists('wc_get_order_notes'))foreach((array)wc_get_order_notes(['order_id'=>$order->get_id(),'type'=>'customer','limit'=>20]) as $note){$notes[]=['content'=>wp_strip_all_tags((string)$note->content),'created_at'=>isset($note->date_created)&&$note->date_created?$note->date_created->date('c'):''];}
        $billing=['first_name'=>$order->get_billing_first_name(),'last_name'=>$order->get_billing_last_name(),'company'=>$order->get_billing_company(),'address_1'=>$order->get_billing_address_1(),'address_2'=>$order->get_billing_address_2(),'city'=>$order->get_billing_city(),'state'=>$order->get_billing_state(),'postcode'=>$order->get_billing_postcode(),'country'=>$order->get_billing_country(),'phone'=>$order->get_billing_phone(),'email'=>$order->get_billing_email()];
        $shipping=['first_name'=>$order->get_shipping_first_name(),'last_name'=>$order->get_shipping_last_name(),'company'=>$order->get_shipping_company(),'address_1'=>$order->get_shipping_address_1(),'address_2'=>$order->get_shipping_address_2(),'city'=>$order->get_shipping_city(),'state'=>$order->get_shipping_state(),'postcode'=>$order->get_shipping_postcode(),'country'=>$order->get_shipping_country(),'phone'=>'','email'=>''];
        return rest_ensure_response(['id'=>$order->get_id(),'number'=>$order->get_order_number(),'status'=>$order->get_status(),'status_label'=>wc_get_order_status_name($order->get_status()),'created_at'=>$order->get_date_created()?$order->get_date_created()->date('c'):'','currency'=>$order->get_currency(),'subtotal'=>(string)$subtotal_incl,'discount_total'=>(string)((float)$order->get_discount_total()+(float)$order->get_discount_tax()),'shipping_total'=>(string)((float)$order->get_shipping_total()+(float)$order->get_shipping_tax()),'tax_total'=>(string)$order->get_total_tax(),'total'=>(string)$order->get_total(),'payment_method'=>$order->get_payment_method_title(),'shipping_method'=>implode(', ',$ship),'customer_note'=>$order->get_customer_note(),'billing'=>$billing,'shipping'=>$shipping,'items'=>$items,'notes'=>$notes]);
    }'''
s=s[:start]+methods+s[end:]

start=s.index('    public static function me_profile(WP_REST_Request $r) {')
end=s.index('\n\n    public static function me_addresses',start)
profile=r'''    public static function me_profile(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        $customer=new WC_Customer($uid);
        if($r->get_method()==='POST'){
            $b=$r->get_json_params(); if(!is_array($b))$b=[];
            if(array_key_exists('first_name',$b))$customer->set_first_name(sanitize_text_field((string)$b['first_name']));
            if(array_key_exists('last_name',$b))$customer->set_last_name(sanitize_text_field((string)$b['last_name']));
            if(array_key_exists('email',$b)){$email=sanitize_email((string)$b['email']);if(!$email||!is_email($email))return new WP_Error('autoid_bad_email','Adresa de email nu este validă.',['status'=>400]);$existing=email_exists($email);if($existing&&(int)$existing!==$uid)return new WP_Error('autoid_email_exists','Există deja un cont cu această adresă de email.',['status'=>409]);$updated=wp_update_user(['ID'=>$uid,'user_email'=>$email]);if(is_wp_error($updated))return $updated;if(method_exists($customer,'set_billing_email'))$customer->set_billing_email($email);}
            $password=(string)($b['new_password']??'');if($password!==''){if(strlen($password)<8)return new WP_Error('autoid_password_short','Parola nouă trebuie să aibă cel puțin 8 caractere.',['status'=>400]);wp_set_password($password,$uid);}
            $customer->save();$customer=new WC_Customer($uid);
        }
        return rest_ensure_response(['profile'=>['id'=>$uid,'email'=>$customer->get_email(),'first_name'=>$customer->get_first_name(),'last_name'=>$customer->get_last_name()]]);
    }'''
s=s[:start]+profile+s[end:]

old="""            $customer->save();
        }
        $vat=(string)get_user_meta($uid,'_eu_vat_guard_vat_number',true);if($vat==='')$vat=(string)get_user_meta($uid,'billing_vat',true);if($vat==='')$vat=(string)get_user_meta($uid,'vat_number',true);return rest_ensure_response(['billing'=>self::account_address_payload($customer,'billing'),'shipping'=>self::account_address_payload($customer,'shipping'),'vat_number'=>$vat]);
    }

    public static function me_payment_methods"""
new="""            $customer->save();
            if(array_key_exists('vat_number',$b)){$vat=sanitize_text_field((string)$b['vat_number']);update_user_meta($uid,'_eu_vat_guard_vat_number',$vat);update_user_meta($uid,'billing_vat',$vat);update_user_meta($uid,'vat_number',$vat);}
        }
        $vat=(string)get_user_meta($uid,'_eu_vat_guard_vat_number',true);if($vat==='')$vat=(string)get_user_meta($uid,'billing_vat',true);if($vat==='')$vat=(string)get_user_meta($uid,'vat_number',true);return rest_ensure_response(['billing'=>self::account_address_payload($customer,'billing'),'shipping'=>self::account_address_payload($customer,'shipping'),'vat_number'=>$vat]);
    }

    public static function me_payment_methods"""
if old not in s: raise SystemExit('addresses VAT anchor')
s=s.replace(old,new,1)

start=s.index('    public static function me_payment_methods(WP_REST_Request $r) {')
end=s.index('\n\n    private static function stripe_secret',start)
pay=r'''    public static function me_payment_methods(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        if($r->get_method()==='POST'){$b=$r->get_json_params();if(!is_array($b))$b=[];$token_id=absint($b['token_id']??0);$action=sanitize_key((string)($b['action']??''));$token=$token_id&&class_exists('WC_Payment_Tokens')?WC_Payment_Tokens::get($token_id):null;if(!$token||!is_object($token)||(int)$token->get_user_id()!==$uid)return new WP_Error('autoid_payment_token_invalid','Metoda de plată nu este validă.',['status'=>404]);if($action==='set_default')WC_Payment_Tokens::set_users_default($uid,$token_id);elseif($action==='delete')WC_Payment_Tokens::delete($token_id);else return new WP_Error('autoid_payment_action','Acțiune invalidă pentru metoda de plată.',['status'=>400]);}
        $tokens=class_exists('WC_Payment_Tokens')?WC_Payment_Tokens::get_customer_tokens($uid):[];$default=class_exists('WC_Payment_Tokens')?WC_Payment_Tokens::get_customer_default_token($uid):null;$default_id=$default&&is_object($default)?(int)$default->get_id():0;$rows=[];
        foreach((array)$tokens as $token){if(!is_object($token)||!method_exists($token,'get_id'))continue;$label=method_exists($token,'get_display_name')?(string)$token->get_display_name():(method_exists($token,'get_type')?(string)$token->get_type():'Metodă salvată');$rows[]=['id'=>(int)$token->get_id(),'type'=>method_exists($token,'get_type')?(string)$token->get_type():'','label'=>wp_strip_all_tags($label),'is_default'=>(int)$token->get_id()===$default_id];}
        return rest_ensure_response(['methods'=>$rows]);
    }'''
s=s[:start]+pay+s[end:]
p.write_text(s)
print('Patched AutoID Mobile v1.1.8: order detail, editable profile/addresses/VAT and payment methods')
