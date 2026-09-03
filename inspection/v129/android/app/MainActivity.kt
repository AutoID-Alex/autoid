package ro.autoid.app

import android.content.Intent
import android.Manifest
import android.os.Build
import androidx.core.app.ActivityCompat
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.codescanner.GmsBarcodeScannerOptions
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import ro.autoid.app.data.*
import ro.autoid.app.ui.theme.AutoIdOrange
import ro.autoid.app.ui.theme.AutoIdTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val api = AutoIdApi()
        val session = SessionStore(this)
        val commerce = CommerceStore(this)
        intent?.getLongExtra("review_order_id",0L)?.takeIf{it>0}?.let{session.pendingReviewOrderId=it}
        OrderNotificationV126.schedule(this)
        OrderNotificationV126.syncNow(this)
        FirebaseBootstrapV128.refreshAndRegister(this,api,session)
        if(PrivacyConsentStoreV128(this).get().transactionalNotifications && Build.VERSION.SDK_INT>=33 && ActivityCompat.checkSelfPermission(this,Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED){ActivityCompat.requestPermissions(this,arrayOf(Manifest.permission.POST_NOTIFICATIONS),126)}
        setContent { AutoIdTheme { AutoIdAppV100(api, session, commerce, ::scan) } }
    }

    override fun onNewIntent(intent:Intent){super.onNewIntent(intent);setIntent(intent);intent.getLongExtra("review_order_id",0L).takeIf{it>0}?.let{SessionStore(this).pendingReviewOrderId=it;recreate()}}

    private fun openUrl(url: String) = startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))

    private fun scan(onResult: (String) -> Unit) {
        val options = GmsBarcodeScannerOptions.Builder().setBarcodeFormats(
            Barcode.FORMAT_QR_CODE,
            Barcode.FORMAT_DATA_MATRIX,
            Barcode.FORMAT_EAN_13,
            Barcode.FORMAT_EAN_8,
            Barcode.FORMAT_CODE_128,
            Barcode.FORMAT_UPC_A,
            Barcode.FORMAT_UPC_E
        ).enableAutoZoom().build()
        GmsBarcodeScanning.getClient(this, options).startScan().addOnSuccessListener { code ->
            code.rawValue?.takeIf(String::isNotBlank)?.let(onResult)
        }
    }
}

enum class Tab(val label: String) {
    Home("Acasă"),
    Categories("Categorii"),
    Cart("Coș"),
    Account("Cont")
}

