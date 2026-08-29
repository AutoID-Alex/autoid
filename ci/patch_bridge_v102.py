from pathlib import Path

p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()
s=s.replace('Version: 1.0.1','Version: 1.0.2',1)
s=s.replace('final class AutoID_Mobile_Commerce_Bridge_101','final class AutoID_Mobile_Commerce_Bridge_102',1)
s=s.replace('AutoID_Mobile_Commerce_Bridge_101::boot();','AutoID_Mobile_Commerce_Bridge_102::boot();',1)
s=s.replace("'version'=>'1.0.1'","'version'=>'1.0.2'",1)

# Lichidari: exact WooCommerce product_cat slug only, direct members only.
old="""        $liquidations=[];
        $liquidation_ids=self::find_product_category_ids(['Lichidări de stoc','Lichidari de stoc'],['lichidari-de-stoc','lichidare-de-stoc','clearance']);
        if($liquidation_ids){
            $q=new WP_Query([
                'post_type'=>'product','post_status'=>'publish','posts_per_page'=>150,
                'fields'=>'ids','no_found_rows'=>true,
                'tax_query'=>[['taxonomy'=>'product_cat','field'=>'term_id','terms'=>$liquidation_ids,'include_children'=>true]]
            ]);
            $candidates=[];
            foreach($q->posts as $id){
                $p=wc_get_product((int)$id);
                if($p && $p->is_visible()) $candidates[]=$p;
            }
            if($candidates){
                shuffle($candidates);
                foreach(array_slice($candidates,0,12) as $p) $liquidations[]=self::product_row($p,false);
            }
        }
"""
new="""        $liquidations=[];
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
                if($p && $p->is_visible()) $candidates[]=$p;
            }
            if($candidates){
                shuffle($candidates);
                foreach(array_slice($candidates,0,12) as $p) $liquidations[]=self::product_row($p,false);
            }
        }
"""
if old not in s: raise SystemExit('v101 liquidation block not found')
s=s.replace(old,new,1)

# Explicit simple-product VAT-inclusive regular/current display values for app loops.
needle="""            'grouped_stock_autoid'=>$p->is_type('grouped')?self::grouped_autoid_stock($p):null,'grouped_stock_distributor'=>$p->is_type('grouped')?self::grouped_distributor_stock($p):null,"""
replacement="""            'grouped_stock_autoid'=>$p->is_type('grouped')?self::grouped_autoid_stock($p):null,'grouped_stock_distributor'=>$p->is_type('grouped')?self::grouped_distributor_stock($p):null,
            'regular_price_incl_vat_display'=>self::simple_vat_price_display($p,'regular'),
            'sale_price_incl_vat_display'=>self::simple_vat_price_display($p,'current'),"""
if needle not in s: raise SystemExit('product row grouped stock anchor missing')
s=s.replace(needle,replacement,1)

anchor='''    private static function grouped_distributor_stock(WC_Product $p){'''
idx=s.index(anchor)
# Insert helper before grouped distributor stock.
helper='''    private static function simple_vat_price_display(WC_Product $p,$mode='current'){
        if($p->is_type('grouped')) return '';
        $raw=$mode==='regular'?$p->get_regular_price():$p->get_price();
        if($raw==='' || !is_numeric($raw)) return '';
        $value=wc_get_price_including_tax($p,['price'=>(float)$raw]);
        return number_format((float)$value,2,',','.') . ' lei';
    }

'''
s=s[:idx]+helper+s[idx:]
p.write_text(s)
print('Patched AutoID Mobile Commerce Bridge v1.0.2')
