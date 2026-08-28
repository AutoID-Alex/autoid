from pathlib import Path

p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()
s=s.replace('Version: 1.0.0','Version: 1.0.1',1)
s=s.replace('final class AutoID_Mobile_Commerce_Bridge_100','final class AutoID_Mobile_Commerce_Bridge_101',1)
s=s.replace('AutoID_Mobile_Commerce_Bridge_100::boot();','AutoID_Mobile_Commerce_Bridge_101::boot();',1)

start=s.index('    public static function home(WP_REST_Request $r) {')
end=s.index('    private static function home_category_specs(){',start)
home=r'''    public static function home(WP_REST_Request $r) {
        $ok = self::require_wc(); if (is_wp_error($ok)) return $ok;
        $sections = [];

        // Main Home category sections remain grouped-only and sorted by effective AutoID stock.
        foreach (self::home_category_specs() as $spec) {
            $term = self::find_product_category($spec['name'], $spec['slugs']);
            if (!$term) continue;
            $q = new WP_Query([
                'post_type'=>'product','post_status'=>'publish','posts_per_page'=>250,
                'fields'=>'ids','no_found_rows'=>true,
                'tax_query'=>[['taxonomy'=>'product_cat','field'=>'term_id','terms'=>[(int)$term->term_id],'include_children'=>true]]
            ]);
            $rows=[];
            foreach($q->posts as $id){
                $p=wc_get_product((int)$id);
                if(!$p || !$p->is_visible() || !$p->is_type('grouped')) continue;
                $rows[]=['stock'=>self::grouped_autoid_stock($p),'row'=>self::product_row($p,false)];
            }
            usort($rows,fn($a,$b)=>($b['stock']<=>$a['stock']) ?: strcasecmp($a['row']['name'],$b['row']['name']));
            $sections[]=[
                'category'=>self::category_row($term),
                'products'=>array_values(array_map(fn($x)=>$x['row'],array_slice($rows,0,12))),
                'total_grouped'=>count($rows)
            ];
        }

        // "În stoc AutoID": one highest-stock product from every requested product family.
        // Important: only the product's own stock_autoid meta is accepted here (>0).
        $recommended=[];
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

        // "Lichidări de stoc": random visible products only from the dedicated category.
        $liquidations=[];
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

        return rest_ensure_response([
            'app'=>['name'=>'AutoID','tagline'=>'Professional Solutions','version'=>'1.0.1'],
            'hero'=>['title'=>'Echipamente AutoID pentru afacerea ta','subtitle'=>'Scanare, etichetare, mobilitate, RFID și soluții profesionale.'],
            'sections'=>$sections,
            'recommended'=>array_values($recommended),
            'offers'=>array_values($liquidations),
            'categories'=>self::category_rows(0),
            'brands'=>self::brand_rows(24)
        ]);
    }

    private static function home_stock_specs(){
        return [
            ['names'=>['Imprimante de etichete'],'slugs'=>['imprimante-de-etichete']],
            ['names'=>['Terminale mobile'],'slugs'=>['terminale-mobile']],
            ['names'=>['Cititoare coduri de bare'],'slugs'=>['cititoare-coduri-de-bare','scanere-coduri-de-bare']],
            ['names'=>['Brațe robotice','Brate robotice'],'slugs'=>['brate-robotice','brate-robot']],
            ['names'=>['Sisteme de inspecție','Sisteme de inspectie'],'slugs'=>['sisteme-de-inspectie','inspectie-industriala']],
            ['names'=>['Echipamente RFID'],'slugs'=>['echipamente-rfid','rfid']],
            ['names'=>['Panel PC-uri','Laptopuri rugged','Laptopuri Rugged'],'slugs'=>['panel-pc-uri','panel-pc','laptopuri-rugged','rugged-laptops']],
            ['names'=>['Sisteme POS și de interacțiune cu clienții','Sisteme POS si de interactiune cu clientii'],'slugs'=>['sisteme-pos-si-de-interactiune-cu-clientii','sisteme-pos-interactiune-clienti','sisteme-pos']],
            ['names'=>['Monitoare touchscreen','Monitoare Touchscreen'],'slugs'=>['monitoare-touchscreen','touchscreen-monitors']],
            ['names'=>['Imprimante de carduri'],'slugs'=>['imprimante-de-carduri','imprimante-carduri']],
            ['names'=>['Cititoare de carduri'],'slugs'=>['cititoare-de-carduri','cititoare-carduri']],
            ['names'=>['Tablete semnătură digitală','Tablete semnatura digitala'],'slugs'=>['tablete-semnatura-digitala','tablete-pentru-semnatura-digitala']],
        ];
    }

    private static function find_product_category_ids($names,$slugs=[]){
        $ids=[];
        foreach((array)$names as $name){
            $t=get_term_by('name',$name,'product_cat');
            if($t && !is_wp_error($t)) $ids[]=(int)$t->term_id;
        }
        foreach((array)$slugs as $slug){
            $t=get_term_by('slug',$slug,'product_cat');
            if($t && !is_wp_error($t)) $ids[]=(int)$t->term_id;
        }
        if(!$ids){
            $needles=array_values(array_filter(array_map(fn($x)=>strtolower(remove_accents((string)$x)),(array)$names)));
            $terms=get_terms(['taxonomy'=>'product_cat','hide_empty'=>false]);
            if(!is_wp_error($terms)) foreach($terms as $t){
                $hay=strtolower(remove_accents($t->name));
                foreach($needles as $needle){
                    if($hay===$needle || str_contains($hay,$needle) || str_contains($needle,$hay)){$ids[]=(int)$t->term_id;break;}
                }
            }
        }
        return array_values(array_unique(array_filter(array_map('intval',$ids))));
    }

'''
s=s[:start]+home+s[end:]
p.write_text(s)
print('Patched AutoID Mobile Commerce Bridge v1.0.1')
