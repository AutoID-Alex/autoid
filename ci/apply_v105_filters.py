from pathlib import Path
import re

APP=Path('android-v0.1/app')

# Facet metadata: hierarchy + counts/depth, backwards compatible through defaults.
p=APP/'src/main/java/ro/autoid/app/data/Models.kt'
s=p.read_text()
old='data class FacetItem(val id:Long,val name:String,val slug:String="")\ndata class CatalogFacets(val minPrice:Double,val maxPrice:Double,val brands:List<FacetItem>,val models:List<FacetItem>,val subcategories:List<ProductCategory>,val liquidationCategories:List<FacetItem> = emptyList(),val specialCategory:String = "")'
new='data class FacetItem(val id:Long,val name:String,val slug:String="",val count:Int=0,val parentId:Long=0,val depth:Int=0)\ndata class CatalogFacets(val minPrice:Double,val maxPrice:Double,val brands:List<FacetItem>,val models:List<FacetItem>,val subcategories:List<ProductCategory>,val liquidationCategories:List<FacetItem> = emptyList(),val specialCategory:String = "",val categoryHierarchy:List<FacetItem> = emptyList())'
if old not in s: raise SystemExit('v1.0.5 facet model anchor missing')
s=s.replace(old,new,1)
p.write_text(s)

# Parse enriched facet items and hierarchy.
p=APP/'src/main/java/ro/autoid/app/data/AutoIdApi.kt'
s=p.read_text()
old='fun fs(key:String):List<FacetItem>{val a=root.optJSONArray(key)?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let{FacetItem(it.optLong("id"),html(it.optString("name")),it.optString("slug"))}}}'
new='fun fs(key:String):List<FacetItem>{val a=root.optJSONArray(key)?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let{FacetItem(it.optLong("id"),html(it.optString("name")),it.optString("slug"),it.optInt("count",0),it.optLong("parent",0),it.optInt("depth",0))}}}'
if old not in s: raise SystemExit('v1.0.5 facet parser anchor missing')
s=s.replace(old,new,1)
old='return CatalogFacets(pr.optDouble("min",0.0),pr.optDouble("max",0.0),fs("brands"),fs("models"),(0 until sc.length()).mapNotNull{sc.optJSONObject(it)?.let(::category)},fs("liquidation_categories"),root.optString("special_category"))'
new='return CatalogFacets(pr.optDouble("min",0.0),pr.optDouble("max",0.0),fs("brands"),fs("models"),(0 until sc.length()).mapNotNull{sc.optJSONObject(it)?.let(::category)},fs("liquidation_categories"),root.optString("special_category"),fs("category_hierarchy"))'
if old not in s: raise SystemExit('v1.0.5 CatalogFacets return anchor missing')
s=s.replace(old,new,1)
s=re.sub(r'AutoID-Android/[0-9.]+','AutoID-Android/1.0.5',s)
p.write_text(s)

p=APP/'src/main/java/ro/autoid/app/V100Screens.kt'
s=p.read_text()

# Normal category subcategory chips move into the Filters sheet. Liquidation retains its special merchandising grid.
old='''        } else {\n            val subs=facets?.subcategories.orEmpty()\n            if(subs.isNotEmpty()){\n                LazyRow(horizontalArrangement=Arrangement.spacedBy(8.dp),modifier=Modifier.padding(vertical=8.dp)){\n                    items(subs,key={it.id}){c->\n                        AssistChip(onClick={onSubcategory(c)},label={Text(c.name)},leadingIcon={Icon(Icons.Default.ChevronRight,null)})\n                    }\n                }\n            }\n        }\n'''
new='''        }\n'''
if old not in s: raise SystemExit('v1.0.5 normal subcategory chip block missing')
s=s.replace(old,new,1)