@Composable
fun AutoIdApp(
    api: AutoIdApi,
    session: SessionStore,
    commerce: CommerceStore,
    scan: ((String) -> Unit) -> Unit,
    openUrl: (String) -> Unit
) {
    var tab by remember { mutableStateOf(Tab.Home) }
    var selectedProduct by remember { mutableStateOf<Product?>(null) }
    var category by remember { mutableStateOf<ProductCategory?>(null) }
    var search by remember { mutableStateOf("") }
    var cartTick by remember { mutableIntStateOf(0) }
    var favoriteTick by remember { mutableIntStateOf(0) }
    var showAi by remember { mutableStateOf(false) }
    var aiProductId by remember { mutableStateOf<Long?>(null) }
    var menuOpen by remember { mutableStateOf(false) }
    var nativeContent by remember { mutableStateOf<NativeContent?>(null) }
    var nativeResource by remember { mutableStateOf<SupportResource?>(null) }
    var showCheckout by remember { mutableStateOf(false) }
    val context = androidx.compose.ui.platform.LocalContext.current
    val appScope = rememberCoroutineScope()
    fun addCart(p:Product){ commerce.addToCart(p); cartTick++; Toast.makeText(context, "${p.name} adăugat în coș · ${commerce.cartCount()} produse", Toast.LENGTH_SHORT).show() }

    if (showCheckout) {
        CheckoutV117(api, session, commerce, onBack={showCheckout=false}, onDone={commerce.clearCart();cartTick++;showCheckout=false;tab=Tab.Account})
        return
    }

    if (nativeContent != null) {
        NativeContentScreen(nativeContent!!, onBack={nativeContent=null})
        return
    }
    if (nativeResource != null) {
        NativeResourceScreen(nativeResource!!, onBack={nativeResource=null})
        return
    }

    if (showAi) {
        NativeAiChatScreen(api=api, productId=aiProductId, onBack={showAi=false;aiProductId=null})
        return
    }

    if (selectedProduct != null) {
        ProductDetail(
            seed = selectedProduct!!,
            api = api,
            commerce = commerce,
            onBack = { selectedProduct = null },
            onCart = { addCart(it) },
            onSupport = { _ -> aiProductId=selectedProduct?.id; showAi=true },
            onProduct = { commerce.addRecent(it); selectedProduct=it },
            onResource = { nativeResource=it },
            onFavorite = { commerce.toggleFavorite(it.id); favoriteTick++ }
        )
        return
    }

    if (category != null) {
        ProductListV08(
            api = api,
            commerce = commerce,
            category = category,
            initialSearch = search,
            onBack = { category = null },
            onProduct = { commerce.addRecent(it); selectedProduct = it },
            onCart = { addCart(it) },
            onFavorite = { commerce.toggleFavorite(it.id); favoriteTick++ },
            scan = scan,
            onHeaderCart = { category=null; tab=Tab.Cart }
        )
        return
    }

    if(menuOpen){
        AutoIdMenu(api=api,onClose={menuOpen=false},onOpen={item->
            menuOpen=false
            when(item.nativeKind){
                "home" -> { tab=Tab.Home; category=null; selectedProduct=null }
                "category" -> { search=""; category=ProductCategory(item.objectId,item.title,0) }
                "product" -> appScope.launch { runCatching { withContext(Dispatchers.IO){ api.product(item.objectId) } }.onSuccess { commerce.addRecent(it); selectedProduct=it } }
                "cart" -> tab=Tab.Cart
                "account" -> tab=Tab.Account
                "support" -> { aiProductId=null; showAi=true }
                "page" -> appScope.launch { runCatching { withContext(Dispatchers.IO){ api.content(item.objectId) } }.onSuccess { nativeContent=it }.onFailure { Toast.makeText(context,"Conținutul nu poate fi încărcat în aplicație.",Toast.LENGTH_SHORT).show() } }
                else -> Toast.makeText(context,"Secțiunea este disponibilă doar în aplicație după mapare.",Toast.LENGTH_SHORT).show()
            }
        })
    }

    Scaffold(
        containerColor = Color(0xFFF6F7F9),
        bottomBar = {
            NavigationBar(containerColor = Color.White) {
                Tab.entries.forEach { item ->
                    val count = if (item == Tab.Cart) commerce.cartCount() else 0
                    NavigationBarItem(
                        selected = tab == item,
                        onClick = { tab = item },
                        icon = {
                            BadgedBox(badge = { if (count > 0) Badge { Text(count.toString()) } }) {
                                Icon(imageVector = when (item) {
                                    Tab.Home -> Icons.Default.Home
                                    Tab.Categories -> Icons.Default.Category
                                    Tab.Cart -> Icons.Default.ShoppingCart
                                    Tab.Account -> Icons.Default.Person
                                }, contentDescription = item.label)
                            }
                        },
                        label = { Text(item.label) }
                    )
                }
            }
        },
    ) { pad ->
        Box(Modifier.padding(pad).fillMaxSize()) {
            when (tab) {
                Tab.Home -> HomeScreenV08(
                    api,
                    commerce,
                    onSearch = { search = it; category = ProductCategory(0, "Rezultate", 0) },
                    onCategory = { category = it },
                    onProduct = { commerce.addRecent(it); selectedProduct = it },
                    onAi = { _ -> aiProductId=null; showAi=true },
                    onCart = { addCart(it) },
                    onFavorite = { commerce.toggleFavorite(it.id); favoriteTick++ },
                    scan = scan,
                    onMenu = { menuOpen=true },
                    onHeaderCart = { tab=Tab.Cart }
                )
                Tab.Categories -> CategoriesScreenV08(
                    api,
                    onCategory = { category = it },
                    onSearch = { search = it; category = ProductCategory(0, "Rezultate", 0) },
                    scan = scan,
                    onMenu = { menuOpen=true },
                    cartCount = commerce.cartCount(),
                    onHeaderCart = { tab=Tab.Cart }
                )
                Tab.Cart -> CartScreenV08(commerce, onProduct = { selectedProduct = it }, onChanged = { cartTick++ }, onCheckout = { showCheckout=true })
                Tab.Account -> AccountScreenV08(api, session, commerce, onProduct = { selectedProduct = it }, onHeaderCart = { tab=Tab.Cart })
            }
        }
    }
}

@Composable
fun GlobalHeader(title: String = "AutoID", cartCount: Int = 0, notificationCount: Int = 0, onMenu: (() -> Unit)? = null) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        if(onMenu!=null){ IconButton(onClick=onMenu){ Icon(Icons.Default.Menu,"Meniu") }; Spacer(Modifier.width(4.dp)) }
        if (title == "AutoID") AsyncImage(
            model = "https://www.autoid.ro/wp-content/uploads/Logo-AutoID.jpg",
            contentDescription = "AutoID", modifier = Modifier.width(126.dp).height(42.dp)
        ) else Text(title, color = Color(0xFF101828), fontSize = 24.sp, fontWeight = FontWeight.ExtraBold)
        Spacer(Modifier.weight(1f))
        if (notificationCount > 0) BadgedBox(badge = { Badge { Text(notificationCount.toString()) } }) { Icon(Icons.Default.Notifications, "Notificări") }
        Spacer(Modifier.width(12.dp))
        BadgedBox(badge = { if (cartCount > 0) Badge { Text(cartCount.toString()) } }) { Icon(Icons.Default.ShoppingCart, "Coș") }
    }
}

@Composable
fun SearchBarBox(
    value: String,
    onValue: (String) -> Unit,
    onSearch: () -> Unit,
    onScan: () -> Unit,
    placeholder: String = "Caută produse, SKU, brand, model..."
) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
        OutlinedTextField(
            value,
            onValue,
            label = { Text(placeholder) },
            singleLine = true,
            modifier = Modifier.weight(1f),
            shape = RoundedCornerShape(16.dp)
        )
        FilledTonalButton(onClick = onScan, contentPadding = PaddingValues(horizontal = 14.dp)) { Icon(Icons.Default.QrCodeScanner, "Scanează") }
    }
    if (value.isNotBlank()) TextButton(onClick = onSearch) { Text("Caută „$value”") }
}

