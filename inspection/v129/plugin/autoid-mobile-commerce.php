<?php
/**
 * Plugin Name: AutoID Mobile
 * Description: Unified mobile gateway for the AutoID Android/iOS apps: catalog, search, support, authentication, account, orders, checkout, Google Sign-In and native payment infrastructure.
 * Version: 1.1.17
 * Author: AutoID / SOFA SOFT SRL
 * Requires at least: 6.5
 * Requires PHP: 8.0
 * WC requires at least: 9.0
 */

if (!defined('ABSPATH')) exit;

final class AutoID_Mobile_115 {
    const NS = 'autoid-app/v1';
    const CACHE_TTL = 600;

    public static function boot() {
        add_action('rest_api_init', [__CLASS__, 'routes']);
        add_action('admin_menu', [__CLASS__, 'hero_studio_menu'], 90);
        add_action('admin_menu', [__CLASS__, 'admin_menu']);
        add_action('admin_init', [__CLASS__, 'admin_init']); // autoid_mobile_hero
        add_filter('wc_order_attribution_origin_formatted_source', [__CLASS__, 'order_origin_source'], 10, 2);
        add_action('woocommerce_order_status_changed',[__CLASS__,'fcm_order_status_changed_v128'],20,4);
        add_action('woocommerce_after_order_object_save',[__CLASS__,'fcm_order_saved_v128'],30,1);
        add_action('added_post_meta',[__CLASS__,'fcm_meta_changed_v128'],30,4);
        add_action('updated_post_meta',[__CLASS__,'fcm_meta_changed_v128'],30,4);
    }

