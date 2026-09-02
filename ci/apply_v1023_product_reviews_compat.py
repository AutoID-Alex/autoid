from pathlib import Path
import re

root=Path('.')

# versions
api=root/'android-v0.1/app/src/main/java/ro/autoid/app/data/AutoIdApi.kt'
models=root/'android-v0.1/app/src/main/java/ro/autoid/app/data/Models.kt'
ux=root/'android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt'
gradle=root/'android-v0.1/app/build.gradle.kts'
plugin=root/'wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php'

# Gradle version
s=gradle.read_text()
s=s.replace('versionCode = 12500','versionCode = 12600').replace('versionName = "1.0.22"','versionName = "1.0.23"')
gradle.write_text(s)

# Models review entities
s=models.read_text()
anchor='data class ProductFamily(val productId: Long, val model: String, val groups: List<FamilyGroup>, val supportAvailable: Boolean)\n'
insert='''data class ProductReview(val id:Long,val author:String,val rating:Int,val content:String,val dateCreated:String,val verified:Boolean=false)\ndata class ProductReviews(val average:Double,val count:Int,val reviews:List<ProductReview>)\n'''
assert anchor in s
s=s.replace(anchor,anchor+insert,1)
models.write_text(s)

# API methods + UA
s=api.read_text().replace('AutoID-Android/1.0.22','AutoID-Android/1.0.23')
anchor='''    fun familyProducts(id:Long,group:String,page:Int=1):List<Product>{val a=JSONObject(get("$MOBILE/products/$id/family/${enc(group)}?page=$page&per_page=20")).optJSONArray("products")?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::product)}}\n\n'''
insert='''    fun productReviews(id:Long,page:Int=1):ProductReviews{\n        val o=JSONObject(get("$MOBILE/products/$id/reviews?page=$page&per_page=8"));val a=o.optJSONArray("reviews")?:JSONArray()\n        return ProductReviews(o.optDouble("average",0.0),o.optInt("count",0),(0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{r->ProductReview(r.optLong("id"),html(r.optString("author")),r.optInt("rating"),html(r.optString("content")),r.optString("date_created"),r.optBoolean("verified"))}})\n    }\n\n    fun submitProductReview(id:Long,rating:Int,content:String,name:String="",email:String="",token:String?=null):Boolean{\n        val b=JSONObject().put("rating",rating).put("content",content).put("name",name).put("email",email)\n        return JSONObject(post("$MOBILE/products/$id/reviews",b.toString(),token)).optBoolean("created")\n    }\n\n'''
assert anchor in s
s=s.replace(anchor,anchor+insert,1)
api.write_text(s)

# UX intro + product call pass session + button shapes + product detail replacement
s=ux.read_text()
s=s.replace(';Text("Pregătim Home-ul AutoID...",fontSize=12.sp,color=Muted)','')
s=s.replace('''                        api,\n                        commerce,''','''                        api,\n                        session,\n                        commerce,''',1)

