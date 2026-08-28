<?php
/**
 * Plugin Name: AutoID Mobile API v2
 * Description: Read-only mobile catalog and support API for the AutoID Android/iOS apps. Does not expose WooCommerce API keys.
 * Version: 0.2.0
 * Author: AutoID
 */

if (!defined('ABSPATH')) { exit; }

final class AutoID_Mobile_API_V2 {
    const NS = 'autoid-app/v2';

    public static function init() {
        add_action('rest_api_init', [__CLASS__, 'routes']);
    }

    public static function routes() {
        register_rest_route(self::NS, '/health', [
            'methods' => 'GET', 'callback' => [__CLASS__, 'health'], 'permission_callback' => '__return_true'
        ]);
        register_rest_route(self::NS, '/products', [
            'methods' => 'GET', 'callback' => [__CLASS__, 'products'], 'permission_callback' => '__return_true',
            'args' => [
                'search' => ['sanitize_callback' => 'sanitize_text_field'],
                'category' => ['sanitize_callback' => 'absint'],
                'per_page' => ['sanitize_callback' => 'absint'],
            ]
        ]);
        register_rest_route(self::NS, '/categories', [
            'methods' => 'GET', 'callback' => [__CLASS__, 'categories'], 'permission_callback' => '__return_true'
        ]);
        register_rest_route(self::NS, '/support', [
            'methods' => 'GET', 'callback' => [__CLASS__, 'support'], 'permission_callback' => '__return_true',
            'args' => [
                'search' => ['required' => true, 'sanitize_callback' => 'sanitize_text_field'],
                'per_page' => ['sanitize_callback' => 'absint'],
            ]
        ]);
    }

    private static function headers(WP_REST_Response $r) {
        $r->header('Cache-Control', 'public, max-age=60, stale-while-revalidate=120');
        $r->header('X-AutoID-Mobile-API', '2.0');
        return $r;
    }

    public static function health() {
        return self::headers(new WP_REST_Response([
            'ok' => true,
            'version' => '0.2.0',
            'woocommerce' => class_exists('WooCommerce'),
            'support' => post_type_exists('autoid_support_res'),
        ], 200));
    }

    public static function products(WP_REST_Request $req) {
        if (!class_exists('WooCommerce')) {
            return new WP_Error('autoid_wc_missing', 'WooCommerce is not available.', ['status' => 503]);
        }

        $per_page = min(max((int)$req->get_param('per_page'), 1), 48);
        if (!$per_page) { $per_page = 24; }
        $search = trim((string)$req->get_param('search'));
        $category = absint($req->get_param('category'));

        $args = [
            'post_type' => 'product',
            'post_status' => 'publish',
            'posts_per_page' => $per_page,
            'orderby' => 'date',
            'order' => 'DESC',
            'no_found_rows' => true,
        ];

        if ($category) {
            $args['tax_query'] = [[
                'taxonomy' => 'product_cat',
                'field' => 'term_id',
                'terms' => [$category],
            ]];
        }

        if ($search !== '') {
            $args['s'] = $search;
            add_filter('posts_search', [__CLASS__, 'extend_product_search'], 10, 2);
            $GLOBALS['autoid_mobile_search_term'] = $search;
        }

        $q = new WP_Query($args);

        if ($search !== '') {
            remove_filter('posts_search', [__CLASS__, 'extend_product_search'], 10);
            unset($GLOBALS['autoid_mobile_search_term']);
        }

        $items = [];
        foreach ($q->posts as $p) {
            $product = wc_get_product($p->ID);
            if (!$product || !$product->is_visible()) { continue; }
            $items[] = self::product_payload($product);
        }

        return self::headers(new WP_REST_Response(['products' => $items], 200));
    }

