from pathlib import Path

p=Path('android-v0.1/app/src/main/java/ro/autoid/app/V114CommerceUx.kt')
s=p.read_text()
decl='    var panel by remember{mutableStateOf("dashboard")}\n'
# Remove any declaration accidentally inserted in an earlier composable.
s=s.replace(decl,'')
account=s.index('fun AccountV114(')
effect=s.index('    LaunchedEffect(Unit){runCatching{withContext(Dispatchers.IO){api.checkoutConfig()}}.onSuccess{cfg=it}}',account)
s=s[:effect]+decl+s[effect:]
p.write_text(s)
print('Placed v1.0.15 account panel state inside AccountV114 composable scope')
