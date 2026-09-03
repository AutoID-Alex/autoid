#!/usr/bin/env python3
"""Apply Android v1.0.30 / AutoID Mobile v1.1.22 RFQ account integration."""

from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app'
API=APP/'data/AutoIdApi.kt'
PLUGIN=ROOT/'wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'
MANIFEST=ROOT/'android-v0.1/app/src/main/AndroidManifest.xml'
ASSETS=ROOT/'ci/v130'

def once(text,old,new,label):
    n=text.count(old)
    if n!=1: raise RuntimeError(f'{label}: expected 1 match, found {n}')
    return text.replace(old,new,1)

def patch_plugin():
    text=PLUGIN.read_text()
    text=once(text,' * Version: 1.1.21',' * Version: 1.1.22','plugin version')
    text=once(text,"        add_action('updated_post_meta',[__CLASS__,'fcm_meta_changed_v128'],30,4);","        add_action('updated_post_meta',[__CLASS__,'fcm_meta_changed_v128'],30,4);\n        add_action('updated_post_meta',[__CLASS__,'rfq_meta_changed_v130'],40,4);",'RFQ push hook')
    text=once(text,"        register_rest_route(self::NS, '/rfq', $public + ['methods'=>'POST','callback'=>[__CLASS__,'rfq']]);","        register_rest_route(self::NS, '/rfq', $public + ['methods'=>'POST','callback'=>[__CLASS__,'rfq']]);\n        register_rest_route(self::NS, '/rfqs', $public + ['methods'=>'POST','callback'=>[__CLASS__,'rfq_create_v130']]);",'RFQ create route')
    anchor="        register_rest_route(self::NS, '/me/orders', ['methods'=>'GET','callback'=>[__CLASS__,'me_orders'],'permission_callback'=>[__CLASS__,'auth_permission']]);"
    routes=anchor+"\n        register_rest_route(self::NS, '/me/rfqs', ['methods'=>'GET','callback'=>[__CLASS__,'rfq_list_v130'],'permission_callback'=>[__CLASS__,'auth_permission']]);\n        register_rest_route(self::NS, '/me/rfqs/(?P<id>\\d+)', ['methods'=>'GET','callback'=>[__CLASS__,'rfq_detail_v130'],'permission_callback'=>[__CLASS__,'auth_permission']]);\n        register_rest_route(self::NS, '/me/rfqs/(?P<id>\\d+)/action', ['methods'=>'POST','callback'=>[__CLASS__,'rfq_action_v130'],'permission_callback'=>[__CLASS__,'auth_permission']]);\n        register_rest_route(self::NS, '/me/rfqs/(?P<id>\\d+)/documents/(?P<kind>offer|proforma|invoice)', ['methods'=>'GET','callback'=>[__CLASS__,'rfq_document_v130'],'permission_callback'=>[__CLASS__,'auth_permission']]);"
    text=once(text,anchor,routes,'RFQ account routes')
    text=once(text,"    private static function support_center_info() {",(ASSETS/'autoid_rfq_v130.php.inc').read_text()+"\n    private static function support_center_info() {",'RFQ backend adapter')
    old="""    private static function chat_device_id_v129(WP_REST_Request $r) {
        $device_id=trim((string)$r->get_param('device_id'));
        if($device_id==='' || strlen($device_id)>128 || !preg_match('/^[A-Za-z0-9._:-]{16,128}$/',$device_id)) {
            return new WP_Error('autoid_chat_device_invalid','Identificatorul sesiunii de chat este invalid.',['status'=>400]);
        }
        return $device_id;
    }"""
    new="""    private static function chat_device_id_v129(WP_REST_Request $r) {
        $device_id=trim((string)$r->get_param('device_id'));
        if($device_id==='')$device_id=trim((string)$r->get_header('x-autoid-device-id'));
        if($device_id===''){$json=$r->get_json_params();if(is_array($json))$device_id=trim((string)($json['device_id']??''));}
        if(strlen($device_id)<8 || strlen($device_id)>256 || preg_match('/[\\x00-\\x1F\\x7F]/',$device_id)) {
            return new WP_Error('autoid_chat_device_invalid','Identificatorul sesiunii de chat este invalid.',['status'=>400]);
        }
        return $device_id;
    }"""
    text=once(text,old,new,'chat identifier compatibility')
    text=once(text,"            'version'=>'1.1.21',","            'version'=>'1.1.22',",'health version')
    text=text.replace('AutoID-Mobile-WordPress/1.1.21','AutoID-Mobile-WordPress/1.1.22')
    PLUGIN.write_text(text)

