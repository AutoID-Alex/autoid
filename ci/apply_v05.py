from pathlib import Path
import re

ROOT = Path('.')


def must_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'v0.5 migration pattern missing: {label}')
    return text.replace(old, new, 1)

# --- WordPress bridge -------------------------------------------------------
php = ROOT / 'wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php'
s = php.read_text()
s = s.replace('Version: 0.4.0', 'Version: 0.5.0')
s = s.replace('AutoID_Mobile_Commerce_Bridge_040', 'AutoID_Mobile_Commerce_Bridge_050')
s = s.replace("'version'=>'0.4.0'", "'version'=>'0.5.0'")
s = s.replace("'|0.4'", "'|0.5'")

s = must_replace(s,
"""        $search = sanitize_text_field((string)$r->get_param('search'));
        if ($search !== '') $args['search'] = '*'.$search.'*';""",
"""        $search = sanitize_text_field((string)$r->get_param('search'));
        if ($search !== '') {
            $ids = self::fibosearch_ids($search, 250);
            if ($ids) {
                $args['include'] = $ids;
                $args['orderby'] = 'include';
            } else {
                $args['search'] = '*'.$search.'*';
            }
        }""", 'products FiboSearch')
s = s.replace("        if (in_array($orderby,['date','price','popularity','rating','title'],true)) $args['orderby'] = $orderby;",
              "        if ($search === '' && in_array($orderby,['date','price','popularity','rating','title'],true)) $args['orderby'] = $orderby;")

s = must_replace(s,
"""        $ids = array_values($data['groups'][$key] ?? []);
        $total = count($ids);
        $slice = array_slice($ids,($page-1)*$per,$per);
        $products = [];
        foreach ($slice as $id) {
            $row = wc_get_product($id);
            if ($row && $row->get_status()==='publish') $products[] = self::product_row($row,false);
        }""",
"""        $ids = array_values($data['groups'][$key] ?? []);
        $ids = array_values(array_filter($ids, function($id) {
            $row = wc_get_product($id);
            return $row && $row->get_status()==='publish' && $row->is_visible();
        }));
        usort($ids, function($a,$b) {
            $sa = (int)(get_post_meta($a,'stock_autoid',true) ?: get_post_meta($a,'_stock_autoid',true) ?: 0);
            $sb = (int)(get_post_meta($b,'stock_autoid',true) ?: get_post_meta($b,'_stock_autoid',true) ?: 0);
            if ($sa === $sb) {
                $da = (int)(get_post_meta($a,'stock_distributie',true) ?: get_post_meta($a,'stock_distributor',true) ?: 0);
                $db = (int)(get_post_meta($b,'stock_distributie',true) ?: get_post_meta($b,'stock_distributor',true) ?: 0);
                return $db <=> $da;
            }
            return $sb <=> $sa;
        });
        $total = count($ids);
        $slice = array_slice($ids,($page-1)*$per,$per);
        $products = [];
        foreach ($slice as $id) {
            $row = wc_get_product($id);
            if ($row) $products[] = self::product_row($row,false);
        }""", 'family stock priority')

