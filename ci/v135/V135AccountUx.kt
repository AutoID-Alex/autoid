package ro.autoid.app

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import ro.autoid.app.data.*
import ro.autoid.app.ui.theme.AutoIdOrange
import java.net.HttpURLConnection
import java.net.URI
import java.net.URLEncoder

private val A135Ink=Color(0xFF101828)
private val A135Muted=Color(0xFF667085)
private val A135Soft=Color(0xFFF6F8FB)
private val A135Border=Color(0xFFE4E7EC)
private val A135Good=Color(0xFF087A55)

private object AccountApiV135 {
    private fun enc(v:String)=URLEncoder.encode(v,"UTF-8")
    fun orders(token:String,query:String="",limit:Int=20):List<Order>{
        val q=if(query.isBlank())"" else "&search=${enc(query.trim())}"
        val c=(URI("${AutoIdApi.MOBILE}/me/orders?limit=${limit.coerceIn(1,50)}$q").toURL().openConnection() as HttpURLConnection).apply{
            requestMethod="GET";connectTimeout=10000;readTimeout=18000;setRequestProperty("Accept","application/json");setRequestProperty("Authorization","Bearer $token");setRequestProperty("User-Agent","AutoID-Android/1.0.30")
        }
        val status=c.responseCode
        val raw=(if(status in 200..299)c.inputStream else c.errorStream)?.bufferedReader()?.use{it.readText()}.orEmpty()
        c.disconnect()
        if(status !in 200..299)throw AutoIdHttpExceptionV129(status,runCatching{JSONObject(raw).optString("message")}.getOrDefault("").ifBlank{"HTTP $status"})
        val a=if(raw.trimStart().startsWith("["))JSONArray(raw) else JSONObject(raw).optJSONArray("orders")?:JSONArray()
        return (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{o->
            val currency=o.optString("currency","RON")
            val total=o.optString("total")+if(currency.equals("EUR",true))" €" else " lei"
            Order(o.optLong("id"),o.optString("number",o.optLong("id").toString()),o.optString("status_label",o.optString("status")),total,o.optString("created_at"),o.optString("status"),o.optString("tracking_number"),o.optString("tracking_url"),o.optString("carrier"),o.optBoolean("review_consent"),o.optBoolean("can_pay"),o.optBoolean("can_cancel"))
        }}
    }
}

@Composable private fun AccountBackV135(title:String,onBack:()->Unit){
    Row(Modifier.fillMaxWidth().padding(horizontal=8.dp,vertical=4.dp),verticalAlignment=Alignment.CenterVertically){
        TextButton(onClick=onBack){Icon(Icons.Default.ArrowBack,null);Spacer(Modifier.width(5.dp));Text("Înapoi la cont")}
        Spacer(Modifier.weight(1f));Text(title,fontWeight=FontWeight.ExtraBold,color=A135Ink,modifier=Modifier.padding(end=12.dp))
    }
}

@Composable private fun AccountMenuRowV135(icon:androidx.compose.ui.graphics.vector.ImageVector,label:String,onClick:()->Unit){
    Row(Modifier.fillMaxWidth().clickable(onClick=onClick).padding(horizontal=14.dp,vertical=13.dp),verticalAlignment=Alignment.CenterVertically){
        Icon(icon,null,tint=A135Muted,modifier=Modifier.size(20.dp));Spacer(Modifier.width(12.dp));Text(label,Modifier.weight(1f),fontWeight=FontWeight.SemiBold,color=A135Ink);Icon(Icons.Default.ChevronRight,null,tint=A135Muted)
    }
}

