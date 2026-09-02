from pathlib import Path

root=Path('android-v0.1')
ux=root/'app/src/main/java/ro/autoid/app/V114CommerceUx.kt'
models=root/'app/src/main/java/ro/autoid/app/data/Models.kt'
api=root/'app/src/main/java/ro/autoid/app/data/AutoIdApi.kt'
gradle=root/'app/build.gradle.kts'
manifest=root/'app/src/main/AndroidManifest.xml'
plugin=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')

g=gradle.read_text()
g=g.replace('versionCode = 12600','versionCode = 12700').replace('versionName = "1.0.23"','versionName = "1.0.24"')
gradle.write_text(g)

a=api.read_text().replace('AutoID-Android/1.0.23','AutoID-Android/1.0.24')
a=a.replace('''            ShippingConfig(sh.optDouble("flat_rate_incl_vat",30.25),sh.optDouble("free_shipping_min",593.0),sh.optDouble("tax_rate",21.0),html(sh.optString("title","Livrare"))),
            o.optString("google_client_id")
''','''            ShippingConfig(sh.optDouble("flat_rate_incl_vat",30.25),sh.optDouble("free_shipping_min",593.0),sh.optDouble("tax_rate",21.0),html(sh.optString("title","Livrare"))),
            o.optString("google_client_id"),
            o.optString("stripe_publishable_key"),
            o.optString("stripe_mode")
''')
api.write_text(a)

m=models.read_text()
m=m.replace('''    val shipping:ShippingConfig = ShippingConfig(),
    val googleClientId:String = ""
)''','''    val shipping:ShippingConfig = ShippingConfig(),
    val googleClientId:String = "",
    val stripePublishableKey:String = "",
    val stripeMode:String = ""
)''')
models.write_text(m)

mt=manifest.read_text()
needle='''        <meta-data android:name="com.google.mlkit.vision.DEPENDENCIES" android:value="barcode_ui" />'''
if 'com.google.android.gms.wallet.api.enabled' not in mt:
    mt=mt.replace(needle,needle+'\n        <meta-data android:name="com.google.android.gms.wallet.api.enabled" android:value="true" />')
manifest.write_text(mt)

p=plugin.read_text()
p=p.replace('Version: 1.1.12','Version: 1.1.13',1)
p=p.replace("return rest_ensure_response(['currency'=>get_woocommerce_currency(),'country'=>WC()->countries->get_base_country(),'payments'=>$out,'shipping'=>self::mobile_shipping_config(),'google_client_id'=>self::mobile_google_client_id()]);",
            "return rest_ensure_response(['currency'=>get_woocommerce_currency(),'country'=>WC()->countries->get_base_country(),'payments'=>$out,'shipping'=>self::mobile_shipping_config(),'google_client_id'=>self::mobile_google_client_id(),'stripe_publishable_key'=>self::stripe_sandbox_ready()?self::stripe_publishable():'','stripe_mode'=>self::stripe_sandbox_ready()?'test':'']);",1)
plugin.write_text(p)

s=ux.read_text()
s=s.replace('''import com.stripe.android.paymentsheet.PaymentSheet
import com.stripe.android.paymentsheet.PaymentSheetResult
import com.stripe.android.paymentsheet.rememberPaymentSheet
''','''import androidx.compose.ui.viewinterop.AndroidView
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
''')

