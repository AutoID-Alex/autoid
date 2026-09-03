package ro.autoid.app

import android.content.Context
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import ro.autoid.app.data.*
import ro.autoid.app.ui.theme.AutoIdOrange

@Composable
fun HeaderV08(title:String="AutoID",cartCount:Int=0,onMenu:(()->Unit)?=null,onCart:(()->Unit)?=null){
    Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
        if(onMenu!=null) IconButton(onClick=onMenu){Icon(Icons.Default.Menu,"Meniu")}
        if(title=="AutoID") Image(painterResource(R.drawable.autoid_logo_transparent),"AutoID Professional Solutions",Modifier.width(158.dp).height(48.dp))
        else Text(title,fontSize=23.sp,fontWeight=FontWeight.ExtraBold,color=Color(0xFF101828))
        Spacer(Modifier.weight(1f))
        if(onCart!=null) IconButton(onClick=onCart){BadgedBox(badge={if(cartCount>0)Badge{Text(cartCount.toString())}}){Icon(Icons.Default.ShoppingCart,"Coș")}}
    }
}

@Composable
fun HomeScreenV08(
    api:AutoIdApi, commerce:CommerceStore, onSearch:(String)->Unit, onCategory:(ProductCategory)->Unit,
    onProduct:(Product)->Unit, onAi:(String)->Unit, onCart:(Product)->Unit, onFavorite:(Product)->Unit,
    scan:((String)->Unit)->Unit, onMenu:()->Unit={}, onHeaderCart:()->Unit={}
){
    var q by remember{mutableStateOf("")};var sections by remember{mutableStateOf<List<HomeSection>>(emptyList())};var loading by remember{mutableStateOf(true)};var error by remember{mutableStateOf<String?>(null)}
    LaunchedEffect(Unit){runCatching{withContext(Dispatchers.IO){api.homeSections()}}.onSuccess{sections=it}.onFailure{error=it.message};loading=false}
    LazyColumn(Modifier.fillMaxSize().padding(horizontal=16.dp).statusBarsPadding(),verticalArrangement=Arrangement.spacedBy(18.dp),contentPadding=PaddingValues(bottom=26.dp)){
        item{Spacer(Modifier.height(4.dp));HeaderV08(cartCount=commerce.cartCount(),onMenu=onMenu,onCart=onHeaderCart);Spacer(Modifier.height(10.dp));SearchBarBox(q,{q=it},{onSearch(q)},{scan{onSearch(it)}})}
        item{Card(shape=RoundedCornerShape(20.dp),colors=CardDefaults.cardColors(containerColor=Color(0xFF171B26))){Column(Modifier.padding(22.dp)){Text("Echipamente AutoID pentru afacerea ta",color=Color.White,fontSize=24.sp,fontWeight=FontWeight.ExtraBold);Spacer(Modifier.height(6.dp));Text("Familii de produse, variante și stoc real AutoID.",color=Color(0xFFD0D5DD));Spacer(Modifier.height(12.dp));Button(onClick={onSearch("")}){Text("Vezi catalogul")}}}}
        if(loading)item{LinearProgressIndicator(Modifier.fillMaxWidth())}
        error?.let{item{Text(it,color=MaterialTheme.colorScheme.error)}}
        sections.forEach{section->
            item{SectionTitle(section.category.name,if(section.totalGrouped>0)"${section.totalGrouped} familii" else "");Spacer(Modifier.height(8.dp));LazyRow(horizontalArrangement=Arrangement.spacedBy(10.dp)){
                items(section.products,key={it.id}){p->GroupedHomeCardV08(p,commerce.isFavorite(p.id),{onProduct(p)},{onFavorite(p)})}
                item{OutlinedCard(Modifier.width(178.dp).height(282.dp).clickable{onCategory(section.category)},shape=RoundedCornerShape(18.dp)){Box(Modifier.fillMaxSize(),contentAlignment=Alignment.Center){Text("Vezi toate →",color=AutoIdOrange,fontWeight=FontWeight.Bold)}}}
            }}
        }
        val recent=commerce.recent();if(recent.isNotEmpty()){item{SectionTitle("Vizualizate recent","")};items(recent.take(4)){p->ProductCard(p,commerce.isFavorite(p.id),{onProduct(p)},{onCart(p)},{onFavorite(p)})}}
    }
}

