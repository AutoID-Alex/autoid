from pathlib import Path

ROOT=Path('.')
SRC=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app'
UI=SRC/'V114CommerceUx.kt'
API=SRC/'data/AutoIdApi.kt'
MODELS=SRC/'data/Models.kt'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'

# Version bump.
s=GRADLE.read_text()
s=s.replace('versionCode = 11800','versionCode = 11900',1)
s=s.replace('versionName = "1.0.15"','versionName = "1.0.16"',1)
if 'storeFile = file("../autoid-dev.keystore")' not in s:
    signing='''    signingConfigs {\n        getByName("debug") {\n            storeFile = file("../autoid-dev.keystore")\n            storePassword = "autoiddev2026"\n            keyAlias = "autoiddev"\n            keyPassword = "autoiddev2026"\n        }\n    }\n\n'''
    marker='    buildTypes {\n'
    if marker not in s: raise SystemExit('Gradle signing anchor missing')
    s=s.replace(marker,signing+marker,1)
GRADLE.write_text(s)

# Models used to hydrate checkout from the authenticated WooCommerce customer.
s=MODELS.read_text()
old='data class CheckoutResult(val orderId:Long,val number:String,val status:String,val total:String,val currency:String,val paymentMethod:String,val requiresPayment:Boolean)'
new='data class CheckoutResult(val orderId:Long,val number:String,val status:String,val total:String,val currency:String,val paymentMethod:String,val requiresPayment:Boolean,val accessToken:String?=null,val customer:Customer?=null,val accountCreated:Boolean=false)'
if old not in s: raise SystemExit('CheckoutResult anchor missing')
s=s.replace(old,new,1)
anchor='data class RegistrationResult(val created:Boolean,val customerId:Long,val email:String)\n'
extra='''data class AccountAddress(val firstName:String="",val lastName:String="",val company:String="",val address1:String="",val address2:String="",val city:String="",val state:String="",val postcode:String="",val country:String="RO",val phone:String="",val email:String="")\ndata class AccountAddresses(val billing:AccountAddress=AccountAddress(),val shipping:AccountAddress=AccountAddress(),val vatNumber:String="")\n'''
if 'data class AccountAddress(' not in s:
    if anchor not in s: raise SystemExit('AccountAddress anchor missing')
    s=s.replace(anchor,anchor+extra,1)
MODELS.write_text(s)

# API: v1.0.16 UA, account addresses, create-account flag and auth token returned by checkout.
s=API.read_text().replace('AutoID-Android/1.0.15','AutoID-Android/1.0.16')
old='''        vat:String, note:String, payment:String, reviewConsent:Boolean, token:String?=null\n    ):CheckoutResult{\n        val b=JSONObject().put("payment_method",payment).put("vat_number",vat).put("customer_note",note).put("review_consent",reviewConsent)'''
new='''        vat:String, note:String, payment:String, reviewConsent:Boolean, createAccount:Boolean, token:String?=null\n    ):CheckoutResult{\n        val b=JSONObject().put("payment_method",payment).put("vat_number",vat).put("customer_note",note).put("review_consent",reviewConsent).put("create_account",createAccount)'''
if old not in s: raise SystemExit('createOrder signature anchor missing')
s=s.replace(old,new,1)
old='''        val o=JSONObject(post("$MOBILE/checkout/order",b.toString(),token));return CheckoutResult(o.optLong("order_id"),o.optString("number"),o.optString("status"),o.optString("total"),o.optString("currency","RON"),o.optString("payment_method",payment),o.optBoolean("requires_payment"))\n    }\n\n    fun googleLogin'''
new='''        val o=JSONObject(post("$MOBILE/checkout/order",b.toString(),token));val u=o.optJSONObject("customer");return CheckoutResult(o.optLong("order_id"),o.optString("number"),o.optString("status"),o.optString("total"),o.optString("currency","RON"),o.optString("payment_method",payment),o.optBoolean("requires_payment"),o.optString("access_token").ifBlank{null},u?.let{Customer(if(it.has("id"))it.optLong("id") else null,listOf(it.optString("first_name"),it.optString("last_name")).filter(String::isNotBlank).joinToString(" ").ifBlank{it.optString("name")},it.optString("email"))},o.optBoolean("account_created"))\n    }\n\n    private fun accountAddress(o:JSONObject)=AccountAddress(o.optString("first_name"),o.optString("last_name"),o.optString("company"),o.optString("address_1"),o.optString("address_2"),o.optString("city"),o.optString("state"),o.optString("postcode"),o.optString("country","RO"),o.optString("phone"),o.optString("email"))\n\n    fun accountAddresses(token:String):AccountAddresses{\n        val o=JSONObject(get("$MOBILE/me/addresses",token));return AccountAddresses(accountAddress(o.optJSONObject("billing")?:JSONObject()),accountAddress(o.optJSONObject("shipping")?:JSONObject()),o.optString("vat_number"))\n    }\n\n    fun googleLogin'''
if old not in s: raise SystemExit('createOrder result anchor missing')
s=s.replace(old,new,1)
API.write_text(s)

