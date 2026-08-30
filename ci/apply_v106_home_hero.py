from pathlib import Path
import re

APP=Path('android-v0.1/app')

p=APP/'src/main/java/ro/autoid/app/data/Models.kt'
s=p.read_text()
old='data class HomeV100Data(val sections:List<HomeSection>,val recommended:List<Product>,val offers:List<Product>,val categories:List<ProductCategory>)'
new='data class HomeV100Data(val sections:List<HomeSection>,val recommended:List<Product>,val offers:List<Product>,val categories:List<ProductCategory>,val liquidationCategory:ProductCategory? = null)'
if old not in s: raise SystemExit('HomeV100Data anchor missing')
s=s.replace(old,new,1)
old='''data class HeroSlideV103(\n    val id: String,\n    val title: String,\n    val description: String,\n    val imageUrl: String? = null,\n    val primaryLabel: String = "",\n    val primaryType: String = "",\n    val primaryTargetId: Long = 0,\n    val secondaryLabel: String = "",\n    val secondaryType: String = "",\n    val secondaryTargetId: Long = 0\n)'''
new='''data class HeroSlideV103(\n    val id: String,\n    val title: String,\n    val description: String,\n    val imageUrl: String? = null,\n    val primaryLabel: String = "",\n    val primaryType: String = "",\n    val primaryTargetId: Long = 0,\n    val secondaryLabel: String = "",\n    val secondaryType: String = "",\n    val secondaryTargetId: Long = 0,\n    val eyebrow: String = "",\n    val background: String = "#229ff2",\n    val intervalMs: Long = 5500\n)'''
if old not in s: raise SystemExit('HeroSlideV103 model anchor missing')
s=s.replace(old,new,1)
p.write_text(s)

p=APP/'src/main/java/ro/autoid/app/data/AutoIdApi.kt'
s=p.read_text()
old='''                secondaryLabel=html(o.optString("secondary_label")),\n                secondaryType=o.optString("secondary_type"),\n                secondaryTargetId=o.optLong("secondary_target_id",0)\n            )'''
new='''                secondaryLabel=html(o.optString("secondary_label")),\n                secondaryType=o.optString("secondary_type"),\n                secondaryTargetId=o.optLong("secondary_target_id",0),\n                eyebrow=html(o.optString("eyebrow")),\n                background=o.optString("background","#229ff2"),\n                intervalMs=o.optLong("interval_ms",5500).coerceIn(2500,20000)\n            )'''
if old not in s: raise SystemExit('hero parser anchor missing')
s=s.replace(old,new,1)
old='''        val ca=root.optJSONArray("categories")?:JSONArray();val cats=(0 until ca.length()).mapNotNull{ca.optJSONObject(it)?.let(::category)}\n        return HomeV100Data(sections,ps("recommended"),ps("offers"),cats)'''
new='''        val ca=root.optJSONArray("categories")?:JSONArray();val cats=(0 until ca.length()).mapNotNull{ca.optJSONObject(it)?.let(::category)}\n        val liquidation=root.optJSONObject("liquidation_category")?.let(::category)\n        return HomeV100Data(sections,ps("recommended"),ps("offers"),cats,liquidation)'''
if old not in s: raise SystemExit('homeData parser anchor missing')
s=s.replace(old,new,1)
s=re.sub(r'AutoID-Android/[0-9.]+','AutoID-Android/1.0.6',s)
p.write_text(s)