@Composable private fun GroupedHomeCardV08(p:Product,favorite:Boolean,onClick:()->Unit,onFavorite:()->Unit){
    ElevatedCard(shape=RoundedCornerShape(18.dp),modifier=Modifier.width(238.dp).height(282.dp)){
        Column(Modifier.clickable(onClick=onClick).padding(12.dp)){
            Box(Modifier.fillMaxWidth().height(112.dp).background(Color.White,RoundedCornerShape(12.dp)),contentAlignment=Alignment.Center){AsyncImage(p.imageUrl,p.name,Modifier.fillMaxSize().padding(8.dp))}
            Spacer(Modifier.height(7.dp));Text(p.brand.ifBlank{p.category},fontSize=11.sp,color=AutoIdOrange,fontWeight=FontWeight.Bold);Text(p.name,maxLines=2,overflow=TextOverflow.Ellipsis,fontWeight=FontWeight.Bold)
            if(p.priceRangeExVat.isNotBlank())Text(p.priceRangeExVat,fontSize=11.sp,fontWeight=FontWeight.Bold)
            Text(p.priceRangeInclVat.ifBlank{p.currentInclVat.ifBlank{p.price}},fontSize=12.sp,fontWeight=FontWeight.ExtraBold)
            val st=p.groupedStockAutoId?:p.stockAutoId?:0;Text(if(st>0)"$st buc. în stoc pe variante" else "Stoc pe variante",fontSize=10.sp,color=if(st>0)Color(0xFF16803A) else Color(0xFF667085),fontWeight=FontWeight.Bold)
            Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){IconButton(onClick=onFavorite){Icon(if(favorite)Icons.Default.Favorite else Icons.Default.FavoriteBorder,"Favorite",tint=if(favorite)AutoIdOrange else LocalContentColor.current)};Spacer(Modifier.weight(1f));FilledTonalButton(onClick=onClick){Text("Variante")}}
        }
    }
}

@Composable
fun CategoriesScreenV08(api:AutoIdApi,onCategory:(ProductCategory)->Unit,onSearch:(String)->Unit,scan:((String)->Unit)->Unit,onMenu:()->Unit={},cartCount:Int=0,onHeaderCart:()->Unit={}){
    var cats by remember{mutableStateOf<List<ProductCategory>>(emptyList())};var q by remember{mutableStateOf("")};var error by remember{mutableStateOf<String?>(null)}
    LaunchedEffect(Unit){runCatching{withContext(Dispatchers.IO){api.categories()}}.onSuccess{cats=it}.onFailure{error=it.message}}
    LazyColumn(Modifier.fillMaxSize().padding(16.dp).statusBarsPadding(),verticalArrangement=Arrangement.spacedBy(12.dp)){
        item{HeaderV08("Categorii",cartCount,onMenu,onHeaderCart);Spacer(Modifier.height(8.dp));SearchBarBox(q,{q=it},{onSearch(q)},{scan{onSearch(it)}})}
        error?.let{item{Text(it,color=MaterialTheme.colorScheme.error)}}
        items(cats,key={it.id}){c->ElevatedCard(onClick={onCategory(c)},shape=RoundedCornerShape(16.dp)){Row(Modifier.padding(14.dp),verticalAlignment=Alignment.CenterVertically){if(c.imageUrl!=null)AsyncImage(c.imageUrl,c.name,Modifier.size(64.dp));Spacer(Modifier.width(12.dp));Column(Modifier.weight(1f)){Text(c.name,fontWeight=FontWeight.Bold);Text("${c.count} produse",color=Color(0xFF667085))};Icon(Icons.Default.ChevronRight,null)}}}
    }
}

