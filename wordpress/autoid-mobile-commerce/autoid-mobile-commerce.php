<?php
/**
 * Plugin Name: AutoID Mobile Commerce Bridge
 * Description: Mobile catalog, product-family, support and search bridge for AutoID. Coexists with AutoID Mobile API auth/order/payment routes.
 * Version: 0.4.0
 * Author: AutoID / SOFA SOFT SRL
 * Requires at least: 6.5
 * Requires PHP: 8.0
 * WC requires at least: 9.0
 */

if (!defined('ABSPATH')) exit;

final class AutoID_Mobile_Commerce_Bridge_040 {
    const NS = 'autoid-app/v1';
    const CACHE_TTL = 600;

    public static function boot() {
        add_action('rest_api_init', [__CLASS__, 'routes']);
    }

    public static function routes() {
        $public = ['permission_callback' => '__return_true'];
        register_rest_route(self::NS, '/home', $public + ['methods'=>'GET','callback'=>[__CLASS__,'home']]);
        register_rest_route(self::NS, '/products', $public + ['methods'=>'GET','callback'=>[__CLASS__,'products']]);
        register_rest_route(self::NS, '/products/(?P<id>\d+)', $public + ['methods'=>'GET','callback'=>[__CLASS__,'product']]);
        register_rest_route(self::NS, '/products/(?P<id>\d+)/family', $public + ['methods'=>'GET','callback'=>[__CLASS__,'family']]);
        register_rest_route(self::NS, '/products/(?P<id>\d+)/family/(?P<group>[a-z-]+)', $public + ['methods'=>'GET','callback'=>[__CLASS__,'family_group']]);
        register_rest_route(self::NS, '/products/(?P<id>\d+)/support', $public + ['methods'=>'GET','callback'=>[__CLASS__,'product_support']]);
        register_rest_route(self::NS, '/categories', $public + ['methods'=>'GET','callback'=>[__CLASS__,'categories']]);
        register_rest_route(self::NS, '/search', $public + ['methods'=>'GET','callback'=>[__CLASS__,'search']]);
        register_rest_route(self::NS, '/support', $public + ['methods'=>'GET','callback'=>[__CLASS__,'support']]);
        register_rest_route(self::NS, '/brands', $public + ['methods'=>'GET','callback'=>[__CLASS__,'brands']]);
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
        $stock = wc_get_products(['status'=>'publish','limit'=>10,'orderby'=>'date','order'=>'DESC','stock_status'=>'instock']);
        $featured = wc_get_products(['status'=>'publish','limit'=>10,'featured'=>true,'orderby'=>'date','order'=>'DESC']);
        if (!$featured) $featured = wc_get_products(['status'=>'publish','limit'=>10,'orderby'=>'popularity','order'=>'DESC']);
        return rest_ensure_response([
            'app'=>['name'=>'AutoID','tagline'=>'Professional Solutions','version'=>'0.4.0'],
            'hero'=>['title'=>'Echipamente AutoID pentru afacerea ta','subtitle'=>'Scanare, etichetare, mobilitate, RFID și soluții profesionale.'],
            'categories'=>array_slice(self::category_rows(),0,12),
            'in_stock'=>array_map([__CLASS__,'product_row'],$stock),
            'recommended'=>array_map([__CLASS__,'product_row'],$featured),
            'brands'=>self::brand_rows(16),
        ]);
    }