@Composable
fun HomeScreen(
    api: AutoIdApi,
    commerce: CommerceStore,
    onSearch: (String) -> Unit,
    onCategory: (ProductCategory) -> Unit,
    onProduct: (Product) -> Unit,
    onAi: (String) -> Unit,
    onCart: (Product) -> Unit,
    onFavorite: (Product) -> Unit,
    scan: ((String) -> Unit) -> Unit,
    onMenu: () -> Unit = {}
) {
    var q by remember { mutableStateOf("") }
    var products by remember { mutableStateOf<List<Product>>(emptyList()) }
    var cats by remember { mutableStateOf<List<ProductCategory>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }

    LaunchedEffect(Unit) {
        withContext(Dispatchers.IO) {
            runCatching {
                products = api.products()
                cats = api.categories()
            }
        }
        loading = false
    }

    LazyColumn(
        Modifier.fillMaxSize().padding(horizontal = 16.dp).statusBarsPadding(),
        verticalArrangement = Arrangement.spacedBy(18.dp),
        contentPadding = PaddingValues(bottom = 24.dp)
    ) {
        item {
            Spacer(Modifier.height(4.dp))
            GlobalHeader(cartCount = commerce.cartCount(), onMenu=onMenu)
            Spacer(Modifier.height(12.dp))
            SearchBarBox(q, { q = it }, { onSearch(q) }, { scan { onSearch(it) } })
        }
        item { HeroCard(onShop = { onSearch("") }, onAi = { onAi("Recomandă-mi echipamente pentru afacerea mea") }) }
        item {
            SectionTitle("Categorii rapide", "Vezi toate")
            LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                items(cats.take(8)) { c -> CategoryChip(c) { onCategory(c) } }
            }
        }
        item { AiPromo { onAi("Ajută-mă să aleg produsul potrivit") } }
        if (loading) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
        if (products.isNotEmpty()) {
            item { SectionTitle("În stoc AutoID", "Livrare rapidă") }
            items(products.take(6)) { p ->
                ProductCard(p, commerce.isFavorite(p.id), { onProduct(p) }, { onCart(p) }, { onFavorite(p) })
            }
        }
        val recent = commerce.recent()
        if (recent.isNotEmpty()) {
            item { SectionTitle("Vizualizate recent", "") }
            items(recent.take(4)) { p ->
                ProductCard(p, commerce.isFavorite(p.id), { onProduct(p) }, { onCart(p) }, { onFavorite(p) })
            }
        }
        item { SupportPromo { onAi("Am nevoie de suport tehnic") } }
    }
}

@Composable
fun HeroCard(onShop: () -> Unit, onAi: () -> Unit) {
    Card(shape = RoundedCornerShape(20.dp), colors = CardDefaults.cardColors(containerColor = Color(0xFF171B26))) {
        Column(Modifier.padding(22.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Echipamente AutoID pentru afacerea ta", color = Color.White, fontSize = 24.sp, fontWeight = FontWeight.ExtraBold)
            Text("Scanare, etichetare, mobilitate, RFID și soluții profesionale.", color = Color(0xFFD0D5DD))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = onShop) { Text("Vezi produsele") }
                OutlinedButton(onClick = onAi, colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White)) { Text("Întreabă AI") }
            }
        }
    }
}

@Composable
fun AiPromo(onClick: () -> Unit) {
    ElevatedCard(onClick = onClick, shape = RoundedCornerShape(18.dp)) {
        Row(Modifier.padding(18.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.SmartToy, contentDescription = null, tint = AutoIdOrange, modifier = Modifier.size(30.dp))
            Spacer(Modifier.width(14.dp))
            Column(Modifier.weight(1f)) {
                Text("Nu știi ce echipament să alegi?", fontWeight = FontWeight.Bold)
                Text("AutoID AI recomandă, compară și verifică compatibilitatea.", fontSize = 13.sp, color = Color(0xFF667085))
            }
            Text("›", fontSize = 26.sp)
        }
    }
}

