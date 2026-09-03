package ro.autoid.app

import android.content.Context
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.rememberLazyGridState
import androidx.compose.foundation.lazy.grid.items as gridItems
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.async
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import ro.autoid.app.data.*
import ro.autoid.app.ui.theme.AutoIdOrange
import kotlin.math.roundToInt

private val Ink=Color(0xFF101828)
private val Muted=Color(0xFF667085)
private val Soft=Color(0xFFF8FAFC)
private val Good=Color(0xFF12B76A)
private val Warn=Color(0xFFF79009)

private object HomeBootstrapV104 {
    @Volatile var loaded: Boolean = false
    @Volatile var data: HomeV100Data? = null
    @Volatile var heroSlides: List<HeroSlideV103> = emptyList()
}
private class HomeDiskCacheV126(context:Context,private val api:AutoIdApi){private val p=context.getSharedPreferences("autoid_home_cache_v126",Context.MODE_PRIVATE);fun load(){if(HomeBootstrapV104.data==null)p.getString("home",null)?.let{runCatching{api.homeDataFromJsonV126(it)}.getOrNull()?.let{x->HomeBootstrapV104.data=x}};if(HomeBootstrapV104.heroSlides.isEmpty())p.getString("hero",null)?.let{runCatching{api.heroSlidesFromJsonV126(it)}.getOrNull()?.let{x->HomeBootstrapV104.heroSlides=x}}};fun saveHome(raw:String){p.edit().putString("home",raw).putLong("home_at",System.currentTimeMillis()).apply()};fun saveHero(raw:String){p.edit().putString("hero",raw).putLong("hero_at",System.currentTimeMillis()).apply()}}

enum class V100Tab(val label:String){Home("Acasă"),Categories("Categorii"),Ai("AI Assistant"),Cart("Coș"),Account("Contul meu")}

@Composable
fun AutoIdAppV100(
    api: AutoIdApi,
    session: SessionStore,
    commerce: CommerceStore,
    scan: ((String) -> Unit) -> Unit
) {
    val appContext=LocalContext.current
    val homeDisk=remember{HomeDiskCacheV126(appContext,api).also{it.load()}}
    var ready by rememberSaveable { mutableStateOf(HomeBootstrapV104.data != null) }
    var reviewOrderId by remember{mutableLongStateOf(session.pendingReviewOrderId)}
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
        if (!ready) {
            val raw=withContext(Dispatchers.IO){runCatching{api.homeDataJsonV126()}.getOrNull()};raw?.let{runCatching{api.homeDataFromJsonV126(it)}.getOrNull()?.let{x->HomeBootstrapV104.data=x;homeDisk.saveHome(it)}};ready=true
        }
        launch(Dispatchers.IO){runCatching{api.homeDataJsonV126()}.getOrNull()?.let{raw->runCatching{api.homeDataFromJsonV126(raw)}.getOrNull()?.let{x->HomeBootstrapV104.data=x;homeDisk.saveHome(raw)}}}
        launch(Dispatchers.IO){runCatching{api.heroSlidesJsonV126()}.getOrNull()?.let{raw->runCatching{api.heroSlidesFromJsonV126(raw)}.getOrNull()?.let{x->HomeBootstrapV104.heroSlides=x;homeDisk.saveHero(raw)}}}
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

    if(reviewOrderId>0){OrderReviewScreenV126(api,session,reviewOrderId,{session.pendingReviewOrderId=0;reviewOrderId=0});return}
    if (checkout) {
        CheckoutV117(
            api,
            session,
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
                V100Bottom(tab, commerce.cartCount(), cartTick) { t ->
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
                        session,
                        commerce,
                        { selected = null },
                        { commerce.toggleFavorite(it.id); favTick++ },
                        { p, q -> addCart(p, q) },
                        { p, q -> addRfq(p, q) },
                        ::openProduct,
                        { ai = true },
                        { notifications = true },
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
                        onNotifications = { notifications = true },
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
                            onAllCategories = {
                                tab = V100Tab.Categories
                                category = null
                                selected = null
                            },
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
                            { notifications = true },
                            { tab = V100Tab.Cart },
                            scan
                        )
                        V100Tab.Cart -> CartV114(
                            api,
                            commerce,
                            ::openProduct,
                            { cartTick++ },
                            { checkout = true },
                            { favorites = true },
                            { notifications = true }
                        )
                        V100Tab.Account -> AccountV117(
                            api,
                            session,
                            commerce,
                            ::openProduct,
                            { tab = V100Tab.Cart },
                            { favorites = true },
                            { notifications = true }
                        )
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

@Composable private fun LoadingScreenV100(){Box(Modifier.fillMaxSize().background(Color.White).statusBarsPadding(),contentAlignment=Alignment.Center){Column(horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(14.dp)){Image(painterResource(R.drawable.autoid_logo_transparent),"AutoID",Modifier.width(270.dp).height(90.dp),contentScale=ContentScale.Fit);Text("Bine ai venit!",fontSize=25.sp,fontWeight=FontWeight.ExtraBold,color=Ink);Text("Soluții profesionale pentru identificare automată",color=Muted);Spacer(Modifier.height(4.dp));AutoIdPulseLoaderV112(compact=true,label="")}}}

@Composable
private fun V100Bottom(tab: V100Tab, count: Int, cartTick: Int, onTab: (V100Tab) -> Unit) {
    var cartPulse by remember { mutableStateOf(false) }
    LaunchedEffect(cartTick) {
        if (cartTick > 0) {
            cartPulse = true
            delay(420)
            cartPulse = false
        }
    }
    val cartIconSize by androidx.compose.animation.core.animateDpAsState(
        targetValue = if (cartPulse) 31.dp else 24.dp,
        label = "cartFooterPulse"
    )
    val cartBadgeSize by androidx.compose.animation.core.animateDpAsState(
        targetValue = if (cartPulse) 23.dp else 18.dp,
        label = "cartBadgePulse"
    )

    NavigationBar(
        containerColor = Color.White,
        tonalElevation = 8.dp,
        modifier = Modifier.navigationBarsPadding().height(78.dp)
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
                            shadowElevation = 7.dp,
                            modifier = Modifier.size(50.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(Icons.Default.SmartToy, contentDescription = "AI", tint = Color.White)
                            }
                        }
                    } else {
                        BadgedBox(
                            badge = {
                                if (item == V100Tab.Cart && count > 0) {
                                    Badge(
                                        containerColor = AutoIdOrange,
                                        modifier = Modifier.size(cartBadgeSize)
                                    ) { Text(count.toString(), fontSize = 9.sp) }
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
                            if (item == V100Tab.Cart) {
                                Surface(
                                    shape = CircleShape,
                                    color = if (cartPulse) Color(0xFFFFE9D9) else Color.Transparent
                                ) {
                                    Icon(
                                        icon,
                                        contentDescription = item.label,
                                        tint = if (cartPulse || tab == item) AutoIdOrange else Ink,
                                        modifier = Modifier.padding(4.dp).size(cartIconSize)
                                    )
                                }
                            } else {
                                Icon(icon, contentDescription = item.label)
                            }
                        }
                    }
                },
                label = { Text(if (item == V100Tab.Ai) "AI" else item.label, fontSize = 10.sp) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = AutoIdOrange,
                    selectedTextColor = AutoIdOrange,
                    indicatorColor = Color(0xFFFFF1E8)
                )
            )
        }
    }
}

@Composable private fun V100Menu(api:AutoIdApi,onClose:()->Unit,onHome:()->Unit,onCategory:(ProductCategory)->Unit,onFavorites:()->Unit,onNotifications:()->Unit,onConsult:()->Unit,onAi:()->Unit){var cats by remember{mutableStateOf<List<ProductCategory>>(emptyList())};var expanded by remember{mutableStateOf(true)};LaunchedEffect(Unit){cats=runCatching{withContext(Dispatchers.IO){api.categories()}}.getOrDefault(emptyList())};ModalDrawerSheet(drawerContainerColor=Color.White,modifier=Modifier.width(330.dp)){Column(Modifier.fillMaxSize().padding(18.dp).statusBarsPadding()){Row(verticalAlignment=Alignment.CenterVertically){Image(painterResource(R.drawable.autoid_logo_transparent),"AutoID",Modifier.width(180.dp).height(58.dp),contentScale=ContentScale.Fit);Spacer(Modifier.weight(1f));IconButton(onClick=onClose){Icon(Icons.Default.Close,"Închide")}};HorizontalDivider();Spacer(Modifier.height(8.dp));MenuRow(Icons.Default.Home,"Acasă",onHome);MenuRow(Icons.Default.Inventory2,"Produse",{expanded=!expanded},if(expanded)Icons.Default.ExpandLess else Icons.Default.ExpandMore);AnimatedVisibility(expanded){Column{cats.forEach{c->Text(c.name,Modifier.fillMaxWidth().clickable{onCategory(c)}.padding(start=46.dp,top=9.dp,bottom=9.dp),fontSize=14.sp)}}};MenuRow(Icons.Default.FavoriteBorder,"Favorite",onFavorites);MenuRow(Icons.Default.NotificationsNone,"Notificări",onNotifications);MenuRow(Icons.Default.SupportAgent,"Consultanță tehnică",onConsult);MenuRow(Icons.Default.SmartToy,"Asistent AutoID AI",onAi);Spacer(Modifier.weight(1f));Text("AutoID · Professional Solutions",fontSize=12.sp,color=Muted)}}}
@Composable private fun MenuRow(icon:androidx.compose.ui.graphics.vector.ImageVector,label:String,onClick:()->Unit,trailing:androidx.compose.ui.graphics.vector.ImageVector?=null){Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).clickable(onClick=onClick).padding(12.dp),verticalAlignment=Alignment.CenterVertically){Icon(icon,null,tint=Ink);Spacer(Modifier.width(12.dp));Text(label,Modifier.weight(1f),fontWeight=FontWeight.SemiBold);trailing?.let{Icon(it,null)}}}

@Composable
private fun HomeHeader(
    commerce: CommerceStore,
    onMenu: () -> Unit,
    onFav: () -> Unit,
    onNotif: () -> Unit,
    onCart: () -> Unit,
    mini: Boolean,
    onMini: (Boolean) -> Unit,
    tick: Int
) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        IconButton(onClick = onMenu) { Icon(Icons.Default.Menu, "Meniu", Modifier.size(28.dp)) }
        Spacer(Modifier.width(6.dp))
        Image(
            painterResource(R.drawable.autoid_logo_transparent),
            "AutoID",
            Modifier.width(126.dp).height(46.dp),
            contentScale = ContentScale.Fit
        )
        Spacer(Modifier.weight(1f))
        IconButton(onClick = onFav) { Icon(Icons.Default.FavoriteBorder, "Favorite") }
        IconButton(onClick = onNotif) {
            BadgedBox(badge = { Badge(containerColor = AutoIdOrange) { Text("3") } }) {
                Icon(Icons.Default.NotificationsNone, "Notificări")
            }
        }
        Box {
            IconButton(onClick = { onMini(!mini) }) {
                BadgedBox(badge = { if (commerce.cartCount() > 0) Badge(containerColor = AutoIdOrange) { Text(commerce.cartCount().toString()) } }) {
                    Icon(Icons.Default.ShoppingCart, "Coș")
                }
            }
            MiniCart(commerce, mini, { onMini(false) }, onCart, tick)
        }
    }
}
private fun miniCartPriceV125(raw:String):String=raw.replace("&amp;nbsp;"," ",true).replace("&nbsp;"," ",true).replace("&#160;"," ",true).replace("&#xA0;"," ",true).replace('\u00A0',' ').replace(Regex("<[^>]+>"),"").replace(Regex("\\s+")," ").trim()
@Composable private fun MiniCart(commerce:CommerceStore,open:Boolean,onDismiss:()->Unit,onCart:()->Unit,tick:Int){DropdownMenu(expanded=open,onDismissRequest=onDismiss,modifier=Modifier.width(344.dp).clip(RoundedCornerShape(16.dp)).background(Color.White)){val lines=commerce.cart();Column(Modifier.fillMaxWidth().padding(horizontal=14.dp,vertical=10.dp),verticalArrangement=Arrangement.spacedBy(9.dp)){Row(verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text("Coșul meu",fontSize=17.sp,fontWeight=FontWeight.ExtraBold,color=Ink);Text("${commerce.cartCount()} produse",fontSize=10.sp,color=Muted)};if(lines.isNotEmpty())TextButton(onClick={commerce.clearCart();onDismiss()}){Text("Golește",fontSize=11.sp,color=AutoIdOrange)}};HorizontalDivider(color=Color(0xFFE8EAED));if(lines.isEmpty()){Box(Modifier.fillMaxWidth().padding(vertical=20.dp),contentAlignment=Alignment.Center){Text("Coșul este gol",color=Muted)}}else lines.take(4).forEach{l->Surface(shape=RoundedCornerShape(12.dp),color=Color(0xFFF8F9FB)){Row(Modifier.fillMaxWidth().padding(9.dp),verticalAlignment=Alignment.CenterVertically){AsyncImage(l.product.imageUrl,l.product.name,Modifier.size(48.dp).clip(RoundedCornerShape(9.dp)).background(Color.White).padding(3.dp),contentScale=ContentScale.Fit);Spacer(Modifier.width(9.dp));Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(3.dp)){Text(l.product.name,maxLines=2,overflow=TextOverflow.Ellipsis,fontSize=11.sp,fontWeight=FontWeight.Bold,color=Ink);Text("Cantitate: ${l.quantity}",fontSize=9.sp,color=Muted)};Spacer(Modifier.width(6.dp));Text(miniCartPriceV125(l.product.currentInclVat.ifBlank{l.product.price}),fontSize=11.sp,fontWeight=FontWeight.ExtraBold,color=AutoIdOrange)}}};if(lines.size>4)Text("+ ${lines.size-4} alte produse",fontSize=9.sp,color=Muted,modifier=Modifier.padding(start=4.dp));if(lines.isNotEmpty())Button(onClick={onDismiss();onCart()},modifier=Modifier.fillMaxWidth().height(48.dp),shape=RoundedCornerShape(10.dp)){Text("Vezi coșul",fontWeight=FontWeight.ExtraBold)}}}}

