package ro.autoid.app

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.launch
import ro.autoid.app.data.*
import ro.autoid.app.ui.theme.AutoIdOrange
import com.stripe.android.PaymentConfiguration
import com.stripe.android.paymentsheet.PaymentSheet
import com.stripe.android.paymentsheet.PaymentSheetResult
import com.stripe.android.paymentsheet.rememberPaymentSheet

// Native route: vezi-comanda/{order_id}/
private val OrderInk=Color(0xFF101828)
private val OrderMuted=Color(0xFF667085)
private val OrderSoft=Color(0xFFF7F8FA)
private val OrderBorder=Color(0xFFEAECF0)
private val OrderGood=Color(0xFF067647)

private fun orderMoneyV120(raw:String,currency:String):String{
    val n=raw.replace(",",".").toDoubleOrNull()?:return raw
    val value=java.text.NumberFormat.getNumberInstance(java.util.Locale("ro","RO")).apply{
        minimumFractionDigits=2;maximumFractionDigits=2
    }.format(n)
    return value+if(currency.equals("RON",true))" lei" else " $currency"
}
private fun orderAddressV120(a:AccountAddress):String=listOf(
    listOf(a.firstName,a.lastName).filter{it.isNotBlank()}.joinToString(" "),
    a.company,a.address1,a.address2,
    listOf(a.postcode,a.city).filter{it.isNotBlank()}.joinToString(" "),
    a.state,a.country
).filter{it.isNotBlank()}.joinToString(", ")

@Composable
private fun OrderSectionV120(icon:androidx.compose.ui.graphics.vector.ImageVector,title:String,subtitle:String="",content:@Composable ColumnScope.()->Unit){
    ElevatedCard(
        shape=RoundedCornerShape(22.dp),
        colors=CardDefaults.elevatedCardColors(containerColor=Color.White),
        elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)
    ){
        Column(Modifier.fillMaxWidth().padding(16.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
            Row(verticalAlignment=Alignment.CenterVertically){
                Surface(shape=RoundedCornerShape(11.dp),color=Color(0xFFFFF1E8)){
                    Icon(icon,null,tint=AutoIdOrange,modifier=Modifier.padding(8.dp).size(18.dp))
                }
                Spacer(Modifier.width(10.dp))
                Column{
                    Text(title,fontSize=16.sp,fontWeight=FontWeight.ExtraBold,color=OrderInk)
                    if(subtitle.isNotBlank())Text(subtitle,fontSize=10.sp,color=OrderMuted)
                }
            }
            content()
        }
    }
}

@Composable
private fun DetailLineV120(label:String,value:String){
    if(value.isBlank())return
    Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.Top){
        Text(label,Modifier.weight(1f),fontSize=10.sp,color=OrderMuted)
        Text(value,Modifier.weight(1.35f),fontSize=10.sp,fontWeight=FontWeight.SemiBold,color=OrderInk,textAlign=TextAlign.End)
    }
}
@Composable
private fun MoneyRowV120(label:String,raw:String,currency:String,bold:Boolean=false){
    Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
        Text(label,Modifier.weight(1f),fontSize=if(bold)13.sp else 11.sp,color=if(bold)OrderInk else OrderMuted,fontWeight=if(bold)FontWeight.ExtraBold else FontWeight.Normal)
        Text(orderMoneyV120(raw,currency),fontSize=if(bold)17.sp else 11.sp,fontWeight=if(bold)FontWeight.ExtraBold else FontWeight.Bold,color=OrderInk)
    }
}