search_pattern = r"    public static function search\(WP_REST_Request \$r\) \{.*?\n    \}\n\n    public static function support"
search_replacement = """    public static function search(WP_REST_Request $r) {
        $q = sanitize_text_field((string)$r->get_param('q'));
        if (mb_strlen($q)<2) return rest_ensure_response(['suggestions'=>[],'engine'=>'none']);
        $ids = self::fibosearch_ids($q, 12);
        $engine = $ids ? 'fibosearch' : 'woocommerce';
        if (!$ids) {
            $products = wc_get_products(['status'=>'publish','limit'=>12,'search'=>'*'.$q.'*']);
        } else {
            $products = [];
            foreach ($ids as $id) {
                $p = wc_get_product($id);
                if ($p && $p->get_status()==='publish' && $p->is_visible()) $products[] = $p;
            }
        }
        $suggestions = [];
        foreach ($products as $p) {
            $suggestions[] = ['type'=>'product','id'=>$p->get_id(),'label'=>$p->get_name(),'sku'=>$p->get_sku(),'image'=>self::image_url($p),'query'=>$p->get_name(),'price'=>wp_strip_all_tags(wc_price(wc_get_price_to_display($p)))];
        }
        return rest_ensure_response(['suggestions'=>$suggestions,'engine'=>$engine]);
    }

    private static function fibosearch_ids($q,$limit=50) {
        if ($q==='') return [];
        $url = add_query_arg(['action'=>'dgwt_wcas_ajax_search','s'=>$q], admin_url('admin-ajax.php'));
        $response = wp_remote_get($url,['timeout'=>4,'redirection'=>0,'headers'=>['X-AutoID-Mobile'=>'1']]);
        if (is_wp_error($response) || (int)wp_remote_retrieve_response_code($response)!==200) return [];
        $json = json_decode(wp_remote_retrieve_body($response),true);
        if (!is_array($json)) return [];
        $ids = [];
        $walk = function($value) use (&$walk,&$ids,$limit) {
            if (count($ids)>=$limit) return;
            if (is_array($value)) {
                if (isset($value['post_id']) && is_numeric($value['post_id'])) $ids[]=(int)$value['post_id'];
                elseif (isset($value['product_id']) && is_numeric($value['product_id'])) $ids[]=(int)$value['product_id'];
                elseif (isset($value['id']) && is_numeric($value['id']) && (isset($value['url']) || isset($value['title']) || isset($value['name']))) $ids[]=(int)$value['id'];
                foreach ($value as $v) $walk($v);
            }
        };
        $walk($json);
        return array_slice(array_values(array_unique(array_filter($ids))),0,$limit);
    }

    public static function support"""
s, n = re.subn(search_pattern, search_replacement, s, flags=re.S)
if n != 1:
    raise RuntimeError('v0.5 migration pattern missing: search function')

s = s.replace("get_terms(['taxonomy'=>'product_cat','hide_empty'=>true,'parent'=>0,'orderby'=>'count','order'=>'DESC'])",
              "get_terms(['taxonomy'=>'product_cat','hide_empty'=>true,'parent'=>0,'orderby'=>'menu_order','order'=>'ASC'])")
s = s.replace("self::numeric_meta($id,['_stock_autoid','stock_autoid','_autoid_stock','autoid_stock'])",
              "self::numeric_meta($id,['stock_autoid','_stock_autoid','_autoid_stock','autoid_stock'])")
s = s.replace("self::numeric_meta($id,['_stock_distributor','stock_distributor','_distributor_stock','distributor_stock'])",
              "self::numeric_meta($id,['stock_distributie','_stock_distributie','stock_distributor','_stock_distributor','_distributor_stock','distributor_stock'])")
s = s.replace("$delivery = 'Livrare rapidă din stoc AutoID'", "$delivery = $autoid.' în stoc. Livrare rapidă'")
s = s.replace("$delivery = 'Livrare estimată 5–7 zile'", "$delivery = $dist.' stoc producător. Livrare în 5–7 zile'")

s = must_replace(s,
"""        $rating = (float)$p->get_average_rating();
        $row = [""",
"""        $rating = (float)$p->get_average_rating();
        $pret_lista = get_post_meta($p->get_id(),'pret_lista',true);
        $pret_autoid_euro = get_post_meta($p->get_id(),'pret_autoid_euro',true);
        $pret_lista = is_numeric($pret_lista) ? (float)$pret_lista : 0.0;
        $pret_autoid_euro = is_numeric($pret_autoid_euro) ? (float)$pret_autoid_euro : 0.0;
        $msrp_display = $pret_lista > 0 ? number_format($pret_lista,2,',','.').' €' : '';
        $autoid_euro_display = $pret_autoid_euro > 0 ? number_format($pret_autoid_euro,2,',','.').' € ex. TVA' : '';
        $regular_incl = $regular > 0 ? wc_get_price_including_tax($p,['price'=>$regular]) : 0.0;
        $current_incl = wc_get_price_including_tax($p,['price'=>(float)$p->get_price()]);
        $regular_incl_display = $regular_incl > 0 ? wp_strip_all_tags(wc_price($regular_incl)) : '';
        $current_incl_display = $current_incl > 0 ? wp_strip_all_tags(wc_price($current_incl)) : '';
        $row = [""", 'price metadata')