def patch_android():
    text=API.read_text()
    text=once(text,'fun chatTokenV129(deviceId:String):ChatSessionV129{val b=JSONObject().put("device_id",deviceId).put("platform","android").put("app_version","1.0.29");val o=JSONObject(post("$MOBILE/ai/token",b.toString()));', 'fun chatTokenV129(deviceId:String):ChatSessionV129{val b=JSONObject().put("device_id",deviceId).put("platform","android").put("app_version","1.0.30");val o=JSONObject(post("$MOBILE/ai/token?device_id=${enc(deviceId)}",b.toString()));','chat token query fallback')
    text=once(text,'return html(JSONObject(post("$MOBILE/ai/chat",b.toString(),chatToken)).optString("answer"))','return html(JSONObject(post("$MOBILE/ai/chat?device_id=${enc(deviceId)}",b.toString(),chatToken)).optString("answer"))','chat request query fallback')
    text=once(text,'AutoID-Android/1.0.29','AutoID-Android/1.0.30','user agent')
    API.write_text(text)

    gradle=GRADLE.read_text()
    gradle=once(gradle,'versionCode = 13200','versionCode = 13300','version code')
    gradle=once(gradle,'versionName = "1.0.29"','versionName = "1.0.30"','version name')
    gradle=once(gradle,'    implementation("androidx.core:core-ktx:1.16.0")','    implementation("androidx.core:core-ktx:1.16.0")\n    implementation("androidx.browser:browser:1.8.0")','custom tabs dependency')
    GRADLE.write_text(gradle)

    shutil.copyfile(ASSETS/'RfqV130.kt',APP/'RfqV130.kt')
    xml=ROOT/'android-v0.1/app/src/main/res/xml';xml.mkdir(parents=True,exist_ok=True);shutil.copyfile(ASSETS/'autoid_file_paths_v130.xml',xml/'autoid_file_paths_v130.xml')

    manifest=MANIFEST.read_text()
    provider='''        <provider android:name="androidx.core.content.FileProvider" android:authorities="${applicationId}.files" android:exported="false" android:grantUriPermissions="true">
            <meta-data android:name="android.support.FILE_PROVIDER_PATHS" android:resource="@xml/autoid_file_paths_v130" />
        </provider>'''
    manifest=once(manifest,'        <service android:name=".AutoIdMessagingServiceV128"',provider+'\n        <service android:name=".AutoIdMessagingServiceV128"','file provider')
    deep='''            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="autoid" android:host="account" android:pathPrefix="/rfq/" />
            </intent-filter>'''
    manifest=once(manifest,'            <intent-filter>\n                <action android:name="android.intent.action.MAIN" />',deep+'\n            <intent-filter>\n                <action android:name="android.intent.action.MAIN" />','RFQ deep link')
    MANIFEST.write_text(manifest)

    session=APP/'data/SessionStore.kt';s=session.read_text();s=once(s,'    var pendingReviewOrderId:Long get()=prefs.getLong("pending_review_order_id",0L); set(v){prefs.edit().putLong("pending_review_order_id",v).apply()}','    var pendingReviewOrderId:Long get()=prefs.getLong("pending_review_order_id",0L); set(v){prefs.edit().putLong("pending_review_order_id",v).apply()}\n    var pendingRfqIdV130:Long get()=prefs.getLong("pending_rfq_id_v130",0L); set(v){prefs.edit().putLong("pending_rfq_id_v130",v).apply()}','pending RFQ');session.write_text(s)

    main=APP/'MainActivity.kt';m=main.read_text();m=once(m,'        intent?.getLongExtra("review_order_id",0L)?.takeIf{it>0}?.let{session.pendingReviewOrderId=it}','        intent?.getLongExtra("review_order_id",0L)?.takeIf{it>0}?.let{session.pendingReviewOrderId=it}\n        intent?.getLongExtra("rfq_id",0L)?.takeIf{it>0}?.let{session.pendingRfqIdV130=it}\n        intent?.data?.takeIf{it.scheme=="autoid"&&it.host=="account"}?.lastPathSegment?.toLongOrNull()?.takeIf{it>0}?.let{session.pendingRfqIdV130=it}','initial RFQ deep link')
    m=once(m,'override fun onNewIntent(intent:Intent){super.onNewIntent(intent);setIntent(intent);intent.getLongExtra("review_order_id",0L).takeIf{it>0}?.let{SessionStore(this).pendingReviewOrderId=it;recreate()}}','override fun onNewIntent(intent:Intent){super.onNewIntent(intent);setIntent(intent);val s=SessionStore(this);intent.getLongExtra("review_order_id",0L).takeIf{it>0}?.let{s.pendingReviewOrderId=it};intent.getLongExtra("rfq_id",0L).takeIf{it>0}?.let{s.pendingRfqIdV130=it};intent.data?.lastPathSegment?.toLongOrNull()?.takeIf{it>0}?.let{s.pendingRfqIdV130=it};recreate()}','new RFQ deep link')
    main.write_text(m)

    push=APP/'PrivacyPushV128.kt';p=push.read_text();p=once(p,'            type=="order_review"&&orderId>0->Intent(context,MainActivity::class.java).putExtra("review_order_id",orderId)','            type=="order_review"&&orderId>0->Intent(context,MainActivity::class.java).putExtra("review_order_id",orderId)\n            type=="rfq_status"&&(d["rfq_id"]?.toLongOrNull()?:0L)>0->Intent(context,MainActivity::class.java).putExtra("rfq_id",d["rfq_id"]!!.toLong())','RFQ notification intent');push.write_text(p)

    root=APP/'V100Screens.kt';v=root.read_text()
    v=once(v,'    var rfq by remember { mutableStateOf(false) }\n    var rfqLines by remember { mutableStateOf<List<CartLine>>(emptyList()) }','    val rfqStoreV130=remember{RfqStoreV130(appContext)}\n    var rfq by remember { mutableStateOf(false) }\n    var rfqAccountV130 by remember { mutableStateOf(session.pendingRfqIdV130>0) }\n    var rfqLines by remember { mutableStateOf(rfqStoreV130.items()) }\n    val rfqScopeV130=rememberCoroutineScope()','RFQ persistent state')
    old='''    fun addRfq(p: Product, q: Int = 1) {
        val x = rfqLines.toMutableList()
        val i = x.indexOfFirst { it.product.id == p.id }
        if (i >= 0) x[i] = x[i].copy(quantity = x[i].quantity + q) else x += CartLine(p, q)
        rfqLines = x
        rfq = true
    }'''
    new='''    fun addRfq(p: Product, q: Int = 1) {
        rfqLines=rfqStoreV130.add(p,q)
        rfq=true
    }'''
    v=once(v,old,new,'persistent add RFQ')
    anchor='''    if (ai) {
        NativeAiChatScreen(api, null) { ai = false }
        return
    }'''
    screens=anchor+'''\n    if(rfq){RfqDraftScreenV130(api,session,rfqLines,{rfqLines=it;rfqStoreV130.replace(it)},{rfq=false},{id->rfq=false;rfqScopeV130.launch{runCatching{withContext(Dispatchers.IO){api.product(id)}}.onSuccess{openProduct(it)}}},{rfqStoreV130.clear();rfqLines=emptyList()});return}\n    if(rfqAccountV130){val initial=session.pendingRfqIdV130;RfqAccountScreenV130(session,{rfqAccountV130=false;session.pendingRfqIdV130=0},{id->rfqAccountV130=false;session.pendingRfqIdV130=0;rfqScopeV130.launch{runCatching{withContext(Dispatchers.IO){api.product(id)}}.onSuccess{openProduct(it)}}},initial);return}'''
    v=once(v,anchor,screens,'RFQ screens')
    old_call='''                        V100Tab.Account -> AccountV117(
                            api,
                            session,
                            commerce,
                            ::openProduct,
                            { tab = V100Tab.Cart },
                            { favorites = true },
                            { notifications = true }
                        )'''
    new_call='''                        V100Tab.Account -> AccountV117(
                            api,
                            session,
                            commerce,
                            ::openProduct,
                            { tab = V100Tab.Cart },
                            { favorites = true },
                            { notifications = true },
                            { rfqAccountV130 = true }
                        )'''
    v=once(v,old_call,new_call,'account RFQ callback')
    old_dialog='''    if (rfq) RfqV100(
        api,
        rfqLines,
        { rfqLines = it },
        { rfq = false },
        { rfqLines = emptyList(); rfq = false }
    )
'''
    v=once(v,old_dialog,'','remove legacy RFQ dialog')
    indicator_anchor='''                        V100Tab.Ai -> Unit
                    }
                }
            }
        }
    }'''
    indicator_replacement='''                        V100Tab.Ai -> Unit
                    }
                }
                if(rfqLines.isNotEmpty())Surface(
                    modifier=Modifier.align(Alignment.TopEnd).padding(12.dp).clickable{rfq=true},
                    shape=RoundedCornerShape(8.dp),color=RfqIndicatorOrangeV130,shadowElevation=5.dp
                ){Row(Modifier.padding(horizontal=12.dp,vertical=10.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.RequestQuote,null,tint=Color.White,modifier=Modifier.size(18.dp));Spacer(Modifier.width(6.dp));Text("Cerere ofertă · ${rfqLines.sumOf{it.quantity}}",color=Color.White,fontWeight=FontWeight.ExtraBold,fontSize=11.sp)}}
            }
        }
    }'''
    v=once(v,indicator_anchor,indicator_replacement,'global RFQ indicator')
    v=once(v,'private val Ink=Color(0xFF101828)','private val Ink=Color(0xFF101828)\nprivate val RfqIndicatorOrangeV130=Color(0xFFF7630C)','RFQ indicator color')
    root.write_text(v)

    wrapper=APP/'V117AccountCheckout.kt';w=wrapper.read_text();w=once(w,'fun AccountV117(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onCart:()->Unit,onFavorites:()->Unit,onNotifications:()->Unit){\n    AccountV114(api,session,commerce,onProduct,onCart,onFavorites,onNotifications)','fun AccountV117(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onCart:()->Unit,onFavorites:()->Unit,onNotifications:()->Unit,onRfqs:()->Unit){\n    AccountV114(api,session,commerce,onProduct,onCart,onFavorites,onNotifications,onRfqs)','account wrapper');wrapper.write_text(w)
    account=APP/'V114CommerceUx.kt';a=account.read_text();a=once(a,'fun AccountV114(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onCart:()->Unit,onFavorites:()->Unit,onNotifications:()->Unit){','fun AccountV114(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onCart:()->Unit,onFavorites:()->Unit,onNotifications:()->Unit,onRfqs:()->Unit){','account signature')
    a=once(a,'Triple("dashboard","Panou control",Icons.Default.Dashboard),Triple("orders","Comenzi",Icons.Default.ReceiptLong),Triple("details","Detalii cont",Icons.Default.ManageAccounts)','Triple("dashboard","Panou control",Icons.Default.Dashboard),Triple("orders","Comenzi",Icons.Default.ReceiptLong),Triple("rfqs","Cereri de ofertă",Icons.Default.RequestQuote),Triple("details","Detalii cont",Icons.Default.ManageAccounts)','account RFQ menu')
    a=once(a,'.clickable{panel=id}.padding(horizontal=12.dp,vertical=12.dp)','.clickable{if(id=="rfqs")onRfqs()else panel=id}.padding(horizontal=12.dp,vertical=12.dp)','account RFQ click')
    account.write_text(a)

def main():
    patch_plugin();patch_android();print('Applied Android v1.0.30 + AutoID Mobile v1.1.22 RFQ account integration and chat identifier hotfix')

if __name__=='__main__':main()
