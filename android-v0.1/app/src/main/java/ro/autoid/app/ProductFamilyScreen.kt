package ro.autoid.app

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import ro.autoid.app.data.*
import ro.autoid.app.ui.theme.AutoIdOrange

private val FamilyGreen = Color(0xFF16803A)
private val FamilyMuted = Color(0xFF667085)
private val FamilyBg = Color(0xFFF5F6F8)

@Composable
fun ProductFamilyScreen(
    seed: Product,
    api: AutoIdApi,
    commerce: CommerceStore,
    onBack: () -> Unit,
    onCart: (Product) -> Unit,
    onSupport: (String) -> Unit,
    onOpen: (String) -> Unit,
    onFavorite: (Product) -> Unit
) {
    var product by remember { mutableStateOf(seed) }
    var family by remember { mutableStateOf<ProductFamily?>(null) }
    var familyProducts by remember { mutableStateOf<List<Product>>(emptyList()) }
    var supportSections by remember { mutableStateOf<List<SupportSection>>(emptyList()) }
    var selectedTab by remember { mutableStateOf("overview") }
    var loading by remember { mutableStateOf(true) }
    var familyLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var qty by remember { mutableIntStateOf(1) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(seed.id) {
        loading = true
        error = null
        runCatching {
            withContext(Dispatchers.IO) {
                Triple(api.product(seed.id), api.productFamily(seed.id), api.productSupport(seed.id))
            }
        }.onSuccess { result ->
            product = result.first
            family = result.second
            supportSections = result.third
            commerce.addRecent(result.first)
        }.onFailure { error = it.message }
        loading = false
    }

    fun loadFamilyGroup(key: String) {
        selectedTab = key
        if (key == "overview" || key == "support") return
        familyLoading = true
        scope.launch {
            runCatching { withContext(Dispatchers.IO) { api.familyProducts(product.id, key) } }
                .onSuccess { familyProducts = it }
                .onFailure { error = it.message }
            familyLoading = false
        }
    }

    Scaffold(
        containerColor = FamilyBg,
        bottomBar = {
            Surface(shadowElevation = 12.dp, color = Color.White) {
                Row(
                    Modifier.fillMaxWidth().navigationBarsPadding().padding(horizontal = 14.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(product.price, color = AutoIdOrange, fontWeight = FontWeight.ExtraBold, fontSize = 20.sp)
                        Text(product.stockLabel, color = if (product.inStock) FamilyGreen else Color(0xFFB42318), fontSize = 11.sp)
                    }
                    Button(
                        onClick = { repeat(qty) { onCart(product) } },
                        enabled = product.inStock,
                        modifier = Modifier.height(50.dp),
                        shape = RoundedCornerShape(14.dp)
                    ) { Text("Adaugă în coș") }
                }
            }
        }
    ) { padding ->
        Column(
            Modifier.padding(padding).fillMaxSize().verticalScroll(rememberScrollState()).statusBarsPadding(),
            verticalArrangement = Arrangement.spacedBy(0.dp)
        ) {
            ProductHubHeader(product, commerce, onBack, { onFavorite(product) })
            if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
            error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(16.dp)) }
            ProductHero(product, qty, { if (qty > 1) qty-- }, { qty++ })
            ProductTrustStrip(product)
            ProductFamilyTabs(
                family = family,
                supportCount = supportSections.sumOf { it.count },
                selected = selectedTab,
                onSelected = ::loadFamilyGroup
            )
            when (selectedTab) {
                "overview" -> ProductOverview(product, onSupport)
                "support" -> ProductSupportTab(product, supportSections, onSupport, onOpen)
                else -> ProductFamilyGroupTab(
                    group = family?.groups?.firstOrNull { it.key == selectedTab },
                    products = familyProducts,
                    loading = familyLoading,
                    commerce = commerce,
                    onCart = onCart,
                    onOpen = onOpen
                )
            }
            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable
private fun ProductHubHeader(product: Product, commerce: CommerceStore, onBack: () -> Unit, onFavorite: () -> Unit) {
    Surface(color = Color.White) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            TextButton(onClick = onBack) { Text("‹", fontSize = 30.sp) }
            Column(Modifier.weight(1f)) {
                Text(product.brand.ifBlank { "AutoID" }, color = AutoIdOrange, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                Text(product.model.ifBlank { product.name }, maxLines = 1, overflow = TextOverflow.Ellipsis, fontWeight = FontWeight.Bold)
            }
            TextButton(onClick = onFavorite) { Text(if (commerce.isFavorite(product.id)) "♥" else "♡", fontSize = 24.sp) }
            BadgedBox(badge = { if (commerce.cartCount() > 0) Badge { Text(commerce.cartCount().toString()) } }) { Text("▣", fontSize = 22.sp) }
        }
    }
}

@Composable
private fun ProductHero(product: Product, qty: Int, onMinus: () -> Unit, onPlus: () -> Unit) {
    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Card(shape = RoundedCornerShape(20.dp), colors = CardDefaults.cardColors(containerColor = Color.White)) {
            Box(Modifier.fillMaxWidth().height(260.dp), contentAlignment = Alignment.Center) {
                AsyncImage(product.imageUrl, product.name, Modifier.fillMaxSize().padding(22.dp))
                if (product.onSale) Surface(
                    modifier = Modifier.align(Alignment.TopStart).padding(12.dp),
                    color = Color(0xFFD92D20), shape = RoundedCornerShape(8.dp)
                ) { Text("OFERTĂ", color = Color.White, fontSize = 11.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(horizontal = 9.dp, vertical = 5.dp)) }
            }
        }
        Text(product.brand.ifBlank { product.category }, color = AutoIdOrange, fontWeight = FontWeight.Bold, fontSize = 12.sp)
        Text(product.name, fontSize = 24.sp, lineHeight = 29.sp, fontWeight = FontWeight.ExtraBold)
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (product.sku.isNotBlank()) Text("SKU ${product.sku}", color = FamilyMuted, fontSize = 12.sp)
            if (product.rating > 0) {
                Spacer(Modifier.width(12.dp)); Text("★ ${"%.1f".format(product.rating)} (${product.reviewCount})", fontSize = 12.sp)
            }
        }
        Text(product.price, color = AutoIdOrange, fontWeight = FontWeight.ExtraBold, fontSize = 25.sp)
        Text(
            if (product.inStock) "● ${product.stockLabel}" else product.stockLabel,
            color = if (product.inStock) FamilyGreen else Color(0xFFB42318),
            fontWeight = FontWeight.Bold
        )
        if (product.deliveryLabel.isNotBlank()) Text(product.deliveryLabel, color = FamilyMuted, fontSize = 12.sp)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Cantitate", fontWeight = FontWeight.Bold)
            Spacer(Modifier.weight(1f))
            OutlinedButton(onClick = onMinus, contentPadding = PaddingValues(horizontal = 15.dp)) { Text("−") }
            Text(qty.toString(), modifier = Modifier.padding(horizontal = 14.dp), fontWeight = FontWeight.Bold)
            OutlinedButton(onClick = onPlus, contentPadding = PaddingValues(horizontal = 15.dp)) { Text("+") }
        }
    }
}