s = must_replace(s,
"""            'price'=>(string)$price,'regular_price'=>$regular?(string)$regular:'','sale_price'=>$sale?(string)$sale:'',
            'price_display'=>wp_strip_all_tags(wc_price($price)),'currency'=>get_woocommerce_currency(),""",
"""            'price'=>(string)$price,'regular_price'=>$regular?(string)$regular:'','sale_price'=>$sale?(string)$sale:'',
            'price_display'=>wp_strip_all_tags(wc_price($price)),'currency'=>get_woocommerce_currency(),
            'pret_lista'=>$pret_lista?:null,'pret_lista_display'=>$msrp_display,
            'pret_autoid_euro'=>$pret_autoid_euro?:null,'pret_autoid_euro_display'=>$autoid_euro_display,
            'regular_incl_vat_display'=>$regular_incl_display,'current_incl_vat_display'=>$current_incl_display,""", 'price fields')
php.write_text(s)

# --- Android models/API -----------------------------------------------------
models = ROOT / 'android-v0.1/app/src/main/java/ro/autoid/app/data/Models.kt'
s = models.read_text()
s = must_replace(s, '    val rating: Double = 0.0,', '    val msrpEuro: String = "",\n    val autoIdEuro: String = "",\n    val regularInclVat: String = "",\n    val currentInclVat: String = "",\n    val rating: Double = 0.0,', 'Product metadata fields')
models.write_text(s)

api = ROOT / 'android-v0.1/app/src/main/java/ro/autoid/app/data/AutoIdApi.kt'
s = api.read_text()
s = must_replace(s, '    fun categories(): List<ProductCategory> {\n', '''    fun searchSuggestions(query: String): List<Product> {\n        if (query.length < 2) return emptyList()\n        val root = JSONObject(get("$MOBILE/search?q=${enc(query)}"))\n        val arr = root.optJSONArray("suggestions") ?: JSONArray()\n        return (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let { suggestion ->\n            suggestion.optLong("id").takeIf { it > 0 }?.let { id -> runCatching { product(id) }.getOrNull() }\n        } }\n    }\n\n    fun categories(): List<ProductCategory> {\n''', 'search suggestions API')
s = must_replace(s,
'            rating=o.optDouble("rating",0.0), reviewCount=o.optInt("review_count",0),',
'            msrpEuro=html(o.optString("pret_lista_display")), autoIdEuro=html(o.optString("pret_autoid_euro_display")),\n            regularInclVat=html(o.optString("regular_incl_vat_display")), currentInclVat=html(o.optString("current_incl_vat_display")),\n            rating=o.optDouble("rating",0.0), reviewCount=o.optInt("review_count",0),', 'API metadata parser')
s = s.replace('AutoID-Android/0.4.0','AutoID-Android/0.5.0')
api.write_text(s)

