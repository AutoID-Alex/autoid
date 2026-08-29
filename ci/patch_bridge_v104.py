from pathlib import Path

p = Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s = p.read_text()

s = s.replace('Version: 1.0.3', 'Version: 1.0.4', 1)
s = s.replace('final class AutoID_Mobile_Commerce_Bridge_103', 'final class AutoID_Mobile_Commerce_Bridge_104', 1)
s = s.replace('AutoID_Mobile_Commerce_Bridge_103::boot();', 'AutoID_Mobile_Commerce_Bridge_104::boot();', 1)
s = s.replace("'version'=>'1.0.3'", "'version'=>'1.0.4'", 1)

# Add a dedicated Home product selector while preserving the existing Hero manager.
old_menu = """    public static function admin_menu() {
        add_submenu_page(
            'woocommerce',
            'AutoID App Hero',
            'AutoID App Hero',
            'manage_woocommerce',
            'autoid-app-hero',
            [__CLASS__, 'render_hero_admin']
        );
    }
"""
new_menu = """    public static function admin_menu() {
        add_submenu_page(
            'woocommerce',
            'AutoID App Hero',
            'AutoID App Hero',
            'manage_woocommerce',
            'autoid-app-hero',
            [__CLASS__, 'render_hero_admin']
        );
        add_submenu_page(
            'woocommerce',
            'AutoID App Home',
            'AutoID App Home',
            'manage_woocommerce',
            'autoid-app-home',
            [__CLASS__, 'render_home_admin']
        );
    }
"""
if old_menu not in s:
    raise SystemExit('v1.0.3 admin_menu block missing')
s = s.replace(old_menu, new_menu, 1)

old_init = """    public static function admin_init() {
        register_setting(
            'autoid_mobile_hero_group',
            'autoid_mobile_hero_slides',
            [
                'type'=>'array',
                'sanitize_callback'=>[__CLASS__, 'sanitize_hero_slides'],
                'default'=>self::default_hero_slides(),
            ]
        );
    }
"""
new_init = """    public static function admin_init() {
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
    }
"""
if old_init not in s:
    raise SystemExit('v1.0.3 admin_init block missing')
s = s.replace(old_init, new_init, 1)

anchor = '    private static function default_hero_slides() {'
if anchor not in s:
    raise SystemExit('default_hero_slides anchor missing')
home_admin = r'''    public static function sanitize_home_skus($value) {
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
                </table>
                <?php submit_button('Salvează produsele Home'); ?>
            </form>
        </div>
        <?php
    }

'''
s = s.replace(anchor, home_admin + anchor, 1)

# Replace only the recommended-products block. Manual SKUs are exact and retain their configured order.
old_recommended = """        $recommended=[];
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
"""
new_recommended = """        $recommended=[];
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
"""
if old_recommended not in s:
    raise SystemExit('recommended products block missing')
s = s.replace(old_recommended, new_recommended, 1)

# Lichidări: direct category members AND own stock_autoid strictly greater than zero.
old_liq = """            foreach($q->posts as $id){
                if(!has_term((int)$liquidation_term->term_id,'product_cat',(int)$id)) continue;
                $p=wc_get_product((int)$id);
                if($p && $p->is_visible()) $candidates[]=$p;
            }
"""
new_liq = """            foreach($q->posts as $id){
                if(!has_term((int)$liquidation_term->term_id,'product_cat',(int)$id)) continue;
                $p=wc_get_product((int)$id);
                if(!$p || !$p->is_visible()) continue;
                $stock_autoid=(int)(self::numeric_meta($p->get_id(),['stock_autoid','_stock_autoid','_autoid_stock','autoid_stock']) ?: 0);
                if($stock_autoid<=0) continue;
                $candidates[]=$p;
            }
"""
if old_liq not in s:
    raise SystemExit('v1.0.2 direct liquidation loop missing')
s = s.replace(old_liq, new_liq, 1)

p.write_text(s)
print('Patched AutoID Mobile Commerce Bridge v1.0.4 Home SKU selector and liquidation stock rule')
