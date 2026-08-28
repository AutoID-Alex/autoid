package ro.autoid.app

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.codescanner.GmsBarcodeScannerOptions
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import ro.autoid.app.data.AutoIdApi
import ro.autoid.app.data.Product
import ro.autoid.app.data.SessionStore
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

enum class Tab(val title: String) { Home("Home"), Products("Produse"), Scan("Scan"), Orders("Comenzi"), Account("Cont") }

@Composable
fun AutoIdApp(api: AutoIdApi, session: SessionStore, scan: ((String) -> Unit) -> Unit, openUrl: (String) -> Unit) {
    var tab by remember { mutableStateOf(Tab.Home) }
    var search by remember { mutableStateOf("") }
    Scaffold(bottomBar = {
        NavigationBar { Tab.entries.forEach { item ->
            NavigationBarItem(selected = tab == item, onClick = { tab = item }, icon = { Text(if (tab == item) "●" else "○") }, label = { Text(item.title) })
        }}
    }) { pad -> Box(Modifier.padding(pad).fillMaxSize()) {
        when (tab) {
            Tab.Home -> Home(api, { search = it; tab = Tab.Products }, { openUrl("https://www.autoid.ro/support/") })
            Tab.Products -> Products(api, search)
            Tab.Scan -> Center { Button(onClick = { scan { search = it; tab = Tab.Products } }) { Text("Scanează codul") } }
            Tab.Orders -> Orders(api, session) { tab = Tab.Account }
            Tab.Account -> Account(api, session)
        }
    }}
}

@Composable
fun BrandHeader(title: String, subtitle: String = "Professional Solutions") {
    Column { Text("AutoID", color = AutoIdOrange, fontSize = 30.sp, fontWeight = FontWeight.ExtraBold); Text(title, fontWeight = FontWeight.Bold, fontSize = 20.sp); Text(subtitle, color = MaterialTheme.colorScheme.onSurfaceVariant) }
}

@Composable
fun Home(api: AutoIdApi, goProducts: (String) -> Unit, support: () -> Unit) {
    var online by remember { mutableStateOf<Boolean?>(null) }
    var query by remember { mutableStateOf("") }
    LaunchedEffect(Unit) { online = withContext(Dispatchers.IO) { api.health() } }
    Column(Modifier.fillMaxSize().padding(20.dp).statusBarsPadding(), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        BrandHeader("Professional Solutions", "Catalog, comenzi și suport AutoID într-un singur loc")
        ElevatedCard { Column(Modifier.padding(18.dp)) {
            Text(if (online == true) "● Conectat la AutoID.ro" else if (online == false) "○ Conexiune indisponibilă" else "Se verifică conexiunea…", color = if (online == true) Color(0xFF15803D) else MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(12.dp)); OutlinedTextField(query, { query = it }, label = { Text("Caută produs, model sau SKU") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
            Spacer(Modifier.height(10.dp)); Button(onClick = { goProducts(query) }, modifier = Modifier.fillMaxWidth()) { Text("Caută în catalog") }
        }}
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            OutlinedButton(onClick = { goProducts("") }, modifier = Modifier.weight(1f)) { Text("Produse") }
            OutlinedButton(onClick = support, modifier = Modifier.weight(1f)) { Text("Support Center") }
        }
    }
}

@Composable
fun Products(api: AutoIdApi, initial: String) {
    var query by remember(initial) { mutableStateOf(initial) }
    var products by remember { mutableStateOf<List<Product>>(emptyList()) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    suspend fun load() { loading = true; error = null; runCatching { withContext(Dispatchers.IO) { api.products(query) } }.onSuccess { products = it }.onFailure { error = it.message }; loading = false }
    LaunchedEffect(initial) { load() }
    Column(Modifier.fillMaxSize().padding(16.dp).statusBarsPadding()) {
        BrandHeader("Produse")
        Spacer(Modifier.height(12.dp)); OutlinedTextField(query, { query = it }, label = { Text("Caută") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        LaunchedEffect(query) { kotlinx.coroutines.delay(500); load() }
        if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
        error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(vertical = 8.dp)) }
        LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp), contentPadding = PaddingValues(vertical = 12.dp)) { items(products) { ProductCard(it) } }
    }
}

@Composable
fun ProductCard(p: Product) {
    ElevatedCard(modifier = Modifier.fillMaxWidth()) { Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
        AsyncImage(model = p.imageUrl, contentDescription = p.name, modifier = Modifier.size(82.dp))
        Spacer(Modifier.width(12.dp)); Column(Modifier.weight(1f)) { Text(p.name, fontWeight = FontWeight.Bold); if (p.sku.isNotBlank()) Text("SKU: ${p.sku}", fontSize = 12.sp); Text(p.price, color = AutoIdOrange, fontWeight = FontWeight.Bold); Text(p.stockLabel, fontSize = 12.sp) }
    }}
}

@Composable
fun Orders(api: AutoIdApi, session: SessionStore, account: () -> Unit) {
    val token = session.accessToken
    if (token == null) { Center { Column(horizontalAlignment = Alignment.CenterHorizontally) { Text("Autentifică-te pentru a vedea comenzile"); Button(onClick = account) { Text("Mergi la Cont") } } }; return }
    var orders by remember { mutableStateOf(emptyList<ro.autoid.app.data.Order>()) }
    var error by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(token) { runCatching { withContext(Dispatchers.IO) { api.orders(token) } }.onSuccess { orders = it }.onFailure { error = it.message } }
    Column(Modifier.fillMaxSize().padding(16.dp).statusBarsPadding()) { BrandHeader("Comenzile mele"); error?.let { Text(it, color = MaterialTheme.colorScheme.error) }; LazyColumn { items(orders) { o -> ListItem(headlineContent = { Text("Comanda #${o.number}") }, supportingContent = { Text(o.status) }, trailingContent = { Text(o.total, fontWeight = FontWeight.Bold) }); HorizontalDivider() } } }
}

@Composable
fun Account(api: AutoIdApi, session: SessionStore) {
    var email by remember { mutableStateOf(session.customerEmail) }; var pass by remember { mutableStateOf("") }; var msg by remember { mutableStateOf("") }; var busy by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxSize().padding(20.dp).statusBarsPadding(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        BrandHeader("Cont AutoID")
        if (session.accessToken != null) { Text("Conectat${session.customerEmail.takeIf { it.isNotBlank() }?.let { " ca $it" } ?: ""}"); OutlinedButton(onClick = { session.clear(); msg = "Deconectat" }) { Text("Deconectare") }; Text(msg); return@Column }
        OutlinedTextField(email, { email = it }, label = { Text("Email") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        OutlinedTextField(pass, { pass = it }, label = { Text("Parolă") }, modifier = Modifier.fillMaxWidth(), singleLine = true, visualTransformation = PasswordVisualTransformation())
        Button(onClick = { busy = true }, enabled = !busy && email.isNotBlank() && pass.isNotBlank(), modifier = Modifier.fillMaxWidth()) { Text(if (busy) "Se conectează…" else "Autentificare") }
        LaunchedEffect(busy) { if (busy) { runCatching { withContext(Dispatchers.IO) { api.login(email, pass) } }.onSuccess { session.saveLogin(it); msg = "Autentificare reușită" }.onFailure { msg = it.message ?: "Eroare" }; busy = false } }
        Text(msg, color = if (msg.contains("reușită")) Color(0xFF15803D) else MaterialTheme.colorScheme.error)
    }
}

@Composable
fun Center(content: @Composable () -> Unit) = Box(Modifier.fillMaxSize().padding(20.dp).statusBarsPadding(), contentAlignment = Alignment.Center) { content() }