# --- Android UI -------------------------------------------------------------
main = ROOT / 'android-v0.1/app/src/main/java/ro/autoid/app/MainActivity.kt'
s = main.read_text()
s = must_replace(s, 'import androidx.compose.material3.*', 'import androidx.compose.material3.*\nimport androidx.compose.material.icons.Icons\nimport androidx.compose.material.icons.filled.*', 'material icons import')
s, n = re.subn(r'enum class Tab\(val label: String, val icon: String\) \{.*?\n\}', 'enum class Tab(val label: String) {\n    Home("Acasă"),\n    Categories("Categorii"),\n    Cart("Coș"),\n    Account("Cont")\n}', s, count=1, flags=re.S)
if n != 1: raise RuntimeError('v0.5 migration pattern missing: Tab enum')
s = must_replace(s, 'setContent { AutoIdTheme { AutoIdApp(api, session, commerce, ::scan, ::openUrl) } }', 'setContent { AutoIdTheme { AutoIdApp(api, session, commerce, ::scan, ::openUrl, ::openAiChat) } }', 'setContent')
s = must_replace(s, '    private fun openUrl(url: String) = startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))', '    private fun openUrl(url: String) = startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))\n    private fun openAiChat() = startActivity(Intent(this, AiWebChatActivity::class.java))', 'AI chat launcher')
s = must_replace(s, '    openUrl: (String) -> Unit\n)', '    openUrl: (String) -> Unit,\n    openAiChat: () -> Unit\n)', 'AutoIdApp signature')
s = s.replace('onSupport = { q -> search = q; selectedProduct = null; tab = Tab.Ai },','onSupport = { _ -> openAiChat() },')
s = s.replace('onAi = { search = it; tab = Tab.Ai },','onAi = { _ -> openAiChat() },')
old_icon = '''                        icon = {\n                            BadgedBox(badge = { if (count > 0) Badge { Text(count.toString()) } }) {\n                                Text(\n                                    item.icon,\n                                    fontSize = 20.sp,\n                                    fontWeight = FontWeight.Bold,\n                                    color = if (item == Tab.Ai) AutoIdOrange else LocalContentColor.current\n                                )\n                            }\n                        },'''
new_icon = '''                        icon = {\n                            BadgedBox(badge = { if (count > 0) Badge { Text(count.toString()) } }) {\n                                Icon(imageVector = when (item) {\n                                    Tab.Home -> Icons.Default.Home\n                                    Tab.Categories -> Icons.Default.Category\n                                    Tab.Cart -> Icons.Default.ShoppingCart\n                                    Tab.Account -> Icons.Default.Person\n                                }, contentDescription = item.label)\n                            }\n                        },'''
s = must_replace(s, old_icon, new_icon, 'bottom navigation icons')
s = must_replace(s, '''            }\n        }\n    ) { pad ->''', '''            }\n        },\n        floatingActionButton = {\n            FloatingActionButton(onClick = openAiChat, containerColor = AutoIdOrange, contentColor = Color.White) {\n                Icon(Icons.Default.SmartToy, contentDescription = "AutoID AI")\n            }\n        }\n    ) { pad ->''', 'AI bubble')
s = re.sub(r'\n\s*Tab\.Ai -> AiScreen\(.*?\n\s*\)', '', s, count=1, flags=re.S)
header_pattern = r'@Composable\nfun GlobalHeader\(title: String = "AutoID", cartCount: Int = 0, notificationCount: Int = 0\) \{.*?\n\}'
header = '''@Composable\nfun GlobalHeader(title: String = "AutoID", cartCount: Int = 0, notificationCount: Int = 0) {\n    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {\n        if (title == "AutoID") AsyncImage(\n            model = "https://www.autoid.ro/wp-content/uploads/Logo-AutoID.jpg",\n            contentDescription = "AutoID", modifier = Modifier.width(126.dp).height(42.dp)\n        ) else Text(title, color = Color(0xFF101828), fontSize = 24.sp, fontWeight = FontWeight.ExtraBold)\n        Spacer(Modifier.weight(1f))\n        if (notificationCount > 0) BadgedBox(badge = { Badge { Text(notificationCount.toString()) } }) { Icon(Icons.Default.Notifications, "Notificări") }\n        Spacer(Modifier.width(12.dp))\n        BadgedBox(badge = { if (cartCount > 0) Badge { Text(cartCount.toString()) } }) { Icon(Icons.Default.ShoppingCart, "Coș") }\n    }\n}'''
s, n = re.subn(header_pattern, header, s, count=1, flags=re.S)
if n != 1: raise RuntimeError('v0.5 migration pattern missing: header')
s = s.replace('FilledTonalButton(onClick = onScan, contentPadding = PaddingValues(horizontal = 14.dp)) { Text("▣") }','FilledTonalButton(onClick = onScan, contentPadding = PaddingValues(horizontal = 14.dp)) { Icon(Icons.Default.QrCodeScanner, "Scanează") }')
s = s.replace('Text("✦", fontSize = 30.sp, color = AutoIdOrange)','Icon(Icons.Default.SmartToy, contentDescription = null, tint = AutoIdOrange, modifier = Modifier.size(30.dp))')
old_card = '''                Text(p.price, color = AutoIdOrange, fontWeight = FontWeight.ExtraBold, fontSize = 17.sp)\n                Text(\n                    if (p.inStock) "● ${p.stockLabel}" else p.stockLabel,\n                    color = if (p.inStock) Color(0xFF16803A) else Color(0xFFB42318),\n                    fontSize = 11.sp\n                )\n                Row {\n                    TextButton(onClick = onFavorite) { Text(if (favorite) "♥" else "♡") }\n                    Button(onClick = onCart, enabled = p.inStock, contentPadding = PaddingValues(horizontal = 12.dp)) { Text("Adaugă") }\n                }'''
new_card = '''                if (p.msrpEuro.isNotBlank()) Text("MSRP: ${p.msrpEuro}", fontSize = 10.sp, color = Color(0xFF667085), textDecoration = androidx.compose.ui.text.style.TextDecoration.LineThrough)\n                if (p.autoIdEuro.isNotBlank()) Text("AutoID: ${p.autoIdEuro}", color = AutoIdOrange, fontWeight = FontWeight.ExtraBold, fontSize = 14.sp)\n                Text((p.currentInclVat.ifBlank { p.price }) + " incl. TVA", color = Color(0xFF101828), fontWeight = FontWeight.Bold, fontSize = 13.sp)\n                if ((p.stockAutoId ?: 0) > 0) Text("${p.stockAutoId} în stoc · Livrare rapidă", color = Color(0xFF16803A), fontSize = 10.sp, fontWeight = FontWeight.Bold)\n                else if ((p.stockDistributor ?: 0) > 0) Text("${p.stockDistributor} producător · 5–7 zile", color = Color(0xFF667085), fontSize = 10.sp)\n                else Text(p.stockLabel, color = if (p.inStock) Color(0xFF16803A) else Color(0xFFB42318), fontSize = 10.sp)\n                Row(verticalAlignment = Alignment.CenterVertically) {\n                    IconButton(onClick = onFavorite) { Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "Favorite", tint = if (favorite) AutoIdOrange else LocalContentColor.current) }\n                    Button(onClick = onCart, enabled = p.inStock, contentPadding = PaddingValues(horizontal = 12.dp)) { Icon(Icons.Default.AddShoppingCart, null); Spacer(Modifier.width(4.dp)); Text("Adaugă") }\n                }'''
s = must_replace(s, old_card, new_card, 'product cards')
main.write_text(s)

