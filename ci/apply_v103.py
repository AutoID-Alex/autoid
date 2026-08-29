from pathlib import Path

APP = Path('android-v0.1/app')

# --- Models: configurable Home hero slides ---
p = APP / 'src/main/java/ro/autoid/app/data/Models.kt'
s = p.read_text()
if 'data class HeroSlideV103' not in s:
    s += '''\n\ndata class HeroSlideV103(\n    val id: String,\n    val title: String,\n    val description: String,\n    val imageUrl: String? = null,\n    val primaryLabel: String = "",\n    val primaryType: String = "",\n    val primaryTargetId: Long = 0,\n    val secondaryLabel: String = "",\n    val secondaryType: String = "",\n    val secondaryTargetId: Long = 0\n)\n'''
p.write_text(s)

# --- API: parse Bridge-managed hero slides without changing HomeV100Data compatibility ---
p = APP / 'src/main/java/ro/autoid/app/data/AutoIdApi.kt'
s = p.read_text()
if 'fun heroSlidesV103()' not in s:
    anchor = '    fun homeData():HomeV100Data{'
    if anchor not in s:
        raise SystemExit('AutoIdApi homeData anchor missing')
    fn = '''    fun heroSlidesV103():List<HeroSlideV103>{\n        val root=JSONObject(get("$MOBILE/home"))\n        val a=root.optJSONArray("hero_slides")?:JSONArray()\n        return (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{o->\n            HeroSlideV103(\n                id=o.optString("id","slide-$i"),\n                title=html(o.optString("title")),\n                description=html(o.optString("description")),\n                imageUrl=o.optString("image").ifBlank{null},\n                primaryLabel=html(o.optString("primary_label")),\n                primaryType=o.optString("primary_type"),\n                primaryTargetId=o.optLong("primary_target_id",0),\n                secondaryLabel=html(o.optString("secondary_label")),\n                secondaryType=o.optString("secondary_type"),\n                secondaryTargetId=o.optLong("secondary_target_id",0)\n            )\n        }}\n    }\n\n'''
    s = s.replace(anchor, fn + anchor, 1)
s = s.replace('AutoID-Android/1.0.2', 'AutoID-Android/1.0.3')
p.write_text(s)

# --- UI: robust mobile hero slider + exact loop pricing/CTA rules ---
p = APP / 'src/main/java/ro/autoid/app/V100Screens.kt'
s = p.read_text()

# Replace HomeV100 and the old hard-coded Hero with the Bridge-driven slider.
home_start = s.find('@Composable fun HomeV100(')
if home_start < 0:
    raise SystemExit('HomeV100 declaration missing')
hero_start = s.find('@Composable private fun Hero(', home_start)
if hero_start < 0:
    raise SystemExit('Legacy Hero declaration missing')
hero_end = s.find('@Composable private fun QuickCategory', hero_start)
if hero_end < 0:
    raise SystemExit('QuickCategory anchor missing')

