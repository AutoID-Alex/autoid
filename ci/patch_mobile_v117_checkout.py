from pathlib import Path
p=Path('autoid-mobile/autoid-mobile.php')
s=p.read_text()
s=s.replace('Version: 1.1.6','Version: 1.1.7',1)
s=s.replace("'bridge_version'=>'1.1.6'","'bridge_version'=>'1.1.7'",1)

boot="        add_action('admin_init', [__CLASS__, 'admin_init']); // autoid_mobile_hero\n"
if "order_origin_source" not in s:
    if boot not in s: raise SystemExit('boot anchor missing')
    s=s.replace(boot,boot+"        add_filter('wc_order_attribution_origin_formatted_source', [__CLASS__, 'order_origin_source'], 10, 2);\n",1)

marker='    private static function require_wc() {'
origin='''    public static function order_origin_source($formatted_source,$source) {\n        $mobile=__('Mobile app','woocommerce');\n        if((string)$source===(string)$mobile || strtolower(trim((string)$source))==='mobile app') return 'Android App';\n        return $formatted_source;\n    }\n\n'''
if origin not in s:
    if marker not in s: raise SystemExit('origin method anchor missing')
    s=s.replace(marker,origin+marker,1)

start=s.index('    public static function checkout_order(WP_REST_Request $r) {')
end=s.index('    public static function register_customer(WP_REST_Request $r){',start)
checkout=r'''    public static function checkout_order(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok)) return $ok;
        $body=$r->get_json_params(); if(!is_array($body)) $body=[];
        $lines=$body['line_items']??[]; if(!is_array($lines)||!$lines) return new WP_Error('autoid_empty_cart','Coșul este gol.',['status'=>400]);
        $payment=sanitize_key((string)($body['payment_method']??'cod')); if(!in_array($payment,['cod','bacs','stripe'],true)) return new WP_Error('autoid_bad_payment','Metodă de plată invalidă.',['status'=>400]);
        if($payment==='stripe' && !apply_filters('autoid_mobile_stripe_native_enabled',false)) return new WP_Error('autoid_stripe_not_ready','Plata Stripe nativă nu este încă activată.',['status'=>409]);
        $billing=is_array($body['billing']??null)?$body['billing']:[];$shipping=is_array($body['shipping']??null)?$body['shipping']:$billing;
        foreach(['first_name','last_name','address_1','city','postcode','country','email','phone'] as $k){if(empty($billing[$k])) return new WP_Error('autoid_missing_'.$k,'Completează toate câmpurile obligatorii.',['status'=>400]);}
        foreach(['first_name','last_name','address_1','city','postcode','country'] as $k){if(empty($shipping[$k])) return new WP_Error('autoid_missing_shipping_'.$k,'Completează adresa de livrare.',['status'=>400]);}
        try{
            $uid=self::bearer_user_id($r);
            $clean_b=[];foreach(['first_name','last_name','company','address_1','address_2','city','state','postcode','country','email','phone'] as $k)$clean_b[$k]=sanitize_text_field((string)($billing[$k]??''));$clean_b['email']=sanitize_email((string)($billing['email']??''));
            $clean_s=[];foreach(['first_name','last_name','company','address_1','address_2','city','state','postcode','country'] as $k)$clean_s[$k]=sanitize_text_field((string)($shipping[$k]??''));
            $vat=sanitize_text_field((string)($body['vat_number']??''));
            $create_account=!$uid&&!empty($body['create_account']);$account_created=false;$new_token='';
            if($create_account){
                if(email_exists($clean_b['email'])) return new WP_Error('autoid_account_exists','Există deja un cont AutoID pentru acest email. Autentifică-te sau debifează „Creează un cont AutoID”.',['status'=>409]);
                $new_uid=wc_create_new_customer($clean_b['email']);if(is_wp_error($new_uid))return $new_uid;$uid=(int)$new_uid;$account_created=true;$new_token=self::issue_token($uid);
            }
            $order=wc_create_order(['customer_id'=>$uid?:0]);
            foreach($lines as $line){$pid=absint($line['product_id']??0);$qty=max(1,absint($line['quantity']??1));$product=wc_get_product($pid);if(!$product||$product->get_status()!=='publish')continue;$order->add_product($product,$qty);}
            if(!$order->get_items())throw new Exception('Nu există produse valide în comandă.');
            $order->set_address($clean_b,'billing');$order->set_address($clean_s,'shipping');
            $order->update_meta_data('_wc_order_attribution_source_type','mobile_app');
            $order->update_meta_data('_wc_order_attribution_device_type','Mobile');
            $order->update_meta_data('_wc_order_attribution_user_agent','AutoID-Android/1.0.16');
            $order->update_meta_data('_autoid_order_source','android_app');
            $order->update_meta_data('_autoid_app_version','1.0.16');
            if($vat!==''){
                $order->update_meta_data('_eu_vat_guard_order_vat_number',$vat);
                $order->update_meta_data('billing_vat',$vat);$order->update_meta_data('_billing_vat',$vat);$order->update_meta_data('vat_number',$vat);
            }
            $review=!empty($body['review_consent']);$order->update_meta_data('_autoid_review_consent',$review?'yes':'no');if($review)$order->update_meta_data('_autoid_review_consent_at',current_time('mysql'));
            $notes=sanitize_textarea_field((string)($body['customer_note']??''));if($notes!=='')$order->set_customer_note($notes);
            if($uid){
                $customer=new WC_Customer($uid);
                foreach($clean_b as $field=>$value){$method='set_billing_'.$field;if(method_exists($customer,$method))$customer->$method($value);}
                foreach($clean_s as $field=>$value){$method='set_shipping_'.$field;if(method_exists($customer,$method))$customer->$method($value);}
                if(method_exists($customer,'set_first_name'))$customer->set_first_name($clean_b['first_name']);if(method_exists($customer,'set_last_name'))$customer->set_last_name($clean_b['last_name']);$customer->save();
                if($vat!==''){update_user_meta($uid,'_eu_vat_guard_vat_number',$vat);update_user_meta($uid,'billing_vat',$vat);update_user_meta($uid,'vat_number',$vat);}
                if($clean_b['company']!=='')update_user_meta($uid,'_eu_vat_guard_company_name',$clean_b['company']);
            }
            $gateways=WC()->payment_gateways()?WC()->payment_gateways()->payment_gateways():[];if(isset($gateways[$payment]))$order->set_payment_method($gateways[$payment]);else$order->set_payment_method($payment);
            $order->calculate_totals();
            $cfg=self::mobile_shipping_config();$before_shipping=(float)$order->get_total();$free=(float)$cfg['free_shipping_min']>0 && $before_shipping>=(float)$cfg['free_shipping_min'];
            $ship_item=new WC_Order_Item_Shipping();$ship_item->set_method_title($free?'Livrare gratuită':(string)$cfg['title']);$ship_item->set_method_id($free?'free_shipping:autoid-mobile':'flat_rate:autoid-mobile');$ship_item->set_total($free?0:(float)$cfg['flat_rate_ex_vat']);
            if(!$free&&!empty($cfg['taxable'])&&class_exists('WC_Tax')){$rates=WC_Tax::get_base_tax_rates('');if($rates)$ship_item->set_taxes(['total'=>WC_Tax::calc_tax((float)$cfg['flat_rate_ex_vat'],$rates,false)]);}
            $order->add_item($ship_item);$order->calculate_totals(false);$order->save();
            if($payment==='cod')$order->update_status('processing','Comandă plasată din aplicația AutoID Android cu plata ramburs.');elseif($payment==='bacs')$order->update_status('on-hold','Comandă plasată din aplicația AutoID Android cu transfer bancar.');
            return rest_ensure_response(['order_id'=>$order->get_id(),'number'=>$order->get_order_number(),'status'=>$order->get_status(),'total'=>$order->get_total(),'currency'=>$order->get_currency(),'payment_method'=>$payment,'requires_payment'=>$payment==='stripe','shipping_total'=>$order->get_shipping_total(),'tax_total'=>$order->get_total_tax(),'review_consent'=>$review,'account_created'=>$account_created,'access_token'=>$new_token,'customer'=>$uid?self::customer_payload($uid):null,'origin'=>'Android App']);
        }catch(Throwable $e){return new WP_Error('autoid_checkout_failed',$e->getMessage(),['status'=>500]);}
    }

'''
s=s[:start]+checkout+s[end:]

