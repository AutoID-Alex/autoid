from pathlib import Path
import re

p = Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s = p.read_text()

s = s.replace('Version: 1.0.2', 'Version: 1.0.3', 1)
s = s.replace('final class AutoID_Mobile_Commerce_Bridge_102', 'final class AutoID_Mobile_Commerce_Bridge_103', 1)
s = s.replace('AutoID_Mobile_Commerce_Bridge_102::boot();', 'AutoID_Mobile_Commerce_Bridge_103::boot();', 1)
s = s.replace("'version'=>'1.0.2'", "'version'=>'1.0.3'", 1)

# Register the Bridge admin manager without weakening public REST permissions.
boot_match = re.search(r"public static function boot\(\)\s*\{(?P<body>.*?)\n\s*\}", s, re.S)
if not boot_match:
    raise SystemExit('boot() not found')
body = boot_match.group('body')
if "autoid_mobile_hero" not in body:
    new_body = body + "\n        add_action('admin_menu', [__CLASS__, 'admin_menu']);\n        add_action('admin_init', [__CLASS__, 'admin_init']); // autoid_mobile_hero"
    s = s[:boot_match.start('body')] + new_body + s[boot_match.end('body'):]

# Add hero_slides to the existing /home payload.
needle = "            'hero'=>['title'=>'Echipamente AutoID pentru afacerea ta','subtitle'=>'Scanare, etichetare, mobilitate, RFID și soluții profesionale.'],"
replacement = needle + "\n            'hero_slides'=>self::hero_slides_public(),"
if needle in s and "'hero_slides'=>self::hero_slides_public()" not in s:
    s = s.replace(needle, replacement, 1)
else:
    # v1.0.1+ home payload may no longer contain the original hero key.
    marker = "            'sections'=>$sections,"
    if marker in s and "'hero_slides'=>self::hero_slides_public()" not in s:
        s = s.replace(marker, "            'hero_slides'=>self::hero_slides_public(),\n" + marker, 1)

# Add the Hero Slider Manager methods before product_row so they remain inside the class.
anchor = '    public static function product_row(WC_Product $p,$detail=false) {'
if anchor not in s:
    raise SystemExit('product_row anchor not found')

manager = r'''    public static function admin_menu() {
        add_submenu_page(
            'woocommerce',
            'AutoID App Hero',
            'AutoID App Hero',
            'manage_woocommerce',
            'autoid-app-hero',
            [__CLASS__, 'render_hero_admin']
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

    private static function hero_slides_public() {
        $slides=get_option('autoid_mobile_hero_slides',self::default_hero_slides());
        $out=[];
        foreach ((array)$slides as $i=>$row) {
            if (empty($row['enabled'])) continue;
            $image_id=absint($row['image_id'] ?? 0);
            $out[]=[
                'id'=>'hero-'.($i+1),
                'title'=>sanitize_text_field($row['title'] ?? ''),
                'description'=>sanitize_textarea_field($row['description'] ?? ''),
                'image'=>$image_id ? (wp_get_attachment_image_url($image_id,'full') ?: '') : '',
                'primary_label'=>sanitize_text_field($row['primary_label'] ?? ''),
                'primary_type'=>sanitize_key($row['primary_type'] ?? ''),
                'primary_target_id'=>absint($row['primary_target_id'] ?? 0),
                'secondary_label'=>sanitize_text_field($row['secondary_label'] ?? ''),
                'secondary_type'=>sanitize_key($row['secondary_type'] ?? ''),
                'secondary_target_id'=>absint($row['secondary_target_id'] ?? 0),
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

'''

if 'public static function render_hero_admin()' not in s:
    s = s.replace(anchor, manager + anchor, 1)

p.write_text(s)
print('Patched AutoID Mobile Commerce Bridge v1.0.3 hero manager')
