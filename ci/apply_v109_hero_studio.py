from pathlib import Path

ROOT=Path('.')
MODELS=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/data/Models.kt'
API=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/data/AutoIdApi.kt'
UI=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'

# Hero API model: add server-controlled style.
s=MODELS.read_text()
hero_start=s.index('data class HeroSlideV103(')
hero_end=s.index('\n)', hero_start)+2
hero=s[hero_start:hero_end]
if 'val style: String' not in hero:
    hero=hero.replace('    val intervalMs: Long = 5500\n)', '    val intervalMs: Long = 5500,\n    val style: String = "card"\n)')
    s=s[:hero_start]+hero+s[hero_end:]
MODELS.write_text(s)

# Parse style; v1.0.9 UA.
s=API.read_text()
anchor='intervalMs=o.optLong("interval_ms",5500).coerceIn(2500,20000)'
if anchor not in s:
    raise SystemExit('Hero interval parser anchor missing')
if 'style=o.optString("style","card")' not in s:
    s=s.replace(anchor, anchor+',\n                style=o.optString("style","card").ifBlank { "card" }',1)
s=s.replace('AutoID-Android/1.0.8','AutoID-Android/1.0.9')
API.write_text(s)

# Replace hero with 2 server-controlled designs. No inferred/fallback product artwork.
s=UI.read_text()
start=s.index('@Composable\nprivate fun HeroSliderV103(')
end=s.index('private fun runHeroActionV103(',start)
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
    if (slides.isEmpty()) {
        ElevatedCard(
            modifier = Modifier.fillMaxWidth().height(238.dp),
            shape = RoundedCornerShape(26.dp),
            colors = CardDefaults.elevatedCardColors(containerColor = Color(0xFFFCFCFD)),
            elevation = CardDefaults.elevatedCardElevation(defaultElevation = 1.dp)
        ) {
            Box(
                Modifier.fillMaxSize().background(
                    Brush.linearGradient(listOf(Color.White, Color(0xFFFFF7F2)))
                )
            ) {
                Column(
                    Modifier.align(Alignment.CenterStart).padding(24.dp).fillMaxWidth(.78f),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Surface(shape = RoundedCornerShape(50), color = Color(0xFFFFE9D9)) {
                        Text("AUTOID • PROFESSIONAL SOLUTIONS", Modifier.padding(horizontal = 10.dp, vertical = 6.dp), fontSize = 9.sp, fontWeight = FontWeight.ExtraBold, color = AutoIdOrange)
                    }
                    Text("Pregătim selecția AutoID", fontSize = 23.sp, lineHeight = 27.sp, fontWeight = FontWeight.ExtraBold, color = Ink)
                    Text("Conținutul sliderului este administrat din WordPress.", fontSize = 12.sp, color = Muted)
                    LinearProgressIndicator(Modifier.fillMaxWidth(.62f), color = AutoIdOrange, trackColor = Color(0xFFFFE9D9))
                }
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
                pagerState.animateScrollToPage((pagerState.currentPage + 1) % rows.size)
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
                val hasImage = !slide.imageUrl.isNullOrBlank()
                val backgroundStyle = slide.style.equals("background", ignoreCase = true)

                if (backgroundStyle) {
                    ElevatedCard(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(26.dp),
                        colors = CardDefaults.elevatedCardColors(containerColor = Color(0xFF132238)),
                        elevation = CardDefaults.elevatedCardElevation(defaultElevation = 3.dp)
                    ) {
                        Box(Modifier.fillMaxWidth().height(286.dp)) {
                            if (hasImage) {
                                AsyncImage(
                                    slide.imageUrl,
                                    slide.title,
                                    Modifier.fillMaxSize(),
                                    contentScale = ContentScale.Crop
                                )
                                Box(
                                    Modifier.fillMaxSize().background(
                                        Brush.horizontalGradient(
                                            listOf(Color(0xF2111D2F), Color(0xC4111D2F), Color(0x33111D2F))
                                        )
                                    )
                                )
                                Box(
                                    Modifier.fillMaxSize().background(
                                        Brush.verticalGradient(
                                            listOf(Color.Transparent, Color(0x6609121F))
                                        )
                                    )
                                )
                            } else {
                                Box(
                                    Modifier.fillMaxSize().background(
                                        Brush.linearGradient(
                                            listOf(Color(0xFF132238), Color(0xFF203A57), accent.copy(alpha = .78f))
                                        )
                                    )
                                )
                            }

                            Column(
                                Modifier.fillMaxHeight().fillMaxWidth(if (hasImage) .78f else .92f).padding(start = 24.dp, top = 22.dp, bottom = 20.dp),
                                verticalArrangement = Arrangement.spacedBy(9.dp)
                            ) {
                                Surface(shape = RoundedCornerShape(50), color = Color.White.copy(alpha = .14f)) {
                                    Text(
                                        (slide.eyebrow.ifBlank { "AUTOID" }).uppercase(),
                                        Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                                        color = Color.White,
                                        fontSize = 9.sp,
                                        fontWeight = FontWeight.ExtraBold,
                                        letterSpacing = .9.sp
                                    )
                                }
                                Text(
                                    slide.title,
                                    color = Color.White,
                                    fontSize = 25.sp,
                                    fontWeight = FontWeight.ExtraBold,
                                    lineHeight = 29.sp,
                                    maxLines = 3,
                                    overflow = TextOverflow.Ellipsis
                                )
                                if (slide.description.isNotBlank()) {
                                    Text(
                                        slide.description,
                                        color = Color.White.copy(alpha = .88f),
                                        fontSize = 12.sp,
                                        lineHeight = 17.sp,
                                        maxLines = 3,
                                        overflow = TextOverflow.Ellipsis
                                    )
                                }
                                Spacer(Modifier.weight(1f))
                                if (slide.primaryLabel.isNotBlank() && slide.primaryType.isNotBlank()) {
                                    Button(
                                        onClick = { runHeroActionV103(scope, api, slide.primaryType, slide.primaryTargetId, onCategory, onProduct, onCatalog, onConsult, onAi) },
                                        shape = RoundedCornerShape(14.dp),
                                        colors = ButtonDefaults.buttonColors(containerColor = Color.White, contentColor = Ink),
                                        contentPadding = PaddingValues(horizontal = 15.dp),
                                        modifier = Modifier.height(44.dp).widthIn(max = 205.dp)
                                    ) {
                                        Text(slide.primaryLabel, fontSize = 11.sp, fontWeight = FontWeight.ExtraBold, maxLines = 1)
                                        Spacer(Modifier.width(5.dp))
                                        Icon(Icons.Default.ArrowForward, null, Modifier.size(15.dp))
                                    }
                                }
                            }
                        }
                    }
                } else {
                    ElevatedCard(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(26.dp),
                        colors = CardDefaults.elevatedCardColors(containerColor = Color.White),
                        elevation = CardDefaults.elevatedCardElevation(defaultElevation = 2.dp)
                    ) {
                        Box(
                            Modifier.fillMaxWidth().height(286.dp).background(
                                Brush.linearGradient(listOf(Color.White, Color(0xFFFFFBF8), accent.copy(alpha = .10f)))
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
                                Modifier.fillMaxHeight().fillMaxWidth(if (hasImage) .65f else .90f).padding(start = 22.dp, top = 20.dp, bottom = 18.dp),
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Surface(shape = RoundedCornerShape(50), color = Color.White.copy(alpha = .84f)) {
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
                                Text(slide.title, color = Ink, fontSize = 24.sp, fontWeight = FontWeight.ExtraBold, lineHeight = 28.sp, maxLines = 3, overflow = TextOverflow.Ellipsis)
                                if (slide.description.isNotBlank()) {
                                    Text(slide.description, color = Muted, fontSize = 12.sp, lineHeight = 17.sp, maxLines = 3, overflow = TextOverflow.Ellipsis)
                                }
                                Spacer(Modifier.weight(1f))
                                if (slide.primaryLabel.isNotBlank() && slide.primaryType.isNotBlank()) {
                                    Button(
                                        onClick = { runHeroActionV103(scope, api, slide.primaryType, slide.primaryTargetId, onCategory, onProduct, onCatalog, onConsult, onAi) },
                                        shape = RoundedCornerShape(14.dp),
                                        contentPadding = PaddingValues(horizontal = 15.dp),
                                        modifier = Modifier.height(44.dp).widthIn(max = 205.dp)
                                    ) {
                                        Text(slide.primaryLabel, fontSize = 11.sp, fontWeight = FontWeight.ExtraBold, maxLines = 1)
                                        Spacer(Modifier.width(5.dp))
                                        Icon(Icons.Default.ArrowForward, null, Modifier.size(15.dp))
                                    }
                                }
                            }

                            if (hasImage) {
                                Surface(
                                    shape = RoundedCornerShape(22.dp),
                                    color = Color.White.copy(alpha = .96f),
                                    shadowElevation = 7.dp,
                                    modifier = Modifier.align(Alignment.BottomEnd).padding(end = 16.dp, bottom = 17.dp).width(132.dp).height(156.dp)
                                ) {
                                    AsyncImage(slide.imageUrl, slide.title, Modifier.fillMaxSize().padding(10.dp), contentScale = ContentScale.Fit)
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
                    Surface(shape = CircleShape, color = Color.White.copy(alpha = .90f), shadowElevation = 2.dp) {
                        Icon(Icons.Default.ChevronLeft, "Slide anterior", tint = Ink, modifier = Modifier.padding(6.dp))
                    }
                }
                IconButton(
                    onClick = { scope.launch { pagerState.animateScrollToPage((pagerState.currentPage + 1) % rows.size) } },
                    modifier = Modifier.align(Alignment.CenterEnd).padding(end = 3.dp).size(34.dp)
                ) {
                    Surface(shape = CircleShape, color = Color.White.copy(alpha = .90f), shadowElevation = 2.dp) {
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
s=s[:start]+hero+s[end:]
UI.write_text(s)

# Version.
g=GRADLE.read_text().replace('versionCode = 11100','versionCode = 11200').replace('versionName = "1.0.8"','versionName = "1.0.9"')
GRADLE.write_text(g)

print('Applied Android v1.0.9: explicit app hero image only + card/background hero styles')
