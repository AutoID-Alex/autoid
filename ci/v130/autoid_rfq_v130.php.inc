    private static function rfq_statuses_v130() {
        return [
            'noua'=>'Nouă','analiza'=>'În analiză','oferta_trimisa'=>'Ofertă trimisă · așteaptă răspuns',
            'oferta_acceptata'=>'Ofertă acceptată','oferta_refuzata'=>'Ofertă refuzată',
            'proforma_trimisa'=>'Proformă trimisă · așteaptă plata','platita'=>'Plătită · așteaptă factura',
            'castigata'=>'Câștigată','inchisa'=>'Închisă · facturată',
        ];
    }

    private static function rfq_status_label_v130($status) {
        $map=self::rfq_statuses_v130();
        return $map[$status]??$map['noua'];
    }

    private static function rfq_owner_v130($rfq_id,$user_id) {
        if($rfq_id<=0||$user_id<=0||get_post_type($rfq_id)!=='autoid_rfq')return false;
        $stored=absint(get_post_meta($rfq_id,'_autoid_rfq_user_id',true));
        if($stored>0)return $stored===$user_id;
        $r=get_post_meta($rfq_id,'_autoid_rfq_requester',true);
        return is_array($r)&&absint($r['user_id']??0)===$user_id;
    }

    private static function rfq_product_value_v130($product) {
        if(!$product instanceof WC_Product)return 0.0;
        if($product->is_type('grouped')){
            $values=[];
            foreach((array)$product->get_children() as $child_id){$child=wc_get_product($child_id);$v=self::rfq_product_value_v130($child);if($v>0)$values[]=$v;}
            return $values?min($values):0.0;
        }
        if($product->is_type('variable')&&method_exists($product,'get_variation_price'))return max(0.0,(float)$product->get_variation_price('min',true));
        $raw=(float)$product->get_price();
        return $raw>0?max(0.0,(float)wc_get_price_including_tax($product,['price'=>$raw])):0.0;
    }

    public static function rfq_create_v130(WP_REST_Request $r) {
        $ok=self::require_wc();if(is_wp_error($ok))return $ok;
        if(!post_type_exists('autoid_rfq'))return new WP_Error('autoid_rfq_backend_missing','Modulul RFQ AutoID nu este activ.',['status'=>503]);
        $uid=absint($r->get_param('_autoid_user_id'));if(!$uid)$uid=self::bearer_user_id($r);
        $b=$r->get_json_params();if(!is_array($b))$b=[];
        $note=sanitize_textarea_field((string)($b['note']??''));
        if($note==='')return new WP_Error('autoid_rfq_note_required','Nota cererii este obligatorie.',['status'=>400]);
        $raw_items=is_array($b['items']??null)?$b['items']:[];$items=[];
        foreach($raw_items as $raw){
            $product_id=absint($raw['product_id']??$raw['id']??0);$qty=max(1,min(9999,absint($raw['quantity']??$raw['qty']??1)));
            $product=$product_id?wc_get_product($product_id):false;if(!$product||!$product->is_visible())continue;
            $unit=self::rfq_product_value_v130($product);
            $items[]=['product_id'=>$product_id,'sku'=>(string)$product->get_sku(),'name'=>(string)$product->get_name(),'qty'=>$qty,
                'url'=>get_permalink($product_id),'estimated_unit_value'=>$unit,'estimated_line_value'=>round($unit*$qty,wc_get_price_decimals())];
        }
        if(!$items)return new WP_Error('autoid_rfq_items_required','Adaugă cel puțin un produs disponibil.',['status'=>400]);
        $user=$uid?get_userdata($uid):false;if($uid&&!$user)return new WP_Error('autoid_user_missing','Contul nu mai este disponibil.',['status'=>401]);
        $first=sanitize_text_field((string)($b['first_name']??($uid?(get_user_meta($uid,'billing_first_name',true)?:$user->first_name):'')));
        $last=sanitize_text_field((string)($b['last_name']??($uid?(get_user_meta($uid,'billing_last_name',true)?:$user->last_name):'')));
        $email=sanitize_email((string)($b['email']??($uid?$user->user_email:'')));
        $phone=sanitize_text_field((string)($b['phone']??($uid?get_user_meta($uid,'billing_phone',true):'')));
        $company=sanitize_text_field((string)($b['company']??($uid?get_user_meta($uid,'billing_company',true):'')));
        $vat=sanitize_text_field((string)($b['vat']??($uid?get_user_meta($uid,'billing_vat_number',true):'')));
        if($first===''||$last===''||!is_email($email)||$phone==='')return new WP_Error('autoid_rfq_requester_required','Completează prenumele, numele, emailul și telefonul.',['status'=>400]);
        $requester=['user_id'=>$uid,'first_name'=>$first,'last_name'=>$last,'email'=>$email,'phone'=>$phone,'company'=>$company,'vat'=>$vat];
        $post_id=wp_insert_post(['post_type'=>'autoid_rfq','post_status'=>'private','post_title'=>'Cerere ofertă AutoID'],true);
        if(is_wp_error($post_id))return new WP_Error('autoid_rfq_save_failed','Cererea nu a putut fi salvată.',['status'=>500]);
        $code='RFQ-'.wp_date('ymd').'-'.str_pad((string)$post_id,5,'0',STR_PAD_LEFT);
        wp_update_post(['ID'=>$post_id,'post_title'=>$code]);
        $value=round(array_sum(array_map(static fn($x)=>(float)($x['estimated_line_value']??0),$items)),wc_get_price_decimals());
        foreach(['_autoid_rfq_code'=>$code,'_autoid_rfq_status'=>'noua','_autoid_rfq_requester'=>$requester,'_autoid_rfq_user_id'=>$uid,
            '_autoid_rfq_items'=>$items,'_autoid_rfq_note'=>$note,'_autoid_rfq_consent'=>1,'_autoid_rfq_create_account'=>0,
            '_autoid_rfq_source_url'=>'autoid://android/rfq','_autoid_rfq_estimated_value'=>$value,'_autoid_rfq_estimated_currency'=>get_woocommerce_currency()] as $key=>$val)update_post_meta($post_id,$key,$val);
        $subject='['.$code.'] Cerere de ofertă din aplicația AutoID';
        $body="Solicitant: {$first} {$last}\nEmail: {$email}\nTelefon: {$phone}\nCompanie: {$company}\nCod TVA: {$vat}\n\nProduse:\n";
        foreach($items as $item)$body.=$item['qty'].' × '.$item['name'].' (SKU '.$item['sku'].")\n";
        $body.="\nNotă:\n".$note."\n\n".admin_url('post.php?post='.$post_id.'&action=edit');
        wp_mail((string)get_option('admin_email'),$subject,$body);
        $payload=self::rfq_payload_v130($post_id,$uid);
        if(!$payload)$payload=['id'=>$post_id,'reference'=>$code,'status'=>'noua','status_label'=>self::rfq_status_label_v130('noua'),'created_at'=>current_time('c'),'estimated_value'=>$value,'currency'=>get_woocommerce_currency(),'items'=>$items,'requester'=>$requester,'note'=>$note,'timeline'=>[['key'=>'created','label'=>'Cerere înregistrată','at'=>current_time('c')]],'documents'=>[],'payments'=>[],'can_accept'=>false,'can_reject'=>false];
        return new WP_REST_Response($payload,201);
    }

    private static function rfq_document_row_v130($rfq_id,$kind) {
        $map=['offer'=>['_autoid_rfq_offer_pdf_id','_autoid_rfq_offer_sent_at','Ofertă comercială'],
            'proforma'=>['_autoid_rfq_proforma_pdf_id','_autoid_rfq_proforma_sent_at','Proformă'],
            'invoice'=>['_autoid_rfq_invoice_pdf_id','_autoid_rfq_invoice_sent_at','Factură finală']];
        if(!isset($map[$kind]))return [];
        [$id_key,$sent_key,$label]=$map[$kind];$attachment_id=absint(get_post_meta($rfq_id,$id_key,true));$sent=(string)get_post_meta($rfq_id,$sent_key,true);
        $file=$attachment_id?get_attached_file($attachment_id):'';
        if($sent===''||!$file||!is_readable($file)||get_post_mime_type($attachment_id)!=='application/pdf')return [];
        return ['kind'=>$kind,'label'=>$label,'sent_at'=>mysql_to_rfc3339($sent),'download_path'=>'/me/rfqs/'.$rfq_id.'/documents/'.$kind,'attachment_id'=>$attachment_id,'file'=>$file];
    }

    private static function rfq_timeline_v130($rfq_id,$status) {
        $post=get_post($rfq_id);$events=[];
        if($post)$events[]=['key'=>'created','label'=>'Cerere înregistrată','at'=>mysql_to_rfc3339($post->post_date_gmt?:$post->post_date)];
        $map=[['_autoid_rfq_offer_sent_at','offer_sent','Ofertă trimisă'],['_autoid_rfq_offer_responded_at','offer_response','Răspuns ofertă înregistrat'],
            ['_autoid_rfq_proforma_sent_at','proforma_sent','Proformă trimisă'],['_autoid_rfq_paid_at','paid','Plată confirmată'],['_autoid_rfq_invoice_sent_at','invoice_sent','Factură trimisă']];
        foreach($map as [$meta,$key,$label]){$at=(string)get_post_meta($rfq_id,$meta,true);if($at!=='')$events[]=['key'=>$key,'label'=>$label,'at'=>mysql_to_rfc3339($at)];}
        $events[]=['key'=>'current','label'=>self::rfq_status_label_v130($status),'at'=>''];
        return $events;
    }

    private static function rfq_payload_v130($rfq_id,$uid) {
        if(!self::rfq_owner_v130($rfq_id,$uid))return null;
        $post=get_post($rfq_id);$status=(string)get_post_meta($rfq_id,'_autoid_rfq_status',true)?:'noua';
        $requester=get_post_meta($rfq_id,'_autoid_rfq_requester',true);if(!is_array($requester))$requester=[];
        $stored=get_post_meta($rfq_id,'_autoid_rfq_items',true);$stored=is_array($stored)?$stored:[];$items=[];
        foreach($stored as $item){$pid=absint($item['product_id']??0);$product=$pid?wc_get_product($pid):false;$items[]=[
            'product_id'=>$pid,'sku'=>(string)($item['sku']??($product?$product->get_sku():'')),'name'=>(string)($item['name']??($product?$product->get_name():'')),
            'quantity'=>max(1,absint($item['qty']??1)),'url'=>(string)($item['url']??($pid?get_permalink($pid):'')),
            'image'=>$product&&$product->get_image_id()?wp_get_attachment_image_url($product->get_image_id(),'woocommerce_thumbnail'):'',
            'unit_value'=>(float)($item['estimated_unit_value']??0),'line_value'=>(float)($item['estimated_line_value']??0)];}
        $docs=[];foreach(['offer','proforma','invoice'] as $kind){$d=self::rfq_document_row_v130($rfq_id,$kind);if($d){unset($d['attachment_id'],$d['file']);$docs[]=$d;}}
        $bank=(bool)get_post_meta($rfq_id,'_autoid_rfq_payment_bank',true);$card=(bool)get_post_meta($rfq_id,'_autoid_rfq_payment_card',true);
        $card_url=esc_url_raw((string)get_post_meta($rfq_id,'_autoid_rfq_card_payment_url',true));
        if($card_url==='' )$card_url=esc_url_raw((string)get_post_meta($rfq_id,'_autoid_rfq_stripe_payment_url',true));
        $proforma_sent=(string)get_post_meta($rfq_id,'_autoid_rfq_proforma_sent_at',true)!=='';$payments=[];
        $code=(string)get_post_meta($rfq_id,'_autoid_rfq_code',true)?:get_the_title($rfq_id);
        if($proforma_sent&&$bank)$payments[]=['type'=>'bank_transfer','label'=>'Transfer bancar','reference'=>$code,'beneficiary'=>'SOFA SOFT SRL','registration'=>'J35/730/1997','vat'=>'RO9601390','address'=>'Strada Florentina, Nr. 16, 307285 Moșnița Nouă, TM','ibans'=>[['iban'=>'RO07INGB0001008225758911','bank'=>'ING BANK N.V. AMSTERDAM SUC. BUCURESTI'],['iban'=>'RO27CITI0000000706842004','bank'=>'CITIBANK EUROPE PLC DUBLIN - SUC. ROMANIA']]];
        if($proforma_sent&&$card&&$card_url!=='')$payments[]=['type'=>'card','label'=>'Plată cu cardul','url'=>$card_url];
        $response=(string)get_post_meta($rfq_id,'_autoid_rfq_offer_response',true);
        return ['id'=>$rfq_id,'reference'=>$code,'status'=>$status,'status_label'=>self::rfq_status_label_v130($status),
            'created_at'=>$post?mysql_to_rfc3339($post->post_date_gmt?:$post->post_date):'',
            'estimated_value'=>(float)get_post_meta($rfq_id,'_autoid_rfq_estimated_value',true),'currency'=>(string)get_post_meta($rfq_id,'_autoid_rfq_estimated_currency',true)?:get_woocommerce_currency(),
            'items'=>$items,'requester'=>$requester,'note'=>(string)get_post_meta($rfq_id,'_autoid_rfq_note',true),
            'timeline'=>self::rfq_timeline_v130($rfq_id,$status),'documents'=>$docs,'payments'=>$payments,
            'offer_response'=>$response,'can_accept'=>$status==='oferta_trimisa'&&$response==='','can_reject'=>$status==='oferta_trimisa'&&$response===''];
    }

    public static function rfq_list_v130(WP_REST_Request $r) {
        $uid=absint($r->get_param('_autoid_user_id'));$page=max(1,absint($r->get_param('page')));$per=max(1,min(30,absint($r->get_param('per_page'))?:10));
        $legacy='s:7:"user_id";i:'.$uid.';';$q=new WP_Query(['post_type'=>'autoid_rfq','post_status'=>['private','publish'],'posts_per_page'=>$per,'paged'=>$page,'orderby'=>'date','order'=>'DESC','meta_query'=>['relation'=>'OR',['key'=>'_autoid_rfq_user_id','value'=>$uid,'compare'=>'=','type'=>'NUMERIC'],['key'=>'_autoid_rfq_requester','value'=>$legacy,'compare'=>'LIKE']]]);
        $rows=[];foreach($q->posts as $post){$p=self::rfq_payload_v130((int)$post->ID,$uid);if($p)$rows[]=['id'=>$p['id'],'reference'=>$p['reference'],'status'=>$p['status'],'status_label'=>$p['status_label'],'created_at'=>$p['created_at'],'estimated_value'=>$p['estimated_value'],'currency'=>$p['currency'],'item_count'=>array_sum(array_map(static fn($x)=>(int)$x['quantity'],$p['items']))];}
        return rest_ensure_response(['items'=>$rows,'page'=>$page,'pages'=>(int)$q->max_num_pages,'total'=>(int)$q->found_posts]);
    }

    public static function rfq_detail_v130(WP_REST_Request $r) {
        $uid=absint($r->get_param('_autoid_user_id'));$id=absint($r['id']);$payload=self::rfq_payload_v130($id,$uid);
        return $payload?rest_ensure_response($payload):new WP_Error('autoid_rfq_not_found','Cererea nu a fost găsită.',['status'=>404]);
    }

    public static function rfq_action_v130(WP_REST_Request $r) {
        $uid=absint($r->get_param('_autoid_user_id'));$id=absint($r['id']);if(!self::rfq_owner_v130($id,$uid))return new WP_Error('autoid_rfq_not_found','Cererea nu a fost găsită.',['status'=>404]);
        $b=$r->get_json_params();$action=sanitize_key((string)($b['action']??''));if(!in_array($action,['accept','reject'],true))return new WP_Error('autoid_rfq_action_invalid','Acțiune RFQ invalidă.',['status'=>400]);
        $status=(string)get_post_meta($id,'_autoid_rfq_status',true);$locked=(string)get_post_meta($id,'_autoid_rfq_proforma_sent_at',true)!==''||(string)get_post_meta($id,'_autoid_rfq_paid_at',true)!=='';
        if($status!=='oferta_trimisa'||$locked||(string)get_post_meta($id,'_autoid_rfq_offer_response',true)!=='')return new WP_Error('autoid_rfq_conflict','Oferta nu mai poate fi modificată în etapa curentă.',['status'=>409]);
        $accepted=$action==='accept';update_post_meta($id,'_autoid_rfq_offer_response',$accepted?'acceptata':'refuzata');update_post_meta($id,'_autoid_rfq_offer_responded_at',current_time('mysql'));update_post_meta($id,'_autoid_rfq_offer_response_source','android-app');update_post_meta($id,'_autoid_rfq_status',$accepted?'oferta_acceptata':'oferta_refuzata');
        $code=(string)get_post_meta($id,'_autoid_rfq_code',true);wp_mail((string)get_option('admin_email'),'['.$code.'] Oferta '.($accepted?'acceptată':'refuzată').' din aplicația AutoID','Clientul a '.($accepted?'acceptat':'refuzat').' oferta. '.admin_url('post.php?post='.$id.'&action=edit'));
        return rest_ensure_response(self::rfq_payload_v130($id,$uid));
    }

    public static function rfq_document_v130(WP_REST_Request $r) {
        $uid=absint($r->get_param('_autoid_user_id'));$id=absint($r['id']);if(!self::rfq_owner_v130($id,$uid))return new WP_Error('autoid_rfq_not_found','Documentul nu a fost găsit.',['status'=>404]);
        $doc=self::rfq_document_row_v130($id,sanitize_key((string)$r['kind']));if(!$doc)return new WP_Error('autoid_rfq_document_missing','Documentul nu este disponibil.',['status'=>404]);
        nocache_headers();header('Content-Type: application/pdf');header('Content-Disposition: attachment; filename="'.sanitize_file_name(wp_basename($doc['file'])).'"');header('Content-Length: '.filesize($doc['file']));readfile($doc['file']);exit;
    }

    public static function rfq_meta_changed_v130($meta_id,$object_id,$meta_key,$meta_value) {
        if($meta_key!=='_autoid_rfq_status'||get_post_type($object_id)!=='autoid_rfq')return;
        $status=sanitize_key((string)$meta_value);if((string)get_post_meta($object_id,'_autoid_rfq_push_status_v130',true)===$status)return;
        update_post_meta($object_id,'_autoid_rfq_push_status_v130',$status);$uid=absint(get_post_meta($object_id,'_autoid_rfq_user_id',true));if(!$uid)return;
        $prefs=self::privacy_for_user_v128($uid);if(empty($prefs['transactional_notifications']))return;$tokens=get_user_meta($uid,'_autoid_fcm_tokens_v128',true);if(!is_array($tokens))return;
        $code=(string)get_post_meta($object_id,'_autoid_rfq_code',true)?:get_the_title($object_id);$label=self::rfq_status_label_v130($status);
        $data=['type'=>'rfq_status','rfq_id'=>(string)$object_id,'title'=>$code.' · '.$label,'body'=>'Cererea ta de ofertă AutoID a fost actualizată.','status'=>$status,'deep_link'=>'autoid://account/rfq/'.$object_id,'notification_id'=>(string)(300000+($object_id%100000))];
        foreach($tokens as $x){$token=is_array($x)?self::clean_fcm_token_v128($x['token']??''):'';if($token!=='')self::fcm_send_token_v128($uid,$token,$data);}
    }
