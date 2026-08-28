from pathlib import Path
import base64, zlib

ROOT = Path('.')
APP = ROOT / 'android-v0.1/app'

# Native v1.0 screens are stored as a source template so v0.5-v0.8 migrations remain reproducible.
src = (ROOT / 'ci/v100/V100Screens.kt').read_text()
src = src.replace('import androidx.compose.ui.clip.clip', 'import androidx.compose.ui.draw.clip')
out = APP / 'src/main/java/ro/autoid/app/V100Screens.kt'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(src)

# Replace the v0.8 bridge with the validated v1.0 server bridge.
bridge = zlib.decompress(base64.b64decode((ROOT / 'ci/v100/bridge_v100.b64').read_text().strip())).decode()
bridge_path = ROOT / 'wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php'
bridge_path.parent.mkdir(parents=True, exist_ok=True)
bridge_path.write_text(bridge)

# Product model: append v1-only fields to preserve every pre-v1 positional constructor.
p = APP / 'src/main/java/ro/autoid/app/data/Models.kt'
s = p.read_text()
needle = '    val attributes: List<ProductAttribute> = emptyList()\n)'
replacement = '''    val attributes: List<ProductAttribute> = emptyList(),\n    val productType: String = "simple",\n    val brandLogoUrl: String? = null,\n    val groupedStockDistributor: Int? = null,\n    val msrpEuroValue: Double = 0.0,\n    val autoIdEuroValue: Double = 0.0\n)'''
if needle not in s:
    raise SystemExit('Models.kt Product anchor not found')
s = s.replace(needle, replacement, 1)
s += '''\n\ndata class FacetItem(val id:Long,val name:String,val slug:String="")\ndata class CatalogFacets(val minPrice:Double,val maxPrice:Double,val brands:List<FacetItem>,val models:List<FacetItem>,val subcategories:List<ProductCategory>)\ndata class HomeV100Data(val sections:List<HomeSection>,val recommended:List<Product>,val offers:List<Product>,val categories:List<ProductCategory>)\n'''
p.write_text(s)

# API additions and v1 product fields.
p = APP / 'src/main/java/ro/autoid/app/data/AutoIdApi.kt'
s = p.read_text()
home_anchor = '''    fun homeSections():List<HomeSection>{\n        val a=JSONObject(get("$MOBILE/home")).optJSONArray("sections")?:JSONArray()\n        return (0 until a.length()).mapNotNull{i->\n            val o=a.optJSONObject(i)?:return@mapNotNull null\n            val c=o.optJSONObject("category")?.let(::category)?:return@mapNotNull null\n            val p=o.optJSONArray("products")?:JSONArray()\n            HomeSection(c,(0 until p.length()).mapNotNull{j->p.optJSONObject(j)?.let(::product)},o.optInt("total_grouped"))\n        }\n    }\n'''
api_extra = '''\n    fun homeData():HomeV100Data{\n        val root=JSONObject(get("$MOBILE/home"))\n        fun ps(key:String):List<Product>{val a=root.optJSONArray(key)?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::product)}}\n        val sa=root.optJSONArray("sections")?:JSONArray()\n        val sections=(0 until sa.length()).mapNotNull{i->val o=sa.optJSONObject(i)?:return@mapNotNull null;val c=o.optJSONObject("category")?.let(::category)?:return@mapNotNull null;val a=o.optJSONArray("products")?:JSONArray();HomeSection(c,(0 until a.length()).mapNotNull{j->a.optJSONObject(j)?.let(::product)},o.optInt("total_grouped"))}\n        val ca=root.optJSONArray("categories")?:JSONArray();val cats=(0 until ca.length()).mapNotNull{ca.optJSONObject(it)?.let(::category)}\n        return HomeV100Data(sections,ps("recommended"),ps("offers"),cats)\n    }\n\n    fun catalogProducts(search:String="",category:Long?=null,page:Int=1,sort:String="stock_autoid",brand:Long?=null,model:Long?=null,minPrice:Double?=null,maxPrice:Double?=null):List<Product>{\n        val q=mutableListOf("per_page=20","page=$page","orderby=${enc(sort)}")\n        if(search.isNotBlank())q+="search=${enc(search)}";category?.takeIf{it>0}?.let{q+="category=$it"};brand?.takeIf{it>0}?.let{q+="brand=$it"};model?.takeIf{it>0}?.let{q+="model=$it"};minPrice?.takeIf{it>0}?.let{q+="min_price=$it"};maxPrice?.takeIf{it>0}?.let{q+="max_price=$it"}\n        val a=JSONObject(get("$MOBILE/products?${q.joinToString("&")}")).optJSONArray("products")?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::product)}\n    }\n\n    fun catalogFacets(category:Long?=null):CatalogFacets{\n        val root=JSONObject(get("$MOBILE/catalog/facets"+(category?.takeIf{it>0}?.let{"?category=$it"}?:"")))\n        fun fs(key:String):List<FacetItem>{val a=root.optJSONArray(key)?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let{FacetItem(it.optLong("id"),html(it.optString("name")),it.optString("slug"))}}}\n        val pr=root.optJSONObject("price")?:JSONObject();val sc=root.optJSONArray("subcategories")?:JSONArray()\n        return CatalogFacets(pr.optDouble("min",0.0),pr.optDouble("max",0.0),fs("brands"),fs("models"),(0 until sc.length()).mapNotNull{sc.optJSONObject(it)?.let(::category)})\n    }\n\n    fun sendRfq(name:String,email:String,company:String,phone:String,message:String,lines:List<CartLine>):Boolean{val a=JSONArray();lines.forEach{a.put(JSONObject().put("id",it.product.id).put("qty",it.quantity))};val b=JSONObject().put("name",name).put("email",email).put("company",company).put("phone",phone).put("message",message).put("products",a);return JSONObject(post("$MOBILE/rfq",b.toString())).optBoolean("sent")}\n    fun requestConsultation(name:String,email:String,company:String,phone:String,message:String):Boolean{val b=JSONObject().put("name",name).put("email",email).put("company",company).put("phone",phone).put("message",message);return JSONObject(post("$MOBILE/consultation/request",b.toString())).optBoolean("sent")}\n'''
if home_anchor not in s:
    raise SystemExit('AutoIdApi home anchor not found')
