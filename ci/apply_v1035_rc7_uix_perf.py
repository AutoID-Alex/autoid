#!/usr/bin/env python3
"""AutoID Android v1.0.30 RC7 / WordPress 1.1.27 UX, performance, RFQ and chat lifecycle."""
from pathlib import Path
import re, shutil

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app'
API=APP/'data/AutoIdApi.kt'
V100=APP/'V100Screens.kt'
WRAPPER=APP/'V117AccountCheckout.kt'
RFQ=APP/'RfqV130.kt'
CHAT=APP/'V129NativeChat.kt'
MAIN=APP/'MainActivity.kt'
PLUGIN=ROOT/'wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'
ACCOUNT_ASSET=ROOT/'ci/v135/V135AccountUx.kt'
CHAT_ASSET=ROOT/'ci/v135/V135PersistentChat.kt'


def once(text,old,new,label):
    n=text.count(old)
    if n!=1: raise RuntimeError(f'{label}: expected 1 match, found {n}')
    return text.replace(old,new,1)

def patch_android_account():
    shutil.copyfile(ACCOUNT_ASSET,APP/'V135AccountUx.kt')
    p=APP/'V135AccountUx.kt';s=p.read_text()
    # Parent app scaffold already applies the system window inset. Do not add a second top inset.
    s=s.replace('.background(A135Soft).statusBarsPadding(),','.background(A135Soft),')
    s=s.replace('session.pendingRfqIdV130=r.id;onRfqs()','onRfqs()')
    old='@Composable fun AccountV135(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onCart:()->Unit,onRfqs:()->Unit){\n    val token=session.accessToken?:return'
    new='@Composable fun AccountV135(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onCart:()->Unit,onFavorites:()->Unit,onNotifications:()->Unit,onRfqs:()->Unit){\n    var loggedOut by remember{mutableStateOf(false)}\n    if(session.accessToken==null||loggedOut){AccountV114(api,session,commerce,onProduct,onCart,onFavorites,onNotifications,onRfqs);return}\n    val token=session.accessToken!!'
    s=once(s,old,new,'AccountV135 auth fallback')
    s=s.replace('OutlinedButton(onClick={session.clear()},modifier=Modifier.fillMaxWidth().height(52.dp)','OutlinedButton(onClick={session.clear();loggedOut=true},modifier=Modifier.fillMaxWidth().height(52.dp)')
    p.write_text(s)

    w=WRAPPER.read_text()
    old='''fun AccountV117(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onCart:()->Unit,onFavorites:()->Unit,onNotifications:()->Unit,onRfqs:()->Unit){
    AccountV114(api,session,commerce,onProduct,onCart,onFavorites,onNotifications,onRfqs)
}'''
    new='''fun AccountV117(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onCart:()->Unit,onFavorites:()->Unit,onNotifications:()->Unit,onRfqs:()->Unit){
    AccountV135(api,session,commerce,onProduct,onCart,onFavorites,onNotifications,onRfqs)
}'''
    w=once(w,old,new,'AccountV117 -> V135')
    WRAPPER.write_text(w)


def patch_chat():
    shutil.copyfile(CHAT_ASSET,CHAT)
    for path in [V100,MAIN]:
        s=path.read_text().replace('PersistentAiChatScreenV134(','PersistentAiChatScreenV135(')
        if 'PersistentAiChatScreenV134(' in s: raise RuntimeError(f'legacy RC6 chat call remains in {path.name}')
        path.write_text(s)

    a=API.read_text()
    anchor='    fun aiChatV134(message:String,productId:Long?,deviceId:String,chatToken:String):ChatReplyV134{val b=JSONObject().put("message",message).put("device_id",deviceId);productId?.let{b.put("product_id",it)};val o=JSONObject(post("$MOBILE/ai/chat?device_id=${enc(deviceId)}",b.toString(),chatToken));return ChatReplyV134(html(o.optString("answer")),o.optString("mode","ai"),o.optBoolean("pending",false))}'
    extra=anchor+'\n    fun aiResetV135(deviceId:String,productId:Long?,chatToken:String):Boolean{val b=JSONObject().put("device_id",deviceId);productId?.let{b.put("product_id",it)};return JSONObject(post("$MOBILE/ai/reset?device_id=${enc(deviceId)}",b.toString(),chatToken)).optBoolean("ok",false)}'
    a=once(a,anchor,extra,'aiReset API')
    API.write_text(a)