@Composable
private fun SmartSearch(
    api: AutoIdApi,
    value: String,
    onValue: (String) -> Unit,
    onSubmit: (String) -> Unit,
    onProduct: (Product) -> Unit,
    scan: ((String) -> Unit) -> Unit,
    placeholder: String = "Caută produse, SKU, brand, model..."
) {
    var suggestions by remember { mutableStateOf<List<Product>>(emptyList()) }
    var busy by remember { mutableStateOf(false) }
    LaunchedEffect(value) {
        delay(260)
        if (value.trim().length >= 2) {
            busy = true
            suggestions = runCatching {
                withContext(Dispatchers.IO) { api.searchSuggestions(value.trim()) }
            }.getOrDefault(emptyList())
            busy = false
        } else suggestions = emptyList()
    }
    Column {
        OutlinedTextField(
            value = value,
            onValueChange = onValue,
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            placeholder = { Text(placeholder) },
            leadingIcon = { Icon(Icons.Default.Search, null) },
            trailingIcon = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    if (busy) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp)
                    IconButton(onClick = { scan { onValue(it); onSubmit(it) } }) {
                        Icon(Icons.Default.QrCodeScanner, "Scanner")
                    }
                }
            },
            shape = RoundedCornerShape(16.dp)
        )
        AnimatedVisibility(suggestions.isNotEmpty()) {
            ElevatedCard(Modifier.fillMaxWidth().padding(top=4.dp),shape=RoundedCornerShape(14.dp)) {
                Column {
                    suggestions.take(6).forEach { product ->
                        Row(
                            Modifier.fillMaxWidth().clickable {
                                suggestions = emptyList()
                                onValue("")
                                onProduct(product)
                            }.padding(10.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            AsyncImage(product.imageUrl,product.name,Modifier.size(42.dp),contentScale=ContentScale.Fit)
                            Spacer(Modifier.width(8.dp))
                            Column(Modifier.weight(1f)) {
                                Text(product.name,maxLines=1,overflow=TextOverflow.Ellipsis,fontWeight=FontWeight.SemiBold)
                                Text(listOf(product.sku,product.brand,product.model).filter{it.isNotBlank()}.joinToString(" · "),fontSize=11.sp,color=Muted)
                            }
                        }
                        HorizontalDivider()
                    }
                }
            }
        }
    }
}

@Composable
fun HomeV100(
    api: AutoIdApi,
    commerce: CommerceStore,
    onMenu: () -> Unit,
    onSearch: (String) -> Unit,
    onCategory: (ProductCategory) -> Unit,
    onProduct: (Product) -> Unit,
    onFavorite: (Product) -> Unit,
    onCart: (Product) -> Unit,
    onRfq: (Product) -> Unit,
    onAi: () -> Unit,
    onConsult: () -> Unit,
    onFavorites: () -> Unit,
    onNotifications: () -> Unit,
    onFullCart: () -> Unit,
    onAllCategories: () -> Unit,
    mini: Boolean,
    onMini: (Boolean) -> Unit,
    scan: ((String) -> Unit) -> Unit,
    cartTick: Int
) {
    val homeContextV126=LocalContext.current
    val homeDisk=remember(homeContextV126,api){HomeDiskCacheV126(homeContextV126,api)}
    var q by remember { mutableStateOf("") }
    var data by remember { mutableStateOf<HomeV100Data?>(HomeBootstrapV104.data) }
    var heroSlides by remember { mutableStateOf(HomeBootstrapV104.heroSlides) }
    var loading by remember { mutableStateOf(data == null) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        if (data == null) {
            runCatching { withContext(Dispatchers.IO) { api.homeDataJsonV126() } }
                .onSuccess { raw -> api.homeDataFromJsonV126(raw).let{fresh->data=fresh;HomeBootstrapV104.data=fresh;homeDisk.saveHome(raw)} }
                .onFailure { error = it.message }
            loading = false
        }
    }

    LaunchedEffect(Unit) {
        // Hero is remote configuration. Fetch it independently from the product payload
        // and refresh it while Home remains visible.
        while (true) {
            runCatching { withContext(Dispatchers.IO) { api.heroSlidesJsonV126() } }
                .onSuccess { raw -> api.heroSlidesFromJsonV126(raw).let{fresh->heroSlides=fresh;HomeBootstrapV104.heroSlides=fresh;homeDisk.saveHero(raw)} }
            delay(12_000)
        }
    }

    LazyColumn(
        Modifier.fillMaxSize().padding(horizontal = 16.dp).statusBarsPadding(),
        verticalArrangement = Arrangement.spacedBy(20.dp),
        contentPadding = PaddingValues(bottom = 24.dp)
    ) {
        item {
            HomeHeader(commerce, onMenu, onFavorites, onNotifications, onFullCart, mini, onMini, cartTick)
            SmartSearch(api, q, { q = it }, { onSearch(it) }, onProduct, scan)
        }
        item {
            HeroSliderV103(
                slides = heroSlides,
                api = api,
                fallbackProduct = data?.recommended?.firstOrNull(),
                onCategory = onCategory,
                onProduct = onProduct,
                onCatalog = onAllCategories,
                onConsult = onConsult,
                onAi = onAi
            )
        }
        item {
            SectionHead("Categorii rapide","Vezi toate"){onCategory(ProductCategory(0,"Categorii de produse",0))};LazyRow(horizontalArrangement = Arrangement.spacedBy(14.dp), contentPadding = PaddingValues(vertical = 4.dp)) {
                items((data?.sections ?: emptyList()).take(8)) { section -> QuickCategory(section.category, onCategory) }
            }
        }
        item { AiCard(onAi) }
        if (loading) item { LinearProgressIndicator(Modifier.fillMaxWidth(), color = AutoIdOrange) }
        error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }

        val recommended = data?.recommended ?: emptyList()
        if (recommended.isNotEmpty()) item {
            SectionHead("În stoc AutoID", "Vezi toate", onAllCategories)
            LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                items(recommended, key = { it.id }) { product ->
                    HomeCard(
                        product,
                        commerce.isFavorite(product.id),
                        { onProduct(product) },
                        { onFavorite(product) },
                        { onCart(product) },
                        { onRfq(product) }
                    )
                }
            }
        }

        val liquidations = (data?.offers ?: emptyList()).filter { (it.stockAutoId ?: 0) > 0 }
        if (liquidations.isNotEmpty()) item {
            SectionHead("Lichidări de stoc", "Vezi toate") {
                val target = data?.liquidationCategory
                    ?: data?.categories?.firstOrNull {
                        it.slug.equals("lichidari-de-stoc", ignoreCase = true) ||
                        it.name.equals("Lichidări de stoc", ignoreCase = true) ||
                        it.name.equals("Lichidari de stoc", ignoreCase = true)
                    }
                target?.let(onCategory)
            }
            LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                items(liquidations, key = { it.id }) { product ->
                    HomeCard(
                        product,
                        commerce.isFavorite(product.id),
                        { onProduct(product) },
                        { onFavorite(product) },
                        { onCart(product) },
                        { onRfq(product) }
                    )
                }
            }
        }
        item { ConsultCard(onConsult) }
    }
}

