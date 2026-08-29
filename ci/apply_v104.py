from pathlib import Path

APP = Path('android-v0.1/app')

# v1.0.4 focuses only on lifecycle/bootstrap stability and exact loop card rules.
p = APP / 'src/main/java/ro/autoid/app/V100Screens.kt'
s = p.read_text()

if 'import androidx.compose.runtime.saveable.rememberSaveable' not in s:
    s = s.replace('import androidx.compose.runtime.*\n', 'import androidx.compose.runtime.*\nimport androidx.compose.runtime.saveable.rememberSaveable\n', 1)

cache_anchor = 'private val Warn=Color(0xFFF79009)\n'
cache_block = '''private val Warn=Color(0xFFF79009)\n\nprivate object HomeBootstrapV104 {\n    @Volatile var loaded: Boolean = false\n    @Volatile var data: HomeV100Data? = null\n    @Volatile var heroSlides: List<HeroSlideV103> = emptyList()\n}\n'''
if 'private object HomeBootstrapV104' not in s:
    if cache_anchor not in s:
        raise SystemExit('Warn color anchor missing')
    s = s.replace(cache_anchor, cache_block, 1)

old_boot = 'var ready by remember{mutableStateOf(false)};LaunchedEffect(Unit){delay(1800);ready=true};if(!ready){LoadingScreenV100();return}'
new_boot = '''var ready by rememberSaveable { mutableStateOf(HomeBootstrapV104.loaded) }\n    LaunchedEffect(Unit) {\n        if (!HomeBootstrapV104.loaded) {\n            HomeBootstrapV104.data = runCatching {\n                withContext(Dispatchers.IO) { api.homeData() }\n            }.getOrNull()\n            HomeBootstrapV104.loaded = true\n        }\n        ready = true\n    }\n    if (!ready) { LoadingScreenV100(); return }'''
if old_boot not in s:
    raise SystemExit('AutoIdAppV100 loading bootstrap anchor missing')
s = s.replace(old_boot, new_boot, 1)

# Replace Home only; keep the v1.0.3 Bridge-driven hero implementation intact.
home_start = s.find('@Composable\nfun HomeV100(')
if home_start < 0:
    raise SystemExit('v1.0.3 HomeV100 start missing')
hero_start = s.find('@Composable\nprivate fun HeroSliderV103(', home_start)
if hero_start < 0:
    raise SystemExit('HeroSliderV103 start missing')

home = r'''@Composable
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
    var data by remember { mutableStateOf<HomeV100Data?>(HomeBootstrapV104.data) }
    var heroSlides by remember { mutableStateOf(HomeBootstrapV104.heroSlides) }
    var loading by remember { mutableStateOf(data == null) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        if (data == null) {
            runCatching { withContext(Dispatchers.IO) { api.homeData() } }
                .onSuccess {
                    data = it
                    HomeBootstrapV104.data = it
                }
                .onFailure { error = it.message }
            loading = false
        }
        if (heroSlides.isEmpty()) {
            runCatching { withContext(Dispatchers.IO) { api.heroSlidesV103() } }
                .onSuccess {
                    heroSlides = it
                    HomeBootstrapV104.heroSlides = it
                }
        }
    }

    LazyColumn(
        Modifier.fillMaxSize().padding(horizontal = 16.dp).statusBarsPadding(),
        verticalArrangement = Arrangement.spacedBy(20.dp),
        contentPadding = PaddingValues(bottom = 24.dp)
    ) {
        item {
            HomeHeader(commerce, onMenu, onFavorites, onNotifications, onFullCart, mini, onMini, cartTick)
            SmartSearch(api, q, { q = it }, { onSearch(it) }, onProduct, scan)
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

        val liquidations = (data?.offers ?: emptyList()).filter { (it.stockAutoId ?: 0) > 0 }
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

'''
s = s[:home_start] + home + s[hero_start:]

