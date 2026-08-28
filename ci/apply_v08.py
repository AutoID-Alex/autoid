from pathlib import Path
import base64, json, zlib

ROOT=Path('.')
# Restore full v0.8 sources/bridge from compact payload chunks.
payload=''.join((ROOT/f'ci/v08_source_{i:02d}.txt').read_text().strip() for i in range(3))
files=json.loads(zlib.decompress(base64.b64decode(payload)).decode())
for rel,text in files.items():
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(text)

# Patch v0.7 root navigation to the v0.8 native screens while preserving proven product-family logic.
p=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app/MainActivity.kt'
s=p.read_text()
s=s.replace('    var nativeResource by remember { mutableStateOf<SupportResource?>(null) }\n','    var nativeResource by remember { mutableStateOf<SupportResource?>(null) }\n    var showCheckout by remember { mutableStateOf(false) }\n',1)
s=s.replace('    if (nativeContent != null) {\n','    if (showCheckout) {\n        CheckoutV08(api, commerce, onBack={showCheckout=false}, onDone={commerce.clearCart();cartTick++;showCheckout=false;tab=Tab.Account})\n        return\n    }\n\n    if (nativeContent != null) {\n',1)
s=s.replace('        ProductList(\n','        ProductListV08(\n',1)
s=s.replace('            scan = scan\n        )\n        return\n    }\n','            scan = scan,\n            onHeaderCart = { category=null; tab=Tab.Cart }\n        )\n        return\n    }\n',1)
s=s.replace('Tab.Home -> HomeScreen(\n','Tab.Home -> HomeScreenV08(\n',1)
s=s.replace('                    onMenu = { menuOpen=true }\n                )','                    onMenu = { menuOpen=true },\n                    onHeaderCart = { tab=Tab.Cart }\n                )',1)
s=s.replace('Tab.Categories -> CategoriesScreen(\n','Tab.Categories -> CategoriesScreenV08(\n',1)
s=s.replace('                    onMenu = { menuOpen=true }\n                )','                    onMenu = { menuOpen=true },\n                    cartCount = commerce.cartCount(),\n                    onHeaderCart = { tab=Tab.Cart }\n                )',1)
s=s.replace('Tab.Cart -> CartScreen(commerce, onProduct = { selectedProduct = it }, onChanged = { cartTick++ })','Tab.Cart -> CartScreenV08(commerce, onProduct = { selectedProduct = it }, onChanged = { cartTick++ }, onCheckout = { showCheckout=true })',1)
s=s.replace('Tab.Account -> AccountScreen(api, session, commerce, onProduct = { selectedProduct = it })','Tab.Account -> AccountScreenV08(api, session, commerce, onProduct = { selectedProduct = it }, onHeaderCart = { tab=Tab.Cart })',1)
s=s.replace('''        floatingActionButton = {\n            FloatingActionButton(onClick = { aiProductId=null; showAi=true }, containerColor = AutoIdOrange, contentColor = Color.White) {\n                Icon(Icons.Default.SmartToy, contentDescription = "AutoID AI")\n            }\n        }\n''','',1)
old='''                Row(verticalAlignment = Alignment.CenterVertically) {\n                    IconButton(onClick = onFavorite) { Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "Favorite", tint = if (favorite) AutoIdOrange else LocalContentColor.current) }\n                    Button(onClick = onCart, enabled = p.inStock, contentPadding = PaddingValues(horizontal = 12.dp)) { Icon(Icons.Default.AddShoppingCart, null); Spacer(Modifier.width(4.dp)); Text("Adaugă") }\n                }'''
new='''                Row(verticalAlignment = Alignment.CenterVertically) {\n                    IconButton(onClick = onFavorite) { Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "Favorite", tint = if (favorite) AutoIdOrange else LocalContentColor.current) }\n                    if (p.groupedChildIds.isNotEmpty()) FilledTonalButton(onClick = onClick) { Text("Variante") }\n                    else Button(onClick = onCart, enabled = p.inStock, contentPadding = PaddingValues(horizontal = 12.dp)) { Icon(Icons.Default.AddShoppingCart, null); Spacer(Modifier.width(4.dp)); Text("Adaugă") }\n                }'''
s=s.replace(old,new,1)
p.write_text(s)

# Version and launcher branding. Raster assets are downloaded during CI then bundled into the APK.
p=ROOT/'android-v0.1/app/build.gradle.kts'
s=p.read_text().replace('versionCode = 6','versionCode = 8').replace('versionName = "0.6.0"','versionName = "0.8.0"')
p.write_text(s)
p=ROOT/'android-v0.1/app/src/main/AndroidManifest.xml'
s=p.read_text().replace('android:icon="@drawable/ic_autoid"','android:icon="@drawable/autoid_icon"').replace('android:roundIcon="@drawable/ic_autoid"','android:roundIcon="@drawable/autoid_icon"')
p.write_text(s)

release='''# AutoID Professional Solutions v0.8.0\n\nNative commerce/UIX release. AI integration is intentionally deferred.\n\n- AutoID icon/logo bundled locally in the generated APK.\n- Home: grouped products only in the 8 requested categories, ordered by summed child `stock_autoid`.\n- Native child-category chips.\n- Functional native header cart navigation.\n- Native checkout with Company, VAT, COD, bank transfer and guarded Stripe option.\n- Native registration and improved account UI with Google sign-in entry point.\n- Native Analytics/Marketing privacy preferences.\n- v0.7 grouped parent/child + product_tag relationship logic preserved.\n'''
(ROOT/'RELEASE-v0.8.0.md').write_text(release)
print('Applied AutoID v0.8.0 native commerce/UIX migration')