@Composable
private fun HeroSliderV103(
    slides: List<HeroSlideV103>,
    api: AutoIdApi,
    fallbackProduct: Product?,
    onCategory: (ProductCategory) -> Unit,
    onProduct: (Product) -> Unit,
    onCatalog: () -> Unit,
    onConsult: () -> Unit,
    onAi: () -> Unit
) {
    if (slides.isEmpty()) {
        ElevatedCard(
            modifier = Modifier.fillMaxWidth().height(238.dp),
            shape = RoundedCornerShape(26.dp),
            colors = CardDefaults.elevatedCardColors(containerColor = Color(0xFFFCFCFD)),
            elevation = CardDefaults.elevatedCardElevation(defaultElevation = 1.dp)
        ) {
            Box(
                Modifier.fillMaxSize().background(
                    Brush.linearGradient(listOf(Color.White, Color(0xFFFFF7F2)))
                )
            ) {
                Column(
                    Modifier.align(Alignment.CenterStart).padding(24.dp).fillMaxWidth(.78f),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Surface(shape = RoundedCornerShape(50), color = Color(0xFFFFE9D9)) {
                        Text("AUTOID • PROFESSIONAL SOLUTIONS", Modifier.padding(horizontal = 10.dp, vertical = 6.dp), fontSize = 9.sp, fontWeight = FontWeight.ExtraBold, color = AutoIdOrange)
                    }
                    Text("Pregătim selecția AutoID", fontSize = 23.sp, lineHeight = 27.sp, fontWeight = FontWeight.ExtraBold, color = Ink)
                    Text("Conținutul sliderului este administrat din WordPress.", fontSize = 12.sp, color = Muted)
                    LinearProgressIndicator(Modifier.fillMaxWidth(.62f), color = AutoIdOrange, trackColor = Color(0xFFFFE9D9))
                }
            }
        }
        return
    }

    val rows = slides
    val pagerState = rememberPagerState(pageCount = { rows.size })
    val scope = rememberCoroutineScope()
    val interval = rows.firstOrNull()?.intervalMs?.coerceIn(3000, 20000) ?: 6000

    LaunchedEffect(rows.size, interval) {
        if (rows.size > 1) {
            while (true) {
                delay(interval)
                pagerState.animateScrollToPage((pagerState.currentPage + 1) % rows.size)
            }
        }
    }

    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Box(Modifier.fillMaxWidth()) {
            HorizontalPager(state = pagerState, modifier = Modifier.fillMaxWidth()) { page ->
                val slide = rows[page]
                val accent = remember(slide.background) {
                    runCatching { Color(android.graphics.Color.parseColor(slide.background)) }.getOrDefault(AutoIdOrange)
                }
                val hasImage = !slide.imageUrl.isNullOrBlank()
                val backgroundStyle = slide.style.equals("background", ignoreCase = true)

                if (backgroundStyle) {
                    ElevatedCard(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(26.dp),
                        colors = CardDefaults.elevatedCardColors(containerColor = Color(0xFF132238)),
                        elevation = CardDefaults.elevatedCardElevation(defaultElevation = 3.dp)
                    ) {
                        Box(Modifier.fillMaxWidth().height(286.dp)) {
                            if (hasImage) {
                                AsyncImage(
                                    slide.imageUrl,
                                    slide.title,
                                    Modifier.fillMaxSize(),
                                    contentScale = ContentScale.Crop
                                )
                                Box(
                                    Modifier.fillMaxSize().background(
                                        Brush.horizontalGradient(
                                            listOf(Color(0xF2111D2F), Color(0xC4111D2F), Color(0x33111D2F))
                                        )
                                    )
                                )
                                Box(
                                    Modifier.fillMaxSize().background(
                                        Brush.verticalGradient(
                                            listOf(Color.Transparent, Color(0x6609121F))
                                        )
                                    )
                                )
                            } else {
                                Box(
                                    Modifier.fillMaxSize().background(
                                        Brush.linearGradient(
                                            listOf(Color(0xFF132238), Color(0xFF203A57), accent.copy(alpha = .78f))
                                        )
                                    )
                                )
                            }

                            Column(
                                Modifier.fillMaxHeight().fillMaxWidth(if (hasImage) .78f else .92f).padding(start = 24.dp, top = 22.dp, bottom = 20.dp),
                                verticalArrangement = Arrangement.spacedBy(9.dp)
                            ) {
                                Surface(shape = RoundedCornerShape(50), color = Color.White.copy(alpha = .14f)) {
                                    Text(
                                        (slide.eyebrow.ifBlank { "AUTOID" }).uppercase(),
                                        Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                                        color = Color.White,
                                        fontSize = 9.sp,
                                        fontWeight = FontWeight.ExtraBold,
                                        letterSpacing = .9.sp
                                    )
                                }
                                Text(
                                    slide.title,
                                    color = Color.White,
                                    fontSize = 25.sp,
                                    fontWeight = FontWeight.ExtraBold,
                                    lineHeight = 29.sp,
                                    maxLines = 3,
                                    overflow = TextOverflow.Ellipsis
                                )
                                if (slide.description.isNotBlank()) {
                                    Text(
                                        slide.description,
                                        color = Color.White.copy(alpha = .88f),
                                        fontSize = 12.sp,
                                        lineHeight = 17.sp,
                                        maxLines = 3,
                                        overflow = TextOverflow.Ellipsis
                                    )
                                }
                                Spacer(Modifier.weight(1f))
                                if (slide.primaryLabel.isNotBlank() && slide.primaryType.isNotBlank()) {
                                    Button(
                                        onClick = { runHeroActionV103(scope, api, slide.primaryType, slide.primaryTargetId, onCategory, onProduct, onCatalog, onConsult, onAi) },
                                        shape = RoundedCornerShape(14.dp),
                                        colors = ButtonDefaults.buttonColors(containerColor = Color.White, contentColor = Ink),
                                        contentPadding = PaddingValues(horizontal = 15.dp),
                                        modifier = Modifier.heightIn(min = 46.dp, max = 64.dp).widthIn(max = 255.dp)
                                    ) {
                                        Text(
                                            slide.primaryLabel,
                                            fontSize = 10.sp,
                                            lineHeight = 13.sp,
                                            fontWeight = FontWeight.ExtraBold,
                                            maxLines = 2,
                                            textAlign = TextAlign.Center,
                                            overflow = TextOverflow.Visible
                                        )
                                        Spacer(Modifier.width(5.dp))
                                        Icon(Icons.Default.ArrowForward, null, Modifier.size(15.dp))
                                    }
                                }
                            }
                        }
                    }
                } else {
                    ElevatedCard(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(26.dp),
                        colors = CardDefaults.elevatedCardColors(containerColor = Color.White),
                        elevation = CardDefaults.elevatedCardElevation(defaultElevation = 2.dp)
                    ) {
                        Box(
                            Modifier.fillMaxWidth().height(286.dp).background(
                                Brush.linearGradient(listOf(Color.White, Color(0xFFFFFBF8), accent.copy(alpha = .10f)))
                            )
                        ) {
                            Box(
                                Modifier.align(Alignment.TopEnd).offset(x = 54.dp, y = (-46).dp).size(180.dp)
                                    .background(accent.copy(alpha = .08f), CircleShape)
                            )
                            Box(
                                Modifier.align(Alignment.BottomStart).offset(x = (-58).dp, y = 68.dp).size(150.dp)
                                    .background(AutoIdOrange.copy(alpha = .05f), CircleShape)
                            )

                            Column(
                                Modifier.fillMaxHeight().fillMaxWidth(if (hasImage) .65f else .90f).padding(start = 22.dp, top = 20.dp, bottom = 18.dp),
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Surface(shape = RoundedCornerShape(50), color = Color.White.copy(alpha = .84f)) {
                                    Text(
                                        (slide.eyebrow.ifBlank { "AUTOID" }).uppercase(),
                                        Modifier.padding(horizontal = 9.dp, vertical = 5.dp),
                                        color = accent,
                                        fontSize = 9.sp,
                                        fontWeight = FontWeight.ExtraBold,
                                        letterSpacing = .8.sp,
                                        maxLines = 1
                                    )
                                }
                                Text(slide.title, color = Ink, fontSize = 24.sp, fontWeight = FontWeight.ExtraBold, lineHeight = 28.sp, maxLines = 3, overflow = TextOverflow.Ellipsis)
                                if (slide.description.isNotBlank()) {
                                    Text(slide.description, color = Muted, fontSize = 12.sp, lineHeight = 17.sp, maxLines = 3, overflow = TextOverflow.Ellipsis)
                                }
                                Spacer(Modifier.weight(1f))
                                if (slide.primaryLabel.isNotBlank() && slide.primaryType.isNotBlank()) {
                                    Button(
                                        onClick = { runHeroActionV103(scope, api, slide.primaryType, slide.primaryTargetId, onCategory, onProduct, onCatalog, onConsult, onAi) },
                                        shape = RoundedCornerShape(14.dp),
                                        contentPadding = PaddingValues(horizontal = 15.dp),
                                        modifier = Modifier.heightIn(min = 46.dp, max = 64.dp).widthIn(max = 255.dp)
                                    ) {
                                        Text(
                                            slide.primaryLabel,
                                            fontSize = 10.sp,
                                            lineHeight = 13.sp,
                                            fontWeight = FontWeight.ExtraBold,
                                            maxLines = 2,
                                            textAlign = TextAlign.Center,
                                            overflow = TextOverflow.Visible
                                        )
                                        Spacer(Modifier.width(5.dp))
                                        Icon(Icons.Default.ArrowForward, null, Modifier.size(15.dp))
                                    }
                                }
                            }

                            if (hasImage) {
                                Surface(
                                    shape = RoundedCornerShape(22.dp),
                                    color = Color.White.copy(alpha = .96f),
                                    shadowElevation = 7.dp,
                                    modifier = Modifier.align(Alignment.BottomEnd).padding(end = 16.dp, bottom = 17.dp).width(132.dp).height(156.dp)
                                ) {
                                    AsyncImage(slide.imageUrl, slide.title, Modifier.fillMaxSize().padding(10.dp), contentScale = ContentScale.Fit)
                                }
                            }
                        }
                    }
                }
            }

            if (rows.size > 1) {
                IconButton(
                    onClick = { scope.launch { pagerState.animateScrollToPage(if (pagerState.currentPage == 0) rows.lastIndex else pagerState.currentPage - 1) } },
                    modifier = Modifier.align(Alignment.CenterStart).padding(start = 3.dp).size(34.dp)
                ) {
                    Surface(shape = CircleShape, color = Color.White.copy(alpha = .90f), shadowElevation = 2.dp) {
                        Icon(Icons.Default.ChevronLeft, "Slide anterior", tint = Ink, modifier = Modifier.padding(6.dp))
                    }
                }
                IconButton(
                    onClick = { scope.launch { pagerState.animateScrollToPage((pagerState.currentPage + 1) % rows.size) } },
                    modifier = Modifier.align(Alignment.CenterEnd).padding(end = 3.dp).size(34.dp)
                ) {
                    Surface(shape = CircleShape, color = Color.White.copy(alpha = .90f), shadowElevation = 2.dp) {
                        Icon(Icons.Default.ChevronRight, "Slide următor", tint = Ink, modifier = Modifier.padding(6.dp))
                    }
                }
            }
        }

        if (rows.size > 1) {
            Row(Modifier.padding(top = 9.dp), horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                rows.indices.forEach { index ->
                    Box(
                        Modifier.width(if (pagerState.currentPage == index) 20.dp else 7.dp).height(7.dp)
                            .background(if (pagerState.currentPage == index) AutoIdOrange else Color(0xFFD0D5DD), CircleShape)
                            .clickable { scope.launch { pagerState.animateScrollToPage(index) } }
                    )
                }
            }
        }
    }
}

private fun runHeroActionV103(
    scope: kotlinx.coroutines.CoroutineScope,
    api: AutoIdApi,
    type: String,
    targetId: Long,
    onCategory: (ProductCategory) -> Unit,
    onProduct: (Product) -> Unit,
    onCatalog: () -> Unit,
    onConsult: () -> Unit,
    onAi: () -> Unit
) {
    when (type.lowercase()) {
        "catalog", "shop", "categories" -> onCatalog()
        "product" -> if (targetId > 0) scope.launch {
            runCatching { withContext(Dispatchers.IO) { api.product(targetId) } }.onSuccess(onProduct)
        }
        "category" -> if (targetId > 0) scope.launch {
            runCatching { withContext(Dispatchers.IO) { api.categories().firstOrNull { it.id == targetId } } }
                .getOrNull()?.let(onCategory)
        }
        "ai", "support" -> onAi()
        "contact", "consultation", "consultanta", "consultanță" -> onConsult()
        else -> Unit
    }
}

@Composable private fun QuickCategory(c:ProductCategory,onCategory:(ProductCategory)->Unit){Column(Modifier.width(92.dp).clickable{onCategory(c)},horizontalAlignment=Alignment.CenterHorizontally){Surface(shape=CircleShape,color=Soft,border=androidx.compose.foundation.BorderStroke(1.dp,Color(0xFFE4E7EC)),modifier=Modifier.size(78.dp)){Box(contentAlignment=Alignment.Center){if(c.imageUrl!=null)AsyncImage(c.imageUrl,c.name,Modifier.fillMaxSize().padding(12.dp),contentScale=ContentScale.Fit) else Icon(Icons.Default.Inventory2,null,Modifier.size(32.dp),tint=Muted)}};Spacer(Modifier.height(6.dp));Text(c.name,maxLines=2,overflow=TextOverflow.Ellipsis,fontSize=12.sp,textAlign=androidx.compose.ui.text.style.TextAlign.Center)}}
@Composable private fun AiCard(onAi:()->Unit){ElevatedCard(shape=RoundedCornerShape(10.dp)){Row(Modifier.padding(14.dp),verticalAlignment=Alignment.CenterVertically){Surface(shape=CircleShape,color=AutoIdOrange,modifier=Modifier.size(54.dp)){Box(contentAlignment=Alignment.Center){Icon(Icons.Default.SmartToy,null,tint=Color.White,modifier=Modifier.size(30.dp))}};Spacer(Modifier.width(12.dp));Column(Modifier.weight(1f)){Text("Asistent AutoID AI",fontWeight=FontWeight.ExtraBold);Text("Îți recomandă produse și oferă suport tehnic pentru echipamentele tale.",fontSize=12.sp,color=Muted)};Button(onClick=onAi){Text("Întreabă")}}}}
@Composable private fun ConsultCard(onConsult:()->Unit){ElevatedCard(shape=RoundedCornerShape(10.dp)){Row(Modifier.padding(16.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.SupportAgent,null,tint=AutoIdOrange,modifier=Modifier.size(42.dp));Spacer(Modifier.width(12.dp));Column(Modifier.weight(1f)){Text("Consultanță tehnică",fontWeight=FontWeight.ExtraBold,fontSize=18.sp);Text("Discută direct cu un tehnic AutoID.",fontSize=12.sp,color=Muted)};OutlinedButton(onClick=onConsult){Text("Contact")}}}}
@Composable private fun SectionHead(title:String,action:String,onAction:()->Unit){Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){Text(title,fontSize=21.sp,fontWeight=FontWeight.ExtraBold,color=Ink,modifier=Modifier.weight(1f));TextButton(onClick=onAction){Text(action,color=AutoIdOrange)}}}