# Register route saves VAT using the exact EU VAT Guard user meta key as well.
old="$vat=sanitize_text_field((string)($b['vat_number']??''));if($vat!==''){update_user_meta($id,'billing_vat',$vat);update_user_meta($id,'vat_number',$vat);}"
new="$vat=sanitize_text_field((string)($b['vat_number']??''));if($vat!==''){update_user_meta($id,'_eu_vat_guard_vat_number',$vat);update_user_meta($id,'billing_vat',$vat);update_user_meta($id,'vat_number',$vat);}"
if old not in s: raise SystemExit('register VAT anchor missing')
s=s.replace(old,new,1)

# Account address payload now includes the VAT number so Android can prefill the checkout.
old="return rest_ensure_response(['billing'=>self::account_address_payload($customer,'billing'),'shipping'=>self::account_address_payload($customer,'shipping')]);"
new="$vat=(string)get_user_meta($uid,'_eu_vat_guard_vat_number',true);if($vat==='')$vat=(string)get_user_meta($uid,'billing_vat',true);if($vat==='')$vat=(string)get_user_meta($uid,'vat_number',true);return rest_ensure_response(['billing'=>self::account_address_payload($customer,'billing'),'shipping'=>self::account_address_payload($customer,'shipping'),'vat_number'=>$vat]);"
if old not in s: raise SystemExit('me addresses response anchor missing')
s=s.replace(old,new,1)

p.write_text(s)
print('Patched AutoID Mobile v1.1.7: EU VAT Guard, Android origin, account creation and address hydration')
