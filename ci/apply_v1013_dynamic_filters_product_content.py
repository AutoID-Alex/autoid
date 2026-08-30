from pathlib import Path

ROOT=Path('.')
MODELS=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/data/Models.kt'
API=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/data/AutoIdApi.kt'
UI=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'

s=MODELS.read_text()
s=s.replace('''    val description: String,\n    val category: String = "",''','''    val description: String,\n    val shortDescription: String = "",\n    val descriptionHtml: String = "",\n    val youtubeIds: List<String> = emptyList(),\n    val category: String = "",''',1)
s=s.replace('data class FacetItem(val id:Long,val name:String,val slug:String="",val count:Int=0,val parentId:Long=0,val depth:Int=0)',
'''data class FacetItem(val id:Long,val name:String,val slug:String="",val count:Int=0,val parentId:Long=0,val depth:Int=0,val brandId:Long=0,val categoryId:Long=0)''',1)
MODELS.write_text(s)

s=API.read_text()
old='''    fun catalogFacets(category:Long?=null):CatalogFacets{\n        val root=JSONObject(get("$MOBILE/catalog/facets"+(category?.takeIf{it>0}?.let{"?category=$it"}?:"")))\n        fun fs(key:String):List<FacetItem>{val a=root.optJSONArray(key)?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let{FacetItem(it.optLong("id"),html(it.optString("name")),it.optString("slug"),it.optInt("count",0),it.optLong("parent",0),it.optInt("depth",0))}}}\n        val pr=root.optJSONObject("price")?:JSONObject();val sc=root.optJSONArray("subcategories")?:JSONArray()\n        return CatalogFacets(pr.optDouble("min",0.0),pr.optDouble("max",0.0),fs("brands"),fs("models"),(0 until sc.length()).mapNotNull{sc.optJSONObject(it)?.let(::category)},fs("liquidation_categories"),root.optString("special_category"),fs("category_hierarchy"))\n    }'''
new='''    fun catalogFacets(category:Long?=null,secondaryCategory:Long?=null,brand:Long?=null,model:Long?=null):CatalogFacets{\n        val q=mutableListOf<String>()\n        category?.takeIf{it>0}?.let{q+="category=$it"}\n        secondaryCategory?.takeIf{it>0}?.let{q+="secondary_category=$it"}\n        brand?.takeIf{it>0}?.let{q+="brand=$it"}\n        model?.takeIf{it>0}?.let{q+="model=$it"}\n        val root=JSONObject(get("$MOBILE/catalog/facets"+(if(q.isEmpty())"" else "?"+q.joinToString("&"))))\n        fun fs(key:String):List<FacetItem>{val a=root.optJSONArray(key)?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let{FacetItem(it.optLong("id"),html(it.optString("name")),it.optString("slug"),it.optInt("count",0),it.optLong("parent",0),it.optInt("depth",0),it.optLong("brand_id",0),it.optLong("category_id",0))}}}\n        val pr=root.optJSONObject("price")?:JSONObject();val sc=root.optJSONArray("subcategories")?:JSONArray()\n        return CatalogFacets(pr.optDouble("min",0.0),pr.optDouble("max",0.0),fs("brands"),fs("models"),(0 until sc.length()).mapNotNull{sc.optJSONObject(it)?.let(::category)},fs("liquidation_categories"),root.optString("special_category"),fs("category_hierarchy"))\n    }'''
if old not in s: raise SystemExit('catalogFacets anchor missing')
s=s.replace(old,new,1)
old2='''        val attrs=o.optJSONArray("attributes")?:JSONArray();val images=o.optJSONArray("images")?:JSONArray();val children=o.optJSONArray("grouped_child_ids")?:JSONArray();val cats=o.optJSONArray("categories")?:JSONArray()'''
new2='''        val attrs=o.optJSONArray("attributes")?:JSONArray();val images=o.optJSONArray("images")?:JSONArray();val children=o.optJSONArray("grouped_child_ids")?:JSONArray();val cats=o.optJSONArray("categories")?:JSONArray();val youtube=o.optJSONArray("youtube_ids")?:JSONArray()'''
if old2 not in s: raise SystemExit('product arrays anchor missing')
s=s.replace(old2,new2,1)
needle='''description=html(o.optString("description",o.optString("short_description"))),category=html(o.optString("category"))'''
replace='''description=html(o.optString("description",o.optString("short_description"))),shortDescription=html(o.optString("short_description")),descriptionHtml=o.optString("description_html"),youtubeIds=(0 until youtube.length()).mapNotNull{youtube.optString(it).takeIf(String::isNotBlank)},category=html(o.optString("category"))'''
if needle not in s: raise SystemExit('product description parser anchor missing')
s=s.replace(needle,replace,1)
s=s.replace('AutoID-Android/1.0.12','AutoID-Android/1.0.13')
API.write_text(s)

s=UI.read_text()
for imp in ['import kotlinx.coroutines.async\n','import kotlinx.coroutines.coroutineScope\n']:
    if imp.strip() not in s:
        s=s.replace('import kotlinx.coroutines.delay\n', 'import kotlinx.coroutines.delay\n'+imp,1)