s = s.replace(home_anchor, home_anchor + api_extra, 1)
# Add fields to the Product constructor by named args, which keeps order-independent safety.
s = s.replace('category=html(o.optString("category")),brand=html(o.optString("brand")),model=', 'category=html(o.optString("category")),brand=html(o.optString("brand")),model=')
old_tail = 'supportQuery=o.optString("support_query",o.optString("sku")),attributes=(0 until attrs.length()).mapNotNull{i->attrs.optJSONObject(i)?.let{a->val vals=a.optJSONArray("values")?:JSONArray();ProductAttribute(html(a.optString("name")),(0 until vals.length()).map{vals.optString(it)})}})'
new_tail = 'supportQuery=o.optString("support_query",o.optString("sku")),attributes=(0 until attrs.length()).mapNotNull{i->attrs.optJSONObject(i)?.let{a->val vals=a.optJSONArray("values")?:JSONArray();ProductAttribute(html(a.optString("name")),(0 until vals.length()).map{vals.optString(it)})}},productType=o.optString("product_type","simple"),brandLogoUrl=o.optString("brand_logo").ifBlank{null},groupedStockDistributor=o.optInt("grouped_stock_distributor").takeIf{o.has("grouped_stock_distributor")&&!o.isNull("grouped_stock_distributor")},msrpEuroValue=o.optDouble("pret_lista",0.0),autoIdEuroValue=o.optDouble("pret_autoid_euro",0.0))'
if old_tail not in s:
    raise SystemExit('AutoIdApi Product tail anchor not found')
s = s.replace(old_tail, new_tail, 1)
s = s.replace('AutoID-Android/0.8.0', 'AutoID-Android/1.0.0')
p.write_text(s)

# Route the Activity to v1 without deleting old stable screens.
p = APP / 'src/main/java/ro/autoid/app/MainActivity.kt'
s = p.read_text()
old = 'setContent { AutoIdTheme { AutoIdApp(api, session, commerce, ::scan, ::openUrl) } }'
if old not in s:
    raise SystemExit('MainActivity setContent anchor not found')
p.write_text(s.replace(old, 'setContent { AutoIdTheme { AutoIdAppV100(api, session, commerce, ::scan) } }', 1))

# v0.8 screens remain used for checkout/account and should use the transparent asset.
for rel in ['src/main/java/ro/autoid/app/V08Screens.kt','src/main/java/ro/autoid/app/ProductFamilyScreen.kt']:
    p = APP / rel
    if p.exists(): p.write_text(p.read_text().replace('R.drawable.autoid_logo','R.drawable.autoid_logo_transparent'))

# Semantic Android version and launcher asset.
p = APP / 'build.gradle.kts'; s=p.read_text().replace('versionCode = 8','versionCode = 100').replace('versionName = "0.8.0"','versionName = "1.0.0"'); p.write_text(s)
p = APP / 'src/main/AndroidManifest.xml'; s=p.read_text().replace('@drawable/autoid_icon','@drawable/autoid_icon_v100'); p.write_text(s)

release = '''# AutoID Professional Solutions v1.0.0\n\nMajor native Android commerce/UIX release.\n\n- Loading screen with greeting and transparent AutoID branding.\n- Home rebuilt around the approved AutoID reference: smart search, promotional hero, quick categories, in-stock recommendations, offers, AI and technical consultation.\n- Built-in hamburger product navigation, favorites, notifications and header mini-cart dropdown.\n- Five-item bottom navigation: Acasă, Categorii, AI, Coș, Contul meu.\n- Native catalog grid with subcategories, price/brand/model(product_tag) filters and stock_autoid-first sorting.\n- Grouped/simple product views with dots gallery, discount chip, brand, rating, SKU, requested EUR price-meta rules, VAT-inclusive RON pricing and stock chips.\n- Multi-product RFQ and technical consultation forms.\n- Native checkout/account from v0.8 retained. AI deep backend integration remains a dedicated follow-up.\n'''
(ROOT/'RELEASE-v1.0.0.md').write_text(release)
print('Applied AutoID v1.0.0 migration')