family = ROOT / 'android-v0.1/app/src/main/java/ro/autoid/app/ProductFamilyScreen.kt'
s = family.read_text()
s = must_replace(s, 'import androidx.compose.material3.*', 'import androidx.compose.material3.*\nimport androidx.compose.material.icons.Icons\nimport androidx.compose.material.icons.filled.*', 'family material icons')
s = s.replace('TextButton(onClick = onBack) { Text("‹", fontSize = 30.sp) }','IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Înapoi") }')
s = s.replace('TextButton(onClick = onFavorite) { Text(if (commerce.isFavorite(product.id)) "♥" else "♡", fontSize = 24.sp) }','IconButton(onClick = onFavorite) { Icon(if (commerce.isFavorite(product.id)) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "Favorite", tint = if (commerce.isFavorite(product.id)) AutoIdOrange else LocalContentColor.current) }')
s = s.replace('BadgedBox(badge = { if (commerce.cartCount() > 0) Badge { Text(commerce.cartCount().toString()) } }) { Text("▣", fontSize = 22.sp) }','BadgedBox(badge = { if (commerce.cartCount() > 0) Badge { Text(commerce.cartCount().toString()) } }) { Icon(Icons.Default.ShoppingCart, "Coș") }')
old_price = '''        Text(product.price, color = AutoIdOrange, fontWeight = FontWeight.ExtraBold, fontSize = 25.sp)\n        Text(\n            if (product.inStock) "● ${product.stockLabel}" else product.stockLabel,\n            color = if (product.inStock) FamilyGreen else Color(0xFFB42318),\n            fontWeight = FontWeight.Bold\n        )\n        if (product.deliveryLabel.isNotBlank()) Text(product.deliveryLabel, color = FamilyMuted, fontSize = 12.sp)'''
new_price = '''        if (product.msrpEuro.isNotBlank()) Text("MSRP: ${product.msrpEuro}", color = FamilyMuted, fontSize = 13.sp, textDecoration = androidx.compose.ui.text.style.TextDecoration.LineThrough)\n        if (product.autoIdEuro.isNotBlank()) Text("AutoID: ${product.autoIdEuro}", color = AutoIdOrange, fontWeight = FontWeight.ExtraBold, fontSize = 20.sp)\n        if (product.regularInclVat.isNotBlank() || product.currentInclVat.isNotBlank()) {\n            Text("Comandă acum", color = FamilyMuted, fontSize = 12.sp, fontWeight = FontWeight.Bold)\n            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {\n                if (product.regularInclVat.isNotBlank() && product.regularInclVat != product.currentInclVat) Text(product.regularInclVat, color = FamilyMuted, textDecoration = androidx.compose.ui.text.style.TextDecoration.LineThrough)\n                Text(product.currentInclVat.ifBlank { product.price } + " incl. TVA", color = Color(0xFF101828), fontWeight = FontWeight.ExtraBold, fontSize = 21.sp)\n            }\n        } else Text(product.price, color = AutoIdOrange, fontWeight = FontWeight.ExtraBold, fontSize = 25.sp)\n        if ((product.stockAutoId ?: 0) > 0) Text("${product.stockAutoId} în stoc. Livrare rapidă", color = FamilyGreen, fontWeight = FontWeight.Bold)\n        if ((product.stockDistributor ?: 0) > 0) Text("${product.stockDistributor} stoc producător. Livrare în 5–7 zile", color = FamilyMuted, fontSize = 12.sp)\n        if ((product.stockAutoId ?: 0) <= 0 && (product.stockDistributor ?: 0) <= 0) Text(product.stockLabel, color = if (product.inStock) FamilyGreen else Color(0xFFB42318), fontWeight = FontWeight.Bold)'''
s = must_replace(s, old_price, new_price, 'product pricing UI')
s = s.replace('Surface(color = Color(0xFFFFF1E8), shape = RoundedCornerShape(14.dp)) { Text("✦", color = AutoIdOrange, fontSize = 26.sp, modifier = Modifier.padding(12.dp)) }','Surface(color = Color(0xFFFFF1E8), shape = RoundedCornerShape(14.dp)) { Icon(Icons.Default.SmartToy, null, tint = AutoIdOrange, modifier = Modifier.padding(12.dp).size(26.dp)) }')
s = s.replace('Text("›", fontSize = 24.sp)','Icon(Icons.Default.ChevronRight, null)')
old_family_card = '''                Text(product.price, color = AutoIdOrange, fontWeight = FontWeight.ExtraBold)\n                Text(product.stockLabel, color = if (product.inStock) FamilyGreen else Color(0xFFB42318), fontSize = 10.sp)\n            }\n            if (product.inStock) FilledTonalButton(onClick = { onCart(product) }, contentPadding = PaddingValues(horizontal = 10.dp)) { Text("+") }'''
new_family_card = '''                if (product.autoIdEuro.isNotBlank()) Text("AutoID: ${product.autoIdEuro}", color = AutoIdOrange, fontWeight = FontWeight.ExtraBold, fontSize = 12.sp)\n                Text(product.currentInclVat.ifBlank { product.price } + " incl. TVA", color = Color(0xFF101828), fontWeight = FontWeight.Bold, fontSize = 12.sp)\n                if ((product.stockAutoId ?: 0) > 0) Text("${product.stockAutoId} în stoc · Livrare rapidă", color = FamilyGreen, fontSize = 10.sp, fontWeight = FontWeight.Bold)\n                else if ((product.stockDistributor ?: 0) > 0) Text("${product.stockDistributor} producător · 5–7 zile", color = FamilyMuted, fontSize = 10.sp)\n                else Text(product.stockLabel, color = if (product.inStock) FamilyGreen else Color(0xFFB42318), fontSize = 10.sp)\n            }\n            if (product.inStock) FilledTonalButton(onClick = { onCart(product) }, contentPadding = PaddingValues(horizontal = 10.dp)) { Icon(Icons.Default.AddShoppingCart, "Adaugă") }'''
s = must_replace(s, old_family_card, new_family_card, 'family cards')
family.write_text(s)

