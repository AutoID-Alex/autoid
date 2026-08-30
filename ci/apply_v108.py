from pathlib import Path

ROOT=Path('.')
UI=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt'
API=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/data/AutoIdApi.kt'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'

s=UI.read_text()

if 'import androidx.compose.ui.graphics.Brush' not in s:
    s=s.replace('import androidx.compose.ui.graphics.Color\n','import androidx.compose.ui.graphics.Color\nimport androidx.compose.ui.graphics.Brush\n')

hero_start=s.index('@Composable\nprivate fun HeroSliderV103(')
hero_end=s.index('private fun runHeroActionV103(', hero_start)
hero='''@Composable
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
    // v1.0.8: never render the old blue fallback hero while the API is loading.
    if (slides.isEmpty()) {
        ElevatedCard(
            modifier = Modifier.fillMaxWidth().height(248.dp),
            shape = RoundedCornerShape(26.dp),
            colors = CardDefaults.elevatedCardColors(containerColor = Color(0xFFFCFCFD)),
            elevation = CardDefaults.elevatedCardElevation(defaultElevation = 1.dp)
        ) {
            Box(
                Modifier.fillMaxSize().background(
                    Brush.linearGradient(listOf(Color(0xFFFFFFFF), Color(0xFFFFF6F0)))
                )
            ) {
                Column(
                    Modifier.align(Alignment.CenterStart).padding(24.dp).fillMaxWidth(.68f),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Surface(shape = RoundedCornerShape(50), color = Color(0xFFFFE9D9)) {
                        Text("AUTOID • PROFESSIONAL SOLUTIONS", Modifier.padding(horizontal = 10.dp, vertical = 6.dp), fontSize = 9.sp, fontWeight = FontWeight.ExtraBold, color = AutoIdOrange)
                    }
                    Text("Pregătim recomandările pentru tine", fontSize = 23.sp, lineHeight = 27.sp, fontWeight = FontWeight.ExtraBold, color = Ink)
                    Text("Se încarcă selecția AutoID…", fontSize = 12.sp, color = Muted)
                    LinearProgressIndicator(Modifier.fillMaxWidth(.72f), color = AutoIdOrange, trackColor = Color(0xFFFFE9D9))
                }
                Surface(shape = CircleShape, color = Color(0xFFFFE9D9), modifier = Modifier.align(Alignment.BottomEnd).offset(x = 24.dp, y = 34.dp).size(150.dp)) {}
            }
        }
        return
    }

    val rows = slides
    val pagerState = rememberPagerState(pageCount = { rows.size })
    val scope = rememberCoroutineScope()
    val interval = rows.firstOrNull()?.intervalMs?.coerceIn(3000, 20000) ?: 6000

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
                val accent = remember(slide.background) {
                    runCatching { Color(android.graphics.Color.parseColor(slide.background)) }.getOrDefault(AutoIdOrange)
                }
                var artwork by remember(slide.id, slide.imageUrl) { mutableStateOf(slide.imageUrl) }

                LaunchedEffect(slide.id, slide.imageUrl, slide.primaryType, slide.primaryTargetId) {
                    if (artwork.isNullOrBlank()) {
                        artwork = runCatching {
                            withContext(Dispatchers.IO) {
                                when (slide.primaryType.lowercase()) {
                                    "product" -> slide.primaryTargetId.takeIf { it > 0 }?.let { api.product(it).imageUrl }
                                    "category" -> slide.primaryTargetId.takeIf { it > 0 }?.let {
                                        api.catalogProducts(category = it, page = 1, sort = "stock_autoid").firstOrNull()?.imageUrl
                                    }
                                    else -> null
                                } ?: fallbackProduct?.imageUrl
                            }
                        }.getOrNull()
                    }
                }

                ElevatedCard(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(26.dp),
                    colors = CardDefaults.elevatedCardColors(containerColor = Color.White),
                    elevation = CardDefaults.elevatedCardElevation(defaultElevation = 2.dp)
                ) {
                    Box(
                        Modifier.fillMaxWidth().height(286.dp).background(
                            Brush.linearGradient(
                                listOf(Color(0xFFFFFFFF), Color(0xFFFFFBF8), accent.copy(alpha = .10f))
                            )
                        )
                    ) {
                        Box(
                            Modifier.align(Alignment.TopEnd).offset(x = 54.dp, y = (-46).dp).size(180.dp)
                                .background(accent.copy(alpha = .08f), CircleShape)
                        )
                        Box(
                            Modifier.align(Alignment.BottomStart).offset(x = (-58).dp, y = 68.dp).size(150.dp)
                                .background(AutoIdOrange.copy(alpha = .05f), CircleShape)
                        )

                        Column(
                            Modifier.fillMaxHeight().fillMaxWidth(.66f).padding(start = 22.dp, top = 20.dp, bottom = 18.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Surface(shape = RoundedCornerShape(50), color = Color.White.copy(alpha = .82f)) {
                                Text(
                                    (slide.eyebrow.ifBlank { "AUTOID" }).uppercase(),
                                    Modifier.padding(horizontal = 9.dp, vertical = 5.dp),
                                    color = accent,
                                    fontSize = 9.sp,
                                    fontWeight = FontWeight.ExtraBold,
                                    letterSpacing = .8.sp,
                                    maxLines = 1
                                )
                            }
                            Text(
                                slide.title,
                                color = Ink,
                                fontSize = 24.sp,
                                fontWeight = FontWeight.ExtraBold,
                                lineHeight = 28.sp,
                                maxLines = 3,
                                overflow = TextOverflow.Ellipsis
                            )
                            if (slide.description.isNotBlank()) {
                                Text(
                                    slide.description,
                                    color = Muted,
                                    fontSize = 12.sp,
                                    lineHeight = 17.sp,
                                    maxLines = 3,
                                    overflow = TextOverflow.Ellipsis
                                )
                            }
                            Spacer(Modifier.weight(1f))
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                                if (slide.primaryLabel.isNotBlank() && slide.primaryType.isNotBlank()) {
                                    Button(
                                        onClick = {
                                            runHeroActionV103(scope, api, slide.primaryType, slide.primaryTargetId, onCategory, onProduct, onCatalog, onConsult, onAi)
                                        },
                                        shape = RoundedCornerShape(14.dp),
                                        contentPadding = PaddingValues(horizontal = 15.dp),
                                        modifier = Modifier.height(44.dp).widthIn(max = 190.dp)
                                    ) {
                                        Text(slide.primaryLabel.replace("VEZI TOATE PRODUSELE", "Vezi produsele", ignoreCase = true), fontSize = 11.sp, fontWeight = FontWeight.ExtraBold, maxLines = 1)
                                        Spacer(Modifier.width(5.dp))
                                        Icon(Icons.Default.ArrowForward, null, Modifier.size(15.dp))
                                    }
                                }
                                if (slide.secondaryLabel.isNotBlank() && slide.secondaryType.isNotBlank()) {
                                    TextButton(onClick = {
                                        runHeroActionV103(scope, api, slide.secondaryType, slide.secondaryTargetId, onCategory, onProduct, onCatalog, onConsult, onAi)
                                    }) { Text(slide.secondaryLabel, fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Ink) }
                                }
                            }
                        }

                        Surface(
                            shape = RoundedCornerShape(22.dp),
                            color = Color.White.copy(alpha = .94f),
                            shadowElevation = 7.dp,
                            modifier = Modifier.align(Alignment.BottomEnd).padding(end = 16.dp, bottom = 17.dp).width(132.dp).height(156.dp)
                        ) {
                            if (!artwork.isNullOrBlank()) {
                                AsyncImage(artwork, slide.title, Modifier.fillMaxSize().padding(10.dp), contentScale = ContentScale.Fit)
                            } else {
                                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                                    Icon(Icons.Default.Inventory2, null, tint = accent.copy(alpha = .75f), modifier = Modifier.size(54.dp))
                                }
                            }
                        }
                    }
                }
            }

            if (rows.size > 1) {
                IconButton(
                    onClick = { scope.launch { pagerState.animateScrollToPage(if (pagerState.currentPage == 0) rows.lastIndex else pagerState.currentPage - 1) } },
                    modifier = Modifier.align(Alignment.CenterStart).padding(start = 3.dp).size(34.dp)
                ) {
                    Surface(shape = CircleShape, color = Color.White.copy(alpha = .92f), shadowElevation = 2.dp) {
                        Icon(Icons.Default.ChevronLeft, "Slide anterior", tint = Ink, modifier = Modifier.padding(6.dp))
                    }
                }
                IconButton(
                    onClick = { scope.launch { pagerState.animateScrollToPage((pagerState.currentPage + 1) % rows.size) } },
                    modifier = Modifier.align(Alignment.CenterEnd).padding(end = 3.dp).size(34.dp)
                ) {
                    Surface(shape = CircleShape, color = Color.White.copy(alpha = .92f), shadowElevation = 2.dp) {
                        Icon(Icons.Default.ChevronRight, "Slide următor", tint = Ink, modifier = Modifier.padding(6.dp))
                    }
                }
            }
        }

        if (rows.size > 1) {
            Row(Modifier.padding(top = 9.dp), horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                rows.indices.forEach { index ->
                    Box(
                        Modifier.width(if (pagerState.currentPage == index) 20.dp else 7.dp).height(7.dp)
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

start=s.index('    var page by remember(category.id) { mutableIntStateOf(1) }', s.index('fun CatalogV100'))
end_marker='    val activeFilterCount = listOf(brand, model, min, max, secondaryCategory).count { it != null }\n'
end=s.index(end_marker,start)+len(end_marker)
paging='''    var page by remember(category.id) { mutableIntStateOf(1) }
    var loading by remember { mutableStateOf(false) }
    var canLoadMore by remember(category.id) { mutableStateOf(true) }
    var filters by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val gridState = rememberLazyGridState()
    val loadMutex = remember(category.id) { kotlinx.coroutines.sync.Mutex() }

    suspend fun load(reset: Boolean) {
        loadMutex.lock()
        try {
            loading = true
            error = null
            if (reset) {
                page = 1
                canLoadMore = true
            }
            val requestPage = page
            val rows = try {
                withContext(Dispatchers.IO) {
                    api.catalogProducts(q, category.id, requestPage, sort, brand, model, min, max, secondaryCategory)
                }
            } catch (cancelled: kotlinx.coroutines.CancellationException) {
                throw cancelled
            } catch (t: Throwable) {
                error = t.message ?: "Produsele nu au putut fi încărcate."
                emptyList()
            }

            val liquidationModeLocal =
                category.slug.equals("lichidari-de-stoc", ignoreCase = true) ||
                category.name.equals("Lichidări de stoc", ignoreCase = true) ||
                category.name.equals("Lichidari de stoc", ignoreCase = true)
            val visibleRows = if (liquidationModeLocal && secondaryCategory != null) {
                rows.filter { product -> product.categories.any { it.id == secondaryCategory } }
            } else rows

            if (reset) {
                products = visibleRows.distinctBy { it.id }
            } else {
                val existing = products.asSequence().map { it.id }.toHashSet()
                val fresh = visibleRows.filterNot { it.id in existing }
                products = products + fresh
                if (fresh.isEmpty()) canLoadMore = false
            }
            if (rows.size < 20) canLoadMore = false
        } finally {
            loading = false
            loadMutex.unlock()
        }
    }

    LaunchedEffect(category.id) {
        facets = runCatching { withContext(Dispatchers.IO) { api.catalogFacets(category.id) } }.getOrNull()
    }
    LaunchedEffect(category.id, brand, model, min, max, sort, secondaryCategory, q) {
        if (q.isNotBlank()) delay(300)
        load(true)
    }

    LaunchedEffect(gridState, category.id, brand, model, min, max, sort, secondaryCategory, q) {
        snapshotFlow {
            val last = gridState.layoutInfo.visibleItemsInfo.lastOrNull()?.index ?: -1
            last to products.size
        }.collect { (last, size) ->
            if (canLoadMore && !loading && size > 0 && last >= size - 5) {
                page += 1
                load(false)
            }
        }
    }

    val activeFilterCount = listOf(brand, model, min, max, secondaryCategory).count { it != null }
