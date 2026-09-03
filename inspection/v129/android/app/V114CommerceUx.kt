package ro.autoid.app

import android.view.ContextThemeWrapper

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.credentials.CredentialManager
import androidx.credentials.CustomCredential
import androidx.credentials.GetCredentialRequest
import androidx.credentials.exceptions.GetCredentialException
import com.google.android.libraries.identity.googleid.GetGoogleIdOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential
import com.stripe.android.PaymentConfiguration
import androidx.compose.ui.viewinterop.AndroidView
import com.stripe.android.googlepaylauncher.GooglePayEnvironment
import com.stripe.android.googlepaylauncher.GooglePayLauncher
import com.stripe.android.googlepaylauncher.rememberGooglePayLauncher
import com.stripe.android.model.Address
import com.stripe.android.model.ConfirmPaymentIntentParams
import com.stripe.android.model.PaymentMethod as StripePaymentMethod
import com.stripe.android.model.PaymentMethodCreateParams
import com.stripe.android.payments.paymentlauncher.PaymentResult
import com.stripe.android.payments.paymentlauncher.rememberPaymentLauncher
import com.stripe.android.view.CardInputWidget
import coil.compose.AsyncImage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import ro.autoid.app.data.*
import ro.autoid.app.ui.theme.AutoIdOrange
import kotlin.math.max

private val C114Ink=Color(0xFF101828)
private val C114Muted=Color(0xFF667085)
private val C114Soft=Color(0xFFF7F8FA)
private val C114Border=Color(0xFFEAECF0)
private val C114Good=Color(0xFF067647)
private val C114GoodSoft=Color(0xFFE8F7EF)
private val C114OrangeSoft=Color(0xFFFFF1E8)

@Composable private fun PrivacyPrefRowV128(title:String,desc:String,checked:Boolean,onChecked:(Boolean)->Unit){
    Row(Modifier.fillMaxWidth().padding(vertical=7.dp),verticalAlignment=Alignment.CenterVertically){
        Column(Modifier.weight(1f)){Text(title,fontWeight=FontWeight.SemiBold,color=C114Ink,fontSize=12.sp);Text(desc,fontSize=9.sp,color=C114Muted)}
        Switch(checked,onChecked)
    }
}

private fun unitRonV114(p:Product):Double?{
    val raw=p.currentInclVat.ifBlank{p.saleInclVatDisplay.ifBlank{p.regularInclVatDisplay.ifBlank{p.price}}}
    val token=Regex("""\d{1,3}(?:\.\d{3})*(?:,\d{2})|\d+(?:[.,]\d{2})?""").find(raw)?.value?:return null
    return token.replace(".","").replace(",",".").toDoubleOrNull()
}
private fun moneyV114(value:Double):String=java.text.NumberFormat.getNumberInstance(java.util.Locale("ro","RO")).apply{minimumFractionDigits=2;maximumFractionDigits=2}.format(value)+" lei"
private data class TotalsV114(val subtotal:Double,val shipping:Double,val vat:Double,val total:Double,val remaining:Double,val progress:Float,val free:Boolean,val allPriced:Boolean)
private fun totalsV114(lines:List<CartLine>,cfg:ShippingConfig):TotalsV114{
    val priced=lines.all{unitRonV114(it.product)!=null}
    val subtotal=lines.sumOf{(unitRonV114(it.product)?:0.0)*it.quantity}
    val threshold=cfg.freeShippingMin.coerceAtLeast(0.0)
    val free=threshold>0.0&&subtotal>=threshold
    val shipping=if(free)0.0 else cfg.flatRateInclVat.coerceAtLeast(0.0)
    val total=subtotal+shipping
    val rate=cfg.taxRate.coerceAtLeast(0.0)
    val vat=if(rate>0)total*rate/(100.0+rate) else 0.0
    val remaining=if(threshold>0)max(0.0,threshold-subtotal) else 0.0
    val progress=if(threshold>0)(subtotal/threshold).coerceIn(0.0,1.0).toFloat() else 1f
    return TotalsV114(subtotal,shipping,vat,total,remaining,progress,free,priced)
}

@Composable
private fun HeaderActionsV114(commerce:CommerceStore,onFavorites:()->Unit,onNotifications:()->Unit,onCart:()->Unit,showCart:Boolean=true){
    IconButton(onClick=onFavorites){Icon(Icons.Default.FavoriteBorder,"Favorite",tint=C114Ink)}
    IconButton(onClick=onNotifications){BadgedBox(badge={Badge(containerColor=AutoIdOrange){Text("3")}}){Icon(Icons.Default.NotificationsNone,"Notificări",tint=C114Ink)}}
    if(showCart)IconButton(onClick=onCart){BadgedBox(badge={if(commerce.cartCount()>0)Badge(containerColor=AutoIdOrange){Text(commerce.cartCount().toString())}}){Icon(Icons.Default.ShoppingCart,"Coș",tint=C114Ink)}}
}

