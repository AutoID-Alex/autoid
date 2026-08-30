from pathlib import Path

p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()
for old,new in [
    ('Version: 1.1.3','Version: 1.1.4'),
    ('final class AutoID_Mobile_113 {','final class AutoID_Mobile_114 {'),
    ('AutoID_Mobile_113::boot();','AutoID_Mobile_114::boot();'),
    ("'version'=>'1.1.3'", "'version'=>'1.1.4'"),
]:
    if old not in s: raise SystemExit('version anchor missing '+old)
    s=s.replace(old,new,1)

start=s.index('    public static function catalog_facets(WP_REST_Request $r){')
end=s.index('    public static function rfq(WP_REST_Request $r)',start)
facets=r'''    public static function catalog_facets(WP_REST_Request $r){
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $category=absint($r->get_param('category'));
        $secondary=absint($r->get_param('secondary_category'));
        $brand=absint($r->get_param('brand'));
        $model=absint($r->get_param('model'));
        $category_term=$category?get_term($category,'product_cat'):null;
        $is_liquidation=$category_term && !is_wp_error($category_term) && $category_term->slug==='lichidari-de-stoc';

        $brand_tax='';
        foreach(['product_brands','product_brand','pa_brand','brand'] as $candidate){ if(taxonomy_exists($candidate)){ $brand_tax=$candidate; break; } }
        $model_tax=taxonomy_exists('product_tag')?'product_tag':'';

        $base_key='autoid_mobile_facets_base_'.md5($category.'|'.($is_liquidation?'liq':'normal').'|1.1.4');
        $rows=get_transient($base_key);
        if(!is_array($rows)){
            $tax=[];
            if($category)$tax[]=['taxonomy'=>'product_cat','field'=>'term_id','terms'=>[$category],'include_children'=>$is_liquidation?false:true,'operator'=>'IN'];
            $args=['post_type'=>'product','post_status'=>'publish','posts_per_page'=>-1,'fields'=>'ids','no_found_rows'=>true,'update_post_meta_cache'=>true,'update_post_term_cache'=>true];
            if($tax)$args['tax_query']=$tax;
            $ids=(new WP_Query($args))->posts;
            $rows=[];
            foreach($ids as $id){
                $p=wc_get_product($id); if(!$p||!$p->is_visible())continue;
                if($is_liquidation){
                    if(!has_term($category,'product_cat',$id))continue;
                    $stock_autoid=(int)(self::numeric_meta($id,['stock_autoid','_stock_autoid','_autoid_stock','autoid_stock'])?:0);
                    if($stock_autoid<=0)continue;
                }
                $cats=wp_get_post_terms($id,'product_cat'); if(is_wp_error($cats))$cats=[];
                $bterms=$brand_tax?wp_get_post_terms($id,$brand_tax):[]; if(is_wp_error($bterms))$bterms=[];
                $mterms=$model_tax?wp_get_post_terms($id,$model_tax):[]; if(is_wp_error($mterms))$mterms=[];
                $rows[]=[
                    'id'=>(int)$id,
                    'price'=>(float)$p->get_price(),
                    'cats'=>array_map(fn($t)=>['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug,'parent'=>(int)$t->parent],$cats),
                    'brands'=>array_map(fn($t)=>['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug],$bterms),
                    'models'=>array_map(fn($t)=>['id'=>(int)$t->term_id,'name'=>$t->name,'slug'=>$t->slug],$mterms),
                ];
            }
            set_transient($base_key,$rows,120);
        }

        $secondary_ids=[];
        if($secondary){
            $children=get_term_children($secondary,'product_cat'); if(is_wp_error($children))$children=[];
            $secondary_ids=array_values(array_unique(array_merge([$secondary],array_map('intval',$children))));
        }
        $matches=function($row,$check_cat=true,$check_brand=true,$check_model=true) use($secondary_ids,$brand,$model){
            if($check_cat && $secondary_ids){
                $ids=array_map('intval',array_column($row['cats'],'id'));
                if(!array_intersect($secondary_ids,$ids))return false;
            }
            if($check_brand && $brand){
                $ids=array_map('intval',array_column($row['brands'],'id'));
                if(!in_array($brand,$ids,true))return false;
            }
            if($check_model && $model){
                $ids=array_map('intval',array_column($row['models'],'id'));
                if(!in_array($model,$ids,true))return false;
            }
            return true;
        };

        $best_category=function($cats) use($category,$is_liquidation){
            $best=0;$best_depth=-1;
            foreach((array)$cats as $ct){
                $cid=(int)($ct['id']??0); if(!$cid || $cid===$category)continue;
                $anc=array_map('intval',(array)get_ancestors($cid,'product_cat'));
                if(!$is_liquidation && $category && !in_array($category,$anc,true))continue;
                $depth=count($anc);
                if($depth>$best_depth){$best=$cid;$best_depth=$depth;}
            }
            return $best;
        };

        $min=null;$max=null;
        foreach($rows as $row){
            if(!$matches($row,true,true,true))continue;
            $pr=(float)$row['price']; if($pr>0){$min=$min===null?$pr:min($min,$pr);$max=$max===null?$pr:max($max,$pr);}
        }

        $category_nodes=[];$liquidation_categories=[];
        foreach($rows as $row){
            if(!$matches($row,false,true,true))continue;
            $seen=[];
            foreach((array)$row['cats'] as $ct){
                $cid=(int)$ct['id']; if(!$cid || $cid===$category || ($ct['slug']??'')==='lichidari-de-stoc')continue;
                if($is_liquidation){
                    if(isset($seen[$cid]))continue; $seen[$cid]=true;
                    if(!isset($liquidation_categories[$cid]))$liquidation_categories[$cid]=['id'=>$cid,'name'=>$ct['name'],'slug'=>$ct['slug'],'count'=>0,'parent'=>(int)$ct['parent'],'depth'=>1];
                    $liquidation_categories[$cid]['count']++;
                    continue;
                }
                if(!$category)continue;
                $cursor=get_term($cid,'product_cat');$path=[];$guard=0;
                while($cursor && !is_wp_error($cursor) && (int)$cursor->term_id!==$category && $guard<20){
                    $path[]=$cursor;
                    if(!(int)$cursor->parent)break;
                    $cursor=get_term((int)$cursor->parent,'product_cat');$guard++;
                }
                if(!$cursor || is_wp_error($cursor) || (int)$cursor->term_id!==$category)continue;
                foreach(array_reverse($path) as $node){
                    $nid=(int)$node->term_id;if(isset($seen[$nid]))continue;$seen[$nid]=true;
                    if(!isset($category_nodes[$nid]))$category_nodes[$nid]=['id'=>$nid,'name'=>$node->name,'slug'=>$node->slug,'count'=>0,'parent'=>(int)$node->parent,'depth'=>1];
                    $category_nodes[$nid]['count']++;
                }
            }
        }

        $brands=[];
        foreach($rows as $row){
            if(!$matches($row,true,false,true))continue;
            $seen=[];
            foreach((array)$row['brands'] as $t){$id=(int)$t['id'];if(!$id||isset($seen[$id]))continue;$seen[$id]=true;if(!isset($brands[$id]))$brands[$id]=['id'=>$id,'name'=>$t['name'],'slug'=>$t['slug'],'count'=>0];$brands[$id]['count']++;}
        }

        $models=[];
        foreach($rows as $row){
            if(!$matches($row,true,true,false))continue;
            $model_brand=(int)($row['brands'][0]['id']??0);
            $model_category=(int)$best_category($row['cats']);
            $seen=[];
            foreach((array)$row['models'] as $t){
                $id=(int)$t['id'];if(!$id||isset($seen[$id]))continue;$seen[$id]=true;
                if(!isset($models[$id]))$models[$id]=['id'=>$id,'name'=>$t['name'],'slug'=>$t['slug'],'count'=>0,'brand_id'=>$model_brand,'category_id'=>$model_category];
                $models[$id]['count']++;
                if(empty($models[$id]['brand_id'])&&$model_brand)$models[$id]['brand_id']=$model_brand;
                if(empty($models[$id]['category_id'])&&$model_category)$models[$id]['category_id']=$model_category;
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
                foreach($children as $child){$child['depth']=$depth;$category_hierarchy[]=$child;$walk((int)$child['id'],$depth+1);}
            };
            $walk($category,1);
        }

        return rest_ensure_response([
            'price'=>['min'=>$min?:0,'max'=>$max?:0],
            'brands'=>array_values($brands),
            'models'=>array_values($models),
            'subcategories'=>[],
            'category_hierarchy'=>$category_hierarchy,
            'liquidation_categories'=>array_values($liquidation_categories),
            'special_category'=>$is_liquidation?'liquidation':'',
            'selection'=>['category'=>$secondary?:null,'brand'=>$brand?:null,'model'=>$model?:null],
            'bridge_version'=>'1.1.4'
        ]);
    }

'''
s=s[:start]+facets+s[end:]