@Composable
private fun OrderStatusV120(d:OrderDetail){
    val terminal=orderIsTerminalV121(d.status)
    val visualStatus=orderDisplayStatusV121(d.status,d.trackingNumber,d.statusLabel.ifBlank{d.status})
    ElevatedCard(shape=RoundedCornerShape(22.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){
        Column(Modifier.fillMaxWidth().padding(17.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
            Text("Comanda #${d.number}",fontSize=20.sp,fontWeight=FontWeight.ExtraBold,color=OrderInk)
            Text(visualStatus,fontSize=11.sp,fontWeight=FontWeight.Bold,color=if(terminal)MaterialTheme.colorScheme.error else OrderGood)
            if(terminal){
                Surface(shape=RoundedCornerShape(14.dp),color=Color(0xFFFFF1F0)){
                    Text("Această comandă nu mai este activă.",Modifier.fillMaxWidth().padding(11.dp),fontSize=10.sp,color=MaterialTheme.colorScheme.error)
                }
            }else{
                OrderStatusProgressV121(d.status,d.trackingNumber)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrderDetailV120(api:AutoIdApi,token:String,orderId:Long,onBack:()->Unit){
    var detail by remember(orderId){mutableStateOf<OrderDetail?>(null)}
    var loading by remember(orderId){mutableStateOf(true)}
    var error by remember(orderId){mutableStateOf("")}
    var reload by remember{mutableIntStateOf(0)}
    var actionBusy by remember{mutableStateOf(false)}
    var actionMessage by remember{mutableStateOf("")}
    var pendingPayment by remember{mutableStateOf<OrderPaymentSessionV127?>(null)}
    val context=androidx.compose.ui.platform.LocalContext.current
    val uriHandler=LocalUriHandler.current
    val paymentSheet=rememberPaymentSheet{result->when(result){
        is PaymentSheetResult.Completed->{val p=pendingPayment;if(p!=null){actionBusy=true;actionMessage="Confirmăm plata…"}}
        is PaymentSheetResult.Canceled->{actionMessage="Plata a fost anulată. Comanda rămâne în așteptare."}
        is PaymentSheetResult.Failed->{actionMessage=result.error.localizedMessage?:"Plata nu a putut fi finalizată."}
    }}
    BackHandler(onBack=onBack)
    LaunchedEffect(actionBusy){if(actionBusy){val p=pendingPayment;if(p!=null){runCatching{withContext(Dispatchers.IO){api.confirmStripePayment(p.orderId,p.paymentIntentId,p.paymentToken,token)}}.onSuccess{ok->if(ok){actionMessage="Plata a fost confirmată.";pendingPayment=null;reload++}else actionMessage="Plata nu este încă confirmată."}.onFailure{actionMessage=it.message?:"Confirmarea plății a eșuat."}};actionBusy=false}}
    LaunchedEffect(orderId,token,reload){
        loading=true;error="";detail=null
        runCatching{withContext(Dispatchers.IO){api.orderDetail(token,orderId)}}
            .onSuccess{detail=it}
            .onFailure{error=it.message?:"Comanda nu a putut fi încărcată."}
        loading=false
    }
    Scaffold(
        containerColor=OrderSoft,
        topBar={
            TopAppBar(
                title={Column{Text("Vezi comanda",fontWeight=FontWeight.ExtraBold);Text("Comenzi",fontSize=10.sp,color=OrderMuted)}},
                navigationIcon={IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi la Comenzi")}},
                colors=TopAppBarDefaults.topAppBarColors(containerColor=Color.White)
            )
        }
    ){pad->
        when{
            loading->Box(Modifier.padding(pad).fillMaxSize(),contentAlignment=Alignment.Center){CircularProgressIndicator(color=AutoIdOrange)}
            error.isNotBlank()->Box(Modifier.padding(pad).fillMaxSize().padding(20.dp),contentAlignment=Alignment.Center){
                ElevatedCard(shape=RoundedCornerShape(22.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){
                    Column(Modifier.padding(18.dp),horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(9.dp)){
                        Icon(Icons.Default.ErrorOutline,null,tint=MaterialTheme.colorScheme.error,modifier=Modifier.size(34.dp))
                        Text("Nu am putut încărca această comandă",fontWeight=FontWeight.ExtraBold,color=OrderInk,textAlign=TextAlign.Center)
                        Text(error,fontSize=10.sp,color=OrderMuted,textAlign=TextAlign.Center)
                        Button(onClick={reload++}){Text("Reîncearcă")}
                    }
                }
            }
            detail!=null->{
                val d=detail!!
                LazyColumn(
                    Modifier.padding(pad).fillMaxSize(),
                    verticalArrangement=Arrangement.spacedBy(12.dp),
                    contentPadding=PaddingValues(horizontal=14.dp,vertical=14.dp)
                ){
                    item{OrderStatusV120(d)}
                    if(d.canPay||d.canCancel) item{
                        OrderSectionV120(Icons.Default.Payments,"Acțiuni comandă"){
                            if(actionMessage.isNotBlank())Text(actionMessage,fontSize=10.sp,color=if(actionMessage.contains("confirmată"))OrderGood else OrderMuted)
                            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(8.dp)){
                                if(d.canPay)Button(onClick={actionMessage="Pregătim plata securizată…";kotlinx.coroutines.CoroutineScope(Dispatchers.Main).launch{runCatching{withContext(Dispatchers.IO){api.orderActionV127(token,d.id,"pay")}}.onSuccess{p->if(p!=null){pendingPayment=p;PaymentConfiguration.init(context,p.publishableKey);paymentSheet.presentWithPaymentIntent(p.clientSecret,PaymentSheet.Configuration(merchantDisplayName="AutoID Professional Solutions",googlePay=PaymentSheet.GooglePayConfiguration(environment=PaymentSheet.GooglePayConfiguration.Environment.Test,countryCode="RO",currencyCode=d.currency),allowsDelayedPaymentMethods=false))}}.onFailure{actionMessage=it.message?:"Plata nu a putut fi reluată."}}},modifier=Modifier.weight(1f),shape=RoundedCornerShape(10.dp)){Text("Plătește",fontWeight=FontWeight.ExtraBold)}
                                if(d.canCancel)OutlinedButton(onClick={actionBusy=true;kotlinx.coroutines.CoroutineScope(Dispatchers.Main).launch{runCatching{withContext(Dispatchers.IO){api.orderActionV127(token,d.id,"cancel")}}.onSuccess{actionMessage="Comanda a fost anulată.";reload++}.onFailure{actionMessage=it.message?:"Comanda nu a putut fi anulată."};actionBusy=false}},modifier=Modifier.weight(1f),shape=RoundedCornerShape(10.dp)){Text("Anulează",color=MaterialTheme.colorScheme.error,fontWeight=FontWeight.ExtraBold)}
                            }
                        }
                    }
                    if(d.trackingNumber.isNotBlank())item{
                        OrderSectionV120(Icons.Default.LocalShipping,"Livrarea comenzii","${d.carrier.ifBlank{"GLS"}} · AWB ${d.trackingNumber}"){
                            Text("Coletul are număr de urmărire disponibil.",fontSize=11.sp,color=OrderMuted)
                            Button(onClick={if(d.trackingUrl.isNotBlank())uriHandler.openUri(d.trackingUrl)},enabled=d.trackingUrl.isNotBlank(),modifier=Modifier.fillMaxWidth()){
                                Icon(Icons.Default.LocationOn,null,Modifier.size(17.dp));Spacer(Modifier.width(6.dp));Text("Urmărește coletul",fontWeight=FontWeight.ExtraBold)
                            }
                        }
                    }
                    item{Text("Produse",fontSize=17.sp,fontWeight=FontWeight.ExtraBold,color=OrderInk)}
                    items(d.items,key={it.productId.toString()+it.name}){line->
                        ElevatedCard(shape=RoundedCornerShape(18.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){
                            Row(Modifier.fillMaxWidth().padding(12.dp),verticalAlignment=Alignment.CenterVertically){
                                if(!line.imageUrl.isNullOrBlank()){
                                    AsyncImage(line.imageUrl,line.name,Modifier.size(62.dp).clip(RoundedCornerShape(12.dp)).background(Color.White),contentScale=ContentScale.Fit)
                                    Spacer(Modifier.width(10.dp))
                                }
                                Column(Modifier.weight(1f)){
                                    Text(line.name,fontWeight=FontWeight.Bold,color=OrderInk,fontSize=12.sp,maxLines=2,overflow=TextOverflow.Ellipsis)
                                    Text("Cantitate: ${line.quantity}",fontSize=9.sp,color=OrderMuted)
                                }
                                Text(orderMoneyV120(line.total,d.currency),fontWeight=FontWeight.ExtraBold,color=OrderInk,fontSize=11.sp)
                            }
                        }
                    }
                    item{
                        OrderSectionV120(Icons.Default.ReceiptLong,"Sumar comandă","Comanda #${d.number}"){
                            MoneyRowV120("Subtotal",d.subtotal,d.currency)
                            val discount=d.discountTotal.toDoubleOrNull()?:0.0
                            if(discount>0)Row(Modifier.fillMaxWidth()){Text("Reducere",Modifier.weight(1f),fontSize=11.sp,color=OrderMuted);Text("-"+orderMoneyV120(d.discountTotal,d.currency),fontSize=11.sp,fontWeight=FontWeight.Bold,color=OrderInk)}
                            MoneyRowV120("Livrare",d.shippingTotal,d.currency)
                            MoneyRowV120("TVA",d.taxTotal,d.currency)
                            HorizontalDivider(color=OrderBorder)
                            MoneyRowV120("Total",d.total,d.currency,bold=true)
                        }
                    }
                    item{
                        OrderSectionV120(Icons.Default.CreditCard,"Plată și livrare"){
                            DetailLineV120("Metoda de plată",d.paymentMethod)
                            DetailLineV120("Metoda de livrare",d.shippingMethod)
                            DetailLineV120("Data comenzii",d.createdAt)
                        }
                    }
                    item{
                        OrderSectionV120(Icons.Default.HomeWork,"Adrese comandă"){
                            Text("Facturare",fontWeight=FontWeight.ExtraBold,color=OrderInk)
                            Text(orderAddressV120(d.billing),fontSize=11.sp,color=OrderMuted)
                            Spacer(Modifier.height(7.dp))
                            Text("Livrare",fontWeight=FontWeight.ExtraBold,color=OrderInk)
                            Text(orderAddressV120(d.shipping),fontSize=11.sp,color=OrderMuted)
                        }
                    }
                    if(d.customerNote.isNotBlank())item{OrderSectionV120(Icons.Default.Notes,"Notă comandă"){Text(d.customerNote,fontSize=11.sp,color=OrderInk)}}
                    if(d.notes.isNotEmpty())item{
                        OrderSectionV120(Icons.Default.History,"Actualizări comandă"){
                            d.notes.forEachIndexed{i,n->
                                Text(n.content,fontSize=11.sp,color=OrderInk)
                                if(n.createdAt.isNotBlank())Text(n.createdAt,fontSize=9.sp,color=OrderMuted)
                                if(i<d.notes.lastIndex)HorizontalDivider(color=OrderBorder)
                            }
                        }
                    }
                }
            }
        }
    }
}