def patch_public_cache_and_product_perf():
    a=API.read_text()
    if 'java.util.concurrent.ConcurrentHashMap' not in a:
        a=a.replace('import java.nio.charset.StandardCharsets\n','import java.nio.charset.StandardCharsets\nimport java.util.concurrent.ConcurrentHashMap\n',1)
    companion='''    companion object {
        const val BASE = "https://www.autoid.ro"
        const val MOBILE = "$BASE/wp-json/autoid-app/v1"'''
    replacement='''    companion object {
        const val BASE = "https://www.autoid.ro"
        const val MOBILE = "$BASE/wp-json/autoid-app/v1"
        private data class PublicCacheEntryV135(val value:String,val expiresAt:Long)
        private val publicCacheV135=ConcurrentHashMap<String,PublicCacheEntryV135>()'''
    a=once(a,companion,replacement,'public cache companion')
    old='    private fun get(url:String,token:String?=null)=request("GET",url,null,token)'
    new='''    private fun get(url:String,token:String?=null):String{
        if(token!=null)return request("GET",url,null,token)
        val cacheable=url.contains("/categories")||url.contains("/products")||url.contains("/hero")
        if(!cacheable)return request("GET",url,null,null)
        val now=System.currentTimeMillis();publicCacheV135[url]?.takeIf{it.expiresAt>now}?.let{return it.value}
        val value=request("GET",url,null,null)
        val ttl=when{url.contains("/categories")->5*60_000L;url.contains("/family")->3*60_000L;url.matches(Regex(".*\\/products\\/\\d+(\\?.*)?$"))->2*60_000L;else->45_000L}
        publicCacheV135[url]=PublicCacheEntryV135(value,now+ttl);return value
    }'''
    a=once(a,old,new,'public GET TTL cache')
    API.write_text(a)

    v=V100.read_text()
    if 'import kotlinx.coroutines.async' not in v:
        v=v.replace('import kotlinx.coroutines.Dispatchers\n','import kotlinx.coroutines.Dispatchers\nimport kotlinx.coroutines.async\nimport kotlinx.coroutines.coroutineScope\n',1)
    old='''    LaunchedEffect(seed.id,reviewRefresh){
        runCatching{withContext(Dispatchers.IO){api.product(seed.id)}}.onSuccess{p=it}
        family=runCatching{withContext(Dispatchers.IO){api.productFamily(seed.id)}}.getOrNull()
        reviews=runCatching{withContext(Dispatchers.IO){api.productReviews(seed.id)}}.getOrDefault(ProductReviews(p.rating,p.reviewCount,emptyList()))
        if(group==null || family?.groups?.none{it.key==group&&it.count>0}!=false) group=family?.groups?.firstOrNull{it.count>0}?.key
        loading=false
    }'''
    new='''    LaunchedEffect(seed.id,reviewRefresh){
        val loaded=withContext(Dispatchers.IO){coroutineScope{
            val productJob=async{runCatching{api.product(seed.id)}.getOrNull()}
            val familyJob=async{runCatching{api.productFamily(seed.id)}.getOrNull()}
            val reviewsJob=async{runCatching{api.productReviews(seed.id)}.getOrNull()}
            Triple(productJob.await(),familyJob.await(),reviewsJob.await())
        }}
        loaded.first?.let{p=it};family=loaded.second;reviews=loaded.third?:ProductReviews(p.rating,p.reviewCount,emptyList())
        if(group==null || family?.groups?.none{it.key==group&&it.count>0}!=false) group=family?.groups?.filter{it.count>0}?.minByOrNull{relatedGroupPriorityV135(it)}?.key
        loading=false
    }'''
    v=once(v,old,new,'parallel product/family/reviews')
    marker='@Composable fun ProductV100('
    helper='''private fun relatedGroupPriorityV135(g:FamilyGroup):Int{
    val s=(g.key+" "+g.label).lowercase()
    return when{listOf("variant","variante","model","configur").any{s.contains(it)}->0;s.contains("accesor")->1;listOf("consum","ribbon","etichet","label").any{s.contains(it)}->2;listOf("service","servici","support").any{s.contains(it)}->3;listOf("software","app","licen").any{s.contains(it)}->4;else->10}
}

'''
    if 'relatedGroupPriorityV135' not in v: v=v.replace(marker,helper+marker,1)
    v=v.replace('val groups=family?.groups.orEmpty().filter{it.count>0}','val groups=family?.groups.orEmpty().filter{it.count>0}.sortedBy(::relatedGroupPriorityV135)',1)
    V100.write_text(v)


