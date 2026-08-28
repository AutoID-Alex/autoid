package ro.autoid.app

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
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
        setContent { AutoIdTheme { AutoIdApp(api, session, ::scan, ::openUrl) } }
    }

    private fun openUrl(url: String) = startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))

    private fun scan(onResult: (String) -> Unit) {
        val options = GmsBarcodeScannerOptions.Builder().setBarcodeFormats(
            Barcode.FORMAT_QR_CODE, Barcode.FORMAT_DATA_MATRIX, Barcode.FORMAT_EAN_13,
            Barcode.FORMAT_EAN_8, Barcode.FORMAT_CODE_128, Barcode.FORMAT_UPC_A, Barcode.FORMAT_UPC_E
        ).enableAutoZoom().build()
        GmsBarcodeScanning.getClient(this, options).startScan().addOnSuccessListener {
            it.rawValue?.takeIf(String::isNotBlank)?.let(onResult)
        }
    }
}

enum class Tab(val title: String, val mark: String) {
    Home("Acasă", "⌂"), Shop("Magazin", "▦"), Scan("Scan", "⌗"), Support("Suport", "?"), Account("Cont", "○")
}

@Composable
fun AutoIdApp(api: AutoIdApi, session: SessionStore, scan: ((String) -> Unit) -> Unit, openUrl: (String) -> Unit) {
    var tab by remember { mutableStateOf(Tab.Home) }
    var shopSearch by remember { mutableStateOf("") }
    var supportSearch by remember { mutableStateOf("") }

    Scaffold(
        containerColor = Color(0xFFF7F8FA),
        bottomBar = {
            NavigationBar(containerColor = Color.White) {
                Tab.entries.forEach { item ->
                    NavigationBarItem(
                        selected = tab == item,
                        onClick = { tab = item },
                        icon = { Text(item.mark, fontWeight = FontWeight.Bold, fontSize = 18.sp) },
                        label = { Text(item.title, fontSize = 11.sp) }
                    )
                }
            }
        }
    ) { pad ->
        Box(Modifier.padding(pad).fillMaxSize()) {
            when (tab) {
                Tab.Home -> HomeScreen(
                    api = api,
                    onShop = { q -> shopSearch = q; tab = Tab.Shop },
                    onSupport = { q -> supportSearch = q; tab = Tab.Support },
                    onOrders = { tab = Tab.Account },
                    onScan = { scan { code -> shopSearch = code; tab = Tab.Shop } }
                )
                Tab.Shop -> ShopScreen(api, shopSearch, openUrl) { q -> supportSearch = q; tab = Tab.Support }
                Tab.Scan -> ScanScreen(
                    scanProduct = { scan { code -> shopSearch = code; tab = Tab.Shop } },
                    scanSupport = { scan { code -> supportSearch = code; tab = Tab.Support } }
                )
                Tab.Support -> SupportScreen(api, supportSearch, openUrl)
                Tab.Account -> AccountHub(api, session, openUrl)
            }
        }
    }
}

@Composable
fun AutoIdTop(title: String, subtitle: String? = null) {
    Row(
        Modifier.fillMaxWidth().background(Color.White).statusBarsPadding().padding(horizontal = 18.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            Modifier.size(42.dp).background(AutoIdOrange, RoundedCornerShape(12.dp)),
            contentAlignment = Alignment.Center
        ) { Text("A", color = Color.White, fontWeight = FontWeight.Black, fontSize = 24.sp) }
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text("AutoID", color = AutoIdOrange, fontWeight = FontWeight.Black, fontSize = 22.sp)
            Text(title, fontWeight = FontWeight.Bold, fontSize = 16.sp)
            subtitle?.let { Text(it, color = Color(0xFF6B7280), fontSize = 12.sp) }
        }
    }
}