# Remove the redundant standalone AI chip: help now lives inside Filters as a support bubble.
old='''        Row(horizontalArrangement=Arrangement.spacedBy(8.dp),modifier=Modifier.padding(bottom=8.dp)){\n            OutlinedButton(onClick={filters=true}){Icon(Icons.Default.Tune,null);Spacer(Modifier.width(6.dp));Text("Filtre")}\n            SortMenu(sort){sort=it}\n            AssistChip(onClick=onAi,label={Text("AI")},leadingIcon={Icon(Icons.Default.SmartToy,null)})\n        }'''
new='''        Row(horizontalArrangement=Arrangement.spacedBy(8.dp),modifier=Modifier.padding(vertical=8.dp)){\n            OutlinedButton(onClick={filters=true}){Icon(Icons.Default.Tune,null);Spacer(Modifier.width(6.dp));Text("Filtre")}\n            SortMenu(sort){sort=it}\n        }'''
if old not in s: raise SystemExit('v1.0.5 catalog actions row missing')
s=s.replace(old,new,1)

old_call='''    if(filters)FilterSheet(facets,brand,model,min,max,{b,m,mi,ma->brand=b;model=m;min=mi;max=ma;filters=false},{filters=false})\n}'''
new_call='''    if(filters) FilterSheetV105(\n        f = facets,\n        category = category,\n        selectedCategory = secondaryCategory,\n        brand = brand,\n        model = model,\n        min = min,\n        max = max,\n        onApply = { c,b,m,mi,ma ->\n            secondaryCategory=c;brand=b;model=m;min=mi;max=ma;filters=false\n        },\n        onClear = {\n            secondaryCategory=null;brand=null;model=null;min=null;max=null;filters=false\n        },\n        onAi = { filters=false;onAi() },\n        onDismiss = { filters=false }\n    )\n}'''
if old_call not in s: raise SystemExit('v1.0.5 FilterSheet call anchor missing')
s=s.replace(old_call,new_call,1)

