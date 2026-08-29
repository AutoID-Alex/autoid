from pathlib import Path
import re

APP=Path('android-v0.1/app')

# Product carries its full WooCommerce category memberships so liquidation filters
# can still be built in-app if an older Bridge response omits liquidation facets.
p=APP/'src/main/java/ro/autoid/app/data/Models.kt'
s=p.read_text()
old='''    val regularInclVatDisplay: String = "",\n    val saleInclVatDisplay: String = ""\n)'''
new='''    val regularInclVatDisplay: String = "",\n    val saleInclVatDisplay: String = "",\n    val categories: List<FacetItem> = emptyList()\n)'''
if old not in s:
    raise SystemExit('Product category-membership model anchor missing')
s=s.replace(old,new,1)
p.write_text(s)

# Parse product category memberships and make User-Agent version deterministic.
p=APP/'src/main/java/ro/autoid/app/data/AutoIdApi.kt'
s=p.read_text()
old='''        val attrs=o.optJSONArray("attributes")?:JSONArray();val images=o.optJSONArray("images")?:JSONArray();val children=o.optJSONArray("grouped_child_ids")?:JSONArray()'''
new='''        val attrs=o.optJSONArray("attributes")?:JSONArray();val images=o.optJSONArray("images")?:JSONArray();val children=o.optJSONArray("grouped_child_ids")?:JSONArray();val cats=o.optJSONArray("categories")?:JSONArray()'''
if old not in s:
    raise SystemExit('Product parser array anchor missing')
s=s.replace(old,new,1)
old_tail='''regularInclVatDisplay=html(o.optString("regular_price_incl_vat_display")),saleInclVatDisplay=html(o.optString("sale_price_incl_vat_display")))'''
new_tail='''regularInclVatDisplay=html(o.optString("regular_price_incl_vat_display")),saleInclVatDisplay=html(o.optString("sale_price_incl_vat_display")),categories=(0 until cats.length()).mapNotNull{i->cats.optJSONObject(i)?.let{c->FacetItem(c.optLong("id"),html(c.optString("name")),c.optString("slug"))}})'''
if old_tail not in s:
    raise SystemExit('Product parser tail anchor missing')
s=s.replace(old_tail,new_tail,1)
s=re.sub(r'AutoID-Android/[0-9.]+','AutoID-Android/1.0.4.3',s)
p.write_text(s)

p=APP/'src/main/java/ro/autoid/app/V100Screens.kt'
s=p.read_text()

# Grouped cards do not need a fake quantity-height spacer. The weighted spacer above
# already pins both action rows consistently and avoids clipping on two-line price ranges.
old='''            if (!isGrouped(p)) {\n                LoopQuantityV104(qty, { if (qty > 1) qty-- }, { if (qty < 99) qty++ })\n                Spacer(Modifier.height(3.dp))\n            } else {\n                Spacer(Modifier.height(31.dp))\n            }'''
new='''            if (!isGrouped(p)) {\n                LoopQuantityV104(qty, { if (qty > 1) qty-- }, { if (qty < 99) qty++ })\n                Spacer(Modifier.height(3.dp))\n            }'''
count=s.count(old)
if count != 2:
    raise SystemExit(f'Expected 2 grouped spacer blocks, found {count}')
s=s.replace(old,new)

# Explicit label color; do not depend on Surface contentColor propagation.
old='''                fontWeight = FontWeight.SemiBold,\n                maxLines = 1,\n                textAlign = androidx.compose.ui.text.style.TextAlign.Center'''
new='''                fontWeight = FontWeight.SemiBold,\n                color = fg,\n                maxLines = 1,\n                textAlign = androidx.compose.ui.text.style.TextAlign.Center'''
if old not in s:
    raise SystemExit('LoopActionButton text style anchor missing')
s=s.replace(old,new,1)
s=s.replace('Modifier.fillMaxSize().padding(horizontal = 8.dp, vertical = 6.dp)','Modifier.fillMaxSize().padding(horizontal = 6.dp, vertical = 4.dp)',1)

# Liquidation detection must work even when the Bridge has not yet been upgraded.
old='''        val liquidationMode = facets?.specialCategory == "liquidation" || category.slug == "lichidari-de-stoc"\n        val liquidationCats = facets?.liquidationCategories.orEmpty()\n        if (liquidationMode && liquidationCats.isNotEmpty()) {'''
new='''        val liquidationMode =\n            facets?.specialCategory == "liquidation" ||\n            category.slug.equals("lichidari-de-stoc", ignoreCase = true) ||\n            category.name.equals("Lichidări de stoc", ignoreCase = true) ||\n            category.name.equals("Lichidari de stoc", ignoreCase = true)\n        val serverLiquidationCats = facets?.liquidationCategories.orEmpty()\n        val derivedLiquidationCats = products\n            .flatMap { it.categories }\n            .filterNot {\n                it.id == category.id ||\n                it.slug.equals("lichidari-de-stoc", ignoreCase = true) ||\n                it.name.equals("Lichidări de stoc", ignoreCase = true) ||\n                it.name.equals("Lichidari de stoc", ignoreCase = true)\n            }\n            .distinctBy { it.id }\n            .sortedBy { it.name.lowercase() }\n        val liquidationCats = (serverLiquidationCats + derivedLiquidationCats).distinctBy { it.id }\n        if (liquidationMode) {'''
if old not in s:
    raise SystemExit('Liquidation grid render anchor missing')
s=s.replace(old,new,1)

# If an older Bridge ignores secondary_category, still make the visible result correct.
old='''        val rows=runCatching{withContext(Dispatchers.IO){api.catalogProducts(q,category.id,page,sort,brand,model,min,max,secondaryCategory)}}\n            .onFailure{error=it.message}.getOrDefault(emptyList())\n        products=if(reset)rows else products+rows'''
new='''        val rows=runCatching{withContext(Dispatchers.IO){api.catalogProducts(q,category.id,page,sort,brand,model,min,max,secondaryCategory)}}\n            .onFailure{error=it.message}.getOrDefault(emptyList())\n        val liquidationModeLocal =\n            category.slug.equals("lichidari-de-stoc", ignoreCase = true) ||\n            category.name.equals("Lichidări de stoc", ignoreCase = true) ||\n            category.name.equals("Lichidari de stoc", ignoreCase = true)\n        val visibleRows = if (liquidationModeLocal && secondaryCategory != null) {\n            rows.filter { product -> product.categories.any { it.id == secondaryCategory } }\n        } else rows\n        products=if(reset)visibleRows else products+visibleRows'''
if old not in s:
    raise SystemExit('Catalog load rows anchor missing')
s=s.replace(old,new,1)

p.write_text(s)

# Unambiguous on-device build identity.
g=APP/'build.gradle.kts'
gs=g.read_text()
if 'versionCode = 10600' not in gs or 'versionName = "1.0.4.2"' not in gs:
    raise SystemExit('v1.0.4.2 Android version anchor missing')
gs=gs.replace('versionCode = 10600','versionCode = 10700',1).replace('versionName = "1.0.4.2"','versionName = "1.0.4.3"',1)
g.write_text(gs)

print('Applied v1.0.4.3: robust liquidation grid fallback, grouped button unclipping, explicit labels, UA and versionCode 10700')