old='''    var payment by remember{mutableStateOf("cod")};var note by remember{mutableStateOf("")};var createAccount by remember{mutableStateOf(true)};var reviewConsent by remember{mutableStateOf(true)};var terms by remember{mutableStateOf(false)};var busy by remember{mutableStateOf(false)};var stripeConfirmBusy by remember{mutableStateOf(false)};var message by remember{mutableStateOf("")};var success by remember{mutableStateOf<CheckoutResult?>(null)}
    var stripePending by remember{mutableStateOf<CheckoutResult?>(null)};var stripePresent by remember{mutableStateOf<CheckoutResult?>(null)}
    val checkoutScope=rememberCoroutineScope();val checkoutContext=LocalContext.current
    val stripePendingCurrent=rememberUpdatedState(stripePending)
    val paymentSheet=rememberPaymentSheet{result->
        val pending=stripePendingCurrent.value
        when(result){
            is PaymentSheetResult.Completed->{
                if(pending==null){message="Plata Stripe a fost confirmată, dar comanda locală nu mai este disponibilă."}
                else{stripeConfirmBusy=true;checkoutScope.launch{runCatching{withContext(Dispatchers.IO){api.confirmStripePayment(pending.orderId,pending.stripePaymentIntentId,pending.stripePaymentToken,authToken)}}.onSuccess{paid->if(paid){success=pending;message="Plată confirmată. Comanda a fost înregistrată."}else message="Stripe a procesat plata, dar serverul nu a confirmat încă încasarea."}.onFailure{message=it.message?:"Nu am putut confirma plata pe server."};stripeConfirmBusy=false}}
            }
            is PaymentSheetResult.Canceled->{message="Plata a fost anulată. Comanda rămâne în așteptare și poți reîncerca plata."}
            is PaymentSheetResult.Failed->{message=result.error.localizedMessage?:"Plata Stripe nu a putut fi finalizată."}
        }
    }
'''
new='''    var payment by remember{mutableStateOf("cod")};var note by remember{mutableStateOf("")};var createAccount by remember{mutableStateOf(true)};var reviewConsent by remember{mutableStateOf(true)};var terms by remember{mutableStateOf(false)};var busy by remember{mutableStateOf(false)};var stripeConfirmBusy by remember{mutableStateOf(false)};var message by remember{mutableStateOf("")};var success by remember{mutableStateOf<CheckoutResult?>(null)}
    var stripePending by remember{mutableStateOf<CheckoutResult?>(null)};var stripePaymentChoice by remember{mutableStateOf("card")};var stripePayRequest by remember{mutableIntStateOf(0)};var stripeCardWidget by remember{mutableStateOf<CardInputWidget?>(null)};var stripeCardValid by remember{mutableStateOf(false)};var googlePayReady by remember{mutableStateOf(false)}
    val checkoutScope=rememberCoroutineScope();val checkoutContext=LocalContext.current
'''
assert old in s, 'old PaymentSheet state block not found'
s=s.replace(old,new,1)

s=s.replace('''    LaunchedEffect(Unit){runCatching{withContext(Dispatchers.IO){api.checkoutConfig()}}.onSuccess{cfg=it;scountry=it.country.ifBlank{"RO"};bcountry=scountry;payment=it.payments.firstOrNull{p->p.enabled}?.id?:"cod"}.onFailure{message=it.message?:"Nu am putut încărca setările checkout."}}''',
'''    LaunchedEffect(Unit){runCatching{withContext(Dispatchers.IO){api.checkoutConfig()}}.onSuccess{loaded->if(loaded.stripeMode=="test"&&loaded.stripePublishableKey.startsWith("pk_test_"))PaymentConfiguration.init(checkoutContext,loaded.stripePublishableKey);cfg=loaded;scountry=loaded.country.ifBlank{"RO"};bcountry=scountry;payment=loaded.payments.firstOrNull{p->p.enabled}?.id?:"cod"}.onFailure{message=it.message?:"Nu am putut încărca setările checkout."}}''',1)

s=s.replace('''else{stripePending=r;stripePresent=r;message="Deschid plata securizată Stripe…"}''','''else{stripePending=r;stripePayRequest+=1;message=if(stripePaymentChoice=="google_pay")"Deschid Google Pay…" else "Procesez plata securizată cu cardul…"}''',1)
old_effect='''    LaunchedEffect(stripePresent?.orderId){val r=stripePresent?:return@LaunchedEffect;stripePresent=null;PaymentConfiguration.init(checkoutContext,r.stripePublishableKey);paymentSheet.presentWithPaymentIntent(r.stripeClientSecret,PaymentSheet.Configuration(merchantDisplayName="AutoID Professional Solutions",allowsDelayedPaymentMethods=false))}
'''
assert old_effect in s, 'PaymentSheet LaunchedEffect not found'
s=s.replace(old_effect,'',1)