@Composable
private fun HomeCard(
    p: Product,
    favorite: Boolean,
    onClick: () -> Unit,
    onFavorite: () -> Unit,
    onCart: () -> Unit,
    onRfq: () -> Unit
) {
    var qty by remember(p.id) { mutableIntStateOf(1) }
    var added by remember(p.id) { mutableStateOf(false) }
    val cardScope = rememberCoroutineScope()
    ElevatedCard(
        modifier = Modifier.width(230.dp).height(462.dp),
        shape = RoundedCornerShape(10.dp)
    ) {
        Column(Modifier.fillMaxSize().padding(12.dp)) {
            Box(Modifier.fillMaxWidth().height(130.dp).clickable(onClick = onClick)) {
                AsyncImage(p.imageUrl, p.name, Modifier.fillMaxSize(), contentScale = ContentScale.Fit)
                IconButton(onClick = onFavorite, modifier = Modifier.align(Alignment.TopEnd)) {
                    Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "Favorite", tint = if (favorite) AutoIdOrange else Ink)
                }
                DiscountChip(p, Modifier.align(Alignment.TopStart))
            }
            Text(p.brand.ifBlank { p.category }, fontSize = 10.sp, color = Muted, maxLines = 1)
            Text(p.name, maxLines = 2, overflow = TextOverflow.Ellipsis, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            RatingLine(p, true)
            Text("SKU: ${p.sku.ifBlank { "—" }}", fontSize = 9.sp, color = Muted, maxLines = 1)
            Spacer(Modifier.height(5.dp))
            LoopPriceBlock(p)
            Spacer(Modifier.height(6.dp))
            StockLine(p, true)
            Spacer(Modifier.weight(1f))
            if (!isGrouped(p)) {
                LoopQuantityV104(qty, { if (qty > 1) qty-- }, { if (qty < 99) qty++ })
                Spacer(Modifier.height(3.dp))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.fillMaxWidth()) {
                if (isGrouped(p)) {
                    LoopActionButtonV104(
                        label = "Detalii produs",
                        filled = false,
                        modifier = Modifier.weight(1f),
                        onClick = onClick
                    )
                } else {
                    LoopActionButtonV104(
                        label = if (added) "Adăugat ✓" else "Adaugă în coș",
                        filled = true,
                        enabled = canAddV104(p),
                        modifier = Modifier.weight(1f),
                        onClick = {
                            repeat(qty) { onCart() }
                            qty = 1
                            added = true
                            cardScope.launch { delay(900); added = false }
                        }
                    )
                }
                LoopActionButtonV104(
                    label = "Cerere de ofertă",
                    filled = false,
                    modifier = Modifier.weight(1f),
                    onClick = onRfq
                )
            }
        }
    }
}

@Composable private fun DiscountChip(p:Product,modifier:Modifier=Modifier){val d=discount(p);if(d>0)Surface(modifier=modifier,shape=RoundedCornerShape(50),color=Good){Text("-$d%",Modifier.padding(horizontal=8.dp,vertical=4.dp),color=Color.White,fontSize=11.sp,fontWeight=FontWeight.Bold)}}
private fun discount(p:Product):Int=if(p.msrpEuroValue>0&&p.autoIdEuroValue>0&&p.msrpEuroValue>p.autoIdEuroValue)(((p.msrpEuroValue-p.autoIdEuroValue)/p.msrpEuroValue)*100).roundToInt().coerceAtLeast(1) else 0
private fun isGrouped(p:Product)=p.productType.equals("grouped",ignoreCase=true)
@Composable private fun CompactPrice(p:Product){Text(if(isGrouped(p))"de la ${p.priceRangeInclVat.ifBlank{p.currentInclVat.ifBlank{p.price}}}" else p.currentInclVat.ifBlank{p.price},fontWeight=FontWeight.ExtraBold,fontSize=14.sp,color=Ink)}
@Composable private fun StockLine(p:Product,compact:Boolean=false){val a=if(isGrouped(p))p.groupedStockAutoId?:0 else p.stockAutoId?:0;val d=if(isGrouped(p))p.groupedStockDistributor?:0 else p.stockDistributor?:0;Row(horizontalArrangement=Arrangement.spacedBy(6.dp),verticalAlignment=Alignment.CenterVertically){if(a>0){Box(Modifier.size(if(compact)7.dp else 9.dp).background(Good,CircleShape));Text("$a în stoc",fontSize=if(compact)10.sp else 12.sp,color=Color(0xFF067647),fontWeight=FontWeight.Bold)};if(d>0){Box(Modifier.size(if(compact)7.dp else 9.dp).background(Warn,CircleShape));Text("$d livrare 5–7 zile",fontSize=if(compact)10.sp else 12.sp,color=Color(0xFFB54708),fontWeight=FontWeight.Bold)};if(a<=0&&d<=0)Text("Cere ofertă pentru disponibilitate",fontSize=if(compact)10.sp else 12.sp,color=Muted,fontWeight=FontWeight.Bold)}}

