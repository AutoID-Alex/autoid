from pathlib import Path
import re

ROOT=Path('.')

def rep(s,old,new,label):
    if old not in s: raise RuntimeError('missing '+label)
    return s.replace(old,new,1)

# PHP assumes v0.5 migration already applied
p=ROOT/'wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php'
s=p.read_text()
s=s.replace('Version: 0.5.0','Version: 0.6.0').replace('AutoID_Mobile_Commerce_Bridge_050','AutoID_Mobile_Commerce_Bridge_060').replace("'version'=>'0.5.0'","'version'=>'0.6.0'").replace("'|0.5'","'|0.6'")
s=rep(s,"register_rest_route(self::NS, '/brands', $public + ['methods'=>'GET','callback'=>[__CLASS__,'brands']]);",
"""register_rest_route(self::NS, '/brands', $public + ['methods'=>'GET','callback'=>[__CLASS__,'brands']]);
        register_rest_route(self::NS, '/navigation', $public + ['methods'=>'GET','callback'=>[__CLASS__,'navigation']]);
        register_rest_route(self::NS, '/ai/chat', $public + ['methods'=>'POST','callback'=>[__CLASS__,'ai_chat']]);""",'routes')
s=re.sub(r"        if \(\$search !== ''\) \{.*?\n        \}","""        if ($search !== '') {
            $ids = self::catalog_search_ids($search, 250);
            if (!$ids) return rest_ensure_response(['products'=>[],'page'=>$page,'per_page'=>$per,'total'=>0,'pages'=>0]);
            $args['include'] = $ids;
            $args['orderby'] = 'include';
        }""",s,count=1,flags=re.S)
pat=r"    public static function search\(WP_REST_Request \$r\) \{.*?\n    \}\n\n    private static function fibosearch_ids\(\$q,\$limit=50\) \{.*?\n    \}\n\n    public static function support"
new="""    public static function search(WP_REST_Request $r) {
        $q = sanitize_text_field((string)$r->get_param('q'));
        if (mb_strlen($q)<2) return rest_ensure_response(['suggestions'=>[],'engine'=>'autoid-catalog']);
        $ids = self::catalog_search_ids($q, 16);
        $suggestions = [];
        foreach ($ids as $id) {
            $p = wc_get_product($id);
            if (!$p || $p->get_status()!=='publish' || !$p->is_visible()) continue;
            $suggestions[] = self::product_row($p,false);
        }
        return rest_ensure_response(['suggestions'=>$suggestions,'engine'=>'autoid-exact+fibosearch']);
    }

    private static function catalog_search_ids($q,$limit=50) {
        $q = trim(sanitize_text_field((string)$q));
        if ($q==='') return [];
        $ids=[]; $seen=[];
        $add=function($id) use (&$ids,&$seen,$limit) { $id=(int)$id; if($id>0 && empty($seen[$id]) && count($ids)<$limit){$seen[$id]=1;$ids[]=$id;} };
        $sku_id = wc_get_product_id_by_sku($q); if ($sku_id) $add($sku_id);
        foreach (['model','pa_model','product_model','autoid_model'] as $tax) {
            if (!taxonomy_exists($tax)) continue;
            $term = get_term_by('slug',sanitize_title($q),$tax);
            if (!$term) $term = get_term_by('name',$q,$tax);
            if (!$term || is_wp_error($term)) continue;
            $query = new WP_Query(['post_type'=>'product','post_status'=>'publish','posts_per_page'=>$limit,'fields'=>'ids','no_found_rows'=>true,
                'tax_query'=>[['taxonomy'=>$tax,'field'=>'term_id','terms'=>[(int)$term->term_id]]],
                'meta_key'=>'stock_autoid','orderby'=>['meta_value_num'=>'DESC','menu_order'=>'ASC','title'=>'ASC']]);
            foreach($query->posts as $id) $add($id);
        }
        global $wpdb;
        $like = '%' . $wpdb->esc_like($q) . '%';
        $rows = $wpdb->get_col($wpdb->prepare("SELECT DISTINCT p.ID FROM {$wpdb->posts} p LEFT JOIN {$wpdb->postmeta} pm ON pm.post_id=p.ID AND pm.meta_key='_sku' WHERE p.post_type='product' AND p.post_status='publish' AND (p.post_title LIKE %s OR pm.meta_value LIKE %s) ORDER BY CASE WHEN p.post_title LIKE %s THEN 0 WHEN pm.meta_value=%s THEN 1 ELSE 2 END, p.post_title ASC LIMIT %d",$like,$like,$q.'%',$q,$limit));
        foreach($rows as $id) $add($id);
        foreach(self::fibosearch_ids($q,$limit) as $id) $add($id);
        return array_slice($ids,0,$limit);
    }

    private static function fibosearch_ids($q,$limit=50) {
        if ($q==='') return [];
        $url = add_query_arg(['action'=>'dgwt_wcas_ajax_search','s'=>$q], admin_url('admin-ajax.php'));
        $response = wp_remote_get($url,['timeout'=>4,'redirection'=>0,'headers'=>['X-AutoID-Mobile'=>'1']]);
        if (is_wp_error($response) || (int)wp_remote_retrieve_response_code($response)!==200) return [];
        $json = json_decode(wp_remote_retrieve_body($response),true); if(!is_array($json)) return [];
        $ids=[];
        $walk=function($value) use (&$walk,&$ids,$limit) {
            if(count($ids)>=$limit || !is_array($value)) return;
            $looks_product = isset($value['url']) || isset($value['title']) || isset($value['name']) || isset($value['sku']);
            if($looks_product){
                foreach(['post_id','product_id','id'] as $k) if(isset($value[$k]) && is_numeric($value[$k])) { $pid=(int)$value[$k]; $p=wc_get_product($pid); if($p) $ids[]=$pid; break; }
            }
            foreach($value as $v) $walk($v);
        };
        $walk($json);
        return array_values(array_unique($ids));
    }

    public static function support"""