s=UI.read_text()
s=s.replace('import androidx.compose.ui.text.style.TextOverflow\n','import androidx.compose.ui.text.style.TextAlign\nimport androidx.compose.ui.text.style.TextOverflow\n',1)
s=s.replace('import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption\n','import com.google.android.libraries.identity.googleid.GetGoogleIdOption\n',1)
old='val option=GetSignInWithGoogleOption.Builder(clientId).build()'
new='val option=GetGoogleIdOption.Builder().setFilterByAuthorizedAccounts(false).setServerClientId(clientId).setAutoSelectEnabled(false).build()'
if old not in s: raise SystemExit('Google option anchor missing')
s=s.replace(old,new,1)
old='''            }catch(e:GetCredentialException){onError(e.message?:"Autentificarea Google a fost anulată.")}'''
new='''            }catch(e:GetCredentialException){val raw=e.message.orEmpty();onError(if(raw.contains("reauth",true))"Google solicită reautentificarea contului. Selectează din nou contul Google." else raw.ifBlank{"Autentificarea Google a fost anulată."})}'''
s=s.replace(old,new,1)

# Checkout defaults: review + account creation enabled.
old='var payment by remember{mutableStateOf("cod")};var note by remember{mutableStateOf("")};var reviewConsent by remember{mutableStateOf(false)};var terms by remember{mutableStateOf(false)};var busy by remember{mutableStateOf(false)};var message by remember{mutableStateOf("")};var success by remember{mutableStateOf<CheckoutResult?>(null)}'
new='var payment by remember{mutableStateOf("cod")};var note by remember{mutableStateOf("")};var createAccount by remember{mutableStateOf(true)};var reviewConsent by remember{mutableStateOf(true)};var terms by remember{mutableStateOf(false)};var busy by remember{mutableStateOf(false)};var message by remember{mutableStateOf("")};var success by remember{mutableStateOf<CheckoutResult?>(null)}'
if old not in s: raise SystemExit('checkout defaults anchor missing')
s=s.replace(old,new,1)

# Create order passes createAccount for guest checkout; successful auto-created accounts are logged in immediately.
old='''LaunchedEffect(busy){if(busy){runCatching{withContext(Dispatchers.IO){api.createOrderV114(lines,email,phone,sf,sl,sa1,sa2,scity,sstate,spost,scountry,billingFirst,billingLast,company,billingA1,billingA2,billingCity,billingState,billingPost,billingCountry,vat,note,payment,reviewConsent,authToken)}}.onSuccess{success=it;message="Comandă plasată cu succes."}.onFailure{message=it.message?:"Comanda nu a putut fi plasată."};busy=false}}'''
new='''LaunchedEffect(busy){if(busy){runCatching{withContext(Dispatchers.IO){api.createOrderV114(lines,email,phone,sf,sl,sa1,sa2,scity,sstate,spost,scountry,billingFirst,billingLast,company,billingA1,billingA2,billingCity,billingState,billingPost,billingCountry,vat,note,payment,reviewConsent,createAccount&&authToken==null,authToken)}}.onSuccess{r->if(!r.accessToken.isNullOrBlank()){session.saveLogin(LoginResult(r.accessToken,customer=r.customer));authToken=r.accessToken;authMode="authenticated"};success=r;message="Comandă plasată cu succes."}.onFailure{message=it.message?:"Comanda nu a putut fi plasată."};busy=false}}'''
if old not in s: raise SystemExit('checkout submit anchor missing')
s=s.replace(old,new,1)

