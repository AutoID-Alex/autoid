from pathlib import Path
p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()

def must(old,new,label):
    global s
    if old not in s: raise SystemExit(label+' anchor missing')
    s=s.replace(old,new,1)

must('Version: 1.1.8','Version: 1.1.9','plugin version')
must("'bridge_version'=>'1.1.8'","'bridge_version'=>'1.1.9'",'bridge version')

# Checkout: actual delivery vs local pickup.
must("$billing=is_array($body['billing']??null)?$body['billing']:[];$shipping=is_array($body['shipping']??null)?$body['shipping']:$billing;",
     "$billing=is_array($body['billing']??null)?$body['billing']:[];$shipping=is_array($body['shipping']??null)?$body['shipping']:$billing;$delivery_mode=sanitize_key((string)($body['delivery_mode']??'delivery'));if(!in_array($delivery_mode,['delivery','pickup'],true))$delivery_mode='delivery';",'delivery mode')
must("foreach(['first_name','last_name','address_1','city','postcode','country'] as $k){if(empty($shipping[$k])) return new WP_Error('autoid_missing_shipping_'.$k,'Completează adresa de livrare.',['status'=>400]);}",
     "if($delivery_mode==='delivery')foreach(['first_name','last_name','address_1','city','postcode','country'] as $k){if(empty($shipping[$k])) return new WP_Error('autoid_missing_shipping_'.$k,'Completează adresa de livrare.',['status'=>400]);}", 'shipping validation')
must("$clean_s=[];foreach(['first_name','last_name','company','address_1','address_2','city','state','postcode','country'] as $k)$clean_s[$k]=sanitize_text_field((string)($shipping[$k]??''));",
     "$clean_s=[];foreach(['first_name','last_name','company','address_1','address_2','city','state','postcode','country'] as $k)$clean_s[$k]=sanitize_text_field((string)(($delivery_mode==='pickup'?$billing:$shipping)[$k]??''));",'shipping clean')
must("$order->update_meta_data('_wc_order_attribution_user_agent','AutoID-Android/1.0.16');", "$order->update_meta_data('_wc_order_attribution_user_agent','AutoID-Android/1.0.19');",'order UA')
must("$order->update_meta_data('_autoid_app_version','1.0.16');", "$order->update_meta_data('_autoid_app_version','1.0.19');$order->update_meta_data('_autoid_delivery_mode',$delivery_mode);",'app version/meta')
old_ship="$cfg=self::mobile_shipping_config();$before_shipping=(float)$order->get_total();$free=(float)$cfg['free_shipping_min']>0 && $before_shipping>=(float)$cfg['free_shipping_min'];\n            $ship_item=new WC_Order_Item_Shipping();$ship_item->set_method_title($free?'Livrare gratuită':(string)$cfg['title']);$ship_item->set_method_id($free?'free_shipping:autoid-mobile':'flat_rate:autoid-mobile');$ship_item->set_total($free?0:(float)$cfg['flat_rate_ex_vat']);\n            if(!$free&&!empty($cfg['taxable'])&&class_exists('WC_Tax')){$rates=WC_Tax::get_base_tax_rates('');if($rates)$ship_item->set_taxes(['total'=>WC_Tax::calc_tax((float)$cfg['flat_rate_ex_vat'],$rates,false)]);}\n            $order->add_item($ship_item);$order->calculate_totals(false);$order->save();"
new_ship="$cfg=self::mobile_shipping_config();$before_shipping=(float)$order->get_total();$free=$delivery_mode==='pickup'||((float)$cfg['free_shipping_min']>0 && $before_shipping>=(float)$cfg['free_shipping_min']);\n            $ship_item=new WC_Order_Item_Shipping();if($delivery_mode==='pickup'){$ship_item->set_method_title('Ridicare din Depozit');$ship_item->set_method_id('local_pickup:autoid-mobile');$ship_item->set_total(0);}else{$ship_item->set_method_title($free?'Livrare gratuită':(string)$cfg['title']);$ship_item->set_method_id($free?'free_shipping:autoid-mobile':'flat_rate:autoid-mobile');$ship_item->set_total($free?0:(float)$cfg['flat_rate_ex_vat']);if(!$free&&!empty($cfg['taxable'])&&class_exists('WC_Tax')){$rates=WC_Tax::get_base_tax_rates('');if($rates)$ship_item->set_taxes(['total'=>WC_Tax::calc_tax((float)$cfg['flat_rate_ex_vat'],$rates,false)]);}}\n            $order->add_item($ship_item);$order->calculate_totals(false);$order->save();"
must(old_ship,new_ship,'shipping calculation')
must("'origin'=>'Android App'])", "'origin'=>'Android App','delivery_mode'=>$delivery_mode])",'checkout response')