# Web-hosted AI: the APK contains only the bubble and WebView shell; assistant instructions remain on autoid.ro.
ai = ROOT / 'android-v0.1/app/src/main/java/ro/autoid/app/AiWebChatActivity.kt'
ai.write_text('''package ro.autoid.app\n\nimport android.annotation.SuppressLint\nimport android.os.Bundle\nimport android.webkit.CookieManager\nimport android.webkit.WebChromeClient\nimport android.webkit.WebView\nimport android.webkit.WebViewClient\nimport androidx.activity.ComponentActivity\nimport androidx.activity.compose.setContent\nimport androidx.activity.enableEdgeToEdge\nimport androidx.compose.foundation.layout.*\nimport androidx.compose.material.icons.Icons\nimport androidx.compose.material.icons.filled.ArrowBack\nimport androidx.compose.material3.*\nimport androidx.compose.runtime.*\nimport androidx.compose.ui.Modifier\nimport androidx.compose.ui.viewinterop.AndroidView\nimport ro.autoid.app.ui.theme.AutoIdTheme\n\nclass AiWebChatActivity : ComponentActivity() {\n    override fun onCreate(savedInstanceState: Bundle?) {\n        super.onCreate(savedInstanceState)\n        enableEdgeToEdge()\n        setContent { AutoIdTheme { AiWebChatScreen { finish() } } }\n    }\n}\n\n@SuppressLint("SetJavaScriptEnabled")\n@Composable\nprivate fun AiWebChatScreen(onBack: () -> Unit) {\n    var loading by remember { mutableStateOf(true) }\n    Scaffold(topBar = { TopAppBar(title = { Text("AutoID AI") }, navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Înapoi") } }) }) { pad ->\n        Box(Modifier.padding(pad).fillMaxSize()) {\n            AndroidView(modifier = Modifier.fillMaxSize(), factory = { context ->\n                WebView(context).apply {\n                    settings.javaScriptEnabled = true\n                    settings.domStorageEnabled = true\n                    settings.userAgentString = settings.userAgentString + " AutoID-Android/0.5.0"\n                    CookieManager.getInstance().setAcceptCookie(true)\n                    webChromeClient = WebChromeClient()\n                    webViewClient = object : WebViewClient() { override fun onPageFinished(view: WebView?, url: String?) { loading = false } }\n                    loadUrl("https://www.autoid.ro/support/?autoid_app=android")\n                }\n            })\n            if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())\n        }\n    }\n}\n''')

manifest = ROOT / 'android-v0.1/app/src/main/AndroidManifest.xml'
s = manifest.read_text()
s = must_replace(s, '        <activity android:name=".MainActivity" android:exported="true">', '        <activity android:name=".AiWebChatActivity" android:exported="false" />\n        <activity android:name=".MainActivity" android:exported="true">', 'AI Activity manifest')
manifest.write_text(s)

gradle = ROOT / 'android-v0.1/app/build.gradle.kts'
s = gradle.read_text()
s = s.replace('versionCode = 4','versionCode = 5').replace('versionName = "0.4.0"','versionName = "0.5.0"')
s = must_replace(s, '    implementation("androidx.compose.material3:material3:1.3.2")', '    implementation("androidx.compose.material3:material3:1.3.2")\n    implementation("androidx.compose.material:material-icons-extended:1.7.8")', 'material icons dependency')
gradle.write_text(s)

print('AutoID v0.5 migration applied')