@Composable
fun SupportPromo(onClick: () -> Unit) {
    ElevatedCard(onClick = onClick, shape = RoundedCornerShape(18.dp)) {
        Column(Modifier.padding(18.dp)) {
            Text("Support Center", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text("Drivere, firmware, documentație, video și troubleshooting pentru echipamentele tale.", color = Color(0xFF667085))
            Spacer(Modifier.height(8.dp))
            Text("Caută model sau problemă →", color = AutoIdOrange, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
fun SectionTitle(title: String, action: String) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(title, fontSize = 19.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.weight(1f))
        if (action.isNotBlank()) Text(action, fontSize = 12.sp, color = AutoIdOrange)
    }
}

@Composable
fun CategoryChip(c: ProductCategory, onClick: () -> Unit) {
    ElevatedCard(onClick = onClick, shape = RoundedCornerShape(16.dp), modifier = Modifier.width(142.dp)) {
        Column(Modifier.padding(14.dp)) {
            if (c.imageUrl != null) AsyncImage(c.imageUrl, c.name, Modifier.fillMaxWidth().height(74.dp))
            Text(c.name, fontWeight = FontWeight.Bold, maxLines = 2, overflow = TextOverflow.Ellipsis)
            Text("${c.count} produse", fontSize = 11.sp, color = Color(0xFF667085))
        }
    }
}

@Composable
fun CategoriesScreen(
    api: AutoIdApi,
    onCategory: (ProductCategory) -> Unit,
    onSearch: (String) -> Unit,
    scan: ((String) -> Unit) -> Unit,
    onMenu: () -> Unit = {}
) {
    var cats by remember { mutableStateOf<List<ProductCategory>>(emptyList()) }
    var q by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        runCatching { withContext(Dispatchers.IO) { api.categories() } }
            .onSuccess { cats = it }
            .onFailure { error = it.message }
    }

    LazyColumn(
        Modifier.fillMaxSize().padding(16.dp).statusBarsPadding(),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            GlobalHeader("Categorii", onMenu=onMenu)
            Spacer(Modifier.height(10.dp))
            SearchBarBox(q, { q = it }, { onSearch(q) }, { scan { onSearch(it) } })
        }
        error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
        items(cats) { c ->
            ElevatedCard(onClick = { onCategory(c) }, shape = RoundedCornerShape(16.dp)) {
                Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    if (c.imageUrl != null) AsyncImage(c.imageUrl, c.name, Modifier.size(64.dp))
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Text(c.name, fontWeight = FontWeight.Bold)
                        Text("${c.count} produse", color = Color(0xFF667085))
                    }
                    Text("›", fontSize = 24.sp)
                }
            }
        }
    }
}

@Composable
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

@Composable
fun ProductCard(
    p: Product,
    favorite: Boolean,
    onClick: () -> Unit,
    onCart: () -> Unit,
    onFavorite: () -> Unit
) {
    ElevatedCard(shape = RoundedCornerShape(16.dp), modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.clickable(onClick = onClick).padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(94.dp).background(Color.White, RoundedCornerShape(12.dp)), contentAlignment = Alignment.Center) {
                AsyncImage(p.imageUrl, p.name, Modifier.fillMaxSize().padding(5.dp))
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(p.brand.ifBlank { p.category }, fontSize = 11.sp, color = AutoIdOrange, fontWeight = FontWeight.Bold)
                Text(p.name, maxLines = 2, overflow = TextOverflow.Ellipsis, fontWeight = FontWeight.Bold)
                if (p.sku.isNotBlank()) Text("SKU: ${p.sku}", fontSize = 10.sp, color = Color(0xFF667085))
                if (p.msrpEuro.isNotBlank()) Text("MSRP: ${p.msrpEuro}", fontSize = 13.sp, color = Color(0xFF667085), fontWeight = FontWeight.ExtraBold, textDecoration = androidx.compose.ui.text.style.TextDecoration.LineThrough)
                if (p.autoIdEuro.isNotBlank()) Text("AutoID: ${p.autoIdEuro}", color = AutoIdOrange, fontWeight = FontWeight.ExtraBold, fontSize = 13.sp)
                Text(p.priceRangeInclVat.ifBlank { p.currentInclVat.ifBlank { p.price } }, color = Color(0xFF101828), fontWeight = FontWeight.Bold, fontSize = 13.sp)
                if ((p.stockAutoId ?: 0) > 0 || (p.stockDistributor ?: 0) > 0) Text(listOfNotNull(p.stockAutoId?.takeIf { it > 0 }?.let { "$it în stoc" }, p.stockDistributor?.takeIf { it > 0 }?.let { "$it livrare în 5–7 zile" }).joinToString(" · "), color = if ((p.stockAutoId ?: 0) > 0) Color(0xFF16803A) else Color(0xFF667085), fontSize = 10.sp, fontWeight = FontWeight.Bold)
                else Text(p.stockLabel, color = if (p.inStock) Color(0xFF16803A) else Color(0xFFB42318), fontSize = 10.sp)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = onFavorite) { Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "Favorite", tint = if (favorite) AutoIdOrange else LocalContentColor.current) }
                    if (p.groupedChildIds.isNotEmpty()) FilledTonalButton(onClick = onClick) { Text("Variante") }
                    else Button(onClick = onCart, enabled = p.inStock, contentPadding = PaddingValues(horizontal = 12.dp)) { Icon(Icons.Default.AddShoppingCart, null); Spacer(Modifier.width(4.dp)); Text("Adaugă") }
                }
            }
        }
    }
}

