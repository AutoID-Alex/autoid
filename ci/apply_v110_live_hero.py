from pathlib import Path

ROOT=Path('.')
API=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/data/AutoIdApi.kt'
UI=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'

s=API.read_text()
old='''    fun heroSlidesV103():List<HeroSlideV103>{\n        val root=JSONObject(get("$MOBILE/home"))'''
new='''    fun heroSlidesV103():List<HeroSlideV103>{\n        // Live Hero config: a dedicated lightweight endpoint + cache buster.\n        // WordPress changes must be visible without rebuilding the APK.\n        val root=JSONObject(get("$MOBILE/hero?_=${System.currentTimeMillis()}"))'''
if old not in s:
    raise SystemExit('heroSlidesV103 endpoint anchor missing')
s=s.replace(old,new,1)

old='''private fun request(method:String,url:String,body:String?,token:String?):String{val c=URI(url).toURL().openConnection() as HttpURLConnection;c.requestMethod=method;c.connectTimeout=12000;c.readTimeout=25000;c.setRequestProperty("Accept","application/json");c.setRequestProperty("User-Agent","AutoID-Android/1.0.9");token?.let{c.setRequestProperty("Authorization","Bearer $it")};'''
new='''private fun request(method:String,url:String,body:String?,token:String?):String{val c=URI(url).toURL().openConnection() as HttpURLConnection;c.requestMethod=method;c.connectTimeout=12000;c.readTimeout=25000;c.useCaches=false;c.setRequestProperty("Accept","application/json");c.setRequestProperty("Cache-Control","no-cache, no-store, max-age=0");c.setRequestProperty("Pragma","no-cache");c.setRequestProperty("User-Agent","AutoID-Android/1.0.10");token?.let{c.setRequestProperty("Authorization","Bearer $it")};'''
if old not in s:
    raise SystemExit('request cache-control anchor missing')
s=s.replace(old,new,1)
API.write_text(s)

s=UI.read_text()
old='''    LaunchedEffect(Unit) {\n        if (data == null) {\n            runCatching { withContext(Dispatchers.IO) { api.homeData() } }\n                .onSuccess {\n                    data = it\n                    HomeBootstrapV104.data = it\n                }\n                .onFailure { error = it.message }\n            loading = false\n        }\n        if (heroSlides.isEmpty()) {\n            runCatching { withContext(Dispatchers.IO) { api.heroSlidesV103() } }\n                .onSuccess {\n                    heroSlides = it\n                    HomeBootstrapV104.heroSlides = it\n                }\n        }\n    }'''
new='''    LaunchedEffect(Unit) {\n        if (data == null) {\n            runCatching { withContext(Dispatchers.IO) { api.homeData() } }\n                .onSuccess {\n                    data = it\n                    HomeBootstrapV104.data = it\n                }\n                .onFailure { error = it.message }\n            loading = false\n        }\n\n        // Hero is remote configuration, not bundled content. Refresh immediately every\n        // time Home enters composition, then keep it fresh while Home stays visible.\n        while (true) {\n            runCatching { withContext(Dispatchers.IO) { api.heroSlidesV103() } }\n                .onSuccess { fresh ->\n                    heroSlides = fresh\n                    HomeBootstrapV104.heroSlides = fresh\n                }\n            delay(20_000)\n        }\n    }'''
if old not in s:
    raise SystemExit('Home hero refresh anchor missing')
s=s.replace(old,new,1)
UI.write_text(s)

g=GRADLE.read_text()
if 'versionCode = 11200' not in g or 'versionName = "1.0.9"' not in g:
    raise SystemExit('v1.0.9 gradle version anchor missing')
g=g.replace('versionCode = 11200','versionCode = 11300',1).replace('versionName = "1.0.9"','versionName = "1.0.10"',1)
GRADLE.write_text(g)
print('Applied Android v1.0.10 live Hero refresh: dedicated /hero endpoint, no-cache requests, 20s foreground refresh')