# Logged-in sessions, password login and Google login all hydrate checkout from WooCommerce account addresses.
auth_effect='''    LaunchedEffect(authBusy){if(authBusy){runCatching{withContext(Dispatchers.IO){api.login(login,pass)}}.onSuccess{session.saveLogin(it);authToken=it.accessToken;authMode="authenticated";email=it.customer?.email.orEmpty().ifBlank{login};message="Autentificare reușită."}.onFailure{message=it.message?:"Autentificare eșuată."};authBusy=false}}\n'''
prefill='''    LaunchedEffect(authToken,authMode){val t=authToken;if(t!=null&&authMode=="authenticated"){runCatching{withContext(Dispatchers.IO){api.accountAddresses(t)}}.onSuccess{a->val sh=if(a.shipping.address1.isNotBlank())a.shipping else a.billing;email=a.billing.email.ifBlank{email};phone=a.billing.phone.ifBlank{phone};sf=sh.firstName;sl=sh.lastName;sa1=sh.address1;sa2=sh.address2;scity=sh.city;sstate=sh.state;spost=sh.postcode;scountry=sh.country.ifBlank{"RO"};bf=a.billing.firstName;bl=a.billing.lastName;company=a.billing.company;ba1=a.billing.address1;ba2=a.billing.address2;bcity=a.billing.city;bstate=a.billing.state;bpost=a.billing.postcode;bcountry=a.billing.country.ifBlank{"RO"};vat=a.vatNumber}}}\n'''
if auth_effect not in s: raise SystemExit('auth effect anchor missing')
s=s.replace(auth_effect,auth_effect+prefill,1)

# Make checkout continuation a clean two-option selector instead of stacked primary/guest buttons.
start=s.index('            item{SectionV114(Icons.Default.Person,"Cum continui?"')
end=s.index('            item{ElevatedCard(Modifier.fillMaxWidth().clickable{summaryOpen=!summaryOpen}',start)
new_auth='''            item{SectionV114(Icons.Default.Person,"Cum continui?","Alege cum vrei să finalizezi comanda"){
                if(authMode=="authenticated"){Surface(shape=RoundedCornerShape(15.dp),color=C114GoodSoft){Row(Modifier.fillMaxWidth().padding(12.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.VerifiedUser,null,tint=C114Good);Spacer(Modifier.width(8.dp));Column(Modifier.weight(1f)){Text("Ești autentificat",fontWeight=FontWeight.Bold,color=C114Good);Text(session.customerEmail.ifBlank{email},fontSize=10.sp,color=C114Muted)};TextButton(onClick={session.clear();authToken=null;authMode="login"}){Text("Schimbă")}}}}
                else{
                    Row(Modifier.fillMaxWidth().background(Color(0xFFF2F4F7),RoundedCornerShape(16.dp)).padding(5.dp),horizontalArrangement=Arrangement.spacedBy(5.dp)){listOf("login" to "Autentificare","guest" to "Continuă ca invitat").forEach{(id,label)->Surface(onClick={authMode=id;message=""},modifier=Modifier.weight(1f),shape=RoundedCornerShape(12.dp),color=if(authMode==id)Color.White else Color.Transparent,shadowElevation=if(authMode==id)2.dp else 0.dp){Text(label,Modifier.fillMaxWidth().padding(horizontal=10.dp,vertical=12.dp),textAlign=TextAlign.Center,fontWeight=FontWeight.ExtraBold,fontSize=11.sp,color=if(authMode==id)C114Ink else C114Muted)}}}
                    if(authMode=="login"){OutlinedTextField(login,{login=it},label={Text("User / Email")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(14.dp));OutlinedTextField(pass,{pass=it},label={Text("Parolă")},singleLine=true,visualTransformation=PasswordVisualTransformation(),modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(14.dp));Button(onClick={authBusy=true},enabled=!authBusy&&login.isNotBlank()&&pass.isNotBlank(),modifier=Modifier.fillMaxWidth().height(52.dp),shape=RoundedCornerShape(16.dp)){Text(if(authBusy)"Se conectează..." else "Autentificare",fontWeight=FontWeight.Bold)};GoogleButtonV114(clientId=cfg.googleClientId,api=api,session=session,onSuccess={r->authToken=r.accessToken;authMode="authenticated";email=r.customer?.email.orEmpty().ifBlank{email};message="Autentificare Google reușită."},onError={message=it},modifier=Modifier.fillMaxWidth())}
                    else Surface(shape=RoundedCornerShape(14.dp),color=Color(0xFFF8F9FB)){Text("Finalizezi rapid fără autentificare. Poți crea automat un cont AutoID odată cu comanda.",Modifier.fillMaxWidth().padding(12.dp),fontSize=10.sp,color=C114Muted)}
                }
            }}
'''
s=s[:start]+new_auth+s[end:]

