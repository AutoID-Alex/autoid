from pathlib import Path

p = Path('android-v0.1/app/src/main/java/ro/autoid/app/AiWebChatActivity.kt')
s = p.read_text()
needle = '@SuppressLint("SetJavaScriptEnabled")\n@Composable\nprivate fun AiWebChatScreen'
replacement = '@OptIn(ExperimentalMaterial3Api::class)\n@SuppressLint("SetJavaScriptEnabled")\n@Composable\nprivate fun AiWebChatScreen'
if needle not in s:
    raise RuntimeError('AiWebChatScreen annotation pattern missing')
p.write_text(s.replace(needle, replacement, 1))
print('v0.5 Material3 opt-in applied')