'''
s=s[:start]+paging+s[end:]

helper_anchor='private fun moneyRonV107(value: Double): String =\n'
helper_pos=s.index(helper_anchor)
insert='''private fun cleanDisplayV108(raw: String): String = raw
    .replace("&amp;nbsp;", " ", ignoreCase = true)
    .replace("&nbsp;", " ", ignoreCase = true)
    .replace("&#160;", " ", ignoreCase = true)
    .replace("&#xA0;", " ", ignoreCase = true)
    .replace('\\u00A0', ' ')
    .replace(Regex("\\\\s+"), " ")
    .trim()

'''
s=s[:helper_pos]+insert+s[helper_pos:]
s=s.replace('Text(line.product.currentInclVat.ifBlank { line.product.price } + " incl. TVA", fontWeight = FontWeight.ExtraBold, fontSize = 13.sp, color = Ink)',
            'Text(cleanDisplayV108(line.product.currentInclVat.ifBlank { line.product.price }) + " incl. TVA", fontWeight = FontWeight.ExtraBold, fontSize = 13.sp, color = Ink)')

UI.write_text(s)

a=API.read_text()
old='''    private fun html(s:String)=Html.fromHtml(s,Html.FROM_HTML_MODE_LEGACY).toString().replace(Regex("\\\\s+")," ").trim()'''
new='''    private fun html(s:String):String {
        var out=s
        repeat(2){ out=Html.fromHtml(out,Html.FROM_HTML_MODE_LEGACY).toString() }
        return out.replace("&amp;nbsp;"," ",ignoreCase=true).replace("&nbsp;"," ",ignoreCase=true).replace("&#160;"," ",ignoreCase=true).replace("&#xA0;"," ",ignoreCase=true).replace('\\u00A0',' ').replace(Regex("\\\\s+")," ").trim()
    }'''
if old not in a:
    raise SystemExit('AutoIdApi html anchor not found')
a=a.replace(old,new)
a=a.replace('AutoID-Android/1.0.7','AutoID-Android/1.0.8')
API.write_text(a)

g=GRADLE.read_text().replace('versionCode = 11000','versionCode = 11100').replace('versionName = "1.0.7"','versionName = "1.0.8"')
GRADLE.write_text(g)

print('Applied Android v1.0.8: premium hero, HTML price cleanup and robust infinite catalog paging')
