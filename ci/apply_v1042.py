from pathlib import Path

APP=Path('android-v0.1/app')

# Extend CatalogFacets with special liquidation categories metadata.
p=APP/'src/main/java/ro/autoid/app/data/Models.kt'
s=p.read_text()
old='data class CatalogFacets(val minPrice:Double,val maxPrice:Double,val brands:List<FacetItem>,val models:List<FacetItem>,val subcategories:List<ProductCategory>)'
new='data class CatalogFacets(val minPrice:Double,val maxPrice:Double,val brands:List<FacetItem>,val models:List<FacetItem>,val subcategories:List<ProductCategory>,val liquidationCategories:List<FacetItem> = emptyList(),val specialCategory:String = "")'
if old not in s: raise SystemExit('CatalogFacets model anchor missing')
s=s.replace(old,new,1)
p.write_text(s)

# API: secondary category filter + liquidation category facets.
p=APP/'src/main/java/ro/autoid/app/data/AutoIdApi.kt'
s=p.read_text()
old_sig='fun catalogProducts(search:String="",category:Long?=null,page:Int=1,sort:String="stock_autoid",brand:Long?=null,model:Long?=null,minPrice:Double?=null,maxPrice:Double?=null):List<Product>{'
new_sig='fun catalogProducts(search:String="",category:Long?=null,page:Int=1,sort:String="stock_autoid",brand:Long?=null,model:Long?=null,minPrice:Double?=null,maxPrice:Double?=null,secondaryCategory:Long?=null):List<Product>{'
if old_sig not in s: raise SystemExit('catalogProducts signature anchor missing')
s=s.replace(old_sig,new_sig,1)
old_q='if(search.isNotBlank())q+="search=${enc(search)}";category?.takeIf{it>0}?.let{q+="category=$it"};brand?.takeIf{it>0}?.let{q+="brand=$it"};model?.takeIf{it>0}?.let{q+="model=$it"};minPrice?.takeIf{it>0}?.let{q+="min_price=$it"};maxPrice?.takeIf{it>0}?.let{q+="max_price=$it"}'
new_q='if(search.isNotBlank())q+="search=${enc(search)}";category?.takeIf{it>0}?.let{q+="category=$it"};secondaryCategory?.takeIf{it>0}?.let{q+="secondary_category=$it"};brand?.takeIf{it>0}?.let{q+="brand=$it"};model?.takeIf{it>0}?.let{q+="model=$it"};minPrice?.takeIf{it>0}?.let{q+="min_price=$it"};maxPrice?.takeIf{it>0}?.let{q+="max_price=$it"}'
if old_q not in s: raise SystemExit('catalogProducts query anchor missing')
s=s.replace(old_q,new_q,1)
old_fac='return CatalogFacets(pr.optDouble("min",0.0),pr.optDouble("max",0.0),fs("brands"),fs("models"),(0 until sc.length()).mapNotNull{sc.optJSONObject(it)?.let(::category)})'
new_fac='return CatalogFacets(pr.optDouble("min",0.0),pr.optDouble("max",0.0),fs("brands"),fs("models"),(0 until sc.length()).mapNotNull{sc.optJSONObject(it)?.let(::category)},fs("liquidation_categories"),root.optString("special_category"))'
if old_fac not in s: raise SystemExit('catalogFacets return anchor missing')
s=s.replace(old_fac,new_fac,1)
s=s.replace('AutoID-Android/1.0.4.1','AutoID-Android/1.0.4.2',1)
p.write_text(s)

# Catalog special UI + filter state.
p=APP/'src/main/java/ro/autoid/app/V100Screens.kt'
s=p.read_text()

old='''    var sort by remember(category.id) { mutableStateOf("stock_autoid") }
    var page by remember(category.id) { mutableIntStateOf(1) }
'''
new='''    var sort by remember(category.id) { mutableStateOf("stock_autoid") }
    var secondaryCategory by remember(category.id) { mutableStateOf<Long?>(null) }
    var page by remember(category.id) { mutableIntStateOf(1) }
'''
if old not in s: raise SystemExit('Catalog state anchor missing')
s=s.replace(old,new,1)

old_call='api.catalogProducts(q,category.id,page,sort,brand,model,min,max)'
new_call='api.catalogProducts(q,category.id,page,sort,brand,model,min,max,secondaryCategory)'
if old_call not in s: raise SystemExit('Catalog load call anchor missing')
s=s.replace(old_call,new_call,1)

old_effect='LaunchedEffect(category.id,brand,model,min,max,sort){load(true)}'
new_effect='LaunchedEffect(category.id,brand,model,min,max,sort,secondaryCategory){load(true)}'
if old_effect not in s: raise SystemExit('Catalog load effect anchor missing')
s=s.replace(old_effect,new_effect,1)

old_subs='''        val subs=facets?.subcategories.orEmpty()
        if(subs.isNotEmpty()){
            LazyRow(horizontalArrangement=Arrangement.spacedBy(8.dp),modifier=Modifier.padding(vertical=8.dp)){
                items(subs,key={it.id}){c->
                    AssistChip(onClick={onSubcategory(c)},label={Text(c.name)},leadingIcon={Icon(Icons.Default.ChevronRight,null)})
                }
            }
        }
'''
new_subs='''        val liquidationMode = facets?.specialCategory == "liquidation" || category.slug == "lichidari-de-stoc"
        val liquidationCats = facets?.liquidationCategories.orEmpty()
        if (liquidationMode && liquidationCats.isNotEmpty()) {
            Text(
                "Filtrează lichidările după categorie",
                fontSize = 12.sp,
                fontWeight = FontWeight.SemiBold,
                color = Muted,
                modifier = Modifier.padding(top = 8.dp, bottom = 6.dp)
            )
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                val all = listOf(FacetItem(0, "Toate", "")) + liquidationCats
                all.chunked(3).forEach { row ->
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        row.forEach { item ->
                            val selected = if (item.id == 0L) secondaryCategory == null else secondaryCategory == item.id
                            FilterChip(
                                selected = selected,
                                onClick = { secondaryCategory = item.id.takeIf { it > 0 } },
                                label = {
                                    Text(
                                        item.name,
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
            Spacer(Modifier.height(8.dp))
        } else {
            val subs=facets?.subcategories.orEmpty()
            if(subs.isNotEmpty()){
                LazyRow(horizontalArrangement=Arrangement.spacedBy(8.dp),modifier=Modifier.padding(vertical=8.dp)){
                    items(subs,key={it.id}){c->
                        AssistChip(onClick={onSubcategory(c)},label={Text(c.name)},leadingIcon={Icon(Icons.Default.ChevronRight,null)})
                    }
                }
            }
        }
'''
if old_subs not in s: raise SystemExit('Catalog subcategory UI anchor missing')
s=s.replace(old_subs,new_subs,1)

# Bump Android hotfix version.
p.write_text(s)

g=APP/'build.gradle.kts'
gs=g.read_text().replace('versionCode = 105','versionCode = 106',1).replace('versionName = "1.0.4.1"','versionName = "1.0.4.2"',1)
g.write_text(gs)

print('Applied Android v1.0.4.2 liquidation category chip grid and server-side intersection filter')