    public static function extend_product_search($search_sql, $query) {
        global $wpdb;
        $term = isset($GLOBALS['autoid_mobile_search_term']) ? trim($GLOBALS['autoid_mobile_search_term']) : '';
        if ($term === '' || !$query->is_main_query() && $query->get('post_type') !== 'product') { return $search_sql; }
        $like = '%' . $wpdb->esc_like($term) . '%';
        $sku_ids = $wpdb->get_col($wpdb->prepare(
            "SELECT post_id FROM {$wpdb->postmeta} WHERE meta_key = '_sku' AND meta_value LIKE %s LIMIT 100", $like
        ));
        if ($sku_ids) {
            $ids = implode(',', array_map('absint', $sku_ids));
            $search_sql = preg_replace('/\)\s*$/', " OR {$wpdb->posts}.ID IN ($ids))", $search_sql, 1);
        }
        return $search_sql;
    }

    private static function product_payload(WC_Product $product) {
        $id = $product->get_id();
        $cats = wc_get_product_category_list($id, ', ', '', '');
        $category_names = wp_strip_all_tags($cats);
        $brand = '';
        foreach (['product_brand', 'pa_brand', 'brand'] as $tax) {
            if (taxonomy_exists($tax)) {
                $terms = get_the_terms($id, $tax);
                if ($terms && !is_wp_error($terms)) { $brand = $terms[0]->name; break; }
            }
        }
        $image = wp_get_attachment_image_url($product->get_image_id(), 'medium');
        $price_html = wp_strip_all_tags($product->get_price_html());
        $stock = $product->is_in_stock() ? ($product->managing_stock() && $product->get_stock_quantity() !== null ? 'În stoc · ' . max(0, (int)$product->get_stock_quantity()) . ' buc.' : 'În stoc / disponibil') : 'Stoc epuizat';
        $support_query = trim(($brand ? $brand . ' ' : '') . $product->get_name());

        return [
            'id' => $id,
            'name' => $product->get_name(),
            'sku' => $product->get_sku(),
            'permalink' => get_permalink($id),
            'image' => $image ?: '',
            'price' => $product->get_price(),
            'price_display' => $price_html ?: 'Preț la cerere',
            'stock_label' => $stock,
            'in_stock' => $product->is_in_stock(),
            'short_description' => wp_strip_all_tags($product->get_short_description()),
            'category' => $category_names,
            'brand' => $brand,
            'support_query' => $support_query,
        ];
    }

    public static function categories() {
        $terms = get_terms([
            'taxonomy' => 'product_cat',
            'hide_empty' => true,
            'parent' => 0,
            'number' => 20,
            'orderby' => 'count',
            'order' => 'DESC',
        ]);
        $items = [];
        if (!is_wp_error($terms)) {
            foreach ($terms as $t) {
                $items[] = ['id' => (int)$t->term_id, 'name' => $t->name, 'count' => (int)$t->count];
            }
        }
        return self::headers(new WP_REST_Response(['categories' => $items], 200));
    }

    public static function support(WP_REST_Request $req) {
        $search = trim((string)$req->get_param('search'));
        if (mb_strlen($search) < 2) {
            return new WP_Error('autoid_short_query', 'Search term must contain at least 2 characters.', ['status' => 400]);
        }
        $per_page = min(max((int)$req->get_param('per_page'), 1), 50);
        if (!$per_page) { $per_page = 30; }

        $types = array_values(array_filter(['autoid_support_res'], 'post_type_exists'));
        if (!$types) { return self::headers(new WP_REST_Response(['resources' => []], 200)); }

        $q = new WP_Query([
            'post_type' => $types,
            'post_status' => 'publish',
            'posts_per_page' => $per_page,
            's' => $search,
            'orderby' => 'relevance',
            'no_found_rows' => true,
        ]);

        $items = [];
        foreach ($q->posts as $p) {
            $type = get_post_meta($p->ID, 'resource_type', true);
            if (!$type) { $type = get_post_meta($p->ID, '_resource_type', true); }
            if (!$type) { $type = 'Resursă tehnică'; }
            $items[] = [
                'id' => (int)$p->ID,
                'title' => get_the_title($p),
                'url' => get_permalink($p),
                'type' => sanitize_text_field($type),
                'summary' => wp_strip_all_tags(get_the_excerpt($p)),
            ];
        }

        return self::headers(new WP_REST_Response(['resources' => $items], 200));
    }
}

AutoID_Mobile_API_V2::init();