@Composable
fun ProductDetail(
    seed: Product,
    api: AutoIdApi,
    commerce: CommerceStore,
    onBack: () -> Unit,
    onCart: (Product) -> Unit,
    onSupport: (String) -> Unit,
    onOpen: (String) -> Unit,
    onFavorite: (Product) -> Unit
) {
    var p by remember { mutableStateOf(seed) }
    var qty by remember { mutableIntStateOf(1) }
    var showSpecs by remember { mutableStateOf(false) }
    var showDesc by remember { mutableStateOf(false) }

    LaunchedEffect(seed.id) {
        runCatching { withContext(Dispatchers.IO) { api.product(seed.id) } }.onSuccess { p = it; commerce.addRecent(it) }
    }

    Scaffold(
        containerColor = Color(0xFFF6F7F9),
        bottomBar = {
            Surface(shadowElevation = 8.dp) {
                Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text(p.price, color = AutoIdOrange, fontWeight = FontWeight.ExtraBold, fontSize = 20.sp)
                        Text(p.stockLabel, fontSize = 11.sp, color = if (p.inStock) Color(0xFF16803A) else Color(0xFFB42318))
                    }
                    Button(onClick = { repeat(qty) { onCart(p) } }, enabled = p.inStock, modifier = Modifier.height(48.dp)) {
                        Text("Adaugă în coș")
                    }
                }
            }
        }
    ) { pad ->
        Column(
            Modifier.padding(pad).fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp).statusBarsPadding(),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                TextButton(onClick = onBack) { Text("‹ Înapoi") }
                Spacer(Modifier.weight(1f))
                TextButton(onClick = { onFavorite(p) }) { Text(if (commerce.isFavorite(p.id)) "♥ Favorite" else "♡ Favorite") }
            }
            Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = Color.White)) {
                Box(Modifier.fillMaxWidth().height(290.dp), contentAlignment = Alignment.Center) {
                    AsyncImage(p.imageUrl, p.name, Modifier.fillMaxSize().padding(20.dp))
                }
            }
            Text(p.brand.ifBlank { p.category }, color = AutoIdOrange, fontWeight = FontWeight.Bold)
            Text(p.name, fontSize = 25.sp, fontWeight = FontWeight.ExtraBold)
            if (p.sku.isNotBlank()) Text("SKU: ${p.sku}", color = Color(0xFF667085))
            Text(p.price, fontSize = 25.sp, fontWeight = FontWeight.ExtraBold, color = AutoIdOrange)
            Text(
                if (p.inStock) "● ${p.stockLabel}" else p.stockLabel,
                color = if (p.inStock) Color(0xFF16803A) else Color(0xFFB42318),
                fontWeight = FontWeight.Bold
            )
            Text("Livrare estimată conform disponibilității afișate de AutoID.", fontSize = 12.sp, color = Color(0xFF667085))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Cantitate", fontWeight = FontWeight.Bold)
                Spacer(Modifier.weight(1f))
                OutlinedButton(onClick = { if (qty > 1) qty-- }) { Text("−") }
                Text("  $qty  ")
                OutlinedButton(onClick = { qty++ }) { Text("+") }
            }
            ElevatedCard(onClick = { onSupport(p.supportQuery.ifBlank { p.name }) }, shape = RoundedCornerShape(18.dp)) {
                Column(Modifier.padding(18.dp)) {
                    Text("✦ Ai nevoie de ajutor?", fontWeight = FontWeight.ExtraBold, fontSize = 18.sp)
                    Text("AutoID AI poate verifica compatibilitatea și găsi documentația tehnică pentru acest produs.")
                    Text("Întreabă AI →", color = AutoIdOrange, fontWeight = FontWeight.Bold)
                }
            }
            if (p.description.isNotBlank()) {
                OutlinedCard(Modifier.fillMaxWidth().clickable { showDesc = !showDesc }) {
                    Column(Modifier.padding(16.dp)) {
                        Text("Descriere ${if (showDesc) "⌃" else "⌄"}", fontWeight = FontWeight.Bold)
                        if (showDesc) Text(p.description)
                    }
                }
            }
            if (p.attributes.isNotEmpty()) {
                OutlinedCard(Modifier.fillMaxWidth().clickable { showSpecs = !showSpecs }) {
                    Column(Modifier.padding(16.dp)) {
                        Text("Specificații tehnice ${if (showSpecs) "⌃" else "⌄"}", fontWeight = FontWeight.Bold)
                        if (showSpecs) p.attributes.take(20).forEach { a ->
                            Row(Modifier.fillMaxWidth().padding(vertical = 5.dp)) {
                                Text(a.name, Modifier.weight(.45f), fontWeight = FontWeight.Medium)
                                Text(a.values.joinToString(", "), Modifier.weight(.55f))
                            }
                        }
                    }
                }
            }
            OutlinedButton(onClick = { onSupport(p.supportQuery.ifBlank { p.name }) }, modifier = Modifier.fillMaxWidth()) {
                Text("Deschide suport tehnic")
            }
            if (p.permalink.isNotBlank()) TextButton(onClick = { onOpen(p.permalink) }, modifier = Modifier.fillMaxWidth()) {
                Text("Vezi și pe AutoID.ro")
            }
        }
    }
}