anchor='''    val valid=authReady&&email.contains("@")&&phone.isNotBlank()&&shippingOk&&billingOk&&terms&&lines.isNotEmpty()
'''
insert='''    val valid=authReady&&email.contains("@")&&phone.isNotBlank()&&shippingOk&&billingOk&&terms&&lines.isNotEmpty()
    val stripeBilling=StripePaymentMethod.BillingDetails(address=Address.Builder().setLine1(billingA1).setLine2(billingA2.ifBlank{null}).setCity(billingCity).setState(billingState.ifBlank{null}).setPostalCode(billingPost).setCountry(billingCountry.ifBlank{"RO"}).build(),email=email.ifBlank{null},name=listOf(billingFirst,billingLast).filter{it.isNotBlank()}.joinToString(" ").ifBlank{null},phone=phone.ifBlank{null})
    if(cfg.stripeMode=="test"&&cfg.stripePublishableKey.startsWith("pk_test_")){
        StripeLaunchersV124(
            publishableKey=cfg.stripePublishableKey,pending=stripePending,payRequest=stripePayRequest,paymentChoice=stripePaymentChoice,cardWidget=stripeCardWidget,billingDetails=stripeBilling,authToken=authToken,api=api,
            onGooglePayReady={googlePayReady=it},onBusy={stripeConfirmBusy=it},onMessage={message=it},onPaid={pending->success=pending;stripePending=null}
        )
    }else googlePayReady=false
'''
assert anchor in s
s=s.replace(anchor,insert,1)

old_cta='''Button(onClick={val pending=stripePending;if(payment=="stripe"&&pending!=null){stripePresent=pending}else busy=true},enabled=valid&&!busy&&!stripeConfirmBusy&&methods.firstOrNull{it.id==payment}?.enabled!=false,modifier=Modifier.fillMaxWidth().height(56.dp),shape=RoundedCornerShape(17.dp)){if(busy||stripeConfirmBusy){CircularProgressIndicator(Modifier.size(20.dp),strokeWidth=2.dp,color=Color.White);Spacer(Modifier.width(8.dp));Text(if(stripeConfirmBusy)"Confirm plata..." else "Se procesează...")}else Text(if(payment=="stripe"&&stripePending!=null)"Reîncearcă plata" else if(payment=="stripe")"Continuă la plata cu cardul" else "Plasează comanda",fontWeight=FontWeight.ExtraBold)}'''
new_cta='''Button(onClick={if(payment=="stripe"){if(stripePaymentChoice=="card"&&stripeCardWidget?.paymentMethodCard==null){message="Completează corect numărul cardului, data expirării și CVC."}else if(stripePaymentChoice=="google_pay"&&!googlePayReady){message="Google Pay nu este disponibil pe acest dispozitiv."}else if(stripePending!=null){stripePayRequest+=1}else busy=true}else busy=true},enabled=valid&&!busy&&!stripeConfirmBusy&&methods.firstOrNull{it.id==payment}?.enabled!=false&&(payment!="stripe"||stripePaymentChoice!="google_pay"||googlePayReady),modifier=Modifier.fillMaxWidth().height(56.dp),shape=RoundedCornerShape(10.dp)){if(busy||stripeConfirmBusy){CircularProgressIndicator(Modifier.size(20.dp),strokeWidth=2.dp,color=Color.White);Spacer(Modifier.width(8.dp));Text(if(stripeConfirmBusy)"Confirm plata..." else "Se procesează...")}else Text(if(payment=="stripe"&&stripePaymentChoice=="google_pay")"Plătește cu Google Pay" else if(payment=="stripe")"Plătește cu cardul" else "Plasează comanda",fontWeight=FontWeight.ExtraBold)}'''
assert old_cta in s, 'old CTA not found'
s=s.replace(old_cta,new_cta,1)