@Composable
fun CategoriesV101(
    api:AutoIdApi,
    commerce:CommerceStore,
    onBack:()->Unit,
    onCategory:(ProductCategory)->Unit,
    onProduct:(Product)->Unit,
    onFavorites:()->Unit,
    onNotifications:()->Unit,
    onCart:()->Unit,
    scan:((String)->Unit)->Unit
){
    var q by remember { mutableStateOf("") }
    var categories by remember { mutableStateOf<List<ProductCategory>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    LaunchedEffect(Unit){
        categories=runCatching{withContext(Dispatchers.IO){api.categories()}}.getOrDefault(emptyList())
        loading=false
    }
    Column(Modifier.fillMaxSize().padding(horizontal=14.dp).statusBarsPadding()){
        Row(verticalAlignment=Alignment.CenterVertically){
            IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")}
            Text("Categorii produse",fontSize=20.sp,fontWeight=FontWeight.ExtraBold,modifier=Modifier.weight(1f))
            IconButton(onClick=onFavorites){Icon(Icons.Default.FavoriteBorder,"Favorite")}
            IconButton(onClick=onNotifications){BadgedBox(badge={Badge(containerColor=AutoIdOrange){Text("3")}}){Icon(Icons.Default.NotificationsNone,"Notificări")}}
            IconButton(onClick=onCart){
                BadgedBox(badge={if(commerce.cartCount()>0)Badge(containerColor=AutoIdOrange){Text(commerce.cartCount().toString())}}){Icon(Icons.Default.ShoppingCart,"Coș")}
            }
        }
        SmartSearch(api,q,{q=it},{},{onProduct(it)},scan,"Caută produse, SKU, brand, model...")
        Spacer(Modifier.height(12.dp))
        val visible=if(q.isBlank())categories else categories.filter{it.name.contains(q,true)}
        Box(Modifier.weight(1f).fillMaxWidth()) {
            if (loading) {
                AutoIdPulseLoaderV112(
                    modifier = Modifier.fillMaxSize(),
                    label = "Încărcăm categoriile AutoID"
                )
            } else {
                LazyVerticalGrid(
                    columns=GridCells.Fixed(2),
                    horizontalArrangement=Arrangement.spacedBy(10.dp),
                    verticalArrangement=Arrangement.spacedBy(10.dp),
                    contentPadding=PaddingValues(bottom=110.dp)
                ){
                    gridItems(visible,key={it.id}){c->
                        ElevatedCard(Modifier.height(175.dp).clickable{onCategory(c)},shape=RoundedCornerShape(10.dp)){
                            Column(Modifier.fillMaxSize().padding(12.dp),horizontalAlignment=Alignment.CenterHorizontally){
                                Box(Modifier.weight(1f).fillMaxWidth(),contentAlignment=Alignment.Center){
                                    if(c.imageUrl!=null)AsyncImage(c.imageUrl,c.name,Modifier.fillMaxSize().padding(8.dp),contentScale=ContentScale.Fit)
                                    else Icon(Icons.Default.Inventory2,null,Modifier.size(42.dp),tint=Muted)
                                }
                                Text(c.name,fontWeight=FontWeight.Bold,maxLines=2,overflow=TextOverflow.Ellipsis,textAlign=androidx.compose.ui.text.style.TextAlign.Center)
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun CatalogV100(
    api: AutoIdApi,
    commerce: CommerceStore,
    category: ProductCategory,
    initialSearch: String,
    onBack: () -> Unit,
    onProduct: (Product) -> Unit,
    onFavorite: (Product) -> Unit,
    onCart: (Product) -> Unit,
    onRfq: (Product) -> Unit,
    onAi: () -> Unit,
    onFavorites: () -> Unit,
    onNotifications: () -> Unit,
    onHeaderCart: () -> Unit,
    onSubcategory: (ProductCategory) -> Unit,
    scan: ((String) -> Unit) -> Unit
) {
    var q by remember(category.id) { mutableStateOf(initialSearch) }
    var products by remember(category.id) { mutableStateOf<List<Product>>(emptyList()) }
    var facets by remember(category.id) { mutableStateOf<CatalogFacets?>(null) }
    var brand by remember(category.id) { mutableStateOf<Long?>(null) }
    var model by remember(category.id) { mutableStateOf<Long?>(null) }
    var min by remember(category.id) { mutableStateOf<Double?>(null) }
    var max by remember(category.id) { mutableStateOf<Double?>(null) }
    var sort by remember(category.id) { mutableStateOf("stock_autoid") }
    var secondaryCategory by remember(category.id) { mutableStateOf<Long?>(null) }
    var page by remember(category.id) { mutableIntStateOf(1) }
    var loading by remember { mutableStateOf(false) }
    var canLoadMore by remember(category.id) { mutableStateOf(true) }
    var filters by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val gridState = rememberLazyGridState()
    val loadMutex = remember(category.id) { kotlinx.coroutines.sync.Mutex() }

    suspend fun load(reset: Boolean) {
        loadMutex.lock()
        try {
            loading = true
            error = null
            if (reset) {
                page = 1
                canLoadMore = true
            }
            val requestPage = page
            val rows = try {
                withContext(Dispatchers.IO) {
                    api.catalogProducts(q, category.id, requestPage, sort, brand, model, min, max, secondaryCategory)
                }
            } catch (cancelled: kotlinx.coroutines.CancellationException) {
                throw cancelled
            } catch (t: Throwable) {
                error = t.message ?: "Produsele nu au putut fi încărcate."
                emptyList()
            }

            val liquidationModeLocal =
                category.slug.equals("lichidari-de-stoc", ignoreCase = true) ||
                category.name.equals("Lichidări de stoc", ignoreCase = true) ||
                category.name.equals("Lichidari de stoc", ignoreCase = true)
            val visibleRows = if (liquidationModeLocal && secondaryCategory != null) {
                rows.filter { product -> product.categories.any { it.id == secondaryCategory } }
            } else rows

            if (reset) {
                products = visibleRows.distinctBy { it.id }
            } else {
                val existing = products.asSequence().map { it.id }.toHashSet()
                val fresh = visibleRows.filterNot { it.id in existing }
                products = products + fresh
                if (fresh.isEmpty()) canLoadMore = false
            }
            if (rows.size < 12) canLoadMore = false
        } finally {
            loading = false
            loadMutex.unlock()
        }
    }

    LaunchedEffect(category.id, secondaryCategory, brand, model) {
        facets = runCatching { withContext(Dispatchers.IO) { api.catalogFacets(category.id, secondaryCategory, brand, model) } }.getOrNull()
    }
    LaunchedEffect(category.id, brand, model, min, max, sort, secondaryCategory, q) {
        if (q.isNotBlank()) delay(300)
        load(true)
    }

    LaunchedEffect(gridState, category.id, brand, model, min, max, sort, secondaryCategory, q) {
        snapshotFlow {
            val last = gridState.layoutInfo.visibleItemsInfo.lastOrNull()?.index ?: -1
            last to products.size
        }.collect { (last, size) ->
            if (canLoadMore && !loading && size > 0 && last >= size - 3) {
                page += 1
                load(false)
            }
        }
    }

    val activeFilterCount = listOf(brand, model, min, max, secondaryCategory).count { it != null }

    Column(Modifier.fillMaxSize().padding(horizontal = 14.dp).statusBarsPadding()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Înapoi") }
            Column(Modifier.weight(1f)) {
                Text(category.name, fontSize = 20.sp, fontWeight = FontWeight.ExtraBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text("${products.size} produse încărcate", fontSize = 10.sp, color = Muted)
            }
            IconButton(onClick = onFavorites) { Icon(Icons.Default.FavoriteBorder, "Favorite") }
            IconButton(onClick = onNotifications) { BadgedBox(badge={Badge(containerColor=AutoIdOrange){Text("3")}}){Icon(Icons.Default.NotificationsNone,"Notificări")} }
            IconButton(onClick = onHeaderCart) {
                BadgedBox(badge = { if (commerce.cartCount() > 0) Badge(containerColor = AutoIdOrange) { Text(commerce.cartCount().toString()) } }) {
                    Icon(Icons.Default.ShoppingCart, "Coș")
                }
            }
        }

        SmartSearch(api, q, { q = it }, { q = it }, onProduct, scan, "Caută în ${category.name}...")

        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(top = 10.dp, bottom = 9.dp)
        ) {
            FilledTonalButton(
                onClick = { filters = true },
                shape = RoundedCornerShape(50),
                colors = ButtonDefaults.filledTonalButtonColors(
                    containerColor = if (activeFilterCount > 0) Color(0xFFFFE9D9) else Color(0xFFF2F4F7),
                    contentColor = if (activeFilterCount > 0) AutoIdOrange else Ink
                )
            ) {
                Icon(Icons.Default.Tune, null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(6.dp))
                Text(if (activeFilterCount > 0) "Filtre ($activeFilterCount)" else "Filtre")
            }
            SortMenu(sort) { sort = it }
            Spacer(Modifier.weight(1f))
        }

        error?.let {
            Surface(color = Color(0xFFFFF1F0), shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)) {
                Text(it, color = MaterialTheme.colorScheme.error, fontSize = 12.sp, modifier = Modifier.padding(10.dp))
            }
        }
        if (loading && products.isNotEmpty()) {
            LinearProgressIndicator(
                modifier = Modifier.fillMaxWidth().height(2.dp),
                color = AutoIdOrange,
                trackColor = Color.Transparent
            )
        }

        Box(Modifier.weight(1f)) {
            LazyVerticalGrid(
                state = gridState,
                columns = GridCells.Fixed(2),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
                contentPadding = PaddingValues(bottom = 150.dp)
            ) {
                gridItems(products, key = { it.id }) { p ->
                    CatalogCard(p, commerce.isFavorite(p.id), { onProduct(p) }, { onFavorite(p) }, { onCart(p) }, { onRfq(p) })
                }
                if (loading && products.isNotEmpty()) {
                    item(span = { GridItemSpan(maxLineSpan) }) {
                        AutoIdPulseLoaderV112(
                            modifier = Modifier.fillMaxWidth().height(72.dp),
                            compact = true,
                            label = ""
                        )
                    }
                }
                if (!canLoadMore && products.isNotEmpty()) {
                    item(span = { GridItemSpan(maxLineSpan) }) {
                        Text("Ai ajuns la final", fontSize = 11.sp, color = Muted, modifier = Modifier.padding(12.dp))
                    }
                }
            }
            if (loading && products.isEmpty()) {
                AutoIdPulseLoaderV112(
                    modifier = Modifier.fillMaxSize(),
                    label = "Încărcăm produsele"
                )
            }
        }
    }

    if (filters) FilterSheetV113(
        api = api,
        f = facets,
        category = category,
        selectedCategory = secondaryCategory,
        brand = brand,
        model = model,
        min = min,
        max = max,
        onApply = { c, b, m, mi, ma ->
            secondaryCategory = c; brand = b; model = m; min = mi; max = ma; filters = false
        },
        onClear = {
            secondaryCategory = null; brand = null; model = null; min = null; max = null; filters = false
        },
        onAi = { filters = false; onAi() },
        onDismiss = { filters = false }
    )
}

@Composable private fun SortMenu(sort:String,onSort:(String)->Unit){var open by remember{mutableStateOf(false)};Box{OutlinedButton(onClick={open=true}){Icon(Icons.Default.SwapVert,null);Spacer(Modifier.width(4.dp));Text(when(sort){"stock_autoid"->"Stoc AutoID";"price_asc"->"Preț ↑";"price_desc"->"Preț ↓";"rating"->"Rating";else->"Sortare"})};DropdownMenu(open,{open=false}){listOf("stock_autoid" to "Stoc AutoID","price_asc" to "Preț crescător","price_desc" to "Preț descrescător","rating" to "Rating","date" to "Cele mai noi").forEach{(k,v)->DropdownMenuItem(text={Text(v)},onClick={onSort(k);open=false})}}}}
@Composable
private fun FacetGridV105(
    items: List<FacetItem>,
    selected: Long?,
    onSelected: (Long?) -> Unit,
    hierarchy: Boolean = false
) {
    val rows = (listOf(FacetItem(0, "Toate")) + items).chunked(2)
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        rows.forEach { row ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                row.forEach { item ->
                    val isSelected = if (item.id == 0L) selected == null else selected == item.id
                    val prefix = if (hierarchy && item.id != 0L && item.depth > 1) "› ".repeat((item.depth - 1).coerceAtMost(2)) else ""
                    FilterChip(
                        selected = isSelected,
                        onClick = { onSelected(item.id.takeIf { it > 0 }) },
                        label = {
                            Column(Modifier.fillMaxWidth()) {
                                Text(
                                    prefix + item.name,
                                    maxLines = 2,
                                    overflow = TextOverflow.Ellipsis,
                                    fontSize = 11.sp,
                                    fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium
                                )
                                if (item.count > 0) Text("${item.count} produse", fontSize = 9.sp, color = if (isSelected) AutoIdOrange else Muted)
                            }
                        },
                        shape = RoundedCornerShape(14.dp),
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = Color(0xFFFFE9D9),
                            selectedLabelColor = Ink
                        ),
                        border = FilterChipDefaults.filterChipBorder(
                            enabled = true,
                            selected = isSelected,
                            borderColor = Color(0xFFE4E7EC),
                            selectedBorderColor = AutoIdOrange
                        ),
                        modifier = Modifier.weight(1f).heightIn(min = 54.dp)
                    )
                }
                repeat(2 - row.size) { Spacer(Modifier.weight(1f)) }
            }
        }
    }
}

private fun filterLeiV105(value: Float): String =
    java.text.NumberFormat.getNumberInstance(java.util.Locale("ro", "RO")).apply {
        minimumFractionDigits = 0
        maximumFractionDigits = 0
    }.format(value)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun FilterSheetV105(
    f: CatalogFacets?,
    category: ProductCategory,
    selectedCategory: Long?,
    brand: Long?,
    model: Long?,
    min: Double?,
    max: Double?,
    onApply: (Long?, Long?, Long?, Double?, Double?) -> Unit,
    onClear: () -> Unit,
    onAi: () -> Unit,
    onDismiss: () -> Unit
) {
    var c by remember(category.id, selectedCategory) { mutableStateOf(selectedCategory) }
    var b by remember(category.id, brand) { mutableStateOf(brand) }
    var m by remember(category.id, model) { mutableStateOf(model) }

    val facetMin = (f?.minPrice ?: 0.0).coerceAtLeast(0.0).toFloat()
    val facetMaxRaw = (f?.maxPrice ?: 0.0).coerceAtLeast(0.0).toFloat()
    val sliderMax = if (facetMaxRaw > facetMin) facetMaxRaw else facetMin + 1f
    val initialStart = (min?.toFloat() ?: facetMin).coerceIn(facetMin, sliderMax)
    val initialEnd = (max?.toFloat() ?: facetMaxRaw.takeIf { it > facetMin } ?: sliderMax).coerceIn(initialStart, sliderMax)
    var priceRange by remember(category.id, f?.minPrice, f?.maxPrice, min, max) { mutableStateOf(initialStart..initialEnd) }

    val categoryItems = f?.categoryHierarchy.orEmpty().ifEmpty {
        f?.subcategories.orEmpty().map { FacetItem(it.id, it.name, it.slug, it.count, it.parent, 1) }
    }
    val priceAvailable = f != null && facetMaxRaw > facetMin
    val stagedCount = listOf(c, b, m).count { it != null } +
        (if (priceAvailable && priceRange.start > facetMin + .5f) 1 else 0) +
        (if (priceAvailable && priceRange.endInclusive < facetMaxRaw - .5f) 1 else 0)

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = Color(0xFFFCFCFD),
        shape = RoundedCornerShape(topStart = 28.dp, topEnd = 28.dp)
    ) {
        Column(Modifier.fillMaxWidth().fillMaxHeight(.92f)) {
            Row(
                Modifier.fillMaxWidth().padding(horizontal = 18.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(Modifier.weight(1f)) {
                    Text("Filtre", fontSize = 25.sp, fontWeight = FontWeight.ExtraBold, color = Ink)
                    Text(if (stagedCount > 0) "$stagedCount filtre selectate" else "Rafinează rezultatele", fontSize = 11.sp, color = Muted)
                }
                Surface(
                    onClick = onAi,
                    shape = RoundedCornerShape(50),
                    color = Color(0xFFFFF0E5)
                ) {
                    Row(Modifier.padding(horizontal = 11.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.SmartToy, null, tint = AutoIdOrange, modifier = Modifier.size(17.dp))
                        Spacer(Modifier.width(5.dp))
                        Text("Ajută-mă AI", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = AutoIdOrange)
                    }
                }
            }

            HorizontalDivider(color = Color(0xFFEAECF0))

            LazyColumn(
                Modifier.weight(1f).fillMaxWidth().padding(horizontal = 18.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp),
                contentPadding = PaddingValues(top = 14.dp, bottom = 18.dp)
            ) {
                if (categoryItems.isNotEmpty()) item {
                    FilterSectionV107(Icons.Default.AccountTree, "Categorie") {
                        FacetGridV105(categoryItems, c, { c = it }, hierarchy = true)
                    }
                }

                item {
                    FilterSectionV107(Icons.Default.Payments, "Preț") {
                        Text(
                            if (priceAvailable) "${filterLeiV105(priceRange.start)} – ${filterLeiV105(priceRange.endInclusive)} lei"
                            else "Interval indisponibil",
                            fontSize = 16.sp,
                            fontWeight = FontWeight.ExtraBold,
                            color = Ink
                        )
                        if (priceAvailable) {
                            RangeSlider(
                                value = priceRange,
                                onValueChange = { priceRange = it },
                                valueRange = facetMin..sliderMax,
                                modifier = Modifier.fillMaxWidth()
                            )
                            Row(Modifier.fillMaxWidth()) {
                                Text("Min. ${filterLeiV105(facetMin)} lei", fontSize = 10.sp, color = Muted)
                                Spacer(Modifier.weight(1f))
                                Text("Max. ${filterLeiV105(facetMaxRaw)} lei", fontSize = 10.sp, color = Muted)
                            }
                        }
                    }
                }

                if (f?.brands.orEmpty().isNotEmpty()) item {
                    FilterSectionV107(Icons.Default.Storefront, "Brand") {
                        FacetGridV105(f?.brands.orEmpty(), b, { b = it })
                    }
                }

                if (f?.models.orEmpty().isNotEmpty()) item {
                    FilterSectionV107(Icons.Default.ViewInAr, "Model") {
                        FacetGridV105(f?.models.orEmpty().take(90), m, { m = it })
                    }
                }
            }

            Surface(shadowElevation = 10.dp, color = Color.White) {
                Row(
                    Modifier.fillMaxWidth().padding(14.dp).navigationBarsPadding(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    OutlinedButton(
                        onClick = onClear,
                        modifier = Modifier.weight(.8f).height(54.dp),
                        shape = RoundedCornerShape(16.dp)
                    ) { Text("Resetează") }
                    Button(
                        onClick = {
                            val appliedMin = if (priceAvailable && priceRange.start > facetMin + .5f) priceRange.start.toDouble() else null
                            val appliedMax = if (priceAvailable && priceRange.endInclusive < facetMaxRaw - .5f) priceRange.endInclusive.toDouble() else null
                            onApply(c, b, m, appliedMin, appliedMax)
                        },
                        modifier = Modifier.weight(1.2f).height(54.dp),
                        shape = RoundedCornerShape(16.dp)
                    ) { Text(if (stagedCount > 0) "Vezi rezultatele" else "Aplică") }
                }
            }
        }
    }
}

@Composable
private fun FilterSectionV107(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    content: @Composable ColumnScope.() -> Unit
) {
    ElevatedCard(
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.elevatedCardColors(containerColor = Color.White),
        elevation = CardDefaults.elevatedCardElevation(defaultElevation = 1.dp)
    ) {
        Column(Modifier.fillMaxWidth().padding(14.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(shape = RoundedCornerShape(10.dp), color = Color(0xFFFFF0E5)) {
                    Icon(icon, null, tint = AutoIdOrange, modifier = Modifier.padding(7.dp).size(18.dp))
                }
                Spacer(Modifier.width(9.dp))
                Text(title, fontWeight = FontWeight.ExtraBold, fontSize = 15.sp, color = Ink)
            }
            content()
        }
    }
}

private fun cleanVatRangeV104(raw: String): String {
    if (raw.isBlank()) return ""
    val numbers = Regex("""\d{1,3}(?:\.\d{3})*(?:,\d{2})|\d+(?:,\d{2})""").findAll(raw).map { it.value }.toList()
    if (numbers.size >= 2) return "${numbers[0]} – ${numbers[1]} lei incl. TVA"
    val clean = raw
        .replace(Regex("(?i)\\s*incl\\.?\\s*TVA"), "")
        .replace(Regex("(?i)\\s*lei\\s*$"), "")
        .trim()
    return if (clean.isBlank()) "" else "$clean lei incl. TVA"
}

private fun canAddV104(p: Product): Boolean =
    !isGrouped(p) && ((p.stockAutoId ?: 0) > 0 || (p.stockDistributor ?: 0) > 0)

@Composable
private fun LoopPriceBlock(p: Product) {
    val grouped = isGrouped(p)
    val msrp = p.msrpEuroValue
    val autoId = p.autoIdEuroValue
    val sameEuro = msrp > 0 && autoId > 0 && kotlin.math.abs(msrp - autoId) < 0.005
    val showAutoId = autoId > 0 && !sameEuro
    val euroDiscount = msrp > 0 && showAutoId && msrp > autoId + 0.005

    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        if (msrp > 0) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("MSRP: ", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Ink)
                Text(
                    "${euro(msrp)} €",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = Ink,
                    textDecoration = if (euroDiscount) androidx.compose.ui.text.style.TextDecoration.LineThrough else null
                )
                if (!showAutoId) Text(" ex. TVA", fontSize = 9.sp, color = Muted)
            }
        }
        if (showAutoId) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("AutoID: ", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Ink)
                Text("${euro(autoId)} €", fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = AutoIdOrange)
                Text(" ex. TVA", fontSize = 9.sp, color = Muted)
            }
        } else if (msrp <= 0 && autoId > 0) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("AutoID: ", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Ink)
                Text("${euro(autoId)} €", fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = AutoIdOrange)
                Text(" ex. TVA", fontSize = 9.sp, color = Muted)
            }
        }

        if (grouped) {
            val range = cleanVatRangeV104(p.priceRangeInclVat.ifBlank { p.currentInclVat.ifBlank { p.price } })
            if (range.isNotBlank()) {
                Text(range, fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = Ink, maxLines = 2)
            }
        } else {
            val regular = p.regularInclVatDisplay
            val current = p.saleInclVatDisplay.ifBlank { p.currentInclVat.ifBlank { p.price } }
            val hasDiscount = regular.isNotBlank() && current.isNotBlank() && regular != current
            Row(verticalAlignment = Alignment.CenterVertically) {
                if (hasDiscount) {
                    Text(
                        regular,
                        fontSize = 11.sp,
                        color = Muted,
                        textDecoration = androidx.compose.ui.text.style.TextDecoration.LineThrough
                    )
                    Spacer(Modifier.width(6.dp))
                }
                Text(current, fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = Ink)
                Spacer(Modifier.width(3.dp))
                Text("incl. TVA", fontSize = 9.sp, color = Muted)
            }
        }
    }
}