s,n=re.subn(pat,new,s,count=1,flags=re.S)
if n!=1: raise RuntimeError('missing search block')
s=s.replace("foreach (['pa_model','product_model','model','autoid_model','product_tag'] as $tax)","foreach (['model','pa_model','product_model','autoid_model','product_tag'] as $tax)")
s=s.replace("$score = (stripos($tax,'model')!==false ? 100 : 20)","$score = ($tax==='model' ? 300 : (stripos($tax,'model')!==false ? 100 : 20))")
marker="    private static function family_candidate_ids(WC_Product $p,$model) {\n        $ids = [];"
s=rep(s,marker,marker+"""
        if (taxonomy_exists('model') && $model['key']!=='') {
            $term = get_term_by('slug',sanitize_title($model['key']),'model');
            if (!$term) $term = get_term_by('name',$model['label'],'model');
            if ($term && !is_wp_error($term)) {
                $q = new WP_Query(['post_type'=>'product','post_status'=>'publish','posts_per_page'=>1000,'fields'=>'ids','no_found_rows'=>true,
                    'tax_query'=>[['taxonomy'=>'model','field'=>'term_id','terms'=>[(int)$term->term_id]]]]);
                if ($q->posts) return array_values(array_unique(array_map('intval',array_merge([$p->get_id()],$q->posts))));
            }
        }""",'family canonical')
s=rep(s,"""        foreach ($map as $group=>$needles) foreach ($needles as $needle) if (strpos($hay,$needle)!==false) return $group;
        return 'variants';""","""        $detected = 'variants';
        foreach ($map as $group=>$needles) foreach ($needles as $needle) if (strpos($hay,$needle)!==false) { $detected=$group; break 2; }
        return (string)apply_filters('autoid_mobile_product_group',$detected,$p,$hay);""",'group hook')