@Composable
fun ProductListV08(api:AutoIdApi,commerce:CommerceStore,category:ProductCategory?,initialSearch:String,onBack:()->Unit,onProduct:(Product)->Unit,onCart:(Product)->Unit,onFavorite:(Product)->Unit,scan:((String)->Unit)->Unit,onHeaderCart:()->Unit={}){
    var q by remember{mutableStateOf(initialSearch)};var products by remember{mutableStateOf<List<Product>>(emptyList())};var subs by remember{mutableStateOf<List<ProductCategory>>(emptyList())};var active by remember(category?.id){mutableStateOf(category)};var loading by remember{mutableStateOf(false)};var canLoadMore by remember{mutableStateOf(true)};var page by remember{mutableIntStateOf(1)};var sort by remember{mutableStateOf("date")};var error by remember{mutableStateOf<String?>(null)};val listState=rememberLazyListState()
    suspend fun load(reset:Boolean){if(loading)return;loading=true;error=null;if(reset){page=1;canLoadMore=true};val rows=runCatching{withContext(Dispatchers.IO){api.products(q,active?.id?.takeIf{it>0},page,sort)}}.onFailure{error=it.message}.getOrDefault(emptyList());if(reset)products=rows.distinctBy{it.id}else{val ids=products.map{it.id}.toHashSet();val fresh=rows.filterNot{it.id in ids};products=products+fresh;if(fresh.isEmpty())canLoadMore=false};if(rows.size<20)canLoadMore=false;loading=false}
    LaunchedEffect(category?.id){subs=if((category?.id?:0)>0)runCatching{withContext(Dispatchers.IO){api.categories(category!!.id)}}.getOrDefault(emptyList()) else emptyList()}
    LaunchedEffect(active?.id,sort){load(true)};LaunchedEffect(q){delay(450);load(true)}
    val shouldLoadMore by remember{derivedStateOf{val last=listState.layoutInfo.visibleItemsInfo.lastOrNull()?.index?:-1;canLoadMore&&!loading&&products.isNotEmpty()&&last>=products.lastIndex-3}}
    LaunchedEffect(shouldLoadMore){if(shouldLoadMore){page++;load(false)}}
    Column(Modifier.fillMaxSize().padding(16.dp).statusBarsPadding()){
        Row(verticalAlignment=Alignment.CenterVertically){IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")};Column(Modifier.weight(1f)){Text(category?.name?:"Produse",fontSize=22.sp,fontWeight=FontWeight.ExtraBold);Text("Scroll continuu",fontSize=11.sp,color=Color(0xFF667085))};IconButton(onClick=onHeaderCart){BadgedBox(badge={if(commerce.cartCount()>0)Badge{Text(commerce.cartCount().toString())}}){Icon(Icons.Default.ShoppingCart,"Coș")}}}
        if(subs.isNotEmpty())LazyRow(horizontalArrangement=Arrangement.spacedBy(8.dp),modifier=Modifier.padding(vertical=8.dp)){item{FilterChip(selected=active?.id==category?.id,onClick={active=category},label={Text("Toate")})};items(subs,key={it.id}){sub->FilterChip(selected=active?.id==sub.id,onClick={active=sub},label={Text(sub.name)})}}
        SearchBarBox(q,{q=it},{},{scan{q=it}},"Caută în categorie...")
        LazyRow(horizontalArrangement=Arrangement.spacedBy(8.dp),modifier=Modifier.padding(vertical=6.dp)){item{FilterChip(sort=="date",{sort="date"},{Text("Recomandate")})};item{FilterChip(sort=="price",{sort="price"},{Text("Preț")})};item{FilterChip(sort=="popularity",{sort="popularity"},{Text("Populare")})}}
        if(loading&&products.isEmpty())LinearProgressIndicator(Modifier.fillMaxWidth());error?.let{Text(it,color=MaterialTheme.colorScheme.error)}
        LazyColumn(state=listState,modifier=Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(10.dp),contentPadding=PaddingValues(vertical=12.dp)){items(products,key={it.id}){p->ProductCard(p,commerce.isFavorite(p.id),{onProduct(p)},{onCart(p)},{onFavorite(p)})};if(loading&&products.isNotEmpty())item{Box(Modifier.fillMaxWidth().height(48.dp),contentAlignment=Alignment.Center){CircularProgressIndicator(Modifier.size(22.dp),strokeWidth=2.dp,color=AutoIdOrange)}}}
    }
}

@Composable
fun CartScreenV08(commerce:CommerceStore,onProduct:(Product)->Unit,onChanged:()->Unit,onCheckout:()->Unit){
    var tick by remember{mutableIntStateOf(0)};val lines=remember(tick){commerce.cart()}
    Column(Modifier.fillMaxSize().padding(16.dp).statusBarsPadding()){HeaderV08("Coș",commerce.cartCount());Text("${commerce.cartCount()} produse",color=Color(0xFF667085));Spacer(Modifier.height(10.dp));if(lines.isEmpty()){Box(Modifier.fillMaxSize(),contentAlignment=Alignment.Center){Column(horizontalAlignment=Alignment.CenterHorizontally){Icon(Icons.Default.ShoppingCart,null,Modifier.size(44.dp),tint=AutoIdOrange);Text("Coșul este gol",fontSize=22.sp,fontWeight=FontWeight.Bold);Text("Adaugă produse din catalogul AutoID.",color=Color(0xFF667085))}};return}
        LazyColumn(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(10.dp)){items(lines,key={it.product.id}){line->ElevatedCard(shape=RoundedCornerShape(14.dp)){Row(Modifier.clickable{onProduct(line.product)}.padding(12.dp),verticalAlignment=Alignment.CenterVertically){AsyncImage(line.product.imageUrl,line.product.name,Modifier.size(68.dp));Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)){Text(line.product.name,maxLines=2,fontWeight=FontWeight.Bold);Text(line.product.priceRangeInclVat.ifBlank{line.product.currentInclVat.ifBlank{line.product.price}},color=AutoIdOrange);Row(verticalAlignment=Alignment.CenterVertically){IconButton(onClick={commerce.changeQty(line.product.id,line.quantity-1);tick++;onChanged()}){Icon(Icons.Default.Remove,"Minus")};Text(line.quantity.toString(),fontWeight=FontWeight.Bold);IconButton(onClick={commerce.changeQty(line.product.id,line.quantity+1);tick++;onChanged()}){Icon(Icons.Default.Add,"Plus")};Spacer(Modifier.weight(1f));TextButton(onClick={commerce.removeFromCart(line.product.id);tick++;onChanged()}){Text("Șterge")}}}}}}}
        ElevatedCard(shape=RoundedCornerShape(18.dp)){Column(Modifier.padding(16.dp)){Text("WooCommerce va calcula transportul și totalul final la checkout.",fontSize=12.sp,color=Color(0xFF667085));Spacer(Modifier.height(8.dp));Button(onClick=onCheckout,Modifier.fillMaxWidth().height(50.dp)){Text("Finalizare comandă")}}}
    }
}