@Composable private fun LatestOrderV135(o:Order,onOpen:()->Unit){
    ElevatedCard(shape=RoundedCornerShape(14.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){
        Column(Modifier.fillMaxWidth().padding(16.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){
            Text("ULTIMA COMANDĂ",fontSize=9.sp,fontWeight=FontWeight.ExtraBold,color=A135Muted)
            Row(verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text("Comanda #${o.number}",fontSize=18.sp,fontWeight=FontWeight.ExtraBold,color=A135Ink);Text(orderDisplayStatusV121(o.statusCode,o.trackingNumber,o.status),fontSize=10.sp,fontWeight=FontWeight.Bold,color=if(orderIsTerminalV121(o.statusCode))MaterialTheme.colorScheme.error else A135Good)};Button(onClick=onOpen,shape=RoundedCornerShape(10.dp)){Text("Vezi comanda",fontSize=10.sp)}}
            Text("Total: ${o.total}",fontWeight=FontWeight.ExtraBold,color=A135Ink)
            if(!orderIsTerminalV121(o.statusCode))OrderStatusProgressV121(o.statusCode,o.trackingNumber)
        }
    }
}

@Composable private fun LatestRfqV135(r:RfqSummaryV130,onOpen:()->Unit){
    ElevatedCard(shape=RoundedCornerShape(14.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){
        Row(Modifier.fillMaxWidth().padding(16.dp),verticalAlignment=Alignment.CenterVertically){
            Surface(shape=RoundedCornerShape(10.dp),color=Color(0xFFFFF1E8)){Icon(Icons.Default.RequestQuote,null,tint=AutoIdOrange,modifier=Modifier.padding(9.dp))};Spacer(Modifier.width(11.dp))
            Column(Modifier.weight(1f)){Text("ULTIMA CERERE DE OFERTĂ",fontSize=9.sp,fontWeight=FontWeight.ExtraBold,color=A135Muted);Text(r.reference.ifBlank{"RFQ #${r.id}"},fontWeight=FontWeight.ExtraBold,color=A135Ink);Text(r.statusLabel,fontSize=10.sp,color=A135Good)}
            TextButton(onClick=onOpen){Text("Vezi")}
        }
    }
}

@Composable private fun AccountOrdersV135(token:String,onBack:()->Unit,onDetail:(Long)->Unit){
    var query by remember{mutableStateOf("")};var rows by remember{mutableStateOf<List<Order>>(emptyList())};var loading by remember{mutableStateOf(true)};var error by remember{mutableStateOf("")}
    LaunchedEffect(query){delay(300);loading=true;error="";runCatching{withContext(Dispatchers.IO){AccountApiV135.orders(token,query,50)}}.onSuccess{rows=it}.onFailure{error=it.message?:"Comenzile nu au putut fi încărcate."};loading=false}
    BackHandler(onBack=onBack)
    LazyColumn(Modifier.fillMaxSize().background(A135Soft),contentPadding=PaddingValues(bottom=24.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
        item{AccountBackV135("Comenzi",onBack)}
        item{OutlinedTextField(query,{query=it},modifier=Modifier.fillMaxWidth().padding(horizontal=14.dp),singleLine=true,leadingIcon={Icon(Icons.Default.Search,null)},placeholder={Text("Caută după Order ID / număr comandă")},shape=RoundedCornerShape(12.dp))}
        if(loading)item{LinearProgressIndicator(Modifier.fillMaxWidth().padding(horizontal=14.dp),color=AutoIdOrange)}
        if(error.isNotBlank())item{Text(error,Modifier.padding(horizontal=14.dp),color=MaterialTheme.colorScheme.error,fontSize=11.sp)}
        if(!loading&&rows.isEmpty())item{Text("Nu am găsit comenzi.",Modifier.padding(18.dp),color=A135Muted)}
        items(rows,key={it.id}){o->ElevatedCard(onClick={onDetail(o.id)},modifier=Modifier.fillMaxWidth().padding(horizontal=14.dp),shape=RoundedCornerShape(14.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Row(Modifier.fillMaxWidth().padding(14.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.ReceiptLong,null,tint=AutoIdOrange);Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)){Text("Comanda #${o.number}",fontWeight=FontWeight.ExtraBold,color=A135Ink);Text(orderDisplayStatusV121(o.statusCode,o.trackingNumber,o.status),fontSize=10.sp,color=A135Muted)};Text(o.total,fontSize=11.sp,fontWeight=FontWeight.Bold,color=A135Ink);Icon(Icons.Default.ChevronRight,null,tint=A135Muted)}}}
    }
}

@Composable private fun AccountProfileV135(api:AutoIdApi,token:String,onBack:()->Unit){
    var p by remember{mutableStateOf<AccountProfile?>(null)};var first by remember{mutableStateOf("")};var last by remember{mutableStateOf("")};var email by remember{mutableStateOf("")};var editing by remember{mutableStateOf(false)};var msg by remember{mutableStateOf("")};val scope=rememberCoroutineScope()
    LaunchedEffect(token){runCatching{withContext(Dispatchers.IO){api.accountProfile(token)}}.onSuccess{p=it;first=it.firstName;last=it.lastName;email=it.email}}
    BackHandler(onBack=onBack)
    LazyColumn(Modifier.fillMaxSize().background(A135Soft),contentPadding=PaddingValues(bottom=24.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
        item{AccountBackV135("Detalii cont",onBack)}
        item{ElevatedCard(Modifier.fillMaxWidth().padding(horizontal=14.dp),shape=RoundedCornerShape(14.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
            if(p==null)CircularProgressIndicator(color=AutoIdOrange) else if(!editing){Text("$first $last".trim().ifBlank{"Cont AutoID"},fontSize=19.sp,fontWeight=FontWeight.ExtraBold,color=A135Ink);Text(email,color=A135Muted);OutlinedButton(onClick={editing=true}){Icon(Icons.Default.Edit,null);Spacer(Modifier.width(5.dp));Text("Editează")}}
            else{OutlinedTextField(first,{first=it},label={Text("Prenume")},modifier=Modifier.fillMaxWidth());OutlinedTextField(last,{last=it},label={Text("Nume")},modifier=Modifier.fillMaxWidth());OutlinedTextField(email,{email=it},label={Text("Email")},modifier=Modifier.fillMaxWidth());Button(onClick={scope.launch{runCatching{withContext(Dispatchers.IO){api.saveAccountProfile(token,first,last,email)}}.onSuccess{p=it;editing=false;msg="Date salvate."}.onFailure{msg=it.message?:"Salvarea a eșuat."}}},modifier=Modifier.fillMaxWidth()){Text("Salvează")}}
            if(msg.isNotBlank())Text(msg,fontSize=11.sp,color=A135Muted)
        }}}
    }
}

@Composable private fun AddressSummaryV135(title:String,a:AccountAddress){
    Column(verticalArrangement=Arrangement.spacedBy(3.dp)){Text(title,fontWeight=FontWeight.ExtraBold,color=A135Ink);Text(listOf("${a.firstName} ${a.lastName}".trim(),a.company,a.address1,a.address2,"${a.postcode} ${a.city}".trim(),a.country,a.phone,a.email).filter{it.isNotBlank()}.joinToString(" · "),fontSize=11.sp,color=A135Muted)}
}

@Composable private fun AccountAddressesV135(api:AutoIdApi,token:String,onBack:()->Unit){
    var data by remember{mutableStateOf<AccountAddresses?>(null)};var editing by remember{mutableStateOf(false)};var billing by remember{mutableStateOf(AccountAddress())};var shipping by remember{mutableStateOf(AccountAddress())};var vat by remember{mutableStateOf("")};var msg by remember{mutableStateOf("")};val scope=rememberCoroutineScope()
    LaunchedEffect(token){runCatching{withContext(Dispatchers.IO){api.accountAddresses(token)}}.onSuccess{data=it;billing=it.billing;shipping=it.shipping;vat=it.vatNumber}}
    BackHandler(onBack=onBack)
    fun field(a:AccountAddress,key:String,v:String)=when(key){"address1"->a.copy(address1=v);"city"->a.copy(city=v);"postcode"->a.copy(postcode=v);"phone"->a.copy(phone=v);"company"->a.copy(company=v);else->a}
    LazyColumn(Modifier.fillMaxSize().background(A135Soft),contentPadding=PaddingValues(bottom=24.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
        item{AccountBackV135("Adrese Facturare / Livrare",onBack)}
        item{ElevatedCard(Modifier.fillMaxWidth().padding(horizontal=14.dp),shape=RoundedCornerShape(14.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
            if(data==null)CircularProgressIndicator(color=AutoIdOrange) else if(!editing){AddressSummaryV135("Facturare",billing);HorizontalDivider(color=A135Border);AddressSummaryV135("Livrare",shipping);if(vat.isNotBlank())Text("Cod TVA: $vat",fontWeight=FontWeight.Bold,color=A135Ink);OutlinedButton(onClick={editing=true}){Text("Editează adresele")}}
            else{Text("Facturare",fontWeight=FontWeight.ExtraBold);OutlinedTextField(billing.company,{billing=field(billing,"company",it)},label={Text("Companie")},modifier=Modifier.fillMaxWidth());OutlinedTextField(billing.address1,{billing=field(billing,"address1",it)},label={Text("Stradă, nr.")},modifier=Modifier.fillMaxWidth());Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){OutlinedTextField(billing.postcode,{billing=field(billing,"postcode",it)},label={Text("Cod poștal")},modifier=Modifier.weight(1f));OutlinedTextField(billing.city,{billing=field(billing,"city",it)},label={Text("Localitate")},modifier=Modifier.weight(1f))};OutlinedTextField(billing.phone,{billing=field(billing,"phone",it)},label={Text("Telefon")},modifier=Modifier.fillMaxWidth());OutlinedTextField(vat,{vat=it},label={Text("Cod TVA")},modifier=Modifier.fillMaxWidth());Text("Livrare",fontWeight=FontWeight.ExtraBold);OutlinedTextField(shipping.address1,{shipping=field(shipping,"address1",it)},label={Text("Stradă, nr.")},modifier=Modifier.fillMaxWidth());Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){OutlinedTextField(shipping.postcode,{shipping=field(shipping,"postcode",it)},label={Text("Cod poștal")},modifier=Modifier.weight(1f));OutlinedTextField(shipping.city,{shipping=field(shipping,"city",it)},label={Text("Localitate")},modifier=Modifier.weight(1f))};Button(onClick={scope.launch{runCatching{withContext(Dispatchers.IO){api.saveAccountAddresses(token,AccountAddresses(billing,shipping,vat))}}.onSuccess{data=it;billing=it.billing;shipping=it.shipping;vat=it.vatNumber;editing=false;msg="Adrese salvate."}.onFailure{msg=it.message?:"Salvarea a eșuat."}}},modifier=Modifier.fillMaxWidth()){Text("Salvează")}}
            if(msg.isNotBlank())Text(msg,fontSize=11.sp,color=A135Muted)
        }}}
    }
}

@Composable private fun AccountPaymentsV135(api:AutoIdApi,token:String,onBack:()->Unit){
    var rows by remember{mutableStateOf<List<SavedPaymentMethod>>(emptyList())};var loading by remember{mutableStateOf(true)};var msg by remember{mutableStateOf("")};val scope=rememberCoroutineScope()
    fun reload(){scope.launch{loading=true;runCatching{withContext(Dispatchers.IO){api.savedPaymentMethods(token)}}.onSuccess{rows=it}.onFailure{msg=it.message?:"Metodele de plată nu pot fi încărcate."};loading=false}}
    LaunchedEffect(token){reload()};BackHandler(onBack=onBack)
    LazyColumn(Modifier.fillMaxSize().background(A135Soft),contentPadding=PaddingValues(bottom=24.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
        item{AccountBackV135("Metode de plată",onBack)}
        if(loading)item{Box(Modifier.fillMaxWidth(),contentAlignment=Alignment.Center){CircularProgressIndicator(color=AutoIdOrange)}}
        if(!loading&&rows.isEmpty())item{Text("Nu ai metode de plată salvate.",Modifier.padding(18.dp),color=A135Muted)}
        items(rows,key={it.id}){m->ElevatedCard(Modifier.fillMaxWidth().padding(horizontal=14.dp),shape=RoundedCornerShape(14.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Row(Modifier.fillMaxWidth().padding(14.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.CreditCard,null,tint=AutoIdOrange);Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)){Text(m.label,fontWeight=FontWeight.Bold,color=A135Ink);if(m.isDefault)Text("Implicită",fontSize=9.sp,color=A135Good)};if(!m.isDefault)TextButton(onClick={scope.launch{runCatching{withContext(Dispatchers.IO){api.paymentMethodAction(token,m.id,"default")}}.onSuccess{rows=it}}}){Text("Implicită")};TextButton(onClick={scope.launch{runCatching{withContext(Dispatchers.IO){api.paymentMethodAction(token,m.id,"delete")}}.onSuccess{rows=it}}}){Text("Șterge",color=MaterialTheme.colorScheme.error)}}}}
        if(msg.isNotBlank())item{Text(msg,Modifier.padding(horizontal=14.dp),fontSize=11.sp,color=A135Muted)}
    }
}

@Composable private fun AccountPrivacyV135(onBack:()->Unit){val uri=LocalUriHandler.current;BackHandler(onBack=onBack);Column(Modifier.fillMaxSize().background(A135Soft)){AccountBackV135("Confidențialitate și consimțământ",onBack);ElevatedCard(Modifier.fillMaxWidth().padding(14.dp),shape=RoundedCornerShape(14.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){Icon(Icons.Default.PrivacyTip,null,tint=AutoIdOrange);Text("Confidențialitate și consimțământ",fontWeight=FontWeight.ExtraBold,color=A135Ink);Text("Poți consulta politica AutoID și opțiunile de confidențialitate asociate contului tău.",fontSize=11.sp,color=A135Muted);OutlinedButton(onClick={uri.openUri("https://www.autoid.ro/politica-de-confidentialitate/")}){Text("Politica de confidențialitate")}}}}
}

@Composable fun AccountV135(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onCart:()->Unit,onRfqs:()->Unit){
    val token=session.accessToken?:return
    var page by remember{mutableStateOf("dashboard")};var selectedOrder by remember{mutableStateOf<Long?>(null)};var profile by remember{mutableStateOf<AccountProfile?>(null)};var addresses by remember{mutableStateOf<AccountAddresses?>(null)};var latestOrder by remember{mutableStateOf<Order?>(null)};var latestRfq by remember{mutableStateOf<RfqSummaryV130?>(null)};var loading by remember{mutableStateOf(true)};val scope=rememberCoroutineScope()
    selectedOrder?.let{id->OrderDetailV120(api,token,id,onBack={selectedOrder=null;page="orders"});return}
    when(page){"orders"->{AccountOrdersV135(token,{page="dashboard"},{selectedOrder=it});return};"details"->{AccountProfileV135(api,token){page="dashboard"};return};"addresses"->{AccountAddressesV135(api,token){page="dashboard"};return};"payments"->{AccountPaymentsV135(api,token){page="dashboard"};return};"privacy"->{AccountPrivacyV135{page="dashboard"};return}}
    LaunchedEffect(token){loading=true;runCatching{withContext(Dispatchers.IO){coroutineScope{val p=async{api.accountProfile(token)};val a=async{api.accountAddresses(token)};val o=async{AccountApiV135.orders(token,"",1).firstOrNull()};val r=async{RfqApiV130.list(token,1,"",1).items.firstOrNull()};arrayOf(p.await(),a.await(),o.await(),r.await())}}}.onSuccess{all->profile=all[0] as AccountProfile;addresses=all[1] as AccountAddresses;latestOrder=all[2] as Order?;latestRfq=all[3] as RfqSummaryV130?};loading=false}
    LazyColumn(Modifier.fillMaxSize().background(A135Soft).statusBarsPadding(),contentPadding=PaddingValues(horizontal=14.dp,vertical=12.dp),verticalArrangement=Arrangement.spacedBy(12.dp)){
        item{ElevatedCard(shape=RoundedCornerShape(12.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color(0xFF111827))){Column(Modifier.fillMaxWidth().padding(18.dp),verticalArrangement=Arrangement.spacedBy(6.dp)){Text("CONT AUTOID: ${addresses?.billing?.company?.ifBlank{"SOFA SOFT SRL"}?:"SOFA SOFT SRL"}",fontWeight=FontWeight.ExtraBold,color=Color.White);addresses?.vatNumber?.takeIf{it.isNotBlank()}?.let{Text("COD TVA: $it",fontSize=10.sp,color=Color(0xFF98A2B3))};Spacer(Modifier.height(8.dp));Text(listOfNotNull(profile?.firstName,profile?.lastName).filter{it.isNotBlank()}.joinToString(" ").ifBlank{"Cont AutoID"},fontSize=22.sp,fontWeight=FontWeight.ExtraBold,color=Color.White);Text(profile?.email?:session.customerEmail,fontSize=11.sp,color=Color(0xFF98A2B3))}}}
        item{ElevatedCard(shape=RoundedCornerShape(14.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Column{AccountMenuRowV135(Icons.Default.Dashboard,"Panou control"){};HorizontalDivider(color=A135Border);AccountMenuRowV135(Icons.Default.ReceiptLong,"Comenzi"){page="orders"};HorizontalDivider(color=A135Border);AccountMenuRowV135(Icons.Default.RequestQuote,"Cereri de ofertă"){onRfqs()};HorizontalDivider(color=A135Border);AccountMenuRowV135(Icons.Default.ManageAccounts,"Detalii cont"){page="details"};HorizontalDivider(color=A135Border);AccountMenuRowV135(Icons.Default.HomeWork,"Adrese Facturare / Livrare"){page="addresses"};HorizontalDivider(color=A135Border);AccountMenuRowV135(Icons.Default.CreditCard,"Metode de plată"){page="payments"};HorizontalDivider(color=A135Border);AccountMenuRowV135(Icons.Default.PrivacyTip,"Confidențialitate și consimțământ"){page="privacy"}}}}
        if(loading)item{LinearProgressIndicator(Modifier.fillMaxWidth(),color=AutoIdOrange)}
        latestOrder?.let{o->item{LatestOrderV135(o){selectedOrder=o.id}}}
        latestRfq?.let{r->item{LatestRfqV135(r){session.pendingRfqIdV130=r.id;onRfqs()}}}
        item{OutlinedButton(onClick={session.clear()},modifier=Modifier.fillMaxWidth().height(52.dp),shape=RoundedCornerShape(12.dp)){Icon(Icons.Default.Logout,null);Spacer(Modifier.width(7.dp));Text("Dezautentificare",fontWeight=FontWeight.ExtraBold)}}
    }
}
