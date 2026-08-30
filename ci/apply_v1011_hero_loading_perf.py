from pathlib import Path

ROOT=Path('.')
UI=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt'
API=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/data/AutoIdApi.kt'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'

s=UI.read_text()
if 'import androidx.compose.foundation.lazy.grid.GridItemSpan' not in s:
    s=s.replace('import androidx.compose.foundation.lazy.grid.GridCells\n','import androidx.compose.foundation.lazy.grid.GridCells\nimport androidx.compose.foundation.lazy.grid.GridItemSpan\n',1)
if 'import androidx.compose.ui.text.style.TextAlign' not in s:
    s=s.replace('import androidx.compose.ui.text.style.TextOverflow\n','import androidx.compose.ui.text.style.TextOverflow\nimport androidx.compose.ui.text.style.TextAlign\n',1)

old='''    var ready by rememberSaveable { mutableStateOf(HomeBootstrapV104.loaded) }'''
if old in s:
    s=s.replace(old,'''    var ready by rememberSaveable { mutableStateOf(true) }''',1)
old_effect='''    LaunchedEffect(Unit) {\n        if (!HomeBootstrapV104.loaded) {\n            HomeBootstrapV104.data = runCatching {\n                withContext(Dispatchers.IO) { api.homeData() }\n            }.getOrNull()\n            HomeBootstrapV104.loaded = true\n        }\n        ready = true\n    }'''
if old_effect in s:
    s=s.replace(old_effect,'''    LaunchedEffect(Unit) {\n        HomeBootstrapV104.loaded = true\n        ready = true\n    }''',1)

old_home='''    LaunchedEffect(Unit) {\n        if (data == null) {\n            runCatching { withContext(Dispatchers.IO) { api.homeData() } }\n                .onSuccess {\n                    data = it\n                    HomeBootstrapV104.data = it\n                }\n                .onFailure { error = it.message }\n            loading = false\n        }\n\n        // Hero is remote configuration, not bundled content. Refresh immediately every\n        // time Home enters composition, then keep it fresh while Home stays visible.\n        while (true) {\n            runCatching { withContext(Dispatchers.IO) { api.heroSlidesV103() } }\n                .onSuccess { fresh ->\n                    heroSlides = fresh\n                    HomeBootstrapV104.heroSlides = fresh\n                }\n            delay(20_000)\n        }\n    }'''
new_home='''    LaunchedEffect(Unit) {\n        if (data == null) {\n            runCatching { withContext(Dispatchers.IO) { api.homeData() } }\n                .onSuccess {\n                    data = it\n                    HomeBootstrapV104.data = it\n                }\n                .onFailure { error = it.message }\n            loading = false\n        }\n    }\n\n    LaunchedEffect(Unit) {\n        // Hero is remote configuration. Fetch it independently from the product payload\n        // and refresh it while Home remains visible.\n        while (true) {\n            runCatching { withContext(Dispatchers.IO) { api.heroSlidesV103() } }\n                .onSuccess { fresh ->\n                    heroSlides = fresh\n                    HomeBootstrapV104.heroSlides = fresh\n                }\n            delay(12_000)\n        }\n    }'''
if old_home not in s:
    raise SystemExit('Home live refresh block not found')
s=s.replace(old_home,new_home,1)

hero_start=s.index('@Composable\nprivate fun HeroSliderV103(')
hero_end=s.index('private fun runHeroActionV103(',hero_start)
h=s[hero_start:hero_end]
h=h.replace('modifier = Modifier.height(44.dp).widthIn(max = 205.dp)', 'modifier = Modifier.heightIn(min = 46.dp, max = 64.dp).widthIn(max = 255.dp)')
h=h.replace('Text(slide.primaryLabel, fontSize = 11.sp, fontWeight = FontWeight.ExtraBold, maxLines = 1)', '''Text(\n                                            slide.primaryLabel,\n                                            fontSize = 10.sp,\n                                            lineHeight = 13.sp,\n                                            fontWeight = FontWeight.ExtraBold,\n                                            maxLines = 2,\n                                            textAlign = TextAlign.Center,\n                                            overflow = TextOverflow.Visible\n                                        )''')
s=s[:hero_start]+h+s[hero_end:]

old='''            Spacer(Modifier.weight(1f))\n            if (loading && products.isNotEmpty()) CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp, color = AutoIdOrange)'''
if old not in s:
    raise SystemExit('catalog top loader block not found')
s=s.replace(old,'''            Spacer(Modifier.weight(1f))''',1)

anchor='''        error?.let {\n            Surface(color = Color(0xFFFFF1F0), shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)) {\n                Text(it, color = MaterialTheme.colorScheme.error, fontSize = 12.sp, modifier = Modifier.padding(10.dp))\n            }\n        }\n\n        Box(Modifier.weight(1f)) {'''
if anchor not in s:
    raise SystemExit('catalog error/grid anchor not found')
s=s.replace(anchor,'''        error?.let {\n            Surface(color = Color(0xFFFFF1F0), shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)) {\n                Text(it, color = MaterialTheme.colorScheme.error, fontSize = 12.sp, modifier = Modifier.padding(10.dp))\n            }\n        }\n        if (loading && products.isNotEmpty()) {\n            LinearProgressIndicator(\n                modifier = Modifier.fillMaxWidth().height(2.dp),\n                color = AutoIdOrange,\n                trackColor = Color.Transparent\n            )\n        }\n\n        Box(Modifier.weight(1f)) {''',1)

s=s.replace('''                if (loading && products.isNotEmpty()) {\n                    item {\n                        Box(Modifier.fillMaxWidth().height(58.dp), contentAlignment = Alignment.Center) {''','''                if (loading && products.isNotEmpty()) {\n                    item(span = { GridItemSpan(maxLineSpan) }) {\n                        Box(Modifier.fillMaxWidth().height(58.dp), contentAlignment = Alignment.Center) {''',1)
s=s.replace('''                if (!canLoadMore && products.isNotEmpty()) {\n                    item {\n                        Text(''','''                if (!canLoadMore && products.isNotEmpty()) {\n                    item(span = { GridItemSpan(maxLineSpan) }) {\n                        Text(''',1)
UI.write_text(s)

s=API.read_text().replace('AutoID-Android/1.0.10','AutoID-Android/1.0.11')
API.write_text(s)

g=GRADLE.read_text()
if 'versionCode = 11300' not in g or 'versionName = "1.0.10"' not in g:
    raise SystemExit('v1.0.10 version anchors missing')
g=g.replace('versionCode = 11300','versionCode = 11400',1).replace('versionName = "1.0.10"','versionName = "1.0.11"',1)
GRADLE.write_text(g)
print('Applied Android v1.0.11 hero CTA, centered loading and non-blocking Home startup')