@Composable
private fun ProductTrustStrip(product: Product) {
    Row(
        Modifier.fillMaxWidth().background(Color.White).padding(horizontal = 16.dp, vertical = 12.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        TrustPill(if ((product.stockAutoId ?: 0) > 0) "Stoc AutoID ${product.stockAutoId}" else "Stoc verificat", Modifier.weight(1f))
        TrustPill("B2B & B2C", Modifier.weight(1f))
        TrustPill("Suport tehnic", Modifier.weight(1f))
    }
}

@Composable
private fun TrustPill(text: String, modifier: Modifier = Modifier) {
    Surface(modifier, color = Color(0xFFF2F4F7), shape = RoundedCornerShape(12.dp)) {
        Text(text, modifier = Modifier.padding(horizontal = 8.dp, vertical = 9.dp), fontSize = 10.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun ProductFamilyTabs(family: ProductFamily?, supportCount: Int, selected: String, onSelected: (String) -> Unit) {
    val tabs = buildList {
        add(FamilyGroup("overview", "Produs", 0))
        family?.groups?.filter { it.count > 0 }?.let(::addAll)
        if (supportCount > 0 || family?.supportAvailable == true) add(FamilyGroup("support", "Suport", supportCount))
    }
    Surface(color = Color.White, shadowElevation = 3.dp) {
        Row(
            Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 12.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(7.dp)
        ) {
            tabs.forEach { tab ->
                FilterChip(
                    selected = selected == tab.key,
                    onClick = { onSelected(tab.key) },
                    label = { Text(if (tab.count > 0) "${tab.label} ${tab.count}" else tab.label) }
                )
            }
        }
    }
}

@Composable
private fun ProductOverview(product: Product, onSupport: (String) -> Unit) {
    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        ElevatedCard(onClick = { onSupport(product.supportQuery.ifBlank { product.name }) }, shape = RoundedCornerShape(18.dp)) {
            Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Surface(color = Color(0xFFFFF1E8), shape = RoundedCornerShape(14.dp)) { Text("✦", color = AutoIdOrange, fontSize = 26.sp, modifier = Modifier.padding(12.dp)) }
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Text("AutoID AI pentru acest produs", fontWeight = FontWeight.ExtraBold)
                    Text("Compatibilitate, accesorii, configurare și depanare.", color = FamilyMuted, fontSize = 12.sp)
                }
                Text("›", fontSize = 24.sp)
            }
        }
        if (product.description.isNotBlank()) ProductInfoCard("Descriere") { Text(product.description, color = Color(0xFF344054)) }
        if (product.attributes.isNotEmpty()) ProductInfoCard("Specificații tehnice") {
            product.attributes.take(24).forEach { a ->
                Row(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                    Text(a.name, Modifier.weight(.42f), color = FamilyMuted, fontSize = 12.sp)
                    Text(a.values.joinToString(", "), Modifier.weight(.58f), fontWeight = FontWeight.Medium, fontSize = 12.sp)
                }
                HorizontalDivider(color = Color(0xFFEAECF0))
            }
        }
    }
}

@Composable
private fun ProductInfoCard(title: String, content: @Composable ColumnScope.() -> Unit) {
    Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = Color.White)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(title, fontSize = 18.sp, fontWeight = FontWeight.ExtraBold)
            content()
        }
    }
}