start=s.index('@Composable fun ProductV100(')
end=s.index('\n@Composable private fun RatingLine', start)
new_func=r'''@Composable fun ProductV100(seed:Product,api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onBack:()->Unit,onFavorite:(Product)->Unit,onCart:(Product,Int)->Unit,onRfq:(Product,Int)->Unit,onOpen:(Product)->Unit,onAi:()->Unit,onNotifications:()->Unit,onHeaderCart:()->Unit){
    var p by remember(seed.id){mutableStateOf(seed)}
    var loading by remember{mutableStateOf(true)}
    var qty by remember{mutableIntStateOf(1)}
    var family by remember{mutableStateOf<ProductFamily?>(null)}
    var group by remember{mutableStateOf<String?>(null)}
    var rows by remember{mutableStateOf<List<Product>>(emptyList())}
    var reviews by remember{mutableStateOf(ProductReviews(0.0,0,emptyList()))}
    var reviewOpen by remember{mutableStateOf(false)}
    var reviewRating by remember{mutableIntStateOf(5)}
    var reviewText by remember{mutableStateOf("")}
    var reviewName by remember{mutableStateOf("")}
    var reviewEmail by remember{mutableStateOf(session.customerEmail)}
    var reviewBusy by remember{mutableStateOf(false)}
    var reviewMessage by remember{mutableStateOf("")}
    var reviewRefresh by remember{mutableIntStateOf(0)}
    LaunchedEffect(seed.id,reviewRefresh){
        runCatching{withContext(Dispatchers.IO){api.product(seed.id)}}.onSuccess{p=it}
        family=runCatching{withContext(Dispatchers.IO){api.productFamily(seed.id)}}.getOrNull()
        reviews=runCatching{withContext(Dispatchers.IO){api.productReviews(seed.id)}}.getOrDefault(ProductReviews(p.rating,p.reviewCount,emptyList()))
        if(group==null || family?.groups?.none{it.key==group&&it.count>0}!=false) group=family?.groups?.firstOrNull{it.count>0}?.key
        loading=false
    }
    LaunchedEffect(group,p.id){group?.let{rows=runCatching{withContext(Dispatchers.IO){api.familyProducts(p.id,it)}}.getOrDefault(emptyList())}}
    LaunchedEffect(reviewBusy){if(reviewBusy){
        runCatching{withContext(Dispatchers.IO){api.submitProductReview(p.id,reviewRating,reviewText,reviewName,reviewEmail,session.accessToken)}}
            .onSuccess{reviewMessage="Mulțumim! Recenzia a fost trimisă.";reviewText="";reviewOpen=false;reviewRefresh++}
            .onFailure{reviewMessage=it.message?:"Recenzia nu a putut fi trimisă."}
        reviewBusy=false
    }}
    LazyColumn(Modifier.fillMaxSize().padding(horizontal=16.dp).statusBarsPadding(),verticalArrangement=Arrangement.spacedBy(12.dp),contentPadding=PaddingValues(bottom=120.dp)){
        item{Row(verticalAlignment=Alignment.CenterVertically){IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")};Spacer(Modifier.weight(1f));IconButton(onClick={onFavorite(p)}){Icon(if(commerce.isFavorite(p.id))Icons.Default.Favorite else Icons.Default.FavoriteBorder,"Favorite",tint=if(commerce.isFavorite(p.id))AutoIdOrange else Ink)};IconButton(onClick=onNotifications){BadgedBox(badge={Badge(containerColor=AutoIdOrange){Text("3")}}){Icon(Icons.Default.NotificationsNone,"Notificări")}};IconButton(onClick=onHeaderCart){BadgedBox(badge={if(commerce.cartCount()>0)Badge(containerColor=AutoIdOrange){Text(commerce.cartCount().toString())}}){Icon(Icons.Default.ShoppingCart,"Coș")}}}}
        item{Gallery(p)}
        item{Brand(p);Text(p.name,fontSize=25.sp,fontWeight=FontWeight.ExtraBold,color=Ink,lineHeight=29.sp);RatingLine(p);Text("Cod produs: ${p.sku.ifBlank{"—"}}",fontSize=12.sp,color=Muted)}
        item{
            Text(if(isGrouped(p))"Prețuri de la:" else "Comandă acum:",fontSize=14.sp,fontWeight=FontWeight.Bold,color=Muted)
            PriceBlock(p,false)
            if(isGrouped(p)&&p.priceRangeInclVat.isNotBlank()){
                val price=p.priceRangeInclVat.replace(Regex("\\s*incl\\.\\s*TVA",RegexOption.IGNORE_CASE),"").trim()
                Row(verticalAlignment=Alignment.Bottom){Text(price,fontSize=18.sp,fontWeight=FontWeight.ExtraBold,color=Ink);Spacer(Modifier.width(5.dp));Text("incl. TVA",fontSize=11.sp,fontWeight=FontWeight.Normal,color=Muted)}
            } else if(!isGrouped(p)){
                Row(verticalAlignment=Alignment.Bottom){Text(p.currentInclVat.ifBlank{p.price},fontSize=18.sp,fontWeight=FontWeight.ExtraBold,color=Ink);Spacer(Modifier.width(5.dp));Text("incl. TVA",fontSize=11.sp,fontWeight=FontWeight.Normal,color=Muted)}
            }
            Spacer(Modifier.height(6.dp));StockLine(p)
        }
        item{
            if(isGrouped(p)){
                OutlinedButton(onClick={onRfq(p,1)},modifier=Modifier.fillMaxWidth().height(52.dp),shape=RoundedCornerShape(10.dp)){Text("Cerere de ofertă")}
            }else{
                Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(8.dp)){
                    OutlinedButton(onClick={if(qty>1)qty--},shape=RoundedCornerShape(10.dp)){Text("−")};Text(qty.toString(),fontWeight=FontWeight.Bold);OutlinedButton(onClick={qty++},shape=RoundedCornerShape(10.dp)){Text("+")}
                    Button(onClick={onCart(p,qty)},modifier=Modifier.weight(1f).height(48.dp),shape=RoundedCornerShape(10.dp)){Text("Adaugă în coș")}
                }
                OutlinedButton(onClick={onRfq(p,qty)},modifier=Modifier.fillMaxWidth().padding(top=7.dp).height(48.dp),shape=RoundedCornerShape(10.dp)){Text("Cerere de ofertă")}
            }
        }
        if(p.shortDescription.isNotBlank() || p.descriptionHtml.isNotBlank())item{ProductAboutV113(p)}
        val groups=family?.groups.orEmpty().filter{it.count>0}
        if(groups.isNotEmpty())item{
            Text("Produse asociate",fontSize=19.sp,fontWeight=FontWeight.ExtraBold)
            LazyRow(horizontalArrangement=Arrangement.spacedBy(7.dp)){items(groups){g->FilterChip(group==g.key,{group=g.key},{Text("${g.label} (${g.count})")},shape=RoundedCornerShape(10.dp))}}
        }
        if(rows.isNotEmpty())item{LazyRow(horizontalArrangement=Arrangement.spacedBy(10.dp)){items(rows,key={it.id}){r->HomeCard(r,commerce.isFavorite(r.id),{onOpen(r)},{onFavorite(r)},{onCart(r,1)},{onRfq(r,1)})}}}
        item{
            HorizontalDivider(color=Color(0xFFE4E7EC));Spacer(Modifier.height(4.dp))
            Row(verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text("Recenzii",fontSize=19.sp,fontWeight=FontWeight.ExtraBold,color=Ink);Text(if(reviews.count>0)"${"%.1f".format(reviews.average)} din 5 · ${reviews.count} recenzii" else "Fii primul care lasă o recenzie",fontSize=12.sp,color=Muted)};OutlinedButton(onClick={reviewOpen=!reviewOpen},shape=RoundedCornerShape(10.dp)){Text(if(reviewOpen)"Închide" else "Scrie o recenzie")}}
            if(reviewOpen){
                Spacer(Modifier.height(10.dp));Text("Evaluarea ta",fontSize=12.sp,fontWeight=FontWeight.Bold,color=Ink)
                Row{(1..5).forEach{i->IconButton(onClick={reviewRating=i},modifier=Modifier.size(36.dp)){Icon(if(i<=reviewRating)Icons.Default.Star else Icons.Default.StarBorder,"$i stele",tint=Color(0xFFFDB022))}}}
                if(session.accessToken==null){OutlinedTextField(reviewName,{reviewName=it},label={Text("Nume")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(10.dp));Spacer(Modifier.height(7.dp));OutlinedTextField(reviewEmail,{reviewEmail=it},label={Text("Email")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(10.dp));Spacer(Modifier.height(7.dp))}
                OutlinedTextField(reviewText,{reviewText=it},label={Text("Recenzia ta")},modifier=Modifier.fillMaxWidth(),minLines=4,shape=RoundedCornerShape(10.dp))
                Spacer(Modifier.height(8.dp));Button(onClick={reviewBusy=true},enabled=!reviewBusy&&reviewText.trim().length>=3&&(session.accessToken!=null||(reviewName.isNotBlank()&&reviewEmail.contains("@"))),modifier=Modifier.fillMaxWidth().height(48.dp),shape=RoundedCornerShape(10.dp)){Text(if(reviewBusy)"Se trimite..." else "Trimite recenzia")}
            }
            if(reviewMessage.isNotBlank()){Spacer(Modifier.height(8.dp));Text(reviewMessage,fontSize=11.sp,color=if(reviewMessage.startsWith("Mulțumim"))Good else MaterialTheme.colorScheme.error)}
            if(reviews.reviews.isNotEmpty()){Spacer(Modifier.height(12.dp));Column(verticalArrangement=Arrangement.spacedBy(10.dp)){reviews.reviews.forEach{r->Surface(shape=RoundedCornerShape(10.dp),color=Soft,modifier=Modifier.fillMaxWidth()){Column(Modifier.padding(12.dp),verticalArrangement=Arrangement.spacedBy(5.dp)){Row(verticalAlignment=Alignment.CenterVertically){Text(r.author,fontWeight=FontWeight.Bold,color=Ink,modifier=Modifier.weight(1f));if(r.verified)Text("Achiziție verificată",fontSize=9.sp,color=Good)};Row{repeat(5){i->Icon(if(i<r.rating)Icons.Default.Star else Icons.Default.StarBorder,null,tint=Color(0xFFFDB022),modifier=Modifier.size(15.dp))}};Text(r.content,fontSize=12.sp,color=Ink,lineHeight=17.sp)}}}}
            }
        }
        item{AiCard(onAi)}
        if(loading)item{LinearProgressIndicator(Modifier.fillMaxWidth(),color=AutoIdOrange)}
    }
}
'''
s=s[:start]+new_func+s[end:]
s=s.replace('shape = RoundedCornerShape(18.dp)', 'shape = RoundedCornerShape(10.dp)')
s=s.replace('shape=RoundedCornerShape(18.dp)', 'shape=RoundedCornerShape(10.dp)')
ux.write_text(s)

