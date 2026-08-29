from pathlib import Path

p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()
for old,new in [
    ('Version: 1.0.4.3','Version: 1.0.5'),
    ('final class AutoID_Mobile_Commerce_Bridge_1043','final class AutoID_Mobile_Commerce_Bridge_105'),
    ('AutoID_Mobile_Commerce_Bridge_1043::boot();','AutoID_Mobile_Commerce_Bridge_105::boot();'),
    ("'version'=>'1.0.4.3'", "'version'=>'1.0.5'"),
]:
    if old not in s: raise SystemExit(f'v1.0.5 Bridge version anchor missing: {old}')
    s=s.replace(old,new,1)

old='''            if($is_liquidation && $secondary_category) {\n                $tax[]=[\n                    'taxonomy'=>'product_cat','field'=>'term_id','terms'=>[$secondary_category],\n                    'include_children'=>true,'operator'=>'IN'\n                ];\n            }'''
new='''            if($secondary_category) {\n                $tax[]=[\n                    'taxonomy'=>'product_cat','field'=>'term_id','terms'=>[$secondary_category],\n                    'include_children'=>true,'operator'=>'IN'\n                ];\n            }'''
if old not in s: raise SystemExit('v1.0.5 secondary category tax anchor missing')
s=s.replace(old,new,1)

old='''        // Search results must obey the same category intersection as normal catalog requests.\n        if($search!=='' && ($category || $secondary_category || $brand || $model || $min_price>0 || $max_price>0)) {\n            $ids=array_values(array_filter($ids,function($id) use($category,$secondary_category,$brand,$model,$min_price,$max_price,$is_liquidation){\n                $p=wc_get_product($id); if(!$p) return false;\n                if($category && !has_term($category,'product_cat',$id)) return false;\n                if($is_liquidation && $secondary_category && !has_term($secondary_category,'product_cat',$id)) return false;'''
new='''        // Search results must obey the same category intersection as normal catalog requests.\n        $category_filter_ids=$category ? ($is_liquidation ? [$category] : array_values(array_unique(array_merge([$category],array_map('intval',(array)get_term_children($category,'product_cat')))))) : [];\n        $secondary_filter_ids=$secondary_category ? array_values(array_unique(array_merge([$secondary_category],array_map('intval',(array)get_term_children($secondary_category,'product_cat'))))) : [];\n        if($search!=='' && ($category || $secondary_category || $brand || $model || $min_price>0 || $max_price>0)) {\n            $ids=array_values(array_filter($ids,function($id) use($category_filter_ids,$secondary_filter_ids,$brand,$model,$min_price,$max_price){\n                $p=wc_get_product($id); if(!$p) return false;\n                if($category_filter_ids && !has_term($category_filter_ids,'product_cat',$id)) return false;\n                if($secondary_filter_ids && !has_term($secondary_filter_ids,'product_cat',$id)) return false;'''
if old not in s: raise SystemExit('v1.0.5 search category filter anchor missing')
s=s.replace(old,new,1)

start=s.find('    public static function catalog_facets(WP_REST_Request $r){')
end=s.find('    public static function rfq(WP_REST_Request $r)',start)
if start < 0 or end < 0: raise SystemExit('v1.0.5 catalog_facets boundaries missing')
facets=r'''    public static function catalog_facets(WP_REST_Request $r){
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $category=absint($r->get_param('category'));
        $category_term=$category?get_term($category,'product_cat'):null;
        $is_liquidation=$category_term && !is_wp_error($category_term) && $category_term->slug==='lichidari-de-stoc';

        $tax=[];
        if($category)$tax[]=['taxonomy'=>'product_cat','field'=>'term_id','terms'=>[$category],'include_children'=>$is_liquidation?false:true,'operator'=>'IN'];
        $args=['post_type'=>'product','post_status'=>'publish','posts_per_page'=>-1,'fields'=>'ids','no_found_rows'=>true];
        if($tax)$args['tax_query']=$tax;
        $ids=(new WP_Query($args))->posts;

        $brands=[];$models=[];$liquidation_categories=[];$category_nodes=[];$min=null;$max=null;
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
            } elseif($category) {
                $terms=wp_get_post_terms($id,'product_cat');
                $seen=[];
                if(!is_wp_error($terms))foreach($terms as $term){
                    $cursor=$term;$path=[];$guard=0;
                    while($cursor && !is_wp_error($cursor) && (int)$cursor->term_id!==$category && $guard<20){
                        $path[]=$cursor;
                        if(!(int)$cursor->parent)break;
                        $cursor=get_term((int)$cursor->parent,'product_cat');
                        $guard++;
                    }
                    if(!$cursor || is_wp_error($cursor) || (int)$cursor->term_id!==$category)continue;
                    foreach(array_reverse($path) as $node){
                        $nid=(int)$node->term_id;
                        if(isset($seen[$nid]))continue;
                        $seen[$nid]=true;
                        if(!isset($category_nodes[$nid]))$category_nodes[$nid]=[
                            'id'=>$nid,'name'=>$node->name,'slug'=>$node->slug,'count'=>0,
                            'parent'=>(int)$node->parent,'depth'=>1
                        ];
                        $category_nodes[$nid]['count']++;
                    }
                }
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
                foreach($children as $child){
                    $child['depth']=$depth;
                    $category_hierarchy[]=$child;
                    $walk((int)$child['id'],$depth+1);
                }
            };
            $walk($category,1);
        }

        return rest_ensure_response([
            'price'=>['min'=>$min?:0,'max'=>$max?:0],
            'brands'=>array_values($brands),
            'models'=>array_values($models),
            'subcategories'=>$is_liquidation?[]:($category?self::category_rows($category):self::category_rows(0)),
            'category_hierarchy'=>$category_hierarchy,
            'liquidation_categories'=>array_values($liquidation_categories),
            'special_category'=>$is_liquidation?'liquidation':'',
            'bridge_version'=>'1.0.5'
        ]);
    }

'''
s=s[:start]+facets+s[end:]
p.write_text(s)
print('Patched Bridge v1.0.5 category hierarchy and universal secondary category filters')