product_start=s.index('    public static function product_row(WC_Product $p,$detail=false) {')
helpers=r'''    private static function product_youtube_ids($content) {
        $ids=[];
        if(preg_match_all('~(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:watch\?(?:[^#\s]*&)?v=|embed/|shorts/))([A-Za-z0-9_-]{6,})~i',(string)$content,$m)){
            foreach((array)($m[1]??[]) as $id){$id=preg_replace('/[^A-Za-z0-9_-]/','',(string)$id);if($id!==''&&!in_array($id,$ids,true))$ids[]=$id;}
        }
        return $ids;
    }

    private static function product_description_html($content) {
        $raw=(string)$content;
        if(trim($raw)==='')return '';
        if($raw===wp_strip_all_tags($raw))$raw=wpautop(esc_html($raw));
        return wp_kses_post($raw);
    }

'''
s=s[:product_start]+helpers+s[product_start:]
old="""        if ($detail) {\n            $row['description'] = wp_strip_all_tags($p->get_description());\n            $row['attributes'] = $attributes;"""
new="""        if ($detail) {\n            $raw_description=(string)$p->get_description();\n            $row['description'] = wp_strip_all_tags($raw_description);\n            $row['description_html'] = self::product_description_html($raw_description);\n            $row['youtube_ids'] = self::product_youtube_ids($raw_description);\n            $row['attributes'] = $attributes;"""
if old not in s: raise SystemExit('product detail anchor missing')
s=s.replace(old,new,1)
p.write_text(s)
print('Patched unified AutoID Mobile v1.1.4 dynamic facets + rich product descriptions')