    public static function products(WP_REST_Request $r) {
        $ok = self::require_wc(); if (is_wp_error($ok)) return $ok;
        $page = self::int_param($r,'page',1,1,100000);
        $per = self::int_param($r,'per_page',20,1,50);
        $args = ['status'=>'publish','limit'=>$per,'page'=>$page,'paginate'=>true,'return'=>'objects'];
        $search = sanitize_text_field((string)$r->get_param('search'));
        if ($search !== '') $args['search'] = '*'.$search.'*';
        $category = absint($r->get_param('category'));
        if ($category) {
            $term = get_term($category,'product_cat');
            if ($term && !is_wp_error($term)) $args['category'] = [$term->slug];
        }
        $stock = sanitize_key((string)$r->get_param('stock'));
        if (in_array($stock,['instock','outofstock','onbackorder'],true)) $args['stock_status'] = $stock;
        $orderby = sanitize_key((string)$r->get_param('orderby'));
        $order = strtoupper(sanitize_text_field((string)$r->get_param('order')));
        if (in_array($orderby,['date','price','popularity','rating','title'],true)) $args['orderby'] = $orderby;
        if (in_array($order,['ASC','DESC'],true)) $args['order'] = $order;
        $result = wc_get_products($args);
        return rest_ensure_response([
            'products'=>array_map([__CLASS__,'product_row'],$result->products),
            'page'=>$page,'per_page'=>$per,'total'=>(int)$result->total,'pages'=>(int)$result->max_num_pages
        ]);
    }