needle="'stock_autoid'=>$stock['autoid'],'stock_distributor'=>$stock['distributor'],'delivery_label'=>$stock['delivery'],"
if needle not in s: raise RuntimeError('missing stock row')
s=s.replace(needle,needle+"\n            'availability_display'=>trim(($stock['autoid']>0?$stock['autoid'].' în stoc':'').(($stock['autoid']>0&&$stock['distributor']>0)?' · ':'').($stock['distributor']>0?$stock['distributor'].' livrare în 5–7 zile':'')),",1)
anchor="    private static function published_product($id) {"
extra=r'''    public static function navigation(WP_REST_Request $r) {
        $locations = get_nav_menu_locations(); $menu_id=0;
        foreach(['primary','main','primary-menu','header','menu-1'] as $loc) if(!empty($locations[$loc])) {$menu_id=(int)$locations[$loc];break;}
        if(!$menu_id){ $menus=wp_get_nav_menus(); if($menus){ usort($menus,fn($a,$b)=>$b->count<=>$a->count); $menu_id=(int)$menus[0]->term_id; } }
        if(!$menu_id) return rest_ensure_response(['items'=>[]]);
        $items=wp_get_nav_menu_items($menu_id,['update_post_term_cache'=>false]); if(!$items) return rest_ensure_response(['items'=>[]]);
        $rows=[]; foreach($items as $i){ if($i->post_status!=='publish') continue; $rows[(int)$i->ID]=['id'=>(int)$i->ID,'parent'=>(int)$i->menu_item_parent,'title'=>wp_strip_all_tags($i->title),'url'=>$i->url,'order'=>(int)$i->menu_order,'children'=>[]]; }
        foreach(array_keys($rows) as $id){$parent=$rows[$id]['parent']; if($parent && isset($rows[$parent])){$rows[$parent]['children'][]=&$rows[$id];}}
        $top=[]; foreach($rows as $id=>&$row) if(!$row['parent'] || !isset($rows[$row['parent']])) $top[]=&$row;
        $clean=function($arr) use (&$clean){ usort($arr,fn($a,$b)=>$a['order']<=>$b['order']); return array_map(function($x) use (&$clean){$x['children']=$clean($x['children']); return $x;},$arr);};
        return rest_ensure_response(['items'=>$clean($top)]);
    }

    public static function ai_chat(WP_REST_Request $r) {
        $message=trim(sanitize_textarea_field((string)$r->get_param('message'))); if($message==='') return new WP_Error('autoid_ai_empty','Mesaj gol.',['status'=>400]);
        $product_id=absint($r->get_param('product_id')); $context=['channel'=>'android-app','product_id'=>$product_id];
        $filtered=apply_filters('autoid_mobile_ai_chat',null,$message,$context);
        if(is_string($filtered) && trim($filtered)!=='') return rest_ensure_response(['answer'=>$filtered,'source'=>'website-filter']);
        if(is_array($filtered) && !empty($filtered['answer'])) return rest_ensure_response($filtered+['source'=>'website-filter']);
        $routes=rest_get_server()->get_routes(); $candidates=[];
        foreach($routes as $route=>$handlers){
            if(strpos($route,'/'.self::NS.'/')===0) continue;
            $low=strtolower($route); if((strpos($low,'chat')!==false || strpos($low,'assistant')!==false || strpos($low,'ai')!==false) && (strpos($low,'autoid')!==false || strpos($low,'support')!==false)) $candidates[]=$route;
        }
        foreach($candidates as $route){
            $req=new WP_REST_Request('POST',$route);
            foreach(['message','question','query','prompt'] as $k) $req->set_param($k,$message);
            $req->set_param('context',$context); if($product_id) $req->set_param('product_id',$product_id);
            $resp=rest_do_request($req); if(is_wp_error($resp) || $resp->is_error()) continue;
            $data=$resp->get_data(); $answer=self::extract_ai_answer($data);
            if($answer!=='') return rest_ensure_response(['answer'=>$answer,'source'=>'website-ai','route'=>$route]);
        }
        return new WP_Error('autoid_ai_adapter_missing','Asistentul AI al website-ului este activ, dar Bridge-ul nu i-a identificat încă endpoint-ul intern.',['status'=>503,'routes_checked'=>$candidates]);
    }

    private static function extract_ai_answer($data) {
        if(is_string($data)) return trim(wp_strip_all_tags($data));
        if(!is_array($data)) return '';
        foreach(['answer','response','reply','text','content','message'] as $k) if(isset($data[$k]) && is_string($data[$k]) && trim($data[$k])!=='') return trim(wp_strip_all_tags($data[$k]));
        foreach($data as $v){$a=self::extract_ai_answer($v); if($a!=='') return $a;} return '';
    }

'''
s=rep(s,anchor,extra+anchor,'nav ai methods')
p.write_text(s)