# Add create-account consent before review consent; both default checked.
old='''            item{ElevatedCard(shape=RoundedCornerShape(18.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)){Column{Row(Modifier.fillMaxWidth().clickable{reviewConsent=!reviewConsent}.padding(horizontal=14.dp,vertical=10.dp),verticalAlignment=Alignment.CenterVertically){Checkbox(reviewConsent,{reviewConsent=it});Spacer(Modifier.width(5.dp));Column(Modifier.weight(1f)){Text("Permite solicitarea unei recenzii",fontSize=11.sp,fontWeight=FontWeight.Bold,color=C114Ink);Text("Putem trimite o invitație de review după livrarea comenzii.",fontSize=9.sp,color=C114Muted)}};HorizontalDivider(color=C114Border);Row(Modifier.fillMaxWidth().clickable{terms=!terms}.padding(horizontal=14.dp,vertical=10.dp),verticalAlignment=Alignment.CenterVertically){Checkbox(terms,{terms=it});Spacer(Modifier.width(5.dp));Text("Accept termenii și condițiile.",fontSize=11.sp,color=C114Ink,modifier=Modifier.weight(1f))}}}}'''
new='''            item{ElevatedCard(shape=RoundedCornerShape(18.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)){Column{if(authMode!="authenticated"){Row(Modifier.fillMaxWidth().clickable{createAccount=!createAccount}.padding(horizontal=14.dp,vertical=10.dp),verticalAlignment=Alignment.CenterVertically){Checkbox(createAccount,{createAccount=it});Spacer(Modifier.width(5.dp));Column(Modifier.weight(1f)){Text("Creează un cont AutoID",fontSize=11.sp,fontWeight=FontWeight.Bold,color=C114Ink);Text("Salvăm datele comenzii și îți trimitem accesul la cont.",fontSize=9.sp,color=C114Muted)}};HorizontalDivider(color=C114Border)};Row(Modifier.fillMaxWidth().clickable{reviewConsent=!reviewConsent}.padding(horizontal=14.dp,vertical=10.dp),verticalAlignment=Alignment.CenterVertically){Checkbox(reviewConsent,{reviewConsent=it});Spacer(Modifier.width(5.dp));Column(Modifier.weight(1f)){Text("Permite solicitarea unei recenzii",fontSize=11.sp,fontWeight=FontWeight.Bold,color=C114Ink);Text("Putem trimite o invitație de review după livrarea comenzii.",fontSize=9.sp,color=C114Muted)}};HorizontalDivider(color=C114Border);Row(Modifier.fillMaxWidth().clickable{terms=!terms}.padding(horizontal=14.dp,vertical=10.dp),verticalAlignment=Alignment.CenterVertically){Checkbox(terms,{terms=it});Spacer(Modifier.width(5.dp));Text("Accept termenii și condițiile.",fontSize=11.sp,color=C114Ink,modifier=Modifier.weight(1f))}}}}'''
if old not in s: raise SystemExit('consent card anchor missing')
s=s.replace(old,new,1)

# Account login/register selector: professional spacing + centered labels.
old='''Row(Modifier.fillMaxWidth().background(Color(0xFFF2F4F7),RoundedCornerShape(14.dp)).padding(4.dp)){listOf("login" to "Autentificare","register" to "Cont nou").forEach{(id,label)->Surface(onClick={mode=id;msg=""},modifier=Modifier.weight(1f),shape=RoundedCornerShape(11.dp),color=if(mode==id)Color.White else Color.Transparent,shadowElevation=if(mode==id)1.dp else 0.dp){Text(label,Modifier.padding(vertical=10.dp),fontWeight=FontWeight.Bold,fontSize=11.sp,color=C114Ink)}}}'''
new='''Row(Modifier.fillMaxWidth().background(Color(0xFFF2F4F7),RoundedCornerShape(16.dp)).padding(5.dp),horizontalArrangement=Arrangement.spacedBy(5.dp)){listOf("login" to "Autentificare","register" to "Cont nou").forEach{(id,label)->Surface(onClick={mode=id;msg=""},modifier=Modifier.weight(1f),shape=RoundedCornerShape(12.dp),color=if(mode==id)Color.White else Color.Transparent,shadowElevation=if(mode==id)2.dp else 0.dp){Text(label,Modifier.fillMaxWidth().padding(horizontal=14.dp,vertical=12.dp),textAlign=TextAlign.Center,fontWeight=FontWeight.ExtraBold,fontSize=11.sp,color=if(mode==id)C114Ink else C114Muted)}}}'''
if old not in s: raise SystemExit('account selector anchor missing')
s=s.replace(old,new,1)

UI.write_text(s)
print('Applied AutoID Android v1.0.16 checkout/account fixes')
