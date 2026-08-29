from pathlib import Path
p=Path('android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt')
s=p.read_text()

# Root Home call: add RFQ callback after cart callback.
old='''::openCategory,::openProduct,{commerce.toggleFavorite(it.id);favTick++},{addCart(it)},{ai=true}'''
new='''::openCategory,::openProduct,{commerce.toggleFavorite(it.id);favTick++},{addCart(it)},{addRfq(it)},{ai=true}'''
if old not in s: raise SystemExit('root HomeV100 callback anchor missing')
s=s.replace(old,new,1)

# HomeV100 signature: add onRfq.
old='''onFavorite:(Product)->Unit,onCart:(Product)->Unit,onAi:()->Unit'''
new='''onFavorite:(Product)->Unit,onCart:(Product)->Unit,onRfq:(Product)->Unit,onAi:()->Unit'''
if old not in s: raise SystemExit('HomeV100 signature anchor missing')
s=s.replace(old,new,1)

# Both Home loops: append RFQ callback to HomeCard.
s=s.replace('''{onFavorite(p)},{onCart(p)})''','''{onFavorite(p)},{onCart(p)},{onRfq(p)})''',2)

# HomeCard signature and button action.
old='''onFavorite: () -> Unit,
    onCart: () -> Unit
) {'''
new='''onFavorite: () -> Unit,
    onCart: () -> Unit,
    onRfq: () -> Unit
) {'''
if old not in s: raise SystemExit('HomeCard signature anchor missing')
s=s.replace(old,new,1)
s=s.replace('''OutlinedButton(onClick = onClick, modifier = Modifier.weight(1f).height(44.dp), contentPadding = PaddingValues(horizontal = 4.dp)) {
                    Text("Cerere ofertă", fontSize = 10.sp)
                }''','''OutlinedButton(onClick = onRfq, modifier = Modifier.weight(1f).height(44.dp), contentPadding = PaddingValues(horizontal = 4.dp)) {
                    Text("Cerere ofertă", fontSize = 10.sp)
                }''',1)

# Related-product HomeCard inside ProductV100 must also receive its actual RFQ callback.
old='''HomeCard(r,commerce.isFavorite(r.id),{onOpen(r)},{onFavorite(r)},{onCart(r,1)})'''
new='''HomeCard(r,commerce.isFavorite(r.id),{onOpen(r)},{onFavorite(r)},{onCart(r,1)},{onRfq(r,1)})'''
if old in s:
    s=s.replace(old,new,1)

p.write_text(s)
print('Wired v1.0.2 Home RFQ callbacks')
