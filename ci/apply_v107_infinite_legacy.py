from pathlib import Path

p=Path('android-v0.1/app/src/main/java/ro/autoid/app/MainActivity.kt')
s=p.read_text()
if 'import androidx.compose.foundation.lazy.rememberLazyListState' not in s:
    s=s.replace('import androidx.compose.foundation.lazy.LazyRow\n','import androidx.compose.foundation.lazy.LazyRow\nimport androidx.compose.foundation.lazy.rememberLazyListState\n',1)
start=s.find('@Composable\nfun ProductList(')
end=s.find('@Composable\nfun ProductCard(',start)
if start<0 or end<0: raise SystemExit('MainActivity ProductList boundaries missing')
new=r'''@Composable
fun ProductList(
    api: AutoIdApi,
    commerce: CommerceStore,
    category: ProductCategory?,
    initialSearch: String,
    onBack: () -> Unit,
    onProduct: (Product) -> Unit,
    onCart: (Product) -> Unit,
    onFavorite: (Product) -> Unit,
    scan: ((String) -> Unit) -> Unit
) {
    var q by remember { mutableStateOf(initialSearch) }
    var products by remember { mutableStateOf<List<Product>>(emptyList()) }
    var loading by remember { mutableStateOf(false) }
    var canLoadMore by remember { mutableStateOf(true) }
    var error by remember { mutableStateOf<String?>(null) }
    var page by remember { mutableIntStateOf(1) }
    var sort by remember { mutableStateOf("date") }
    val listState = rememberLazyListState()

    suspend fun load(reset: Boolean) {
        if (loading) return
        loading = true
        error = null
        if (reset) { page = 1; canLoadMore = true }
        val rows = runCatching {
            withContext(Dispatchers.IO) { api.products(q, category?.id?.takeIf { it > 0 }, page, sort) }
        }.onFailure { error = it.message }.getOrDefault(emptyList())
        if (reset) products = rows.distinctBy { it.id }
        else {
            val ids = products.map { it.id }.toHashSet()
            val fresh = rows.filterNot { it.id in ids }
            products = products + fresh
            if (fresh.isEmpty()) canLoadMore = false
        }
        if (rows.size < 20) canLoadMore = false
        loading = false
    }

    LaunchedEffect(category?.id, initialSearch, sort) { load(true) }
    LaunchedEffect(q) { delay(450); load(true) }
    val shouldLoadMore by remember {
        derivedStateOf {
            val last = listState.layoutInfo.visibleItemsInfo.lastOrNull()?.index ?: -1
            canLoadMore && !loading && products.isNotEmpty() && last >= products.lastIndex - 3
        }
    }
    LaunchedEffect(shouldLoadMore) { if (shouldLoadMore) { page++; load(false) } }

    Column(Modifier.fillMaxSize().padding(16.dp).statusBarsPadding()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            TextButton(onClick = onBack) { Text("‹") }
            Column(Modifier.weight(1f)) {
                Text(category?.name ?: "Produse", fontSize = 22.sp, fontWeight = FontWeight.ExtraBold)
                Text("Scroll continuu", fontSize = 11.sp, color = Color(0xFF667085))
            }
        }
        SearchBarBox(q, { q = it }, {}, { scan { q = it } }, "Caută în categorie...")
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(selected = sort == "date", onClick = { sort = "date" }, label = { Text("Recomandate") })
            FilterChip(selected = sort == "price", onClick = { sort = "price" }, label = { Text("Preț") })
            FilterChip(selected = sort == "popularity", onClick = { sort = "popularity" }, label = { Text("Populare") })
        }
        if (loading && products.isEmpty()) LinearProgressIndicator(Modifier.fillMaxWidth())
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        LazyColumn(
            state = listState,
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(vertical = 12.dp)
        ) {
            items(products, key = { it.id }) { p ->
                ProductCard(p, commerce.isFavorite(p.id), { onProduct(p) }, { onCart(p) }, { onFavorite(p) })
            }
            if (loading && products.isNotEmpty()) item {
                Box(Modifier.fillMaxWidth().height(48.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(Modifier.size(22.dp), strokeWidth = 2.dp, color = AutoIdOrange)
                }
            }
        }
    }
}

'''
s=s[:start]+new+s[end:]
p.write_text(s)
print('Applied v1.0.7 infinite scroll to legacy ProductList')

# Checkout compile compatibility after the v1.0.7 UI migration.
p=Path('android-v0.1/app/src/main/java/ro/autoid/app/V08Screens.kt')
s=p.read_text()
rounded='import androidx.compose.foundation.shape.RoundedCornerShape\n'
if 'import androidx.compose.foundation.shape.CircleShape\n' not in s:
    if rounded not in s: raise SystemExit('RoundedCornerShape import anchor missing')
    s=s.replace(rounded, rounded+'import androidx.compose.foundation.shape.CircleShape\n', 1)
modifier='import androidx.compose.ui.Modifier\n'
if 'import androidx.compose.ui.draw.clip\n' not in s:
    if modifier not in s: raise SystemExit('Modifier import anchor missing')
    s=s.replace(modifier, modifier+'import androidx.compose.ui.draw.clip\n', 1)
if 'import androidx.compose.ui.layout.ContentScale\n' not in s:
    clip='import androidx.compose.ui.draw.clip\n'
    s=s.replace(clip, clip+'import androidx.compose.ui.layout.ContentScale\n', 1)
s=s.replace('color = Ink', 'color = Color(0xFF101828)')
s=s.replace('color=Ink', 'color=Color(0xFF101828)')
s=s.replace('else Ink', 'else Color(0xFF101828)')
p.write_text(s)
print('Fixed v1.0.7 checkout Compose imports and color scope')