@Composable
fun HomeScreen(api: AutoIdApi, onShop: (String) -> Unit, onSupport: (String) -> Unit, onOrders: () -> Unit, onScan: () -> Unit) {
    var online by remember { mutableStateOf<Boolean?>(null) }
    var query by remember { mutableStateOf("") }
    LaunchedEffect(Unit) { online = withContext(Dispatchers.IO) { api.health() } }

    LazyColumn(contentPadding = PaddingValues(bottom = 22.dp)) {
        item { AutoIdTop("Magazin & Support", "Produse, comenzi și suport tehnic AutoID") }
        item {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                ElevatedCard(colors = CardDefaults.elevatedCardColors(containerColor = Color(0xFF171A21))) {
                    Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        Text("Găsește rapid produsul sau soluția tehnică", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 22.sp)
                        Text("Caută după model, SKU, EAN sau problemă tehnică.", color = Color(0xFFD1D5DB))
                        OutlinedTextField(
                            value = query,
                            onValueChange = { query = it },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                            label = { Text("Ex: ZT411, DS3608, P1083320-056") },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedContainerColor = Color.White,
                                unfocusedContainerColor = Color.White,
                                focusedTextColor = Color.Black,
                                unfocusedTextColor = Color.Black
                            )
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            Button(onClick = { onShop(query) }, modifier = Modifier.weight(1f)) { Text("Produse") }
                            OutlinedButton(
                                onClick = { onSupport(query) },
                                modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White)
                            ) { Text("Suport") }
                        }
                    }
                }

                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    QuickTile("Scanează", "EAN / QR / SKU", onScan, Modifier.weight(1f))
                    QuickTile("Comenzile mele", "Status și istoric", onOrders, Modifier.weight(1f))
                }
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    QuickTile("Support Center", "Manuale · drivere · video", { onSupport("") }, Modifier.weight(1f))
                    QuickTile("Catalog AutoID", "Produse profesionale", { onShop("") }, Modifier.weight(1f))
                }

                ElevatedCard {
                    Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.size(10.dp).background(if (online == true) Color(0xFF16A34A) else Color(0xFFF59E0B), RoundedCornerShape(20.dp)))
                        Spacer(Modifier.width(10.dp))
                        Column {
                            Text(if (online == true) "Conectat la AutoID.ro" else "Verificare conexiune AutoID", fontWeight = FontWeight.Bold)
                            Text("Aplicație v0.2 · Shop + Support", color = Color(0xFF6B7280), fontSize = 12.sp)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun QuickTile(title: String, subtitle: String, action: () -> Unit, modifier: Modifier = Modifier) {
    ElevatedCard(modifier.clickable { action() }) {
        Column(Modifier.padding(16.dp).heightIn(min = 86.dp), verticalArrangement = Arrangement.Center) {
            Text(title, fontWeight = FontWeight.Bold, fontSize = 16.sp)
            Spacer(Modifier.height(4.dp))
            Text(subtitle, color = Color(0xFF6B7280), fontSize = 12.sp)
        }
    }
}

@Composable
fun ShopScreen(api: AutoIdApi, initial: String, openUrl: (String) -> Unit, openSupport: (String) -> Unit) {
    var query by remember(initial) { mutableStateOf(initial) }
    var categories by remember { mutableStateOf<List<ProductCategory>>(emptyList()) }
    var selectedCategory by remember { mutableStateOf<Long?>(null) }
    var products by remember { mutableStateOf<List<Product>>(emptyList()) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        runCatching { withContext(Dispatchers.IO) { api.categories() } }.onSuccess { categories = it }
    }
    LaunchedEffect(query, selectedCategory) {
        delay(350)
        loading = true; error = null
        runCatching { withContext(Dispatchers.IO) { api.products(query, selectedCategory) } }
            .onSuccess { products = it }
            .onFailure { error = it.message ?: "Nu am putut încărca produsele." }
        loading = false
    }

    Column(Modifier.fillMaxSize()) {
        AutoIdTop("Magazin", "Catalogul AutoID")
        Column(Modifier.padding(horizontal = 14.dp, vertical = 10.dp)) {
            OutlinedTextField(
                query, { query = it },
                modifier = Modifier.fillMaxWidth(), singleLine = true,
                label = { Text("Caută produs, model, SKU sau EAN") }
            )
            if (categories.isNotEmpty()) {
                Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(top = 10.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(selected = selectedCategory == null, onClick = { selectedCategory = null }, label = { Text("Toate") })
                    categories.take(12).forEach { c ->
                        FilterChip(selected = selectedCategory == c.id, onClick = { selectedCategory = c.id }, label = { Text(c.name) })
                    }
                }
            }
        }
        if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
        error?.let {
            ElevatedCard(Modifier.padding(14.dp)) {
                Column(Modifier.padding(16.dp)) {
                    Text("Catalogul nu este disponibil încă", fontWeight = FontWeight.Bold)
                    Text(it, color = MaterialTheme.colorScheme.error, fontSize = 13.sp)
                    Spacer(Modifier.height(8.dp))
                    Text("Instalează AutoID Mobile API v0.2 pe site; aplicația nu mai cere acces public la WooCommerce Store API.", fontSize = 12.sp)
                }
            }
        }
        LazyColumn(contentPadding = PaddingValues(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(products) { p -> ProductCard(p, openUrl, openSupport) }
        }
    }
}

@Composable
fun ProductCard(p: Product, openUrl: (String) -> Unit, openSupport: (String) -> Unit) {
    ElevatedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(shape = RoundedCornerShape(12.dp), color = Color(0xFFF3F4F6)) {
                    AsyncImage(model = p.imageUrl, contentDescription = p.name, modifier = Modifier.size(96.dp).padding(6.dp))
                }
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    if (p.brand.isNotBlank()) Text(p.brand.uppercase(), color = Color(0xFF6B7280), fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    Text(p.name, fontWeight = FontWeight.Bold, maxLines = 3, overflow = TextOverflow.Ellipsis)
                    if (p.sku.isNotBlank()) Text("SKU: ${p.sku}", color = Color(0xFF6B7280), fontSize = 12.sp)
                    Spacer(Modifier.height(4.dp))
                    Text(p.price.ifBlank { "Preț la cerere" }, color = AutoIdOrange, fontWeight = FontWeight.Black, fontSize = 17.sp)
                    Text(p.stockLabel, color = if (p.stockLabel.contains("stoc", true)) Color(0xFF15803D) else Color(0xFF6B7280), fontSize = 12.sp)
                }
            }
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { if (p.permalink.isNotBlank()) openUrl(p.permalink) }, modifier = Modifier.weight(1f)) { Text("Vezi produsul") }
                OutlinedButton(onClick = { openSupport(p.supportQuery.ifBlank { p.name }) }, modifier = Modifier.weight(1f)) { Text("Suport") }
            }
        }
    }
}