private fun checkoutUnitRonV107(p: Product): Double? {
    val raw = p.currentInclVat.ifBlank { p.price }
    val token = Regex("""\d{1,3}(?:\.\d{3})*(?:,\d{2})|\d+(?:[.,]\d{2})?""").find(raw)?.value ?: return null
    return token.replace(".", "").replace(",", ".").toDoubleOrNull()
}

private fun checkoutMoneyRonV107(value: Double): String =
    java.text.NumberFormat.getNumberInstance(java.util.Locale("ro", "RO")).apply {
        minimumFractionDigits = 2
        maximumFractionDigits = 2
    }.format(value) + " lei"

@Composable
private fun CheckoutStepV107(label: String, active: Boolean, done: Boolean = false) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.widthIn(min = 72.dp)) {
        Surface(
            shape = CircleShape,
            color = when { done -> Color(0xFFE8F7EF); active -> Color(0xFFFFE9D9); else -> Color(0xFFF2F4F7) },
            modifier = Modifier.size(30.dp)
        ) {
            Box(contentAlignment = Alignment.Center) {
                if (done) Icon(Icons.Default.Check, null, tint = Color(0xFF067647), modifier = Modifier.size(16.dp))
                else Box(Modifier.size(8.dp).background(if (active) AutoIdOrange else Color(0xFF98A2B3), CircleShape))
            }
        }
        Spacer(Modifier.height(4.dp))
        Text(label, fontSize = 9.sp, fontWeight = if (active) FontWeight.Bold else FontWeight.Medium, color = if (active) Color(0xFF101828) else Color(0xFF667085))
    }
}