@Composable
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
        shape = RoundedCornerShape(10.dp),
        color = bg,
        contentColor = fg,
        border = if (filled) null else androidx.compose.foundation.BorderStroke(1.dp, outline)
    ) {
        Box(
            modifier = Modifier.fillMaxSize().padding(horizontal = 6.dp, vertical = 4.dp),
            contentAlignment = Alignment.Center
        ) {
            Text(
                label,
                fontSize = 10.sp,
                fontWeight = FontWeight.SemiBold,
                color = fg,
                maxLines = 1,
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
        }
    }
}

@Composable
private fun LoopQuantityV104(qty: Int, onMinus: () -> Unit, onPlus: () -> Unit) {
    Row(
        modifier = Modifier.height(28.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.Center
    ) {
        IconButton(onClick = onMinus, enabled = qty > 1, modifier = Modifier.size(28.dp)) {
            Icon(Icons.Default.Remove, "Scade cantitatea", modifier = Modifier.size(15.dp))
        }
        Text(qty.toString(), fontSize = 11.sp, fontWeight = FontWeight.Bold, modifier = Modifier.widthIn(min = 20.dp), textAlign = androidx.compose.ui.text.style.TextAlign.Center)
        IconButton(onClick = onPlus, modifier = Modifier.size(28.dp)) {
            Icon(Icons.Default.Add, "Crește cantitatea", modifier = Modifier.size(15.dp))
        }
    }
}

@Composable
private fun CatalogCard(
    p: Product,
    favorite: Boolean,
    onProduct: () -> Unit,
    onFavorite: () -> Unit,
    onCart: () -> Unit,
    onRfq: () -> Unit
) {
    var qty by remember(p.id) { mutableIntStateOf(1) }
    ElevatedCard(
        modifier = Modifier.height(462.dp),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.fillMaxSize().padding(10.dp)) {
            Box(Modifier.fillMaxWidth().height(128.dp).clickable(onClick = onProduct)) {
                AsyncImage(p.imageUrl, p.name, Modifier.fillMaxSize(), contentScale = ContentScale.Fit)
                DiscountChip(p, Modifier.align(Alignment.TopStart))
                IconButton(onClick = onFavorite, modifier = Modifier.align(Alignment.TopEnd)) {
                    Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "Favorite", tint = if (favorite) AutoIdOrange else Ink)
                }
            }
            Text(p.brand, fontSize = 10.sp, color = Muted, maxLines = 1)
            Text(p.name, maxLines = 2, overflow = TextOverflow.Ellipsis, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            RatingLine(p, true)
            Text("SKU: ${p.sku.ifBlank { "—" }}", fontSize = 9.sp, color = Muted, maxLines = 1)
            Spacer(Modifier.height(5.dp))
            LoopPriceBlock(p)
            Spacer(Modifier.height(6.dp))
            StockLine(p, true)
            Spacer(Modifier.weight(1f))
            if (!isGrouped(p)) {
                LoopQuantityV104(qty, { if (qty > 1) qty-- }, { if (qty < 99) qty++ })
                Spacer(Modifier.height(3.dp))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.fillMaxWidth()) {
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
            }
        }
    }
}