@Composable
fun ScanScreen(scanProduct: () -> Unit, scanSupport: () -> Unit) {
    Column(Modifier.fillMaxSize()) {
        AutoIdTop("Scan", "Identifică rapid produsul")
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            ElevatedCard(colors = CardDefaults.elevatedCardColors(containerColor = Color(0xFF171A21))) {
                Column(Modifier.padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("⌗", color = AutoIdOrange, fontSize = 54.sp, fontWeight = FontWeight.Black)
                    Text("Scanează un cod", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 22.sp)
                    Text("EAN, UPC, Code 128, QR sau DataMatrix", color = Color(0xFFD1D5DB))
                    Spacer(Modifier.height(18.dp))
                    Button(scanProduct, Modifier.fillMaxWidth()) { Text("Caută produsul") }
                    Spacer(Modifier.height(8.dp))
                    OutlinedButton(scanSupport, Modifier.fillMaxWidth(), colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White)) { Text("Caută în Support Center") }
                }
            }
            Text("Util pentru depozit și service", fontWeight = FontWeight.Bold)
            Text("Scanezi eticheta unui echipament sau SKU-ul unei piese și continui direct către catalog sau documentație tehnică.", color = Color(0xFF6B7280))
        }
    }
}

@Composable
fun SupportScreen(api: AutoIdApi, initial: String, openUrl: (String) -> Unit) {
    var query by remember(initial) { mutableStateOf(initial) }
    var results by remember { mutableStateOf<List<SupportResource>>(emptyList()) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(query) {
        if (query.length < 2) { results = emptyList(); return@LaunchedEffect }
        delay(350); loading = true; error = null
        runCatching { withContext(Dispatchers.IO) { api.support(query) } }
            .onSuccess { results = it }
            .onFailure { error = it.message }
        loading = false
    }

    Column(Modifier.fillMaxSize()) {
        AutoIdTop("Support Center", "Manuale · drivere · firmware · video · depanare")
        Column(Modifier.padding(14.dp)) {
            OutlinedTextField(query, { query = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("Model sau problemă: ex. ZT610 calibrare") })
            if (query.isBlank()) {
                Spacer(Modifier.height(14.dp))
                Text("Căutări rapide", fontWeight = FontWeight.Bold)
                Row(Modifier.horizontalScroll(rememberScrollState()).padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("ZT111", "ZT411", "ZT610", "ZD421", "DS3608").forEach { q -> AssistChip(onClick = { query = q }, label = { Text(q) }) }
                }
            }
        }
        if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
        error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(horizontal = 14.dp)) }
        LazyColumn(contentPadding = PaddingValues(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(results) { r ->
                ElevatedCard(Modifier.fillMaxWidth().clickable { if (r.url.isNotBlank()) openUrl(r.url) }) {
                    Column(Modifier.padding(14.dp)) {
                        Text(r.type.uppercase(), color = AutoIdOrange, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        Text(r.title, fontWeight = FontWeight.Bold)
                        if (r.summary.isNotBlank()) Text(r.summary, color = Color(0xFF6B7280), fontSize = 12.sp, maxLines = 3, overflow = TextOverflow.Ellipsis)
                    }
                }
            }
        }
    }
}

@Composable
fun AccountHub(api: AutoIdApi, session: SessionStore, openUrl: (String) -> Unit) {
    var showOrders by remember { mutableStateOf(false) }
    if (showOrders) { Orders(api, session) { showOrders = false }; return }

    Column(Modifier.fillMaxSize()) {
        AutoIdTop("Cont", "Comenzi și date client")
        if (session.accessToken != null) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                ElevatedCard { Column(Modifier.padding(16.dp)) {
                    Text("Cont conectat", fontWeight = FontWeight.Bold)
                    if (session.customerEmail.isNotBlank()) Text(session.customerEmail, color = Color(0xFF6B7280))
                }}
                Button(onClick = { showOrders = true }, modifier = Modifier.fillMaxWidth()) { Text("Comenzile mele") }
                OutlinedButton(onClick = { openUrl("https://www.autoid.ro/my-account/") }, modifier = Modifier.fillMaxWidth()) { Text("Deschide contul pe AutoID.ro") }
                OutlinedButton(onClick = { session.clear() }, modifier = Modifier.fillMaxWidth()) { Text("Deconectare") }
            }
        } else AccountLogin(api, session)
    }
}

