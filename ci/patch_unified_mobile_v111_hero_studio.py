from pathlib import Path

p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()

s=s.replace('Version: 1.1.0','Version: 1.1.1',1)
s=s.replace('final class AutoID_Mobile_110 {','final class AutoID_Mobile_111 {',1)
s=s.replace('AutoID_Mobile_110::boot();','AutoID_Mobile_111::boot();',1)
s=s.replace("'version'=>'1.1.0'", "'version'=>'1.1.1'")

boot="""    public static function boot() {\n        add_action('rest_api_init', [__CLASS__, 'routes']);"""
if boot not in s:
    raise SystemExit('boot anchor missing after unified patch')
s=s.replace(boot, boot+"\n        add_action('admin_menu', [__CLASS__, 'hero_studio_menu'], 90);",1)

start=s.find('    private static function native_hero_action_from_url($raw_url) {')
end=s.find('    private static function hero_action_options() {',start)
if start<0 or end<0:
    raise SystemExit('hero public block boundaries missing')

block=r'''    private static function native_hero_action_from_url($raw_url) {
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
        $mega_slides=is_array($mega) && is_array($mega['slides'] ?? null) ? $mega['slides'] : [];
        $interval=max(2500,min(20000,absint($mega['slider_interval'] ?? 5500)));
        $out=[];

        foreach(array_values($mega_slides) as $i=>$row){
            if(!is_array($row)) continue;
            if(array_key_exists('app_enabled',$row) && empty($row['app_enabled'])) continue;
            $title=sanitize_text_field($row['title'] ?? '');
            if($title==='') continue;

            $explicit=self::explicit_app_hero_action($row);
            $action=is_array($explicit) ? $explicit : self::native_hero_action_from_url($row['button_url'] ?? '');
            $label=sanitize_text_field($row['app_button_text'] ?? '');
            if($label==='') $label=sanitize_text_field($row['button_text'] ?? '');
            if(($action['type'] ?? '')==='') $label='';

            // App imagery is deliberately independent from website imagery.
            // Never reuse the website image or infer a product/category image.
            $app_image='';
            $app_image_id=absint($row['app_image_id'] ?? 0);
            if($app_image_id) $app_image=(string)(wp_get_attachment_image_url($app_image_id,'full') ?: '');
            if($app_image==='' && !empty($row['app_image'])) $app_image=esc_url_raw((string)$row['app_image']);

            $style=sanitize_key((string)($row['app_style'] ?? 'card'));
            if(!in_array($style,['card','background'],true)) $style='card';

            $out[]=[
                'id'=>'mega-'.($i+1),
                'eyebrow'=>sanitize_text_field($row['eyebrow'] ?? ''),
                'title'=>$title,
                'description'=>sanitize_text_field($row['subtitle'] ?? ''),
                'image'=>$app_image,
                'background'=>sanitize_hex_color($row['app_accent'] ?? $row['background'] ?? '') ?: '#f7630c',
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

'''
s=s[:start]+block+s[end:]

# Insert the non-destructive admin editor before the class closing brace.
class_end=s.rfind('\n}\n\nAutoID_Mobile_111::boot();')
if class_end<0:
    raise SystemExit('unified v111 class end missing')
