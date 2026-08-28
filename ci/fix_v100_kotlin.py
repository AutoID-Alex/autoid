from pathlib import Path

p = Path('android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt')
s = p.read_text()

# Keep the bottom navigation explicit so the Kotlin parser does not have to
# disambiguate a deeply nested one-line composable expression.
start = s.index('@Composable private fun V100Bottom')
end = s.index('@Composable private fun V100Menu', start)
replacement = '''@Composable
private fun V100Bottom(tab: V100Tab, count: Int, onTab: (V100Tab) -> Unit) {
    NavigationBar(
        containerColor = Color.White,
        tonalElevation = 10.dp,
        modifier = Modifier.navigationBarsPadding()
    ) {
        V100Tab.entries.forEach { item ->
            NavigationBarItem(
                selected = tab == item,
                onClick = { onTab(item) },
                icon = {
                    if (item == V100Tab.Ai) {
                        Surface(
                            shape = CircleShape,
                            color = AutoIdOrange,
                            shadowElevation = 5.dp,
                            modifier = Modifier.size(48.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(Icons.Default.SmartToy, contentDescription = "AI", tint = Color.White)
                            }
                        }
                    } else {
                        BadgedBox(
                            badge = {
                                if (item == V100Tab.Cart && count > 0) {
                                    Badge(containerColor = AutoIdOrange) { Text(count.toString()) }
                                }
                            }
                        ) {
                            val icon = when (item) {
                                V100Tab.Home -> Icons.Default.Home
                                V100Tab.Categories -> Icons.Default.GridView
                                V100Tab.Cart -> Icons.Default.ShoppingCart
                                V100Tab.Account -> Icons.Default.Person
                                V100Tab.Ai -> Icons.Default.SmartToy
                            }
                            Icon(icon, contentDescription = item.label)
                        }
                    }
                },
                label = {
                    Text(
                        if (item == V100Tab.Ai) "AI" else item.label,
                        fontSize = 10.sp
                    )
                },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = AutoIdOrange,
                    selectedTextColor = AutoIdOrange,
                    indicatorColor = Color(0xFFFFF1E8)
                )
            )
        }
    }
}

'''
s = s[:start] + replacement + s[end:]

