from pathlib import Path

p = Path('android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt')
s = p.read_text()

start = s.find('@Composable\nfun AutoIdAppV100(')
if start < 0:
    start = s.find('@Composable\r\nfun AutoIdAppV100(')
if start < 0:
    raise SystemExit('AutoIdAppV100 root start missing')

end_marker = '@Composable private fun LoadingScreenV100()'
end = s.find(end_marker, start)
if end < 0:
    raise SystemExit('LoadingScreenV100 boundary missing')

root = r'''@Composable
fun AutoIdAppV100(
    api: AutoIdApi,
    session: SessionStore,
    commerce: CommerceStore,
    scan: ((String) -> Unit) -> Unit
) {
    var ready by rememberSaveable { mutableStateOf(HomeBootstrapV104.loaded) }
    var tab by remember { mutableStateOf(V100Tab.Home) }
    var category by remember { mutableStateOf<ProductCategory?>(null) }
    var selected by remember { mutableStateOf<Product?>(null) }
    var search by remember { mutableStateOf("") }
    var menu by remember { mutableStateOf(false) }
    var favorites by remember { mutableStateOf(false) }
    var notifications by remember { mutableStateOf(false) }
    var checkout by remember { mutableStateOf(false) }
    var ai by remember { mutableStateOf(false) }
    var consult by remember { mutableStateOf(false) }
    var rfq by remember { mutableStateOf(false) }
    var rfqLines by remember { mutableStateOf<List<CartLine>>(emptyList()) }
    var miniCart by remember { mutableStateOf(false) }
    var cartTick by remember { mutableIntStateOf(0) }
    var favTick by remember { mutableIntStateOf(0) }

    LaunchedEffect(Unit) {
        if (!HomeBootstrapV104.loaded) {
            HomeBootstrapV104.data = runCatching {
                withContext(Dispatchers.IO) { api.homeData() }
            }.getOrNull()
            HomeBootstrapV104.loaded = true
        }
        ready = true
    }
    if (!ready) {
        LoadingScreenV100()
        return
    }

    fun addCart(p: Product, q: Int = 1) {
        commerce.addToCart(p, q)
        cartTick++
        miniCart = true
    }
    fun addRfq(p: Product, q: Int = 1) {
        val x = rfqLines.toMutableList()
        val i = x.indexOfFirst { it.product.id == p.id }
        if (i >= 0) x[i] = x[i].copy(quantity = x[i].quantity + q) else x += CartLine(p, q)
        rfqLines = x
        rfq = true
    }
    fun openProduct(p: Product) {
        commerce.addRecent(p)
        selected = p
        category = null
        favorites = false
    }
    fun openCategory(c: ProductCategory) {
        category = c
        selected = null
        tab = V100Tab.Categories
        favorites = false
    }

    if (checkout) {
        CheckoutV08(
            api,
            commerce,
            onBack = { checkout = false },
            onDone = {
                commerce.clearCart()
                cartTick++
                checkout = false
                tab = V100Tab.Account
            }
        )
        return
    }
    if (ai) {
        NativeAiChatScreen(api, null) { ai = false }
        return
    }

    val drawer = rememberDrawerState(DrawerValue.Closed)
    LaunchedEffect(menu) {
        if (menu) drawer.open() else drawer.close()
    }

    ModalNavigationDrawer(
        drawerState = drawer,
        gesturesEnabled = menu,
        drawerContent = {
            V100Menu(
                api,
                { menu = false },
                {
                    menu = false
                    tab = V100Tab.Home
                    category = null
                    selected = null
                },
                { menu = false; openCategory(it) },
                { menu = false; favorites = true },
                { menu = false; notifications = true },
                { menu = false; consult = true },
                { menu = false; ai = true }
            )
        }
    ) {
        Scaffold(
            containerColor = Color.White,
            bottomBar = {
                V100Bottom(tab, commerce.cartCount()) { t ->
                    if (t == V100Tab.Ai) {
                        ai = true
                    } else {
                        tab = t
                        selected = null
                        if (t != V100Tab.Categories) category = null
                        favorites = false
                        notifications = false
                    }
                }
            }
        ) { pad ->
            Box(Modifier.padding(pad).fillMaxSize()) {
                when {
                    favorites -> FavoritesV100(
                        api,
                        commerce,
                        { favorites = false },
                        ::openProduct,
                        { tab = V100Tab.Cart; favorites = false }
                    )
                    notifications -> NotificationsV100(
                        { notifications = false },
                        { tab = V100Tab.Cart; notifications = false }
                    )
                    selected != null -> ProductV100(
                        selected!!,
                        api,
                        commerce,
                        { selected = null },
                        { commerce.toggleFavorite(it.id); favTick++ },
                        { p, q -> addCart(p, q) },
                        { p, q -> addRfq(p, q) },
                        ::openProduct,
                        { ai = true },
                        { tab = V100Tab.Cart; selected = null }
                    )
                    category != null -> CatalogV100(
                        api = api,
                        commerce = commerce,
                        category = category!!,
                        initialSearch = search,
                        onBack = { category = null },
                        onSubcategory = ::openCategory,
                        onProduct = ::openProduct,
                        onFavorite = { product ->
                            commerce.toggleFavorite(product.id)
                            favTick++
                        },
                        onCart = { product -> addCart(product) },
                        onRfq = { product -> addRfq(product) },
                        onAi = { ai = true },
                        onFavorites = { favorites = true },
                        onHeaderCart = {
                            tab = V100Tab.Cart
                            category = null
                        },
                        scan = scan
                    )
                    else -> when (tab) {
                        V100Tab.Home -> HomeV100(
                            api = api,
                            commerce = commerce,
                            onMenu = { menu = true },
                            onSearch = { value ->
                                search = value
                                category = ProductCategory(0, "Rezultate", 0)
                            },
                            onCategory = ::openCategory,
                            onProduct = ::openProduct,
                            onFavorite = { product ->
                                commerce.toggleFavorite(product.id)
                                favTick++
                            },
                            onCart = { product -> addCart(product) },
                            onRfq = { product -> addRfq(product) },
                            onAi = { ai = true },
                            onConsult = { consult = true },
                            onFavorites = { favorites = true },
                            onNotifications = { notifications = true },
                            onFullCart = { tab = V100Tab.Cart },
                            mini = miniCart,
                            onMini = { value -> miniCart = value },
                            scan = scan,
                            cartTick = cartTick
                        )
                        V100Tab.Categories -> CategoriesV101(
                            api,
                            commerce,
                            { tab = V100Tab.Home },
                            ::openCategory,
                            ::openProduct,
                            { favorites = true },
                            { tab = V100Tab.Cart },
                            scan
                        )
                        V100Tab.Cart -> CartV100(
                            commerce,
                            ::openProduct,
                            { cartTick++ },
                            { checkout = true }
                        )
                        V100Tab.Account -> AccountScreenV08(
                            api,
                            session,
                            commerce,
                            ::openProduct
                        ) { tab = V100Tab.Cart }
                        V100Tab.Ai -> Unit
                    }
                }
            }
        }
    }

    if (rfq) RfqV100(
        api,
        rfqLines,
        { rfqLines = it },
        { rfq = false },
        { rfqLines = emptyList(); rfq = false }
    )
    if (consult) ConsultV100(api) { consult = false }
}

'''

s = s[:start] + root + s[end:]
p.write_text(s)

# Fail fast if state variables were accidentally dropped again.
check = s[start:s.find(end_marker, start)]
for name in ['var tab', 'var category', 'var rfqLines', 'var cartTick', 'var miniCart']:
    if name not in check:
        raise SystemExit(f'root state validation failed: {name}')

print('Rebuilt AutoIdAppV100 root deterministically for v1.0.4')
