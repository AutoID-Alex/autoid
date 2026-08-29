from pathlib import Path

p = Path('ci/apply_v104.py')
s = p.read_text()

old = '''old_boot = 'var ready by remember{mutableStateOf(false)};LaunchedEffect(Unit){delay(1800);ready=true};if(!ready){LoadingScreenV100();return}'\nnew_boot = ''' + "'''" + '''var ready by rememberSaveable { mutableStateOf(HomeBootstrapV104.loaded) }\\n    LaunchedEffect(Unit) {\\n        if (!HomeBootstrapV104.loaded) {\\n            HomeBootstrapV104.data = runCatching {\\n                withContext(Dispatchers.IO) { api.homeData() }\\n            }.getOrNull()\\n            HomeBootstrapV104.loaded = true\\n        }\\n        ready = true\\n    }\\n    if (!ready) { LoadingScreenV100(); return }''' + "'''" + '''\nif old_boot not in s:\n    raise SystemExit('AutoIdAppV100 loading bootstrap anchor missing')\ns = s.replace(old_boot, new_boot, 1)\n'''

new = '''new_boot = ''' + "'''" + '''var ready by rememberSaveable { mutableStateOf(HomeBootstrapV104.loaded) }\\n    LaunchedEffect(Unit) {\\n        if (!HomeBootstrapV104.loaded) {\\n            HomeBootstrapV104.data = runCatching {\\n                withContext(Dispatchers.IO) { api.homeData() }\\n            }.getOrNull()\\n            HomeBootstrapV104.loaded = true\\n        }\\n        ready = true\\n    }\\n    if (!ready) { LoadingScreenV100(); return }''' + "'''" + '''\n\napp_pos = s.find('fun AutoIdAppV100(')\nif app_pos < 0:\n    raise SystemExit('AutoIdAppV100 declaration missing')\nloading_pos = s.find('LoadingScreenV100()', app_pos)\nif loading_pos < 0:\n    raise SystemExit('AutoIdAppV100 LoadingScreenV100 call missing')\nready_pos = s.rfind('var ready', app_pos, loading_pos)\nif ready_pos < 0:\n    raise SystemExit('AutoIdAppV100 ready state missing before loading screen')\nreturn_pos = s.find('return', loading_pos)\nif return_pos < 0:\n    raise SystemExit('AutoIdAppV100 loading return missing')\nblock_end = return_pos + len('return')\nwhile block_end < len(s) and s[block_end] in ' ;}':\n    block_end += 1\ns = s[:ready_pos] + new_boot + s[block_end:]\n'''

if old not in s:
    raise SystemExit('v1.0.4 strict bootstrap patch block not found')

p.write_text(s.replace(old, new, 1))
print('Normalized v1.0.4 bootstrap anchor structurally')
