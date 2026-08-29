from pathlib import Path

p = Path('android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt')
s = p.read_text()

anchor = '''@Composable
private fun LoopQuantityV104(qty: Int, onMinus: () -> Unit, onPlus: () -> Unit) {'''
if anchor not in s:
    raise SystemExit('LoopQuantityV104 anchor missing')

component = r'''@Composable
private fun LoopActionButtonV104(
    label: String,
    filled: Boolean,
    enabled: Boolean = true,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    val outline = if (enabled) Color(0xFF667085) else Color(0xFFD0D5DD)
    val bg = when {
        filled && enabled -> AutoIdOrange
        filled -> Color(0xFFF2F4F7)
        else -> Color.Transparent
    }
    val fg = when {
        filled && enabled -> Color.White
        !enabled -> Color(0xFF98A2B3)
        else -> AutoIdOrange
    }
    Surface(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier.height(48.dp),
        shape = RoundedCornerShape(24.dp),
        color = bg,
        contentColor = fg,
        border = if (filled) null else androidx.compose.foundation.BorderStroke(1.dp, outline)
    ) {
        Box(
            modifier = Modifier.fillMaxSize().padding(horizontal = 8.dp, vertical = 6.dp),
            contentAlignment = Alignment.Center
        ) {
            Text(
                label,
                fontSize = 10.sp,
                fontWeight = FontWeight.SemiBold,
                maxLines = 1,
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
        }
    }
}

'''

if 'private fun LoopActionButtonV104(' not in s:
    s = s.replace(anchor, component + anchor, 1)

catalog_old = '''            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.fillMaxWidth()) {
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
            }'''

catalog_new = '''            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.fillMaxWidth()) {
                if (isGrouped(p)) {
                    LoopActionButtonV104(
                        label = "Detalii produs",
                        filled = false,
                        modifier = Modifier.weight(1f),
                        onClick = onProduct
                    )
                } else {
                    LoopActionButtonV104(
                        label = "Adaugă în coș",
                        filled = true,
                        enabled = canAddV104(p),
                        modifier = Modifier.weight(1f),
                        onClick = { repeat(qty) { onCart() }; qty = 1 }
                    )
                }
                LoopActionButtonV104(
                    label = "Cerere de ofertă",
                    filled = false,
                    modifier = Modifier.weight(1f),
                    onClick = onRfq
                )
            }'''

home_old = catalog_old.replace('onProduct', 'onClick')
home_new = catalog_new.replace('onProduct', 'onClick')

count = 0
if catalog_old in s:
    s = s.replace(catalog_old, catalog_new, 1)
    count += 1
if home_old in s:
    s = s.replace(home_old, home_new, 1)
    count += 1

if count != 2:
    raise SystemExit(f'Expected to normalize 2 loop action rows, normalized {count}')

p.write_text(s)

# Make the hotfix unmistakable on-device while keeping the feature release at 1.0.4.
g = Path('android-v0.1/app/build.gradle.kts')
gs = g.read_text()
gs = gs.replace('versionCode = 104', 'versionCode = 105', 1)
gs = gs.replace('versionName = "1.0.4"', 'versionName = "1.0.4.1"', 1)
g.write_text(gs)

api = Path('android-v0.1/app/src/main/java/ro/autoid/app/data/AutoIdApi.kt')
asrc = api.read_text().replace('AutoID-Android/1.0.4', 'AutoID-Android/1.0.4.1', 1)
api.write_text(asrc)

print('Normalized grouped/simple loop buttons to one exact 48dp component; Android 1.0.4.1 / code 105')