admin=r'''

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

        if($_SERVER['REQUEST_METHOD']==='POST' && isset($_POST['autoid_hero_studio_nonce'])){
            check_admin_referer('autoid_hero_studio_save','autoid_hero_studio_nonce');
            $posted=is_array($_POST['slides'] ?? null) ? wp_unslash($_POST['slides']) : [];
            foreach($slides as $i=>&$row){
                if(!is_array($row)) $row=[];
                $in=is_array($posted[$i] ?? null) ? $posted[$i] : [];
                $row['app_enabled']=!empty($in['app_enabled']) ? 1 : 0;
                $row['app_image_id']=absint($in['app_image_id'] ?? 0);
                $row['app_image']=esc_url_raw((string)($in['app_image'] ?? ''));
                $style=sanitize_key((string)($in['app_style'] ?? 'card'));
                $row['app_style']=in_array($style,['card','background'],true)?$style:'card';
                $row['app_button_text']=sanitize_text_field((string)($in['app_button_text'] ?? ''));
                $type=sanitize_key((string)($in['app_action_type'] ?? 'none'));
                $allowed=['none','catalog','category','product_sku','consultation','ai'];
                $row['app_action_type']=in_array($type,$allowed,true)?$type:'none';
                $row['app_action_value']=sanitize_text_field((string)($in['app_action_value'] ?? ''));
                $row['app_accent']=sanitize_hex_color((string)($in['app_accent'] ?? '')) ?: '';
            }
            unset($row);
            $settings['slides']=$slides;
            update_option('autoid_mega_menu_settings',$settings,false);
            echo '<div class="notice notice-success is-dismissible"><p><strong>AutoID Hero App salvat.</strong> Setările website-ului au fost păstrate.</p></div>';
        }

        echo '<div class="wrap autoid-hero-studio"><h1>AutoID Mega Menu Hero · App</h1>';
        echo '<p class="description">Website și aplicația folosesc același set de slide-uri, dar <strong>imaginea, stilul și destinația din app sunt independente</strong>. Câmpurile website-ului nu sunt modificate aici.</p>';
        if(!$slides){ echo '<div class="notice notice-warning"><p>Nu există slide-uri în <code>autoid_mega_menu_settings</code>. Adaugă-le mai întâi din AutoID Mega Menu Hero.</p></div></div>'; return; }
        echo '<form method="post">'; wp_nonce_field('autoid_hero_studio_save','autoid_hero_studio_nonce');
        echo '<div class="aid-hero-grid">';
        foreach($slides as $i=>$row){
            $enabled=!array_key_exists('app_enabled',$row) || !empty($row['app_enabled']);
            $app_image_id=absint($row['app_image_id'] ?? 0);
            $app_image=$app_image_id ? (wp_get_attachment_image_url($app_image_id,'medium') ?: '') : esc_url((string)($row['app_image'] ?? ''));
            $web_image=esc_url((string)($row['image'] ?? ''));
            $style=sanitize_key((string)($row['app_style'] ?? 'card'));
            $type=sanitize_key((string)($row['app_action_type'] ?? ''));
            $value=(string)($row['app_action_value'] ?? '');
            $button=(string)($row['app_button_text'] ?? ($row['button_text'] ?? ''));
            echo '<section class="aid-hero-card" data-slide="'.esc_attr((string)$i).'">';
            echo '<div class="aid-card-head"><div><span>SLIDE '.esc_html((string)($i+1)).'</span><h2>'.esc_html((string)($row['title'] ?? 'Fără titlu')).'</h2></div><label class="aid-switch"><input type="checkbox" name="slides['.$i.'][app_enabled]" value="1" '.checked($enabled,true,false).'> Activ în App</label></div>';
            echo '<div class="aid-web-ref"><strong>Website</strong><span>'.esc_html((string)($row['button_url'] ?? 'Fără link')).'</span>'.($web_image?'<img src="'.$web_image.'" alt="">':'<em>Fără imagine website</em>').'</div>';
            echo '<div class="aid-fields">';
            echo '<label><span>Hero Style în App</span><select name="slides['.$i.'][app_style]"><option value="card" '.selected($style,'card',false).'>Card · imagine separată în dreapta</option><option value="background" '.selected($style,'background',false).'>Background · imagine full + text overlay</option></select></label>';
            echo '<label><span>Text buton App</span><input type="text" name="slides['.$i.'][app_button_text]" value="'.esc_attr($button).'" placeholder="Ex. Vezi produsele"></label>';
            echo '<label><span>Destinație App</span><select class="aid-action-type" name="slides['.$i.'][app_action_type]"><option value="" '.selected($type,'',false).'>Auto (compatibilitate din link website)</option><option value="none" '.selected($type,'none',false).'>Fără acțiune / fără buton</option><option value="catalog" '.selected($type,'catalog',false).'>Catalog</option><option value="category" '.selected($type,'category',false).'>Categorie / Subcategorie</option><option value="product_sku" '.selected($type,'product_sku',false).'>Produs după SKU</option><option value="ai" '.selected($type,'ai',false).'>AutoID AI</option><option value="consultation" '.selected($type,'consultation',false).'>Consultanță</option></select></label>';
            echo '<label class="aid-action-value"><span>SKU / ID categorie</span><input class="aid-action-input" type="text" name="slides['.$i.'][app_action_value]" value="'.esc_attr($value).'" placeholder="SKU produs sau ID categorie"><select class="aid-category-select"><option value="">Alege categoria / subcategoria…</option>'.self::hero_category_options_html($type==='category'?absint($value):0).'</select></label>';
            echo '<label><span>Accent App (opțional)</span><input type="color" name="slides['.$i.'][app_accent]" value="'.esc_attr(sanitize_hex_color($row['app_accent'] ?? '') ?: '#f7630c').'"></label>';
            echo '</div>';
            echo '<div class="aid-image-field"><div><strong>Imagine App</strong><p>Separată de website. Dacă rămâne goală, APK-ul <strong>nu inventează și nu preia altă imagine</strong>.</p></div><input class="aid-image-id" type="hidden" name="slides['.$i.'][app_image_id]" value="'.esc_attr((string)$app_image_id).'"><input class="aid-image-url" type="hidden" name="slides['.$i.'][app_image]" value="'.esc_attr((string)($row['app_image'] ?? '')).'"><div class="aid-app-preview">'.($app_image?'<img src="'.esc_url($app_image).'" alt="">':'<span>Fără imagine App</span>').'</div><div class="aid-media-actions"><button type="button" class="button button-primary aid-pick-image">Alege imagine App</button><button type="button" class="button aid-clear-image">Elimină</button></div></div>';
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
'''
s=s[:class_end]+admin+s[class_end:]

p.write_text(s)
print('Patched AutoID Mobile v1.1.1: Mega Menu Hero App Studio, separate app images, native destinations, clean nested category URL fallback')