@Composable fun ProductV100(seed:Product,api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onBack:()->Unit,onFavorite:(Product)->Unit,onCart:(Product,Int)->Unit,onRfq:(Product,Int)->Unit,onOpen:(Product)->Unit,onAi:()->Unit,onNotifications:()->Unit,onHeaderCart:()->Unit){
    var p by remember(seed.id){mutableStateOf(seed)}
    var loading by remember{mutableStateOf(true)}
    var qty by remember{mutableIntStateOf(1)}
    var family by remember{mutableStateOf<ProductFamily?>(null)}
    var group by remember{mutableStateOf<String?>(null)}
    var rows by remember{mutableStateOf<List<Product>>(emptyList())}
    var familyFilters by remember{mutableStateOf<List<FamilyFacet>>(emptyList())}
    var familyCategory by remember{mutableLongStateOf(0L)}
    var reviews by remember{mutableStateOf(ProductReviews(0.0,0,emptyList()))}
    var reviewOpen by remember{mutableStateOf(false)}
    var reviewRating by remember{mutableIntStateOf(5)}
    var reviewText by remember{mutableStateOf("")}
    var reviewName by remember{mutableStateOf("")}
    var reviewEmail by remember{mutableStateOf(session.customerEmail)}
    var reviewBusy by remember{mutableStateOf(false)}
    var reviewMessage by remember{mutableStateOf("")}
    var reviewRefresh by remember{mutableIntStateOf(0)}
    LaunchedEffect(seed.id,reviewRefresh){
        runCatching{withContext(Dispatchers.IO){api.product(seed.id)}}.onSuccess{p=it}
        family=runCatching{withContext(Dispatchers.IO){api.productFamily(seed.id)}}.getOrNull()
        reviews=runCatching{withContext(Dispatchers.IO){api.productReviews(seed.id)}}.getOrDefault(ProductReviews(p.rating,p.reviewCount,emptyList()))
        if(group==null || family?.groups?.none{it.key==group&&it.count>0}!=false) group=family?.groups?.firstOrNull{it.count>0}?.key
        loading=false
    }
    LaunchedEffect(group,p.id,familyCategory){group?.let{key->if(key!="accessories"&&key!="consumables")familyCategory=0;val page=runCatching{withContext(Dispatchers.IO){api.familyProductsPage(p.id,key,category=familyCategory)}}.getOrDefault(FamilyProductsPage(emptyList(),emptyList(),familyCategory));rows=page.products;familyFilters=if(key=="accessories"||key=="consumables")page.filters else emptyList()}}
    LaunchedEffect(reviewBusy){if(reviewBusy){
        runCatching{withContext(Dispatchers.IO){api.submitProductReview(p.id,reviewRating,reviewText,reviewName,reviewEmail,session.accessToken)}}
            .onSuccess{reviewMessage="Mulțumim! Recenzia a fost trimisă.";reviewText="";reviewOpen=false;reviewRefresh++}
            .onFailure{reviewMessage=it.message?:"Recenzia nu a putut fi trimisă."}
        reviewBusy=false
    }}
    LazyColumn(Modifier.fillMaxSize().padding(horizontal=16.dp).statusBarsPadding(),verticalArrangement=Arrangement.spacedBy(12.dp),contentPadding=PaddingValues(bottom=120.dp)){
        item{Row(verticalAlignment=Alignment.CenterVertically){IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")};Spacer(Modifier.weight(1f));IconButton(onClick={onFavorite(p)}){Icon(if(commerce.isFavorite(p.id))Icons.Default.Favorite else Icons.Default.FavoriteBorder,"Favorite",tint=if(commerce.isFavorite(p.id))AutoIdOrange else Ink)};IconButton(onClick=onNotifications){BadgedBox(badge={Badge(containerColor=AutoIdOrange){Text("3")}}){Icon(Icons.Default.NotificationsNone,"Notificări")}};IconButton(onClick=onHeaderCart){BadgedBox(badge={if(commerce.cartCount()>0)Badge(containerColor=AutoIdOrange){Text(commerce.cartCount().toString())}}){Icon(Icons.Default.ShoppingCart,"Coș")}}}}
        item{Gallery(p)}
        item{Brand(p);Text(p.name,fontSize=25.sp,fontWeight=FontWeight.ExtraBold,color=Ink,lineHeight=29.sp);RatingLine(p);Text("Cod produs: ${p.sku.ifBlank{"—"}}",fontSize=12.sp,color=Muted)}
        item{
            Text(if(isGrouped(p))"Prețuri de la:" else "Comandă acum:",fontSize=14.sp,fontWeight=FontWeight.Bold,color=Muted)
            PriceBlock(p,false)
            if(isGrouped(p)&&p.priceRangeInclVat.isNotBlank()){
                val price=p.priceRangeInclVat.replace(Regex("\\s*incl\\.\\s*TVA",RegexOption.IGNORE_CASE),"").trim()
                Row(verticalAlignment=Alignment.Bottom){Text(price,fontSize=18.sp,fontWeight=FontWeight.ExtraBold,color=Ink);Spacer(Modifier.width(5.dp));Text("incl. TVA",fontSize=11.sp,fontWeight=FontWeight.Normal,color=Muted)}
            } else if(!isGrouped(p)){
                Row(verticalAlignment=Alignment.Bottom){Text(p.currentInclVat.ifBlank{p.price},fontSize=18.sp,fontWeight=FontWeight.ExtraBold,color=Ink);Spacer(Modifier.width(5.dp));Text("incl. TVA",fontSize=11.sp,fontWeight=FontWeight.Normal,color=Muted)}
            }
            Spacer(Modifier.height(6.dp));StockLine(p)
        }
        item{
            if(isGrouped(p)){
                OutlinedButton(onClick={onRfq(p,1)},modifier=Modifier.fillMaxWidth().height(52.dp),shape=RoundedCornerShape(10.dp)){Text("Cerere de ofertă")}
            }else{
                Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(8.dp)){
                    OutlinedButton(onClick={if(qty>1)qty--},shape=RoundedCornerShape(10.dp)){Text("−")};Text(qty.toString(),fontWeight=FontWeight.Bold);OutlinedButton(onClick={qty++},shape=RoundedCornerShape(10.dp)){Text("+")}
                    Button(onClick={onCart(p,qty)},modifier=Modifier.weight(1f).height(48.dp),shape=RoundedCornerShape(10.dp)){Text("Adaugă în coș")}
                }
                OutlinedButton(onClick={onRfq(p,qty)},modifier=Modifier.fillMaxWidth().padding(top=7.dp).height(48.dp),shape=RoundedCornerShape(10.dp)){Text("Cerere de ofertă")}
            }
        }
        if(p.shortDescription.isNotBlank() || p.descriptionHtml.isNotBlank())item{ProductAboutV113(p)}
        val groups=family?.groups.orEmpty().filter{it.count>0}
        if(groups.isNotEmpty())item{
            Text("Produse asociate",fontSize=19.sp,fontWeight=FontWeight.ExtraBold)
            LazyRow(horizontalArrangement=Arrangement.spacedBy(7.dp)){items(groups){g->FilterChip(group==g.key,{group=g.key;familyCategory=0L},{Text("${g.label} (${g.count})")},shape=RoundedCornerShape(10.dp))}}
        }
        if((group=="accessories"||group=="consumables")&&familyFilters.isNotEmpty())item{Column(verticalArrangement=Arrangement.spacedBy(7.dp)){Text("Filtrează după categorie",fontSize=12.sp,fontWeight=FontWeight.Bold,color=Muted);LazyRow(horizontalArrangement=Arrangement.spacedBy(7.dp)){item{FilterChip(familyCategory==0L,{familyCategory=0L},{Text("Toate")},shape=RoundedCornerShape(10.dp))};items(familyFilters,key={it.id}){f->FilterChip(familyCategory==f.id,{familyCategory=f.id},{Text("${f.name} (${f.count})")},shape=RoundedCornerShape(10.dp))}}}}
        if(rows.isNotEmpty())item{LazyRow(horizontalArrangement=Arrangement.spacedBy(10.dp)){items(rows,key={it.id}){r->HomeCard(r,commerce.isFavorite(r.id),{onOpen(r)},{onFavorite(r)},{onCart(r,1)},{onRfq(r,1)})}}}
        item{
            HorizontalDivider(color=Color(0xFFE4E7EC));Spacer(Modifier.height(4.dp))
            Row(verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text("Recenzii",fontSize=19.sp,fontWeight=FontWeight.ExtraBold,color=Ink);Text(if(reviews.count>0)"${"%.1f".format(reviews.average)} din 5 · ${reviews.count} recenzii" else "Fii primul care lasă o recenzie",fontSize=12.sp,color=Muted)};OutlinedButton(onClick={reviewOpen=!reviewOpen},shape=RoundedCornerShape(10.dp)){Text(if(reviewOpen)"Închide" else "Scrie o recenzie")}}
            if(reviewOpen){
                Spacer(Modifier.height(10.dp));Text("Evaluarea ta",fontSize=12.sp,fontWeight=FontWeight.Bold,color=Ink)
                Row{(1..5).forEach{i->IconButton(onClick={reviewRating=i},modifier=Modifier.size(36.dp)){Icon(if(i<=reviewRating)Icons.Default.Star else Icons.Default.StarBorder,"$i stele",tint=Color(0xFFFDB022))}}}
                if(session.accessToken==null){OutlinedTextField(reviewName,{reviewName=it},label={Text("Nume")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(10.dp));Spacer(Modifier.height(7.dp));OutlinedTextField(reviewEmail,{reviewEmail=it},label={Text("Email")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(10.dp));Spacer(Modifier.height(7.dp))}
                OutlinedTextField(reviewText,{reviewText=it},label={Text("Recenzia ta")},modifier=Modifier.fillMaxWidth(),minLines=4,shape=RoundedCornerShape(10.dp))
                Spacer(Modifier.height(8.dp));Button(onClick={reviewBusy=true},enabled=!reviewBusy&&reviewText.trim().length>=3&&(session.accessToken!=null||(reviewName.isNotBlank()&&reviewEmail.contains("@"))),modifier=Modifier.fillMaxWidth().height(48.dp),shape=RoundedCornerShape(10.dp)){Text(if(reviewBusy)"Se trimite..." else "Trimite recenzia")}
            }
            if(reviewMessage.isNotBlank()){Spacer(Modifier.height(8.dp));Text(reviewMessage,fontSize=11.sp,color=if(reviewMessage.startsWith("Mulțumim"))Good else MaterialTheme.colorScheme.error)}
            if(reviews.reviews.isNotEmpty()){Spacer(Modifier.height(12.dp));Column(verticalArrangement=Arrangement.spacedBy(10.dp)){reviews.reviews.forEach{r->Surface(shape=RoundedCornerShape(10.dp),color=Soft,modifier=Modifier.fillMaxWidth()){Column(Modifier.padding(12.dp),verticalArrangement=Arrangement.spacedBy(5.dp)){Row(verticalAlignment=Alignment.CenterVertically){Text(r.author,fontWeight=FontWeight.Bold,color=Ink,modifier=Modifier.weight(1f));if(r.verified)Text("Achiziție verificată",fontSize=9.sp,color=Good)};Row{repeat(5){i->Icon(if(i<r.rating)Icons.Default.Star else Icons.Default.StarBorder,null,tint=Color(0xFFFDB022),modifier=Modifier.size(15.dp))}};Text(r.content,fontSize=12.sp,color=Ink,lineHeight=17.sp)}}}}
            }
        }
        item{AiCard(onAi)}
        if(loading)item{LinearProgressIndicator(Modifier.fillMaxWidth(),color=AutoIdOrange)}
    }
}

@Composable private fun Gallery(p:Product){val imgs=(listOfNotNull(p.imageUrl)+p.images).distinct();val pager=rememberPagerState{imgs.size.coerceAtLeast(1)};Box{Column{HorizontalPager(pager,Modifier.fillMaxWidth().height(330.dp)){i->if(imgs.isNotEmpty())AsyncImage(imgs[i],p.name,Modifier.fillMaxSize().padding(8.dp),contentScale=ContentScale.Fit) else Box(Modifier.fillMaxSize().background(Soft))};if(imgs.size>1)Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.Center){repeat(imgs.size){i->Box(Modifier.padding(3.dp).size(if(pager.currentPage==i)9.dp else 7.dp).background(if(pager.currentPage==i)AutoIdOrange else Color(0xFFD0D5DD),CircleShape))}}};DiscountChip(p,Modifier.align(Alignment.TopStart).padding(8.dp))}}
@Composable private fun Brand(p:Product){if(p.brandLogoUrl!=null)AsyncImage(p.brandLogoUrl,p.brand,Modifier.height(34.dp).widthIn(max=120.dp),contentScale=ContentScale.Fit) else if(p.brand.isNotBlank())Text(p.brand.uppercase(),fontSize=12.sp,fontWeight=FontWeight.ExtraBold,color=Muted)}
@Composable private fun RatingLine(p:Product,compact:Boolean=false){val r=if(p.rating>0)p.rating else 0.0;Row(verticalAlignment=Alignment.CenterVertically){repeat(5){i->Icon(if(i<r.roundToInt())Icons.Default.Star else Icons.Default.StarBorder,null,tint=Color(0xFFFDB022),modifier=Modifier.size(if(compact)12.dp else 17.dp))};Spacer(Modifier.width(4.dp));Text(if(r>0)"${"%.1f".format(r)} (${p.reviewCount} recenzii)" else "Fără recenzii",fontSize=if(compact)9.sp else 12.sp,color=Muted)}}
@Composable private fun PriceBlock(p:Product,compact:Boolean){val m=p.msrpEuroValue;val a=p.autoIdEuroValue;val same=m>0&&a>0&&kotlin.math.abs(m-a)<0.005;val fs=if(compact)11.sp else 16.sp;if(m>0){Row(verticalAlignment=Alignment.CenterVertically){Text("MSRP: ",fontSize=fs,fontWeight=FontWeight.Bold);Text("${euro(m)} €",fontSize=fs,fontWeight=FontWeight.Bold,textDecoration=if(!same&&a>0)androidx.compose.ui.text.style.TextDecoration.LineThrough else null);if(!same&&a>0){Text("  AutoID: ",fontSize=fs,fontWeight=FontWeight.Bold,color=AutoIdOrange);Surface(color=Color(0xFFFFF1E8),shape=RoundedCornerShape(8.dp)){Text("${euro(a)} €",Modifier.padding(horizontal=6.dp,vertical=2.dp),fontSize=fs,fontWeight=FontWeight.ExtraBold,color=Color(0xFFB93815))}}};if(!compact)Text("EURO ex. TVA",fontSize=10.sp,color=Muted)}else if(a>0)Text("AutoID: ${euro(a)} € ex. TVA",fontSize=fs,fontWeight=FontWeight.ExtraBold,color=AutoIdOrange)else Text(p.priceRangeExVat.ifBlank{p.price},fontSize=fs,fontWeight=FontWeight.Bold)}
private fun euro(v:Double)=java.text.NumberFormat.getNumberInstance(java.util.Locale("ro","RO")).apply{minimumFractionDigits=2;maximumFractionDigits=2}.format(v)

private fun cartUnitRonV107(p: Product): Double? {
    val raw = p.currentInclVat.ifBlank { p.price }
    val token = Regex("""\d{1,3}(?:\.\d{3})*(?:,\d{2})|\d+(?:[.,]\d{2})?""").find(raw)?.value ?: return null
    return token.replace(".", "").replace(",", ".").toDoubleOrNull()
}

private fun cleanDisplayV108(raw: String): String = raw
    .replace("&amp;nbsp;", " ", ignoreCase = true)
    .replace("&nbsp;", " ", ignoreCase = true)
    .replace("&#160;", " ", ignoreCase = true)
    .replace("&#xA0;", " ", ignoreCase = true)
    .replace('\u00A0', ' ')
    .replace(Regex("\\s+"), " ")
    .trim()

private fun moneyRonV107(value: Double): String =
    java.text.NumberFormat.getNumberInstance(java.util.Locale("ro", "RO")).apply {
        minimumFractionDigits = 2
        maximumFractionDigits = 2
    }.format(value) + " lei"

@Composable
fun CartV100(
    commerce: CommerceStore,
    onProduct: (Product) -> Unit,
    onChanged: () -> Unit,
    onCheckout: () -> Unit
) {
    val lines = commerce.cart()
    val allPriced = lines.all { cartUnitRonV107(it.product) != null }
    val subtotal = lines.sumOf { (cartUnitRonV107(it.product) ?: 0.0) * it.quantity }

    Column(Modifier.fillMaxSize().background(Color(0xFFF8FAFC)).statusBarsPadding()) {
        Row(
            Modifier.fillMaxWidth().background(Color.White).padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(Modifier.weight(1f)) {
                Text("Coșul tău", fontSize = 25.sp, fontWeight = FontWeight.ExtraBold, color = Ink)
                Text("${commerce.cartCount()} ${if (commerce.cartCount() == 1) "produs" else "produse"}", fontSize = 12.sp, color = Muted)
            }
            Surface(shape = RoundedCornerShape(50), color = Color(0xFFFFF0E5)) {
                Row(Modifier.padding(horizontal = 10.dp, vertical = 7.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.ShoppingBag, null, tint = AutoIdOrange, modifier = Modifier.size(17.dp))
                    Spacer(Modifier.width(5.dp))
                    Text("AutoID", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = AutoIdOrange)
                }
            }
        }

        if (lines.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    Surface(shape = CircleShape, color = Color(0xFFFFF0E5), modifier = Modifier.size(82.dp)) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(Icons.Default.ShoppingCart, null, Modifier.size(38.dp), tint = AutoIdOrange)
                        }
                    }
                    Text("Coșul este gol", fontSize = 22.sp, fontWeight = FontWeight.ExtraBold, color = Ink)
                    Text("Adaugă produsele de care ai nevoie.", color = Muted, fontSize = 13.sp)
                }
            }
            return
        }

        LazyColumn(
            Modifier.weight(1f).padding(horizontal = 14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(top = 12.dp, bottom = 18.dp)
        ) {
            items(lines, key = { it.product.id }) { line ->
                val unit = cartUnitRonV107(line.product)
                ElevatedCard(
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.elevatedCardColors(containerColor = Color.White),
                    elevation = CardDefaults.elevatedCardElevation(defaultElevation = 1.dp)
                ) {
                    Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.Top) {
                        Surface(
                            shape = RoundedCornerShape(14.dp),
                            color = Color(0xFFF8FAFC),
                            modifier = Modifier.size(92.dp).clickable { onProduct(line.product) }
                        ) {
                            AsyncImage(line.product.imageUrl, line.product.name, Modifier.padding(8.dp), contentScale = ContentScale.Fit)
                        }
                        Spacer(Modifier.width(12.dp))
                        Column(Modifier.weight(1f)) {
                            Text(line.product.brand.uppercase(), fontSize = 9.sp, fontWeight = FontWeight.Bold, color = AutoIdOrange, maxLines = 1)
                            Text(line.product.name, maxLines = 2, overflow = TextOverflow.Ellipsis, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Ink)
                            Text("SKU: ${line.product.sku.ifBlank { "—" }}", fontSize = 10.sp, color = Muted)
                            Spacer(Modifier.height(5.dp))
                            Text(cleanDisplayV108(line.product.currentInclVat.ifBlank { line.product.price }) + " incl. TVA", fontWeight = FontWeight.ExtraBold, fontSize = 13.sp, color = Ink)
                            Spacer(Modifier.height(8.dp))
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Surface(shape = RoundedCornerShape(12.dp), color = Color(0xFFF2F4F7)) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        IconButton(
                                            onClick = { commerce.changeQty(line.product.id, line.quantity - 1); onChanged() },
                                            modifier = Modifier.size(34.dp)
                                        ) { Icon(Icons.Default.Remove, "Scade", modifier = Modifier.size(16.dp)) }
                                        Text(line.quantity.toString(), fontWeight = FontWeight.ExtraBold, fontSize = 12.sp, modifier = Modifier.widthIn(min = 24.dp), textAlign = androidx.compose.ui.text.style.TextAlign.Center)
                                        IconButton(
                                            onClick = { commerce.changeQty(line.product.id, line.quantity + 1); onChanged() },
                                            modifier = Modifier.size(34.dp)
                                        ) { Icon(Icons.Default.Add, "Crește", modifier = Modifier.size(16.dp)) }
                                    }
                                }
                                Spacer(Modifier.weight(1f))
                                if (unit != null) Text(moneyRonV107(unit * line.quantity), fontWeight = FontWeight.ExtraBold, color = Ink, fontSize = 13.sp)
                            }
                        }
                        IconButton(
                            onClick = { commerce.removeFromCart(line.product.id); onChanged() },
                            modifier = Modifier.size(34.dp)
                        ) { Icon(Icons.Default.Close, "Șterge", tint = Muted, modifier = Modifier.size(18.dp)) }
                    }
                }
            }

            item {
                ElevatedCard(
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.elevatedCardColors(containerColor = Color.White),
                    elevation = CardDefaults.elevatedCardElevation(defaultElevation = 1.dp)
                ) {
                    Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                        Text("Sumar comandă", fontSize = 17.sp, fontWeight = FontWeight.ExtraBold, color = Ink)
                        Row { Text("Subtotal", color = Muted); Spacer(Modifier.weight(1f)); Text(if (allPriced) moneyRonV107(subtotal) else "La checkout", fontWeight = FontWeight.Bold) }
                        Row { Text("Livrare", color = Muted); Spacer(Modifier.weight(1f)); Text("Calculată la checkout", fontSize = 12.sp, fontWeight = FontWeight.SemiBold) }
                        Row { Text("TVA", color = Muted); Spacer(Modifier.weight(1f)); Text("Inclus în prețurile afișate", fontSize = 12.sp, fontWeight = FontWeight.SemiBold) }
                        HorizontalDivider(color = Color(0xFFEAECF0))
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Total estimat", fontWeight = FontWeight.ExtraBold, fontSize = 15.sp)
                            Spacer(Modifier.weight(1f))
                            Text(if (allPriced) moneyRonV107(subtotal) else "—", fontWeight = FontWeight.ExtraBold, fontSize = 18.sp, color = AutoIdOrange)
                        }
                    }
                }
            }
        }

        Surface(color = Color.White, shadowElevation = 12.dp) {
            Column(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Lock, null, tint = Good, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(6.dp))
                    Text("Finalizare comandă în aplicație", fontSize = 10.sp, color = Muted)
                    Spacer(Modifier.weight(1f))
                    if (allPriced) Text(moneyRonV107(subtotal), fontWeight = FontWeight.ExtraBold, color = Ink)
                }
                Spacer(Modifier.height(8.dp))
                Button(
                    onClick = onCheckout,
                    modifier = Modifier.fillMaxWidth().height(56.dp),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Text("Continuă la finalizare", fontWeight = FontWeight.ExtraBold)
                    Spacer(Modifier.width(8.dp))
                    Icon(Icons.Default.ArrowForward, null, modifier = Modifier.size(18.dp))
                }
            }
        }
    }
}