    public static function routes() {
        $public = ['permission_callback' => '__return_true'];
        register_rest_route(self::NS, '/home', $public + ['methods'=>'GET','callback'=>[__CLASS__,'home']]);
        register_rest_route(self::NS, '/hero', $public + ['methods'=>'GET','callback'=>[__CLASS__,'hero_live']]);
        register_rest_route(self::NS, '/products', $public + ['methods'=>'GET','callback'=>[__CLASS__,'products']]);
        register_rest_route(self::NS, '/products/(?P<id>\d+)', $public + ['methods'=>'GET','callback'=>[__CLASS__,'product']]);
        register_rest_route(self::NS, '/products/(?P<id>\d+)/family', $public + ['methods'=>'GET','callback'=>[__CLASS__,'family']]);
        register_rest_route(self::NS, '/products/(?P<id>\d+)/reviews', $public + ['methods'=>['GET','POST'],'callback'=>[__CLASS__,'product_reviews']]);
        register_rest_route(self::NS, '/products/(?P<id>\d+)/family/(?P<group>[a-z-]+)', $public + ['methods'=>'GET','callback'=>[__CLASS__,'family_group']]);
        register_rest_route(self::NS, '/products/(?P<id>\d+)/support', $public + ['methods'=>'GET','callback'=>[__CLASS__,'product_support']]);
        register_rest_route(self::NS, '/categories', $public + ['methods'=>'GET','callback'=>[__CLASS__,'categories']]);
        register_rest_route(self::NS, '/checkout/config', $public + ['methods'=>'GET','callback'=>[__CLASS__,'checkout_config']]);
        register_rest_route(self::NS, '/checkout/order', $public + ['methods'=>'POST','callback'=>[__CLASS__,'checkout_order']]);
        register_rest_route(self::NS, '/register', $public + ['methods'=>'POST','callback'=>[__CLASS__,'register_customer']]);
        register_rest_route(self::NS, '/search', $public + ['methods'=>'GET','callback'=>[__CLASS__,'search']]);
        register_rest_route(self::NS, '/support', $public + ['methods'=>'GET','callback'=>[__CLASS__,'support']]);
        register_rest_route(self::NS, '/brands', $public + ['methods'=>'GET','callback'=>[__CLASS__,'brands']]);
        register_rest_route(self::NS, '/navigation', $public + ['methods'=>'GET','callback'=>[__CLASS__,'navigation']]);
        register_rest_route(self::NS, '/ai/chat', $public + ['methods'=>'POST','callback'=>[__CLASS__,'ai_chat']]);
        register_rest_route(self::NS, '/content', $public + ['methods'=>'GET','callback'=>[__CLASS__,'content']]);
        register_rest_route(self::NS, '/catalog/facets', $public + ['methods'=>'GET','callback'=>[__CLASS__,'catalog_facets']]);
        register_rest_route(self::NS, '/rfq', $public + ['methods'=>'POST','callback'=>[__CLASS__,'rfq']]);
        register_rest_route(self::NS, '/consultation/request', $public + ['methods'=>'POST','callback'=>[__CLASS__,'consultation_request']]);
        register_rest_route(self::NS, '/health', $public + ['methods'=>'GET','callback'=>[__CLASS__,'health']]);
        register_rest_route(self::NS, '/push/config', $public + ['methods'=>'GET','callback'=>[__CLASS__,'push_config_v128']]);
        register_rest_route(self::NS, '/auth/login', $public + ['methods'=>'POST','callback'=>[__CLASS__,'auth_login']]);
        register_rest_route(self::NS, '/auth/google', $public + ['methods'=>'POST','callback'=>[__CLASS__,'auth_google']]);
        register_rest_route(self::NS, '/me', ['methods'=>'GET','callback'=>[__CLASS__,'me'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/me/orders', ['methods'=>'GET','callback'=>[__CLASS__,'me_orders'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/me/orders/(?P<id>\d+)', ['methods'=>'GET','callback'=>[__CLASS__,'me_order_detail'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/me/orders/(?P<id>\d+)/action', ['methods'=>'POST','callback'=>[__CLASS__,'me_order_action_v127'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/push/register', ['methods'=>'POST','callback'=>[__CLASS__,'push_register_v128'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/push/unregister', ['methods'=>'POST','callback'=>[__CLASS__,'push_unregister_v128'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/me/privacy', ['methods'=>['GET','POST'],'callback'=>[__CLASS__,'me_privacy_v128'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/me/profile', ['methods'=>['GET','POST'],'callback'=>[__CLASS__,'me_profile'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/me/addresses', ['methods'=>['GET','POST'],'callback'=>[__CLASS__,'me_addresses'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/me/payment-methods', ['methods'=>['GET','POST'],'callback'=>[__CLASS__,'me_payment_methods'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/payments/intent', ['methods'=>'POST','callback'=>[__CLASS__,'payment_intent'],'permission_callback'=>[__CLASS__,'auth_permission']]);
        register_rest_route(self::NS, '/payments/stripe/confirm', $public + ['methods'=>'POST','callback'=>[__CLASS__,'stripe_confirm']]);
    }

    public static function order_origin_source($formatted_source,$source) {
        $mobile=__('Mobile app','woocommerce');
        if((string)$source===(string)$mobile || strtolower(trim((string)$source))==='mobile app') return 'Android App';
        return $formatted_source;
    }

    private static function require_wc() {
        if (!function_exists('wc_get_products')) {
            return new WP_Error('autoid_wc_unavailable', 'WooCommerce is unavailable.', ['status'=>503]);
        }
        return true;
    }

    private static function int_param($r, $key, $default, $min=1, $max=100) {
        $v = absint($r->get_param($key));
        if (!$v) $v = $default;
        return max($min, min($max, $v));
    }

    public static function home(WP_REST_Request $r) {
        $ok = self::require_wc(); if (is_wp_error($ok)) return $ok;
        $sections = [];

        // Main Home category sections remain grouped-only and sorted by effective AutoID stock.
        foreach (self::home_category_specs() as $spec) {
            $term = self::find_product_category($spec['name'], $spec['slugs']);
            if (!$term) continue;
            $q = new WP_Query([
                'post_type'=>'product','post_status'=>'publish','posts_per_page'=>250,
                'fields'=>'ids','no_found_rows'=>true,
                'tax_query'=>[['taxonomy'=>'product_cat','field'=>'term_id','terms'=>[(int)$term->term_id],'include_children'=>true]]
            ]);
            $rows=[];
            foreach($q->posts as $id){
                $p=wc_get_product((int)$id);
                if(!$p || !$p->is_visible() || !$p->is_type('grouped')) continue;
                $rows[]=['stock'=>self::grouped_autoid_stock($p),'row'=>self::product_row($p,false)];
            }
            usort($rows,fn($a,$b)=>($b['stock']<=>$a['stock']) ?: strcasecmp($a['row']['name'],$b['row']['name']));
            $sections[]=[
                'category'=>self::category_row($term),
                'products'=>array_values(array_map(fn($x)=>$x['row'],array_slice($rows,0,12))),
                'total_grouped'=>count($rows)
            ];
        }

        // "În stoc AutoID": one highest-stock product from every requested product family.
        // Important: only the product's own stock_autoid meta is accepted here (>0).
        $recommended=[];
        $manual_skus=self::home_selected_skus();
        if($manual_skus){
            foreach($manual_skus as $sku){
                $id=wc_get_product_id_by_sku($sku);
                if(!$id) continue;
                $p=wc_get_product((int)$id);
                if(!$p || !$p->is_visible()) continue;
                $recommended[]=self::product_row($p,false);
            }
        } else {
            foreach(self::home_stock_specs() as $spec){
                $term_ids=self::find_product_category_ids($spec['names'],$spec['slugs']);
                if(!$term_ids) continue;
                $q=new WP_Query([
                    'post_type'=>'product','post_status'=>'publish','posts_per_page'=>300,
                    'fields'=>'ids','no_found_rows'=>true,
                    'tax_query'=>[['taxonomy'=>'product_cat','field'=>'term_id','terms'=>$term_ids,'include_children'=>true]]
                ]);
                $pool=[];
                foreach($q->posts as $id){
                    $p=wc_get_product((int)$id);
                    if(!$p || !$p->is_visible()) continue;
                    $group=self::related_group($p);
                    if(in_array($group,['service','software'],true)) continue;
                    $stock=(int)(self::numeric_meta($p->get_id(),['stock_autoid','_stock_autoid','_autoid_stock','autoid_stock']) ?: 0);
                    if($stock<=0) continue;
                    $pool[]=['stock'=>$stock,'row'=>self::product_row($p,false)];
                }
                usort($pool,fn($a,$b)=>($b['stock']<=>$a['stock']) ?: strcasecmp($a['row']['name'],$b['row']['name']));
                if($pool) $recommended[]=$pool[0]['row'];
            }
        }

        // "Lichidări de stoc": random visible products only from the dedicated category.
        $liquidations=[];
        $liquidation_term=get_term_by('slug','lichidari-de-stoc','product_cat');
        if($liquidation_term && !is_wp_error($liquidation_term)){
            $q=new WP_Query([
                'post_type'=>'product','post_status'=>'publish','posts_per_page'=>150,
                'fields'=>'ids','no_found_rows'=>true,
                'tax_query'=>[['taxonomy'=>'product_cat','field'=>'term_id','terms'=>[(int)$liquidation_term->term_id],'include_children'=>false,'operator'=>'IN']]
            ]);
            $candidates=[];
            foreach($q->posts as $id){
                if(!has_term((int)$liquidation_term->term_id,'product_cat',(int)$id)) continue;
                $p=wc_get_product((int)$id);
                if(!$p || !$p->is_visible()) continue;
                $stock_autoid=(int)(self::numeric_meta($p->get_id(),['stock_autoid','_stock_autoid','_autoid_stock','autoid_stock']) ?: 0);
                if($stock_autoid<=0) continue;
                $candidates[]=$p;
            }
            if($candidates){
                shuffle($candidates);
                foreach(array_slice($candidates,0,12) as $p) $liquidations[]=self::product_row($p,false);
            }
        }

        return self::live_response([
            'app'=>['name'=>'AutoID','tagline'=>'Professional Solutions','version'=>'1.0.6'],
            'hero'=>['title'=>'Echipamente AutoID pentru afacerea ta','subtitle'=>'Scanare, etichetare, mobilitate, RFID și soluții profesionale.'],
            'hero_slides'=>self::hero_slides_public(),
            'sections'=>$sections,
            'recommended'=>array_values($recommended),
            'offers'=>array_values($liquidations),
            'liquidation_category'=>($liquidation_term && !is_wp_error($liquidation_term)) ? self::category_row($liquidation_term) : null,
            'hero_source'=>'autoid-mega-menu',
            'categories'=>self::category_rows(0),
            'brands'=>self::brand_rows(24)
        ]);
    }

    private static function home_stock_specs(){
        return [
            ['names'=>['Imprimante de etichete'],'slugs'=>['imprimante-de-etichete']],
            ['names'=>['Terminale mobile'],'slugs'=>['terminale-mobile']],
            ['names'=>['Cititoare coduri de bare'],'slugs'=>['cititoare-coduri-de-bare','scanere-coduri-de-bare']],
            ['names'=>['Brațe robotice','Brate robotice'],'slugs'=>['brate-robotice','brate-robot']],
            ['names'=>['Sisteme de inspecție','Sisteme de inspectie'],'slugs'=>['sisteme-de-inspectie','inspectie-industriala']],
            ['names'=>['Echipamente RFID'],'slugs'=>['echipamente-rfid','rfid']],
            ['names'=>['Panel PC-uri','Laptopuri rugged','Laptopuri Rugged'],'slugs'=>['panel-pc-uri','panel-pc','laptopuri-rugged','rugged-laptops']],
            ['names'=>['Sisteme POS și de interacțiune cu clienții','Sisteme POS si de interactiune cu clientii'],'slugs'=>['sisteme-pos-si-de-interactiune-cu-clientii','sisteme-pos-interactiune-clienti','sisteme-pos']],
            ['names'=>['Monitoare touchscreen','Monitoare Touchscreen'],'slugs'=>['monitoare-touchscreen','touchscreen-monitors']],
            ['names'=>['Imprimante de carduri'],'slugs'=>['imprimante-de-carduri','imprimante-carduri']],
            ['names'=>['Cititoare de carduri'],'slugs'=>['cititoare-de-carduri','cititoare-carduri']],
            ['names'=>['Tablete semnătură digitală','Tablete semnatura digitala'],'slugs'=>['tablete-semnatura-digitala','tablete-pentru-semnatura-digitala']],
        ];
    }

    private static function find_product_category_ids($names,$slugs=[]){
        $ids=[];
        foreach((array)$names as $name){
            $t=get_term_by('name',$name,'product_cat');
            if($t && !is_wp_error($t)) $ids[]=(int)$t->term_id;
        }
        foreach((array)$slugs as $slug){
            $t=get_term_by('slug',$slug,'product_cat');
            if($t && !is_wp_error($t)) $ids[]=(int)$t->term_id;
        }
        if(!$ids){
            $needles=array_values(array_filter(array_map(fn($x)=>strtolower(remove_accents((string)$x)),(array)$names)));
            $terms=get_terms(['taxonomy'=>'product_cat','hide_empty'=>false]);
            if(!is_wp_error($terms)) foreach($terms as $t){
                $hay=strtolower(remove_accents($t->name));
                foreach($needles as $needle){
                    if($hay===$needle || str_contains($hay,$needle) || str_contains($needle,$hay)){$ids[]=(int)$t->term_id;break;}
                }
            }
        }
        return array_values(array_unique(array_filter(array_map('intval',$ids))));
    }

    private static function home_category_specs(){
        return [
            ['name'=>'Imprimante de etichete','slugs'=>['imprimante-de-etichete']],
            ['name'=>'Terminale mobile','slugs'=>['terminale-mobile']],
            ['name'=>'Cititoare coduri de bare','slugs'=>['cititoare-coduri-de-bare','scanere-coduri-de-bare']],
            ['name'=>'Automatizare industrială și robotică','slugs'=>['automatizare-industriala-si-robotica','automatizare-industriala-robotica']],
            ['name'=>'Echipamente RFID','slugs'=>['echipamente-rfid','rfid']],
            ['name'=>'Calculatoare industriale','slugs'=>['calculatoare-industriale']],
            ['name'=>'Soluții audio-vizuale și de afișare digital','slugs'=>['solutii-audio-vizuale-si-de-afisare-digital','solutii-audio-vizuale-afisare-digitala','digital-signage']],
            ['name'=>'Sisteme de identificare și carduri','slugs'=>['sisteme-de-identificare-si-carduri','identificare-si-carduri']],
        ];
    }

    private static function find_product_category($name,$slugs=[]){
        $term=get_term_by('name',$name,'product_cat'); if($term && !is_wp_error($term)) return $term;
        foreach((array)$slugs as $slug){$term=get_term_by('slug',$slug,'product_cat'); if($term && !is_wp_error($term)) return $term;}
        $needle=strtolower(remove_accents($name));
        $terms=get_terms(['taxonomy'=>'product_cat','hide_empty'=>false]); if(is_wp_error($terms)) return null;
        foreach($terms as $t){$hay=strtolower(remove_accents($t->name)); if($hay===$needle) return $t;}
        return null;
    }

    private static function grouped_autoid_stock(WC_Product $p){
        if(!$p->is_type('grouped')) return (int)(self::numeric_meta($p->get_id(),['stock_autoid','_stock_autoid']) ?: 0);
        $sum=0; foreach((array)$p->get_children() as $cid){$sum+=(int)(self::numeric_meta((int)$cid,['stock_autoid','_stock_autoid','_autoid_stock','autoid_stock']) ?: 0);} return $sum;
    }

    private static function simple_vat_price_display(WC_Product $p,$mode='current'){
        if($p->is_type('grouped')) return '';
        $raw=$mode==='regular'?$p->get_regular_price():$p->get_price();
        if($raw==='' || !is_numeric($raw)) return '';
        $value=wc_get_price_including_tax($p,['price'=>(float)$raw]);
        return number_format((float)$value,2,',','.') . ' lei';
    }

    private static function grouped_distributor_stock(WC_Product $p){if(!$p->is_type('grouped'))return (int)(self::numeric_meta($p->get_id(),['stock_distributie','_stock_distributie','stock_distributor','_stock_distributor'])?:0);$sum=0;foreach((array)$p->get_children() as $cid)$sum+=(int)(self::numeric_meta((int)$cid,['stock_distributie','_stock_distributie','stock_distributor','_stock_distributor'])?:0);return $sum;}

    public static function products(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok)) return $ok;
        $page=self::int_param($r,'page',1,1,100000);
        $per=self::int_param($r,'per_page',20,1,50);
        $search=sanitize_text_field((string)$r->get_param('search'));
        $category=absint($r->get_param('category'));
        $secondary_category=absint($r->get_param('secondary_category'));
        $brand=absint($r->get_param('brand'));
        $model=absint($r->get_param('model'));
        $min_price=(float)$r->get_param('min_price');
        $max_price=(float)$r->get_param('max_price');
        $orderby=sanitize_key((string)$r->get_param('orderby')); if($orderby==='') $orderby='stock_autoid';

        $cache_key='autoid_mobile_catalog_'.md5(wp_json_encode([$search,$category,$secondary_category,$brand,$model,$min_price,$max_price,$orderby]));
        $sorted_ids=get_transient($cache_key);
        $cache_hit=is_array($sorted_ids);

        if(!$cache_hit){
            $category_term=$category ? get_term($category,'product_cat') : null;
            $is_liquidation=$category_term && !is_wp_error($category_term) && $category_term->slug==='lichidari-de-stoc';
            $ids=[];
            if($search!=='') {
                $ids=self::catalog_search_ids($search,500);
            } else {
                $tax=[];
                if($category) $tax[]=['taxonomy'=>'product_cat','field'=>'term_id','terms'=>[$category],'include_children'=>$is_liquidation?false:true,'operator'=>'IN'];
                if($secondary_category) $tax[]=['taxonomy'=>'product_cat','field'=>'term_id','terms'=>[$secondary_category],'include_children'=>true,'operator'=>'IN'];
                if($brand){ foreach(['product_brands','product_brand','pa_brand','brand'] as $bt){ if(taxonomy_exists($bt)){ $tax[]=['taxonomy'=>$bt,'field'=>'term_id','terms'=>[$brand]]; break; } } }
                if($model && taxonomy_exists('product_tag')) $tax[]=['taxonomy'=>'product_tag','field'=>'term_id','terms'=>[$model]];
                $meta=[];
                if($min_price>0 || $max_price>0){
                    $cl=['key'=>'_price','type'=>'NUMERIC'];
                    if($min_price>0 && $max_price>0){$cl['value']=[$min_price,$max_price];$cl['compare']='BETWEEN';}
                    elseif($min_price>0){$cl['value']=$min_price;$cl['compare']='>=';}
                    else{$cl['value']=$max_price;$cl['compare']='<=';}
                    $meta[]=$cl;
                }
                $args=['post_type'=>'product','post_status'=>'publish','posts_per_page'=>-1,'fields'=>'ids','no_found_rows'=>true];
                if($tax) $args['tax_query']=array_merge(['relation'=>'AND'],$tax);
                if($meta) $args['meta_query']=$meta;
                $ids=(new WP_Query($args))->posts;
            }

            $category_filter_ids=$category ? ($is_liquidation ? [$category] : array_values(array_unique(array_merge([$category],array_map('intval',(array)get_term_children($category,'product_cat')))))) : [];
            $secondary_filter_ids=$secondary_category ? array_values(array_unique(array_merge([$secondary_category],array_map('intval',(array)get_term_children($secondary_category,'product_cat'))))) : [];
            if($search!=='' && ($category || $secondary_category || $brand || $model || $min_price>0 || $max_price>0)) {
                $ids=array_values(array_filter($ids,function($id) use($category_filter_ids,$secondary_filter_ids,$brand,$model,$min_price,$max_price){
                    $p=wc_get_product($id); if(!$p) return false;
                    if($category_filter_ids && !has_term($category_filter_ids,'product_cat',$id)) return false;
                    if($secondary_filter_ids && !has_term($secondary_filter_ids,'product_cat',$id)) return false;
                    if($brand){$hit=false;foreach(['product_brands','product_brand','pa_brand','brand'] as $bt)if(taxonomy_exists($bt)&&has_term($brand,$bt,$id)){$hit=true;break;}if(!$hit)return false;}
                    if($model && taxonomy_exists('product_tag') && !has_term($model,'product_tag',$id)) return false;
                    $pr=(float)$p->get_price(); if($min_price>0&&$pr<$min_price)return false; if($max_price>0&&$pr>$max_price)return false;
                    return true;
                }));
            }

            $rows=[];
            foreach(array_unique(array_map('intval',$ids)) as $id) {
                $p=wc_get_product($id);
                if(!$p || $p->get_status()!=='publish' || !$p->is_visible()) continue;
                if($is_liquidation){
                    if(!has_term($category,'product_cat',$id)) continue;
                    $stock_autoid=(int)(self::numeric_meta($id,['stock_autoid','_stock_autoid','_autoid_stock','autoid_stock']) ?: 0);
                    if($stock_autoid<=0) continue;
                }
                $rows[]=$p;
            }

            usort($rows,function($a,$b)use($orderby){
                if($orderby==='price_asc'||$orderby==='price_desc'){$cmp=((float)$a->get_price())<=>((float)$b->get_price());return $orderby==='price_desc'?-$cmp:$cmp;}
                if($orderby==='rating')return ((float)$b->get_average_rating())<=>((float)$a->get_average_rating());
                if($orderby==='title')return strcasecmp($a->get_name(),$b->get_name());
                if($orderby==='date')return strcmp($b->get_date_created()?->date('c')??'',$a->get_date_created()?->date('c')??'');
                $sa=$a->is_type('grouped')?self::grouped_autoid_stock($a):(int)(self::numeric_meta($a->get_id(),['stock_autoid','_stock_autoid','_autoid_stock','autoid_stock'])?:0);
                $sb=$b->is_type('grouped')?self::grouped_autoid_stock($b):(int)(self::numeric_meta($b->get_id(),['stock_autoid','_stock_autoid','_autoid_stock','autoid_stock'])?:0);
                return $sa===$sb?strcasecmp($a->get_name(),$b->get_name()):($sb<=>$sa);
            });
            $sorted_ids=array_map(static fn($p)=>(int)$p->get_id(),$rows);
            set_transient($cache_key,$sorted_ids,90);
        }

        $total=count($sorted_ids);
        $slice_ids=array_slice($sorted_ids,($page-1)*$per,$per);
        $slice=[];
        foreach($slice_ids as $id){ $p=wc_get_product((int)$id); if($p) $slice[]=$p; }
        return rest_ensure_response([
            'products'=>array_map(fn($p)=>self::product_row($p,false),$slice),
            'page'=>$page,'per_page'=>$per,'total'=>$total,'pages'=>$total?(int)ceil($total/$per):0,
            'catalog_cache'=>$cache_hit?'hit':'miss'
        ]);
    }

    public static function product(WP_REST_Request $r) {
        $ok = self::require_wc(); if (is_wp_error($ok)) return $ok;
        $p = self::published_product(absint($r['id']));
        if (is_wp_error($p)) return $p;
        return rest_ensure_response(self::product_row($p,true));
    }

    public static function product_reviews(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $p=self::published_product(absint($r['id'])); if(is_wp_error($p))return $p;
        if($r->get_method()==='POST'){
            if(!comments_open($p->get_id()))return new WP_Error('autoid_reviews_closed','Recenziile sunt închise pentru acest produs.',['status'=>403]);
            $b=$r->get_json_params(); if(!is_array($b))$b=[];
            $rating=max(1,min(5,absint($b['rating']??0)));$content=trim(wp_strip_all_tags((string)($b['content']??'')));
            if(strlen($content)<3)return new WP_Error('autoid_review_short','Recenzia este prea scurtă.',['status'=>400]);
            $uid=self::bearer_user_id($r);$name='';$email='';
            if($uid){$u=get_userdata($uid);if($u){$name=trim((string)$u->display_name);$email=(string)$u->user_email;}}
            if(!$uid){$name=sanitize_text_field((string)($b['name']??''));$email=sanitize_email((string)($b['email']??''));if($name===''||!is_email($email))return new WP_Error('autoid_review_identity','Numele și emailul valid sunt obligatorii.',['status'=>400]);}
            $guard='autoid_mobile_review_guard_'.md5($p->get_id().'|'.strtolower($email));if(get_transient($guard))return new WP_Error('autoid_review_duplicate','Recenzia tocmai a fost trimisă.',['status'=>429]);set_transient($guard,1,30);
            $approved=get_option('comment_moderation')?0:1;
            $comment_id=wp_insert_comment(['comment_post_ID'=>$p->get_id(),'comment_author'=>$name,'comment_author_email'=>$email,'comment_content'=>$content,'comment_type'=>'review','comment_parent'=>0,'user_id'=>$uid,'comment_approved'=>$approved,'comment_agent'=>'AutoID Android App']);
            if(!$comment_id)return new WP_Error('autoid_review_failed','Recenzia nu a putut fi salvată.',['status'=>500]);
            update_comment_meta($comment_id,'rating',$rating);
            $verified=$uid && function_exists('wc_customer_bought_product') && wc_customer_bought_product($email,$uid,$p->get_id());
            update_comment_meta($comment_id,'verified',$verified?1:0);
            if(function_exists('WC_Comments::clear_transients'))WC_Comments::clear_transients($p->get_id());
            return rest_ensure_response(['created'=>true,'comment_id'=>$comment_id,'approved'=>(bool)$approved]);
        }
        $page=self::int_param($r,'page',1,1,10000);$per=self::int_param($r,'per_page',8,1,30);
        $comments=get_comments(['post_id'=>$p->get_id(),'status'=>'approve','type'=>'review','number'=>$per,'offset'=>($page-1)*$per,'orderby'=>'comment_date_gmt','order'=>'DESC']);
        $rows=[];foreach($comments as $c){$rows[]=['id'=>(int)$c->comment_ID,'author'=>$c->comment_author,'rating'=>(int)get_comment_meta($c->comment_ID,'rating',true),'content'=>wp_strip_all_tags($c->comment_content),'date_created'=>mysql2date('c',$c->comment_date_gmt,false),'verified'=>(bool)get_comment_meta($c->comment_ID,'verified',true)];}
        return rest_ensure_response(['product_id'=>$p->get_id(),'average'=>(float)$p->get_average_rating(),'count'=>(int)$p->get_review_count(),'page'=>$page,'per_page'=>$per,'reviews'=>$rows]);
    }

    public static function family(WP_REST_Request $r) {
        $ok = self::require_wc(); if (is_wp_error($ok)) return $ok;
        $p = self::published_product(absint($r['id']));
        if (is_wp_error($p)) return $p;
        $data = self::family_data($p);
        $summaries = [];
        foreach (self::group_labels() as $key=>$label) {
            $summaries[] = ['key'=>$key,'label'=>$label,'count'=>count($data['groups'][$key] ?? [])];
        }
        return rest_ensure_response([
            'product_id'=>$p->get_id(),
            'model'=>$data['model'],
            'brand'=>self::brand_name($p),
            'source'=>$data['source'],
            'groups'=>$summaries,
            'support_available'=>self::support_exists_for_model($data['model']['key']),
        ]);
    }

    public static function family_group(WP_REST_Request $r) {
        $ok = self::require_wc(); if (is_wp_error($ok)) return $ok;
        $p = self::published_product(absint($r['id']));
        if (is_wp_error($p)) return $p;
        $key = sanitize_key((string)$r['group']);
        if (!isset(self::group_labels()[$key])) return new WP_Error('autoid_bad_group','Unknown product family group.',['status'=>400]);
        $page = self::int_param($r,'page',1,1,100000);
        $per = self::int_param($r,'per_page',20,1,50);
        $data = self::family_data($p);
        $ids = array_values($data['groups'][$key] ?? []);
        $ids = array_values(array_filter($ids, function($id) {
            $row = wc_get_product($id);
            return $row && $row->get_status()==='publish' && $row->is_visible();
        }));
        usort($ids, function($a,$b) {
            $sa = (int)(get_post_meta($a,'stock_autoid',true) ?: get_post_meta($a,'_stock_autoid',true) ?: 0);
            $sb = (int)(get_post_meta($b,'stock_autoid',true) ?: get_post_meta($b,'_stock_autoid',true) ?: 0);
            if ($sa === $sb) {
                $da = (int)(get_post_meta($a,'stock_distributie',true) ?: get_post_meta($a,'stock_distributor',true) ?: 0);
                $db = (int)(get_post_meta($b,'stock_distributie',true) ?: get_post_meta($b,'stock_distributor',true) ?: 0);
                return $db <=> $da;
            }
            return $sb <=> $sa;
        });
        $filters=[];$selected_category=absint($r->get_param('category'));
        if(in_array($key,['accessories','consumables'],true)){
            $cfg=self::mobile_tabs_settings();$root_key=$key==='accessories'?'accessories':'consumables';$root=absint($cfg['roots'][$root_key]??0);$counts=[];
            if($root){foreach($ids as $pid){$terms=wp_get_post_terms($pid,'product_cat',['fields'=>'ids']);if(is_wp_error($terms))continue;$seen=[];foreach($terms as $term_id){$term_id=(int)$term_id;if($term_id===$root)continue;$anc=array_reverse(array_map('intval',get_ancestors($term_id,'product_cat','taxonomy')));$direct=0;if(in_array($root,$anc,true)){foreach($anc as $ancestor){$t=get_term($ancestor,'product_cat');if($t&&!is_wp_error($t)&&(int)$t->parent===$root){$direct=(int)$t->term_id;break;}}if(!$direct){$t=get_term($term_id,'product_cat');if($t&&!is_wp_error($t)&&(int)$t->parent===$root)$direct=$term_id;}}if($direct)$seen[$direct]=true;}foreach(array_keys($seen) as $fid)$counts[$fid]=($counts[$fid]??0)+1;}}
            arsort($counts);foreach($counts as $fid=>$count){$term=get_term($fid,'product_cat');if($term&&!is_wp_error($term))$filters[]=['id'=>(int)$fid,'name'=>$term->name,'count'=>(int)$count];}
            if($selected_category){$ids=array_values(array_filter($ids,function($pid)use($selected_category){$row=wc_get_product($pid);return $row&&self::mobile_in_cat_tree($row,$selected_category);}));}
        }
        $total = count($ids);
        $slice = array_slice($ids,($page-1)*$per,$per);
        $products = [];
        foreach ($slice as $id) {
            $row = wc_get_product($id);
            if ($row) $products[] = self::product_row($row,false);
        }
        return rest_ensure_response([
            'group'=>['key'=>$key,'label'=>self::group_labels()[$key]],
            'model'=>$data['model'],'count'=>$total,'page'=>$page,'per_page'=>$per,
            'pages'=>$total ? (int)ceil($total/$per) : 0,'products'=>$products,'filters'=>$filters,'selected_category'=>$selected_category,
        ]);
    }

    public static function product_support(WP_REST_Request $r) {
        $ok = self::require_wc(); if (is_wp_error($ok)) return $ok;
        $p = self::published_product(absint($r['id']));
        if (is_wp_error($p)) return $p;
        $model = self::model_context($p);
        $rows = self::support_rows($model['key'],80);
        $sections = [];
        foreach (self::support_labels() as $key=>$label) $sections[$key] = [];
        foreach ($rows as $row) $sections[self::support_group($row['type'],$row['title'])][] = $row;
        $out = [];
        foreach (self::support_labels() as $key=>$label) {
            $out[] = ['key'=>$key,'label'=>$label,'count'=>count($sections[$key]),'resources'=>$sections[$key]];
        }
        return rest_ensure_response(['product_id'=>$p->get_id(),'model'=>$model,'sections'=>$out]);
    }

    public static function categories(WP_REST_Request $r) {
        $parent = absint($r->get_param('parent'));
        return rest_ensure_response(['parent'=>$parent,'categories'=>self::category_rows($parent)]);
    }

    private static function mobile_google_client_id() {
        $manual=trim((string)get_option('autoid_mobile_google_client_id',''));
        if($manual!=='') return $manual;
        global $wpdb;
        $values=$wpdb->get_col("SELECT option_value FROM {$wpdb->options} WHERE option_name LIKE '%google%' LIMIT 80");
        foreach($values as $raw){
            if(!is_string($raw)||$raw==='')continue;
            if(preg_match('/[0-9]{6,}-[A-Za-z0-9_-]+\.apps\.googleusercontent\.com/',$raw,$m)) return $m[0];
        }
        return '';
    }

    private static function mobile_shipping_config() {
        $fallback_incl=(float)apply_filters('autoid_mobile_flat_rate_incl_vat',30.25);
        $fallback_free=(float)apply_filters('autoid_mobile_free_shipping_min',593.00);
        $fallback_tax=(float)apply_filters('autoid_mobile_standard_tax_rate',21.0);
        $flat_ex=null;$free_min=null;$title='Livrare';$taxable=true;
        if(class_exists('WC_Shipping_Zones')){
            $zones=[];
            $zones[]=new WC_Shipping_Zone(0);
            foreach(WC_Shipping_Zones::get_zones() as $z){$zones[]=new WC_Shipping_Zone((int)$z['zone_id']);}
            foreach($zones as $zone){
                foreach($zone->get_shipping_methods(true) as $method){
                    if(($method->enabled??'no')!=='yes')continue;
                    if($method->id==='flat_rate' && $flat_ex===null){
                        $raw=(string)$method->get_option('cost','');
                        if(preg_match('/-?[0-9]+(?:[\.,][0-9]+)?/',$raw,$m))$flat_ex=(float)str_replace(',','.',$m[0]);
                        $title=wp_strip_all_tags((string)$method->get_option('title',$method->get_method_title()));
                        $taxable=(string)$method->get_option('tax_status','taxable')!=='none';
                    }
                    if($method->id==='free_shipping' && $free_min===null){
                        $v=(float)$method->get_option('min_amount',0);if($v>0)$free_min=$v;
                    }
                }
            }
        }
        $rates=class_exists('WC_Tax')?WC_Tax::get_base_tax_rates(''):[];
        $rate=$fallback_tax;
        if($rates){$first=reset($rates);if(is_array($first)&&isset($first['rate']))$rate=(float)$first['rate'];}
        $flat_incl=$fallback_incl;
        if($flat_ex!==null){$flat_incl=max(0,(float)$flat_ex);if($taxable&&$rates)$flat_incl+=array_sum(WC_Tax::calc_tax($flat_ex,$rates,false));}
        if($free_min===null||$free_min<=0)$free_min=$fallback_free;
        return ['flat_rate_incl_vat'=>round($flat_incl,2),'flat_rate_ex_vat'=>$flat_ex!==null?round(max(0,$flat_ex),4):round($fallback_incl/(1+($rate/100)),4),'free_shipping_min'=>round($free_min,2),'tax_rate'=>round($rate,4),'title'=>$title?:'Livrare','taxable'=>$taxable];
    }

    public static function checkout_config(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok)) return $ok;
        $gateways=WC()->payment_gateways()?WC()->payment_gateways()->payment_gateways():[];
        $defaults=['cod'=>['Numerar la livrare (COD)','Plată la livrare.'],'bacs'=>['Transfer bancar','Plată prin ordin de plată.'],'stripe'=>['Card (Stripe)','Plată securizată cu cardul în aplicație.']];
        $out=[];
        foreach($defaults as $id=>$fallback){
            $g=$gateways[$id]??null;
            $enabled=$id==='stripe'?self::stripe_sandbox_ready():($g?($g->enabled==='yes'):true);
            $out[]=['id'=>$id,'title'=>$g?wp_strip_all_tags($g->get_title()):$fallback[0],'description'=>$g?wp_strip_all_tags($g->get_description()):$fallback[1],'enabled'=>$enabled];
        }
        return rest_ensure_response(['currency'=>get_woocommerce_currency(),'country'=>WC()->countries->get_base_country(),'payments'=>$out,'shipping'=>self::mobile_shipping_config(),'google_client_id'=>self::mobile_google_client_id(),'stripe_publishable_key'=>self::stripe_sandbox_ready()?self::stripe_publishable():'','stripe_mode'=>self::stripe_sandbox_ready()?'test':'']);
    }

    public static function checkout_order(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok)) return $ok;
        $body=$r->get_json_params(); if(!is_array($body)) $body=[];
        $lines=$body['line_items']??[]; if(!is_array($lines)||!$lines) return new WP_Error('autoid_empty_cart','Coșul este gol.',['status'=>400]);
        $payment=sanitize_key((string)($body['payment_method']??'cod')); if(!in_array($payment,['cod','bacs','stripe'],true)) return new WP_Error('autoid_bad_payment','Metodă de plată invalidă.',['status'=>400]);
        if($payment==='stripe' && !self::stripe_sandbox_ready()) return new WP_Error('autoid_stripe_not_ready','Stripe Sandbox nu este configurat. Adaugă pk_test_ și sk_test_ în WooCommerce → AutoID App Home.',['status'=>409]);
        $billing=is_array($body['billing']??null)?$body['billing']:[];$shipping=is_array($body['shipping']??null)?$body['shipping']:$billing;$delivery_mode=sanitize_key((string)($body['delivery_mode']??'delivery'));if(!in_array($delivery_mode,['delivery','pickup'],true))$delivery_mode='delivery';
        foreach(['first_name','last_name','address_1','city','postcode','country','email','phone'] as $k){if(empty($billing[$k])) return new WP_Error('autoid_missing_'.$k,'Completează toate câmpurile obligatorii.',['status'=>400]);}
        if($delivery_mode==='delivery')foreach(['first_name','last_name','address_1','city','postcode','country'] as $k){if(empty($shipping[$k])) return new WP_Error('autoid_missing_shipping_'.$k,'Completează adresa de livrare.',['status'=>400]);}
        try{
            $uid=self::bearer_user_id($r);
            $clean_b=[];foreach(['first_name','last_name','company','address_1','address_2','city','state','postcode','country','email','phone'] as $k)$clean_b[$k]=sanitize_text_field((string)($billing[$k]??''));$clean_b['email']=sanitize_email((string)($billing['email']??''));
            $clean_s=[];foreach(['first_name','last_name','company','address_1','address_2','city','state','postcode','country'] as $k)$clean_s[$k]=sanitize_text_field((string)(($delivery_mode==='pickup'?$billing:$shipping)[$k]??''));
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
            $order->update_meta_data('_wc_order_attribution_user_agent','AutoID-Android/1.0.22');
            $order->update_meta_data('_autoid_order_source','android_app');
            $order->update_meta_data('_autoid_app_version','1.0.22');$order->update_meta_data('_autoid_delivery_mode',$delivery_mode);
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
            $cfg=self::mobile_shipping_config();$before_shipping=(float)$order->get_total();$free=$delivery_mode==='pickup'||((float)$cfg['free_shipping_min']>0 && $before_shipping>=(float)$cfg['free_shipping_min']);
            $ship_item=new WC_Order_Item_Shipping();if($delivery_mode==='pickup'){$ship_item->set_method_title('Ridicare din Depozit');$ship_item->set_method_id('local_pickup:autoid-mobile');$ship_item->set_total(0);}else{$ship_item->set_method_title($free?'Livrare gratuită':(string)$cfg['title']);$ship_item->set_method_id($free?'free_shipping:autoid-mobile':'flat_rate:autoid-mobile');$ship_item->set_total($free?0:(float)$cfg['flat_rate_ex_vat']);if(!$free&&!empty($cfg['taxable'])&&class_exists('WC_Tax')){$rates=WC_Tax::get_base_tax_rates('');if($rates)$ship_item->set_taxes(['total'=>WC_Tax::calc_tax((float)$cfg['flat_rate_ex_vat'],$rates,false)]);}}
            $order->add_item($ship_item);$order->calculate_totals(false);$order->save();
            if($payment==='cod')$order->update_status('processing','Comandă plasată din aplicația AutoID Android cu plata ramburs.');elseif($payment==='bacs')$order->update_status('on-hold','Comandă plasată din aplicația AutoID Android cu transfer bancar.');
            $stripe_payload=[];
            if($payment==='stripe'){
                $pi=self::stripe_create_intent_for_order($order);
                if(is_wp_error($pi)){$order->update_status('failed','PaymentIntent Stripe Sandbox nu a putut fi creat: '.$pi->get_error_message());return $pi;}
                $stripe_payload=['stripe_publishable_key'=>self::stripe_publishable(),'stripe_client_secret'=>$pi['client_secret'],'stripe_payment_intent_id'=>$pi['payment_intent_id'],'stripe_payment_token'=>$pi['payment_token'],'stripe_mode'=>'test'];
            }
            return rest_ensure_response(array_merge(['order_id'=>$order->get_id(),'number'=>$order->get_order_number(),'status'=>$order->get_status(),'total'=>$order->get_total(),'currency'=>$order->get_currency(),'payment_method'=>$payment,'requires_payment'=>$payment==='stripe','shipping_total'=>$order->get_shipping_total(),'tax_total'=>$order->get_total_tax(),'review_consent'=>$review,'account_created'=>$account_created,'access_token'=>$new_token,'customer'=>$uid?self::customer_payload($uid):null,'origin'=>'Android App','delivery_mode'=>$delivery_mode],$stripe_payload));
        }catch(Throwable $e){return new WP_Error('autoid_checkout_failed',$e->getMessage(),['status'=>500]);}
    }

    public static function register_customer(WP_REST_Request $r){
        $ok=self::require_wc(); if(is_wp_error($ok)) return $ok; $b=$r->get_json_params(); if(!is_array($b))$b=[];
        $email=sanitize_email((string)($b['email']??''));$password=(string)($b['password']??''); if(!is_email($email)||strlen($password)<8)return new WP_Error('autoid_bad_register','Email valid și parolă de minimum 8 caractere.',['status'=>400]);
        $id=wc_create_new_customer($email,'',$password); if(is_wp_error($id))return $id;
        $u=new WC_Customer($id);$u->set_first_name(sanitize_text_field((string)($b['first_name']??'')));$u->set_last_name(sanitize_text_field((string)($b['last_name']??'')));$u->set_billing_company(sanitize_text_field((string)($b['company']??'')));$u->save();
        $vat=sanitize_text_field((string)($b['vat_number']??''));if($vat!==''){update_user_meta($id,'_eu_vat_guard_vat_number',$vat);update_user_meta($id,'billing_vat',$vat);update_user_meta($id,'vat_number',$vat);}
        return rest_ensure_response(['created'=>true,'customer_id'=>$id,'email'=>$email]);
    }

    public static function brands(WP_REST_Request $r) {
        return rest_ensure_response(['brands'=>self::brand_rows(100)]);
    }

    public static function search(WP_REST_Request $r) {
        $q = sanitize_text_field((string)$r->get_param('q'));
        if (mb_strlen($q)<2) return rest_ensure_response(['suggestions'=>[],'engine'=>'autoid-catalog']);
        $ids = self::catalog_search_ids($q, 16);
        $suggestions = [];
        foreach ($ids as $id) {
            $p = wc_get_product($id);
            if (!$p || $p->get_status()!=='publish' || !$p->is_visible()) continue;
            $suggestions[] = self::product_row($p,false);
        }
        return rest_ensure_response(['suggestions'=>$suggestions,'engine'=>'autoid-exact+fibosearch']);
    }

    private static function catalog_search_ids($q,$limit=50) {
        $q = trim(sanitize_text_field((string)$q));
        if ($q==='') return [];
        $ids=[]; $seen=[];
        $add=function($id) use (&$ids,&$seen,$limit) { $id=(int)$id; if($id>0 && empty($seen[$id]) && count($ids)<$limit){$seen[$id]=1;$ids[]=$id;} };
        $sku_id = wc_get_product_id_by_sku($q); if ($sku_id) $add($sku_id);
        foreach (['model','pa_model','product_model','autoid_model'] as $tax) {
            if (!taxonomy_exists($tax)) continue;
            $term = get_term_by('slug',sanitize_title($q),$tax);
            if (!$term) $term = get_term_by('name',$q,$tax);
            if (!$term || is_wp_error($term)) continue;
            $query = new WP_Query(['post_type'=>'product','post_status'=>'publish','posts_per_page'=>$limit,'fields'=>'ids','no_found_rows'=>true,
                'tax_query'=>[['taxonomy'=>$tax,'field'=>'term_id','terms'=>[(int)$term->term_id]]],
                'meta_key'=>'stock_autoid','orderby'=>['meta_value_num'=>'DESC','menu_order'=>'ASC','title'=>'ASC']]);
            foreach($query->posts as $id) $add($id);
        }
        global $wpdb;
        $like = '%' . $wpdb->esc_like($q) . '%';
        $rows = $wpdb->get_col($wpdb->prepare("SELECT DISTINCT p.ID FROM {$wpdb->posts} p LEFT JOIN {$wpdb->postmeta} pm ON pm.post_id=p.ID AND pm.meta_key='_sku' WHERE p.post_type='product' AND p.post_status='publish' AND (p.post_title LIKE %s OR pm.meta_value LIKE %s) ORDER BY CASE WHEN p.post_title LIKE %s THEN 0 WHEN pm.meta_value=%s THEN 1 ELSE 2 END, p.post_title ASC LIMIT %d",$like,$like,$q.'%',$q,$limit));
        foreach($rows as $id) $add($id);
        foreach(self::fibosearch_ids($q,$limit) as $id) $add($id);
        return array_slice($ids,0,$limit);
    }

    private static function fibosearch_ids($q,$limit=50) {
        if ($q==='') return [];
        $url = add_query_arg(['action'=>'dgwt_wcas_ajax_search','s'=>$q], admin_url('admin-ajax.php'));
        $response = wp_remote_get($url,['timeout'=>4,'redirection'=>0,'headers'=>['X-AutoID-Mobile'=>'1']]);
        if (is_wp_error($response) || (int)wp_remote_retrieve_response_code($response)!==200) return [];
        $json = json_decode(wp_remote_retrieve_body($response),true); if(!is_array($json)) return [];
        $ids=[];
        $walk=function($value) use (&$walk,&$ids,$limit) {
            if(count($ids)>=$limit || !is_array($value)) return;
            $looks_product = isset($value['url']) || isset($value['title']) || isset($value['name']) || isset($value['sku']);
            if($looks_product){
                foreach(['post_id','product_id','id'] as $k) if(isset($value[$k]) && is_numeric($value[$k])) { $pid=(int)$value[$k]; $p=wc_get_product($pid); if($p) $ids[]=$pid; break; }
            }
            foreach($value as $v) $walk($v);
        };
        $walk($json);
        return array_values(array_unique($ids));
    }

    public static function support(WP_REST_Request $r) {
        $q = sanitize_text_field((string)$r->get_param('search'));
        if ($q==='') return rest_ensure_response(['resources'=>[]]);
        return rest_ensure_response(['resources'=>self::support_rows($q,30)]);
    }

    public static function navigation(WP_REST_Request $r) {
        $locations = get_nav_menu_locations(); $menu_id=0;
        foreach(['primary','main','primary-menu','header','menu-1'] as $loc) if(!empty($locations[$loc])) {$menu_id=(int)$locations[$loc];break;}
        if(!$menu_id){ $menus=wp_get_nav_menus(); if($menus){ usort($menus,fn($a,$b)=>$b->count<=>$a->count); $menu_id=(int)$menus[0]->term_id; } }
        if(!$menu_id) return rest_ensure_response(['items'=>[]]);
        $items=wp_get_nav_menu_items($menu_id,['update_post_term_cache'=>false]); if(!$items) return rest_ensure_response(['items'=>[]]);
        $rows=[];
        foreach($items as $i){
            if($i->post_status!=='publish') continue;
            $kind='none'; $object=(string)$i->object; $object_id=(int)$i->object_id; $url=(string)$i->url;
            if($object==='product_cat') $kind='category';
            elseif($object==='product') $kind='product';
            elseif($object==='page' || $i->type==='post_type') $kind='page';
            $path=(string)wp_parse_url($url,PHP_URL_PATH);
            if($path==='/' || $path==='') $kind='home';
            elseif(strpos($path,'/cart')===0 || strpos($path,'/cos')===0) $kind='cart';
            elseif(strpos($path,'/my-account')===0 || strpos($path,'/contul-meu')===0) $kind='account';
            elseif(strpos($path,'/support')===0) $kind='support';
            if($kind==='none' && $url){ $post_id=url_to_postid($url); if($post_id){$kind='page';$object_id=(int)$post_id;} }
            $rows[(int)$i->ID]=[
                'id'=>(int)$i->ID,'parent'=>(int)$i->menu_item_parent,'title'=>wp_strip_all_tags($i->title),'url'=>$url,'order'=>(int)$i->menu_order,
                'object'=>$object,'object_id'=>$object_id,'type'=>(string)$i->type,'native_kind'=>$kind,'children'=>[]
            ];
        }
        foreach(array_keys($rows) as $id){$parent=$rows[$id]['parent']; if($parent && isset($rows[$parent])){$rows[$parent]['children'][]=&$rows[$id];}}
        $top=[]; foreach($rows as $id=>&$row) if(!$row['parent'] || !isset($rows[$row['parent']])) $top[]=&$row;
        $clean=function($arr) use (&$clean){ usort($arr,fn($a,$b)=>$a['order']<=>$b['order']); return array_map(function($x) use (&$clean){$x['children']=$clean($x['children']); return $x;},$arr);};
        return rest_ensure_response(['items'=>$clean($top)]);
    }

    public static function content(WP_REST_Request $r) {
        $id=absint($r->get_param('id'));
        if(!$id){ $url=esc_url_raw((string)$r->get_param('url')); if($url) $id=(int)url_to_postid($url); }
        if(!$id) return new WP_Error('autoid_content_not_found','Conținutul nu a fost identificat.',['status'=>404]);
        $post=get_post($id); if(!$post || $post->post_status!=='publish') return new WP_Error('autoid_content_not_found','Conținut indisponibil.',['status'=>404]);
        return rest_ensure_response(['id'=>$id,'title'=>get_the_title($id),'type'=>$post->post_type,'content'=>wp_strip_all_tags(apply_filters('the_content',$post->post_content)),'url'=>get_permalink($id)]);
    }

    public static function ai_chat(WP_REST_Request $r) {
        $message=trim(sanitize_textarea_field((string)$r->get_param('message'))); if($message==='') return new WP_Error('autoid_ai_empty','Mesaj gol.',['status'=>400]);
        $product_id=absint($r->get_param('product_id')); $context=['channel'=>'android-app','product_id'=>$product_id,'support_center'=>self::support_center_info()];
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

    private static function support_center_info() {
        $info=['active'=>false,'version'=>'','file'=>''];
        if(!function_exists('get_plugins')) require_once ABSPATH.'wp-admin/includes/plugin.php';
        foreach((array)get_plugins() as $file=>$data){
            $name=(string)($data['Name']??'');
            if(stripos($name,'AutoID Support Center')!==false){
                $info=['active'=>is_plugin_active($file),'version'=>(string)($data['Version']??''),'file'=>$file]; break;
            }
        }
        return $info;
    }

    private static function callback_is_support_center($callback) {
        try{
            if(is_array($callback) && count($callback)>=2) $ref=new ReflectionMethod($callback[0],$callback[1]);
            elseif(is_string($callback) && function_exists($callback)) $ref=new ReflectionFunction($callback);
            elseif($callback instanceof Closure) $ref=new ReflectionFunction($callback);
            else return false;
            $file=strtolower((string)$ref->getFileName());
            return strpos($file,'autoid')!==false && strpos($file,'support')!==false;
        }catch(Throwable $e){ return false; }
    }

    private static function support_center_rest_ai($message,$product_id,$context) {
        $routes=rest_get_server()->get_routes();
        foreach($routes as $route=>$handlers){
            foreach((array)$handlers as $handler){
                $cb=$handler['callback']??null; if(!$cb || !self::callback_is_support_center($cb)) continue;
                $low=strtolower($route); if(strpos($low,'chat')===false && strpos($low,'assistant')===false && strpos($low,'ai')===false) continue;
                $req=new WP_REST_Request('POST',$route);
                foreach(['message','question','query','prompt'] as $k) $req->set_param($k,$message);
                $req->set_param('context',$context); if($product_id) $req->set_param('product_id',$product_id);
                $resp=rest_do_request($req); if(is_wp_error($resp) || $resp->is_error()) continue;
                $answer=self::extract_ai_answer($resp->get_data()); if($answer!=='') return $answer;
            }
        }
        return '';
    }

    private static function support_center_ajax_ai($message,$product_id,$context) {
        global $wp_filter;
        $tags=array_keys((array)$wp_filter);
        foreach($tags as $tag){
            if(strpos($tag,'wp_ajax_')!==0) continue;
            $action=preg_replace('/^wp_ajax_(nopriv_)?/','',$tag); $low=strtolower($action);
            if(strpos($low,'chat')===false && strpos($low,'assistant')===false && strpos($low,'ai')===false) continue;
            $hook=$wp_filter[$tag]??null; if(!$hook || !isset($hook->callbacks) || !is_array($hook->callbacks)) continue;
            $owned=false; foreach((array)$hook->callbacks as $priority=>$callbacks) foreach((array)$callbacks as $cb) if(self::callback_is_support_center($cb['function']??null)) {$owned=true;break 2;}
            if(!$owned) continue;
            $old_post=$_POST; $old_request=$_REQUEST;
            $_POST=array_merge($_POST,['action'=>$action,'message'=>$message,'question'=>$message,'query'=>$message,'prompt'=>$message,'context'=>wp_json_encode($context),'product_id'=>$product_id]); $_REQUEST=array_merge($_REQUEST,$_POST);
            ob_start();
            try{ do_action($tag); }catch(Throwable $e){}
            $out=trim((string)ob_get_clean()); $_POST=$old_post; $_REQUEST=$old_request;
            if($out==='') continue; $decoded=json_decode($out,true); $answer=self::extract_ai_answer(is_array($decoded)?$decoded:$out); if($answer!=='') return $answer;
        }
        return '';
    }

    private static function extract_ai_answer($data) {
        if(is_string($data)) return trim(wp_strip_all_tags($data));
        if(!is_array($data)) return '';
        foreach(['answer','response','reply','text','content','message'] as $k) if(isset($data[$k]) && is_string($data[$k]) && trim($data[$k])!=='') return trim(wp_strip_all_tags($data[$k]));
        foreach($data as $v){$a=self::extract_ai_answer($v); if($a!=='') return $a;} return '';
    }

    public static function catalog_facets(WP_REST_Request $r){
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $category=absint($r->get_param('category'));
        $secondary=absint($r->get_param('secondary_category'));
        $brand=absint($r->get_param('brand'));
        $model=absint($r->get_param('model'));
        $category_term=$category?get_term($category,'product_cat'):null;
        $is_liquidation=$category_term && !is_wp_error($category_term) && $category_term->slug==='lichidari-de-stoc';

        $brand_tax='';
        foreach(['product_brands','product_brand','pa_brand','brand'] as $candidate){ if(taxonomy_exists($candidate)){ $brand_tax=$candidate; break; } }
        $model_tax=taxonomy_exists('product_tag')?'product_tag':'';

        $base_key='autoid_mobile_facets_base_'.md5($category.'|'.($is_liquidation?'liq':'normal').'|1.1.4');
        $rows=get_transient($base_key);
        if(!is_array($rows)){
            $tax=[];
            if($category)$tax[]=['taxonomy'=>'product_cat','field'=>'term_id','terms'=>[$category],'include_children'=>$is_liquidation?false:true,'operator'=>'IN'];
            $args=['post_type'=>'product','post_status'=>'publish','posts_per_page'=>-1,'fields'=>'ids','no_found_rows'=>true,'update_post_meta_cache'=>true,'update_post_term_cache'=>true];
            if($tax)$args['tax_query']=$tax;
            $ids=(new WP_Query($args))->posts;
            $rows=[];
            foreach($ids as $id){
                $p=wc_get_product($id); if(!$p||!$p->is_visible())continue;
                if($is_liquidation){
                    if(!has_term($category,'product_cat',$id))continue;
                    $stock_autoid=(int)(self::numeric_meta($id,['stock_autoid','_stock_autoid','_autoid_stock','autoid_stock'])?:0);
                    if($stock_autoid<=0)continue;
                }
                $cats=wp_get_post_terms($id,'product_cat'); if(is_wp_error($cats))$cats=[];
                $bterms=$brand_tax?wp_get_post_terms($id,$brand_tax):[]; if(is_wp_error($bterms))$bterms=[];
                $mterms=$model_tax?wp_get_post_terms($id,$model_tax):[]; if(is_wp_error($mterms))$mterms=[];
                $rows[]=[
                    'id'=>(int)$id,
                    'price'=>(float)$p->get_price(),
                    'cats'=>array_map(fn($t)=>['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug,'parent'=>(int)$t->parent],$cats),
                    'brands'=>array_map(fn($t)=>['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug],$bterms),
                    'models'=>array_map(fn($t)=>['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug],$mterms),
                ];
            }
            set_transient($base_key,$rows,120);
        }

        $secondary_ids=[];
        if($secondary){
            $children=get_term_children($secondary,'product_cat'); if(is_wp_error($children))$children=[];
            $secondary_ids=array_values(array_unique(array_merge([$secondary],array_map('intval',$children))));
        }
        $matches=function($row,$check_cat=true,$check_brand=true,$check_model=true) use($secondary_ids,$brand,$model){
            if($check_cat && $secondary_ids){
                $ids=array_map('intval',array_column($row['cats'],'id'));
                if(!array_intersect($secondary_ids,$ids))return false;
            }
            if($check_brand && $brand){
                $ids=array_map('intval',array_column($row['brands'],'id'));
                if(!in_array($brand,$ids,true))return false;
            }
            if($check_model && $model){
                $ids=array_map('intval',array_column($row['models'],'id'));
                if(!in_array($model,$ids,true))return false;
            }
            return true;
        };

        $best_category=function($cats) use($category,$is_liquidation){
            $best=0;$best_depth=-1;
            foreach((array)$cats as $ct){
                $cid=(int)($ct['id']??0); if(!$cid || $cid===$category)continue;
                $anc=array_map('intval',(array)get_ancestors($cid,'product_cat'));
                if(!$is_liquidation && $category && !in_array($category,$anc,true))continue;
                $depth=count($anc);
                if($depth>$best_depth){$best=$cid;$best_depth=$depth;}
            }
            return $best;
        };

        $min=null;$max=null;
        foreach($rows as $row){
            if(!$matches($row,true,true,true))continue;
            $pr=(float)$row['price']; if($pr>0){$min=$min===null?$pr:min($min,$pr);$max=$max===null?$pr:max($max,$pr);}
        }

        $category_nodes=[];$liquidation_categories=[];
        foreach($rows as $row){
            if(!$matches($row,false,true,true))continue;
            $seen=[];
            foreach((array)$row['cats'] as $ct){
                $cid=(int)$ct['id']; if(!$cid || $cid===$category || ($ct['slug']??'')==='lichidari-de-stoc')continue;
                if($is_liquidation){
                    if(isset($seen[$cid]))continue; $seen[$cid]=true;
                    if(!isset($liquidation_categories[$cid]))$liquidation_categories[$cid]=['id'=>$cid,'name'=>$ct['name'],'slug'=>$ct['slug'],'count'=>0,'parent'=>(int)$ct['parent'],'depth'=>1];
                    $liquidation_categories[$cid]['count']++;
                    continue;
                }
                if(!$category)continue;
                $cursor=get_term($cid,'product_cat');$path=[];$guard=0;
                while($cursor && !is_wp_error($cursor) && (int)$cursor->term_id!==$category && $guard<20){
                    $path[]=$cursor;
                    if(!(int)$cursor->parent)break;
                    $cursor=get_term((int)$cursor->parent,'product_cat');$guard++;
                }
                if(!$cursor || is_wp_error($cursor) || (int)$cursor->term_id!==$category)continue;
                foreach(array_reverse($path) as $node){
                    $nid=(int)$node->term_id;if(isset($seen[$nid]))continue;$seen[$nid]=true;
                    if(!isset($category_nodes[$nid]))$category_nodes[$nid]=['id'=>$nid,'name'=>$node->name,'slug'=>$node->slug,'count'=>0,'parent'=>(int)$node->parent,'depth'=>1];
                    $category_nodes[$nid]['count']++;
                }
            }
        }

        $brands=[];
        foreach($rows as $row){
            if(!$matches($row,true,false,true))continue;
            $seen=[];
            foreach((array)$row['brands'] as $t){$id=(int)$t['id'];if(!$id||isset($seen[$id]))continue;$seen[$id]=true;if(!isset($brands[$id]))$brands[$id]=['id'=>$id,'name'=>$t['name'],'slug'=>$t['slug'],'count'=>0];$brands[$id]['count']++;}
        }

        $models=[];
        foreach($rows as $row){
            if(!$matches($row,true,true,false))continue;
            $model_brand=(int)($row['brands'][0]['id']??0);
            $model_category=(int)$best_category($row['cats']);
            $seen=[];
            foreach((array)$row['models'] as $t){
                $id=(int)$t['id'];if(!$id||isset($seen[$id]))continue;$seen[$id]=true;
                if(!isset($models[$id]))$models[$id]=['id'=>$id,'name'=>$t['name'],'slug'=>$t['slug'],'count'=>0,'brand_id'=>$model_brand,'category_id'=>$model_category];
                $models[$id]['count']++;
                if(empty($models[$id]['brand_id'])&&$model_brand)$models[$id]['brand_id']=$model_brand;
                if(empty($models[$id]['category_id'])&&$model_category)$models[$id]['category_id']=$model_category;
            }
        }

        uasort($brands,fn($a,$b)=>strcasecmp($a['name'],$b['name']));
        uasort($models,fn($a,$b)=>strcasecmp($a['name'],$b['name']));
        uasort($liquidation_categories,function($a,$b){$c=$b['count']<=>$a['count'];return $c!==0?$c:strcasecmp($a['name'],$b['name']);});

        $category_hierarchy=[];
        if(!$is_liquidation && $category && $category_nodes){
            $walk=function($parent,$depth) use (&$walk,&$category_hierarchy,$category_nodes){
                $children=array_filter($category_nodes,fn($x)=>(int)$x['parent']===(int)$parent);
                uasort($children,fn($a,$b)=>strcasecmp($a['name'],$b['name']));
                foreach($children as $child){$child['depth']=$depth;$category_hierarchy[]=$child;$walk((int)$child['id'],$depth+1);}
            };
            $walk($category,1);
        }

        return rest_ensure_response([
            'price'=>['min'=>$min?:0,'max'=>$max?:0],
            'brands'=>array_values($brands),
            'models'=>array_values($models),
            'subcategories'=>[],
            'category_hierarchy'=>$category_hierarchy,
            'liquidation_categories'=>array_values($liquidation_categories),
            'special_category'=>$is_liquidation?'liquidation':'',
            'selection'=>['category'=>$secondary?:null,'brand'=>$brand?:null,'model'=>$model?:null],
            'bridge_version'=>'1.1.10'
        ]);
    }

    public static function rfq(WP_REST_Request $r){$b=$r->get_json_params();if(!is_array($b))$b=[];$email=sanitize_email((string)($b['email']??''));$name=sanitize_text_field((string)($b['name']??''));if(!$name||!is_email($email))return new WP_Error('autoid_rfq_invalid','Numele și emailul sunt obligatorii.',['status'=>400]);$products=[];foreach((array)($b['products']??[]) as $row){$id=absint($row['id']??0);$qty=max(1,absint($row['qty']??1));$p=$id?wc_get_product($id):null;if($p)$products[]=$qty.' x '.$p->get_name().' ('.$p->get_sku().')';}if(!$products)return new WP_Error('autoid_rfq_empty','Adaugă cel puțin un produs în cererea de ofertă.',['status'=>400]);$company=sanitize_text_field((string)($b['company']??''));$phone=sanitize_text_field((string)($b['phone']??''));$message=sanitize_textarea_field((string)($b['message']??''));$to=(string)apply_filters('autoid_mobile_rfq_email',get_option('admin_email'));$body="Nume: $name\nEmail: $email\nCompanie: $company\nTelefon: $phone\n\nProduse:\n- ".implode("\n- ",$products)."\n\nMesaj:\n$message";$sent=wp_mail($to,'Cerere ofertă din aplicația AutoID',$body,['Reply-To: '.$name.' <'.$email.'>']);if(!$sent)return new WP_Error('autoid_rfq_mail','Cererea nu a putut fi trimisă.',['status'=>500]);return rest_ensure_response(['sent'=>true]);}

    public static function consultation_request(WP_REST_Request $r){$b=$r->get_json_params();if(!is_array($b))$b=[];$email=sanitize_email((string)($b['email']??''));$name=sanitize_text_field((string)($b['name']??''));$message=sanitize_textarea_field((string)($b['message']??''));if(!$name||!is_email($email)||!$message)return new WP_Error('autoid_consult_invalid','Numele, emailul și mesajul sunt obligatorii.',['status'=>400]);$to=(string)apply_filters('autoid_mobile_consultation_email',get_option('admin_email'));$body="Nume: $name\nEmail: $email\nTelefon: ".sanitize_text_field((string)($b['phone']??''))."\nCompanie: ".sanitize_text_field((string)($b['company']??''))."\n\n$message";$sent=wp_mail($to,'Solicitare consultanță tehnică din aplicația AutoID',$body,['Reply-To: '.$name.' <'.$email.'>']);if(!$sent)return new WP_Error('autoid_consult_mail','Solicitarea nu a putut fi trimisă.',['status'=>500]);return rest_ensure_response(['sent'=>true]);}

    private static function published_product($id) {
        $p = wc_get_product($id);
        if (!$p || $p->get_status()!=='publish') return new WP_Error('autoid_product_not_found','Product not found.',['status'=>404]);
        return $p;
    }

    private static function category_row($t) {
        $thumb=absint(get_term_meta($t->term_id,'thumbnail_id',true));
        return ['id'=>(int)$t->term_id,'parent'=>(int)$t->parent,'name'=>$t->name,'slug'=>$t->slug,'count'=>(int)$t->count,'image'=>$thumb?wp_get_attachment_image_url($thumb,'woocommerce_thumbnail'):null];
    }

    private static function category_rows($parent=0) {
        $terms = get_terms(['taxonomy'=>'product_cat','hide_empty'=>true,'parent'=>(int)$parent,'orderby'=>'menu_order','order'=>'ASC']);
        if (is_wp_error($terms)) return [];
        return array_map([__CLASS__,'category_row'],$terms);
    }

    private static function brand_rows($limit) {
        foreach (['product_brands','product_brand','pa_brand','brand'] as $tax) {
            if (!taxonomy_exists($tax)) continue;
            $terms = get_terms(['taxonomy'=>$tax,'hide_empty'=>true,'number'=>$limit,'orderby'=>'count','order'=>'DESC']);
            if (is_wp_error($terms)) continue;
            return array_map(fn($t)=>['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug,'count'=>(int)$t->count],$terms);
        }
        return [];
    }

    private static function image_url(WC_Product $p,$detail=false) {
        $id = $p->get_image_id();
        return $id ? wp_get_attachment_image_url($id,$detail?'large':'woocommerce_thumbnail') : null;
    }

    private static function brand_name(WC_Product $p) {
        foreach (['product_brands','product_brand','pa_brand','brand'] as $tax) {
            if (!taxonomy_exists($tax)) continue;
            $terms = wp_get_post_terms($p->get_id(),$tax,['fields'=>'names']);
            if (!is_wp_error($terms) && $terms) return (string)$terms[0];
        }
        foreach (['brand','pa_brand'] as $attr) {
            $v = $p->get_attribute($attr);
            if (is_string($v) && trim($v)!=='') return trim($v);
        }
        return '';
    }

    private static function brand_logo(WC_Product $p){foreach(['product_brands','product_brand','pa_brand','brand'] as $tax){if(!taxonomy_exists($tax))continue;$terms=wp_get_post_terms($p->get_id(),$tax);if(is_wp_error($terms)||!$terms)continue;$t=$terms[0];foreach(['thumbnail_id','brand_thumbnail_id','image_id'] as $key){$id=absint(get_term_meta($t->term_id,$key,true));if($id){$u=wp_get_attachment_image_url($id,'medium');if($u)return $u;}}}return '';}

    private static function model_context(WC_Product $p) {
        $id = $p->get_id();
        $candidates = [];
        foreach (['model','pa_model','product_model','autoid_model','product_tag'] as $tax) {
            if (!taxonomy_exists($tax)) continue;
            $terms = wp_get_post_terms($id,$tax);
            if (is_wp_error($terms)) continue;
            foreach ($terms as $t) {
                $score = ($tax==='model' ? 300 : (stripos($tax,'model')!==false ? 100 : 20)) + (preg_match('/^[a-z]{1,5}-?\d{2,5}[a-z0-9-]*$/i',$t->slug)?20:0);
                $candidates[] = ['key'=>strtoupper($t->name),'label'=>$t->name,'taxonomy'=>$tax,'term_id'=>(int)$t->term_id,'score'=>$score];
            }
        }
        foreach (['model','pa_model'] as $attr) {
            $v = trim((string)$p->get_attribute($attr));
            if ($v!=='') $candidates[] = ['key'=>strtoupper($v),'label'=>$v,'taxonomy'=>'attribute','term_id'=>0,'score'=>90];
        }
        foreach (['_autoid_model','autoid_model','product_model','_product_model','model','_model'] as $meta) {
            $v = get_post_meta($id,$meta,true);
            if (is_scalar($v) && trim((string)$v)!=='') $candidates[] = ['key'=>strtoupper(trim((string)$v)),'label'=>trim((string)$v),'taxonomy'=>'meta:'.$meta,'term_id'=>0,'score'=>80];
        }
        if (preg_match_all('/\b[A-Z]{1,5}\d{2,5}[A-Z]?\b/i',strtoupper($p->get_name()),$m)) {
            foreach ($m[0] as $token) $candidates[] = ['key'=>$token,'label'=>$token,'taxonomy'=>'name','term_id'=>0,'score'=>60-strlen($token)];
        }
        usort($candidates,fn($a,$b)=>$b['score']<=>$a['score']);
        $best = $candidates[0] ?? ['key'=>'','label'=>'','taxonomy'=>'fallback','term_id'=>0,'score'=>0];
        $best['key'] = trim(preg_replace('/\s+.*/','',$best['key']));
        unset($best['score']);
        return $best;
    }

    private static function mobile_tabs_settings() {
        $saved=get_option('sofa_enterprise_tabs_settings_v4',[]);if(!is_array($saved))$saved=[];
        return [
            'roots'=>[
                'accessories'=>absint($saved['root_accessories']??1179)?:1179,
                'consumables'=>absint($saved['root_consumables']??3287)?:3287,
                'software'=>absint($saved['root_software']??3814)?:3814,
                'services'=>absint($saved['root_services']??1184)?:1184,
            ],
            'visible'=>[
                'accessories'=>array_values(array_filter(array_map('absint',(array)($saved['visible_accessories']??[1157,19,1156,4540,1163,4541,3603,4542])))),
                'consumables'=>array_values(array_filter(array_map('absint',(array)($saved['visible_consumables']??[19,7661,1161])))),
                'software'=>array_values(array_filter(array_map('absint',(array)($saved['visible_software']??[1157,19,1156,4540,1163,4542])))),
                'services'=>array_values(array_filter(array_map('absint',(array)($saved['visible_services']??[1157,19,1156,4540,1163,4541,3603,4542])))),
            ],
        ];
    }

    private static function mobile_product_cat_ids(WC_Product $p){$ids=wp_get_post_terms($p->get_id(),'product_cat',['fields'=>'ids']);return is_wp_error($ids)?[]:array_values(array_filter(array_map('absint',$ids)));}
    private static function mobile_in_cat_tree(WC_Product $p,$root){$root=absint($root);if(!$root)return false;foreach(self::mobile_product_cat_ids($p) as $cid){if($cid===$root)return true;$anc=array_map('absint',get_ancestors($cid,'product_cat'));if(in_array($root,$anc,true))return true;}return false;}
    private static function mobile_visible_for(WC_Product $p,$type,$cfg){$root=$cfg['roots'][$type]??0;if($root&&self::mobile_in_cat_tree($p,$root))return false;$rules=$cfg['visible'][$type]??[];if(!$rules)return true;$allowed=[];foreach($rules as $rid){$allowed[]=$rid;$kids=get_term_children($rid,'product_cat');if(!is_wp_error($kids))$allowed=array_merge($allowed,array_map('absint',$kids));}return (bool)array_intersect(array_unique($allowed),self::mobile_product_cat_ids($p));}

    private static function enterprise_related_group(WC_Product $current,WC_Product $candidate,$cfg){
        $roots=$cfg['roots'];$current_compat=false;$candidate_compat=false;
        foreach($roots as $type=>$root){if(self::mobile_in_cat_tree($current,$root))$current_compat=true;if(self::mobile_in_cat_tree($candidate,$root))$candidate_compat=true;}
        if($current_compat)return $candidate_compat?null:'products';
        $map=['accessories'=>'accessories','consumables'=>'consumables','software'=>'software','services'=>'service'];
        foreach($map as $type=>$group){if(self::mobile_visible_for($current,$type,$cfg)&&self::mobile_in_cat_tree($candidate,$roots[$type]??0))return $group;}
        return null;
    }

    private static function family_data(WC_Product $p) {
        $model=self::model_context($p);$cfg=self::mobile_tabs_settings();$cache_key='autoid_mob_family_enterprise_'.md5($p->get_id().'|'.$model['key'].'|'.wp_json_encode($cfg).'|1.0.23');
        $cached=get_transient($cache_key);if(is_array($cached))return $cached;
        $groups=array_fill_keys(array_keys(self::group_labels()),[]);$grouped=self::grouped_parent($p);$tag_source=$grouped?:$p;
        if($grouped){foreach((array)$grouped->get_children() as $child_id){$child=wc_get_product($child_id);if($child&&$child->get_status()==='publish'&&$child->is_visible())$groups['variants'][]=(int)$child_id;}}
        $tags=wp_get_post_terms($tag_source->get_id(),'product_tag',['fields'=>'ids']);if((is_wp_error($tags)||!$tags)&&$tag_source->get_id()!==$p->get_id())$tags=wp_get_post_terms($p->get_id(),'product_tag',['fields'=>'ids']);
        if(!is_wp_error($tags)&&$tags){
            $q=new WP_Query(['post_type'=>'product','post_status'=>'publish','posts_per_page'=>1500,'fields'=>'ids','no_found_rows'=>true,'tax_query'=>[['taxonomy'=>'product_tag','field'=>'term_id','terms'=>array_map('intval',$tags)]]]);
            $variant_lookup=array_fill_keys($groups['variants'],true);
            foreach($q->posts as $id){$id=(int)$id;if($id===$p->get_id()||($grouped&&$id===$grouped->get_id())||isset($variant_lookup[$id]))continue;$rp=wc_get_product($id);if(!$rp||$rp->get_status()!=='publish'||!$rp->is_visible())continue;$g=self::enterprise_related_group($p,$rp,$cfg);if($g)$groups[$g][]=$id;}
        }
        foreach($groups as $key=>$rows)$groups[$key]=array_values(array_unique(array_map('intval',$rows)));
        $source=['strategy'=>'enterprise-tabs:common-product-tags+root-category+visibility','grouped_parent_id'=>$grouped?$grouped->get_id():0,'tag_ids'=>!is_wp_error($tags)?array_values(array_map('intval',(array)$tags)):[],'roots'=>$cfg['roots'],'visibility'=>$cfg['visible']];
        $data=['model'=>$model,'source'=>$source,'groups'=>$groups];set_transient($cache_key,$data,self::CACHE_TTL);return $data;
    }

    private static function grouped_parent(WC_Product $p) {
        if($p->is_type('grouped')) return $p;
        global $wpdb; $id=(int)$p->get_id();
        $likes=['%i:'.$id.';%','%"'.$id.'"%']; $candidate_ids=[];
        foreach($likes as $like){$found=$wpdb->get_col($wpdb->prepare("SELECT post_id FROM {$wpdb->postmeta} WHERE meta_key='_children' AND meta_value LIKE %s LIMIT 50",$like));$candidate_ids=array_merge($candidate_ids,$found);}
        foreach(array_unique(array_map('intval',$candidate_ids)) as $pid){$parent=wc_get_product($pid);if($parent&&$parent->is_type('grouped')&&in_array($id,array_map('intval',$parent->get_children()),true))return $parent;}
        return null;
    }

    private static function group_labels() {
        return ['variants'=>'Variante','products'=>'Modele compatibile','accessories'=>'Accesorii','service'=>'Service','software'=>'Software & Apps','consumables'=>'Consumabile'];
    }

    private static function support_rows($q,$limit=30) {
        $q = sanitize_text_field((string)$q);
        if ($q==='') return [];
        $types = ['autoid_support_res','autoid_support_resource','support_resource'];
        $existing = array_values(array_filter($types,'post_type_exists'));
        if (!$existing) return [];
        $query = new WP_Query(['post_type'=>$existing,'post_status'=>'publish','s'=>$q,'posts_per_page'=>$limit,'no_found_rows'=>true]);
        $rows = [];
        foreach ($query->posts as $post) {
            $type = get_post_meta($post->ID,'resource_type',true) ?: get_post_meta($post->ID,'_resource_type',true) ?: 'Resursă';
            $external = get_post_meta($post->ID,'resource_url',true) ?: get_post_meta($post->ID,'_resource_url',true);
            $rows[] = ['id'=>$post->ID,'title'=>get_the_title($post),'url'=>$external?:get_permalink($post),'type'=>sanitize_text_field($type),'summary'=>wp_strip_all_tags(get_the_excerpt($post))];
        }
        return $rows;
    }

    private static function support_exists_for_model($model) {
        return !empty(self::support_rows($model,1));
    }

    private static function support_group($type,$title='') {
        $v = strtolower(remove_accents($type.' '.$title));
        if (strpos($v,'driver')!==false) return 'drivers';
        if (strpos($v,'firmware')!==false) return 'firmware';
        if (strpos($v,'video')!==false || strpos($v,'youtube')!==false) return 'videos';
        if (strpos($v,'troubleshoot')!==false || strpos($v,'depan')!==false || strpos($v,'eroare')!==false) return 'troubleshooting';
        if (strpos($v,'software')!==false || strpos($v,'application')!==false || strpos($v,'developer')!==false || strpos($v,'utility')!==false || strpos($v,'sdk')!==false) return 'software';
        return 'documentation';
    }

    private static function support_labels() {
        return ['drivers'=>'Drivere','firmware'=>'Firmware','documentation'=>'Documentație','videos'=>'Video','troubleshooting'=>'Depanare','software'=>'Software'];
    }

    private static function numeric_meta($id,$keys) {
        foreach ($keys as $key) {
            $v = get_post_meta($id,$key,true);
            if ($v!=='' && is_numeric($v)) return (int)$v;
        }
        return null;
    }

    private static function stock_info(WC_Product $p) {
        $id = $p->get_id();
        $autoid = self::numeric_meta($id,['stock_autoid','_stock_autoid','_autoid_stock','autoid_stock']);
        $dist = self::numeric_meta($id,['stock_distributie','_stock_distributie','stock_distributor','_stock_distributor','_distributor_stock','distributor_stock']);
        if ($autoid!==null && $autoid>0) $delivery = $autoid.' în stoc. Livrare rapidă';
        elseif ($dist!==null && $dist>0) $delivery = $dist.' stoc producător. Livrare în 5–7 zile';
        elseif ($p->is_in_stock()) $delivery = $p->get_stock_status()==='onbackorder' ? 'Disponibil la comandă' : 'Disponibil';
        else $delivery = 'Cere ofertă pentru disponibilitate';
        return ['autoid'=>$autoid,'distributor'=>$dist,'delivery'=>$delivery];
    }

    public static function admin_menu() {
        add_submenu_page(
            'woocommerce',
            'AutoID App Home',
            'AutoID App Home',
            'manage_woocommerce',
            'autoid-app-home',
            [__CLASS__, 'render_home_admin']
        );
    }

    public static function admin_init() {
        register_setting(
            'autoid_mobile_hero_group',
            'autoid_mobile_hero_slides',
            [
                'type'=>'array',
                'sanitize_callback'=>[__CLASS__, 'sanitize_hero_slides'],
                'default'=>self::default_hero_slides(),
            ]
        );
        register_setting(
            'autoid_mobile_home_group',
            'autoid_mobile_home_skus',
            [
                'type'=>'string',
                'sanitize_callback'=>[__CLASS__, 'sanitize_home_skus'],
                'default'=>'',
            ]
        );
        register_setting(
            'autoid_mobile_home_group',
            'autoid_mobile_google_client_id',
            [
                'type'=>'string',
                'sanitize_callback'=>function($value){return sanitize_text_field(trim((string)$value));},
                'default'=>'',
            ]
        );
        register_setting(
            'autoid_mobile_home_group',
            'autoid_mobile_stripe_publishable_test',
            [
                'type'=>'string',
                'sanitize_callback'=>function($value){$v=trim((string)$value);return str_starts_with($v,'pk_test_')?sanitize_text_field($v):'';},
                'default'=>'',
            ]
        );
        register_setting(
            'autoid_mobile_home_group',
            'autoid_mobile_stripe_secret_test',
            [
                'type'=>'string',
                'sanitize_callback'=>function($value){$v=trim((string)$value);return str_starts_with($v,'sk_test_')?sanitize_text_field($v):'';},
                'default'=>'',
            ]
        );

        register_setting('autoid_mobile_home_group','autoid_mobile_firebase_enabled',['type'=>'integer','sanitize_callback'=>fn($v)=>empty($v)?0:1,'default'=>0]);
        foreach(['project_id','application_id','api_key','sender_id'] as $f) register_setting('autoid_mobile_home_group','autoid_mobile_firebase_'.$f,['type'=>'string','sanitize_callback'=>fn($v)=>sanitize_text_field(trim((string)$v)),'default'=>'']);
        register_setting('autoid_mobile_home_group','autoid_mobile_firebase_service_json',['type'=>'string','sanitize_callback'=>[__CLASS__,'sanitize_firebase_service_json_v128'],'default'=>'']);
    }


    public static function sanitize_firebase_service_json_v128($value){
        $v=trim(wp_unslash((string)$value));if($v==='')return (string)get_option('autoid_mobile_firebase_service_json','');$j=json_decode($v,true);if(!is_array($j)||empty($j['client_email'])||empty($j['private_key'])||empty($j['project_id']))return (string)get_option('autoid_mobile_firebase_service_json','');return wp_json_encode($j,JSON_UNESCAPED_SLASHES);
    }
    private static function firebase_public_v128(){return ['enabled'=>(bool)get_option('autoid_mobile_firebase_enabled',0),'project_id'=>trim((string)get_option('autoid_mobile_firebase_project_id','')),'application_id'=>trim((string)get_option('autoid_mobile_firebase_application_id','')),'api_key'=>trim((string)get_option('autoid_mobile_firebase_api_key','')),'sender_id'=>trim((string)get_option('autoid_mobile_firebase_sender_id',''))];}
    public static function push_config_v128(){ $c=self::firebase_public_v128();$c['enabled']=$c['enabled']&&$c['project_id']!==''&&$c['application_id']!==''&&$c['api_key']!==''&&$c['sender_id']!=='';return rest_ensure_response($c);}
    private static function privacy_default_v128(){return ['transactional_notifications'=>true,'analytics'=>false,'personalization'=>false,'marketing'=>false];}
    private static function privacy_for_user_v128($uid){$v=get_user_meta((int)$uid,'_autoid_privacy_v128',true);return is_array($v)?array_merge(self::privacy_default_v128(),array_map(fn($x)=>(bool)$x,$v)):self::privacy_default_v128();}
    public static function me_privacy_v128(WP_REST_Request $r){$uid=absint($r->get_param('_autoid_user_id'));if(!$uid)$uid=self::bearer_user_id($r);if($r->get_method()==='POST'){$b=$r->get_json_params();$v=['transactional_notifications'=>!empty($b['transactional_notifications']),'analytics'=>!empty($b['analytics']),'personalization'=>!empty($b['personalization']),'marketing'=>!empty($b['marketing'])];update_user_meta($uid,'_autoid_privacy_v128',$v);if(!$v['transactional_notifications']&&!$v['marketing'])delete_user_meta($uid,'_autoid_fcm_tokens_v128');return rest_ensure_response($v);}return rest_ensure_response(self::privacy_for_user_v128($uid));}
    private static function clean_fcm_token_v128($v){$v=trim((string)$v);return preg_match('/^[A-Za-z0-9_:\\-]{40,4096}$/',$v)?$v:'';}
    public static function push_register_v128(WP_REST_Request $r){$uid=absint($r->get_param('_autoid_user_id'));if(!$uid)$uid=self::bearer_user_id($r);$b=$r->get_json_params();$token=self::clean_fcm_token_v128($b['token']??'');if($token==='')return new WP_Error('autoid_fcm_token','Token FCM invalid.',['status'=>400]);$prefs=['transactional_notifications'=>!empty($b['transactional_notifications']),'analytics'=>!empty($b['analytics']),'personalization'=>!empty($b['personalization']),'marketing'=>!empty($b['marketing'])];update_user_meta($uid,'_autoid_privacy_v128',$prefs);if(!$prefs['transactional_notifications']&&!$prefs['marketing'])return rest_ensure_response(['registered'=>false]);$list=get_user_meta($uid,'_autoid_fcm_tokens_v128',true);if(!is_array($list))$list=[];$list=array_values(array_filter($list,fn($x)=>is_array($x)&&($x['token']??'')!==$token));array_unshift($list,['token'=>$token,'platform'=>'android','updated'=>time()]);update_user_meta($uid,'_autoid_fcm_tokens_v128',array_slice($list,0,5));return rest_ensure_response(['registered'=>true]);}
    public static function push_unregister_v128(WP_REST_Request $r){$uid=absint($r->get_param('_autoid_user_id'));if(!$uid)$uid=self::bearer_user_id($r);$b=$r->get_json_params();$token=self::clean_fcm_token_v128($b['token']??'');$list=get_user_meta($uid,'_autoid_fcm_tokens_v128',true);if(!is_array($list))$list=[];$list=array_values(array_filter($list,fn($x)=>is_array($x)&&($x['token']??'')!==$token));update_user_meta($uid,'_autoid_fcm_tokens_v128',$list);return rest_ensure_response(['unregistered'=>true]);}
    private static function firebase_service_v128(){ $j=json_decode((string)get_option('autoid_mobile_firebase_service_json',''),true);return is_array($j)?$j:[];}
    private static function b64u_v128($s){return rtrim(strtr(base64_encode($s),'+/','-_'),'=');}
    private static function firebase_access_token_v128(){if($v=get_transient('autoid_fcm_oauth_v128'))return $v;$sa=self::firebase_service_v128();if(empty($sa['client_email'])||empty($sa['private_key']))return new WP_Error('autoid_fcm_service','Firebase Service Account nu este configurat.');$now=time();$h=self::b64u_v128(wp_json_encode(['alg'=>'RS256','typ'=>'JWT']));$c=self::b64u_v128(wp_json_encode(['iss'=>$sa['client_email'],'scope'=>'https://www.googleapis.com/auth/firebase.messaging','aud'=>'https://oauth2.googleapis.com/token','iat'=>$now,'exp'=>$now+3500]));$input=$h.'.'.$c;$sig='';if(!openssl_sign($input,$sig,$sa['private_key'],OPENSSL_ALGO_SHA256))return new WP_Error('autoid_fcm_sign','Nu am putut semna JWT Firebase.');$jwt=$input.'.'.self::b64u_v128($sig);$res=wp_remote_post('https://oauth2.googleapis.com/token',['timeout'=>12,'body'=>['grant_type'=>'urn:ietf:params:oauth:grant-type:jwt-bearer','assertion'=>$jwt]]);if(is_wp_error($res))return $res;$o=json_decode(wp_remote_retrieve_body($res),true);$token=$o['access_token']??'';if($token==='')return new WP_Error('autoid_fcm_oauth','Firebase OAuth token indisponibil.');set_transient('autoid_fcm_oauth_v128',$token,3000);return $token;}
    private static function remove_fcm_token_v128($uid,$token){$list=get_user_meta($uid,'_autoid_fcm_tokens_v128',true);if(!is_array($list))return;$list=array_values(array_filter($list,fn($x)=>is_array($x)&&($x['token']??'')!==$token));update_user_meta($uid,'_autoid_fcm_tokens_v128',$list);}
    private static function fcm_send_token_v128($uid,$token,$data){$pub=self::firebase_public_v128();if(empty($pub['enabled'])||$pub['project_id']==='')return false;$access=self::firebase_access_token_v128();if(is_wp_error($access))return false;$payload=['message'=>['token'=>$token,'data'=>array_map('strval',$data),'android'=>['priority'=>'HIGH','ttl'=>'3600s']]];$url='https://fcm.googleapis.com/v1/projects/'.rawurlencode($pub['project_id']).'/messages:send';$res=wp_remote_post($url,['timeout'=>12,'headers'=>['Authorization'=>'Bearer '.$access,'Content-Type'=>'application/json; charset=UTF-8'],'body'=>wp_json_encode($payload)]);$code=wp_remote_retrieve_response_code($res);if($code===404||$code===410){self::remove_fcm_token_v128($uid,$token);return false;}return !is_wp_error($res)&&$code>=200&&$code<300;}
    private static function fcm_order_v128($order,$type){if(!$order instanceof WC_Order)return;$uid=(int)$order->get_customer_id();if(!$uid)return;$prefs=self::privacy_for_user_v128($uid);if(empty($prefs['transactional_notifications']))return;$tokens=get_user_meta($uid,'_autoid_fcm_tokens_v128',true);if(!is_array($tokens)||!$tokens)return;$tracking=self::order_tracking_payload($order);$number=$order->get_order_number();if($type==='order_awb'){$title='Comanda #'.$number.' a plecat din depozitul AutoID';$body='AWB '.$tracking['tracking_number'].' a fost generat. Urmărește livrarea.';}elseif($type==='order_review'){$title='Revizuiește comanda #'.$number;$body='Cum a fost experiența cu AutoID? Lasă-ne un review pe Google și, dacă dorești, recenzii produselor comandate.';}else{$title='Comanda #'.$number.' · '.wc_get_order_status_name($order->get_status());$body='Statusul comenzii tale AutoID a fost actualizat.';}$data=['type'=>$type,'order_id'=>(string)$order->get_id(),'title'=>$title,'body'=>$body,'tracking_number'=>$tracking['tracking_number'],'tracking_url'=>$tracking['tracking_url'],'status'=>$order->get_status(),'notification_id'=>(string)(100000+($order->get_id()%100000))];foreach($tokens as $x){$t=is_array($x)?self::clean_fcm_token_v128($x['token']??''):'';if($t!=='')self::fcm_send_token_v128($uid,$t,$data);}}
    public static function fcm_order_status_changed_v128($order_id,$from,$to,$order){if(!$order instanceof WC_Order)$order=wc_get_order($order_id);if(!$order)return;if($to==='completed'&&$order->get_meta('_autoid_review_consent',true)==='yes')self::fcm_order_v128($order,'order_review');else self::fcm_order_v128($order,'order_status');}
    public static function fcm_order_saved_v128($order){if(!$order instanceof WC_Order)return;$tracking=self::order_tracking_payload($order);if($tracking['tracking_number']==='')return;$key='autoid_fcm_awb_hash_'.$order->get_id();$hash=hash('sha256',$tracking['tracking_number']);if(get_option($key,'')===$hash)return;update_option($key,$hash,false);self::fcm_order_v128($order,'order_awb');}
    public static function fcm_meta_changed_v128($meta_id,$object_id,$meta_key,$meta_value){if(!in_array($meta_key,['GLS_AWB','_GLS_AWB','AWB_GLS','_AWB_GLS','gls_awb','_gls_awb'],true))return;$order=wc_get_order((int)$object_id);if($order)self::fcm_order_saved_v128($order);}

    public static function sanitize_home_skus($value) {
        $parts=preg_split('/[\r\n,;]+/',(string)$value);
        $out=[];
        foreach((array)$parts as $sku){
            $sku=trim(wp_strip_all_tags((string)$sku));
            if($sku==='' || in_array($sku,$out,true)) continue;
            $out[]=$sku;
        }
        return implode("\n",$out);
    }

    private static function home_selected_skus() {
        $raw=(string)get_option('autoid_mobile_home_skus','');
        if($raw==='') return [];
        return array_values(array_filter(array_map('trim',preg_split('/[\r\n,;]+/',$raw))));
    }

    public static function render_home_admin() {
        if (!current_user_can('manage_woocommerce')) return;
        $value=(string)get_option('autoid_mobile_home_skus','');
        $google_client_id=(string)get_option('autoid_mobile_google_client_id','');
        $stripe_pk=(string)get_option('autoid_mobile_stripe_publishable_test','');
        $stripe_sk=(string)get_option('autoid_mobile_stripe_secret_test','');
        $firebase_enabled=(bool)get_option('autoid_mobile_firebase_enabled',0);$firebase_project=(string)get_option('autoid_mobile_firebase_project_id','');$firebase_app=(string)get_option('autoid_mobile_firebase_application_id','');$firebase_api=(string)get_option('autoid_mobile_firebase_api_key','');$firebase_sender=(string)get_option('autoid_mobile_firebase_sender_id','');$firebase_service=(string)get_option('autoid_mobile_firebase_service_json','');
        ?>
        <div class="wrap">
            <h1>AutoID App · Home</h1>
            <p>Alege exact produsele afișate în secțiunea <strong>În stoc AutoID</strong>. Ordinea SKU-urilor este ordinea din aplicație.</p>
            <form method="post" action="options.php">
                <?php settings_fields('autoid_mobile_home_group'); ?>
                <table class="form-table" role="presentation">
                    <tr>
                        <th scope="row"><label for="autoid_mobile_home_skus">SKU-uri produse</label></th>
                        <td>
                            <textarea id="autoid_mobile_home_skus" name="autoid_mobile_home_skus" rows="14" class="large-text code" placeholder="ZT411R&#10;MC333R-GI4HG4EU"><?php echo esc_textarea($value); ?></textarea>
                            <p class="description">Un SKU pe linie. Sunt acceptate și virgulă sau punct și virgulă. Dacă lista este goală, aplicația folosește selecția automată existentă.</p>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row"><label for="autoid_mobile_google_client_id">Google Web OAuth Client ID</label></th>
                        <td>
                            <input type="text" id="autoid_mobile_google_client_id" name="autoid_mobile_google_client_id" value="<?php echo esc_attr($google_client_id); ?>" class="large-text code" placeholder="123456789-xxxx.apps.googleusercontent.com" />
                            <p class="description">Client ID de tip <strong>Web application</strong> folosit de Android Credential Manager pentru ID token. În Google Cloud configurează separat și clientul Android pentru package <code>ro.autoid.app</code> + SHA-1/SHA-256 al certificatului aplicației.</p>
                        </td>
                    </tr>

                    <tr><th scope="row">Firebase Cloud Messaging</th><td><label><input type="checkbox" name="autoid_mobile_firebase_enabled" value="1" <?php checked($firebase_enabled); ?> /> Activează notificările FCM instant</label><p class="description">Folosește Firebase Cloud Messaging HTTP v1. Dacă nu este configurat, aplicația păstrează fallback-ul periodic WorkManager.</p></td></tr>
                    <tr><th scope="row"><label for="autoid_mobile_firebase_project_id">Firebase Project ID</label></th><td><input id="autoid_mobile_firebase_project_id" name="autoid_mobile_firebase_project_id" value="<?php echo esc_attr($firebase_project); ?>" class="large-text code" placeholder="autoid-mobile" /></td></tr>
                    <tr><th scope="row"><label for="autoid_mobile_firebase_application_id">Firebase Android App ID</label></th><td><input id="autoid_mobile_firebase_application_id" name="autoid_mobile_firebase_application_id" value="<?php echo esc_attr($firebase_app); ?>" class="large-text code" placeholder="1:1234567890:android:abcdef" /><p class="description">Android package: <code>ro.autoid.app</code>.</p></td></tr>
                    <tr><th scope="row"><label for="autoid_mobile_firebase_api_key">Firebase API key</label></th><td><input id="autoid_mobile_firebase_api_key" name="autoid_mobile_firebase_api_key" value="<?php echo esc_attr($firebase_api); ?>" class="large-text code" autocomplete="off" /></td></tr>
                    <tr><th scope="row"><label for="autoid_mobile_firebase_sender_id">Firebase Sender ID / Project number</label></th><td><input id="autoid_mobile_firebase_sender_id" name="autoid_mobile_firebase_sender_id" value="<?php echo esc_attr($firebase_sender); ?>" class="large-text code" /></td></tr>
                    <tr><th scope="row"><label for="autoid_mobile_firebase_service_json">Firebase Service Account JSON</label></th><td><textarea id="autoid_mobile_firebase_service_json" name="autoid_mobile_firebase_service_json" rows="5" class="large-text code" placeholder="Lipește JSON-ul service account; dacă îl lași gol, configurația salvată se păstrează."></textarea><p class="description"><?php echo $firebase_service!==''?'<strong>Service account salvat pe server.</strong> Nu este transmis aplicației.':'Nu este configurat încă.'; ?></p></td></tr>
                    <tr>
                        <th scope="row"><label for="autoid_mobile_stripe_publishable_test">Stripe Sandbox · Publishable key</label></th>
                        <td><input type="text" id="autoid_mobile_stripe_publishable_test" name="autoid_mobile_stripe_publishable_test" value="<?php echo esc_attr($stripe_pk); ?>" class="large-text code" autocomplete="off" placeholder="pk_test_..." /><p class="description">Doar cheia de test <code>pk_test_...</code>. Este singura cheie Stripe transmisă aplicației Android.</p></td>
                    </tr>
                    <tr>
                        <th scope="row"><label for="autoid_mobile_stripe_secret_test">Stripe Sandbox · Secret key</label></th>
                        <td><input type="password" id="autoid_mobile_stripe_secret_test" name="autoid_mobile_stripe_secret_test" value="<?php echo esc_attr($stripe_sk); ?>" class="large-text code" autocomplete="new-password" placeholder="sk_test_..." /><p class="description">Cheia secretă rămâne exclusiv pe server. Cheile <code>sk_live_...</code> sunt respinse în această versiune Sandbox.</p></td>
                    </tr>
                </table>
                <?php submit_button('Salvează setările AutoID App'); ?>
            </form>
        </div>
        <?php
    }

    private static function default_hero_slides() {
        return [[
            'enabled'=>1,
            'title'=>'Echipamente AutoID pentru afacerea ta',
            'description'=>'Scanare, etichetare, mobilitate, RFID și soluții profesionale.',
            'image_id'=>0,
            'primary_label'=>'Vezi produsele',
            'primary_type'=>'category',
            'primary_target_id'=>0,
            'secondary_label'=>'Consultanță',
            'secondary_type'=>'consultation',
            'secondary_target_id'=>0,
        ]];
    }

    public static function sanitize_hero_slides($value) {
        if (!is_array($value)) return self::default_hero_slides();
        $out=[];
        $allowed=['product','category','contact','consultation','ai',''];
        foreach (array_values($value) as $row) {
            if (!is_array($row)) continue;
            $primary_type=sanitize_key($row['primary_type'] ?? '');
            $secondary_type=sanitize_key($row['secondary_type'] ?? '');
            if (!in_array($primary_type,$allowed,true)) $primary_type='';
            if (!in_array($secondary_type,$allowed,true)) $secondary_type='';
            $title=sanitize_text_field($row['title'] ?? '');
            if ($title==='') continue;
            $out[]=[
                'enabled'=>empty($row['enabled'])?0:1,
                'title'=>$title,
                'description'=>sanitize_textarea_field($row['description'] ?? ''),
                'image_id'=>absint($row['image_id'] ?? 0),
                'primary_label'=>sanitize_text_field($row['primary_label'] ?? ''),
                'primary_type'=>$primary_type,
                'primary_target_id'=>absint($row['primary_target_id'] ?? 0),
                'secondary_label'=>sanitize_text_field($row['secondary_label'] ?? ''),
                'secondary_type'=>$secondary_type,
                'secondary_target_id'=>absint($row['secondary_target_id'] ?? 0),
            ];
        }
        return $out ?: self::default_hero_slides();
    }

    private static function live_response($data) {
        $response=rest_ensure_response($data);
        if($response instanceof WP_REST_Response){
            $response->header('Cache-Control','no-store, no-cache, must-revalidate, max-age=0');
            $response->header('Pragma','no-cache');
            $response->header('Expires','Wed, 11 Jan 1984 05:00:00 GMT');
            $response->header('Surrogate-Control','no-store');
            $response->header('X-AutoID-Live-Config','1');
        }
        return $response;
    }

    private static function hero_app_overrides() {
        $rows=get_option('autoid_mobile_hero_app_overrides',[]);
        return is_array($rows) ? $rows : [];
    }

    private static function maybe_migrate_legacy_hero_overrides($slides,$overrides) {
        if($overrides) return $overrides;
        $migrated=[];
        foreach(array_values((array)$slides) as $i=>$row){
            if(!is_array($row)) continue;
            $has=false;
            foreach(['app_enabled','app_image_id','app_image','app_style','app_button_text','app_action_type','app_action_value','app_accent'] as $k){
                if(array_key_exists($k,$row)){ $has=true; break; }
            }
            if(!$has) continue;
            $style=sanitize_key((string)($row['app_style']??'card'));
            $migrated[$i]=[
                'app_enabled'=>!empty($row['app_enabled'])?1:0,
                'app_image_id'=>absint($row['app_image_id']??0),
                'app_image'=>esc_url_raw((string)($row['app_image']??'')),
                'app_style'=>in_array($style,['card','background'],true)?$style:'card',
                'app_button_text'=>sanitize_text_field((string)($row['app_button_text']??'')),
                'app_action_type'=>sanitize_key((string)($row['app_action_type']??'')),
                'app_action_value'=>sanitize_text_field((string)($row['app_action_value']??'')),
                'app_accent'=>sanitize_hex_color((string)($row['app_accent']??''))?:'',
            ];
        }
        if($migrated){
            update_option('autoid_mobile_hero_app_overrides',$migrated,false);
            update_option('autoid_mobile_hero_last_saved',time(),false);
            return $migrated;
        }
        return [];
    }

    public static function hero_live(WP_REST_Request $r) {
        $settings=get_option('autoid_mega_menu_settings',[]);
        $overrides=self::hero_app_overrides();
        $fingerprint=substr(hash('sha256',wp_json_encode([$settings,$overrides,get_option('autoid_mobile_hero_last_saved',0)])),0,16);
        return self::live_response([
            'hero_slides'=>self::hero_slides_public(),
            'revision'=>$fingerprint,
            'source'=>'autoid-mega-menu-app',
            'generated_at'=>gmdate('c'),
        ]);
    }

    private static function native_hero_action_from_url($raw_url) {
        $url=trim((string)$raw_url);
        if($url==='' || $url==='#') return ['type'=>'','id'=>0];
        $path=wp_parse_url($url,PHP_URL_PATH);
        if(!is_string($path) || $path==='') $path=$url;
        $path='/'.trim($path,'/').'/';

        if(in_array($path,['/magazin/','/shop/','/produse/'],true)) return ['type'=>'catalog','id'=>0];

        if(preg_match('#/(?:categorie-produs|product-category)/([^/]+)/?$#i',$path,$m)){
            $term=get_term_by('slug',sanitize_title($m[1]),'product_cat');
            if($term && !is_wp_error($term)) return ['type'=>'category','id'=>(int)$term->term_id];
        }

        if(preg_match('#/(?:produs|product)/([^/]+)/?$#i',$path,$m)){
            $post=get_page_by_path(sanitize_title($m[1]),OBJECT,'product');
            if($post) return ['type'=>'product','id'=>(int)$post->ID];
        }

        // AutoID uses clean nested WooCommerce category permalinks, e.g.
        // /imprimante-de-etichete/sisteme-de-imprimare-aplicare/.
        // Resolve the last path segment against product_cat and verify the canonical URL.
        $segments=array_values(array_filter(explode('/',trim($path,'/'))));
        if($segments){
            $slug=sanitize_title(end($segments));
            $term=get_term_by('slug',$slug,'product_cat');
            if($term && !is_wp_error($term)){
                $term_link=get_term_link($term,'product_cat');
                if(!is_wp_error($term_link)){
                    $wanted=untrailingslashit((string)wp_parse_url($url,PHP_URL_PATH));
                    $actual=untrailingslashit((string)wp_parse_url($term_link,PHP_URL_PATH));
                    if($wanted===$actual || basename($wanted)===basename($actual)){
                        return ['type'=>'category','id'=>(int)$term->term_id];
                    }
                }
            }
        }

        $post_id=url_to_postid($url);
        if($post_id && get_post_type($post_id)==='product') return ['type'=>'product','id'=>(int)$post_id];

        if(str_contains($path,'/consultanta/') || str_contains($path,'/contact/')) return ['type'=>'consultation','id'=>0];
        if(str_starts_with($path,'/support/')) return ['type'=>'ai','id'=>0];
        return ['type'=>'','id'=>0];
    }

    private static function explicit_app_hero_action($row) {
        $type=sanitize_key((string)($row['app_action_type'] ?? ''));
        $value=is_scalar($row['app_action_value'] ?? null) ? trim((string)$row['app_action_value']) : '';
        if($type==='') return null; // legacy slide: fall back to website URL inference.
        if($type==='none') return ['type'=>'','id'=>0];
        if($type==='catalog') return ['type'=>'catalog','id'=>0];
        if($type==='category'){
            $id=absint($value);
            $term=$id ? get_term($id,'product_cat') : null;
            return ($term && !is_wp_error($term)) ? ['type'=>'category','id'=>$id] : ['type'=>'','id'=>0];
        }
        if($type==='product_sku'){
            $id=function_exists('wc_get_product_id_by_sku') ? absint(wc_get_product_id_by_sku($value)) : 0;
            return $id ? ['type'=>'product','id'=>$id] : ['type'=>'','id'=>0];
        }
        if($type==='product'){
            $id=absint($value);
            return ($id && get_post_type($id)==='product') ? ['type'=>'product','id'=>$id] : ['type'=>'','id'=>0];
        }
        if($type==='consultation') return ['type'=>'consultation','id'=>0];
        if($type==='ai') return ['type'=>'ai','id'=>0];
        return ['type'=>'','id'=>0];
    }

    private static function hero_slides_public() {
        $mega=get_option('autoid_mega_menu_settings',[]);
        $mega_slides=is_array($mega) && is_array($mega['slides'] ?? null) ? array_values($mega['slides']) : [];
        $overrides=self::maybe_migrate_legacy_hero_overrides($mega_slides,self::hero_app_overrides());
        $interval=max(2500,min(20000,absint($mega['slider_interval'] ?? 5500)));
        $last_saved=max(1,absint(get_option('autoid_mobile_hero_last_saved',1)));
        $out=[];

        foreach($mega_slides as $i=>$row){
            if(!is_array($row)) continue;
            $app=is_array($overrides[$i] ?? null) ? $overrides[$i] : [];
            $merged=array_merge($row,$app);
            if(array_key_exists('app_enabled',$merged) && empty($merged['app_enabled'])) continue;
            $title=sanitize_text_field($row['title'] ?? '');
            if($title==='') continue;

            $explicit=self::explicit_app_hero_action($merged);
            $action=is_array($explicit) ? $explicit : self::native_hero_action_from_url($row['button_url'] ?? '');
            $label=sanitize_text_field($merged['app_button_text'] ?? '');
            if($label==='') $label=sanitize_text_field($row['button_text'] ?? '');
            if(($action['type'] ?? '')==='') $label='';

            $app_image='';
            $app_image_id=absint($merged['app_image_id'] ?? 0);
            if($app_image_id) $app_image=(string)(wp_get_attachment_image_url($app_image_id,'full') ?: '');
            if($app_image==='' && !empty($merged['app_image'])) $app_image=esc_url_raw((string)$merged['app_image']);
            if($app_image!=='') $app_image=add_query_arg('autoid_app_v',$last_saved,$app_image);

            $style=sanitize_key((string)($merged['app_style'] ?? 'card'));
            if(!in_array($style,['card','background'],true)) $style='card';

            $out[]=[
                'id'=>'mega-'.($i+1),
                'eyebrow'=>sanitize_text_field($row['eyebrow'] ?? ''),
                'title'=>$title,
                'description'=>sanitize_text_field($row['subtitle'] ?? ''),
                'image'=>$app_image,
                'app_image_id'=>$app_image_id,
                'background'=>sanitize_hex_color($merged['app_accent'] ?? $row['background'] ?? '') ?: '#f7630c',
                'style'=>$style,
                'interval_ms'=>$interval,
                'primary_label'=>$label,
                'primary_type'=>sanitize_key($action['type'] ?? ''),
                'primary_target_id'=>absint($action['id'] ?? 0),
                'secondary_label'=>'',
                'secondary_type'=>'',
                'secondary_target_id'=>0,
                'source'=>'autoid-mega-menu-app',
            ];
        }
        return $out;
    }

    private static function hero_action_options() {
        return [
            'product'=>'Produs',
            'category'=>'Categorie produs',
            'contact'=>'Contact',
            'consultation'=>'Consultanță',
            'ai'=>'Asistent AI',
            ''=>'Fără acțiune',
        ];
    }

    public static function render_hero_admin() {
        if (!current_user_can('manage_woocommerce')) return;
        wp_enqueue_media();
        $slides=get_option('autoid_mobile_hero_slides',self::default_hero_slides());
        $actions=self::hero_action_options();
        ?>
        <div class="wrap">
            <h1>AutoID App · Hero Slider</h1>
            <p>Controlează bannerul din pagina Acasă a aplicației. Ordinea cardurilor de mai jos este ordinea slide-urilor din aplicație.</p>
            <form method="post" action="options.php">
                <?php settings_fields('autoid_mobile_hero_group'); ?>
                <div id="autoid-hero-slides">
                    <?php foreach ((array)$slides as $i=>$row):
                        self::render_hero_slide_row((int)$i,(array)$row,$actions);
                    endforeach; ?>
                </div>
                <p><button type="button" class="button button-secondary" id="autoid-add-slide">+ Adaugă slide</button></p>
                <?php submit_button('Salvează Hero Slider'); ?>
            </form>
        </div>
        <style>
            .autoid-hero-row{background:#fff;border:1px solid #dcdcde;border-radius:12px;padding:18px;margin:16px 0;max-width:1050px}
            .autoid-hero-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px 18px}
            .autoid-hero-grid label{display:flex;flex-direction:column;font-weight:600;gap:5px}
            .autoid-hero-grid input[type=text],.autoid-hero-grid input[type=number],.autoid-hero-grid select,.autoid-hero-grid textarea{width:100%;font-weight:400}
            .autoid-hero-wide{grid-column:1/-1}.autoid-hero-actions{display:flex;gap:8px;align-items:center;margin-bottom:12px}
            .autoid-image-preview img{max-width:320px;max-height:140px;object-fit:contain;border:1px solid #e5e7eb;border-radius:8px;background:#f8fafc}
            @media(max-width:800px){.autoid-hero-grid{grid-template-columns:1fr}.autoid-hero-wide{grid-column:1}}
        </style>
        <script>
        (function($){
            const wrap=$('#autoid-hero-slides');
            const actions=<?php echo wp_json_encode($actions); ?>;
            function options(selected){return Object.entries(actions).map(([v,l])=>`<option value="${v}" ${v===selected?'selected':''}>${l}</option>`).join('')}
            function row(i){return `<div class="autoid-hero-row" data-index="${i}">
                <div class="autoid-hero-actions"><strong>Slide ${i+1}</strong><span style="flex:1"></span><button type="button" class="button autoid-up">↑</button><button type="button" class="button autoid-down">↓</button><button type="button" class="button-link-delete autoid-remove">Șterge</button></div>
                <div class="autoid-hero-grid">
                    <label><span>Activ</span><input type="checkbox" name="autoid_mobile_hero_slides[${i}][enabled]" value="1" checked></label>
                    <label>Titlu<input type="text" name="autoid_mobile_hero_slides[${i}][title]" required></label>
                    <label class="autoid-hero-wide">Descriere<textarea rows="3" name="autoid_mobile_hero_slides[${i}][description]"></textarea></label>
                    <label>ID imagine<input class="autoid-image-id" type="number" min="0" name="autoid_mobile_hero_slides[${i}][image_id]" value="0"><button type="button" class="button autoid-pick-image">Alege din Media Library</button><span class="autoid-image-preview"></span></label>
                    <span></span>
                    <label>Buton principal · text<input type="text" name="autoid_mobile_hero_slides[${i}][primary_label]" value="Vezi produsele"></label>
                    <label>Buton principal · tip<select name="autoid_mobile_hero_slides[${i}][primary_type]">${options('category')}</select></label>
                    <label>Buton principal · ID produs/categorie<input type="number" min="0" name="autoid_mobile_hero_slides[${i}][primary_target_id]" value="0"></label>
                    <span></span>
                    <label>Buton secundar · text<input type="text" name="autoid_mobile_hero_slides[${i}][secondary_label]" value="Consultanță"></label>
                    <label>Buton secundar · tip<select name="autoid_mobile_hero_slides[${i}][secondary_type]">${options('consultation')}</select></label>
                    <label>Buton secundar · ID produs/categorie<input type="number" min="0" name="autoid_mobile_hero_slides[${i}][secondary_target_id]" value="0"></label>
                </div></div>`}
            function reindex(){wrap.children('.autoid-hero-row').each(function(i){const r=$(this);r.attr('data-index',i);r.find('strong').first().text('Slide '+(i+1));r.find('[name]').each(function(){this.name=this.name.replace(/autoid_mobile_hero_slides\[\d+\]/,`autoid_mobile_hero_slides[${i}]`)})})}
            $('#autoid-add-slide').on('click',()=>{wrap.append(row(wrap.children().length));reindex()});
            wrap.on('click','.autoid-remove',function(){if(wrap.children().length>1)$(this).closest('.autoid-hero-row').remove();reindex()});
            wrap.on('click','.autoid-up',function(){const r=$(this).closest('.autoid-hero-row');r.prev().before(r);reindex()});
            wrap.on('click','.autoid-down',function(){const r=$(this).closest('.autoid-hero-row');r.next().after(r);reindex()});
            wrap.on('click','.autoid-pick-image',function(e){e.preventDefault();const box=$(this).closest('label');const frame=wp.media({title:'Alege imagine Hero',multiple:false,library:{type:'image'}});frame.on('select',()=>{const a=frame.state().get('selection').first().toJSON();box.find('.autoid-image-id').val(a.id);box.find('.autoid-image-preview').html(`<img src="${a.url}">`)});frame.open()});
        })(jQuery);
        </script>
        <?php
    }

    private static function render_hero_slide_row($i,$row,$actions) {
        $image_id=absint($row['image_id'] ?? 0);
        $image=$image_id ? wp_get_attachment_image_url($image_id,'medium') : '';
        ?>
        <div class="autoid-hero-row" data-index="<?php echo esc_attr($i); ?>">
            <div class="autoid-hero-actions"><strong>Slide <?php echo esc_html($i+1); ?></strong><span style="flex:1"></span><button type="button" class="button autoid-up">↑</button><button type="button" class="button autoid-down">↓</button><button type="button" class="button-link-delete autoid-remove">Șterge</button></div>
            <div class="autoid-hero-grid">
                <label><span>Activ</span><input type="checkbox" name="autoid_mobile_hero_slides[<?php echo $i; ?>][enabled]" value="1" <?php checked(!empty($row['enabled'])); ?>></label>
                <label>Titlu<input type="text" required name="autoid_mobile_hero_slides[<?php echo $i; ?>][title]" value="<?php echo esc_attr($row['title'] ?? ''); ?>"></label>
                <label class="autoid-hero-wide">Descriere<textarea rows="3" name="autoid_mobile_hero_slides[<?php echo $i; ?>][description]"><?php echo esc_textarea($row['description'] ?? ''); ?></textarea></label>
                <label>ID imagine<input class="autoid-image-id" type="number" min="0" name="autoid_mobile_hero_slides[<?php echo $i; ?>][image_id]" value="<?php echo esc_attr($image_id); ?>"><button type="button" class="button autoid-pick-image">Alege din Media Library</button><span class="autoid-image-preview"><?php if($image): ?><img src="<?php echo esc_url($image); ?>"><?php endif; ?></span></label>
                <span></span>
                <label>Buton principal · text<input type="text" name="autoid_mobile_hero_slides[<?php echo $i; ?>][primary_label]" value="<?php echo esc_attr($row['primary_label'] ?? ''); ?>"></label>
                <label>Buton principal · tip<select name="autoid_mobile_hero_slides[<?php echo $i; ?>][primary_type]"><?php foreach($actions as $value=>$label): ?><option value="<?php echo esc_attr($value); ?>" <?php selected(($row['primary_type'] ?? ''),$value); ?>><?php echo esc_html($label); ?></option><?php endforeach; ?></select></label>
                <label>Buton principal · ID produs/categorie<input type="number" min="0" name="autoid_mobile_hero_slides[<?php echo $i; ?>][primary_target_id]" value="<?php echo esc_attr(absint($row['primary_target_id'] ?? 0)); ?>"></label>
                <span></span>
                <label>Buton secundar · text<input type="text" name="autoid_mobile_hero_slides[<?php echo $i; ?>][secondary_label]" value="<?php echo esc_attr($row['secondary_label'] ?? ''); ?>"></label>
                <label>Buton secundar · tip<select name="autoid_mobile_hero_slides[<?php echo $i; ?>][secondary_type]"><?php foreach($actions as $value=>$label): ?><option value="<?php echo esc_attr($value); ?>" <?php selected(($row['secondary_type'] ?? ''),$value); ?>><?php echo esc_html($label); ?></option><?php endforeach; ?></select></label>
                <label>Buton secundar · ID produs/categorie<input type="number" min="0" name="autoid_mobile_hero_slides[<?php echo $i; ?>][secondary_target_id]" value="<?php echo esc_attr(absint($row['secondary_target_id'] ?? 0)); ?>"></label>
            </div>
        </div>
        <?php
    }

    private static function product_youtube_ids($content) {
        $ids=[];
        if(preg_match_all('~(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:watch\?(?:[^#\s]*&)?v=|embed/|shorts/))([A-Za-z0-9_-]{6,})~i',(string)$content,$m)){
            foreach((array)($m[1]??[]) as $id){$id=preg_replace('/[^A-Za-z0-9_-]/','',(string)$id);if($id!==''&&!in_array($id,$ids,true))$ids[]=$id;}
        }
        return $ids;
    }

    private static function product_description_html($content) {
        $raw=(string)$content;
        if(trim($raw)==='')return '';
        if($raw===wp_strip_all_tags($raw))$raw=wpautop(esc_html($raw));
        return wp_kses_post($raw);
    }

    public static function product_row(WC_Product $p,$detail=false) {
        $cats = wp_get_post_terms($p->get_id(),'product_cat',['fields'=>'all']);
        if (is_wp_error($cats)) $cats = [];
        $images = [];
        foreach (array_filter(array_merge([$p->get_image_id()],$p->get_gallery_image_ids())) as $id) {
            $u = wp_get_attachment_image_url($id,'large'); if ($u) $images[] = $u;
        }
        $attributes = [];
        if ($detail) {
            foreach ($p->get_attributes() as $a) {
                $name = wc_attribute_label($a->get_name());
                $values = $a->is_taxonomy() ? wc_get_product_terms($p->get_id(),$a->get_name(),['fields'=>'names']) : $a->get_options();
                $attributes[] = ['name'=>$name,'values'=>array_values(array_map('strval',$values))];
            }
        }
        $brand = self::brand_name($p);
        $model = self::model_context($p);
        $stock = self::stock_info($p);
        $price = wc_get_price_to_display($p);
        $regular = (float)$p->get_regular_price();
        $sale = (float)$p->get_sale_price();
        $rating = (float)$p->get_average_rating();
        if($p->is_type('grouped')){$pret_lista=get_post_meta($p->get_id(),'grp_pret_lista_mic',true);$pret_autoid_euro=get_post_meta($p->get_id(),'grp_pret_autoid_mic',true);if(!is_numeric($pret_lista))$pret_lista=get_post_meta($p->get_id(),'pret_lista',true);if(!is_numeric($pret_autoid_euro))$pret_autoid_euro=get_post_meta($p->get_id(),'pret_autoid_euro',true);}else{$pret_lista=get_post_meta($p->get_id(),'pret_lista',true);$pret_autoid_euro=get_post_meta($p->get_id(),'pret_autoid_euro',true);}
        $pret_lista=is_numeric($pret_lista)?(float)$pret_lista:0.0;$pret_autoid_euro=is_numeric($pret_autoid_euro)?(float)$pret_autoid_euro:0.0;
        $msrp_display = $pret_lista > 0 ? number_format($pret_lista,2,',','.').' €' : '';
        $autoid_euro_display = $pret_autoid_euro > 0 ? number_format($pret_autoid_euro,2,',','.').' € ex. TVA' : '';
        $regular_incl = $regular > 0 ? wc_get_price_including_tax($p,['price'=>$regular]) : 0.0;
        $current_incl = wc_get_price_including_tax($p,['price'=>(float)$p->get_price()]);
        $regular_incl_display = $regular_incl > 0 ? wp_strip_all_tags(wc_price($regular_incl)) : '';
        $current_incl_display = $current_incl > 0 ? wp_strip_all_tags(wc_price($current_incl)) : '';
        $price_range_ex=''; $price_range_incl=''; $grouped_parent_id=0; $grouped_child_ids=[];
        $grouped=self::grouped_parent($p);
        if($grouped){
            $grouped_parent_id=(int)$grouped->get_id(); $grouped_child_ids=array_values(array_map('intval',$grouped->get_children()));
            if($p->is_type('grouped')){
                $ex=[]; $inc=[];
                foreach($grouped_child_ids as $cid){$cp=wc_get_product($cid); if(!$cp || $cp->get_status()!=='publish') continue; $v=(float)$cp->get_price(); if($v>0){$ex[]=$v;$inc[]=wc_get_price_including_tax($cp,['price'=>$v]);}}
                if($ex){$min=min($ex);$max=max($ex);$price_range_ex=wp_strip_all_tags(wc_price($min)).($max>$min?' – '.wp_strip_all_tags(wc_price($max)):'').' ex. TVA';}
                if($inc){$min=min($inc);$max=max($inc);$price_range_incl=wp_strip_all_tags(wc_price($min)).($max>$min?' – '.wp_strip_all_tags(wc_price($max)):'').' incl. TVA';}
            }
        }
        $row = [
            'id'=>$p->get_id(),'name'=>$p->get_name(),'slug'=>$p->get_slug(),'sku'=>$p->get_sku(),'product_type'=>$p->get_type(),
            'brand'=>$brand,'brand_logo'=>self::brand_logo($p),'model'=>$model['label'],'model_key'=>$model['key'],'permalink'=>$p->get_permalink(),
            'image'=>self::image_url($p,$detail),'images'=>$images,
            'price'=>(string)$price,'regular_price'=>$regular?(string)$regular:'','sale_price'=>$sale?(string)$sale:'',
            'price_display'=>wp_strip_all_tags(wc_price($price)),'currency'=>get_woocommerce_currency(),
            'pret_lista'=>$pret_lista?:null,'pret_lista_display'=>$msrp_display,
            'pret_autoid_euro'=>$pret_autoid_euro?:null,'pret_autoid_euro_display'=>$autoid_euro_display,
            'regular_incl_vat_display'=>$regular_incl_display,'current_incl_vat_display'=>$current_incl_display,'price_range_ex_vat_display'=>$price_range_ex,'price_range_incl_vat_display'=>$price_range_incl,
            'grouped_parent_id'=>$grouped_parent_id,'grouped_child_ids'=>$grouped_child_ids,
            'grouped_stock_autoid'=>$p->is_type('grouped')?self::grouped_autoid_stock($p):null,'grouped_stock_distributor'=>$p->is_type('grouped')?self::grouped_distributor_stock($p):null,
            'regular_price_incl_vat_display'=>self::simple_vat_price_display($p,'regular'),
            'sale_price_incl_vat_display'=>self::simple_vat_price_display($p,'current'),
            'on_sale'=>$p->is_on_sale(),'in_stock'=>$p->is_in_stock(),'stock_status'=>$p->get_stock_status(),
            'stock_quantity'=>$p->managing_stock()?$p->get_stock_quantity():null,
            'stock_autoid'=>$stock['autoid'],'stock_distributor'=>$stock['distributor'],'delivery_label'=>$stock['delivery'],
            'availability_display'=>trim(($stock['autoid']>0?$stock['autoid'].' în stoc':'').(($stock['autoid']>0&&$stock['distributor']>0)?' · ':'').($stock['distributor']>0?$stock['distributor'].' livrare în 5–7 zile':'')),
            'stock_label'=>$p->is_in_stock()?($p->get_stock_status()==='onbackorder'?'Disponibil la comandă':'În stoc / disponibil'):'Stoc epuizat',
            'short_description'=>wp_strip_all_tags($p->get_short_description()),
            'category'=>$cats?$cats[0]->name:'','categories'=>array_map(fn($c)=>['id'=>(int)$c->term_id,'name'=>$c->name,'slug'=>$c->slug],$cats),
            'support_query'=>trim($brand.' '.$model['label'].' '.$p->get_sku()),'featured'=>$p->is_featured(),'type'=>$p->get_type(),
            'rating'=>$rating,'review_count'=>(int)$p->get_review_count(),
        ];
        if ($detail) {
            $raw_description=(string)$p->get_description();
            $row['description'] = wp_strip_all_tags($raw_description);
            $row['description_html'] = self::product_description_html($raw_description);
            $row['youtube_ids'] = self::product_youtube_ids($raw_description);
            $row['attributes'] = $attributes;
            $row['variation_ids'] = $p->is_type('variable')?array_map('intval',$p->get_children()):[];
            $row['upsell_ids'] = array_map('intval',$p->get_upsell_ids());
            $row['cross_sell_ids'] = array_map('intval',$p->get_cross_sell_ids());
        }
        return $row;
    }

    public static function health(WP_REST_Request $r) {
        return rest_ensure_response([
            'ok'=>true,
            'plugin'=>'AutoID Mobile',
            'version'=>'1.1.12',
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
        $client_id=self::mobile_google_client_id();
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

    private static function order_tracking_payload($order) {
        $awb='';
        foreach(['GLS_AWB','_GLS_AWB','AWB_GLS','_AWB_GLS','gls_awb','_gls_awb'] as $key){
            $value=trim((string)$order->get_meta($key,true));
            if($value!==''){$awb=$value;break;}
        }
        if($awb==='')return ['carrier'=>'','tracking_number'=>'','tracking_url'=>''];
        return ['carrier'=>'GLS','tracking_number'=>$awb,'tracking_url'=>'https://gls-group.eu/RO/ro/urmarire-colet.html?match='.rawurlencode($awb)];
    }

    public static function me_orders(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        $orders=wc_get_orders(['customer_id'=>$uid,'limit'=>20,'orderby'=>'date','order'=>'DESC']);
        $rows=[];
        foreach($orders as $o){$tracking=self::order_tracking_payload($o);$rows[]=['id'=>$o->get_id(),'number'=>$o->get_order_number(),'status'=>$o->get_status(),'status_label'=>wc_get_order_status_name($o->get_status()),'total'=>$o->get_total(),'currency'=>$o->get_currency(),'created_at'=>$o->get_date_created()?$o->get_date_created()->date('c'):null,'review_consent'=>$o->get_meta('_autoid_review_consent',true)==='yes','can_pay'=>$o->needs_payment() && !$o->is_paid() && $o->get_payment_method()==='stripe','can_cancel'=>!$o->is_paid() && $o->has_status(['pending','failed','on-hold'])]+$tracking;}
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
        $tracking=self::order_tracking_payload($order);return rest_ensure_response(['id'=>$order->get_id(),'number'=>$order->get_order_number(),'status'=>$order->get_status(),'status_label'=>wc_get_order_status_name($order->get_status()),'created_at'=>$order->get_date_created()?$order->get_date_created()->date('c'):'','currency'=>$order->get_currency(),'subtotal'=>(string)$subtotal_incl,'discount_total'=>(string)((float)$order->get_discount_total()+(float)$order->get_discount_tax()),'shipping_total'=>(string)((float)$order->get_shipping_total()+(float)$order->get_shipping_tax()),'tax_total'=>(string)$order->get_total_tax(),'total'=>(string)$order->get_total(),'payment_method'=>$order->get_payment_method_title(),'shipping_method'=>implode(', ',$ship),'customer_note'=>$order->get_customer_note(),'carrier'=>$tracking['carrier'],'tracking_number'=>$tracking['tracking_number'],'tracking_url'=>$tracking['tracking_url'],'review_consent'=>$order->get_meta('_autoid_review_consent',true)==='yes','can_pay'=>$order->needs_payment() && !$order->is_paid() && $order->get_payment_method()==='stripe','can_cancel'=>!$order->is_paid() && $order->has_status(['pending','failed','on-hold']),'billing'=>$billing,'shipping'=>$shipping,'items'=>$items,'notes'=>$notes]);
    }


    public static function me_order_action_v127(WP_REST_Request $r) {
        $ok=self::require_wc();if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id'));if(!$uid)$uid=self::bearer_user_id($r);
        $id=absint($r->get_param('id'));$order=$id?wc_get_order($id):null;
        if(!$order)return new WP_Error('autoid_order_missing','Comanda nu există.',['status'=>404]);
        if((int)$order->get_customer_id()!==$uid)return new WP_Error('autoid_order_forbidden','Comanda nu aparține contului curent.',['status'=>403]);
        $b=$r->get_json_params();if(!is_array($b))$b=[];$action=sanitize_key((string)($b['action']??''));
        if($action==='cancel'){
            if($order->is_paid()||!$order->has_status(['pending','failed','on-hold']))return new WP_Error('autoid_order_not_cancelable','Comanda nu mai poate fi anulată.',['status'=>409]);
            $order->update_status('cancelled','Comandă anulată de client din aplicația AutoID.');
            return rest_ensure_response(['ok'=>true,'order_id'=>$order->get_id(),'status'=>$order->get_status()]);
        }
        if($action==='pay'){
            if($order->is_paid()||!$order->needs_payment())return new WP_Error('autoid_order_not_payable','Comanda nu mai necesită plată.',['status'=>409]);
            if($order->get_payment_method()!=='stripe')return new WP_Error('autoid_order_payment_method','Plata din aplicație este disponibilă pentru comenzile Stripe.',['status'=>409]);
            $pi=self::stripe_create_intent_for_order($order);if(is_wp_error($pi))return $pi;
            $order->add_order_note('Plata a fost reluată de client din aplicația AutoID.');
            return rest_ensure_response(['ok'=>true,'order_id'=>$order->get_id(),'stripe_publishable_key'=>self::stripe_publishable(),'stripe_client_secret'=>$pi['client_secret'],'stripe_payment_intent_id'=>$pi['payment_intent_id'],'stripe_payment_token'=>$pi['payment_token'],'stripe_mode'=>'test']);
        }
        return new WP_Error('autoid_order_action','Acțiune invalidă.',['status'=>400]);
    }

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
            if(array_key_exists('email',$b)){$email=sanitize_email((string)$b['email']);if(!$email||!is_email($email))return new WP_Error('autoid_bad_email','Adresa de email nu este validă.',['status'=>400]);$existing=email_exists($email);if($existing&&(int)$existing!==$uid)return new WP_Error('autoid_email_exists','Există deja un cont cu această adresă de email.',['status'=>409]);$updated=wp_update_user(['ID'=>$uid,'user_email'=>$email]);if(is_wp_error($updated))return $updated;if(method_exists($customer,'set_billing_email'))$customer->set_billing_email($email);}
            $password=(string)($b['new_password']??'');if($password!==''){if(strlen($password)<8)return new WP_Error('autoid_password_short','Parola nouă trebuie să aibă cel puțin 8 caractere.',['status'=>400]);wp_set_password($password,$uid);}
            $customer->save();$customer=new WC_Customer($uid);
        }
        return rest_ensure_response(['profile'=>['id'=>$uid,'email'=>$customer->get_email(),'first_name'=>$customer->get_first_name(),'last_name'=>$customer->get_last_name()]]);
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
            if(array_key_exists('vat_number',$b)){$vat=sanitize_text_field((string)$b['vat_number']);update_user_meta($uid,'_eu_vat_guard_vat_number',$vat);update_user_meta($uid,'billing_vat',$vat);update_user_meta($uid,'vat_number',$vat);}
        }
        $vat=(string)get_user_meta($uid,'_eu_vat_guard_vat_number',true);if($vat==='')$vat=(string)get_user_meta($uid,'billing_vat',true);if($vat==='')$vat=(string)get_user_meta($uid,'vat_number',true);return rest_ensure_response(['billing'=>self::account_address_payload($customer,'billing'),'shipping'=>self::account_address_payload($customer,'shipping'),'vat_number'=>$vat]);
    }

    public static function me_payment_methods(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id')); if(!$uid)$uid=self::bearer_user_id($r);
        if($r->get_method()==='POST'){$b=$r->get_json_params();if(!is_array($b))$b=[];$token_id=absint($b['token_id']??0);$action=sanitize_key((string)($b['action']??''));$token=$token_id&&class_exists('WC_Payment_Tokens')?WC_Payment_Tokens::get($token_id):null;if(!$token||!is_object($token)||(int)$token->get_user_id()!==$uid)return new WP_Error('autoid_payment_token_invalid','Metoda de plată nu este validă.',['status'=>404]);if($action==='set_default')WC_Payment_Tokens::set_users_default($uid,$token_id);elseif($action==='delete')WC_Payment_Tokens::delete($token_id);else return new WP_Error('autoid_payment_action','Acțiune invalidă pentru metoda de plată.',['status'=>400]);}
        $tokens=class_exists('WC_Payment_Tokens')?WC_Payment_Tokens::get_customer_tokens($uid):[];$default=class_exists('WC_Payment_Tokens')?WC_Payment_Tokens::get_customer_default_token($uid):null;$default_id=$default&&is_object($default)?(int)$default->get_id():0;$rows=[];
        foreach((array)$tokens as $token){if(!is_object($token)||!method_exists($token,'get_id'))continue;$label=method_exists($token,'get_display_name')?(string)$token->get_display_name():(method_exists($token,'get_type')?(string)$token->get_type():'Metodă salvată');$rows[]=['id'=>(int)$token->get_id(),'type'=>method_exists($token,'get_type')?(string)$token->get_type():'','label'=>wp_strip_all_tags($label),'is_default'=>(int)$token->get_id()===$default_id];}
        return rest_ensure_response(['methods'=>$rows]);
    }

    private static function stripe_publishable() {
        $manual=trim((string)get_option('autoid_mobile_stripe_publishable_test',''));
        if(str_starts_with($manual,'pk_test_')) return $manual;
        foreach(['woocommerce_stripe_settings','woocommerce_stripe_cc_settings'] as $opt){
            $cfg=get_option($opt,[]); if(!is_array($cfg)||($cfg['testmode']??'no')!=='yes') continue;
            foreach(['test_publishable_key','test_pk','publishable_key'] as $key){$v=trim((string)($cfg[$key]??''));if(str_starts_with($v,'pk_test_'))return $v;}
        }
        return '';
    }

    private static function stripe_secret() {
        $manual=trim((string)get_option('autoid_mobile_stripe_secret_test',''));
        if(str_starts_with($manual,'sk_test_')) return $manual;
        foreach(['woocommerce_stripe_settings','woocommerce_stripe_cc_settings'] as $opt){
            $cfg=get_option($opt,[]); if(!is_array($cfg)||($cfg['testmode']??'no')!=='yes') continue;
            foreach(['test_secret_key','test_sk','secret_key'] as $key){$v=trim((string)($cfg[$key]??''));if(str_starts_with($v,'sk_test_'))return $v;}
        }
        return '';
    }

    private static function stripe_sandbox_ready() {
        return str_starts_with(self::stripe_publishable(),'pk_test_') && str_starts_with(self::stripe_secret(),'sk_test_');
    }

    private static function stripe_request($method,$path,$body=[]) {
        $secret=self::stripe_secret();
        if(!str_starts_with($secret,'sk_test_')) return new WP_Error('autoid_stripe_not_configured','Stripe Sandbox nu este configurat.',['status'=>409]);
        $args=['method'=>$method,'timeout'=>20,'headers'=>['Authorization'=>'Bearer '.$secret]];
        if($body)$args['body']=$body;
        $response=wp_remote_request('https://api.stripe.com/v1/'.$path,$args);
        if(is_wp_error($response))return new WP_Error('autoid_stripe_error',$response->get_error_message(),['status'=>502]);
        $code=(int)wp_remote_retrieve_response_code($response);$data=json_decode(wp_remote_retrieve_body($response),true);
        if($code<200||$code>=300||!is_array($data))return new WP_Error('autoid_stripe_error',sanitize_text_field((string)($data['error']['message']??'Stripe a returnat o eroare.')),['status'=>502]);
        return $data;
    }

    private static function stripe_create_intent_for_order($order) {
        if(!$order||!is_a($order,'WC_Order'))return new WP_Error('autoid_order_missing','Comanda nu există.',['status'=>404]);
        if(!self::stripe_sandbox_ready())return new WP_Error('autoid_stripe_not_configured','Configurează cheile pk_test_ și sk_test_ în WooCommerce → AutoID App Home.',['status'=>409]);
        $amount=(int)round(((float)$order->get_total())*100);if($amount<50)return new WP_Error('autoid_stripe_amount','Valoarea comenzii este invalidă pentru Stripe.',['status'=>400]);
        $data=self::stripe_request('POST','payment_intents',[
            'amount'=>$amount,
            'currency'=>strtolower($order->get_currency()),
            'automatic_payment_methods[enabled]'=>'true',
            'metadata[order_id]'=>(string)$order->get_id(),
            'metadata[source]'=>'autoid_android',
            'description'=>'AutoID order #'.$order->get_order_number(),
            'receipt_email'=>$order->get_billing_email(),
        ]);
        if(is_wp_error($data))return $data;
        if(empty($data['id'])||empty($data['client_secret']))return new WP_Error('autoid_stripe_invalid','Stripe nu a returnat PaymentIntent complet.',['status'=>502]);
        $token=wp_generate_password(64,false,false);
        $order->update_meta_data('_autoid_stripe_payment_intent',sanitize_text_field((string)$data['id']));
        $order->update_meta_data('_autoid_stripe_payment_token_hash',hash('sha256',$token));
        $order->update_meta_data('_autoid_stripe_mode','test');
        $order->save();
        return ['payment_intent_id'=>(string)$data['id'],'client_secret'=>(string)$data['client_secret'],'payment_token'=>$token,'amount'=>$amount,'currency'=>strtolower($order->get_currency())];
    }

    private static function stripe_order_access($order,WP_REST_Request $r,$payment_token='') {
        if(!$order)return false;
        $uid=self::bearer_user_id($r);
        if($uid>0 && (int)$order->get_customer_id()===$uid)return true;
        $expected=(string)$order->get_meta('_autoid_stripe_payment_token_hash',true);
        return $expected!=='' && $payment_token!=='' && hash_equals($expected,hash('sha256',$payment_token));
    }

    public static function payment_intent(WP_REST_Request $r) {
        $ok=self::require_wc();if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id'));if(!$uid)$uid=self::bearer_user_id($r);
        $b=$r->get_json_params();if(!is_array($b))$b=[];$oid=absint($b['order_id']??0);
        $order=$oid?wc_get_order($oid):null;if(!$order)return new WP_Error('autoid_order_missing','Comanda nu există.',['status'=>404]);
        if((int)$order->get_customer_id()!==$uid)return new WP_Error('autoid_order_forbidden','Comanda nu aparține contului curent.',['status'=>403]);
        if($order->is_paid())return new WP_Error('autoid_order_paid','Comanda este deja plătită.',['status'=>409]);
        $pi=self::stripe_create_intent_for_order($order);if(is_wp_error($pi))return $pi;
        return rest_ensure_response(['payment_intent_id'=>$pi['payment_intent_id'],'client_secret'=>$pi['client_secret'],'order_id'=>$order->get_id(),'amount'=>$pi['amount'],'currency'=>$pi['currency'],'publishable_key'=>self::stripe_publishable(),'mode'=>'test']);
    }

    public static function stripe_confirm(WP_REST_Request $r) {
        $ok=self::require_wc();if(is_wp_error($ok))return $ok;
        $b=$r->get_json_params();if(!is_array($b))$b=[];
        $oid=absint($b['order_id']??0);$pi_id=sanitize_text_field((string)($b['payment_intent_id']??''));$payment_token=(string)($b['payment_token']??'');
        $order=$oid?wc_get_order($oid):null;if(!$order)return new WP_Error('autoid_order_missing','Comanda nu există.',['status'=>404]);
        if(!self::stripe_order_access($order,$r,$payment_token))return new WP_Error('autoid_order_forbidden','Confirmarea plății nu este autorizată.',['status'=>403]);
        $stored=(string)$order->get_meta('_autoid_stripe_payment_intent',true);if($stored===''||$pi_id===''||!hash_equals($stored,$pi_id))return new WP_Error('autoid_stripe_mismatch','PaymentIntent nu corespunde comenzii.',['status'=>409]);
        $pi=self::stripe_request('GET','payment_intents/'.rawurlencode($pi_id));if(is_wp_error($pi))return $pi;
        $expected_amount=(int)round(((float)$order->get_total())*100);$expected_currency=strtolower($order->get_currency());
        if((string)($pi['status']??'')!=='succeeded')return new WP_Error('autoid_stripe_not_paid','Plata Stripe nu este încă finalizată.',['status'=>409,'stripe_status'=>sanitize_text_field((string)($pi['status']??''))]);
        if((int)($pi['amount']??0)!==$expected_amount)return new WP_Error('autoid_stripe_amount_mismatch','Suma Stripe nu corespunde comenzii.',['status'=>409]);
        if(strtolower((string)($pi['currency']??''))!==$expected_currency)return new WP_Error('autoid_stripe_currency_mismatch','Moneda Stripe nu corespunde comenzii.',['status'=>409]);
        // Stripe metadata['order_id'] is verified against the WooCommerce order before payment_complete().
        if((int)($pi['metadata']['order_id']??0)!==$order->get_id())return new WP_Error('autoid_stripe_order_mismatch','Metadatele Stripe nu corespund comenzii.',['status'=>409]);
        if(!$order->is_paid()){$order->payment_complete($pi_id);$order->add_order_note('Plată Stripe Sandbox confirmată server-side pentru PaymentIntent '.$pi_id.'.');}
        $order->delete_meta_data('_autoid_stripe_payment_token_hash');$order->save();
        return rest_ensure_response(['paid'=>true,'order_id'=>$order->get_id(),'status'=>$order->get_status(),'payment_intent_id'=>$pi_id,'stripe_status'=>'succeeded','mode'=>'test']);
    }

    public static function hero_studio_menu() {
        add_submenu_page(
            'woocommerce',
            'AutoID Mega Menu Hero · App',
            'AutoID Hero · App',
            'manage_woocommerce',
            'autoid-mobile-hero-studio',
            [__CLASS__,'render_hero_studio']
        );
    }

    private static function hero_category_options_html($selected=0) {
        $terms=get_terms(['taxonomy'=>'product_cat','hide_empty'=>false,'orderby'=>'name','order'=>'ASC']);
        if(is_wp_error($terms)) return '';
        $by_parent=[];
        foreach($terms as $t) $by_parent[(int)$t->parent][]=$t;
        $html='';
        $walk=function($parent,$depth) use (&$walk,&$by_parent,$selected,&$html){
            foreach(($by_parent[$parent] ?? []) as $t){
                $prefix=str_repeat('— ',max(0,$depth));
                $html.='<option value="'.esc_attr((string)$t->term_id).'" '.selected((int)$selected,(int)$t->term_id,false).'>'.esc_html($prefix.$t->name).'</option>';
                $walk((int)$t->term_id,$depth+1);
            }
        };
        $walk(0,0);
        return $html;
    }

    public static function render_hero_studio() {
        if(!current_user_can('manage_woocommerce')) return;
        wp_enqueue_media();
        $settings=get_option('autoid_mega_menu_settings',[]);
        if(!is_array($settings)) $settings=[];
        $slides=is_array($settings['slides'] ?? null) ? array_values($settings['slides']) : [];
        $overrides=self::maybe_migrate_legacy_hero_overrides($slides,self::hero_app_overrides());

        if($_SERVER['REQUEST_METHOD']==='POST' && isset($_POST['autoid_hero_studio_nonce'])){
            check_admin_referer('autoid_hero_studio_save','autoid_hero_studio_nonce');
            $posted=is_array($_POST['slides'] ?? null) ? wp_unslash($_POST['slides']) : [];
            $next=[];
            foreach($slides as $i=>$row){
                $in=is_array($posted[$i] ?? null) ? $posted[$i] : [];
                $style=sanitize_key((string)($in['app_style'] ?? 'card'));
                $type=sanitize_key((string)($in['app_action_type'] ?? 'none'));
                $allowed=['none','catalog','category','product_sku','consultation','ai'];
                $next[$i]=[
                    'app_enabled'=>!empty($in['app_enabled']) ? 1 : 0,
                    'app_image_id'=>absint($in['app_image_id'] ?? 0),
                    'app_image'=>esc_url_raw((string)($in['app_image'] ?? '')),
                    'app_style'=>in_array($style,['card','background'],true)?$style:'card',
                    'app_button_text'=>sanitize_text_field((string)($in['app_button_text'] ?? '')),
                    'app_action_type'=>in_array($type,$allowed,true)?$type:'none',
                    'app_action_value'=>sanitize_text_field((string)($in['app_action_value'] ?? '')),
                    'app_accent'=>sanitize_hex_color((string)($in['app_accent'] ?? '')) ?: '',
                ];
            }
            $overrides=$next;
            update_option('autoid_mobile_hero_app_overrides',$overrides,false);
            update_option('autoid_mobile_hero_last_saved',time(),false);
            echo '<div class="notice notice-success is-dismissible"><p><strong>AutoID Hero App salvat.</strong> Configurația este live; aplicația o va reîncărca automat. Setările website-ului au fost păstrate.</p></div>';
        }

        echo '<div class="wrap autoid-hero-studio"><h1>AutoID Mega Menu Hero · App</h1>';
        echo '<p class="description">Website și aplicația folosesc același set de slide-uri, dar <strong>imaginea, stilul și destinația din app sunt independente</strong>. Câmpurile website-ului nu sunt modificate aici.</p>';
        if(!$slides){ echo '<div class="notice notice-warning"><p>Nu există slide-uri în <code>autoid_mega_menu_settings</code>. Adaugă-le mai întâi din AutoID Mega Menu Hero.</p></div></div>'; return; }
        echo '<form method="post">'; wp_nonce_field('autoid_hero_studio_save','autoid_hero_studio_nonce');
        echo '<div class="aid-hero-grid">';
        foreach($slides as $i=>$row){
            $app=is_array($overrides[$i] ?? null) ? $overrides[$i] : [];
            $merged=array_merge($row,$app);
            $enabled=!array_key_exists('app_enabled',$merged) || !empty($merged['app_enabled']);
            $app_image_id=absint($merged['app_image_id'] ?? 0);
            $app_image=$app_image_id ? (wp_get_attachment_image_url($app_image_id,'medium') ?: '') : esc_url((string)($merged['app_image'] ?? ''));
            $web_image=esc_url((string)($row['image'] ?? ''));
            $style=sanitize_key((string)($merged['app_style'] ?? 'card'));
            $type=sanitize_key((string)($merged['app_action_type'] ?? ''));
            $value=(string)($merged['app_action_value'] ?? '');
            $button=(string)($merged['app_button_text'] ?? ($row['button_text'] ?? ''));
            echo '<section class="aid-hero-card" data-slide="'.esc_attr((string)$i).'">';
            echo '<div class="aid-card-head"><div><span>SLIDE '.esc_html((string)($i+1)).'</span><h2>'.esc_html((string)($row['title'] ?? 'Fără titlu')).'</h2></div><label class="aid-switch"><input type="checkbox" name="slides['.$i.'][app_enabled]" value="1" '.checked($enabled,true,false).'> Activ în App</label></div>';
            echo '<div class="aid-web-ref"><strong>Website</strong><span>'.esc_html((string)($row['button_url'] ?? 'Fără link')).'</span>'.($web_image?'<img src="'.$web_image.'" alt="">':'<em>Fără imagine website</em>').'</div>';
            echo '<div class="aid-fields">';
            echo '<label><span>Hero Style în App</span><select name="slides['.$i.'][app_style]"><option value="card" '.selected($style,'card',false).'>Card · imagine separată în dreapta</option><option value="background" '.selected($style,'background',false).'>Background · imagine full + text overlay</option></select></label>';
            echo '<label><span>Text buton App</span><input type="text" name="slides['.$i.'][app_button_text]" value="'.esc_attr($button).'" placeholder="Ex. Vezi produsele"></label>';
            echo '<label><span>Destinație App</span><select class="aid-action-type" name="slides['.$i.'][app_action_type]"><option value="" '.selected($type,'',false).'>Auto (compatibilitate din link website)</option><option value="none" '.selected($type,'none',false).'>Fără acțiune / fără buton</option><option value="catalog" '.selected($type,'catalog',false).'>Catalog</option><option value="category" '.selected($type,'category',false).'>Categorie / Subcategorie</option><option value="product_sku" '.selected($type,'product_sku',false).'>Produs după SKU</option><option value="ai" '.selected($type,'ai',false).'>AutoID AI</option><option value="consultation" '.selected($type,'consultation',false).'>Consultanță</option></select></label>';
            echo '<label class="aid-action-value"><span>SKU / ID categorie</span><input class="aid-action-input" type="text" name="slides['.$i.'][app_action_value]" value="'.esc_attr($value).'" placeholder="SKU produs sau ID categorie"><select class="aid-category-select"><option value="">Alege categoria / subcategoria…</option>'.self::hero_category_options_html($type==='category'?absint($value):0).'</select></label>';
            echo '<label><span>Accent App (opțional)</span><input type="color" name="slides['.$i.'][app_accent]" value="'.esc_attr(sanitize_hex_color($merged['app_accent'] ?? '') ?: '#f7630c').'"></label>';
            echo '</div>';
            echo '<div class="aid-image-field"><div><strong>Imagine App</strong><p>Separată de website. Dacă rămâne goală, APK-ul <strong>nu inventează și nu preia altă imagine</strong>.</p></div><input class="aid-image-id" type="hidden" name="slides['.$i.'][app_image_id]" value="'.esc_attr((string)$app_image_id).'"><input class="aid-image-url" type="hidden" name="slides['.$i.'][app_image]" value="'.esc_attr((string)($merged['app_image'] ?? '')).'"><div class="aid-app-preview">'.($app_image?'<img src="'.esc_url($app_image).'" alt="">':'<span>Fără imagine App</span>').'</div><div class="aid-media-actions"><button type="button" class="button button-primary aid-pick-image">Alege imagine App</button><button type="button" class="button aid-clear-image">Elimină</button></div></div>';
            echo '</section>';
        }
        echo '</div><p class="submit"><button type="submit" class="button button-primary button-hero">Salvează Hero App</button></p></form></div>';
        ?>
        <style>
        .autoid-hero-studio{max-width:1280px}.autoid-hero-studio>.description{font-size:14px;margin-bottom:20px}.aid-hero-grid{display:grid;gap:18px}.aid-hero-card{background:#fff;border:1px solid #d9e1ea;border-radius:18px;padding:20px;box-shadow:0 6px 20px rgba(16,35,58,.04)}.aid-card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;border-bottom:1px solid #edf0f3;padding-bottom:14px;margin-bottom:16px}.aid-card-head span{font-size:11px;font-weight:800;color:#f7630c;letter-spacing:.08em}.aid-card-head h2{margin:4px 0 0;font-size:18px}.aid-switch{font-weight:700}.aid-web-ref{display:grid;grid-template-columns:100px minmax(240px,1fr) 110px;gap:14px;align-items:center;background:#f7f8fa;border-radius:12px;padding:10px 12px;margin-bottom:16px;color:#5d6878}.aid-web-ref img{width:100px;height:54px;object-fit:contain;background:#fff;border-radius:8px}.aid-web-ref em{font-size:12px}.aid-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.aid-fields label{display:grid;gap:6px}.aid-fields label>span{font-size:12px;font-weight:800;color:#56657a}.aid-fields input[type=text],.aid-fields select{width:100%;min-height:42px}.aid-action-value{grid-template-columns:1fr}.aid-category-select{display:none}.aid-image-field{display:grid;grid-template-columns:minmax(220px,1fr) 160px auto;gap:16px;align-items:center;margin-top:18px;padding-top:16px;border-top:1px solid #edf0f3}.aid-image-field p{margin:4px 0;color:#667085}.aid-app-preview{width:160px;height:96px;border-radius:12px;background:#f5f7fa;border:1px dashed #cbd5e1;display:grid;place-items:center;overflow:hidden;color:#7b8798}.aid-app-preview img{width:100%;height:100%;object-fit:contain;background:#fff}.aid-media-actions{display:flex;gap:8px;flex-wrap:wrap}.button-hero{min-height:46px;padding:0 22px!important;font-weight:700}.aid-fields input[type=color]{width:100%;height:42px;padding:2px}.aid-action-value.is-category .aid-category-select{display:block}.aid-action-value.is-category .aid-action-input{display:none}@media(max-width:800px){.aid-fields{grid-template-columns:1fr}.aid-web-ref{grid-template-columns:1fr}.aid-image-field{grid-template-columns:1fr}.aid-card-head{flex-direction:column}}
        </style>
        <script>
        jQuery(function($){
            function syncAction($card){var type=$card.find('.aid-action-type').val();var $wrap=$card.find('.aid-action-value');$wrap.toggleClass('is-category',type==='category');}
            $('.aid-hero-card').each(function(){syncAction($(this));});
            $(document).on('change','.aid-action-type',function(){syncAction($(this).closest('.aid-hero-card'));});
            $(document).on('change','.aid-category-select',function(){var $card=$(this).closest('.aid-hero-card');$card.find('.aid-action-input').val($(this).val());});
            $(document).on('click','.aid-pick-image',function(e){e.preventDefault();var $card=$(this).closest('.aid-hero-card');var frame=wp.media({title:'Imagine Hero pentru aplicația AutoID',button:{text:'Folosește în App'},multiple:false});frame.on('select',function(){var a=frame.state().get('selection').first().toJSON();$card.find('.aid-image-id').val(a.id||'');$card.find('.aid-image-url').val(a.url||'');$card.find('.aid-app-preview').html('<img src="'+a.url+'" alt="">');});frame.open();});
            $(document).on('click','.aid-clear-image',function(e){e.preventDefault();var $card=$(this).closest('.aid-hero-card');$card.find('.aid-image-id,.aid-image-url').val('');$card.find('.aid-app-preview').html('<span>Fără imagine App</span>');});
        });
        </script>
        <?php
    }

}

AutoID_Mobile_115::boot();


register_activation_hook(__FILE__, function(){
    if(!function_exists('deactivate_plugins')) require_once ABSPATH.'wp-admin/includes/plugin.php';
    $self=plugin_basename(__FILE__);
    foreach(['autoid-mobile-api/autoid-mobile-api.php','autoid-mobile-commerce/autoid-mobile-commerce.php'] as $legacy){
        if($legacy!==$self && is_plugin_active($legacy)) deactivate_plugins($legacy,true);
    }
    flush_rewrite_rules(false);
});