@Composable
fun AccountLogin(api: AutoIdApi, session: SessionStore) {
    var email by remember { mutableStateOf(session.customerEmail) }
    var pass by remember { mutableStateOf("") }
    var msg by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Autentificare AutoID", fontWeight = FontWeight.Bold, fontSize = 20.sp)
        Text("Conectează-te pentru comenzi, status și istoric.", color = Color(0xFF6B7280))
        OutlinedTextField(email, { email = it }, label = { Text("Email") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        OutlinedTextField(pass, { pass = it }, label = { Text("Parolă") }, modifier = Modifier.fillMaxWidth(), singleLine = true, visualTransformation = PasswordVisualTransformation())
        Button(onClick = { busy = true }, enabled = !busy && email.isNotBlank() && pass.isNotBlank(), modifier = Modifier.fillMaxWidth()) { Text(if (busy) "Se conectează…" else "Autentificare") }
        LaunchedEffect(busy) {
            if (busy) {
                runCatching { withContext(Dispatchers.IO) { api.login(email, pass) } }
                    .onSuccess { session.saveLogin(it); msg = "Autentificare reușită" }
                    .onFailure { msg = it.message ?: "Eroare" }
                busy = false
            }
        }
        if (msg.isNotBlank()) Text(msg, color = if (msg.contains("reușită")) Color(0xFF15803D) else MaterialTheme.colorScheme.error)
    }
}

@Composable
fun Orders(api: AutoIdApi, session: SessionStore, back: () -> Unit) {
    val token = session.accessToken
    var orders by remember { mutableStateOf(emptyList<Order>()) }
    var error by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(token) {
        if (token != null) runCatching { withContext(Dispatchers.IO) { api.orders(token) } }.onSuccess { orders = it }.onFailure { error = it.message }
    }
    Column(Modifier.fillMaxSize()) {
        AutoIdTop("Comenzile mele")
        TextButton(onClick = back, modifier = Modifier.padding(horizontal = 12.dp)) { Text("← Înapoi la cont") }
        error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(14.dp)) }
        LazyColumn(contentPadding = PaddingValues(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(orders) { o ->
                ElevatedCard {
                    Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text("Comanda #${o.number}", fontWeight = FontWeight.Bold)
                            Text(o.status, color = Color(0xFF6B7280))
                        }
                        Text(o.total, fontWeight = FontWeight.Black)
                    }
                }
            }
        }
    }
}