@Composable private fun FavoritesV100(api:AutoIdApi,commerce:CommerceStore,onBack:()->Unit,onProduct:(Product)->Unit,onCart:()->Unit){var rows by remember{mutableStateOf<List<Product>>(emptyList())};var loading by remember{mutableStateOf(true)};val ids=commerce.wishlistIds();LaunchedEffect(ids){rows=withContext(Dispatchers.IO){ids.mapNotNull{id->runCatching{api.product(id)}.getOrNull()}};loading=false};Column(Modifier.fillMaxSize().padding(14.dp).statusBarsPadding()){Row(verticalAlignment=Alignment.CenterVertically){IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")};Text("Favorite",fontSize=22.sp,fontWeight=FontWeight.ExtraBold,modifier=Modifier.weight(1f));IconButton(onClick=onCart){Icon(Icons.Default.ShoppingCart,"Coș")}};if(loading)LinearProgressIndicator(Modifier.fillMaxWidth());LazyVerticalGrid(GridCells.Fixed(2),horizontalArrangement=Arrangement.spacedBy(10.dp),verticalArrangement=Arrangement.spacedBy(10.dp),contentPadding=PaddingValues(bottom=100.dp)){gridItems(rows){p->CatalogCard(p,true,{onProduct(p)},{commerce.toggleFavorite(p.id)},{commerce.addToCart(p)},{})}}}}
@Composable private fun NotificationsV100(onBack:()->Unit,onCart:()->Unit){LazyColumn(Modifier.fillMaxSize().padding(16.dp).statusBarsPadding(),verticalArrangement=Arrangement.spacedBy(10.dp)){item{Row(verticalAlignment=Alignment.CenterVertically){IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")};Text("Notificări",fontSize=22.sp,fontWeight=FontWeight.ExtraBold,modifier=Modifier.weight(1f));IconButton(onClick=onCart){Icon(Icons.Default.ShoppingCart,"Coș")}}};item{Notif(Icons.Default.Inventory2,"Produse în stoc","Aici vei primi alerte când produsele urmărite reintră în stoc.",Good)};item{Notif(Icons.Default.LocalOffer,"Promoții","Ofertele AutoID vor apărea aici după activarea notificărilor push.",AutoIdOrange)};item{Notif(Icons.Default.ReceiptLong,"Comenzi","Statusul comenzilor tale va apărea aici.",Color(0xFF2E90FA))}}}
@Composable private fun Notif(icon:androidx.compose.ui.graphics.vector.ImageVector,title:String,text:String,color:Color){ElevatedCard{Row(Modifier.padding(14.dp),verticalAlignment=Alignment.CenterVertically){Surface(shape=CircleShape,color=color.copy(alpha=.12f),modifier=Modifier.size(46.dp)){Box(contentAlignment=Alignment.Center){Icon(icon,null,tint=color)}};Spacer(Modifier.width(12.dp));Column{Text(title,fontWeight=FontWeight.Bold);Text(text,fontSize=12.sp,color=Muted)}}}}

@Composable private fun RfqV100(api:AutoIdApi,lines:List<CartLine>,onLines:(List<CartLine>)->Unit,onDismiss:()->Unit,onSent:()->Unit){var name by remember{mutableStateOf("")};var email by remember{mutableStateOf("")};var company by remember{mutableStateOf("")};var phone by remember{mutableStateOf("")};var message by remember{mutableStateOf("")};var busy by remember{mutableStateOf(false)};var status by remember{mutableStateOf("")};val scope=rememberCoroutineScope();AlertDialog(onDismissRequest=onDismiss,title={Text("Cerere de ofertă")},text={LazyColumn(verticalArrangement=Arrangement.spacedBy(8.dp)){item{Text("Produse în cerere",fontWeight=FontWeight.Bold)};items(lines,key={it.product.id}){l->Row(verticalAlignment=Alignment.CenterVertically){Text("${l.quantity} × ${l.product.name}",Modifier.weight(1f),fontSize=12.sp,maxLines=2);IconButton(onClick={onLines(lines.filterNot{it.product.id==l.product.id})}){Icon(Icons.Default.Close,"Șterge")}}};item{OutlinedTextField(name,{name=it},label={Text("Nume *")},modifier=Modifier.fillMaxWidth());OutlinedTextField(email,{email=it},label={Text("Email *")},modifier=Modifier.fillMaxWidth());OutlinedTextField(company,{company=it},label={Text("Companie")},modifier=Modifier.fillMaxWidth());OutlinedTextField(phone,{phone=it},label={Text("Telefon")},modifier=Modifier.fillMaxWidth());OutlinedTextField(message,{message=it},label={Text("Mesaj")},modifier=Modifier.fillMaxWidth(),minLines=2);if(status.isNotBlank())Text(status,fontSize=12.sp,color=if(status.contains("trimis"))Good else MaterialTheme.colorScheme.error)}}},confirmButton={Button(onClick={busy=true;scope.launch{runCatching{withContext(Dispatchers.IO){api.sendRfq(name,email,company,phone,message,lines)}}.onSuccess{if(it){status="Cererea a fost trimisă.";delay(700);onSent()}else status="Cererea nu a fost trimisă."}.onFailure{status=it.message?:"Eroare"};busy=false}},enabled=!busy&&name.isNotBlank()&&email.contains("@")&&lines.isNotEmpty()){Text(if(busy)"Se trimite..." else "Trimite cererea")}},dismissButton={TextButton(onClick=onDismiss){Text("Închide")}})}
@Composable private fun ConsultV100(api:AutoIdApi,onDismiss:()->Unit){var name by remember{mutableStateOf("")};var email by remember{mutableStateOf("")};var company by remember{mutableStateOf("")};var phone by remember{mutableStateOf("")};var message by remember{mutableStateOf("")};var busy by remember{mutableStateOf(false)};var status by remember{mutableStateOf("")};val scope=rememberCoroutineScope();AlertDialog(onDismissRequest=onDismiss,title={Text("Consultanță tehnică AutoID")},text={Column(verticalArrangement=Arrangement.spacedBy(7.dp)){OutlinedTextField(name,{name=it},label={Text("Nume *")});OutlinedTextField(email,{email=it},label={Text("Email *")});OutlinedTextField(company,{company=it},label={Text("Companie")});OutlinedTextField(phone,{phone=it},label={Text("Telefon")});OutlinedTextField(message,{message=it},label={Text("Cu ce te putem ajuta? *")},minLines=3);if(status.isNotBlank())Text(status,fontSize=12.sp)}},confirmButton={Button(onClick={busy=true;scope.launch{runCatching{withContext(Dispatchers.IO){api.requestConsultation(name,email,company,phone,message)}}.onSuccess{status=if(it)"Solicitarea a fost trimisă." else "Nu a putut fi trimisă."}.onFailure{status=it.message?:"Eroare"};busy=false}},enabled=!busy&&name.isNotBlank()&&email.contains("@")&&message.isNotBlank()){Text("Trimite")}},dismissButton={TextButton(onClick=onDismiss){Text("Închide")}})}
