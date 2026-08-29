from pathlib import Path

p = Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s = p.read_text()

s = s.replace('Version: 1.0.4', 'Version: 1.0.4.2', 1)
s = s.replace('final class AutoID_Mobile_Commerce_Bridge_104', 'final class AutoID_Mobile_Commerce_Bridge_1042', 1)
s = s.replace('AutoID_Mobile_Commerce_Bridge_104::boot();', 'AutoID_Mobile_Commerce_Bridge_1042::boot();', 1)
s = s.replace("'version'=>'1.0.4'", "'version'=>'1.0.4.2'", 1)

start = s.find('    public static function products(WP_REST_Request $r) {')
end = s.find('    public static function product(WP_REST_Request $r) {', start)
if start < 0 or end < 0:
    raise SystemExit('products function boundaries missing')

products = r'''    public static function products(WP_REST_Request $r) {
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

        $category_term=$category ? get_term($category,'product_cat') : null;
        $is_liquidation=$category_term && !is_wp_error($category_term) && $category_term->slug==='lichidari-de-stoc';
        $ids=[];

        if($search!=='') {
            $ids=self::catalog_search_ids($search,500);
        } else {
            $tax=[];
            if($category) {
                $tax[]=[
                    'taxonomy'=>'product_cat','field'=>'term_id','terms'=>[$category],
                    'include_children'=>$is_liquidation ? false : true,
                    'operator'=>'IN'
                ];
            }
            if($is_liquidation && $secondary_category) {
                $tax[]=[
                    'taxonomy'=>'product_cat','field'=>'term_id','terms'=>[$secondary_category],
                    'include_children'=>true,'operator'=>'IN'
                ];
            }
            if($brand) {
                foreach(['product_brands','product_brand','pa_brand','brand'] as $bt) {
                    if(taxonomy_exists($bt)) { $tax[]=['taxonomy'=>$bt,'field'=>'term_id','terms'=>[$brand]]; break; }
                }
            }
            if($model && taxonomy_exists('product_tag')) $tax[]=['taxonomy'=>'product_tag','field'=>'term_id','terms'=>[$model]];

            $meta=[];
            if($min_price>0 || $max_price>0) {
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

        // Search results must obey the same category intersection as normal catalog requests.
        if($search!=='' && ($category || $secondary_category || $brand || $model || $min_price>0 || $max_price>0)) {
            $ids=array_values(array_filter($ids,function($id) use($category,$secondary_category,$brand,$model,$min_price,$max_price,$is_liquidation){
                $p=wc_get_product($id); if(!$p) return false;
                if($category && !has_term($category,'product_cat',$id)) return false;
                if($is_liquidation && $secondary_category && !has_term($secondary_category,'product_cat',$id)) return false;
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
            if($is_liquidation) {
                // Liquidation is a merchandising flag, not a normal hierarchy. Require direct membership + own AutoID stock.
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

        $total=count($rows);
        $slice=array_slice($rows,($page-1)*$per,$per);
        return rest_ensure_response([
            'products'=>array_map(fn($p)=>self::product_row($p,false),$slice),
            'page'=>$page,'per_page'=>$per,'total'=>$total,'pages'=>$total?(int)ceil($total/$per):0
        ]);
    }

'''
s = s[:start] + products + s[end:]

start = s.find('    public static function catalog_facets(WP_REST_Request $r)')
end = s.find('    public static function rfq(WP_REST_Request $r)', start)
if start < 0 or end < 0:
    raise SystemExit('catalog_facets function boundaries missing')

facets = r'''    public static function catalog_facets(WP_REST_Request $r){
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $category=absint($r->get_param('category'));
        $category_term=$category?get_term($category,'product_cat'):null;
        $is_liquidation=$category_term && !is_wp_error($category_term) && $category_term->slug==='lichidari-de-stoc';

        $tax=[];
        if($category)$tax[]=['taxonomy'=>'product_cat','field'=>'term_id','terms'=>[$category],'include_children'=>$is_liquidation?false:true,'operator'=>'IN'];
        $args=['post_type'=>'product','post_status'=>'publish','posts_per_page'=>-1,'fields'=>'ids','no_found_rows'=>true];
        if($tax)$args['tax_query']=$tax;
        $ids=(new WP_Query($args))->posts;

        $brands=[];$models=[];$liquidation_categories=[];$min=null;$max=null;
        foreach($ids as $id){
            $p=wc_get_product($id); if(!$p||!$p->is_visible())continue;
            if($is_liquidation){
                if(!has_term($category,'product_cat',$id))continue;
                $stock_autoid=(int)(self::numeric_meta($id,['stock_autoid','_stock_autoid','_autoid_stock','autoid_stock'])?:0);
                if($stock_autoid<=0)continue;
            }
            $pr=(float)$p->get_price(); if($pr>0){$min=$min===null?$pr:min($min,$pr);$max=$max===null?$pr:max($max,$pr);}
            foreach(['product_brands','product_brand','pa_brand','brand'] as $bt){
                if(!taxonomy_exists($bt))continue;
                $ts=wp_get_post_terms($id,$bt);
                if(!is_wp_error($ts))foreach($ts as $t)$brands[$t->term_id]=['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug];
                if($ts&&!is_wp_error($ts))break;
            }
            if(taxonomy_exists('product_tag')){
                $ts=wp_get_post_terms($id,'product_tag');
                if(!is_wp_error($ts))foreach($ts as $t)$models[$t->term_id]=['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug];
            }
            if($is_liquidation){
                $terms=wp_get_post_terms($id,'product_cat');
                if(!is_wp_error($terms))foreach($terms as $t){
                    if((int)$t->term_id===$category || $t->slug==='lichidari-de-stoc')continue;
                    if(!isset($liquidation_categories[$t->term_id]))$liquidation_categories[$t->term_id]=['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug,'count'=>0];
                    $liquidation_categories[$t->term_id]['count']++;
                }
            }
        }
        uasort($brands,fn($a,$b)=>strcasecmp($a['name'],$b['name']));
        uasort($models,fn($a,$b)=>strcasecmp($a['name'],$b['name']));
        uasort($liquidation_categories,function($a,$b){$c=$b['count']<=>$a['count'];return $c!==0?$c:strcasecmp($a['name'],$b['name']);});
        return rest_ensure_response([
            'price'=>['min'=>$min?:0,'max'=>$max?:0],
            'brands'=>array_values($brands),
            'models'=>array_values($models),
            'subcategories'=>$is_liquidation?[]:($category?self::category_rows($category):self::category_rows(0)),
            'liquidation_categories'=>array_values($liquidation_categories),
            'special_category'=>$is_liquidation?'liquidation':''
        ]);
    }

'''
s = s[:start] + facets + s[end:]

p.write_text(s)
print('Patched Bridge v1.0.4.2: liquidation category intersections, category facets, direct membership and stock_autoid > 0')