# Product type is authoritative. Family/group associations must never turn a Woo simple product into a grouped loop card.
old_grouped = 'private fun isGrouped(p:Product)=p.productType=="grouped"||p.groupedChildIds.isNotEmpty()'
new_grouped = 'private fun isGrouped(p:Product)=p.productType.equals("grouped",ignoreCase=true)'
if old_grouped not in s:
    raise SystemExit('isGrouped v1.0.3 anchor missing')
s = s.replace(old_grouped, new_grouped, 1)

# Exact loop price rules and a normalizer for already-formatted grouped VAT ranges.
price_start = s.find('@Composable\nprivate fun LoopPriceBlock')
if price_start < 0:
    raise SystemExit('LoopPriceBlock start missing')
catalog_fn = s.find('private fun CatalogCard(', price_start)
if catalog_fn < 0:
    raise SystemExit('CatalogCard after LoopPriceBlock missing')
price_end = s.rfind('@Composable', price_start, catalog_fn)
if price_end <= price_start:
    raise SystemExit('LoopPriceBlock end missing')

price_block = r'''private fun cleanVatRangeV104(raw: String): String {
    if (raw.isBlank()) return ""
    val numbers = Regex("""\d{1,3}(?:\.\d{3})*(?:,\d{2})|\d+(?:,\d{2})""").findAll(raw).map { it.value }.toList()
    if (numbers.size >= 2) return "${numbers[0]} – ${numbers[1]} lei incl. TVA"
    val clean = raw
        .replace(Regex("(?i)\\s*incl\\.?\\s*TVA"), "")
        .replace(Regex("(?i)\\s*lei\\s*$"), "")
        .trim()
    return if (clean.isBlank()) "" else "$clean lei incl. TVA"
}

private fun canAddV104(p: Product): Boolean =
    !isGrouped(p) && ((p.stockAutoId ?: 0) > 0 || (p.stockDistributor ?: 0) > 0)

@Composable
private fun LoopPriceBlock(p: Product) {
    val grouped = isGrouped(p)
    val msrp = p.msrpEuroValue
    val autoId = p.autoIdEuroValue
    val sameEuro = msrp > 0 && autoId > 0 && kotlin.math.abs(msrp - autoId) < 0.005
    val showAutoId = autoId > 0 && !sameEuro
    val euroDiscount = msrp > 0 && showAutoId && msrp > autoId + 0.005

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
                if (!showAutoId) Text(" ex. TVA", fontSize = 9.sp, color = Muted)
            }
        }
        if (showAutoId) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("AutoID: ", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Ink)
                Text("${euro(autoId)} €", fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = AutoIdOrange)
                Text(" ex. TVA", fontSize = 9.sp, color = Muted)
            }
        } else if (msrp <= 0 && autoId > 0) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("AutoID: ", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Ink)
                Text("${euro(autoId)} €", fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = AutoIdOrange)
                Text(" ex. TVA", fontSize = 9.sp, color = Muted)
            }
        }

        if (grouped) {
            val range = cleanVatRangeV104(p.priceRangeInclVat.ifBlank { p.currentInclVat.ifBlank { p.price } })
            if (range.isNotBlank()) {
                Text(range, fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = Ink, maxLines = 2)
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

@Composable
private fun LoopQuantityV104(qty: Int, onMinus: () -> Unit, onPlus: () -> Unit) {
    Row(
        modifier = Modifier.height(28.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.Center
    ) {
        IconButton(onClick = onMinus, enabled = qty > 1, modifier = Modifier.size(28.dp)) {
            Icon(Icons.Default.Remove, "Scade cantitatea", modifier = Modifier.size(15.dp))
        }
        Text(qty.toString(), fontSize = 11.sp, fontWeight = FontWeight.Bold, modifier = Modifier.widthIn(min = 20.dp), textAlign = androidx.compose.ui.text.style.TextAlign.Center)
        IconButton(onClick = onPlus, modifier = Modifier.size(28.dp)) {
            Icon(Icons.Default.Add, "Crește cantitatea", modifier = Modifier.size(15.dp))
        }
    }
}

'''
s = s[:price_start] + price_block + s[price_end:]