m=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/data/Models.kt'; s=m.read_text()
s=rep(s,'data class AiMessage(val fromUser: Boolean, val text: String, val productIds: List<Long> = emptyList())','''data class AiMessage(val fromUser: Boolean, val text: String, val productIds: List<Long> = emptyList())
data class NavItem(val id:Long,val parent:Long,val title:String,val url:String,val children:List<NavItem> = emptyList())''','nav model')
m.write_text(s)
api=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/data/AutoIdApi.kt'; s=api.read_text().replace('AutoID-Android/0.5.0','AutoID-Android/0.6.0')
s=rep(s,'    fun categories(): List<ProductCategory> {','''    fun navigation(): List<NavItem> {
        val root=JSONObject(get("$MOBILE/navigation")); val arr=root.optJSONArray("items")?:JSONArray()
        fun parse(a:JSONArray):List<NavItem>=(0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{o->NavItem(o.optLong("id"),o.optLong("parent"),html(o.optString("title")),o.optString("url"),parse(o.optJSONArray("children")?:JSONArray()))}}
        return parse(arr)
    }

    fun aiChat(message:String, productId:Long?=null):String {
        val body=JSONObject().put("message",message); productId?.let{body.put("product_id",it)}
        val root=JSONObject(post("$MOBILE/ai/chat",body.toString())); return html(root.optString("answer")).ifBlank{error("Asistentul AI nu a returnat răspuns.")}
    }

    fun categories(): List<ProductCategory> {''','api nav ai')
old='''        return (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let { suggestion ->
            suggestion.optLong("id").takeIf { it > 0 }?.let { id -> runCatching { product(id) }.getOrNull() }
        } }'''
s=rep(s,old,'return (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let(::product) }','search parse')
api.write_text(s)
main=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/MainActivity.kt'; s=main.read_text()
s=s.replace('import android.os.Bundle','import android.os.Bundle\nimport android.widget.Toast')
s=s.replace('setContent { AutoIdTheme { AutoIdApp(api, session, commerce, ::scan, ::openUrl, ::openAiChat) } }','setContent { AutoIdTheme { AutoIdApp(api, session, commerce, ::scan, ::openUrl) } }')
s=s.replace('    private fun openAiChat() = startActivity(Intent(this, AiWebChatActivity::class.java))\n','')
s=s.replace('    openUrl: (String) -> Unit,\n    openAiChat: () -> Unit\n)', '    openUrl: (String) -> Unit\n)')
s=rep(s,'    var favoriteTick by remember { mutableIntStateOf(0) }','''    var favoriteTick by remember { mutableIntStateOf(0) }
    var showAi by remember { mutableStateOf(false) }
    var aiProductId by remember { mutableStateOf<Long?>(null) }
    var menuOpen by remember { mutableStateOf(false) }
    val context = androidx.compose.ui.platform.LocalContext.current
    fun addCart(p:Product){ commerce.addToCart(p); cartTick++; Toast.makeText(context, "${p.name} adăugat în coș · ${commerce.cartCount()} produse", Toast.LENGTH_SHORT).show() }''','state')
s=rep(s,'    if (selectedProduct != null) {','''    if (showAi) {
        NativeAiChatScreen(api=api, productId=aiProductId, onBack={showAi=false;aiProductId=null})
        return
    }

    if (selectedProduct != null) {''','native ai gate')