old='''    var ready by rememberSaveable { mutableStateOf(true) }'''
new='''    var ready by rememberSaveable { mutableStateOf(HomeBootstrapV104.data != null && HomeBootstrapV104.heroSlides.isNotEmpty()) }'''
if old not in s: raise SystemExit('ready anchor missing')
s=s.replace(old,new,1)
old='''    LaunchedEffect(Unit) {\n        HomeBootstrapV104.loaded = true\n        ready = true\n    }'''
new='''    LaunchedEffect(Unit) {\n        if (!ready) {\n            val started = System.currentTimeMillis()\n            coroutineScope {\n                val homeJob = async(Dispatchers.IO) { runCatching { api.homeData() }.getOrNull() }\n                val heroJob = async(Dispatchers.IO) { runCatching { api.heroSlidesV103() }.getOrNull() }\n                homeJob.await()?.let { HomeBootstrapV104.data = it }\n                heroJob.await()?.let { HomeBootstrapV104.heroSlides = it }\n            }\n            HomeBootstrapV104.loaded = true\n            val minimumWelcomeMs = 900L\n            val remaining = minimumWelcomeMs - (System.currentTimeMillis() - started)\n            if (remaining > 0) delay(remaining)\n            ready = true\n        }\n    }'''
if old not in s: raise SystemExit('bootstrap effect anchor missing')
s=s.replace(old,new,1)
old_loader='''@Composable private fun LoadingScreenV100(){Box(Modifier.fillMaxSize().background(Color.White).statusBarsPadding(),contentAlignment=Alignment.Center){Column(horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(14.dp)){Image(painterResource(R.drawable.autoid_logo_transparent),"AutoID",Modifier.width(270.dp).height(90.dp),contentScale=ContentScale.Fit);Text("Bine ai venit!",fontSize=25.sp,fontWeight=FontWeight.ExtraBold,color=Ink);Text("Soluții profesionale pentru identificare automată",color=Muted);Spacer(Modifier.height(8.dp));LinearProgressIndicator(Modifier.width(210.dp),color=AutoIdOrange,trackColor=Color(0xFFF2F4F7));Text("Se încarcă experiența AutoID...",fontSize=12.sp,color=Muted)}}}'''
new_loader='''@Composable private fun LoadingScreenV100(){Box(Modifier.fillMaxSize().background(Color.White).statusBarsPadding(),contentAlignment=Alignment.Center){Column(horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(14.dp)){Image(painterResource(R.drawable.autoid_logo_transparent),"AutoID",Modifier.width(270.dp).height(90.dp),contentScale=ContentScale.Fit);Text("Bine ai venit!",fontSize=25.sp,fontWeight=FontWeight.ExtraBold,color=Ink);Text("Soluții profesionale pentru identificare automată",color=Muted);Spacer(Modifier.height(4.dp));AutoIdPulseLoaderV112(compact=true,label="");Text("Pregătim Home-ul AutoID...",fontSize=12.sp,color=Muted)}}}'''
if old_loader not in s: raise SystemExit('loading screen anchor missing')
s=s.replace(old_loader,new_loader,1)
old='''    LaunchedEffect(category.id) {\n        facets = runCatching { withContext(Dispatchers.IO) { api.catalogFacets(category.id) } }.getOrNull()\n    }'''
new='''    LaunchedEffect(category.id, secondaryCategory, brand, model) {\n        facets = runCatching { withContext(Dispatchers.IO) { api.catalogFacets(category.id, secondaryCategory, brand, model) } }.getOrNull()\n    }'''
if old not in s: raise SystemExit('catalog facets effect anchor missing')
s=s.replace(old,new,1)
a=s.index('''        val liquidationMode =\n            facets?.specialCategory == "liquidation"''')
b=s.index('''        Row(\n            horizontalArrangement = Arrangement.spacedBy(8.dp),''',a)
s=s[:a]+s[b:]
old='''    if (filters) FilterSheetV112(\n        f = facets,'''
new='''    if (filters) FilterSheetV113(\n        api = api,\n        f = facets,'''
if old not in s: raise SystemExit('filter sheet call anchor missing')
s=s.replace(old,new,1)
old_about='''if(p.description.isNotBlank())item{Text("Despre produs",fontSize=19.sp,fontWeight=FontWeight.ExtraBold);Text(p.description,color=Color(0xFF344054),lineHeight=21.sp)}'''
new_about='''if(p.shortDescription.isNotBlank() || p.descriptionHtml.isNotBlank())item{ProductAboutV113(p)}'''
if old_about not in s: raise SystemExit('product about anchor missing')
s=s.replace(old_about,new_about,1)
UI.write_text(s)

g=GRADLE.read_text()
if 'versionCode = 11500' not in g or 'versionName = "1.0.12"' not in g: raise SystemExit('version anchors missing')
g=g.replace('versionCode = 11500','versionCode = 11600',1).replace('versionName = "1.0.12"','versionName = "1.0.13"',1)
GRADLE.write_text(g)
print('Applied v1.0.13 bootstrap, dynamic facets wiring, liquidation filter cleanup and rich product content')