# Catalog loop card: simple = QTY + Add to cart; grouped = Details. RFQ stays identical in both.
catalog_fn = s.find('private fun CatalogCard(')
if catalog_fn < 0:
    raise SystemExit('CatalogCard declaration missing')
catalog_start = s.rfind('@Composable', 0, catalog_fn)
product_fn = s.find('fun ProductV100', catalog_fn)
if product_fn < 0:
    raise SystemExit('ProductV100 after CatalogCard missing')
catalog_end = s.rfind('@Composable', catalog_fn, product_fn)
if catalog_start < 0 or catalog_end <= catalog_start:
    raise SystemExit('CatalogCard boundaries missing')

catalog = r'''@Composable
private fun CatalogCard(
    p: Product,
    favorite: Boolean,
    onProduct: () -> Unit,
    onFavorite: () -> Unit,
    onCart: () -> Unit,
    onRfq: () -> Unit
) {
    var qty by remember(p.id) { mutableIntStateOf(1) }
    ElevatedCard(
        modifier = Modifier.height(462.dp),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.fillMaxSize().padding(10.dp)) {
            Box(Modifier.fillMaxWidth().height(128.dp).clickable(onClick = onProduct)) {
                AsyncImage(p.imageUrl, p.name, Modifier.fillMaxSize(), contentScale = ContentScale.Fit)
                DiscountChip(p, Modifier.align(Alignment.TopStart))
                IconButton(onClick = onFavorite, modifier = Modifier.align(Alignment.TopEnd)) {
                    Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "Favorite", tint = if (favorite) AutoIdOrange else Ink)
                }
            }
            Text(p.brand, fontSize = 10.sp, color = Muted, maxLines = 1)
            Text(p.name, maxLines = 2, overflow = TextOverflow.Ellipsis, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            RatingLine(p, true)
            Text("SKU: ${p.sku.ifBlank { "—" }}", fontSize = 9.sp, color = Muted, maxLines = 1)
            Spacer(Modifier.height(5.dp))
            LoopPriceBlock(p)
            Spacer(Modifier.height(6.dp))
            StockLine(p, true)
            Spacer(Modifier.weight(1f))
            if (!isGrouped(p)) {
                LoopQuantityV104(qty, { if (qty > 1) qty-- }, { if (qty < 99) qty++ })
                Spacer(Modifier.height(3.dp))
            } else {
                Spacer(Modifier.height(31.dp))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.fillMaxWidth()) {
                if (isGrouped(p)) {
                    OutlinedButton(onClick = onProduct, modifier = Modifier.weight(1f).height(44.dp), contentPadding = PaddingValues(horizontal = 4.dp)) {
                        Text("Detalii produs", fontSize = 10.sp)
                    }
                } else {
                    Button(
                        onClick = { repeat(qty) { onCart() }; qty = 1 },
                        enabled = canAddV104(p),
                        modifier = Modifier.weight(1f).height(44.dp),
                        contentPadding = PaddingValues(horizontal = 4.dp)
                    ) { Text("Adaugă în coș", fontSize = 10.sp) }
                }
                OutlinedButton(onClick = onRfq, modifier = Modifier.weight(1f).height(44.dp), contentPadding = PaddingValues(horizontal = 4.dp)) {
                    Text("Cerere de ofertă", fontSize = 10.sp)
                }
            }
        }
    }
}

'''
s = s[:catalog_start] + catalog + s[catalog_end:]

# Home horizontal card gets the same exact template split.
homecard_fn = s.find('private fun HomeCard(')
if homecard_fn < 0:
    raise SystemExit('HomeCard declaration missing')