p=APP/'src/main/java/ro/autoid/app/V100Screens.kt'
s=p.read_text()
old='''@Composable private fun HomeHeader(commerce:CommerceStore,onMenu:()->Unit,onFav:()->Unit,onNotif:()->Unit,onCart:()->Unit,mini:Boolean,onMini:(Boolean)->Unit,tick:Int){Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){IconButton(onClick=onMenu){Icon(Icons.Default.Menu,"Meniu",Modifier.size(28.dp))};Spacer(Modifier.weight(1f));Image(painterResource(R.drawable.autoid_logo_transparent),"AutoID",Modifier.width(160.dp).height(54.dp),contentScale=ContentScale.Fit);Spacer(Modifier.weight(1f));IconButton(onClick=onFav){Icon(Icons.Default.FavoriteBorder,"Favorite")};IconButton(onClick=onNotif){BadgedBox(badge={Badge(containerColor=AutoIdOrange){Text("3")}}){Icon(Icons.Default.NotificationsNone,"Notificări")}};Box{IconButton(onClick={onMini(!mini)}){BadgedBox(badge={if(commerce.cartCount()>0)Badge(containerColor=AutoIdOrange){Text(commerce.cartCount().toString())}}){Icon(Icons.Default.ShoppingCart,"Coș")}};MiniCart(commerce,mini,{onMini(false)},onCart,tick)}}}'''
new='''@Composable\nprivate fun HomeHeader(\n    commerce: CommerceStore,\n    onMenu: () -> Unit,\n    onFav: () -> Unit,\n    onNotif: () -> Unit,\n    onCart: () -> Unit,\n    mini: Boolean,\n    onMini: (Boolean) -> Unit,\n    tick: Int\n) {\n    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {\n        IconButton(onClick = onMenu) { Icon(Icons.Default.Menu, "Meniu", Modifier.size(28.dp)) }\n        Spacer(Modifier.width(6.dp))\n        Image(\n            painterResource(R.drawable.autoid_logo_transparent),\n            "AutoID",\n            Modifier.width(126.dp).height(46.dp),\n            contentScale = ContentScale.Fit\n        )\n        Spacer(Modifier.weight(1f))\n        IconButton(onClick = onFav) { Icon(Icons.Default.FavoriteBorder, "Favorite") }\n        IconButton(onClick = onNotif) {\n            BadgedBox(badge = { Badge(containerColor = AutoIdOrange) { Text("3") } }) {\n                Icon(Icons.Default.NotificationsNone, "Notificări")\n            }\n        }\n        Box {\n            IconButton(onClick = { onMini(!mini) }) {\n                BadgedBox(badge = { if (commerce.cartCount() > 0) Badge(containerColor = AutoIdOrange) { Text(commerce.cartCount().toString()) } }) {\n                    Icon(Icons.Default.ShoppingCart, "Coș")\n                }\n            }\n            MiniCart(commerce, mini, { onMini(false) }, onCart, tick)\n        }\n    }\n}'''
if old not in s: raise SystemExit('HomeHeader anchor missing')
s=s.replace(old,new,1)

old='''    onNotifications: () -> Unit,\n    onFullCart: () -> Unit,\n    mini: Boolean,'''
new='''    onNotifications: () -> Unit,\n    onFullCart: () -> Unit,\n    onAllCategories: () -> Unit,\n    mini: Boolean,'''
if old not in s: raise SystemExit('HomeV100 signature callback anchor missing')
s=s.replace(old,new,1)
old='''                            onNotifications = { notifications = true },\n                            onFullCart = { tab = V100Tab.Cart },\n                            mini = miniCart,'''
new='''                            onNotifications = { notifications = true },\n                            onFullCart = { tab = V100Tab.Cart },\n                            onAllCategories = {\n                                tab = V100Tab.Categories\n                                category = null\n                                selected = null\n                            },\n                            mini = miniCart,'''
if old not in s: raise SystemExit('HomeV100 root call anchor missing')
s=s.replace(old,new,1)
old='''                onCategory = onCategory,\n                onProduct = onProduct,\n                onConsult = onConsult,\n                onAi = onAi'''
new='''                onCategory = onCategory,\n                onProduct = onProduct,\n                onCatalog = onAllCategories,\n                onConsult = onConsult,\n                onAi = onAi'''
if old not in s: raise SystemExit('HeroSlider Home call anchor missing')
s=s.replace(old,new,1)
old='SectionHead("În stoc AutoID", "Vezi toate") {}'
new='SectionHead("În stoc AutoID", "Vezi toate", onAllCategories)'
if old not in s: raise SystemExit('In stock See all anchor missing')
s=s.replace(old,new,1)
old='SectionHead("Lichidări de stoc", "Vezi toate") {}'
new='''SectionHead("Lichidări de stoc", "Vezi toate") {\n                val target = data?.liquidationCategory\n                    ?: data?.categories?.firstOrNull {\n                        it.slug.equals("lichidari-de-stoc", ignoreCase = true) ||\n                        it.name.equals("Lichidări de stoc", ignoreCase = true) ||\n                        it.name.equals("Lichidari de stoc", ignoreCase = true)\n                    }\n                target?.let(onCategory)\n            }'''
if old not in s: raise SystemExit('Liquidations See all anchor missing')
s=s.replace(old,new,1)