def patch_rfq_android():
    s=RFQ.read_text()
    if 'import androidx.compose.ui.platform.LocalUriHandler' not in s:
        s=s.replace('import androidx.compose.ui.platform.LocalContext\n','import androidx.compose.ui.platform.LocalContext\nimport androidx.compose.ui.platform.LocalUriHandler\n',1)
    if 'import kotlinx.coroutines.delay' not in s:
        s=s.replace('import kotlinx.coroutines.Dispatchers\n','import kotlinx.coroutines.Dispatchers\nimport kotlinx.coroutines.delay\n',1)
    old='fun create(token:String?,rows:List<RfqDraftItemV130>,who:RfqRequesterV130,note:String):RfqDetailV130{val a=JSONArray();rows.forEach{a.put(JSONObject().put("product_id",it.productId).put("quantity",it.quantity))};val b=JSONObject().put("items",a).put("first_name",who.firstName).put("last_name",who.lastName).put("email",who.email).put("phone",who.phone).put("company",who.company).put("vat",who.vat).put("note",note);return detail(JSONObject(request("POST","/rfqs",token,b)))}'
    new='fun create(token:String?,rows:List<RfqDraftItemV130>,who:RfqRequesterV130,note:String,createAccount:Boolean=false,consent:Boolean=false):RfqDetailV130{val a=JSONArray();rows.forEach{a.put(JSONObject().put("product_id",it.productId).put("quantity",it.quantity))};val b=JSONObject().put("items",a).put("first_name",who.firstName).put("last_name",who.lastName).put("email",who.email).put("phone",who.phone).put("company",who.company).put("vat",who.vat).put("note",note).put("create_account",createAccount).put("consent",consent).put("source","APK");return detail(JSONObject(request("POST","/rfqs",token,b)))}'
    s=once(s,old,new,'RFQ create flags')
    old='fun list(token:String,page:Int=1):RfqPageV130{val o=JSONObject(request("GET","/me/rfqs?page=$page&per_page=10",token));val a=o.optJSONArray("items")?:JSONArray();return RfqPageV130((0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::summary)},o.optInt("page",page),o.optInt("pages",1),o.optInt("total"))}'
    new='fun list(token:String,page:Int=1,search:String="",perPage:Int=10):RfqPageV130{val q=if(search.isBlank())"" else "&search=${java.net.URLEncoder.encode(search.trim(),\"UTF-8\")}";val o=JSONObject(request("GET","/me/rfqs?page=$page&per_page=${perPage.coerceIn(1,30)}$q",token));val a=o.optJSONArray("items")?:JSONArray();return RfqPageV130((0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::summary)},o.optInt("page",page),o.optInt("pages",1),o.optInt("total"))}'
    s=once(s,old,new,'RFQ searchable list')

    old_state='val scope=rememberCoroutineScope();var who by remember{mutableStateOf(RfqRequesterV130(email=session.customerEmail))};var note by remember{mutableStateOf("")};var busy by remember{mutableStateOf(false)};var error by remember{mutableStateOf("")};var sent by remember{mutableStateOf<RfqDetailV130?>(null)}'
    new_state='val scope=rememberCoroutineScope();val uriHandler=LocalUriHandler.current;val loggedIn=session.accessToken!=null;var who by remember{mutableStateOf(RfqRequesterV130(email=session.customerEmail))};var editRequester by remember{mutableStateOf(!loggedIn)};var createAccount by remember{mutableStateOf(!loggedIn)};var consent by remember{mutableStateOf(false)};var note by remember{mutableStateOf("")};var busy by remember{mutableStateOf(false)};var error by remember{mutableStateOf("")};var sent by remember{mutableStateOf<RfqDetailV130?>(null)}'
    s=once(s,old_state,new_state,'RFQ requester state')
    old_section='item{RfqSection("Solicitant"){Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){RfqField(who.firstName,{who=who.copy(firstName=it)},"Prenume *",Modifier.weight(1f));RfqField(who.lastName,{who=who.copy(lastName=it)},"Nume *",Modifier.weight(1f))};RfqField(who.email,{who=who.copy(email=it)},"Email *",keyboard=KeyboardType.Email);RfqField(who.phone,{who=who.copy(phone=it)},"Telefon *",keyboard=KeyboardType.Phone);RfqField(who.company,{who=who.copy(company=it)},"Companie (opțional)");RfqField(who.vat,{who=who.copy(vat=it)},"Cod TVA (opțional)")}}'
    new_section='''item{RfqSection("Solicitant"){
            if(loggedIn&&!editRequester){
                Row(verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text("${who.firstName} ${who.lastName}",fontWeight=FontWeight.ExtraBold,color=RfqInk);Text(who.email,fontSize=11.sp,color=RfqMuted);Text(who.phone,fontSize=11.sp,color=RfqMuted);if(who.company.isNotBlank())Text(listOf(who.company,who.vat).filter{it.isNotBlank()}.joinToString(" · "),fontSize=11.sp,color=RfqMuted)};TextButton(onClick={editRequester=true}){Icon(Icons.Default.Edit,null);Spacer(Modifier.width(4.dp));Text("Editează")}}
            }else{
                Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){RfqField(who.firstName,{who=who.copy(firstName=it)},"Prenume *",Modifier.weight(1f));RfqField(who.lastName,{who=who.copy(lastName=it)},"Nume *",Modifier.weight(1f))};RfqField(who.email,{who=who.copy(email=it)},"Email *",keyboard=KeyboardType.Email);RfqField(who.phone,{who=who.copy(phone=it)},"Telefon *",keyboard=KeyboardType.Phone);RfqField(who.company,{who=who.copy(company=it)},"Companie (opțional)");RfqField(who.vat,{who=who.copy(vat=it)},"Cod TVA (opțional)");if(loggedIn)OutlinedButton(onClick={editRequester=false},modifier=Modifier.fillMaxWidth()){Text("Gata")}
            }
            if(!loggedIn){Row(Modifier.fillMaxWidth().clickable{createAccount=!createAccount},verticalAlignment=Alignment.CenterVertically){Checkbox(createAccount,{createAccount=it});Text("Creează cont AutoID",fontWeight=FontWeight.Bold,color=RfqInk)}}
        }}'''
    s=once(s,old_section,new_section,'RFQ requester UX')
    old_details='item{RfqSection("Detalii cerere"){OutlinedTextField(note,{if(it.length<=4000)note=it},label={Text("Notă comandă *")},supportingText={Text("Descrie configurația, termenul sau cerințele speciale.")},modifier=Modifier.fillMaxWidth(),minLines=4,shape=RoundedCornerShape(8.dp));if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error,fontSize=12.sp)}}'
    new_details='''item{RfqSection("Detalii cerere"){OutlinedTextField(note,{if(it.length<=4000)note=it},label={Text("Notă comandă *")},supportingText={Text("Descrie configurația, termenul sau cerințele speciale.")},modifier=Modifier.fillMaxWidth(),minLines=4,shape=RoundedCornerShape(8.dp));HorizontalDivider(color=RfqBorder);Row(Modifier.fillMaxWidth().clickable{consent=!consent},verticalAlignment=Alignment.Top){Checkbox(consent,{consent=it});Column(Modifier.weight(1f).padding(top=10.dp)){Text("Vom folosi informațiile furnizate pentru a răspunde solicitării și pentru actualizări despre produse și servicii conexe. Vă puteți dezabona în orice moment. *",fontSize=10.sp,color=RfqMuted);TextButton(onClick={uriHandler.openUri("https://www.autoid.ro/politica-de-confidentialitate/")},contentPadding=PaddingValues(0.dp)){Text("Politica de confidențialitate",fontSize=10.sp,fontWeight=FontWeight.Bold)}}};if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error,fontSize=12.sp)}}'''
    s=once(s,old_details,new_details,'RFQ consent UX')
    s=s.replace('RfqApiV130.create(session.accessToken,rows,who,note)','RfqApiV130.create(session.accessToken,rows,who,note,createAccount&&!loggedIn,consent)',1)
    s=s.replace('&&note.isNotBlank(),modifier=Modifier.fillMaxWidth()','&&note.isNotBlank()&&consent,modifier=Modifier.fillMaxWidth()',1)

    old_account_state='var error by remember{mutableStateOf("")};var confirm by remember{mutableStateOf<String?>(null)}'
    new_account_state='var error by remember{mutableStateOf("")};var confirm by remember{mutableStateOf<String?>(null)};var query by remember{mutableStateOf("")}'
    s=once(s,old_account_state,new_account_state,'RFQ account query state')
    s=s.replace('RfqApiV130.list(token,target)','RfqApiV130.list(token,target,query,10)',1)
    s=s.replace('LaunchedEffect(initialId){if(initialId>0)loadDetail(initialId)else loadList(true)}','LaunchedEffect(initialId){if(initialId>0)loadDetail(initialId)else loadList(true)}\n    LaunchedEffect(query){if(initialId<=0){delay(300);loadList(true)}}',1)
    old_list='if(selected==null)LazyColumn(Modifier.padding(pad).fillMaxSize(),contentPadding=PaddingValues(14.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){if(busy&&list.isEmpty())'
    new_list='if(selected==null)LazyColumn(Modifier.padding(pad).fillMaxSize(),contentPadding=PaddingValues(14.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){item{OutlinedTextField(query,{query=it},modifier=Modifier.fillMaxWidth(),singleLine=true,leadingIcon={Icon(Icons.Default.Search,null)},placeholder={Text("Caută după RFQ / ID")},shape=RoundedCornerShape(10.dp))};if(busy&&list.isEmpty())'
    s=once(s,old_list,new_list,'RFQ search field')
    RFQ.write_text(s)