homecard_start = s.rfind('@Composable', 0, homecard_fn)
discount_fn = s.find('private fun DiscountChip', homecard_fn)
if discount_fn < 0:
    raise SystemExit('DiscountChip after HomeCard missing')
homecard_end = s.rfind('@Composable', homecard_fn, discount_fn)
if homecard_start < 0 or homecard_end <= homecard_start:
    raise SystemExit('HomeCard boundaries missing')

homecard = r'''@Composable
private fun HomeCard(
    p: Product,
    favorite: Boolean,
    onClick: () -> Unit,
    onFavorite: () -> Unit,
    onCart: () -> Unit,
    onRfq: () -> Unit
) {
    var qty by remember(p.id) { mutableIntStateOf(1) }
    ElevatedCard(
        modifier = Modifier.width(230.dp).height(462.dp),
        shape = RoundedCornerShape(18.dp)
    ) {
        Column(Modifier.fillMaxSize().padding(12.dp)) {
            Box(Modifier.fillMaxWidth().height(130.dp).clickable(onClick = onClick)) {
                AsyncImage(p.imageUrl, p.name, Modifier.fillMaxSize(), contentScale = ContentScale.Fit)
                IconButton(onClick = onFavorite, modifier = Modifier.align(Alignment.TopEnd)) {
                    Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "Favorite", tint = if (favorite) AutoIdOrange else Ink)
                }
                DiscountChip(p, Modifier.align(Alignment.TopStart))
            }
            Text(p.brand.ifBlank { p.category }, fontSize = 10.sp, color = Muted, maxLines = 1)
            Text(p.name, maxLines = 2, overflow = TextOverflow.Ellipsis, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            RatingLine(p, true)
            Text("SKU: ${p.sku.ifBlank { "—" }}", fontSize = 9.sp, color = Muted, maxLines = 1)
            Spacer(Modifier.height(5.dp))
            LoopPriceBlock(p)
            Spacer(Modifier.height(6.dp))
            StockLine(p, true)
            Spacer(Modifier.weight(1f))
            if (!isGrouped(p)) {
                LoopQuantityV104(qty, { if (qty > 1) qty-- }, { if (qty < 99) qty++ })
                Spacer(Modifier.height(3.dp))
            } else {
                Spacer(Modifier.height(31.dp))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.fillMaxWidth()) {
                if (isGrouped(p)) {
                    OutlinedButton(onClick = onClick, modifier = Modifier.weight(1f).height(44.dp), contentPadding = PaddingValues(horizontal = 4.dp)) {
                        Text("Detalii produs", fontSize = 10.sp)
                    }
                } else {
                    Button(
                        onClick = { repeat(qty) { onCart() }; qty = 1 },
                        enabled = canAddV104(p),
                        modifier = Modifier.weight(1f).height(44.dp),
                        contentPadding = PaddingValues(horizontal = 4.dp)
                    ) { Text("Adaugă în coș", fontSize = 10.sp) }
                }
                OutlinedButton(onClick = onRfq, modifier = Modifier.weight(1f).height(44.dp), contentPadding = PaddingValues(horizontal = 4.dp)) {
                    Text("Cerere de ofertă", fontSize = 10.sp)
                }
            }
        }
    }
}

'''
s = s[:homecard_start] + homecard + s[homecard_end:]

p.write_text(s)

# User-Agent and semantic Android version.
p = APP / 'src/main/java/ro/autoid/app/data/AutoIdApi.kt'
s = p.read_text().replace('AutoID-Android/1.0.3', 'AutoID-Android/1.0.4')
p.write_text(s)

p = APP / 'build.gradle.kts'
s = p.read_text().replace('versionCode = 103', 'versionCode = 104').replace('versionName = "1.0.3"', 'versionName = "1.0.4"')
p.write_text(s)

print('Applied AutoID Android v1.0.4 lifecycle, loop pricing, quantity and stock rules')