# Plugin version + routes + reviews + enterprise-compatible family grouping
s=plugin.read_text()
s=s.replace('Version: 1.1.11','Version: 1.1.12',1)
needle="        register_rest_route(self::NS, '/products/(?P<id>\\d+)/family', $public + ['methods'=>'GET','callback'=>[__CLASS__,'family']]);\n"
assert needle in s
s=s.replace(needle, needle+"        register_rest_route(self::NS, '/products/(?P<id>\\d+)/reviews', $public + ['methods'=>['GET','POST'],'callback'=>[__CLASS__,'product_reviews']]);\n",1)
anchor='    public static function family(WP_REST_Request $r) {'
assert anchor in s
review_php=r'''    public static function product_reviews(WP_REST_Request $r) {
        $ok=self::require_wc(); if(is_wp_error($ok))return $ok;
        $p=self::published_product(absint($r['id'])); if(is_wp_error($p))return $p;
        if($r->get_method()==='POST'){
            if(!comments_open($p->get_id()))return new WP_Error('autoid_reviews_closed','Recenziile sunt închise pentru acest produs.',['status'=>403]);
            $b=$r->get_json_params(); if(!is_array($b))$b=[];
            $rating=max(1,min(5,absint($b['rating']??0)));$content=trim(wp_strip_all_tags((string)($b['content']??'')));
            if(strlen($content)<3)return new WP_Error('autoid_review_short','Recenzia este prea scurtă.',['status'=>400]);
            $uid=self::bearer_user_id($r);$name='';$email='';
            if($uid){$u=get_userdata($uid);if($u){$name=trim((string)$u->display_name);$email=(string)$u->user_email;}}
            if(!$uid){$name=sanitize_text_field((string)($b['name']??''));$email=sanitize_email((string)($b['email']??''));if($name===''||!is_email($email))return new WP_Error('autoid_review_identity','Numele și emailul valid sunt obligatorii.',['status'=>400]);}
            $guard='autoid_mobile_review_guard_'.md5($p->get_id().'|'.strtolower($email));if(get_transient($guard))return new WP_Error('autoid_review_duplicate','Recenzia tocmai a fost trimisă.',['status'=>429]);set_transient($guard,1,30);
            $approved=get_option('comment_moderation')?0:1;
            $comment_id=wp_insert_comment(['comment_post_ID'=>$p->get_id(),'comment_author'=>$name,'comment_author_email'=>$email,'comment_content'=>$content,'comment_type'=>'review','comment_parent'=>0,'user_id'=>$uid,'comment_approved'=>$approved,'comment_agent'=>'AutoID Android App']);
            if(!$comment_id)return new WP_Error('autoid_review_failed','Recenzia nu a putut fi salvată.',['status'=>500]);
            update_comment_meta($comment_id,'rating',$rating);
            $verified=$uid && function_exists('wc_customer_bought_product') && wc_customer_bought_product($email,$uid,$p->get_id());
            update_comment_meta($comment_id,'verified',$verified?1:0);
            if(function_exists('WC_Comments::clear_transients'))WC_Comments::clear_transients($p->get_id());
            return rest_ensure_response(['created'=>true,'comment_id'=>$comment_id,'approved'=>(bool)$approved]);
        }
        $page=self::int_param($r,'page',1,1,10000);$per=self::int_param($r,'per_page',8,1,30);
        $comments=get_comments(['post_id'=>$p->get_id(),'status'=>'approve','type'=>'review','number'=>$per,'offset'=>($page-1)*$per,'orderby'=>'comment_date_gmt','order'=>'DESC']);
        $rows=[];foreach($comments as $c){$rows[]=['id'=>(int)$c->comment_ID,'author'=>$c->comment_author,'rating'=>(int)get_comment_meta($c->comment_ID,'rating',true),'content'=>wp_strip_all_tags($c->comment_content),'date_created'=>mysql2date('c',$c->comment_date_gmt,false),'verified'=>(bool)get_comment_meta($c->comment_ID,'verified',true)];}
        return rest_ensure_response(['product_id'=>$p->get_id(),'average'=>(float)$p->get_average_rating(),'count'=>(int)$p->get_review_count(),'page'=>$page,'per_page'=>$per,'reviews'=>$rows]);
    }

'''
s=s.replace(anchor,review_php+anchor,1)
s=s.replace("return ['variants'=>'Variante','accessories'=>'Accesorii','service'=>'Service','software'=>'Software & Apps','consumables'=>'Consumabile'];","return ['variants'=>'Variante','products'=>'Modele compatibile','accessories'=>'Accesorii','service'=>'Service','software'=>'Software & Apps','consumables'=>'Consumabile'];")
start=s.index('    private static function family_data(WC_Product $p) {')
end=s.index('    private static function group_labels() {', start)
new_family=r'''    private static function mobile_tabs_settings() {
        $saved=get_option('sofa_enterprise_tabs_settings_v4',[]);if(!is_array($saved))$saved=[];
        return [
            'roots'=>[
                'accessories'=>absint($saved['root_accessories']??1179)?:1179,
                'consumables'=>absint($saved['root_consumables']??3287)?:3287,
                'software'=>absint($saved['root_software']??3814)?:3814,
                'services'=>absint($saved['root_services']??1184)?:1184,
            ],
            'visible'=>[
                'accessories'=>array_values(array_filter(array_map('absint',(array)($saved['visible_accessories']??[1157,19,1156,4540,1163,4541,3603,4542])))),
                'consumables'=>array_values(array_filter(array_map('absint',(array)($saved['visible_consumables']??[19,7661,1161])))),
                'software'=>array_values(array_filter(array_map('absint',(array)($saved['visible_software']??[1157,19,1156,4540,1163,4542])))),
                'services'=>array_values(array_filter(array_map('absint',(array)($saved['visible_services']??[1157,19,1156,4540,1163,4541,3603,4542])))),
            ],
        ];
    }

    private static function mobile_product_cat_ids(WC_Product $p){$ids=wp_get_post_terms($p->get_id(),'product_cat',['fields'=>'ids']);return is_wp_error($ids)?[]:array_values(array_filter(array_map('absint',$ids)));}
    private static function mobile_in_cat_tree(WC_Product $p,$root){$root=absint($root);if(!$root)return false;foreach(self::mobile_product_cat_ids($p) as $cid){if($cid===$root)return true;$anc=array_map('absint',get_ancestors($cid,'product_cat'));if(in_array($root,$anc,true))return true;}return false;}
    private static function mobile_visible_for(WC_Product $p,$type,$cfg){$root=$cfg['roots'][$type]??0;if($root&&self::mobile_in_cat_tree($p,$root))return false;$rules=$cfg['visible'][$type]??[];if(!$rules)return true;$allowed=[];foreach($rules as $rid){$allowed[]=$rid;$kids=get_term_children($rid,'product_cat');if(!is_wp_error($kids))$allowed=array_merge($allowed,array_map('absint',$kids));}return (bool)array_intersect(array_unique($allowed),self::mobile_product_cat_ids($p));}

    private static function enterprise_related_group(WC_Product $current,WC_Product $candidate,$cfg){
        $roots=$cfg['roots'];$current_compat=false;$candidate_compat=false;
        foreach($roots as $type=>$root){if(self::mobile_in_cat_tree($current,$root))$current_compat=true;if(self::mobile_in_cat_tree($candidate,$root))$candidate_compat=true;}
        if($current_compat)return $candidate_compat?null:'products';
        $map=['accessories'=>'accessories','consumables'=>'consumables','software'=>'software','services'=>'service'];
        foreach($map as $type=>$group){if(self::mobile_visible_for($current,$type,$cfg)&&self::mobile_in_cat_tree($candidate,$roots[$type]??0))return $group;}
        return null;
    }

    private static function family_data(WC_Product $p) {
        $model=self::model_context($p);$cfg=self::mobile_tabs_settings();$cache_key='autoid_mob_family_enterprise_'.md5($p->get_id().'|'.$model['key'].'|'.wp_json_encode($cfg).'|1.0.23');
        $cached=get_transient($cache_key);if(is_array($cached))return $cached;
        $groups=array_fill_keys(array_keys(self::group_labels()),[]);$grouped=self::grouped_parent($p);$tag_source=$grouped?:$p;
        if($grouped){foreach((array)$grouped->get_children() as $child_id){$child=wc_get_product($child_id);if($child&&$child->get_status()==='publish'&&$child->is_visible())$groups['variants'][]=(int)$child_id;}}
        $tags=wp_get_post_terms($tag_source->get_id(),'product_tag',['fields'=>'ids']);if((is_wp_error($tags)||!$tags)&&$tag_source->get_id()!==$p->get_id())$tags=wp_get_post_terms($p->get_id(),'product_tag',['fields'=>'ids']);
        if(!is_wp_error($tags)&&$tags){
            $q=new WP_Query(['post_type'=>'product','post_status'=>'publish','posts_per_page'=>1500,'fields'=>'ids','no_found_rows'=>true,'tax_query'=>[['taxonomy'=>'product_tag','field'=>'term_id','terms'=>array_map('intval',$tags)]]]);
            $variant_lookup=array_fill_keys($groups['variants'],true);
            foreach($q->posts as $id){$id=(int)$id;if($id===$p->get_id()||($grouped&&$id===$grouped->get_id())||isset($variant_lookup[$id]))continue;$rp=wc_get_product($id);if(!$rp||$rp->get_status()!=='publish'||!$rp->is_visible())continue;$g=self::enterprise_related_group($p,$rp,$cfg);if($g)$groups[$g][]=$id;}
        }
        foreach($groups as $key=>$rows)$groups[$key]=array_values(array_unique(array_map('intval',$rows)));
        $source=['strategy'=>'enterprise-tabs:common-product-tags+root-category+visibility','grouped_parent_id'=>$grouped?$grouped->get_id():0,'tag_ids'=>!is_wp_error($tags)?array_values(array_map('intval',(array)$tags)):[],'roots'=>$cfg['roots'],'visibility'=>$cfg['visible']];
        $data=['model'=>$model,'source'=>$source,'groups'=>$groups];set_transient($cache_key,$data,self::CACHE_TTL);return $data;
    }

    private static function grouped_parent(WC_Product $p) {
        if($p->is_type('grouped')) return $p;
        global $wpdb; $id=(int)$p->get_id();
        $likes=['%i:'.$id.';%','%"'.$id.'"%']; $candidate_ids=[];
        foreach($likes as $like){$found=$wpdb->get_col($wpdb->prepare("SELECT post_id FROM {$wpdb->postmeta} WHERE meta_key='_children' AND meta_value LIKE %s LIMIT 50",$like));$candidate_ids=array_merge($candidate_ids,$found);}
        foreach(array_unique(array_map('intval',$candidate_ids)) as $pid){$parent=wc_get_product($pid);if($parent&&$parent->is_type('grouped')&&in_array($id,array_map('intval',$parent->get_children()),true))return $parent;}
        return null;
    }

'''
s=s[:start]+new_family+s[end:]
s=s.replace("'version'=>'1.1.4'","'version'=>'1.1.12'")
plugin.write_text(s)
print('patched v1.0.23 / plugin v1.1.12')