old_payment='''            item{SectionV114(Icons.Default.CreditCard,"Metoda de plată"){methods.forEach{m->val selected=payment==m.id;OutlinedCard(Modifier.fillMaxWidth().clickable(enabled=m.enabled){payment=m.id},shape=RoundedCornerShape(16.dp),colors=CardDefaults.outlinedCardColors(containerColor=if(selected)C114OrangeSoft else Color.White),border=BorderStroke(if(selected)2.dp else 1.dp,if(selected)AutoIdOrange else C114Border)){Row(Modifier.fillMaxWidth().padding(13.dp),verticalAlignment=Alignment.CenterVertically){Icon(when(m.id.lowercase()){ "cod"->Icons.Default.LocalShipping;"bacs"->Icons.Default.AccountBalance;else->Icons.Default.CreditCard},null,tint=if(selected)AutoIdOrange else C114Muted);Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)){Text(m.title,fontWeight=FontWeight.Bold,color=C114Ink);Text(m.description,fontSize=9.sp,color=C114Muted)};RadioButton(selected,{if(m.enabled)payment=m.id},enabled=m.enabled)}}}}}'''
new_payment='''            item{SectionV114(Icons.Default.CreditCard,"Metoda de plată"){methods.forEach{m->val selected=payment==m.id;OutlinedCard(Modifier.fillMaxWidth().clickable(enabled=m.enabled){payment=m.id},shape=RoundedCornerShape(10.dp),colors=CardDefaults.outlinedCardColors(containerColor=if(selected)C114OrangeSoft else Color.White),border=BorderStroke(if(selected)2.dp else 1.dp,if(selected)AutoIdOrange else C114Border)){Row(Modifier.fillMaxWidth().padding(13.dp),verticalAlignment=Alignment.CenterVertically){Icon(when(m.id.lowercase()){ "cod"->Icons.Default.LocalShipping;"bacs"->Icons.Default.AccountBalance;else->Icons.Default.CreditCard},null,tint=if(selected)AutoIdOrange else C114Muted);Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)){Text(m.title,fontWeight=FontWeight.Bold,color=C114Ink);Text(m.description,fontSize=9.sp,color=C114Muted)};RadioButton(selected,{if(m.enabled)payment=m.id},enabled=m.enabled)}}};if(payment=="stripe"){Column(verticalArrangement=Arrangement.spacedBy(10.dp)){Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){StripeChoiceV124("card","Card",stripePaymentChoice,{stripePaymentChoice=it},Modifier.weight(1f));if(googlePayReady)StripeChoiceV124("google_pay","Google Pay",stripePaymentChoice,{stripePaymentChoice=it},Modifier.weight(1f))};if(stripePaymentChoice=="card"){Surface(shape=RoundedCornerShape(10.dp),color=Color.White,border=BorderStroke(1.dp,C114Border)){Column(Modifier.fillMaxWidth().padding(12.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){Text("Date card",fontSize=12.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text("Introdu doar datele cardului. Numele și adresa sunt preluate din checkout-ul AutoID.",fontSize=9.sp,color=C114Muted);AndroidView(factory={ctx->CardInputWidget(ctx).apply{postalCodeEnabled=false;setCardValidCallback{validCard,_->stripeCardValid=validCard};stripeCardWidget=this}},update={stripeCardWidget=it},modifier=Modifier.fillMaxWidth().heightIn(min=58.dp))}};if(!stripeCardValid)Text("Număr card · expirare · CVC",fontSize=9.sp,color=C114Muted)}else{Surface(shape=RoundedCornerShape(10.dp),color=Color.White,border=BorderStroke(1.dp,C114Border)){Column(Modifier.fillMaxWidth().padding(12.dp),verticalArrangement=Arrangement.spacedBy(5.dp)){Text("Google Pay",fontWeight=FontWeight.ExtraBold,color=C114Ink);Text("Plata se deschide în Google Pay. Nu solicităm din nou adresa sau datele de contact.",fontSize=9.sp,color=C114Muted)}}}}}}}'''
assert old_payment in s, 'payment method section not found'
s=s.replace(old_payment,new_payment,1)

helper_anchor='''@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CheckoutV114'''
helpers='''@Composable
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
fun CheckoutV114'''
assert helper_anchor in s
s=s.replace(helper_anchor,helpers,1)

ux.write_text(s)

values=root/'app/src/main/res/values'
values.mkdir(parents=True,exist_ok=True)
style=values/'stripe_autoid_v124.xml'
style.write_text('''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Stripe.CardInputWidget.EditText" parent="Stripe.Base.CardInputWidget.EditText">
        <item name="android:textColor">#111827</item>
        <item name="android:textColorHint">#667085</item>
        <item name="android:textSize">15sp</item>
    </style>
</resources>
''')
print('Applied AutoID Android v1.0.24 + AutoID Mobile v1.1.13 inline Stripe Card + Google Pay checkout')