hero_start=s.find('@Composable\nprivate fun HeroSliderV103(')
hero_end=s.find('\nprivate fun runHeroActionV103(',hero_start)
if hero_start < 0 or hero_end < 0: raise SystemExit('HeroSlider boundaries missing')
hero=r'''@Composable
private fun HeroSliderV103(
    slides: List<HeroSlideV103>,
    api: AutoIdApi,
    fallbackProduct: Product?,
    onCategory: (ProductCategory) -> Unit,
    onProduct: (Product) -> Unit,
    onCatalog: () -> Unit,
    onConsult: () -> Unit,
    onAi: () -> Unit
) {
    val fallback = remember(fallbackProduct) {
        listOf(
            HeroSlideV103(
                id = "fallback",
                title = "Echipamente AutoID pentru afacerea ta",
                description = "Scanare, etichetare, mobilitate, RFID și soluții profesionale.",
                imageUrl = fallbackProduct?.imageUrl,
                primaryLabel = "Vezi produsele",
                primaryType = "catalog",
                background = "#117ee8",
                intervalMs = 5500
            )
        )
    }
    val rows = if (slides.isNotEmpty()) slides else fallback
    val pagerState = rememberPagerState(pageCount = { rows.size })
    val scope = rememberCoroutineScope()
    val interval = rows.firstOrNull()?.intervalMs?.coerceIn(2500, 20000) ?: 5500

    LaunchedEffect(rows.size, interval) {
        if (rows.size > 1) {
            while (true) {
                delay(interval)
                val next = (pagerState.currentPage + 1) % rows.size
                pagerState.animateScrollToPage(next)
            }
        }
    }

    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(Modifier.fillMaxWidth()) {
            HorizontalPager(state = pagerState, modifier = Modifier.fillMaxWidth()) { page ->
                val slide = rows[page]
                val bg = remember(slide.background) {
                    runCatching { Color(android.graphics.Color.parseColor(slide.background)) }
                        .getOrDefault(Color(0xFF117EE8))
                }
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(22.dp),
                    colors = CardDefaults.cardColors(containerColor = bg)
                ) {
                    Box(Modifier.fillMaxWidth().height(318.dp)) {
                        slide.imageUrl?.let { image ->
                            AsyncImage(
                                image,
                                slide.title,
                                Modifier
                                    .align(Alignment.BottomEnd)
                                    .fillMaxWidth(0.56f)
                                    .height(150.dp)
                                    .padding(end = 8.dp, bottom = 4.dp),
                                contentScale = ContentScale.Fit
                            )
                        }
                        Column(
                            Modifier.fillMaxSize().padding(start = 22.dp, top = 22.dp, end = 22.dp, bottom = 18.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            if (slide.eyebrow.isNotBlank()) {
                                Text(
                                    slide.eyebrow.uppercase(),
                                    color = Color.White.copy(alpha = .84f),
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    letterSpacing = 1.sp,
                                    maxLines = 1
                                )
                            }
                            Text(
                                slide.title,
                                color = Color.White,
                                fontSize = 27.sp,
                                fontWeight = FontWeight.ExtraBold,
                                lineHeight = 31.sp,
                                maxLines = 3,
                                overflow = TextOverflow.Ellipsis,
                                modifier = Modifier.fillMaxWidth(0.92f)
                            )
                            if (slide.description.isNotBlank()) {
                                Text(
                                    slide.description,
                                    color = Color.White.copy(alpha = .92f),
                                    fontSize = 13.sp,
                                    lineHeight = 18.sp,
                                    maxLines = 3,
                                    overflow = TextOverflow.Ellipsis,
                                    modifier = Modifier.fillMaxWidth(0.88f)
                                )
                            }
                            Spacer(Modifier.weight(1f))
                            if (slide.primaryLabel.isNotBlank() && slide.primaryType.isNotBlank()) {
                                Button(
                                    onClick = {
                                        runHeroActionV103(
                                            scope, api, slide.primaryType, slide.primaryTargetId,
                                            onCategory, onProduct, onCatalog, onConsult, onAi
                                        )
                                    },
                                    shape = RoundedCornerShape(50),
                                    colors = ButtonDefaults.buttonColors(containerColor = Color.White, contentColor = Color(0xFF101828)),
                                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 0.dp),
                                    modifier = Modifier.height(44.dp).widthIn(max = 210.dp)
                                ) {
                                    Text(slide.primaryLabel, fontSize = 11.sp, fontWeight = FontWeight.Bold, maxLines = 1)
                                }
                            }
                            Spacer(Modifier.height(if (slide.imageUrl != null) 82.dp else 4.dp))
                        }
                    }
                }
            }

            if (rows.size > 1) {
                IconButton(
                    onClick = {
                        scope.launch {
                            val prev = if (pagerState.currentPage == 0) rows.lastIndex else pagerState.currentPage - 1
                            pagerState.animateScrollToPage(prev)
                        }
                    },
                    modifier = Modifier.align(Alignment.CenterStart).padding(start = 2.dp).size(38.dp)
                ) {
                    Surface(shape = CircleShape, color = Color.Black.copy(alpha = .18f)) {
                        Icon(Icons.Default.ChevronLeft, "Slide anterior", tint = Color.White, modifier = Modifier.padding(7.dp))
                    }
                }
                IconButton(
                    onClick = {
                        scope.launch {
                            val next = (pagerState.currentPage + 1) % rows.size
                            pagerState.animateScrollToPage(next)
                        }
                    },
                    modifier = Modifier.align(Alignment.CenterEnd).padding(end = 2.dp).size(38.dp)
                ) {
                    Surface(shape = CircleShape, color = Color.Black.copy(alpha = .18f)) {
                        Icon(Icons.Default.ChevronRight, "Slide următor", tint = Color.White, modifier = Modifier.padding(7.dp))
                    }
                }
            }
        }

        if (rows.size > 1) {
            Row(
                Modifier.padding(top = 9.dp),
                horizontalArrangement = Arrangement.spacedBy(7.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                rows.indices.forEach { index ->
                    Box(
                        Modifier
                            .size(if (pagerState.currentPage == index) 9.dp else 7.dp)
                            .background(if (pagerState.currentPage == index) AutoIdOrange else Color(0xFFD0D5DD), CircleShape)
                            .clickable { scope.launch { pagerState.animateScrollToPage(index) } }
                    )
                }
            }
        }
    }
}
'''
s=s[:hero_start]+hero+s[hero_end:]