@Composable
private fun ProductFamilyGroupTab(
    group: FamilyGroup?,
    products: List<Product>,
    loading: Boolean,
    commerce: CommerceStore,
    onCart: (Product) -> Unit,
    onOpen: (String) -> Unit
) {
    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text(group?.label ?: "Produse compatibile", fontSize = 21.sp, fontWeight = FontWeight.ExtraBold)
        Text("${group?.count ?: products.size} SKU-uri asociate modelului", color = FamilyMuted, fontSize = 12.sp)
        if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
        if (!loading && products.isEmpty()) Text("Nu sunt elemente disponibile în această grupă.", color = FamilyMuted)
        products.forEach { p -> FamilySkuCard(p, commerce.isFavorite(p.id), onCart, onOpen) }
    }
}

@Composable
private fun FamilySkuCard(product: Product, favorite: Boolean, onCart: (Product) -> Unit, onOpen: (String) -> Unit) {
    ElevatedCard(shape = RoundedCornerShape(16.dp)) {
        Row(
            Modifier.fillMaxWidth().clickable { if (product.permalink.isNotBlank()) onOpen(product.permalink) }.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(Modifier.size(74.dp).background(Color.White, RoundedCornerShape(12.dp)), contentAlignment = Alignment.Center) {
                AsyncImage(product.imageUrl, product.name, Modifier.fillMaxSize().padding(5.dp))
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                if (product.sku.isNotBlank()) Text(product.sku, color = FamilyMuted, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                Text(product.name, maxLines = 2, overflow = TextOverflow.Ellipsis, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                Text(product.price, color = AutoIdOrange, fontWeight = FontWeight.ExtraBold)
                Text(product.stockLabel, color = if (product.inStock) FamilyGreen else Color(0xFFB42318), fontSize = 10.sp)
            }
            if (product.inStock) FilledTonalButton(onClick = { onCart(product) }, contentPadding = PaddingValues(horizontal = 10.dp)) { Text("+") }
        }
    }
}

@Composable
private fun ProductSupportTab(
    product: Product,
    sections: List<SupportSection>,
    onSupport: (String) -> Unit,
    onOpen: (String) -> Unit
) {
    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        ElevatedCard(onClick = { onSupport(product.supportQuery.ifBlank { product.name }) }, shape = RoundedCornerShape(18.dp)) {
            Column(Modifier.padding(16.dp)) {
                Text("✦ Întreabă AutoID AI", color = AutoIdOrange, fontWeight = FontWeight.ExtraBold)
                Text("Spune problema exactă și păstrăm contextul produsului ${product.model.ifBlank { product.name }}.", fontSize = 12.sp)
            }
        }
        sections.filter { it.count > 0 }.forEach { section ->
            ProductInfoCard("${section.label} · ${section.count}") {
                section.resources.take(12).forEach { resource ->
                    Column(
                        Modifier.fillMaxWidth().clickable { onOpen(resource.url) }.padding(vertical = 8.dp)
                    ) {
                        Text(resource.title, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        if (resource.summary.isNotBlank()) Text(resource.summary, maxLines = 2, overflow = TextOverflow.Ellipsis, color = FamilyMuted, fontSize = 11.sp)
                        Text("Deschide →", color = AutoIdOrange, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    }
                    HorizontalDivider(color = Color(0xFFEAECF0))
                }
            }
        }
    }
}
