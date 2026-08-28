<?php
/**
 * Plugin Name: AutoID Mobile Commerce Bridge
 * Description: Read-only catalog, search, home and support endpoints for the AutoID mobile app. Designed to coexist with AutoID Mobile API v1 auth/order/payment routes.
 * Version: 0.3.0
 * Author: AutoID / SOFA SOFT SRL
 * Requires at least: 6.5
 * Requires PHP: 8.0
 * WC requires at least: 9.0
 */

if (!defined('ABSPATH')) exit;

final class AutoID_Mobile_Commerce_Bridge_030 {
    const NS = 'autoid-app/v1';

    public static function boot() {
        add_action('rest_api_init', [__CLASS__, 'routes']);
    }

    public static function routes() {
        register_rest_route(self::NS, '/home', [
            'methods' => 'GET', 'callback' => [__CLASS__, 'home'], 'permission_callback' => '__return_true'
        ]);
        register_rest_route(self::NS, '/products', [
            'methods' => 'GET', 'callback' => [__CLASS__, 'products'], 'permission_callback' => '__return_true'
        ]);
        register_rest_route(self::NS, '/products/(?P<id>\d+)', [
            'methods' => 'GET', 'callback' => [__CLASS__, 'product'], 'permission_callback' => '__return_true'
        ]);
        register_rest_route(self::NS, '/categories', [
            'methods' => 'GET', 'callback' => [__CLASS__, 'categories'], 'permission_callback' => '__return_true'
        ]);
        register_rest_route(self::NS, '/search', [
            'methods' => 'GET', 'callback' => [__CLASS__, 'search'], 'permission_callback' => '__return_true'
        ]);
        register_rest_route(self::NS, '/support', [
            'methods' => 'GET', 'callback' => [__CLASS__, 'support'], 'permission_callback' => '__return_true'
        ]);
        register_rest_route(self::NS, '/brands', [
            'methods' => 'GET', 'callback' => [__CLASS__, 'brands'], 'permission_callback' => '__return_true'
        ]);
    }

    private static function require_wc() {
        if (!function_exists('wc_get_products')) {
            return new WP_Error('autoid_wc_unavailable', 'WooCommerce is unavailable.', ['status' => 503]);
        }
        return true;
    }

    private static function int_param($r, $key, $default, $min = 1, $max = 100) {
        $v = absint($r->get_param($key));
        if (!$v) $v = $default;
        return max($min, min($max, $v));
    }

    public static function home(WP_REST_Request $r) {
        $ok = self::require_wc(); if (is_wp_error($ok)) return $ok;
        $stock = wc_get_products(['status'=>'publish','limit'=>8,'orderby'=>'date','order'=>'DESC','stock_status'=>'instock']);
        $featured = wc_get_products(['status'=>'publish','limit'=>8,'featured'=>true,'orderby'=>'date','order'=>'DESC']);
        if (!$featured) $featured = wc_get_products(['status'=>'publish','limit'=>8,'orderby'=>'popularity','order'=>'DESC']);
        return rest_ensure_response([
            'app' => ['name'=>'AutoID','tagline'=>'Professional Solutions','version'=>'0.3.0'],
            'hero' => ['title'=>'Echipamente AutoID pentru afacerea ta','subtitle'=>'Scanare, etichetare, mobilitate, RFID și soluții profesionale.'],
            'categories' => array_slice(self::category_rows(), 0, 12),
            'in_stock' => array_map([__CLASS__,'product_row'], $stock),
            'recommended' => array_map([__CLASS__,'product_row'], $featured),
            'brands' => self::brand_rows(12),
        ]);
    }