home_and_hero = r'''@Composable
fun HomeV100(
    api: AutoIdApi,
    commerce: CommerceStore,
    onMenu: () -> Unit,
    onSearch: (String) -> Unit,
    onCategory: (ProductCategory) -> Unit,
    onProduct: (Product) -> Unit,
    onFavorite: (Product) -> Unit,
    onCart: (Product) -> Unit,
    onRfq: (Product) -> Unit,
    onAi: () -> Unit,
    onConsult: () -> Unit,
    onFavorites: () -> Unit,
    onNotifications: () -> Unit,
    onFullCart: () -> Unit,
    mini: Boolean,
    onMini: (Boolean) -> Unit,
    scan: ((String) -> Unit) -> Unit,
    cartTick: Int
) {
    var q by remember { mutableStateOf("") }
    var data by remember { mutableStateOf<HomeV100Data?>(null) }
    var heroSlides by remember { mutableStateOf<List<HeroSlideV103>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        runCatching {
            withContext(Dispatchers.IO) {
                val home = api.homeData()
                val slides = runCatching { api.heroSlidesV103() }.getOrDefault(emptyList())
                home to slides
            }
        }.onSuccess {
            data = it.first
            heroSlides = it.second
        }.onFailure { error = it.message }
        loading = false
    }

    LazyColumn(
        Modifier.fillMaxSize().padding(horizontal = 16.dp).statusBarsPadding(),
        verticalArrangement = Arrangement.spacedBy(20.dp),
        contentPadding = PaddingValues(bottom = 24.dp)
    ) {
        item {
            HomeHeader(commerce, onMenu, onFavorites, onNotifications, onFullCart, mini, onMini, cartTick)
            SmartSearch(api, q, { q = it }, { onSearch(it) }, scan)
        }
        item {
            HeroSliderV103(
                slides = heroSlides,
                api = api,
                fallbackProduct = data?.recommended?.firstOrNull(),
                onCategory = onCategory,
                onProduct = onProduct,
                onConsult = onConsult,
                onAi = onAi
            )
        }
        item {
            SectionHead("Categorii rapide", "Vezi toate") {}
            LazyRow(horizontalArrangement = Arrangement.spacedBy(14.dp), contentPadding = PaddingValues(vertical = 4.dp)) {
                items((data?.sections ?: emptyList()).take(8)) { section -> QuickCategory(section.category, onCategory) }
            }
        }
        item { AiCard(onAi) }
        if (loading) item { LinearProgressIndicator(Modifier.fillMaxWidth(), color = AutoIdOrange) }
        error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }

        val recommended = data?.recommended ?: emptyList()
        if (recommended.isNotEmpty()) item {
            SectionHead("În stoc AutoID", "Vezi toate") {}
            LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                items(recommended, key = { it.id }) { product ->
                    HomeCard(
                        product,
                        commerce.isFavorite(product.id),
                        { onProduct(product) },
                        { onFavorite(product) },
                        { onCart(product) },
                        { onRfq(product) }
                    )
                }
            }
        }

        val liquidations = data?.offers ?: emptyList()
        if (liquidations.isNotEmpty()) item {
            SectionHead("Lichidări de stoc", "Vezi toate") {}
            LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                items(liquidations, key = { it.id }) { product ->
                    HomeCard(
                        product,
                        commerce.isFavorite(product.id),
                        { onProduct(product) },
                        { onFavorite(product) },
                        { onCart(product) },
                        { onRfq(product) }
                    )
                }
            }
        }
        item { ConsultCard(onConsult) }
    }
}

@Composable
private fun HeroSliderV103(
    slides: List<HeroSlideV103>,
    api: AutoIdApi,
    fallbackProduct: Product?,
    onCategory: (ProductCategory) -> Unit,
    onProduct: (Product) -> Unit,
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
                primaryType = "category",
                primaryTargetId = 0,
                secondaryLabel = "Consultanță",
                secondaryType = "consultation"
            )
        )
    }
    val rows = if (slides.isNotEmpty()) slides else fallback
    val pagerState = rememberPagerState(pageCount = { rows.size })
    val scope = rememberCoroutineScope()

    LaunchedEffect(rows.size) {
        if (rows.size > 1) {
            while (true) {
                delay(5500)
                val next = (pagerState.currentPage + 1) % rows.size
                pagerState.animateScrollToPage(next)
            }
        }
    }

    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        HorizontalPager(state = pagerState, modifier = Modifier.fillMaxWidth()) { page ->
            val slide = rows[page]
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(22.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF151A23))
            ) {
                Box(Modifier.fillMaxWidth().heightIn(min = 330.dp)) {
                    slide.imageUrl?.let { image ->
                        AsyncImage(
                            image,
                            slide.title,
                            Modifier.fillMaxSize(),
                            contentScale = ContentScale.Crop,
                            alpha = 0.32f
                        )
                    }
                    Box(Modifier.fillMaxSize().background(Color(0x55101520)))
                    Column(
                        Modifier.fillMaxWidth().padding(20.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Spacer(Modifier.height(12.dp))
                        Text(
                            slide.title,
                            color = Color.White,
                            fontSize = 26.sp,
                            fontWeight = FontWeight.ExtraBold,
                            lineHeight = 30.sp,
                            maxLines = 4,
                            overflow = TextOverflow.Ellipsis
                        )
                        Text(
                            slide.description,
                            color = Color(0xFFF2F4F7),
                            fontSize = 14.sp,
                            lineHeight = 20.sp,
                            maxLines = 4,
                            overflow = TextOverflow.Ellipsis
                        )
                        Spacer(Modifier.weight(1f))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            if (slide.primaryLabel.isNotBlank()) {
                                Button(
                                    onClick = {
                                        runHeroActionV103(scope, api, slide.primaryType, slide.primaryTargetId, onCategory, onProduct, onConsult, onAi)
                                    },
                                    modifier = Modifier.weight(1f).height(48.dp),
                                    contentPadding = PaddingValues(horizontal = 8.dp)
                                ) {
                                    Text(slide.primaryLabel, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                }
                            }
                            if (slide.secondaryLabel.isNotBlank() && slide.secondaryType.isNotBlank()) {
                                OutlinedButton(
                                    onClick = {
                                        runHeroActionV103(scope, api, slide.secondaryType, slide.secondaryTargetId, onCategory, onProduct, onConsult, onAi)
                                    },
                                    modifier = Modifier.weight(1f).height(48.dp),
                                    contentPadding = PaddingValues(horizontal = 8.dp),
                                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White)
                                ) {
                                    Text(slide.secondaryLabel, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                }
                            }
                        }
                        Spacer(Modifier.height(8.dp))
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

private fun runHeroActionV103(
    scope: kotlinx.coroutines.CoroutineScope,
    api: AutoIdApi,
    type: String,
    targetId: Long,
    onCategory: (ProductCategory) -> Unit,
    onProduct: (Product) -> Unit,
    onConsult: () -> Unit,
    onAi: () -> Unit
) {
    when (type.lowercase()) {
        "product" -> if (targetId > 0) scope.launch {
            runCatching { withContext(Dispatchers.IO) { api.product(targetId) } }.onSuccess(onProduct)
        }
        "category" -> if (targetId > 0) scope.launch {
            runCatching { withContext(Dispatchers.IO) { api.categories().firstOrNull { it.id == targetId } } }
                .getOrNull()?.let(onCategory)
        }
        "ai" -> onAi()
        "contact", "consultation", "consultanta", "consultanță" -> onConsult()
        else -> onConsult()
    }
}

'''
s = s[:home_start] + home_and_hero + s[hero_end:]