@Composable
private fun CheckoutSectionV107(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    subtitle: String = "",
    content: @Composable ColumnScope.() -> Unit
) {
    ElevatedCard(
        shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.elevatedCardColors(containerColor = Color.White),
        elevation = CardDefaults.elevatedCardElevation(defaultElevation = 1.dp)
    ) {
        Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(shape = RoundedCornerShape(12.dp), color = Color(0xFFFFF0E5)) {
                    Icon(icon, null, tint = AutoIdOrange, modifier = Modifier.padding(8.dp).size(19.dp))
                }
                Spacer(Modifier.width(10.dp))
                Column {
                    Text(title, fontWeight = FontWeight.ExtraBold, fontSize = 17.sp, color = Color(0xFF101828))
                    if (subtitle.isNotBlank()) Text(subtitle, fontSize = 10.sp, color = Color(0xFF667085))
                }
            }
            content()
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CheckoutV08(api:AutoIdApi,commerce:CommerceStore,onBack:()->Unit,onDone:()->Unit){
    val lines=remember{commerce.cart()}
    var config by remember{mutableStateOf<CheckoutConfig?>(null)}
    var first by remember{mutableStateOf("")};var last by remember{mutableStateOf("")};var company by remember{mutableStateOf("")};var vat by remember{mutableStateOf("")};var email by remember{mutableStateOf("")};var phone by remember{mutableStateOf("")};var address by remember{mutableStateOf("")};var address2 by remember{mutableStateOf("")};var city by remember{mutableStateOf("")};var state by remember{mutableStateOf("")};var postcode by remember{mutableStateOf("")};var country by remember{mutableStateOf("RO")};var note by remember{mutableStateOf("")};var payment by remember{mutableStateOf("cod")};var terms by remember{mutableStateOf(false)};var busy by remember{mutableStateOf(false)};var message by remember{mutableStateOf("")};var success by remember{mutableStateOf<CheckoutResult?>(null)}
    val methods=config?.payments?:listOf(PaymentMethod("cod","Numerar la livrare (COD)","Plată la livrare."),PaymentMethod("bacs","Transfer bancar","Plată prin ordin de plată."),PaymentMethod("stripe","Card (Stripe)","Plată cu cardul în aplicație.",false))
    val allPriced=lines.all{checkoutUnitRonV107(it.product)!=null}
    val subtotal=lines.sumOf{(checkoutUnitRonV107(it.product)?:0.0)*it.quantity}
    val valid=first.isNotBlank()&&last.isNotBlank()&&email.contains("@")&&phone.isNotBlank()&&address.isNotBlank()&&city.isNotBlank()&&postcode.isNotBlank()&&terms&&lines.isNotEmpty()

    LaunchedEffect(Unit){runCatching{withContext(Dispatchers.IO){api.checkoutConfig()}}.onSuccess{config=it;country=it.country.ifBlank{"RO"};payment=it.payments.firstOrNull{p->p.enabled}?.id?:"cod"}.onFailure{message=it.message?:"Nu am putut încărca metodele de plată."}}
    LaunchedEffect(busy){if(busy){runCatching{withContext(Dispatchers.IO){api.createOrder(lines,first,last,company,vat,email,phone,address,address2,city,state,postcode,country,note,payment)}}.onSuccess{success=it;message="Comandă plasată cu succes."}.onFailure{message=it.message?:"Comanda nu a putut fi plasată."};busy=false}}

    if(success!=null){
        val r=success!!
        Box(Modifier.fillMaxSize().background(Color(0xFFF8FAFC)).statusBarsPadding(),contentAlignment=Alignment.Center){
            ElevatedCard(Modifier.padding(20.dp),shape=RoundedCornerShape(28.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){
                Column(Modifier.padding(24.dp),horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(10.dp)){
                    Surface(shape=CircleShape,color=Color(0xFFE8F7EF),modifier=Modifier.size(76.dp)){Box(contentAlignment=Alignment.Center){Icon(Icons.Default.CheckCircle,null,tint=Color(0xFF067647),modifier=Modifier.size(42.dp))}}
                    Text("Comandă confirmată",fontSize=24.sp,fontWeight=FontWeight.ExtraBold,color=Color(0xFF101828))
                    Text("Comanda #${r.number} a fost creată.",color=Color(0xFF667085))
                    if(r.total.isNotBlank())Text(r.total,fontSize=20.sp,fontWeight=FontWeight.ExtraBold,color=AutoIdOrange)
                    Button(onClick=onDone,modifier=Modifier.fillMaxWidth().height(54.dp),shape=RoundedCornerShape(16.dp)){Text("Vezi contul meu")}
                }
            }
        }
        return
    }

    Scaffold(
        containerColor=Color(0xFFF8FAFC),
        topBar={
            TopAppBar(
                title={Column{Text("Finalizare comandă",fontWeight=FontWeight.ExtraBold);Text("Checkout AutoID",fontSize=10.sp,color=Color(0xFF667085))}},
                navigationIcon={IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")}},
                actions={Surface(shape=RoundedCornerShape(50),color=Color(0xFFE8F7EF),modifier=Modifier.padding(end=12.dp)){Row(Modifier.padding(horizontal=9.dp,vertical=6.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.Lock,null,tint=Color(0xFF067647),modifier=Modifier.size(14.dp));Spacer(Modifier.width(4.dp));Text("Checkout",fontSize=9.sp,fontWeight=FontWeight.Bold,color=Color(0xFF067647))}}},
                colors=TopAppBarDefaults.topAppBarColors(containerColor=Color.White)
            )
        },
        bottomBar={
            Surface(color=Color.White,shadowElevation=14.dp){
                Column(Modifier.fillMaxWidth().padding(horizontal=14.dp,vertical=12.dp).navigationBarsPadding()){
                    Row(verticalAlignment=Alignment.CenterVertically){Text("${commerce.cartCount()} produse",fontSize=11.sp,color=Color(0xFF667085));Spacer(Modifier.weight(1f));if(allPriced)Text(checkoutMoneyRonV107(subtotal),fontWeight=FontWeight.ExtraBold,fontSize=17.sp,color=Color(0xFF101828))}
                    Spacer(Modifier.height(7.dp))
                    Button(onClick={busy=true},enabled=valid&&!busy&&methods.firstOrNull{it.id==payment}?.enabled!=false,modifier=Modifier.fillMaxWidth().height(58.dp),shape=RoundedCornerShape(16.dp)){
                        if(busy){CircularProgressIndicator(Modifier.size(20.dp),strokeWidth=2.dp,color=Color.White);Spacer(Modifier.width(8.dp));Text("Se procesează...")}
                        else{Icon(Icons.Default.Lock,null,modifier=Modifier.size(17.dp));Spacer(Modifier.width(7.dp));Text("Plasează comanda",fontWeight=FontWeight.ExtraBold)}
                    }
                }
            }
        }
    ){pad->
        LazyColumn(
            Modifier.padding(pad).fillMaxSize().padding(horizontal=14.dp),
            verticalArrangement=Arrangement.spacedBy(12.dp),
            contentPadding=PaddingValues(top=12.dp,bottom=18.dp)
        ){
            item{
                Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceEvenly,verticalAlignment=Alignment.Top){
                    CheckoutStepV107("Contact",active=true)
                    Box(Modifier.padding(top=15.dp).height(1.dp).weight(1f).background(Color(0xFFE4E7EC)))
                    CheckoutStepV107("Livrare",active=false)
                    Box(Modifier.padding(top=15.dp).height(1.dp).weight(1f).background(Color(0xFFE4E7EC)))
                    CheckoutStepV107("Plată",active=false)
                }
            }

            item{
                ElevatedCard(shape=RoundedCornerShape(22.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color(0xFF101828))){
                    Column(Modifier.fillMaxWidth().padding(16.dp),verticalArrangement=Arrangement.spacedBy(9.dp)){
                        Row(verticalAlignment=Alignment.CenterVertically){Text("Comanda ta",color=Color.White,fontSize=17.sp,fontWeight=FontWeight.ExtraBold);Spacer(Modifier.weight(1f));Text("${commerce.cartCount()} buc.",color=Color(0xFFD0D5DD),fontSize=11.sp)}
                        lines.take(3).forEach{line->Row(verticalAlignment=Alignment.CenterVertically){AsyncImage(line.product.imageUrl,line.product.name,Modifier.size(44.dp).clip(RoundedCornerShape(9.dp)).background(Color.White).padding(3.dp),contentScale=ContentScale.Fit);Spacer(Modifier.width(8.dp));Text("${line.quantity} × ${line.product.name}",Modifier.weight(1f),color=Color.White,fontSize=11.sp,maxLines=1,overflow=TextOverflow.Ellipsis)}}
                        if(lines.size>3)Text("+ ${lines.size-3} alte produse",fontSize=10.sp,color=Color(0xFFD0D5DD))
                        HorizontalDivider(color=Color.White.copy(alpha=.14f))
                        Row{Text("Total estimat",color=Color(0xFFD0D5DD));Spacer(Modifier.weight(1f));Text(if(allPriced)checkoutMoneyRonV107(subtotal) else "Calculat la final",color=Color.White,fontWeight=FontWeight.ExtraBold)}
                    }
                }
            }

            item{
                CheckoutSectionV107(Icons.Default.AlternateEmail,"Contact","Pentru confirmarea și actualizările comenzii"){
                    OutlinedTextField(email,{email=it},label={Text("Email *")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(14.dp))
                    OutlinedTextField(phone,{phone=it},label={Text("Telefon *")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(14.dp))
                }
            }

            item{
                CheckoutSectionV107(Icons.Default.LocalShipping,"Livrare și facturare","Completează adresa de livrare"){
                    Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){
                        OutlinedTextField(first,{first=it},label={Text("Prenume *")},singleLine=true,modifier=Modifier.weight(1f),shape=RoundedCornerShape(14.dp))
                        OutlinedTextField(last,{last=it},label={Text("Nume *")},singleLine=true,modifier=Modifier.weight(1f),shape=RoundedCornerShape(14.dp))
                    }
                    OutlinedTextField(address,{address=it},label={Text("Stradă, nr. *")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(14.dp))
                    OutlinedTextField(address2,{address2=it},label={Text("Apartament / clădire (opțional)")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(14.dp))
                    Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){
                        OutlinedTextField(city,{city=it},label={Text("Localitate *")},singleLine=true,modifier=Modifier.weight(1.25f),shape=RoundedCornerShape(14.dp))
                        OutlinedTextField(postcode,{postcode=it},label={Text("Cod poștal *")},singleLine=true,modifier=Modifier.weight(.75f),shape=RoundedCornerShape(14.dp))
                    }
                    Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){
                        OutlinedTextField(state,{state=it},label={Text("Județ")},singleLine=true,modifier=Modifier.weight(1f),shape=RoundedCornerShape(14.dp))
                        OutlinedTextField(country,{country=it},label={Text("Țară")},singleLine=true,modifier=Modifier.weight(1f),shape=RoundedCornerShape(14.dp))
                    }
                }
            }

            item{
                CheckoutSectionV107(Icons.Default.Business,"Date companie","Opțional · pentru facturare B2B"){
                    OutlinedTextField(company,{company=it},label={Text("Companie")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(14.dp))
                    OutlinedTextField(vat,{vat=it},label={Text("Cod TVA")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(14.dp))
                }
            }

            item{
                CheckoutSectionV107(Icons.Default.CreditCard,"Metoda de plată"){
                    methods.forEach{m->
                        val selected=payment==m.id
                        OutlinedCard(
                            Modifier.fillMaxWidth().clickable(enabled=m.enabled){payment=m.id},
                            shape=RoundedCornerShape(16.dp),
                            colors=CardDefaults.outlinedCardColors(containerColor=if(selected)Color(0xFFFFF0E5) else Color.White),
                            border=androidx.compose.foundation.BorderStroke(if(selected)2.dp else 1.dp,if(selected)AutoIdOrange else Color(0xFFE4E7EC))
                        ){
                            Row(Modifier.fillMaxWidth().padding(13.dp),verticalAlignment=Alignment.CenterVertically){
                                Surface(shape=RoundedCornerShape(10.dp),color=if(selected)Color.White else Color(0xFFF2F4F7)){
                                    Icon(when(m.id.lowercase()){ "cod"->Icons.Default.LocalShipping;"bacs"->Icons.Default.AccountBalance;"stripe"->Icons.Default.CreditCard;else->Icons.Default.Payments},null,tint=if(selected)AutoIdOrange else Color(0xFF475467),modifier=Modifier.padding(7.dp).size(18.dp))
                                }
                                Spacer(Modifier.width(10.dp))
                                Column(Modifier.weight(1f)){Text(m.title,fontWeight=FontWeight.Bold,color=Color(0xFF101828));Text(m.description,fontSize=10.sp,color=Color(0xFF667085));if(!m.enabled)Text("Indisponibil momentan",fontSize=9.sp,color=AutoIdOrange,fontWeight=FontWeight.Bold)}
                                RadioButton(selected,{if(m.enabled)payment=m.id},enabled=m.enabled)
                            }
                        }
                    }
                }
            }

            item{
                CheckoutSectionV107(Icons.Default.EditNote,"Observații","Opțional"){
                    OutlinedTextField(note,{note=it},label={Text("Instrucțiuni pentru comandă")},minLines=2,maxLines=4,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(14.dp))
                }
            }

            item{
                ElevatedCard(shape=RoundedCornerShape(18.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)){
                    Row(Modifier.fillMaxWidth().clickable{terms=!terms}.padding(14.dp),verticalAlignment=Alignment.CenterVertically){Checkbox(terms,{terms=it});Spacer(Modifier.width(5.dp));Text("Accept termenii și condițiile.",fontSize=11.sp,color=Color(0xFF344054),modifier=Modifier.weight(1f))}
                }
            }

            if(message.isNotBlank())item{
                Surface(color=Color(0xFFFFF1F0),shape=RoundedCornerShape(14.dp),modifier=Modifier.fillMaxWidth()){
                    Row(Modifier.padding(12.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.Info,null,tint=MaterialTheme.colorScheme.error,modifier=Modifier.size(18.dp));Spacer(Modifier.width(7.dp));Text(message,color=MaterialTheme.colorScheme.error,fontSize=11.sp)}
                }
            }
        }
    }
}

@Composable
fun AccountScreenV08(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onHeaderCart:()->Unit={}){
    var mode by remember{mutableStateOf("login")};var email by remember{mutableStateOf(session.customerEmail)};var pass by remember{mutableStateOf("")};var first by remember{mutableStateOf("")};var last by remember{mutableStateOf("")};var company by remember{mutableStateOf("")};var vat by remember{mutableStateOf("")};var msg by remember{mutableStateOf("")};var busy by remember{mutableStateOf(false)};var orders by remember{mutableStateOf<List<Order>>(emptyList())};val token=session.accessToken;val context=androidx.compose.ui.platform.LocalContext.current;val privacy=remember{context.getSharedPreferences("autoid_privacy_v08",Context.MODE_PRIVATE)};var analytics by remember{mutableStateOf(privacy.getBoolean("analytics",false))};var marketing by remember{mutableStateOf(privacy.getBoolean("marketing",false))}
    LaunchedEffect(token){if(token!=null)runCatching{withContext(Dispatchers.IO){api.orders(token)}}.onSuccess{orders=it}}
    LazyColumn(Modifier.fillMaxSize().padding(16.dp).statusBarsPadding(),verticalArrangement=Arrangement.spacedBy(12.dp),contentPadding=PaddingValues(bottom=28.dp)){
        item{HeaderV08("Contul meu",commerce.cartCount(),onCart=onHeaderCart)}
        if(token==null){item{Row{FilterChip(mode=="login",{mode="login";msg=""},{Text("Autentificare")},modifier=Modifier.weight(1f));Spacer(Modifier.width(8.dp));FilterChip(mode=="register",{mode="register";msg=""},{Text("Înregistrare")},modifier=Modifier.weight(1f))}}
            item{ElevatedCard(shape=RoundedCornerShape(20.dp)){Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){Image(painterResource(R.drawable.autoid_logo_transparent),"AutoID",Modifier.width(180.dp).height(54.dp));Text(if(mode=="login")"Bine ai revenit" else "Creează cont AutoID",fontSize=22.sp,fontWeight=FontWeight.ExtraBold);if(mode=="register"){Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){OutlinedTextField(first,{first=it},label={Text("Prenume")},modifier=Modifier.weight(1f));OutlinedTextField(last,{last=it},label={Text("Nume")},modifier=Modifier.weight(1f))};OutlinedTextField(company,{company=it},label={Text("Companie")},modifier=Modifier.fillMaxWidth());OutlinedTextField(vat,{vat=it},label={Text("Cod TVA")},modifier=Modifier.fillMaxWidth())};OutlinedTextField(email,{email=it},label={Text("Email")},modifier=Modifier.fillMaxWidth());OutlinedTextField(pass,{pass=it},label={Text("Parolă")},visualTransformation=PasswordVisualTransformation(),modifier=Modifier.fillMaxWidth());Button(onClick={busy=true},enabled=!busy&&email.isNotBlank()&&pass.length>=8,modifier=Modifier.fillMaxWidth()){Text(if(mode=="login")"Autentificare" else "Creează cont")};OutlinedButton(onClick={msg="Google Sign-In este inclus în UI; OAuth-ul nativ îl conectăm după configurarea Client ID + validarea tokenului în Bridge."},modifier=Modifier.fillMaxWidth()){Icon(Icons.Default.AccountCircle,null);Spacer(Modifier.width(8.dp));Text("Continuă cu Google")};if(msg.isNotBlank())Text(msg,fontSize=12.sp,color=Color(0xFF667085))}}}
            item{LaunchedEffect(busy){if(busy){if(mode=="login")runCatching{withContext(Dispatchers.IO){api.login(email,pass)}}.onSuccess{session.saveLogin(it);msg="Autentificare reușită"}.onFailure{msg=it.message?:"Eroare"} else runCatching{withContext(Dispatchers.IO){api.register(email,pass,first,last,company,vat)}}.onSuccess{msg="Cont creat. Te poți autentifica.";mode="login"}.onFailure{msg=it.message?:"Înregistrarea a eșuat"};busy=false}}}
        }else{item{ElevatedCard{Column(Modifier.padding(16.dp)){Text("● ${session.customerEmail}",fontWeight=FontWeight.ExtraBold,fontSize=18.sp);Text("Client AutoID",color=Color(0xFF667085));OutlinedButton(onClick={session.clear()}){Text("Deconectare")}}}};item{SectionTitle("Comenzile mele","")};if(orders.isEmpty())item{Text("Nu sunt comenzi disponibile sau încă se încarcă.",color=Color(0xFF667085))};items(orders){o->ElevatedCard{ListItem(headlineContent={Text("Comanda #${o.number}",fontWeight=FontWeight.Bold)},supportingContent={Text(o.status)},trailingContent={Text(o.total,fontWeight=FontWeight.Bold)})}}}
        val recent=commerce.recent();if(recent.isNotEmpty()){item{SectionTitle("Vizualizate recent","")};items(recent.take(5)){p->OutlinedCard(Modifier.fillMaxWidth().clickable{onProduct(p)}){Text(p.name,Modifier.padding(14.dp),fontWeight=FontWeight.Medium)}}}
        item{SectionTitle("Confidențialitate în aplicație","");ElevatedCard{Column(Modifier.padding(10.dp)){ListItem(headlineContent={Text("Necesare")},supportingContent={Text("Coș, cont și comenzi")},trailingContent={Switch(true,null)});ListItem(headlineContent={Text("Analytics")},supportingContent={Text("Măsurarea utilizării aplicației")},trailingContent={Switch(analytics,{analytics=it;privacy.edit().putBoolean("analytics",it).apply()})});ListItem(headlineContent={Text("Marketing")},supportingContent={Text("Atribuire și personalizare marketing")},trailingContent={Switch(marketing,{marketing=it;privacy.edit().putBoolean("marketing",it).apply()})})}}}
    }
}