@Composable
fun AiScreen(
    api: AutoIdApi,
    commerce: CommerceStore,
    initial: String,
    onProduct: (Product) -> Unit,
    onCart: (Product) -> Unit,
    onOpen: (String) -> Unit
) {
    var q by remember(initial) { mutableStateOf(initial) }
    var products by remember { mutableStateOf<List<Product>>(emptyList()) }
    var resources by remember { mutableStateOf<List<SupportResource>>(emptyList()) }
    var answer by remember { mutableStateOf("Spune-mi ce vrei să cumperi sau ce problemă tehnică ai. Pot căuta produse și resurse AutoID relevante.") }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    fun ask(text: String) {
        q = text
        busy = true
        scope.launch {
            val p = runCatching { withContext(Dispatchers.IO) { api.products(text) } }.getOrDefault(emptyList())
            val r = runCatching { withContext(Dispatchers.IO) { api.support(text) } }.getOrDefault(emptyList())
            products = p.take(4)
            resources = r.take(8)
            answer = when {
                p.isNotEmpty() && r.isNotEmpty() -> "Am găsit atât produse, cât și resurse tehnice relevante. Poți deschide produsul sau documentația direct din aplicație."
                p.isNotEmpty() -> "Am găsit produse relevante. Deschide un produs pentru specificații, compatibilitate și suport contextual."
                r.isNotEmpty() -> "Am găsit resurse tehnice relevante pentru problema/modelul menționat."
                else -> "Nu am găsit încă o potrivire exactă. Încearcă modelul complet, SKU-ul sau descrie problema mai specific."
            }
            busy = false
        }
    }

    LaunchedEffect(initial) { if (initial.isNotBlank()) ask(initial) }

    LazyColumn(
        Modifier.fillMaxSize().padding(16.dp).statusBarsPadding(),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        contentPadding = PaddingValues(bottom = 24.dp)
    ) {
        item {
            GlobalHeader("AutoID AI", commerce.cartCount())
            Text("Shopping & Technical Assistant", color = Color(0xFF667085))
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                AssistChip({ ask("Recomandă-mi un produs") }, { Text("Recomandă") })
                AssistChip({ ask("Compară două produse") }, { Text("Compară") })
            }
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                AssistChip({ ask("Am o problemă tehnică") }, { Text("Problemă tehnică") })
                AssistChip({ ask("Verifică compatibilitatea") }, { Text("Compatibilitate") })
            }
        }
        item { ElevatedCard(shape = RoundedCornerShape(16.dp)) { Text(answer, Modifier.padding(16.dp)) } }
        item {
            OutlinedTextField(
                q,
                { q = it },
                placeholder = { Text("Scrie întrebarea ta...") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 2,
                maxLines = 4,
                shape = RoundedCornerShape(16.dp)
            )
            Button(onClick = { ask(q) }, enabled = q.isNotBlank() && !busy, modifier = Modifier.fillMaxWidth()) {
                Text(if (busy) "Caut..." else "Trimite către AutoID AI")
            }
        }
        if (busy) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
        if (products.isNotEmpty()) item { SectionTitle("Produse recomandate", "") }
        items(products) { p ->
            ProductCard(p, commerce.isFavorite(p.id), { onProduct(p) }, { onCart(p) }, { commerce.toggleFavorite(p.id) })
        }
        if (resources.isNotEmpty()) item { SectionTitle("Resurse tehnice", "") }
        items(resources) { r ->
            ElevatedCard(onClick = { onOpen(r.url) }, shape = RoundedCornerShape(14.dp)) {
                Column(Modifier.padding(14.dp)) {
                    Text(r.type.uppercase(), fontSize = 10.sp, color = AutoIdOrange, fontWeight = FontWeight.Bold)
                    Text(r.title, fontWeight = FontWeight.Bold)
                    if (r.summary.isNotBlank()) Text(r.summary, maxLines = 2, overflow = TextOverflow.Ellipsis, fontSize = 12.sp, color = Color(0xFF667085))
                    Text("Deschide →", color = AutoIdOrange)
                }
            }
        }
    }
}

@Composable
fun CartScreen(commerce: CommerceStore, onProduct: (Product) -> Unit, onChanged: () -> Unit) {
    var tick by remember { mutableIntStateOf(0) }
    val lines = remember(tick) { commerce.cart() }
    val total = lines.sumOf { line -> parseMoney(line.product.price) * line.quantity }

    Column(Modifier.fillMaxSize().padding(16.dp).statusBarsPadding()) {
        GlobalHeader("Coș", commerce.cartCount())
        Text("${commerce.cartCount()} produse", color = Color(0xFF667085))
        Spacer(Modifier.height(10.dp))
        if (lines.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("Coșul este gol", fontSize = 22.sp, fontWeight = FontWeight.Bold)
                    Text("Adaugă produse din catalog sau din recomandările AI.")
                }
            }
            return
        }
        LazyColumn(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(lines, key = { it.product.id }) { line ->
                ElevatedCard(shape = RoundedCornerShape(14.dp)) {
                    Row(Modifier.clickable { onProduct(line.product) }.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        AsyncImage(line.product.imageUrl, line.product.name, Modifier.size(68.dp))
                        Spacer(Modifier.width(10.dp))
                        Column(Modifier.weight(1f)) {
                            Text(line.product.name, maxLines = 2, fontWeight = FontWeight.Bold)
                            Text(line.product.price, color = AutoIdOrange)
                            Row {
                                TextButton(onClick = { commerce.changeQty(line.product.id, line.quantity - 1); tick++; onChanged() }) { Text("−") }
                                Text("${line.quantity}", Modifier.padding(top = 12.dp))
                                TextButton(onClick = { commerce.changeQty(line.product.id, line.quantity + 1); tick++; onChanged() }) { Text("+") }
                                TextButton(onClick = { commerce.removeFromCart(line.product.id); tick++; onChanged() }) { Text("Șterge") }
                            }
                        }
                    }
                }
            }
        }
        ElevatedCard {
            Column(Modifier.padding(16.dp)) {
                Row { Text("Subtotal", Modifier.weight(1f)); Text(formatLei(total), fontWeight = FontWeight.Bold) }
                Text("Transportul și TVA-ul final se confirmă la checkout.", fontSize = 11.sp, color = Color(0xFF667085))
                Spacer(Modifier.height(8.dp))
                Button(onClick = {}, modifier = Modifier.fillMaxWidth()) { Text("Finalizare comandă") }
                Text(
                    "Checkout v0.3: review UI pregătit; plasarea server-side rămâne dezactivată până la validarea endpointului write.",
                    fontSize = 10.sp,
                    color = Color(0xFF667085),
                    modifier = Modifier.padding(top = 6.dp)
                )
            }
        }
    }
}