# Price block: AutoID price must always follow MSRP. If AutoID EUR is absent,
# display MSRP as the AutoID ex-VAT fallback instead of dropping the line.
price_start = s.find('@Composable\nprivate fun LoopPriceBlock')
if price_start < 0:
    price_start = s.find('@Composable\r\nprivate fun LoopPriceBlock')
if price_start < 0:
    raise SystemExit('LoopPriceBlock missing')
catalog_marker = s.find('private fun CatalogCard(', price_start)
if catalog_marker < 0:
    raise SystemExit('CatalogCard marker missing')
price_end = s.rfind('@Composable', price_start, catalog_marker)
if price_end <= price_start:
    raise SystemExit('LoopPriceBlock end missing')

price_block = r'''@Composable
private fun LoopPriceBlock(p: Product) {
    val grouped = isGrouped(p)
    val msrp = p.msrpEuroValue
    val configuredAutoId = p.autoIdEuroValue
    val autoId = if (configuredAutoId > 0) configuredAutoId else msrp
    val euroDiscount = msrp > 0 && autoId > 0 && msrp > autoId + 0.005

    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        if (msrp > 0) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("MSRP: ", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Ink)
                Text(
                    "${euro(msrp)} €",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = Ink,
                    textDecoration = if (euroDiscount) androidx.compose.ui.text.style.TextDecoration.LineThrough else null
                )
            }
        }
        if (autoId > 0) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("AutoID: ", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Ink)
                Text("${euro(autoId)} €", fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = AutoIdOrange)
                Text(" ex. TVA", fontSize = 9.sp, color = Muted)
            }
        }

        if (grouped) {
            val range = p.priceRangeInclVat.ifBlank { p.currentInclVat.ifBlank { p.price } }
            if (range.isNotBlank()) {
                Text("$range incl. TVA", fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = Ink, maxLines = 2)
            }
        } else {
            val regular = p.regularInclVatDisplay
            val current = p.saleInclVatDisplay.ifBlank { p.currentInclVat.ifBlank { p.price } }
            val hasDiscount = regular.isNotBlank() && current.isNotBlank() && regular != current
            Row(verticalAlignment = Alignment.CenterVertically) {
                if (hasDiscount) {
                    Text(
                        regular,
                        fontSize = 11.sp,
                        color = Muted,
                        textDecoration = androidx.compose.ui.text.style.TextDecoration.LineThrough
                    )
                    Spacer(Modifier.width(6.dp))
                }
                Text(current, fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = Ink)
                Spacer(Modifier.width(3.dp))
                Text("incl. TVA", fontSize = 9.sp, color = Muted)
            }
        }
    }
}

'''
s = s[:price_start] + price_block + s[price_end:]

# Exact CTA wording requested; dimensions remain identical from v1.0.2.
s = s.replace('Text("Cerere ofertă"', 'Text("Cerere de ofertă"')

p.write_text(s)

# Android semantic version.
p = APP / 'build.gradle.kts'
s = p.read_text().replace('versionCode = 102', 'versionCode = 103').replace('versionName = "1.0.2"', 'versionName = "1.0.3"')
p.write_text(s)

print('Applied AutoID Android v1.0.3 configurable hero and loop fixes')