start=s.find('@OptIn(ExperimentalMaterial3Api::class) @Composable private fun FilterSheet(')
end=s.find('\n\nprivate fun cleanVatRangeV104',start)
if start < 0 or end < 0: raise SystemExit('v1.0.5 FilterSheet boundaries missing')
replacement=r'''@Composable
private fun FacetGridV105(
    items: List<FacetItem>,
    selected: Long?,
    onSelected: (Long?) -> Unit,
    hierarchy: Boolean = false
) {
    val rows = (listOf(FacetItem(0, "Toate")) + items).chunked(3)
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        rows.forEach { row ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                row.forEach { item ->
                    val isSelected = if (item.id == 0L) selected == null else selected == item.id
                    val prefix = if (hierarchy && item.id != 0L && item.depth > 1) "› ".repeat((item.depth - 1).coerceAtMost(2)) else ""
                    FilterChip(
                        selected = isSelected,
                        onClick = { onSelected(item.id.takeIf { it > 0 }) },
                        label = {
                            Text(
                                prefix + item.name,
                                maxLines = 2,
                                overflow = TextOverflow.Ellipsis,
                                textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                                fontSize = 10.sp
                            )
                        },
                        modifier = Modifier.weight(1f).heightIn(min = 44.dp)
                    )
                }
                repeat(3 - row.size) { Spacer(Modifier.weight(1f)) }
            }
        }
    }
}

private fun filterLeiV105(value: Float): String =
    java.text.NumberFormat.getNumberInstance(java.util.Locale("ro", "RO")).apply {
        minimumFractionDigits = 0
        maximumFractionDigits = 0
    }.format(value)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun FilterSheetV105(
    f: CatalogFacets?,
    category: ProductCategory,
    selectedCategory: Long?,
    brand: Long?,
    model: Long?,
    min: Double?,
    max: Double?,
    onApply: (Long?, Long?, Long?, Double?, Double?) -> Unit,
    onClear: () -> Unit,
    onAi: () -> Unit,
    onDismiss: () -> Unit
) {
    var c by remember(category.id, selectedCategory) { mutableStateOf(selectedCategory) }
    var b by remember(category.id, brand) { mutableStateOf(brand) }
    var m by remember(category.id, model) { mutableStateOf(model) }

    val facetMin = (f?.minPrice ?: 0.0).coerceAtLeast(0.0).toFloat()
    val facetMaxRaw = (f?.maxPrice ?: 0.0).coerceAtLeast(0.0).toFloat()
    val sliderMax = if (facetMaxRaw > facetMin) facetMaxRaw else facetMin + 1f
    val initialStart = (min?.toFloat() ?: facetMin).coerceIn(facetMin, sliderMax)
    val initialEnd = (max?.toFloat() ?: facetMaxRaw.takeIf { it > facetMin } ?: sliderMax).coerceIn(initialStart, sliderMax)
    var priceRange by remember(category.id, f?.minPrice, f?.maxPrice, min, max) {
        mutableStateOf(initialStart..initialEnd)
    }

    val categoryItems = f?.categoryHierarchy.orEmpty().ifEmpty {
        f?.subcategories.orEmpty().map { FacetItem(it.id, it.name, it.slug, it.count, it.parent, 1) }
    }
    val priceAvailable = f != null && facetMaxRaw > facetMin

    ModalBottomSheet(onDismissRequest = onDismiss) {
        LazyColumn(
            Modifier.fillMaxWidth().padding(horizontal = 18.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            contentPadding = PaddingValues(bottom = 40.dp)
        ) {
            item {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Filtre", fontSize = 24.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.weight(1f))
                    Surface(
                        onClick = onAi,
                        shape = RoundedCornerShape(18.dp),
                        color = Color(0xFFFFF4EC),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFFD7BF))
                    ) {
                        Row(
                            Modifier.padding(horizontal = 10.dp, vertical = 7.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(Icons.Default.SmartToy, null, tint = AutoIdOrange, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(6.dp))
                            Column {
                                Text("Ai nevoie de ajutor?", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Ink)
                                Text("Întreabă AutoID AI", fontSize = 10.sp, color = AutoIdOrange, fontWeight = FontWeight.SemiBold)
                            }
                        }
                    }
                }
            }

            if (categoryItems.isNotEmpty()) item {
                Text("Subcategorie", fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(7.dp))
                FacetGridV105(categoryItems, c, { c = it }, hierarchy = true)
            }

            item {
                Text("Preț", fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(2.dp))
                Text(
                    if (priceAvailable) "${filterLeiV105(priceRange.start)} – ${filterLeiV105(priceRange.endInclusive)} lei"
                    else "Interval de preț indisponibil",
                    fontSize = 12.sp,
                    color = Muted
                )
                if (priceAvailable) {
                    RangeSlider(
                        value = priceRange,
                        onValueChange = { priceRange = it },
                        valueRange = facetMin..sliderMax,
                        modifier = Modifier.fillMaxWidth()
                    )
                    Row(Modifier.fillMaxWidth()) {
                        Text("Min. ${filterLeiV105(facetMin)} lei", fontSize = 10.sp, color = Muted)
                        Spacer(Modifier.weight(1f))
                        Text("Max. ${filterLeiV105(facetMaxRaw)} lei", fontSize = 10.sp, color = Muted)
                    }
                }
            }

            if (f?.brands.orEmpty().isNotEmpty()) item {
                Text("Brand", fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(7.dp))
                FacetGridV105(f?.brands.orEmpty(), b, { b = it })
            }

            if (f?.models.orEmpty().isNotEmpty()) item {
                Text("Model", fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(7.dp))
                FacetGridV105(f?.models.orEmpty().take(90), m, { m = it })
            }

            item {
                Button(
                    onClick = {
                        val appliedMin = if (priceAvailable && priceRange.start > facetMin + 0.5f) priceRange.start.toDouble() else null
                        val appliedMax = if (priceAvailable && priceRange.endInclusive < facetMaxRaw - 0.5f) priceRange.endInclusive.toDouble() else null
                        onApply(c, b, m, appliedMin, appliedMax)
                    },
                    modifier = Modifier.fillMaxWidth().height(52.dp)
                ) { Text("Aplică filtrele") }
                TextButton(onClick = onClear, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.FilterAltOff, null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(6.dp))
                    Text("Șterge filtrele")
                }
            }
        }
    }
}'''
s=s[:start]+replacement+s[end:]
p.write_text(s)

# App identity.
g=APP/'build.gradle.kts'
gs=g.read_text()
if 'versionCode = 10700' not in gs or 'versionName = "1.0.4.3"' not in gs:
    raise SystemExit('v1.0.5 version anchor missing')
gs=gs.replace('versionCode = 10700','versionCode = 10800',1).replace('versionName = "1.0.4.3"','versionName = "1.0.5"',1)
g.write_text(gs)

print('Applied Android v1.0.5 catalog filter UX: hierarchy, RangeSlider, facet grids and AutoID AI help bubble')