@Composable
fun AccountScreen(api: AutoIdApi, session: SessionStore, commerce: CommerceStore, onProduct: (Product) -> Unit) {
    var email by remember { mutableStateOf(session.customerEmail) }
    var pass by remember { mutableStateOf("") }
    var msg by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var orders by remember { mutableStateOf<List<Order>>(emptyList()) }
    val token = session.accessToken

    LaunchedEffect(token) {
        if (token != null) runCatching { withContext(Dispatchers.IO) { api.orders(token) } }.onSuccess { orders = it }
    }

    LazyColumn(
        Modifier.fillMaxSize().padding(16.dp).statusBarsPadding(),
        verticalArrangement = Arrangement.spacedBy(10.dp),
        contentPadding = PaddingValues(bottom = 24.dp)
    ) {
        item { GlobalHeader("Contul meu", commerce.cartCount()) }
        if (token == null) {
            item {
                ElevatedCard {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text("Autentificare AutoID", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                        OutlinedTextField(email, { email = it }, label = { Text("Email") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(pass, { pass = it }, label = { Text("Parolă") }, visualTransformation = PasswordVisualTransformation(), singleLine = true, modifier = Modifier.fillMaxWidth())
                        Button(onClick = { busy = true }, enabled = !busy && email.isNotBlank() && pass.isNotBlank(), modifier = Modifier.fillMaxWidth()) {
                            Text(if (busy) "Se conectează..." else "Autentificare")
                        }
                        Text(msg, color = if (msg.contains("reușită")) Color(0xFF16803A) else MaterialTheme.colorScheme.error)
                    }
                }
            }
            item {
                LaunchedEffect(busy) {
                    if (busy) {
                        runCatching { withContext(Dispatchers.IO) { api.login(email, pass) } }
                            .onSuccess { session.saveLogin(it); msg = "Autentificare reușită" }
                            .onFailure { msg = it.message ?: "Eroare" }
                        busy = false
                    }
                }
            }
        } else {
            item {
                ElevatedCard {
                    Column(Modifier.padding(16.dp)) {
                        Text("● ${session.customerEmail}", fontWeight = FontWeight.Bold)
                        Text("Client AutoID", color = Color(0xFF667085))
                        OutlinedButton(onClick = { session.clear(); msg = "Deconectat" }) { Text("Logout") }
                    }
                }
            }
            item { SectionTitle("Comenzile mele", "") }
            if (orders.isEmpty()) item { Text("Nu sunt comenzi disponibile sau încă se încarcă.", color = Color(0xFF667085)) }
            items(orders) { o ->
                ElevatedCard {
                    ListItem(
                        headlineContent = { Text("Comanda #${o.number}", fontWeight = FontWeight.Bold) },
                        supportingContent = { Text(o.status) },
                        trailingContent = { Text(o.total, fontWeight = FontWeight.Bold) }
                    )
                }
            }
        }
        val fav = commerce.wishlistIds()
        item { SectionTitle("Favorite", "${fav.size}") }
        if (fav.isEmpty()) item { Text("Nu ai produse favorite.", color = Color(0xFF667085)) }
        val recent = commerce.recent()
        if (recent.isNotEmpty()) {
            item { SectionTitle("Produse vizualizate recent", "") }
            items(recent.take(5)) { p ->
                OutlinedCard(Modifier.fillMaxWidth().clickable { onProduct(p) }) {
                    Text(p.name, Modifier.padding(14.dp), fontWeight = FontWeight.Medium)
                }
            }
        }
        item {
            SectionTitle("Setări", "")
            ListItem(headlineContent = { Text("Notificări") }, supportingContent = { Text("Pregătit pentru FCM în release-ul următor") })
            ListItem(headlineContent = { Text("Confidențialitate") })
            ListItem(headlineContent = { Text("Limba") }, trailingContent = { Text("Română") })
        }
    }
}

private fun parseMoney(v: String): Double = Regex("[0-9.,]+").find(v.replace(".", ""))?.value?.replace(",", ".")?.toDoubleOrNull() ?: 0.0
private fun formatLei(v: Double) = java.text.NumberFormat.getNumberInstance(java.util.Locale("ro", "RO")).format(v) + " lei"


@Composable
fun AutoIdMenu(api:AutoIdApi,onClose:()->Unit,onOpen:(NavItem)->Unit){
    var items by remember{mutableStateOf<List<NavItem>>(emptyList())}
    LaunchedEffect(Unit){runCatching{withContext(Dispatchers.IO){api.navigation()}}.onSuccess{items=it}}
    androidx.compose.ui.window.Dialog(onDismissRequest=onClose){
        Surface(shape=RoundedCornerShape(20.dp),color=Color.White,modifier=Modifier.fillMaxWidth().heightIn(max=650.dp)){
            Column(Modifier.padding(18.dp)){
                Row(verticalAlignment=Alignment.CenterVertically){Text("Meniu AutoID",fontSize=22.sp,fontWeight=FontWeight.ExtraBold,modifier=Modifier.weight(1f));IconButton(onClick=onClose){Icon(Icons.Default.Close,"Închide")}}
                LazyColumn{items(items){i->MenuRow(i,0,onOpen)}}
            }
        }
    }
}

@Composable private fun MenuRow(i:NavItem,depth:Int,onOpen:(NavItem)->Unit){
    Column{Row(Modifier.fillMaxWidth().clickable{if(i.nativeKind!="none")onOpen(i)}.padding(start=(depth*14).dp,top=10.dp,bottom=10.dp),verticalAlignment=Alignment.CenterVertically){
        Text(i.title,modifier=Modifier.weight(1f),fontWeight=if(depth==0)FontWeight.Bold else FontWeight.Medium);Icon(Icons.Default.ChevronRight,null,modifier=Modifier.size(18.dp))
    }; i.children.take(12).forEach{MenuRow(it,depth+1,onOpen)}}
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NativeContentScreen(content:NativeContent,onBack:()->Unit){
    Scaffold(topBar={CenterAlignedTopAppBar(title={Text(content.title,maxLines=1,overflow=TextOverflow.Ellipsis)},navigationIcon={IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")}})}){pad->
        Column(Modifier.padding(pad).fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp),verticalArrangement=Arrangement.spacedBy(12.dp)){
            Text(content.title,fontSize=25.sp,fontWeight=FontWeight.ExtraBold)
            Text(content.content,color=Color(0xFF344054),lineHeight=23.sp)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NativeResourceScreen(resource:SupportResource,onBack:()->Unit){
    Scaffold(topBar={CenterAlignedTopAppBar(title={Text(resource.type)},navigationIcon={IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")}})}){pad->
        Column(Modifier.padding(pad).fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp),verticalArrangement=Arrangement.spacedBy(14.dp)){
            Text(resource.title,fontSize=24.sp,fontWeight=FontWeight.ExtraBold)
            if(resource.summary.isNotBlank()) Text(resource.summary,color=Color(0xFF344054),lineHeight=23.sp)
            Surface(color=Color(0xFFFFF1E8),shape=RoundedCornerShape(14.dp)){Text("Resursa este deschisă în contextul aplicației AutoID. Nu te trimitem către browserul extern.",Modifier.padding(14.dp),color=Color(0xFF7A2E00),fontWeight=FontWeight.Medium)}
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NativeAiChatScreen(api:AutoIdApi,productId:Long?,onBack:()->Unit){
    var input by remember{mutableStateOf("")}; var busy by remember{mutableStateOf(false)}
    var messages by remember{mutableStateOf(listOf(AiMessage(false,"Salut! Sunt asistentul AutoID AI. Cu ce te pot ajuta?")))}; val scope=rememberCoroutineScope()
    fun send(){val q=input.trim();if(q.isBlank()||busy)return; input="";messages=messages+AiMessage(true,q);busy=true;scope.launch{val ans=runCatching{withContext(Dispatchers.IO){api.aiChat(q,productId)}}.getOrElse{"Nu pot contacta momentan asistentul AutoID: ${it.message}"};messages=messages+AiMessage(false,ans);busy=false}}
    Scaffold(topBar={CenterAlignedTopAppBar(title={Text("AutoID AI")},navigationIcon={IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")}})},bottomBar={Surface(shadowElevation=8.dp){Row(Modifier.fillMaxWidth().navigationBarsPadding().padding(10.dp),verticalAlignment=Alignment.CenterVertically){OutlinedTextField(input,{input=it},modifier=Modifier.weight(1f),placeholder={Text("Scrie întrebarea ta aici…")},maxLines=4);Spacer(Modifier.width(8.dp));IconButton(onClick={send()},enabled=!busy){Icon(Icons.Default.Send,"Trimite",tint=AutoIdOrange)}}}}){pad->
        LazyColumn(Modifier.padding(pad).fillMaxSize().padding(12.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){items(messages){m->Row(Modifier.fillMaxWidth(),horizontalArrangement=if(m.fromUser)Arrangement.End else Arrangement.Start){Surface(color=if(m.fromUser)AutoIdOrange else Color.White,shape=RoundedCornerShape(16.dp),modifier=Modifier.widthIn(max=320.dp)){Text(m.text,color=if(m.fromUser)Color.White else Color(0xFF101828),modifier=Modifier.padding(12.dp))}}};if(busy)item{LinearProgressIndicator(Modifier.fillMaxWidth())}}
    }
}