# CatalogV100 was initially generated as one very long expression. Rewrite it
# as normal Kotlin blocks; besides being readable, this removes the brace/parser
# ambiguity that stopped compileDebugKotlin.
start = s.index('@Composable fun CatalogV100')
end = s.index('@Composable private fun SortMenu', start)
replacement = '''@Composable
fun CatalogV100(
    api: AutoIdApi,
    commerce: CommerceStore,
    category: ProductCategory?,
    initialSearch: String,
    onBack: () -> Unit,
    onProduct: (Product) -> Unit,
    onFavorite: (Product) -> Unit,
    onCart: (Product) -> Unit,
    onRfq: (Product) -> Unit,
    onAi: () -> Unit,
    onFavorites: () -> Unit,
    onHeaderCart: () -> Unit,
    scan: ((String) -> Unit) -> Unit
) {
    var q by remember(category?.id) { mutableStateOf(initialSearch) }
    var products by remember { mutableStateOf<List<Product>>(emptyList()) }
    var facets by remember { mutableStateOf<CatalogFacets?>(null) }
    var active by remember(category?.id) { mutableStateOf(category) }
    var brand by remember { mutableStateOf<Long?>(null) }
    var model by remember { mutableStateOf<Long?>(null) }
    var min by remember { mutableStateOf<Double?>(null) }
    var max by remember { mutableStateOf<Double?>(null) }
    var sort by remember { mutableStateOf("stock_autoid") }
    var page by remember { mutableIntStateOf(1) }
    var loading by remember { mutableStateOf(false) }
    var filters by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    suspend fun load(reset: Boolean) {
        loading = true
        error = null
        if (reset) page = 1
        val rows = runCatching {
            withContext(Dispatchers.IO) {
                api.catalogProducts(q, active?.id, page, sort, brand, model, min, max)
            }
        }.onFailure {
            error = it.message
        }.getOrDefault(emptyList())
        products = if (reset) rows else products + rows
        loading = false
    }

    LaunchedEffect(category?.id) {
        facets = runCatching {
            withContext(Dispatchers.IO) { api.catalogFacets(category?.id) }
        }.getOrNull()
    }
    LaunchedEffect(active?.id, brand, model, min, max, sort) { load(true) }
    LaunchedEffect(q) {
        delay(350)
        load(true)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 14.dp)
            .statusBarsPadding()
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) {
                Icon(Icons.Default.ArrowBack, contentDescription = "Înapoi")
            }
            Text(
                category?.name ?: "Categorii produse",
                fontSize = 20.sp,
                fontWeight = FontWeight.ExtraBold,
                modifier = Modifier.weight(1f),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            IconButton(onClick = onFavorites) {
                Icon(Icons.Default.FavoriteBorder, contentDescription = "Favorite")
            }
            IconButton(onClick = onHeaderCart) {
                BadgedBox(
                    badge = {
                        if (commerce.cartCount() > 0) {
                            Badge(containerColor = AutoIdOrange) {
                                Text(commerce.cartCount().toString())
                            }
                        }
                    }
                ) {
                    Icon(Icons.Default.ShoppingCart, contentDescription = "Coș")
                }
            }
        }

        SmartSearch(
            api = api,
            value = q,
            onValue = { q = it },
            onSubmit = { q = it },
            scan = scan,
            placeholder = if (category == null) {
                "Caută în catalog..."
            } else {
                "Caută în ${category.name}..."
            }
        )

        val subs = facets?.subcategories.orEmpty()
        if (subs.isNotEmpty()) {
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.padding(vertical = 8.dp)
            ) {
                item {
                    FilterChip(
                        selected = active?.id == category?.id,
                        onClick = { active = category },
                        label = { Text("Toate") }
                    )
                }
                items(subs) { c ->
                    FilterChip(
                        selected = active?.id == c.id,
                        onClick = { active = c },
                        label = { Text(c.name) }
                    )
                }
            }
        }

        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.padding(bottom = 8.dp)
        ) {
            OutlinedButton(onClick = { filters = true }) {
                Icon(Icons.Default.Tune, contentDescription = null)
                Spacer(Modifier.width(6.dp))
                Text("Filtre")
            }
            SortMenu(sort) { sort = it }
            AssistChip(
                onClick = onAi,
                label = { Text("AI") },
                leadingIcon = { Icon(Icons.Default.SmartToy, contentDescription = null) }
            )
        }

        error?.let {
            Text(it, color = MaterialTheme.colorScheme.error, fontSize = 12.sp)
        }

        Box(Modifier.weight(1f)) {
            LazyVerticalGrid(
                columns = GridCells.Fixed(2),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
                contentPadding = PaddingValues(bottom = 120.dp)
            ) {
                gridItems(products, key = { it.id }) { product ->
                    CatalogCard(
                        p = product,
                        favorite = commerce.isFavorite(product.id),
                        onProduct = { onProduct(product) },
                        onFavorite = { onFavorite(product) },
                        onCart = { onCart(product) },
                        onRfq = { onRfq(product) }
                    )
                }
                if (products.isNotEmpty()) {
                    item {
                        OutlinedButton(
                            onClick = {
                                page++
                                scope.launch { load(false) }
                            },
                            enabled = !loading,
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(50.dp)
                        ) {
                            Text(if (loading) "Se încarcă..." else "Încarcă mai multe")
                        }
                    }
                }
            }

            if (loading && products.isEmpty()) {
                CircularProgressIndicator(
                    modifier = Modifier.align(Alignment.Center),
                    color = AutoIdOrange
                )
            }
        }
    }

    if (filters) {
        FilterSheet(
            f = facets,
            brand = brand,
            model = model,
            min = min,
            max = max,
            onApply = { b, m, mi, ma ->
                brand = b
                model = m
                min = mi
                max = ma
                filters = false
            },
            onDismiss = { filters = false }
        )
    }
}

'''
s = s[:start] + replacement + s[end:]

p.write_text(s)
print('Fixed V100Bottom and CatalogV100 Kotlin parser issues')