def patch_plugin():
    s=PLUGIN.read_text()
    s=once(s,' * Version: 1.1.26',' * Version: 1.1.27','plugin version')
    s=once(s,"            'version'=>'1.1.26',","            'version'=>'1.1.27',",'health version')
    s=s.replace('AutoID-Mobile-WordPress/1.1.26','AutoID-Mobile-WordPress/1.1.27')

    route="        register_rest_route(self::NS, '/ai/history', $public + ['methods'=>'GET','callback'=>[__CLASS__,'ai_history_v134']]);"
    s=once(s,route,route+"\n        register_rest_route(self::NS, '/ai/reset', $public + ['methods'=>'POST','callback'=>[__CLASS__,'ai_reset_v135']]);",'ai reset route')
    marker='    private static function support_center_app_chat_v132($message,$product_id,$device_id,$context) {'
    reset='''    public static function ai_reset_v135(WP_REST_Request $r) {
        $device_id=self::chat_device_id_v129($r);if(is_wp_error($device_id))return $device_id;
        $authorized=self::verify_chat_token_v129($r,$device_id);if(is_wp_error($authorized))return $authorized;
        $old=self::chat_thread_v134($device_id,0,false);
        if($old>0){
            self::chat_set_mode_v134($old,'closed');
            update_post_meta($old,'_autoid_chat_archived_device_hash',(string)get_post_meta($old,'_autoid_chat_device_hash',true));
            delete_post_meta($old,'_autoid_chat_device_hash');
            self::chat_append_v134($old,'system','Clientul a pornit o conversație nouă din aplicația AutoID.');
        }
        delete_transient('autoid_sc_app_'.md5(hash('sha256',(string)$device_id)));
        $product_id=absint($r->get_param('product_id'));
        $thread_id=self::chat_thread_v134($device_id,$product_id,true);
        return rest_ensure_response(['ok'=>$thread_id>0,'thread_id'=>$thread_id,'mode'=>'ai','source'=>'APK']);
    }

'''
    s=once(s,marker,reset+marker,'ai reset handler')

    # RFQ consent/create-account values are explicit rather than hard-coded.
    requester="        $requester=['user_id'=>$uid,'first_name'=>$first,'last_name'=>$last,'email'=>$email,'phone'=>$phone,'company'=>$company,'vat'=>$vat];"
    requester_new="""        $consent=!empty($b['consent']);if(!$consent)return new WP_Error('autoid_rfq_consent_required','Consimțământul pentru procesarea solicitării este obligatoriu.',['status'=>400]);
        $create_account=!$uid && !empty($b['create_account']);
        if($create_account){
            if(email_exists($email))return new WP_Error('autoid_rfq_account_exists','Există deja un cont cu acest email. Autentifică-te înainte de a crea cererea.',['status'=>409]);
            $new_uid=wc_create_new_customer($email,'',wp_generate_password(24,true,true));if(is_wp_error($new_uid))return $new_uid;$uid=absint($new_uid);
            wp_update_user(['ID'=>$uid,'first_name'=>$first,'last_name'=>$last,'display_name'=>trim($first.' '.$last)]);
            update_user_meta($uid,'billing_first_name',$first);update_user_meta($uid,'billing_last_name',$last);update_user_meta($uid,'billing_phone',$phone);update_user_meta($uid,'billing_company',$company);if($vat!=='')update_user_meta($uid,'billing_vat_number',$vat);
        }
        $requester=['user_id'=>$uid,'first_name'=>$first,'last_name'=>$last,'email'=>$email,'phone'=>$phone,'company'=>$company,'vat'=>$vat];"""
    s=once(s,requester,requester_new,'RFQ consent/account')
    s=once(s,"'_autoid_rfq_items'=>$items,'_autoid_rfq_note'=>$note,'_autoid_rfq_consent'=>1,'_autoid_rfq_create_account'=>0,","'_autoid_rfq_items'=>$items,'_autoid_rfq_note'=>$note,'_autoid_rfq_consent'=>$consent?1:0,'_autoid_rfq_create_account'=>$create_account?1:0,",'RFQ meta flags')

    old_list="""        $uid=absint($r->get_param('_autoid_user_id'));$page=max(1,absint($r->get_param('page')));$per=max(1,min(30,absint($r->get_param('per_page'))?:10));
        $legacy='s:7:\"user_id\";i:'.$uid.';';$q=new WP_Query(['post_type'=>'autoid_rfq','post_status'=>['private','publish'],'posts_per_page'=>$per,'paged'=>$page,'orderby'=>'date','order'=>'DESC','meta_query'=>['relation'=>'OR',['key'=>'_autoid_rfq_user_id','value'=>$uid,'compare'=>'=','type'=>'NUMERIC'],['key'=>'_autoid_rfq_requester','value'=>$legacy,'compare'=>'LIKE']]]);"""
    new_list="""        $uid=absint($r->get_param('_autoid_user_id'));$page=max(1,absint($r->get_param('page')));$per=max(1,min(30,absint($r->get_param('per_page'))?:10));$search=sanitize_text_field((string)$r->get_param('search'));
        $legacy='s:7:\"user_id\";i:'.$uid.';';$args=['post_type'=>'autoid_rfq','post_status'=>['private','publish'],'posts_per_page'=>$per,'paged'=>$page,'orderby'=>'date','order'=>'DESC','meta_query'=>['relation'=>'OR',['key'=>'_autoid_rfq_user_id','value'=>$uid,'compare'=>'=','type'=>'NUMERIC'],['key'=>'_autoid_rfq_requester','value'=>$legacy,'compare'=>'LIKE']]];if($search!==''){if(ctype_digit($search))$args['post__in']=[absint($search)];else $args['s']=$search;}$q=new WP_Query($args);"""
    s=once(s,old_list,new_list,'RFQ backend search')

    # Replace the current account orders handler with a lightweight search/limit-aware response.
    pattern=r"    public static function me_orders\(WP_REST_Request \$r\) \{.*?\n    \}\n\n    public static function me_order_detail"
    replacement='''    public static function me_orders(WP_REST_Request $r) {
        $ok=self::require_wc();if(is_wp_error($ok))return $ok;
        $uid=absint($r->get_param('_autoid_user_id'));if(!$uid)$uid=self::bearer_user_id($r);if(!$uid)return new WP_Error('autoid_auth_required','Autentificare necesară.',['status'=>401]);
        $limit=max(1,min(50,absint($r->get_param('limit'))?:20));$search=sanitize_text_field((string)$r->get_param('search'));
        $args=['customer_id'=>$uid,'limit'=>$search!==''?50:$limit,'orderby'=>'date','order'=>'DESC','return'=>'objects'];
        if($search!==''&&ctype_digit($search))$args['include']=[absint($search)];
        $orders=wc_get_orders($args);$out=[];
        foreach($orders as $o){if($search!==''&&!ctype_digit($search)&&stripos((string)$o->get_order_number(),$search)===false)continue;$tracking=self::order_tracking_payload_v119($o);$out[]=['id'=>$o->get_id(),'number'=>(string)$o->get_order_number(),'status'=>$o->get_status(),'status_label'=>wc_get_order_status_name($o->get_status()),'total'=>$o->get_total(),'currency'=>$o->get_currency(),'created_at'=>$o->get_date_created()?$o->get_date_created()->date('c'):'','tracking_number'=>$tracking['tracking_number']??'','tracking_url'=>$tracking['tracking_url']??'','carrier'=>$tracking['carrier']??'','review_consent'=>$o->get_meta('_autoid_review_consent',true)==='yes','can_pay'=>$o->needs_payment()&&!$o->is_paid()&&$o->get_payment_method()==='stripe','can_cancel'=>!$o->is_paid()&&$o->has_status(['pending','failed','on-hold'])];if(count($out)>=$limit)break;}
        return rest_ensure_response(['orders'=>$out]);
    }

    public static function me_order_detail'''
    s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
    if n!=1: raise RuntimeError(f'me_orders replacement expected 1 match, found {n}')
    PLUGIN.write_text(s)


def patch_gradle():
    s=GRADLE.read_text();s=once(s,'versionCode = 13302','versionCode = 13303','RC7 versionCode');GRADLE.write_text(s)


def main():
    patch_android_account();patch_chat();patch_public_cache_and_product_perf();patch_rfq_android();patch_plugin();patch_gradle()
    checks={
        APP/'V135AccountUx.kt':['Înapoi la cont','Caută după Order ID'],
        CHAT:['Pornește o conversație nouă','PersistentAiChatScreenV135'],
        RFQ:['Caută după RFQ / ID','Creează cont AutoID','Politica de confidențialitate'],
        PLUGIN:["'/ai/reset'",'Version: 1.1.27',"'source'=>'APK'"],
    }
    for p,needles in checks.items():
        t=p.read_text()
        for needle in needles:
            if needle not in t:raise RuntimeError(f'{p.name}: missing {needle}')
    print('Applied RC7 UX/performance/RFQ/chat lifecycle patch')

if __name__=='__main__': main()