# Tracking helper + lightweight order list. AWB_GLS drives the shipping stage.
marker='    public static function me_orders(WP_REST_Request $r) {'
helper='''    private static function order_tracking_payload($order) {\n        $awb=trim((string)$order->get_meta('AWB_GLS',true));\n        if($awb==='')$awb=trim((string)$order->get_meta('_AWB_GLS',true));\n        if($awb==='')return ['carrier'=>'','tracking_number'=>'','tracking_url'=>''];\n        return ['carrier'=>'GLS','tracking_number'=>$awb,'tracking_url'=>'https://gls-group.eu/RO/ro/urmarire-colet.html?match='.rawurlencode($awb)];\n    }\n\n'''
if helper not in s:
    if marker not in s: raise SystemExit('me_orders marker missing')
    s=s.replace(marker,helper+marker,1)

old_orders="""        $orders=wc_get_orders(['customer_id'=>$uid,'limit'=>50,'orderby'=>'date','order'=>'DESC']);\n        $rows=[];\n        foreach($orders as $o){$rows[]=['id'=>$o->get_id(),'number'=>$o->get_order_number(),'status'=>$o->get_status(),'status_label'=>wc_get_order_status_name($o->get_status()),'total'=>$o->get_total(),'currency'=>$o->get_currency(),'created_at'=>$o->get_date_created()?$o->get_date_created()->date('c'):null];}\n"""
new_orders="""        $orders=wc_get_orders(['customer_id'=>$uid,'limit'=>20,'orderby'=>'date','order'=>'DESC']);\n        $rows=[];\n        foreach($orders as $o){$tracking=self::order_tracking_payload($o);$rows[]=['id'=>$o->get_id(),'number'=>$o->get_order_number(),'status'=>$o->get_status(),'status_label'=>wc_get_order_status_name($o->get_status()),'total'=>$o->get_total(),'currency'=>$o->get_currency(),'created_at'=>$o->get_date_created()?$o->get_date_created()->date('c'):null]+$tracking;}\n"""
must(old_orders,new_orders,'order list')

new_detail="$tracking=self::order_tracking_payload($order);return rest_ensure_response(['id'=>$order->get_id(),'number'=>$order->get_order_number(),'status'=>$order->get_status(),'status_label'=>wc_get_order_status_name($order->get_status()),'created_at'=>$order->get_date_created()?$order->get_date_created()->date('c'):'','currency'=>$order->get_currency(),'subtotal'=>(string)$subtotal_incl,'discount_total'=>(string)((float)$order->get_discount_total()+(float)$order->get_discount_tax()),'shipping_total'=>(string)((float)$order->get_shipping_total()+(float)$order->get_shipping_tax()),'tax_total'=>(string)$order->get_total_tax(),'total'=>(string)$order->get_total(),'payment_method'=>$order->get_payment_method_title(),'shipping_method'=>implode(', ',$ship),'customer_note'=>$order->get_customer_note(),'carrier'=>$tracking['carrier'],'tracking_number'=>$tracking['tracking_number'],'tracking_url'=>$tracking['tracking_url'],'billing'=>$billing,'shipping'=>$shipping,'items'=>$items,'notes'=>$notes]);"
# Replace whole return tail safely by locating the original return statement prefix.
orig_prefix="return rest_ensure_response(['id'=>$order->get_id(),'number'=>$order->get_order_number(),'status'=>$order->get_status()"
pos=s.find(orig_prefix,s.find('public static function me_order_detail'))
if pos<0: raise SystemExit('order detail return missing')
end=s.find("'notes'=>$notes]);",pos)
if end<0: raise SystemExit('order detail return end missing')
end += len("'notes'=>$notes]);")
s=s[:pos]+new_detail+s[end:]

p.write_text(s)
print('Patched AutoID Mobile v1.1.9: delivery/pickup, AWB_GLS tracking and leaner order list')