@Composable
private fun SectionV114(icon:androidx.compose.ui.graphics.vector.ImageVector,title:String,subtitle:String="",content:@Composable ColumnScope.()->Unit){
    ElevatedCard(shape=RoundedCornerShape(22.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)){
        Column(Modifier.fillMaxWidth().padding(16.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
            Row(verticalAlignment=Alignment.CenterVertically){Surface(shape=RoundedCornerShape(11.dp),color=C114OrangeSoft){Icon(icon,null,tint=AutoIdOrange,modifier=Modifier.padding(8.dp).size(18.dp))};Spacer(Modifier.width(10.dp));Column{Text(title,fontSize=16.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);if(subtitle.isNotBlank())Text(subtitle,fontSize=10.sp,color=C114Muted)}}
            content()
        }
    }
}

@Composable
private fun TotalRowsV114(t:TotalsV114,shippingTitle:String,compact:Boolean=false){
    @Composable fun row(label:String,value:String,bold:Boolean=false,muted:Boolean=false){Row(Modifier.fillMaxWidth().padding(vertical=if(compact)3.dp else 5.dp),verticalAlignment=Alignment.CenterVertically){Text(label,Modifier.weight(1f),fontSize=if(compact)11.sp else 13.sp,color=if(muted)C114Muted else C114Ink,fontWeight=if(bold)FontWeight.ExtraBold else FontWeight.Normal);Text(value,fontSize=if(compact)11.sp else if(bold)17.sp else 13.sp,fontWeight=if(bold)FontWeight.ExtraBold else FontWeight.SemiBold,color=if(bold)C114Ink else C114Ink)}}
    row("Subtotal",if(t.allPriced)moneyV114(t.subtotal) else "Calculat la checkout")
    row(if(t.free)"Livrare gratuită" else shippingTitle,if(t.free)"0,00 lei" else moneyV114(t.shipping)+(if(compact)"" else " (incl. TVA)"),muted=false)
    row("TVA",if(t.allPriced)moneyV114(t.vat) else "—")
    HorizontalDivider(color=C114Border,modifier=Modifier.padding(vertical=5.dp))
    row("Total (incl. TVA)",if(t.allPriced)moneyV114(t.total) else "Calculat la checkout",bold=true)
}

@Composable
fun CartV114(api:AutoIdApi,commerce:CommerceStore,onProduct:(Product)->Unit,onChanged:()->Unit,onCheckout:()->Unit,onFavorites:()->Unit,onNotifications:()->Unit){
    var cfg by remember{mutableStateOf(CheckoutConfig("RON","RO",emptyList()))}
    val lines=commerce.cart()
    val totals=totalsV114(lines,cfg.shipping)
    LaunchedEffect(Unit){runCatching{withContext(Dispatchers.IO){api.checkoutConfig()}}.onSuccess{cfg=it}}
    Column(Modifier.fillMaxSize().background(C114Soft).statusBarsPadding()){
        Row(Modifier.fillMaxWidth().background(Color.White).padding(start=16.dp,end=7.dp,top=7.dp,bottom=7.dp),verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text("Coșul tău",fontSize=23.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text("${commerce.cartCount()} bucăți",fontSize=10.sp,color=C114Muted)};HeaderActionsV114(commerce,onFavorites,onNotifications,{},showCart=false)}
        if(lines.isEmpty()){Box(Modifier.fillMaxSize(),contentAlignment=Alignment.Center){Column(horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(9.dp)){Surface(shape=CircleShape,color=C114OrangeSoft,modifier=Modifier.size(74.dp)){Box(contentAlignment=Alignment.Center){Icon(Icons.Default.ShoppingCart,null,tint=AutoIdOrange,modifier=Modifier.size(34.dp))}};Text("Coșul este gol",fontSize=22.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text("Adaugă produse din catalog pentru a continua.",color=C114Muted,fontSize=12.sp)}};return}
        LazyColumn(Modifier.weight(1f).fillMaxWidth().padding(horizontal=14.dp),verticalArrangement=Arrangement.spacedBy(10.dp),contentPadding=PaddingValues(top=12.dp,bottom=12.dp)){
            items(lines,key={it.product.id}){line->
                ElevatedCard(shape=RoundedCornerShape(19.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)){
                    Row(Modifier.fillMaxWidth().clickable{onProduct(line.product)}.padding(12.dp),verticalAlignment=Alignment.CenterVertically){
                        AsyncImage(line.product.imageUrl,line.product.name,Modifier.size(74.dp).clip(RoundedCornerShape(14.dp)).background(Color.White).padding(4.dp),contentScale=ContentScale.Fit);Spacer(Modifier.width(11.dp))
                        Column(Modifier.weight(1f)){Text(line.product.name,maxLines=2,overflow=TextOverflow.Ellipsis,fontWeight=FontWeight.Bold,color=C114Ink,fontSize=13.sp);if(line.product.sku.isNotBlank())Text("SKU ${line.product.sku}",fontSize=9.sp,color=C114Muted);Text(unitRonV114(line.product)?.let(::moneyV114)?:line.product.price,color=AutoIdOrange,fontWeight=FontWeight.ExtraBold,fontSize=14.sp);Row(verticalAlignment=Alignment.CenterVertically){Surface(shape=RoundedCornerShape(50),color=Color(0xFFF2F4F7)){Row(verticalAlignment=Alignment.CenterVertically){IconButton(onClick={commerce.changeQty(line.product.id,line.quantity-1);onChanged()},modifier=Modifier.size(36.dp)){Icon(Icons.Default.Remove,null,Modifier.size(15.dp))};Text(line.quantity.toString(),fontWeight=FontWeight.ExtraBold,fontSize=12.sp);IconButton(onClick={commerce.changeQty(line.product.id,line.quantity+1);onChanged()},modifier=Modifier.size(36.dp)){Icon(Icons.Default.Add,null,Modifier.size(15.dp))}}};Spacer(Modifier.weight(1f));IconButton(onClick={commerce.removeFromCart(line.product.id);onChanged()}){Icon(Icons.Default.DeleteOutline,"Șterge",tint=C114Muted)}}}
                    }
                }
            }
            item{
                ElevatedCard(shape=RoundedCornerShape(22.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)){
                    Column(Modifier.fillMaxWidth().padding(17.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){
                        Text("Costul tău",fontSize=19.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink)
                        if(cfg.shipping.freeShippingMin>0){Text(if(totals.free)"Ai livrare gratuită ✓" else "Mai adaugă ${moneyV114(totals.remaining)} pentru livrare gratuită",fontSize=11.sp,color=if(totals.free)C114Good else C114Muted,fontWeight=FontWeight.Bold);LinearProgressIndicator(progress={totals.progress},modifier=Modifier.fillMaxWidth().height(7.dp).clip(CircleShape),color=if(totals.free)C114Good else AutoIdOrange,trackColor=Color(0xFFF0F2F5))}
                        Spacer(Modifier.height(2.dp));TotalRowsV114(totals,cfg.shipping.title)
                    }
                }
            }
        }
        Surface(color=Color.White,shadowElevation=14.dp){Column(Modifier.fillMaxWidth().padding(14.dp).navigationBarsPadding()){Button(onClick=onCheckout,modifier=Modifier.fillMaxWidth().height(56.dp),shape=RoundedCornerShape(17.dp)){Text("Finalizare comandă",fontWeight=FontWeight.ExtraBold,fontSize=15.sp)}}}
    }
}

@Composable
private fun GoogleButtonV114(clientId:String,api:AutoIdApi,session:SessionStore,onSuccess:(LoginResult)->Unit,onError:(String)->Unit,modifier:Modifier=Modifier,label:String="Continuă cu Google"){
    val context=LocalContext.current
    val scope=rememberCoroutineScope()
    val manager=remember(context){CredentialManager.create(context)}
    var busy by remember{mutableStateOf(false)}
    OutlinedButton(onClick={
        if(clientId.isBlank()){onError("Configurează Google Web OAuth Client ID în WooCommerce → AutoID App Home.");return@OutlinedButton}
        busy=true
        scope.launch{
            try{
                val option=GetGoogleIdOption.Builder().setFilterByAuthorizedAccounts(false).setServerClientId(clientId).setAutoSelectEnabled(false).build()
                val request=GetCredentialRequest.Builder().addCredentialOption(option).build()
                val result=manager.getCredential(context=context,request=request)
                val credential=result.credential
                if(credential !is CustomCredential || credential.type!=GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL){onError("Google nu a returnat o identitate compatibilă.")}
                else{
                    val token=GoogleIdTokenCredential.createFrom(credential.data).idToken
                    val login=withContext(Dispatchers.IO){api.googleLogin(token)}
                    session.saveLogin(login);onSuccess(login)
                }
            }catch(e:GetCredentialException){val raw=e.message.orEmpty();onError(if(raw.contains("reauth",true))"Google solicită reautentificarea contului. Selectează din nou contul Google." else raw.ifBlank{"Autentificarea Google a fost anulată."})}
            catch(e:Throwable){onError(e.message?:"Autentificare Google eșuată.")}
            finally{busy=false}
        }
    },modifier=modifier.height(54.dp),enabled=!busy,shape=RoundedCornerShape(16.dp),border=BorderStroke(1.dp,C114Border),colors=ButtonDefaults.outlinedButtonColors(containerColor=Color.White,contentColor=C114Ink)){
        Surface(shape=CircleShape,color=Color.White,border=BorderStroke(1.dp,C114Border),modifier=Modifier.size(25.dp)){Box(contentAlignment=Alignment.Center){Text("G",color=Color(0xFF4285F4),fontWeight=FontWeight.ExtraBold,fontSize=14.sp)}}
        Spacer(Modifier.width(10.dp));Text(if(busy)"Se conectează..." else label,fontWeight=FontWeight.Bold)
    }
}

@Composable
private fun AddressFieldsV114(prefix:String,first:String,onFirst:(String)->Unit,last:String,onLast:(String)->Unit,company:String?=null,onCompany:((String)->Unit)?=null,address1:String,onAddress1:(String)->Unit,address2:String,onAddress2:(String)->Unit,city:String,onCity:(String)->Unit,state:String,onState:(String)->Unit,postcode:String,onPostcode:(String)->Unit,country:String,onCountry:(String)->Unit){
    Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){OutlinedTextField(first,onFirst,label={Text("Prenume *")},singleLine=true,modifier=Modifier.weight(1f),shape=RoundedCornerShape(13.dp));OutlinedTextField(last,onLast,label={Text("Nume *")},singleLine=true,modifier=Modifier.weight(1f),shape=RoundedCornerShape(13.dp))}
    if(company!=null&&onCompany!=null)OutlinedTextField(company,onCompany,label={Text("Companie")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(13.dp))
    OutlinedTextField(address1,onAddress1,label={Text("Stradă, nr. *")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(13.dp))
    OutlinedTextField(address2,onAddress2,label={Text("Apartament / clădire (opțional)")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(13.dp))
    Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){OutlinedTextField(city,onCity,label={Text("Localitate *")},singleLine=true,modifier=Modifier.weight(1.2f),shape=RoundedCornerShape(13.dp));OutlinedTextField(postcode,onPostcode,label={Text("Cod poștal *")},singleLine=true,modifier=Modifier.weight(.8f),shape=RoundedCornerShape(13.dp))}
    Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){OutlinedTextField(state,onState,label={Text("Județ")},singleLine=true,modifier=Modifier.weight(1f),shape=RoundedCornerShape(13.dp));OutlinedTextField(country,onCountry,label={Text("Țară")},singleLine=true,modifier=Modifier.weight(1f),shape=RoundedCornerShape(13.dp))}
}

@Composable
private fun StripeChoiceV124(id:String,label:String,selected:String,onSelect:(String)->Unit,modifier:Modifier=Modifier){
    val active=id==selected
    Surface(modifier=modifier.clickable{onSelect(id)},shape=RoundedCornerShape(10.dp),color=if(active)C114OrangeSoft else Color.White,border=BorderStroke(if(active)2.dp else 1.dp,if(active)AutoIdOrange else C114Border)){Row(Modifier.fillMaxWidth().padding(horizontal=10.dp,vertical=11.dp),verticalAlignment=Alignment.CenterVertically){RadioButton(active,{onSelect(id)});Spacer(Modifier.width(3.dp));Text(label,fontSize=11.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink)}}
}

@Composable
private fun StripeLaunchersV124(publishableKey:String,pending:CheckoutResult?,payRequest:Int,paymentChoice:String,cardWidget:CardInputWidget?,billingDetails:StripePaymentMethod.BillingDetails,authToken:String?,api:AutoIdApi,onGooglePayReady:(Boolean)->Unit,onBusy:(Boolean)->Unit,onMessage:(String)->Unit,onPaid:(CheckoutResult)->Unit){
    val scope=rememberCoroutineScope();val pendingNow=rememberUpdatedState(pending);val tokenNow=rememberUpdatedState(authToken)
    fun confirmServer(){val p=pendingNow.value?:return;onBusy(true);scope.launch{runCatching{withContext(Dispatchers.IO){api.confirmStripePayment(p.orderId,p.stripePaymentIntentId,p.stripePaymentToken,tokenNow.value)}}.onSuccess{paid->if(paid){onMessage("Plată confirmată. Comanda a fost înregistrată.");onPaid(p)}else onMessage("Stripe a procesat plata, dar serverul nu a confirmat încă încasarea.")}.onFailure{onMessage(it.message?:"Nu am putut confirma plata pe server.")};onBusy(false)}}
    val paymentLauncher=rememberPaymentLauncher(publishableKey=publishableKey){result->when(result){PaymentResult.Completed->confirmServer();PaymentResult.Canceled->onMessage("Plata a fost anulată. Comanda rămâne în așteptare și poți reîncerca plata.");is PaymentResult.Failed->onMessage(result.throwable.localizedMessage?:"Plata Stripe nu a putut fi finalizată.")}}
    val googlePayLauncher=rememberGooglePayLauncher(config=GooglePayLauncher.Config(environment=GooglePayEnvironment.Test,merchantCountryCode="RO",merchantName="AutoID Professional Solutions",isEmailRequired=false,existingPaymentMethodRequired=false),readyCallback={onGooglePayReady(it)},resultCallback={result->when(result){GooglePayLauncher.Result.Completed->confirmServer();GooglePayLauncher.Result.Canceled->onMessage("Plata Google Pay a fost anulată. Poți reîncerca fără să recreăm comanda.");is GooglePayLauncher.Result.Failed->onMessage(result.error.localizedMessage?:"Google Pay nu a putut finaliza plata.")}})
    LaunchedEffect(payRequest){if(payRequest<=0)return@LaunchedEffect;val p=pending?:return@LaunchedEffect;if(paymentChoice=="google_pay"){googlePayLauncher.presentForPaymentIntent(p.stripeClientSecret,"AutoID")}else{val card=cardWidget?.paymentMethodCard;if(card==null){onMessage("Completează corect datele cardului.");return@LaunchedEffect};val params=PaymentMethodCreateParams.create(card,billingDetails);paymentLauncher.confirm(ConfirmPaymentIntentParams.createWithPaymentMethodCreateParams(params,p.stripeClientSecret))}}
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CheckoutV114(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onBack:()->Unit,onDone:()->Unit){
    val lines=commerce.cart();var cfg by remember{mutableStateOf(CheckoutConfig("RON","RO",emptyList()))};var summaryOpen by remember{mutableStateOf(false)}
    var authMode by remember{mutableStateOf(if(session.accessToken!=null)"authenticated" else "login")};var authToken by remember{mutableStateOf(session.accessToken)};var login by remember{mutableStateOf(session.customerEmail)};var pass by remember{mutableStateOf("")};var authBusy by remember{mutableStateOf(false)}
    var email by remember{mutableStateOf(session.customerEmail)};var phone by remember{mutableStateOf("")}
    var sf by remember{mutableStateOf("")};var sl by remember{mutableStateOf("")};var sa1 by remember{mutableStateOf("")};var sa2 by remember{mutableStateOf("")};var scity by remember{mutableStateOf("")};var sstate by remember{mutableStateOf("")};var spost by remember{mutableStateOf("")};var scountry by remember{mutableStateOf("RO")}
    var sameBilling by remember{mutableStateOf(true)};var bf by remember{mutableStateOf("")};var bl by remember{mutableStateOf("")};var company by remember{mutableStateOf("")};var ba1 by remember{mutableStateOf("")};var ba2 by remember{mutableStateOf("")};var bcity by remember{mutableStateOf("")};var bstate by remember{mutableStateOf("")};var bpost by remember{mutableStateOf("")};var bcountry by remember{mutableStateOf("RO")};var vat by remember{mutableStateOf("")}
    var deliveryMode by remember{mutableStateOf("delivery")};var contactEdit by remember{mutableStateOf(false)};var addressEdit by remember{mutableStateOf(false)}
    var payment by remember{mutableStateOf("cod")};var note by remember{mutableStateOf("")};var createAccount by remember{mutableStateOf(true)};var reviewConsent by remember{mutableStateOf(true)};var terms by remember{mutableStateOf(false)};var busy by remember{mutableStateOf(false)};var stripeConfirmBusy by remember{mutableStateOf(false)};var message by remember{mutableStateOf("")};var success by remember{mutableStateOf<CheckoutResult?>(null)}
    var stripePending by remember{mutableStateOf<CheckoutResult?>(null)};var stripePaymentChoice by remember{mutableStateOf("card")};var stripePayRequest by remember{mutableIntStateOf(0)};var stripeCardWidget by remember{mutableStateOf<CardInputWidget?>(null)};var stripeCardValid by remember{mutableStateOf(false)};var googlePayReady by remember{mutableStateOf(false)}
    val checkoutScope=rememberCoroutineScope();val checkoutContext=LocalContext.current
    val methods=cfg.payments.ifEmpty{listOf(PaymentMethod("cod","Numerar la livrare (COD)","Plată la livrare."),PaymentMethod("bacs","Transfer bancar","Plată prin ordin de plată."))}
    val checkoutShipping=if(deliveryMode=="pickup")cfg.shipping.copy(flatRateInclVat=0.0,freeShippingMin=0.0,title="Ridicare din Depozit") else cfg.shipping
    val totals=totalsV114(lines,checkoutShipping)
    val useShippingForBilling=sameBilling&&deliveryMode=="delivery"
    val billingFirst=if(useShippingForBilling)sf else bf;val billingLast=if(useShippingForBilling)sl else bl;val billingA1=if(useShippingForBilling)sa1 else ba1;val billingA2=if(useShippingForBilling)sa2 else ba2;val billingCity=if(useShippingForBilling)scity else bcity;val billingState=if(useShippingForBilling)sstate else bstate;val billingPost=if(useShippingForBilling)spost else bpost;val billingCountry=if(useShippingForBilling)scountry else bcountry
    val authReady=authMode=="guest"||authMode=="authenticated"
    val shippingOk=deliveryMode=="pickup"||(sf.isNotBlank()&&sl.isNotBlank()&&sa1.isNotBlank()&&scity.isNotBlank()&&spost.isNotBlank())
    val billingOk=billingFirst.isNotBlank()&&billingLast.isNotBlank()&&billingA1.isNotBlank()&&billingCity.isNotBlank()&&billingPost.isNotBlank()
    val valid=authReady&&email.contains("@")&&phone.isNotBlank()&&shippingOk&&billingOk&&terms&&lines.isNotEmpty()
    val stripeBilling=StripePaymentMethod.BillingDetails(address=Address.Builder().setLine1(billingA1).setLine2(billingA2.ifBlank{null}).setCity(billingCity).setState(billingState.ifBlank{null}).setPostalCode(billingPost).setCountry(billingCountry.ifBlank{"RO"}).build(),email=email.ifBlank{null},name=listOf(billingFirst,billingLast).filter{it.isNotBlank()}.joinToString(" ").ifBlank{null},phone=phone.ifBlank{null})
    if(cfg.stripeMode=="test"&&cfg.stripePublishableKey.startsWith("pk_test_")){
        StripeLaunchersV124(
            publishableKey=cfg.stripePublishableKey,pending=stripePending,payRequest=stripePayRequest,paymentChoice=stripePaymentChoice,cardWidget=stripeCardWidget,billingDetails=stripeBilling,authToken=authToken,api=api,
            onGooglePayReady={googlePayReady=it},onBusy={stripeConfirmBusy=it},onMessage={message=it},onPaid={pending->success=pending;stripePending=null}
        )
    }else googlePayReady=false
    LaunchedEffect(Unit){runCatching{withContext(Dispatchers.IO){api.checkoutConfig()}}.onSuccess{loaded->if(loaded.stripeMode=="test"&&loaded.stripePublishableKey.startsWith("pk_test_"))PaymentConfiguration.init(checkoutContext,loaded.stripePublishableKey);cfg=loaded;scountry=loaded.country.ifBlank{"RO"};bcountry=scountry;payment=loaded.payments.firstOrNull{p->p.enabled}?.id?:"cod"}.onFailure{message=it.message?:"Nu am putut încărca setările checkout."}}
    LaunchedEffect(busy){if(busy){runCatching{withContext(Dispatchers.IO){api.createOrderV114(lines,email,phone,sf,sl,sa1,sa2,scity,sstate,spost,scountry,billingFirst,billingLast,company,billingA1,billingA2,billingCity,billingState,billingPost,billingCountry,vat,note,payment,reviewConsent,createAccount&&authToken==null,deliveryMode,authToken)}}.onSuccess{r->if(!r.accessToken.isNullOrBlank()){session.saveLogin(LoginResult(r.accessToken,customer=r.customer));authToken=r.accessToken;authMode="authenticated"};if(r.requiresPayment&&r.paymentMethod=="stripe"){if(r.stripeMode!="test"||!r.stripePublishableKey.startsWith("pk_test_")||r.stripeClientSecret.isBlank()||r.stripePaymentIntentId.isBlank()||r.stripePaymentToken.isBlank()){message="Stripe Sandbox nu este configurat corect pe server."}else{stripePending=r;stripePayRequest+=1;message=if(stripePaymentChoice=="google_pay")"Deschid Google Pay…" else "Procesez plata securizată cu cardul…"}}else{success=r;message="Comandă plasată cu succes."}}.onFailure{message=it.message?:"Comanda nu a putut fi plasată."};busy=false}}
    LaunchedEffect(authBusy){if(authBusy){runCatching{withContext(Dispatchers.IO){api.login(login,pass)}}.onSuccess{session.saveLogin(it);authToken=it.accessToken;authMode="authenticated";email=it.customer?.email.orEmpty().ifBlank{login};message="Autentificare reușită."}.onFailure{message=it.message?:"Autentificare eșuată."};authBusy=false}}
    LaunchedEffect(authToken,authMode){val t=authToken;if(t!=null&&authMode=="authenticated"){runCatching{withContext(Dispatchers.IO){api.accountAddresses(t)}}.onSuccess{a->val sh=if(a.shipping.address1.isNotBlank())a.shipping else a.billing;email=a.billing.email.ifBlank{email};phone=a.billing.phone.ifBlank{phone};sf=sh.firstName;sl=sh.lastName;sa1=sh.address1;sa2=sh.address2;scity=sh.city;sstate=sh.state;spost=sh.postcode;scountry=sh.country.ifBlank{"RO"};bf=a.billing.firstName;bl=a.billing.lastName;company=a.billing.company;ba1=a.billing.address1;ba2=a.billing.address2;bcity=a.billing.city;bstate=a.billing.state;bpost=a.billing.postcode;bcountry=a.billing.country.ifBlank{"RO"};vat=a.vatNumber;contactEdit=false;addressEdit=false}}}
    if(success!=null){val r=success!!;Box(Modifier.fillMaxSize().background(C114Soft).statusBarsPadding(),contentAlignment=Alignment.Center){ElevatedCard(Modifier.padding(20.dp),shape=RoundedCornerShape(28.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Column(Modifier.padding(24.dp),horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(10.dp)){Surface(shape=CircleShape,color=C114GoodSoft,modifier=Modifier.size(76.dp)){Box(contentAlignment=Alignment.Center){Icon(Icons.Default.CheckCircle,null,tint=C114Good,modifier=Modifier.size(42.dp))}};Text("Comandă confirmată",fontSize=24.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text("Comanda #${r.number} a fost creată.",color=C114Muted);if(r.total.isNotBlank())Text(r.total+" "+r.currency,fontSize=20.sp,fontWeight=FontWeight.ExtraBold,color=AutoIdOrange);Button(onClick=onDone,modifier=Modifier.fillMaxWidth().height(54.dp),shape=RoundedCornerShape(16.dp)){Text("Vezi contul meu")}}}};return}
    Scaffold(containerColor=C114Soft,topBar={TopAppBar(title={Column{Text("Finalizare comandă",fontWeight=FontWeight.ExtraBold);Text("Checkout AutoID securizat",fontSize=10.sp,color=C114Muted)}},navigationIcon={IconButton(onClick=onBack){Icon(Icons.Default.ArrowBack,"Înapoi")}},colors=TopAppBarDefaults.topAppBarColors(containerColor=Color.White))},bottomBar={Surface(color=Color.White,shadowElevation=14.dp){Column(Modifier.fillMaxWidth().padding(horizontal=14.dp,vertical=11.dp).navigationBarsPadding()){Row(verticalAlignment=Alignment.CenterVertically){Text("Total (incl. TVA)",fontSize=11.sp,color=C114Muted);Spacer(Modifier.weight(1f));Text(if(totals.allPriced)moneyV114(totals.total) else "Calculat la checkout",fontWeight=FontWeight.ExtraBold,fontSize=18.sp,color=C114Ink)};Spacer(Modifier.height(7.dp));Button(onClick={if(payment=="stripe"){if(stripePaymentChoice=="card"&&stripeCardWidget?.paymentMethodCard==null){message="Completează corect numărul cardului, data expirării și CVC."}else if(stripePaymentChoice=="google_pay"&&!googlePayReady){message="Google Pay nu este disponibil pe acest dispozitiv."}else if(stripePending!=null){stripePayRequest+=1}else busy=true}else busy=true},enabled=valid&&!busy&&!stripeConfirmBusy&&methods.firstOrNull{it.id==payment}?.enabled!=false&&(payment!="stripe"||stripePaymentChoice!="google_pay"||googlePayReady),modifier=Modifier.fillMaxWidth().height(56.dp),shape=RoundedCornerShape(10.dp)){if(busy||stripeConfirmBusy){CircularProgressIndicator(Modifier.size(20.dp),strokeWidth=2.dp,color=Color.White);Spacer(Modifier.width(8.dp));Text(if(stripeConfirmBusy)"Confirm plata..." else "Se procesează...")}else Text(if(payment=="stripe"&&stripePaymentChoice=="google_pay")"Plătește cu Google Pay" else if(payment=="stripe")"Plătește cu cardul" else "Plasează comanda",fontWeight=FontWeight.ExtraBold)}}}}){pad->
        LazyColumn(Modifier.padding(pad).fillMaxSize().padding(horizontal=14.dp),verticalArrangement=Arrangement.spacedBy(12.dp),contentPadding=PaddingValues(top=12.dp,bottom=18.dp)){
            item{
                ElevatedCard(
                    modifier=Modifier.fillMaxWidth(),
                    shape=RoundedCornerShape(18.dp),
                    colors=CardDefaults.elevatedCardColors(containerColor=Color.White),
                    elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)
                ){
                    Column(Modifier.fillMaxWidth().padding(horizontal=16.dp,vertical=12.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
                        if(authMode=="authenticated"){
                            Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
                                Surface(shape=CircleShape,color=C114GoodSoft,modifier=Modifier.size(34.dp)){Box(contentAlignment=Alignment.Center){Icon(Icons.Default.VerifiedUser,null,tint=C114Good,modifier=Modifier.size(18.dp))}}
                                Spacer(Modifier.width(10.dp))
                                Column(Modifier.weight(1f)){Text("Cont AutoID conectat",fontSize=12.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(session.customerEmail.ifBlank{email},fontSize=10.sp,color=C114Muted)}
                                TextButton(onClick={session.clear();authToken=null;authMode="guest";message=""}){Text("Schimbă",fontWeight=FontWeight.Bold)}
                            }
                        }else{
                            Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
                                Text("Ai cont AutoID?",fontSize=12.sp,fontWeight=FontWeight.SemiBold,color=C114Ink,modifier=Modifier.weight(1f))
                                TextButton(onClick={authMode=if(authMode=="login")"guest" else "login";message=""}){Text(if(authMode=="login")"Închide" else "Autentificare",fontWeight=FontWeight.ExtraBold,color=AutoIdOrange)}
                            }
                            AnimatedVisibility(visible=authMode=="login"){
                                Column(verticalArrangement=Arrangement.spacedBy(10.dp)){
                                    HorizontalDivider(color=C114Border)
                                    OutlinedTextField(login,{login=it},label={Text("User / Email")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(13.dp))
                                    OutlinedTextField(pass,{pass=it},label={Text("Parolă")},singleLine=true,visualTransformation=PasswordVisualTransformation(),modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(13.dp))
                                    val uriHandler=LocalUriHandler.current
                                    Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
                                        TextButton(onClick={uriHandler.openUri("https://www.autoid.ro/contul-meu/lost-password/")},contentPadding=PaddingValues(0.dp)){Text("Ai uitat parola?",fontSize=11.sp,fontWeight=FontWeight.SemiBold,color=C114Muted)}
                                        Spacer(Modifier.weight(1f))
                                    }
                                    Button(onClick={authBusy=true},enabled=!authBusy&&login.isNotBlank()&&pass.isNotBlank(),modifier=Modifier.fillMaxWidth().height(50.dp),shape=RoundedCornerShape(13.dp)){Text(if(authBusy)"Se conectează..." else "Autentificare",fontWeight=FontWeight.ExtraBold)}
                                    GoogleButtonV114(clientId=cfg.googleClientId,api=api,session=session,onSuccess={r->authToken=r.accessToken;authMode="authenticated";email=r.customer?.email.orEmpty().ifBlank{email};message="Autentificare Google reușită."},onError={message=it},modifier=Modifier.fillMaxWidth())
                                }
                            }
                        }
                    }
                }
            }
            item{ElevatedCard(Modifier.fillMaxWidth().clickable{summaryOpen=!summaryOpen},shape=RoundedCornerShape(22.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)){Column(Modifier.fillMaxWidth().padding(16.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){Row(verticalAlignment=Alignment.CenterVertically){Text("Comanda ta",fontSize=17.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Spacer(Modifier.weight(1f));Text("${commerce.cartCount()} buc.",fontSize=11.sp,fontWeight=FontWeight.Bold,color=C114Muted);Spacer(Modifier.width(5.dp));Icon(if(summaryOpen)Icons.Default.ExpandLess else Icons.Default.ChevronRight,null,tint=C114Muted)};AnimatedVisibility(summaryOpen){Column(verticalArrangement=Arrangement.spacedBy(8.dp)){HorizontalDivider(color=C114Border);lines.forEach{line->Row(verticalAlignment=Alignment.CenterVertically){AsyncImage(line.product.imageUrl,line.product.name,Modifier.size(42.dp).clip(RoundedCornerShape(9.dp)).background(Color.White).padding(3.dp),contentScale=ContentScale.Fit);Spacer(Modifier.width(8.dp));Text("${line.quantity} × ${line.product.name}",Modifier.weight(1f),fontSize=10.sp,maxLines=1,overflow=TextOverflow.Ellipsis,color=C114Ink);unitRonV114(line.product)?.let{Text(moneyV114(it*line.quantity),fontSize=10.sp,fontWeight=FontWeight.Bold)}}};HorizontalDivider(color=C114Border);TotalRowsV114(totals,checkoutShipping.title,compact=true)}}}
            }}
            item{SectionV114(Icons.Default.AlternateEmail,"Informații de contact","Pentru confirmare și actualizările comenzii."){
                if(authMode=="authenticated"&&!contactEdit){Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text(email,fontWeight=FontWeight.Bold,color=C114Ink);Text(phone,fontSize=10.sp,color=C114Muted)};TextButton(onClick={contactEdit=true}){Text("Editează",fontWeight=FontWeight.ExtraBold,color=AutoIdOrange)}}}
                else{OutlinedTextField(email,{email=it},label={Text("Email *")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(13.dp));OutlinedTextField(phone,{phone=it},label={Text("Telefon *")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(13.dp));if(authMode=="authenticated")TextButton(onClick={contactEdit=false},modifier=Modifier.align(Alignment.End)){Text("Gata")}}
            }}
            item{SectionV114(Icons.Default.LocalShipping,"Livrare și Facturare",if(deliveryMode=="pickup")"Facturare pentru ridicare" else "Adresele comenzii"){
                if(authMode=="authenticated"&&!addressEdit){Column(verticalArrangement=Arrangement.spacedBy(6.dp)){if(deliveryMode=="delivery"){Text("Livrare",fontSize=9.sp,fontWeight=FontWeight.ExtraBold,color=C114Muted);Text(listOf(sf+" "+sl,sa1,scity+" "+spost).filter{it.isNotBlank()}.joinToString(", "),fontSize=11.sp,color=C114Ink)};Text("Facturare",fontSize=9.sp,fontWeight=FontWeight.ExtraBold,color=C114Muted);Text(listOf(billingFirst+" "+billingLast,billingA1,billingCity+" "+billingPost).filter{it.isNotBlank()}.joinToString(", "),fontSize=11.sp,color=C114Ink);if(company.isNotBlank())Text(company,fontWeight=FontWeight.Bold,color=C114Ink);if(vat.isNotBlank())Text("Cod TVA: $vat",fontSize=10.sp,color=C114Muted);TextButton(onClick={addressEdit=true},modifier=Modifier.align(Alignment.End)){Text("Editează",fontWeight=FontWeight.ExtraBold,color=AutoIdOrange)}}}else{if(deliveryMode=="delivery"){Text("Adresa de livrare",fontWeight=FontWeight.Bold,color=C114Ink);AddressFieldsV114("shipping",sf,{sf=it},sl,{sl=it},address1=sa1,onAddress1={sa1=it},address2=sa2,onAddress2={sa2=it},city=scity,onCity={scity=it},state=sstate,onState={sstate=it},postcode=spost,onPostcode={spost=it},country=scountry,onCountry={scountry=it});Surface(shape=RoundedCornerShape(15.dp),color=Color(0xFFF8F9FB)){Row(Modifier.fillMaxWidth().clickable{sameBilling=!sameBilling}.padding(horizontal=10.dp,vertical=7.dp),verticalAlignment=Alignment.CenterVertically){Checkbox(sameBilling,{sameBilling=it});Text("Folosește aceeași adresă pentru facturare",fontSize=11.sp,fontWeight=FontWeight.Bold,color=C114Ink)}}};if(deliveryMode=="pickup"||!sameBilling){Text("Adresa de facturare",fontWeight=FontWeight.Bold,color=C114Ink);AddressFieldsV114("billing",bf,{bf=it},bl,{bl=it},address1=ba1,onAddress1={ba1=it},address2=ba2,onAddress2={ba2=it},city=bcity,onCity={bcity=it},state=bstate,onState={bstate=it},postcode=bpost,onPostcode={bpost=it},country=bcountry,onCountry={bcountry=it})};OutlinedTextField(company,{company=it},label={Text("Companie (opțional)")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(13.dp));OutlinedTextField(vat,{vat=it},label={Text("Cod TVA / CUI (opțional)")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(13.dp));if(authMode=="authenticated")TextButton(onClick={addressEdit=false},modifier=Modifier.align(Alignment.End)){Text("Gata")}}
            }}
            item {
                SectionV114(Icons.Default.LocalShipping, "Livrare", "Alege cum primești comanda") {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(9.dp)
                    ) {
                        listOf("delivery" to "Livrare", "pickup" to "Ridicare din Depozit").forEach { option ->
                            val id = option.first
                            val label = option.second
                            val selected = deliveryMode == id
                            OutlinedCard(
                                modifier = Modifier.weight(1f).clickable {
                                    if (id == "pickup" && deliveryMode != "pickup") {
                                        if (bf.isBlank()) {
                                            bf = sf
                                            bl = sl
                                            ba1 = sa1
                                            ba2 = sa2
                                            bcity = scity
                                            bstate = sstate
                                            bpost = spost
                                            bcountry = scountry
                                        }
                                        sameBilling = false
                                    }
                                    deliveryMode = id
                                },
                                shape = RoundedCornerShape(16.dp),
                                colors = CardDefaults.outlinedCardColors(containerColor = if (selected) C114OrangeSoft else Color.White),
                                border = BorderStroke(if (selected) 2.dp else 1.dp, if (selected) AutoIdOrange else C114Border)
                            ) {
                                Column(
                                    modifier = Modifier.fillMaxWidth().padding(12.dp),
                                    horizontalAlignment = Alignment.CenterHorizontally
                                ) {
                                    Icon(
                                        if (id == "delivery") Icons.Default.LocalShipping else Icons.Default.Storefront,
                                        contentDescription = null,
                                        tint = if (selected) AutoIdOrange else C114Muted
                                    )
                                    Spacer(Modifier.height(5.dp))
                                    Text(label, fontSize = 10.sp, fontWeight = FontWeight.ExtraBold, color = C114Ink, textAlign = TextAlign.Center)
                                }
                            }
                        }
                    }
                    if (deliveryMode == "pickup") {
                        Text(
                            "Ridicarea din depozit este gratuită. Primești confirmare când comanda este pregătită.",
                            fontSize = 10.sp,
                            color = C114Muted
                        )
                    }
                }
            }
            item{SectionV114(Icons.Default.CreditCard,"Metoda de plată"){methods.forEach{m->val selected=payment==m.id;OutlinedCard(Modifier.fillMaxWidth().clickable(enabled=m.enabled){payment=m.id},shape=RoundedCornerShape(10.dp),colors=CardDefaults.outlinedCardColors(containerColor=if(selected)C114OrangeSoft else Color.White),border=BorderStroke(if(selected)2.dp else 1.dp,if(selected)AutoIdOrange else C114Border)){Row(Modifier.fillMaxWidth().padding(13.dp),verticalAlignment=Alignment.CenterVertically){Icon(when(m.id.lowercase()){ "cod"->Icons.Default.LocalShipping;"bacs"->Icons.Default.AccountBalance;else->Icons.Default.CreditCard},null,tint=if(selected)AutoIdOrange else C114Muted);Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)){Text(m.title,fontWeight=FontWeight.Bold,color=C114Ink);Text(m.description,fontSize=9.sp,color=C114Muted)};RadioButton(selected,{if(m.enabled)payment=m.id},enabled=m.enabled)}}};if(payment=="stripe"){Column(verticalArrangement=Arrangement.spacedBy(10.dp)){Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){StripeChoiceV124("card","Card",stripePaymentChoice,{stripePaymentChoice=it},Modifier.weight(1f));StripeChoiceV124("google_pay","Google Pay",stripePaymentChoice,{stripePaymentChoice=it},Modifier.weight(1f))};if(stripePaymentChoice=="card"){Surface(shape=RoundedCornerShape(10.dp),color=Color.White,border=BorderStroke(1.dp,C114Border)){Column(Modifier.fillMaxWidth().padding(12.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){Text("Date card",fontSize=12.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text("Introdu doar datele cardului. Numele și adresa sunt preluate din checkout-ul AutoID.",fontSize=9.sp,color=C114Muted);AndroidView(factory={ctx->val themed=ContextThemeWrapper(ctx,R.style.Theme_AutoIDStripeCard);CardInputWidget(themed).apply{postalCodeEnabled=false;postalCodeRequired=false;setCardValidCallback{validCard,_->stripeCardValid=validCard};stripeCardWidget=this}},update={stripeCardWidget=it},modifier=Modifier.fillMaxWidth().heightIn(min=58.dp))}};if(!stripeCardValid)Text("Număr card · expirare · CVC",fontSize=9.sp,color=C114Muted)}else{Surface(shape=RoundedCornerShape(10.dp),color=Color.White,border=BorderStroke(1.dp,C114Border)){Column(Modifier.fillMaxWidth().padding(12.dp),verticalArrangement=Arrangement.spacedBy(5.dp)){Text("Google Pay",fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(if(googlePayReady)"Disponibil pe acest dispozitiv · plata se deschide securizat în Google Pay." else "Google Pay este activat, dar acest dispozitiv/cont nu este momentan ready pentru plată.",fontSize=9.sp,color=if(googlePayReady)Color(0xFF16794B) else C114Muted);Text("Nu solicităm din nou adresa sau datele de contact.",fontSize=9.sp,color=C114Muted)}}}}}}}
            item{SectionV114(Icons.Default.EditNote,"Observații","Opțional"){OutlinedTextField(note,{note=it},label={Text("Instrucțiuni pentru comandă")},minLines=2,maxLines=4,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(13.dp))}}
            item{ElevatedCard(shape=RoundedCornerShape(16.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)){Column{if(authMode!="authenticated"){Row(Modifier.fillMaxWidth().clickable{createAccount=!createAccount}.padding(horizontal=14.dp,vertical=10.dp),verticalAlignment=Alignment.CenterVertically){Checkbox(createAccount,{createAccount=it});Spacer(Modifier.width(5.dp));Column(Modifier.weight(1f)){Text("Creează un cont AutoID",fontSize=11.sp,fontWeight=FontWeight.Bold,color=C114Ink);Text("Salvăm datele comenzii și îți trimitem accesul la cont.",fontSize=9.sp,color=C114Muted)}};HorizontalDivider(color=C114Border)};Row(Modifier.fillMaxWidth().clickable{reviewConsent=!reviewConsent}.padding(horizontal=14.dp,vertical=10.dp),verticalAlignment=Alignment.CenterVertically){Checkbox(reviewConsent,{reviewConsent=it});Spacer(Modifier.width(5.dp));Column(Modifier.weight(1f)){Text("Permite solicitarea unei recenzii",fontSize=11.sp,fontWeight=FontWeight.Bold,color=C114Ink);Text("Putem trimite o invitație de review după livrarea comenzii.",fontSize=9.sp,color=C114Muted)}};HorizontalDivider(color=C114Border);Row(Modifier.fillMaxWidth().clickable{terms=!terms}.padding(horizontal=14.dp,vertical=10.dp),verticalAlignment=Alignment.CenterVertically){Checkbox(terms,{terms=it});Spacer(Modifier.width(5.dp));Text("Accept termenii și condițiile.",fontSize=11.sp,color=C114Ink,modifier=Modifier.weight(1f))}}}}
            if(message.isNotBlank())item{Surface(color=if(message.contains("reușită"))C114GoodSoft else Color(0xFFFFF1F0),shape=RoundedCornerShape(13.dp),modifier=Modifier.fillMaxWidth()){Row(Modifier.padding(12.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.Info,null,tint=if(message.contains("reușită"))C114Good else MaterialTheme.colorScheme.error,modifier=Modifier.size(18.dp));Spacer(Modifier.width(7.dp));Text(message,color=if(message.contains("reușită"))C114Good else MaterialTheme.colorScheme.error,fontSize=11.sp)}}}
        }
    }
}

@Composable
private fun LatestOrderCardV119(o: Order, onTrack: () -> Unit, onView: () -> Unit) {
    val terminal = orderIsTerminalV121(o.statusCode)
    val visualStatus = orderDisplayStatusV121(o.statusCode, o.trackingNumber, o.status)
    ElevatedCard(
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.elevatedCardColors(containerColor = Color.White),
        elevation = CardDefaults.elevatedCardElevation(defaultElevation = 1.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text("ULTIMA COMANDĂ", fontSize = 9.sp, fontWeight = FontWeight.ExtraBold, color = C114Muted)
            Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("Comanda: #${o.number}", fontWeight = FontWeight.ExtraBold, color = C114Ink)
                    Text(o.dateCreated, fontSize = 9.sp, color = C114Muted)
                    Text(
                        visualStatus,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.ExtraBold,
                        color = if (terminal) MaterialTheme.colorScheme.error else C114Good
                    )
                }
                OutlinedButton(onClick = onTrack, enabled = o.trackingUrl.isNotBlank()) {
                    Text("Urmărește", fontSize = 9.sp, fontWeight = FontWeight.Bold)
                }
                Spacer(Modifier.width(5.dp))
                Button(onClick = onView) {
                    Text("Vezi comanda", fontSize = 9.sp, fontWeight = FontWeight.Bold)
                }
            }
            Text("Total: ${o.total}", fontSize = 14.sp, fontWeight = FontWeight.ExtraBold, color = C114Ink)
            Text("incl. TVA", fontSize = 9.sp, color = C114Muted)
            if (terminal) {
                Surface(shape = RoundedCornerShape(12.dp), color = Color(0xFFFFF1F0)) {
                    Text(
                        visualStatus,
                        modifier = Modifier.fillMaxWidth().padding(10.dp),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.error
                    )
                }
            } else {
                OrderStatusProgressV121(o.statusCode, o.trackingNumber)
                if (o.trackingNumber.isNotBlank()) {
                    val carrierLabel = if (o.carrier.isBlank()) "GLS" else o.carrier
                    Text("$carrierLabel · AWB ${o.trackingNumber}", fontSize = 9.sp, color = C114Muted)
                }
            }
        }
    }
}

@Composable
fun AccountV114(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onCart:()->Unit,onFavorites:()->Unit,onNotifications:()->Unit){
    var token by remember{mutableStateOf(session.accessToken)};var cfg by remember{mutableStateOf(CheckoutConfig("RON","RO",emptyList()))};var mode by remember{mutableStateOf("login")};var email by remember{mutableStateOf(session.customerEmail)};var pass by remember{mutableStateOf("")};var first by remember{mutableStateOf("")};var last by remember{mutableStateOf("")};var company by remember{mutableStateOf("")};var vat by remember{mutableStateOf("")};var msg by remember{mutableStateOf("")};var busy by remember{mutableStateOf(false)};var orders by remember{mutableStateOf<List<Order>>(emptyList())}
    var profile by remember{mutableStateOf(AccountProfile())};var profileEdit by remember{mutableStateOf(AccountProfile())};var addresses by remember{mutableStateOf(AccountAddresses())};var addressesEdit by remember{mutableStateOf(AccountAddresses())};var detailsEditing by remember{mutableStateOf(false)};var addressesEditing by remember{mutableStateOf(false)};var accountBusy by remember{mutableStateOf(false)};var newPassword by remember{mutableStateOf("")}
    val privacyContext=LocalContext.current;val privacyStore=remember{PrivacyConsentStoreV128(privacyContext)};var privacyPrefs by remember{mutableStateOf(privacyStore.get())};var privacyBusy by remember{mutableStateOf(false)}
    var panel by remember{mutableStateOf("dashboard")};var selectedOrderId by remember{mutableStateOf<Long?>(null)};val accountScope=rememberCoroutineScope();val uriHandler=LocalUriHandler.current
    LaunchedEffect(Unit){runCatching{withContext(Dispatchers.IO){api.checkoutConfig()}}.onSuccess{cfg=it}}
    LaunchedEffect(token){val t=token;if(t==null){orders=emptyList();profile=AccountProfile();addresses=AccountAddresses()}else{runCatching{withContext(Dispatchers.IO){api.privacyV128(t)}}.onSuccess{privacyPrefs=it;privacyStore.save(it);FirebaseBootstrapV128.applyConsent(privacyContext,api,session,it)};runCatching{withContext(Dispatchers.IO){Triple(api.orders(t),api.accountProfile(t),api.accountAddresses(t))}}.onSuccess{(oo,pp,aa)->orders=oo;profile=pp;profileEdit=pp;addresses=aa;addressesEdit=aa;email=pp.email.ifBlank{email}}.onFailure{msg=it.message?:"Datele contului nu au putut fi încărcate."}}}
    val heroBilling=addresses.billing;val heroCompany=heroBilling.company.ifBlank{"COMPANIE"};val heroName=listOf(profile.firstName,profile.lastName).filter{it.isNotBlank()}.joinToString(" ").ifBlank{session.customerEmail};val heroVat=addresses.vatNumber
    selectedOrderId?.let{id->val t=token;if(t!=null){OrderDetailV120(api,t,id,onBack={selectedOrderId=null;panel="orders"});return}}
    LaunchedEffect(busy){if(busy){if(mode=="register")runCatching{withContext(Dispatchers.IO){api.register(email,pass,first,last,company,vat)}}.onSuccess{msg="Cont creat. Te poți autentifica.";mode="login"}.onFailure{msg=it.message?:"Înregistrare eșuată."} else runCatching{withContext(Dispatchers.IO){api.login(email,pass)}}.onSuccess{session.saveLogin(it);token=it.accessToken;email=it.customer?.email.orEmpty().ifBlank{email};msg="Autentificare reușită."}.onFailure{msg=it.message?:"Autentificare eșuată."};busy=false}}
    LazyColumn(Modifier.fillMaxSize().background(C114Soft).statusBarsPadding(),verticalArrangement=Arrangement.spacedBy(12.dp),contentPadding=PaddingValues(bottom=28.dp)){
        item{Row(Modifier.fillMaxWidth().background(Color.White).padding(start=16.dp,end=7.dp,top=8.dp,bottom=8.dp),verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text("Contul meu",fontSize=23.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(if(token==null)"Intră în ecosistemul AutoID" else session.customerEmail,fontSize=10.sp,color=C114Muted,maxLines=1,overflow=TextOverflow.Ellipsis)};HeaderActionsV114(commerce,onFavorites,onNotifications,onCart)}}
        if(token==null){item{Box(Modifier.padding(horizontal=14.dp)){ElevatedCard(shape=RoundedCornerShape(26.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)){Column(Modifier.fillMaxWidth().padding(18.dp),verticalArrangement=Arrangement.spacedBy(11.dp)){Surface(shape=RoundedCornerShape(50),color=C114OrangeSoft){Text("AUTOID ACCOUNT",Modifier.padding(horizontal=10.dp,vertical=5.dp),color=AutoIdOrange,fontSize=9.sp,fontWeight=FontWeight.ExtraBold)};Text(if(mode=="login")"Bună," else "Creează cont AutoID",fontSize=25.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(if(mode=="login")"Comenzi, favorite și suport într-un singur loc." else "Salvează datele și urmărește comenzile mai ușor.",color=C114Muted,fontSize=12.sp);Row(Modifier.fillMaxWidth().background(Color(0xFFF2F4F7),RoundedCornerShape(16.dp)).padding(5.dp),horizontalArrangement=Arrangement.spacedBy(5.dp)){listOf("login" to "Autentificare","register" to "Cont nou").forEach{(id,label)->Surface(onClick={mode=id;msg=""},modifier=Modifier.weight(1f),shape=RoundedCornerShape(12.dp),color=if(mode==id)Color.White else Color.Transparent,shadowElevation=if(mode==id)2.dp else 0.dp){Text(label,Modifier.fillMaxWidth().padding(horizontal=14.dp,vertical=12.dp),textAlign=TextAlign.Center,fontWeight=FontWeight.ExtraBold,fontSize=11.sp,color=if(mode==id)C114Ink else C114Muted)}}};if(mode=="register"){Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){OutlinedTextField(first,{first=it},label={Text("Prenume")},modifier=Modifier.weight(1f),singleLine=true,shape=RoundedCornerShape(13.dp));OutlinedTextField(last,{last=it},label={Text("Nume")},modifier=Modifier.weight(1f),singleLine=true,shape=RoundedCornerShape(13.dp))};OutlinedTextField(company,{company=it},label={Text("Companie")},modifier=Modifier.fillMaxWidth(),singleLine=true,shape=RoundedCornerShape(13.dp));OutlinedTextField(vat,{vat=it},label={Text("Cod TVA")},modifier=Modifier.fillMaxWidth(),singleLine=true,shape=RoundedCornerShape(13.dp))};OutlinedTextField(email,{email=it},label={Text("Email")},modifier=Modifier.fillMaxWidth(),singleLine=true,shape=RoundedCornerShape(13.dp));OutlinedTextField(pass,{pass=it},label={Text("Parolă")},modifier=Modifier.fillMaxWidth(),singleLine=true,visualTransformation=PasswordVisualTransformation(),shape=RoundedCornerShape(13.dp));Button(onClick={busy=true},enabled=!busy&&email.isNotBlank()&&pass.length>=8,modifier=Modifier.fillMaxWidth().height(54.dp),shape=RoundedCornerShape(16.dp)){Text(if(busy)"Se procesează..." else if(mode=="login")"Autentificare" else "Creează cont",fontWeight=FontWeight.ExtraBold)};GoogleButtonV114(clientId=cfg.googleClientId,api=api,session=session,onSuccess={r->token=r.accessToken;email=r.customer?.email.orEmpty().ifBlank{email};msg="Autentificare Google reușită."},onError={msg=it},modifier=Modifier.fillMaxWidth(),label=if(mode=="login")"Continuă cu Google" else "Înscrie-te cu Google");if(msg.isNotBlank())Text(msg,fontSize=10.sp,color=if(msg.contains("reușită")||msg.contains("creat"))C114Good else MaterialTheme.colorScheme.error)}}}}
        }else{
            item{Box(Modifier.padding(horizontal=14.dp)){ElevatedCard(shape=RoundedCornerShape(26.dp),colors=CardDefaults.elevatedCardColors(containerColor=C114Ink)){Column(Modifier.fillMaxWidth().padding(20.dp),verticalArrangement=Arrangement.spacedBy(5.dp)){Text("CONT AUTOID: $heroCompany",fontSize=13.sp,fontWeight=FontWeight.ExtraBold,color=Color.White);if(heroVat.isNotBlank())Text("COD TVA: $heroVat",fontSize=9.sp,color=Color(0xFF98A2B3));Spacer(Modifier.height(5.dp));Text(heroName,fontSize=20.sp,fontWeight=FontWeight.ExtraBold,color=Color.White);Text("Email: ${profile.email.ifBlank{session.customerEmail}}   Telefon: ${heroBilling.phone}",fontSize=9.sp,color=Color(0xFF98A2B3))}}}}
            item{Box(Modifier.padding(horizontal=14.dp)){ElevatedCard(shape=RoundedCornerShape(22.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Column(Modifier.fillMaxWidth().padding(8.dp)){listOf(
                Triple("dashboard","Panou control",Icons.Default.Dashboard),Triple("orders","Comenzi",Icons.Default.ReceiptLong),Triple("details","Detalii cont",Icons.Default.ManageAccounts),Triple("addresses","Adrese Facturare / Livrare",Icons.Default.HomeWork),Triple("payments","Metode de plată",Icons.Default.CreditCard),Triple("preferences","Confidențialitate și consimțământ",Icons.Default.PrivacyTip)
            ).forEach{(id,label,icon)->val active=panel==id;Row(Modifier.fillMaxWidth().background(if(active)C114OrangeSoft else Color.Transparent,RoundedCornerShape(14.dp)).clickable{panel=id}.padding(horizontal=12.dp,vertical=12.dp),verticalAlignment=Alignment.CenterVertically){Icon(icon,null,tint=if(active)AutoIdOrange else C114Muted,modifier=Modifier.size(19.dp));Spacer(Modifier.width(10.dp));Text(label,Modifier.weight(1f),fontWeight=if(active)FontWeight.ExtraBold else FontWeight.SemiBold,color=C114Ink,fontSize=12.sp);Icon(Icons.Default.ChevronRight,null,tint=C114Muted,modifier=Modifier.size(18.dp))}}}}}}
            when(panel){
                "dashboard"->{if(orders.isEmpty())item{Box(Modifier.padding(horizontal=14.dp)){Surface(shape=RoundedCornerShape(18.dp),color=Color.White){Text("Nu ai încă comenzi disponibile.",Modifier.fillMaxWidth().padding(17.dp),color=C114Muted,fontSize=11.sp)}}}else item{val o=orders.first();Box(Modifier.padding(horizontal=14.dp)){LatestOrderCardV119(o,onTrack={if(o.trackingUrl.isNotBlank())uriHandler.openUri(o.trackingUrl)},onView={selectedOrderId=o.id})}}}
                "orders"->{item{Text("Comenzi",Modifier.padding(horizontal=16.dp),fontSize=18.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink)};if(orders.isEmpty())item{Box(Modifier.padding(horizontal=14.dp)){Surface(shape=RoundedCornerShape(18.dp),color=Color.White){Text("Nu ai încă comenzi disponibile.",Modifier.fillMaxWidth().padding(17.dp),color=C114Muted,fontSize=11.sp)}}}else items(orders,key={it.id}){o->Box(Modifier.padding(horizontal=14.dp)){ElevatedCard(modifier=Modifier.fillMaxWidth().clickable{selectedOrderId=o.id},shape=RoundedCornerShape(18.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Row(Modifier.fillMaxWidth().padding(15.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.Inventory2,null,tint=AutoIdOrange);Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)){Text("Comanda #${o.number}",fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(o.dateCreated,fontSize=9.sp,color=C114Muted);if(o.trackingNumber.isNotBlank())Text("GLS · AWB ${o.trackingNumber}",fontSize=9.sp,color=C114Muted)};Column(horizontalAlignment=Alignment.End){val visualStatus=orderDisplayStatusV121(o.statusCode,o.trackingNumber,o.status);Text(visualStatus,fontSize=9.sp,fontWeight=FontWeight.Bold,color=if(orderIsTerminalV121(o.statusCode))MaterialTheme.colorScheme.error else C114Good);Text(o.total,fontWeight=FontWeight.ExtraBold,color=C114Ink,fontSize=12.sp);if(o.canPay||o.canCancel){Row(horizontalArrangement=Arrangement.spacedBy(5.dp)){if(o.canPay)TextButton(onClick={selectedOrderId=o.id}){Text("Plătește",fontSize=9.sp,fontWeight=FontWeight.ExtraBold)};if(o.canCancel)TextButton(onClick={selectedOrderId=o.id}){Text("Anulează",fontSize=9.sp,color=MaterialTheme.colorScheme.error)}}}else Icon(Icons.Default.ChevronRight,null,tint=C114Muted,modifier=Modifier.size(18.dp))}}}}}}
                "details"->item{Box(Modifier.padding(horizontal=14.dp)){SectionV114(Icons.Default.ManageAccounts,"Detalii cont","Sincronizate cu WooCommerce"){if(!detailsEditing){Text(listOf(profile.firstName,profile.lastName).filter{it.isNotBlank()}.joinToString(" "),fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(profile.email,fontSize=11.sp,color=C114Muted);TextButton(onClick={profileEdit=profile;newPassword="";detailsEditing=true},modifier=Modifier.align(Alignment.End)){Text("Editează",fontWeight=FontWeight.ExtraBold)}}else{Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){OutlinedTextField(profileEdit.firstName,{profileEdit=profileEdit.copy(firstName=it)},label={Text("Prenume")},modifier=Modifier.weight(1f),singleLine=true);OutlinedTextField(profileEdit.lastName,{profileEdit=profileEdit.copy(lastName=it)},label={Text("Nume")},modifier=Modifier.weight(1f),singleLine=true)};OutlinedTextField(profileEdit.email,{profileEdit=profileEdit.copy(email=it)},label={Text("Email")},modifier=Modifier.fillMaxWidth(),singleLine=true);OutlinedTextField(newPassword,{newPassword=it},label={Text("Parolă nouă (opțional)")},modifier=Modifier.fillMaxWidth(),singleLine=true,visualTransformation=PasswordVisualTransformation());Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.End){TextButton(onClick={detailsEditing=false}){Text("Anulează")};Button(onClick={val t=token?:return@Button;accountScope.launch{accountBusy=true;runCatching{withContext(Dispatchers.IO){api.saveAccountProfile(t,profileEdit.firstName,profileEdit.lastName,profileEdit.email,newPassword)}}.onSuccess{profile=it;profileEdit=it;session.customerEmail=it.email;detailsEditing=false;msg="Detaliile contului au fost salvate."}.onFailure{msg=it.message?:"Salvarea a eșuat."};accountBusy=false}},enabled=!accountBusy&&profileEdit.email.contains("@")){Text(if(accountBusy)"Se salvează..." else "Salvează")}}}}}}
                "addresses"->item{Box(Modifier.padding(horizontal=14.dp)){SectionV114(Icons.Default.HomeWork,"Adrese Facturare / Livrare","Companie și CUI incluse"){if(!addressesEditing){val b=addresses.billing;val sh=addresses.shipping;Text("Facturare",fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(listOf(b.company,b.address1,b.city,b.postcode).filter{it.isNotBlank()}.joinToString(", "),fontSize=11.sp,color=C114Muted);if(addresses.vatNumber.isNotBlank())Text("CUI / Cod TVA: ${addresses.vatNumber}",fontSize=10.sp,color=C114Muted);Spacer(Modifier.height(7.dp));Text("Livrare",fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(listOf(sh.address1,sh.city,sh.postcode).filter{it.isNotBlank()}.joinToString(", "),fontSize=11.sp,color=C114Muted);TextButton(onClick={addressesEdit=addresses;addressesEditing=true},modifier=Modifier.align(Alignment.End)){Text("Editează",fontWeight=FontWeight.ExtraBold)}}else{val b=addressesEdit.billing;val sh=addressesEdit.shipping;Text("Facturare",fontWeight=FontWeight.ExtraBold,color=C114Ink);AddressFieldsV114("account-billing",b.firstName,{addressesEdit=addressesEdit.copy(billing=addressesEdit.billing.copy(firstName=it))},b.lastName,{addressesEdit=addressesEdit.copy(billing=addressesEdit.billing.copy(lastName=it))},address1=b.address1,onAddress1={addressesEdit=addressesEdit.copy(billing=addressesEdit.billing.copy(address1=it))},address2=b.address2,onAddress2={addressesEdit=addressesEdit.copy(billing=addressesEdit.billing.copy(address2=it))},city=b.city,onCity={addressesEdit=addressesEdit.copy(billing=addressesEdit.billing.copy(city=it))},state=b.state,onState={addressesEdit=addressesEdit.copy(billing=addressesEdit.billing.copy(state=it))},postcode=b.postcode,onPostcode={addressesEdit=addressesEdit.copy(billing=addressesEdit.billing.copy(postcode=it))},country=b.country,onCountry={addressesEdit=addressesEdit.copy(billing=addressesEdit.billing.copy(country=it))});OutlinedTextField(b.company,{addressesEdit=addressesEdit.copy(billing=addressesEdit.billing.copy(company=it))},label={Text("Companie")},modifier=Modifier.fillMaxWidth(),singleLine=true);OutlinedTextField(addressesEdit.vatNumber,{addressesEdit=addressesEdit.copy(vatNumber=it)},label={Text("CUI / Cod TVA")},modifier=Modifier.fillMaxWidth(),singleLine=true);OutlinedTextField(b.phone,{addressesEdit=addressesEdit.copy(billing=addressesEdit.billing.copy(phone=it))},label={Text("Telefon")},modifier=Modifier.fillMaxWidth(),singleLine=true);OutlinedTextField(b.email,{addressesEdit=addressesEdit.copy(billing=addressesEdit.billing.copy(email=it))},label={Text("Email")},modifier=Modifier.fillMaxWidth(),singleLine=true);HorizontalDivider(color=C114Border);Text("Livrare",fontWeight=FontWeight.ExtraBold,color=C114Ink);AddressFieldsV114("account-shipping",sh.firstName,{addressesEdit=addressesEdit.copy(shipping=addressesEdit.shipping.copy(firstName=it))},sh.lastName,{addressesEdit=addressesEdit.copy(shipping=addressesEdit.shipping.copy(lastName=it))},address1=sh.address1,onAddress1={addressesEdit=addressesEdit.copy(shipping=addressesEdit.shipping.copy(address1=it))},address2=sh.address2,onAddress2={addressesEdit=addressesEdit.copy(shipping=addressesEdit.shipping.copy(address2=it))},city=sh.city,onCity={addressesEdit=addressesEdit.copy(shipping=addressesEdit.shipping.copy(city=it))},state=sh.state,onState={addressesEdit=addressesEdit.copy(shipping=addressesEdit.shipping.copy(state=it))},postcode=sh.postcode,onPostcode={addressesEdit=addressesEdit.copy(shipping=addressesEdit.shipping.copy(postcode=it))},country=sh.country,onCountry={addressesEdit=addressesEdit.copy(shipping=addressesEdit.shipping.copy(country=it))});Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.End){TextButton(onClick={addressesEditing=false}){Text("Anulează")};Button(onClick={val t=token?:return@Button;accountScope.launch{accountBusy=true;runCatching{withContext(Dispatchers.IO){api.saveAccountAddresses(t,addressesEdit)}}.onSuccess{addresses=it;addressesEdit=it;addressesEditing=false;msg="Adresele au fost salvate."}.onFailure{msg=it.message?:"Salvarea adreselor a eșuat."};accountBusy=false}},enabled=!accountBusy){Text(if(accountBusy)"Se salvează..." else "Salvează")}}}}}}
                "payments"->item{Box(Modifier.padding(horizontal=14.dp)){SectionV114(Icons.Default.CreditCard,"Metode de plată","Cont WooCommerce"){Text("Metodele salvate vor fi afișate aici odată cu activarea plății native.",fontSize=11.sp,color=C114Muted)}}}
                "preferences"->item{Box(Modifier.padding(horizontal=14.dp)){SectionV114(Icons.Default.PrivacyTip,"Confidențialitate și consimțământ","Control nativ · modificabil oricând"){
                    Text("Necesare",fontWeight=FontWeight.ExtraBold,color=C114Ink);Text("Funcții esențiale pentru cont, coș, checkout și securitate. Sunt întotdeauna active.",fontSize=10.sp,color=C114Muted);Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){Text("Necesare",Modifier.weight(1f),fontWeight=FontWeight.SemiBold,color=C114Ink);Switch(true,{},enabled=false)}
                    HorizontalDivider(color=C114Border);Text("Preferințe opționale",fontWeight=FontWeight.ExtraBold,color=C114Ink)
                    PrivacyPrefRowV128("Actualizări despre comenzi","AWB, status, finalizare și invitația de review.",privacyPrefs.transactionalNotifications){privacyPrefs=privacyPrefs.copy(transactionalNotifications=it)}
                    PrivacyPrefRowV128("Analytics","Măsurarea utilizării aplicației. Dezactivat implicit.",privacyPrefs.analytics){privacyPrefs=privacyPrefs.copy(analytics=it)}
                    PrivacyPrefRowV128("Personalizare","Conținut și recomandări adaptate. Dezactivat implicit.",privacyPrefs.personalization){privacyPrefs=privacyPrefs.copy(personalization=it)}
                    PrivacyPrefRowV128("Marketing & promoții","Notificări comerciale și campanii. Dezactivat implicit.",privacyPrefs.marketing){privacyPrefs=privacyPrefs.copy(marketing=it)}
                    Text("Poți retrage oricând consimțământul. AutoID nu activează Analytics sau Marketing înainte de acord.",fontSize=9.sp,color=C114Muted)
                    Button(onClick={privacyStore.save(privacyPrefs);FirebaseBootstrapV128.applyConsent(privacyContext,api,session,privacyPrefs);val t=token;if(t!=null)accountScope.launch{privacyBusy=true;runCatching{withContext(Dispatchers.IO){api.savePrivacyV128(t,privacyPrefs)}}.onSuccess{privacyPrefs=it;privacyStore.save(it);msg="Preferințele de confidențialitate au fost salvate."}.onFailure{msg=it.message?:"Preferințele au fost salvate local."};privacyBusy=false}},enabled=!privacyBusy,modifier=Modifier.fillMaxWidth()){Text(if(privacyBusy)"Se salvează..." else "Salvează preferințele")}
                }}}
            }
            item{Box(Modifier.padding(start=14.dp,end=14.dp,top=3.dp)){OutlinedButton(onClick={val oldToken=token;if(oldToken!=null)FirebaseBootstrapV128.unregisterForLogout(privacyContext,api,oldToken);session.clear();token=null;orders=emptyList();msg=""},modifier=Modifier.fillMaxWidth().height(50.dp),shape=RoundedCornerShape(16.dp)){Icon(Icons.Default.Logout,null,Modifier.size(17.dp));Spacer(Modifier.width(6.dp));Text("Dezautentificare",fontWeight=FontWeight.Bold)}}}
        }
    }
}