    public static function product(WP_REST_Request $r) {
        $ok = self::require_wc(); if (is_wp_error($ok)) return $ok;
        $p = self::published_product(absint($r['id']));
        if (is_wp_error($p)) return $p;
        return rest_ensure_response(self::product_row($p,true));
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
        $total = count($ids);
        $slice = array_slice($ids,($page-1)*$per,$per);
        $products = [];
        foreach ($slice as $id) {
            $row = wc_get_product($id);
            if ($row && $row->get_status()==='publish') $products[] = self::product_row($row,false);
        }
        return rest_ensure_response([
            'group'=>['key'=>$key,'label'=>self::group_labels()[$key]],
            'model'=>$data['model'],'count'=>$total,'page'=>$page,'per_page'=>$per,
            'pages'=>$total ? (int)ceil($total/$per) : 0,'products'=>$products,
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
        return rest_ensure_response(['categories'=>self::category_rows()]);
    }

    public static function brands(WP_REST_Request $r) {
        return rest_ensure_response(['brands'=>self::brand_rows(100)]);
    }

    public static function search(WP_REST_Request $r) {
        $q = sanitize_text_field((string)$r->get_param('q'));
        if (mb_strlen($q)<2) return rest_ensure_response(['suggestions'=>[]]);
        $products = wc_get_products(['status'=>'publish','limit'=>10,'search'=>'*'.$q.'*']);
        $suggestions = [];
        foreach ($products as $p) {
            $suggestions[] = ['type'=>'product','id'=>$p->get_id(),'label'=>$p->get_name(),'sku'=>$p->get_sku(),'image'=>self::image_url($p),'query'=>$p->get_name()];
        }
        return rest_ensure_response(['suggestions'=>$suggestions]);
    }

    public static function support(WP_REST_Request $r) {
        $q = sanitize_text_field((string)$r->get_param('search'));
        if ($q==='') return rest_ensure_response(['resources'=>[]]);
        return rest_ensure_response(['resources'=>self::support_rows($q,30)]);
    }

    private static function published_product($id) {
        $p = wc_get_product($id);
        if (!$p || $p->get_status()!=='publish') return new WP_Error('autoid_product_not_found','Product not found.',['status'=>404]);
        return $p;
    }

    private static function category_rows() {
        $terms = get_terms(['taxonomy'=>'product_cat','hide_empty'=>true,'parent'=>0,'orderby'=>'count','order'=>'DESC']);
        if (is_wp_error($terms)) return [];
        return array_map(function($t){
            $thumb = absint(get_term_meta($t->term_id,'thumbnail_id',true));
            return ['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug,'count'=>(int)$t->count,'image'=>$thumb?wp_get_attachment_image_url($thumb,'woocommerce_thumbnail'):null];
        },$terms);
    }

    private static function brand_rows($limit) {
        foreach (['product_brand','pa_brand','brand'] as $tax) {
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
        foreach (['product_brand','pa_brand','brand'] as $tax) {
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

    private static function model_context(WC_Product $p) {
        $id = $p->get_id();
        $candidates = [];
        foreach (['pa_model','product_model','model','autoid_model','product_tag'] as $tax) {
            if (!taxonomy_exists($tax)) continue;
            $terms = wp_get_post_terms($id,$tax);
            if (is_wp_error($terms)) continue;
            foreach ($terms as $t) {
                $score = (stripos($tax,'model')!==false ? 100 : 20) + (preg_match('/^[a-z]{1,5}-?\d{2,5}[a-z0-9-]*$/i',$t->slug)?20:0);
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

    private static function family_data(WC_Product $p) {
        $model = self::model_context($p);
        $cache_key = 'autoid_mob_family_'.md5($p->get_id().'|'.$model['key'].'|0.4');
        $cached = get_transient($cache_key);
        if (is_array($cached)) return $cached;
        $ids = self::family_candidate_ids($p,$model);
        $groups = array_fill_keys(array_keys(self::group_labels()),[]);
        foreach ($ids as $id) {
            if ((int)$id === (int)$p->get_id()) continue;
            $rp = wc_get_product($id);
            if (!$rp || $rp->get_status()!=='publish') continue;
            $groups[self::product_group($rp)][] = (int)$id;
        }
        foreach ($groups as $key=>$rows) $groups[$key] = array_values(array_unique($rows));
        $source = ['strategy'=>'model+taxonomy','taxonomy'=>$model['taxonomy'],'candidate_count'=>count($ids)];
        $data = ['model'=>$model,'source'=>$source,'groups'=>$groups];
        set_transient($cache_key,$data,self::CACHE_TTL);
        return $data;
    }

    private static function family_candidate_ids(WC_Product $p,$model) {
        $ids = [];
        $tax_query = ['relation'=>'OR'];
        if ($model['term_id'] && taxonomy_exists($model['taxonomy'])) {
            $tax_query[] = ['taxonomy'=>$model['taxonomy'],'field'=>'term_id','terms'=>[(int)$model['term_id']]];
        }
        $slug = sanitize_title($model['key']);
        if ($slug!=='') {
            foreach (get_object_taxonomies('product','objects') as $tax=>$obj) {
                if (!taxonomy_exists($tax)) continue;
                $term = get_term_by('slug',$slug,$tax);
                if (!$term) $term = get_term_by('name',$model['label'],$tax);
                if ($term && !is_wp_error($term)) $tax_query[] = ['taxonomy'=>$tax,'field'=>'term_id','terms'=>[(int)$term->term_id]];
            }
        }
        if (count($tax_query)>1) {
            $q = new WP_Query(['post_type'=>'product','post_status'=>'publish','posts_per_page'=>600,'fields'=>'ids','no_found_rows'=>true,'tax_query'=>$tax_query]);
            $ids = array_merge($ids,$q->posts);
        }
        if ($model['key']!=='') {
            $q = new WP_Query(['post_type'=>'product','post_status'=>'publish','posts_per_page'=>250,'fields'=>'ids','no_found_rows'=>true,'s'=>$model['key']]);
            $ids = array_merge($ids,$q->posts);
            $meta_query = ['relation'=>'OR'];
            foreach (['_compatible_models','compatible_models','_models','models','model','_model','autoid_models'] as $key) {
                $meta_query[] = ['key'=>$key,'value'=>$model['key'],'compare'=>'LIKE'];
            }
            $mq = new WP_Query(['post_type'=>'product','post_status'=>'publish','posts_per_page'=>600,'fields'=>'ids','no_found_rows'=>true,'meta_query'=>$meta_query]);
            $ids = array_merge($ids,$mq->posts);
        }
        $ids[] = $p->get_id();
        return array_values(array_unique(array_map('intval',$ids)));
    }

    private static function product_group(WC_Product $p) {
        $parts = [$p->get_name(),$p->get_type()];
        $terms = wp_get_post_terms($p->get_id(),'product_cat');
        if (!is_wp_error($terms)) foreach ($terms as $t) {
            $parts[] = $t->name; $parts[] = $t->slug;
            $parents = get_ancestors($t->term_id,'product_cat');
            foreach ($parents as $parent_id) { $pt=get_term($parent_id,'product_cat'); if ($pt && !is_wp_error($pt)) { $parts[]=$pt->name; $parts[]=$pt->slug; } }
        }
        $hay = strtolower(remove_accents(implode(' ',array_filter($parts))));
        $map = [
            'service'=>['service','servici','onecare','warranty','garantie','contract suport','support contract','care plan'],
            'software'=>['software','aplicatii','apps','application','license','licenta','developer','print dna','zebradesigner'],
            'consumables'=>['consumabil','consumable','ribbon','ribbo','etichete','label','media','supplies','cartus','toner','cerneala','tag rfid'],
            'accessories'=>['accesor','accessor','piese','parts','cabl','cradle','dock','bater','battery','alimentator','power supply','adapter','mount','holster','curea','stand'],
        ];
        foreach ($map as $group=>$needles) foreach ($needles as $needle) if (strpos($hay,$needle)!==false) return $group;
        return 'variants';
    }

    private static function group_labels() {
        return ['variants'=>'Variante','accessories'=>'Accesorii','service'=>'Service','software'=>'Software & Apps','consumables'=>'Consumabile'];
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
        $autoid = self::numeric_meta($id,['_stock_autoid','stock_autoid','_autoid_stock','autoid_stock']);
        $dist = self::numeric_meta($id,['_stock_distributor','stock_distributor','_distributor_stock','distributor_stock']);
        if ($autoid!==null && $autoid>0) $delivery = 'Livrare rapidă din stoc AutoID';
        elseif ($dist!==null && $dist>0) $delivery = 'Livrare estimată 5–7 zile';
        elseif ($p->is_in_stock()) $delivery = $p->get_stock_status()==='onbackorder' ? 'Disponibil la comandă' : 'Disponibil';
        else $delivery = 'Cere ofertă pentru disponibilitate';
        return ['autoid'=>$autoid,'distributor'=>$dist,'delivery'=>$delivery];
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
        $row = [
            'id'=>$p->get_id(),'name'=>$p->get_name(),'slug'=>$p->get_slug(),'sku'=>$p->get_sku(),
            'brand'=>$brand,'model'=>$model['label'],'model_key'=>$model['key'],'permalink'=>$p->get_permalink(),
            'image'=>self::image_url($p,$detail),'images'=>$images,
            'price'=>(string)$price,'regular_price'=>$regular?(string)$regular:'','sale_price'=>$sale?(string)$sale:'',
            'price_display'=>wp_strip_all_tags(wc_price($price)),'currency'=>get_woocommerce_currency(),
            'on_sale'=>$p->is_on_sale(),'in_stock'=>$p->is_in_stock(),'stock_status'=>$p->get_stock_status(),
            'stock_quantity'=>$p->managing_stock()?$p->get_stock_quantity():null,
            'stock_autoid'=>$stock['autoid'],'stock_distributor'=>$stock['distributor'],'delivery_label'=>$stock['delivery'],
            'stock_label'=>$p->is_in_stock()?($p->get_stock_status()==='onbackorder'?'Disponibil la comandă':'În stoc / disponibil'):'Stoc epuizat',
            'short_description'=>wp_strip_all_tags($p->get_short_description()),
            'category'=>$cats?$cats[0]->name:'','categories'=>array_map(fn($c)=>['id'=>(int)$c->term_id,'name'=>$c->name,'slug'=>$c->slug],$cats),
            'support_query'=>trim($brand.' '.$model['label'].' '.$p->get_sku()),'featured'=>$p->is_featured(),'type'=>$p->get_type(),
            'rating'=>$rating,'review_count'=>(int)$p->get_review_count(),
        ];
        if ($detail) {
            $row['description'] = wp_strip_all_tags($p->get_description());
            $row['attributes'] = $attributes;
            $row['variation_ids'] = $p->is_type('variable')?array_map('intval',$p->get_children()):[];
            $row['upsell_ids'] = array_map('intval',$p->get_upsell_ids());
            $row['cross_sell_ids'] = array_map('intval',$p->get_cross_sell_ids());
        }
        return $row;
    }
}

AutoID_Mobile_Commerce_Bridge_040::boot();