s=s.replace('onCart = { commerce.addToCart(it); cartTick++ },','onCart = { addCart(it) },')
s=s.replace('onSupport = { _ -> openAiChat() },','onSupport = { _ -> aiProductId=selectedProduct?.id; showAi=true },')
s=s.replace('floatingActionButton = {\n            FloatingActionButton(onClick = openAiChat,','floatingActionButton = {\n            FloatingActionButton(onClick = { aiProductId=null; showAi=true },')
s=s.replace('onAi = { _ -> openAiChat() },','onAi = { _ -> aiProductId=null; showAi=true },')
s=s.replace('fun GlobalHeader(title: String = "AutoID", cartCount: Int = 0, notificationCount: Int = 0) {','fun GlobalHeader(title: String = "AutoID", cartCount: Int = 0, notificationCount: Int = 0, onMenu: (() -> Unit)? = null) {')
s=s.replace('    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {','''    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        if(onMenu!=null){ IconButton(onClick=onMenu){ Icon(Icons.Default.Menu,"Meniu") }; Spacer(Modifier.width(4.dp)) }''',1)
s=s.replace('    scan: ((String) -> Unit) -> Unit\n) {','    scan: ((String) -> Unit) -> Unit,\n    onMenu: () -> Unit = {}\n) {',1)
s=s.replace('GlobalHeader(cartCount = commerce.cartCount())','GlobalHeader(cartCount = commerce.cartCount(), onMenu=onMenu)',1)
idx=s.find('fun CategoriesScreen(');part=s[idx:]
part=part.replace('    scan: ((String) -> Unit) -> Unit\n) {','    scan: ((String) -> Unit) -> Unit,\n    onMenu: () -> Unit = {}\n) {',1).replace('GlobalHeader("Categorii")','GlobalHeader("Categorii", onMenu=onMenu)',1);s=s[:idx]+part
s=s.replace('                    scan = scan\n                )','                    scan = scan,\n                    onMenu = { menuOpen=true }\n                )',1)
s=s.replace('                    scan = scan\n                )','                    scan = scan,\n                    onMenu = { menuOpen=true }\n                )',1)
anchor='    Scaffold(\n        containerColor = Color(0xFFF6F7F9),'
s=rep(s,anchor,'''    if(menuOpen){
        AutoIdMenu(api=api,onClose={menuOpen=false},onOpen={url->menuOpen=false;openUrl(url)})
    }

'''+anchor,'menu overlay')
s += r'''

@Composable
fun AutoIdMenu(api:AutoIdApi,onClose:()->Unit,onOpen:(String)->Unit){
    var items by remember{mutableStateOf<List<NavItem>>(emptyList())}
    LaunchedEffect(Unit){runCatching{withContext(Dispatchers.IO){api.navigation()}}.onSuccess{items=it}}
    androidx.compose.ui.window.Dialog(onDismissRequest=onClose){
        Surface(shape=RoundedCornerShape(20.dp),color=Color.White,modifier=Modifier.fillMaxWidth().heightIn(max=650.dp)){
            Column(Modifier.padding(18.dp)){
                Row(verticalAlignment=Alignment.CenterVertically){Text("Meniu AutoID",fontSize=22.sp,fontWeight=FontWeight.ExtraBold,modifier=Modifier.weight(1f));IconButton(onClick=onClose){Icon(Icons.Default.Close,"Închide")}}
                LazyColumn{items(items){i->MenuRow(i,0,onOpen)}}
            }
        }
    }
}

@Composable private fun MenuRow(i:NavItem,depth:Int,onOpen:(String)->Unit){
    Column{Row(Modifier.fillMaxWidth().clickable{if(i.url.isNotBlank())onOpen(i.url)}.padding(start=(depth*14).dp,top=10.dp,bottom=10.dp),verticalAlignment=Alignment.CenterVertically){
        Text(i.title,modifier=Modifier.weight(1f),fontWeight=if(depth==0)FontWeight.Bold else FontWeight.Medium);Icon(Icons.Default.ChevronRight,null,modifier=Modifier.size(18.dp))
    }; i.children.take(12).forEach{MenuRow(it,depth+1,onOpen)}}
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NativeAiChatScreen(api:AutoIdApi,productId:Long?,onBack:()->Unit){
    var input by remember{mutableStateOf("")}; var busy by remember{mutableStateOf(false)}
    var messages by remember{mutableStateOf(listOf(AiMessage(false,"Salut! Sunt asistentul AutoID AI. Cu ce te pot ajuta?")))}; val scope=rememberCoroutineScope()
    fun send(){val q=input.trim();if(q.isBlank()||busy)return; input="";messages=messages+AiMessage(true,q);busy=true;scope.launch{val ans=runCatching{withContext(Dispatchers.IO){api.aiChat(q,productId)}}.getOrElse{"Nu pot contacta momentan asistentul AutoID: ${it.message}"};messages=messages+AiMessage(false,ans);busy=false}}
    Scaffold(topBar={CenterAlignedTopAppBar(title={Text("AutoID AI")},navigationIcon={IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")}})},bottomBar={Surface(shadowElevation=8.dp){Row(Modifier.fillMaxWidth().navigationBarsPadding().padding(10.dp),verticalAlignment=Alignment.CenterVertically){OutlinedTextField(input,{input=it},modifier=Modifier.weight(1f),placeholder={Text("Scrie întrebarea ta aici…")},maxLines=4);Spacer(Modifier.width(8.dp));IconButton(onClick={send()},enabled=!busy){Icon(Icons.Default.Send,"Trimite",tint=AutoIdOrange)}}}}){pad->
        LazyColumn(Modifier.padding(pad).fillMaxSize().padding(12.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){items(messages){m->Row(Modifier.fillMaxWidth(),horizontalArrangement=if(m.fromUser)Arrangement.End else Arrangement.Start){Surface(color=if(m.fromUser)AutoIdOrange else Color.White,shape=RoundedCornerShape(16.dp),modifier=Modifier.widthIn(max=320.dp)){Text(m.text,color=if(m.fromUser)Color.White else Color(0xFF101828),modifier=Modifier.padding(12.dp))}}};if(busy)item{LinearProgressIndicator(Modifier.fillMaxWidth())}}
    }
}
'''
main.write_text(s)
pf=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/ProductFamilyScreen.kt'; s=pf.read_text()
s=s.replace('fontSize = 13.sp, textDecoration','fontSize = 20.sp, fontWeight = FontWeight.ExtraBold, textDecoration',1)
s=s.replace('if ((product.stockAutoId ?: 0) > 0) Text("${product.stockAutoId} în stoc. Livrare rapidă", color = FamilyGreen, fontWeight = FontWeight.Bold)\n        if ((product.stockDistributor ?: 0) > 0) Text("${product.stockDistributor} stoc producător. Livrare în 5–7 zile", color = FamilyMuted, fontSize = 12.sp)','''if ((product.stockAutoId ?: 0) > 0 || (product.stockDistributor ?: 0) > 0) {
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                if ((product.stockAutoId ?: 0) > 0) Text("${product.stockAutoId} în stoc", color = FamilyGreen, fontWeight = FontWeight.Bold)
                if ((product.stockAutoId ?: 0) > 0 && (product.stockDistributor ?: 0) > 0) Text("·", color = FamilyMuted)
                if ((product.stockDistributor ?: 0) > 0) Text("${product.stockDistributor} livrare în 5–7 zile", color = FamilyMuted, fontSize = 12.sp)
            }
        }''')
pf.write_text(s)
b=ROOT/'android-v0.1/app/build.gradle.kts'; s=b.read_text().replace('versionCode = 5','versionCode = 6').replace('versionName = "0.5.0"','versionName = "0.6.0"'); b.write_text(s)
print('v0.6 patch applied')
