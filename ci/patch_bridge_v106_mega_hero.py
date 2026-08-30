from pathlib import Path

p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()

repls=[
    ('Version: 1.0.5','Version: 1.0.6'),
    ('final class AutoID_Mobile_Commerce_Bridge_105','final class AutoID_Mobile_Commerce_Bridge_106'),
    ('AutoID_Mobile_Commerce_Bridge_105::boot();','AutoID_Mobile_Commerce_Bridge_106::boot();'),
    ("'version'=>'1.0.5'", "'version'=>'1.0.6'"),
]
for old,new in repls:
    if old not in s: raise SystemExit(f'Bridge v1.0.6 version anchor missing: {old}')
    s=s.replace(old,new,1)

old="""            'offers'=>array_values($liquidations),\n            'categories'=>self::category_rows(0),\n            'brands'=>self::brand_rows(24)"""
new="""            'offers'=>array_values($liquidations),\n            'liquidation_category'=>($liquidation_term && !is_wp_error($liquidation_term)) ? self::category_row($liquidation_term) : null,\n            'hero_source'=>'autoid-mega-menu',\n            'categories'=>self::category_rows(0),\n            'brands'=>self::brand_rows(24)"""
if old not in s: raise SystemExit('home response anchor missing')
s=s.replace(old,new,1)

start=s.find('    private static function hero_slides_public() {')
end=s.find('    private static function hero_action_options() {',start)
if start < 0 or end < 0: raise SystemExit('hero_slides_public boundaries missing')
block=r'''    private static function native_hero_action_from_url($raw_url) {
        $url=trim((string)$raw_url);
        if($url==='' || $url==='#') return ['type'=>'','id'=>0];
        $path=wp_parse_url($url,PHP_URL_PATH);
        if(!is_string($path) || $path==='') $path=$url;
        $path='/'.trim($path,'/').'/';

        if(in_array($path,['/magazin/','/shop/','/produse/'],true)) return ['type'=>'catalog','id'=>0];

        if(preg_match('#/(?:categorie-produs|product-category)/([^/]+)/?$#i',$path,$m)){
            $slug=sanitize_title($m[1]);
            $term=get_term_by('slug',$slug,'product_cat');
            if($term && !is_wp_error($term)) return ['type'=>'category','id'=>(int)$term->term_id];
        }

        if(preg_match('#/(?:produs|product)/([^/]+)/?$#i',$path,$m)){
            $slug=sanitize_title($m[1]);
            $post=get_page_by_path($slug,OBJECT,'product');
            if($post) return ['type'=>'product','id'=>(int)$post->ID];
        }

        if(str_contains($path,'/consultanta/') || str_contains($path,'/contact/')) return ['type'=>'consultation','id'=>0];
        if(str_starts_with($path,'/support/')) return ['type'=>'ai','id'=>0];
        return ['type'=>'','id'=>0];
    }

    private static function hero_slides_public() {
        $mega=get_option('autoid_mega_menu_settings',[]);
        $mega_slides=is_array($mega) && is_array($mega['slides'] ?? null) ? $mega['slides'] : [];
        $interval=max(2500,min(20000,absint($mega['slider_interval'] ?? 5500)));
        $out=[];

        foreach(array_values($mega_slides) as $i=>$row){
            if(!is_array($row)) continue;
            $title=sanitize_text_field($row['title'] ?? '');
            if($title==='') continue;
            $action=self::native_hero_action_from_url($row['button_url'] ?? '');
            $label=sanitize_text_field($row['button_text'] ?? '');
            if(($action['type'] ?? '')==='') $label='';
            $out[]=[
                'id'=>'mega-'.($i+1),
                'eyebrow'=>sanitize_text_field($row['eyebrow'] ?? ''),
                'title'=>$title,
                'description'=>sanitize_text_field($row['subtitle'] ?? ''),
                'image'=>esc_url_raw($row['image'] ?? ''),
                'background'=>sanitize_hex_color($row['background'] ?? '') ?: '#229ff2',
                'interval_ms'=>$interval,
                'primary_label'=>$label,
                'primary_type'=>sanitize_key($action['type'] ?? ''),
                'primary_target_id'=>absint($action['id'] ?? 0),
                'secondary_label'=>'',
                'secondary_type'=>'',
                'secondary_target_id'=>0,
                'source'=>'autoid-mega-menu',
            ];
        }

        if($out) return $out;

        $slides=get_option('autoid_mobile_hero_slides',self::default_hero_slides());
        foreach((array)$slides as $i=>$row){
            if(empty($row['enabled'])) continue;
            $image_id=absint($row['image_id'] ?? 0);
            $out[]=[
                'id'=>'fallback-'.($i+1),
                'eyebrow'=>'',
                'title'=>sanitize_text_field($row['title'] ?? ''),
                'description'=>sanitize_textarea_field($row['description'] ?? ''),
                'image'=>$image_id ? (wp_get_attachment_image_url($image_id,'full') ?: '') : '',
                'background'=>'#117ee8',
                'interval_ms'=>5500,
                'primary_label'=>sanitize_text_field($row['primary_label'] ?? ''),
                'primary_type'=>sanitize_key($row['primary_type'] ?? ''),
                'primary_target_id'=>absint($row['primary_target_id'] ?? 0),
                'secondary_label'=>sanitize_text_field($row['secondary_label'] ?? ''),
                'secondary_type'=>sanitize_key($row['secondary_type'] ?? ''),
                'secondary_target_id'=>absint($row['secondary_target_id'] ?? 0),
                'source'=>'mobile-fallback',
            ];
        }
        return $out;
    }

'''
s=s[:start]+block+s[end:]

old="""        add_submenu_page(\n            'woocommerce',\n            'AutoID App Hero',\n            'AutoID App Hero',\n            'manage_woocommerce',\n            'autoid-app-hero',\n            [__CLASS__, 'render_hero_admin']\n        );\n"""
if old in s:
    s=s.replace(old,'',1)

p.write_text(s)
print('Patched Bridge v1.0.6: Mega Menu site slider -> native app hero mapping, explicit liquidation target')