    public static function products(WP_REST_Request $r) {
        $ok = self::require_wc(); if (is_wp_error($ok)) return $ok;
        $page = self::int_param($r,'page',1,1,100000);
        $per = self::int_param($r,'per_page',20,1,50);
        $args = ['status'=>'publish','limit'=>$per,'page'=>$page,'paginate'=>true,'return'=>'objects'];
        $search = sanitize_text_field((string)$r->get_param('search'));
        if ($search !== '') $args['search'] = '*' . $search . '*';
        $category = absint($r->get_param('category'));
        if ($category) {
            $term = get_term($category, 'product_cat');
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
            'products' => array_map([__CLASS__,'product_row'], $result->products),
            'page'=>$page,'per_page'=>$per,'total'=>(int)$result->total,'pages'=>(int)$result->max_num_pages
        ]);
    }

    public static function product(WP_REST_Request $r) {
        $ok = self::require_wc(); if (is_wp_error($ok)) return $ok;
        $p = wc_get_product(absint($r['id']));
        if (!$p || $p->get_status() !== 'publish') return new WP_Error('autoid_product_not_found','Product not found.',['status'=>404]);
        $row = self::product_row($p, true);
        return rest_ensure_response($row);
    }

    public static function categories(WP_REST_Request $r) {
        return rest_ensure_response(['categories'=>self::category_rows()]);
    }

    public static function brands(WP_REST_Request $r) {
        return rest_ensure_response(['brands'=>self::brand_rows(100)]);
    }

    public static function search(WP_REST_Request $r) {
        $q = sanitize_text_field((string)$r->get_param('q'));
        if (mb_strlen($q) < 2) return rest_ensure_response(['suggestions'=>[]]);
        $products = wc_get_products(['status'=>'publish','limit'=>8,'search'=>'*'.$q.'*']);
        $suggestions = [];
        foreach ($products as $p) {
            $suggestions[] = ['type'=>'product','id'=>$p->get_id(),'label'=>$p->get_name(),'sku'=>$p->get_sku(),'image'=>self::image_url($p),'query'=>$p->get_name()];
        }
        return rest_ensure_response(['suggestions'=>$suggestions]);
    }

    public static function support(WP_REST_Request $r) {
        $q = sanitize_text_field((string)$r->get_param('search'));
        if ($q === '') return rest_ensure_response(['resources'=>[]]);
        $types = ['autoid_support_res','autoid_support_resource','support_resource'];
        $existing = array_values(array_filter($types, 'post_type_exists'));
        if (!$existing) return rest_ensure_response(['resources'=>[]]);
        $query = new WP_Query(['post_type'=>$existing,'post_status'=>'publish','s'=>$q,'posts_per_page'=>30,'no_found_rows'=>true]);
        $rows = [];
        foreach ($query->posts as $post) {
            $type = get_post_meta($post->ID,'resource_type',true) ?: get_post_meta($post->ID,'_resource_type',true) ?: 'Resursă';
            $external = get_post_meta($post->ID,'resource_url',true) ?: get_post_meta($post->ID,'_resource_url',true);
            $rows[] = [
                'id'=>$post->ID,
                'title'=>get_the_title($post),
                'url'=>$external ?: get_permalink($post),
                'type'=>sanitize_text_field($type),
                'summary'=>wp_strip_all_tags(get_the_excerpt($post)),
            ];
        }
        return rest_ensure_response(['resources'=>$rows]);
    }

    private static function category_rows() {
        $terms = get_terms(['taxonomy'=>'product_cat','hide_empty'=>true,'parent'=>0,'orderby'=>'count','order'=>'DESC']);
        if (is_wp_error($terms)) return [];
        return array_map(function($t){
            $thumb = absint(get_term_meta($t->term_id,'thumbnail_id',true));
            return ['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug,'count'=>(int)$t->count,'image'=>$thumb?wp_get_attachment_image_url($thumb,'woocommerce_thumbnail'):null];
        }, $terms);
    }

    private static function brand_rows($limit) {
        foreach (['product_brand','pa_brand'] as $tax) {
            if (!taxonomy_exists($tax)) continue;
            $terms = get_terms(['taxonomy'=>$tax,'hide_empty'=>true,'number'=>$limit,'orderby'=>'count','order'=>'DESC']);
            if (is_wp_error($terms)) continue;
            return array_map(fn($t)=>['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug,'count'=>(int)$t->count],$terms);
        }
        return [];
    }

    private static function image_url(WC_Product $p) {
        $id = $p->get_image_id();
        return $id ? wp_get_attachment_image_url($id,'woocommerce_thumbnail') : null;
    }

    private static function brand_name(WC_Product $p) {
        foreach (['product_brand','pa_brand'] as $tax) {
            if (!taxonomy_exists($tax)) continue;
            $terms = wp_get_post_terms($p->get_id(),$tax,['fields'=>'names']);
            if (!is_wp_error($terms) && $terms) return (string)$terms[0];
        }
        $v = $p->get_attribute('brand');
        return is_string($v) ? $v : '';
    }

    public static function product_row(WC_Product $p, $detail = false) {
        $cats = wp_get_post_terms($p->get_id(),'product_cat',['fields'=>'all']);
        if (is_wp_error($cats)) $cats = [];
        $images = [];
        foreach (array_filter(array_merge([$p->get_image_id()], $p->get_gallery_image_ids())) as $id) {
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
        $price = wc_get_price_to_display($p);
        $regular = (float)$p->get_regular_price();
        $sale = (float)$p->get_sale_price();
        $row = [
            'id'=>$p->get_id(),'name'=>$p->get_name(),'slug'=>$p->get_slug(),'sku'=>$p->get_sku(),
            'brand'=>$brand,'permalink'=>$p->get_permalink(),'image'=>self::image_url($p),'images'=>$images,
            'price'=>(string)$price,'regular_price'=>$regular ? (string)$regular : '', 'sale_price'=>$sale ? (string)$sale : '',
            'price_display'=>wp_strip_all_tags(wc_price($price)),'currency'=>get_woocommerce_currency(),
            'on_sale'=>$p->is_on_sale(),'in_stock'=>$p->is_in_stock(),'stock_status'=>$p->get_stock_status(),
            'stock_quantity'=>$p->managing_stock() ? $p->get_stock_quantity() : null,
            'stock_label'=>$p->is_in_stock() ? ($p->get_stock_status()==='onbackorder'?'Disponibil la comandă':'În stoc / disponibil') : 'Stoc epuizat',
            'short_description'=>wp_strip_all_tags($p->get_short_description()),
            'category'=>$cats ? $cats[0]->name : '',
            'categories'=>array_map(fn($c)=>['id'=>(int)$c->term_id,'name'=>$c->name,'slug'=>$c->slug],$cats),
            'support_query'=>trim($brand.' '.$p->get_name().' '.$p->get_sku()),
            'featured'=>$p->is_featured(),'type'=>$p->get_type(),
        ];
        if ($detail) {
            $row['description'] = wp_strip_all_tags($p->get_description());
            $row['attributes'] = $attributes;
            $row['variation_ids'] = $p->is_type('variable') ? array_map('intval',$p->get_children()) : [];
            $row['upsell_ids'] = array_map('intval',$p->get_upsell_ids());
            $row['cross_sell_ids'] = array_map('intval',$p->get_cross_sell_ids());
        }
        return $row;
    }
}

AutoID_Mobile_Commerce_Bridge_030::boot();