start=s.find('private fun runHeroActionV103(')
end=s.find('\n@Composable private fun QuickCategory',start)
if start < 0 or end < 0: raise SystemExit('hero action boundaries missing')
action=r'''private fun runHeroActionV103(
    scope: kotlinx.coroutines.CoroutineScope,
    api: AutoIdApi,
    type: String,
    targetId: Long,
    onCategory: (ProductCategory) -> Unit,
    onProduct: (Product) -> Unit,
    onCatalog: () -> Unit,
    onConsult: () -> Unit,
    onAi: () -> Unit
) {
    when (type.lowercase()) {
        "catalog", "shop", "categories" -> onCatalog()
        "product" -> if (targetId > 0) scope.launch {
            runCatching { withContext(Dispatchers.IO) { api.product(targetId) } }.onSuccess(onProduct)
        }
        "category" -> if (targetId > 0) scope.launch {
            runCatching { withContext(Dispatchers.IO) { api.categories().firstOrNull { it.id == targetId } } }
                .getOrNull()?.let(onCategory)
        }
        "ai", "support" -> onAi()
        "contact", "consultation", "consultanta", "consultanță" -> onConsult()
        else -> Unit
    }
}
'''
s=s[:start]+action+s[end:]
p.write_text(s)

g=APP/'build.gradle.kts'
gs=g.read_text()
if 'versionCode = 10800' not in gs or 'versionName = "1.0.5"' not in gs:
    raise SystemExit('v1.0.6 version anchor missing')
gs=gs.replace('versionCode = 10800','versionCode = 10900',1).replace('versionName = "1.0.5"','versionName = "1.0.6"',1)
g.write_text(gs)

print('Applied Android v1.0.6 header, functional Home links and site-sourced native hero UI')
