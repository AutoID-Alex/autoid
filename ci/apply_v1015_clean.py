from pathlib import Path

ROOT=Path('.')
APP=ROOT/'android-v0.1/app'
SRC=APP/'src/main/java/ro/autoid/app'
UI=SRC/'V114CommerceUx.kt'
API=SRC/'data/AutoIdApi.kt'
GRADLE=APP/'build.gradle.kts'

s=GRADLE.read_text()
s=s.replace('versionCode = 11700','versionCode = 11800',1).replace('versionName = "1.0.14"','versionName = "1.0.15"',1)
old='    implementation("com.google.android.gms:play-services-auth:21.2.0")\n'
new='''    implementation("androidx.credentials:credentials:1.6.0")\n    implementation("androidx.credentials:credentials-play-services-auth:1.6.0")\n    implementation("com.google.android.libraries.identity.googleid:googleid:1.2.0")\n'''
if old in s: s=s.replace(old,new,1)
elif 'androidx.credentials:credentials:1.6.0' not in s: raise SystemExit('Google dependency anchor missing')
GRADLE.write_text(s)

s=API.read_text().replace('AutoID-Android/1.0.14','AutoID-Android/1.0.15')
API.write_text(s)

s=UI.read_text()
for line in [
'import androidx.activity.compose.rememberLauncherForActivityResult\n',
'import androidx.activity.result.contract.ActivityResultContracts\n',
'import com.google.android.gms.auth.api.signin.GoogleSignIn\n',
'import com.google.android.gms.auth.api.signin.GoogleSignInOptions\n',
'import com.google.android.gms.common.api.ApiException\n',
]: s=s.replace(line,'')
anchor='import androidx.compose.ui.unit.sp\n'
imports='''import androidx.credentials.CredentialManager\nimport androidx.credentials.CustomCredential\nimport androidx.credentials.GetCredentialRequest\nimport androidx.credentials.exceptions.GetCredentialException\nimport com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption\nimport com.google.android.libraries.identity.googleid.GoogleIdTokenCredential\n'''
if 'import androidx.credentials.CredentialManager' not in s:
    if anchor not in s: raise SystemExit('Credential import anchor missing')
    s=s.replace(anchor,anchor+imports,1)

a=s.index('@Composable\nprivate fun GoogleButtonV114(')
b=s.index('\n@Composable\nprivate fun AddressFieldsV114',a)
google='''@Composable
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
                val option=GetSignInWithGoogleOption.Builder(clientId).build()
                val request=GetCredentialRequest.Builder().addCredentialOption(option).build()
                val result=manager.getCredential(context=context,request=request)
                val credential=result.credential
                if(credential !is CustomCredential || credential.type!=GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL){onError("Google nu a returnat o identitate compatibilă.")}
                else{
                    val token=GoogleIdTokenCredential.createFrom(credential.data).idToken
                    val login=withContext(Dispatchers.IO){api.googleLogin(token)}
                    session.saveLogin(login);onSuccess(login)
                }
            }catch(e:GetCredentialException){onError(e.message?:"Autentificarea Google a fost anulată.")}
            catch(e:Throwable){onError(e.message?:"Autentificare Google eșuată.")}
            finally{busy=false}
        }
    },modifier=modifier.height(54.dp),enabled=!busy,shape=RoundedCornerShape(16.dp),border=BorderStroke(1.dp,C114Border),colors=ButtonDefaults.outlinedButtonColors(containerColor=Color.White,contentColor=C114Ink)){
        Surface(shape=CircleShape,color=Color.White,border=BorderStroke(1.dp,C114Border),modifier=Modifier.size(25.dp)){Box(contentAlignment=Alignment.Center){Text("G",color=Color(0xFF4285F4),fontWeight=FontWeight.ExtraBold,fontSize=14.sp)}}
        Spacer(Modifier.width(10.dp));Text(if(busy)"Se conectează..." else label,fontWeight=FontWeight.Bold)
    }
}
'''
s=s[:a]+google+s[b:]

old='''lines.forEach{line->Row(verticalAlignment=Alignment.CenterVertically){AsyncImage(line.product.imageUrl,line.product.name,Modifier.size(42.dp).clip(RoundedCornerShape(9.dp)).background(Color.White).padding(3.dp),contentScale=ContentScale.Fit);Spacer(Modifier.width(8.dp));Text("${line.quantity} × ${line.product.name}",Modifier.weight(1f),fontSize=10.sp,maxLines=1,overflow=TextOverflow.Ellipsis,color=C114Ink);unitRonV114(line.product)?.let{Text(moneyV114(it*line.quantity),fontSize=10.sp,fontWeight=FontWeight.Bold)}};TotalRowsV114(totals,cfg.shipping.title,compact=true)}'''
new='''lines.forEach{line->Row(verticalAlignment=Alignment.CenterVertically){AsyncImage(line.product.imageUrl,line.product.name,Modifier.size(42.dp).clip(RoundedCornerShape(9.dp)).background(Color.White).padding(3.dp),contentScale=ContentScale.Fit);Spacer(Modifier.width(8.dp));Text("${line.quantity} × ${line.product.name}",Modifier.weight(1f),fontSize=10.sp,maxLines=1,overflow=TextOverflow.Ellipsis,color=C114Ink);unitRonV114(line.product)?.let{Text(moneyV114(it*line.quantity),fontSize=10.sp,fontWeight=FontWeight.Bold)}}};HorizontalDivider(color=C114Border);TotalRowsV114(totals,cfg.shipping.title,compact=true)'''
if old not in s: raise SystemExit('Checkout summary anchor missing')
s=s.replace(old,new,1)

old=''';if(mode=="login")GoogleButtonV114(clientId=cfg.googleClientId,api=api,session=session,onSuccess={r->token=r.accessToken;email=r.customer?.email.orEmpty().ifBlank{email};msg="Autentificare Google reușită."},onError={msg=it},modifier=Modifier.fillMaxWidth());if(msg.isNotBlank())'''
new=''';GoogleButtonV114(clientId=cfg.googleClientId,api=api,session=session,onSuccess={r->token=r.accessToken;email=r.customer?.email.orEmpty().ifBlank{email};msg="Autentificare Google reușită."},onError={msg=it},modifier=Modifier.fillMaxWidth(),label=if(mode=="login")"Continuă cu Google" else "Înscrie-te cu Google");if(msg.isNotBlank())'''
if old not in s: raise SystemExit('Account Google anchor missing')
s=s.replace(old,new,1)

start=s.index('        }else{',s.index('fun AccountV114'))
end=s.index('            item{Box(Modifier.padding(start=14.dp,end=14.dp,top=3.dp)){OutlinedButton(onClick={session.clear();token=null;orders=emptyList();msg=""}',start)
replacement='''        }else{
            var panel by remember{mutableStateOf("dashboard")}
            item{Box(Modifier.padding(horizontal=14.dp)){ElevatedCard(shape=RoundedCornerShape(26.dp),colors=CardDefaults.elevatedCardColors(containerColor=C114Ink)){Column(Modifier.fillMaxWidth().padding(20.dp),verticalArrangement=Arrangement.spacedBy(7.dp)){Text("AUTOID ACCOUNT",fontSize=9.sp,fontWeight=FontWeight.ExtraBold,color=Color(0xFFFDBA8C));Text(session.customerEmail.ifBlank{email},fontSize=19.sp,fontWeight=FontWeight.ExtraBold,color=Color.White);Text("Professional Solutions",fontSize=10.sp,color=Color(0xFF98A2B3))}}}}
            item{Box(Modifier.padding(horizontal=14.dp)){ElevatedCard(shape=RoundedCornerShape(22.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Column(Modifier.fillMaxWidth().padding(8.dp)){listOf(
                Triple("dashboard","Panou control",Icons.Default.Dashboard),Triple("orders","Comenzi",Icons.Default.ReceiptLong),Triple("details","Detalii cont",Icons.Default.ManageAccounts),Triple("addresses","Adrese Facturare / Livrare",Icons.Default.HomeWork),Triple("payments","Metode de plată",Icons.Default.CreditCard),Triple("preferences","Listă cu preferințe",Icons.Default.Tune)
            ).forEach{(id,label,icon)->val active=panel==id;Row(Modifier.fillMaxWidth().background(if(active)C114OrangeSoft else Color.Transparent,RoundedCornerShape(14.dp)).clickable{panel=id}.padding(horizontal=12.dp,vertical=12.dp),verticalAlignment=Alignment.CenterVertically){Icon(icon,null,tint=if(active)AutoIdOrange else C114Muted,modifier=Modifier.size(19.dp));Spacer(Modifier.width(10.dp));Text(label,Modifier.weight(1f),fontWeight=if(active)FontWeight.ExtraBold else FontWeight.SemiBold,color=C114Ink,fontSize=12.sp);Icon(Icons.Default.ChevronRight,null,tint=C114Muted,modifier=Modifier.size(18.dp))}}}}}}
            when(panel){
                "dashboard"->item{Box(Modifier.padding(horizontal=14.dp)){Row(horizontalArrangement=Arrangement.spacedBy(10.dp)){ElevatedCard(onClick={panel="orders"},modifier=Modifier.weight(1f),shape=RoundedCornerShape(18.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Column(Modifier.padding(15.dp)){Icon(Icons.Default.ReceiptLong,null,tint=AutoIdOrange);Text(orders.size.toString(),fontSize=22.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text("Comenzi",fontSize=10.sp,color=C114Muted)}};ElevatedCard(onClick=onFavorites,modifier=Modifier.weight(1f),shape=RoundedCornerShape(18.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Column(Modifier.padding(15.dp)){Icon(Icons.Default.FavoriteBorder,null,tint=AutoIdOrange);Text(commerce.wishlistIds().size.toString(),fontSize=22.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text("Favorite",fontSize=10.sp,color=C114Muted)}}}}}
                "orders"->{item{Text("Comenzi",Modifier.padding(horizontal=16.dp),fontSize=18.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink)};if(orders.isEmpty())item{Box(Modifier.padding(horizontal=14.dp)){Surface(shape=RoundedCornerShape(18.dp),color=Color.White){Text("Nu ai încă comenzi disponibile.",Modifier.fillMaxWidth().padding(17.dp),color=C114Muted,fontSize=11.sp)}}}else items(orders,key={it.id}){o->Box(Modifier.padding(horizontal=14.dp)){ElevatedCard(shape=RoundedCornerShape(18.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Row(Modifier.fillMaxWidth().padding(15.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.Inventory2,null,tint=AutoIdOrange);Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)){Text("Comanda #${o.number}",fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(o.dateCreated,fontSize=9.sp,color=C114Muted)};Column(horizontalAlignment=Alignment.End){Text(o.status,fontSize=9.sp,fontWeight=FontWeight.Bold,color=C114Good);Text(o.total,fontWeight=FontWeight.ExtraBold,color=C114Ink,fontSize=12.sp)}}}}}}
                "details"->item{Box(Modifier.padding(horizontal=14.dp)){SectionV114(Icons.Default.ManageAccounts,"Detalii cont","Gestionarea datelor contului"){Text(session.customerEmail,fontWeight=FontWeight.Bold,color=C114Ink);Text("Datele sunt sincronizate cu WooCommerce.",fontSize=11.sp,color=C114Muted)}}}
                "addresses"->item{Box(Modifier.padding(horizontal=14.dp)){SectionV114(Icons.Default.HomeWork,"Adrese Facturare / Livrare","Cont WooCommerce"){Text("Checkout-ul folosește separat adresa de facturare și livrare. Managementul complet al adreselor este pregătit în API v1.1.6.",fontSize=11.sp,color=C114Muted)}}}
                "payments"->item{Box(Modifier.padding(horizontal=14.dp)){SectionV114(Icons.Default.CreditCard,"Metode de plată","Cont WooCommerce"){Text("Metodele salvate vor fi afișate aici odată cu activarea plății native.",fontSize=11.sp,color=C114Muted)}}}
                "preferences"->item{Box(Modifier.padding(horizontal=14.dp)){SectionV114(Icons.Default.Tune,"Listă cu preferințe","Google UMP / Consent Mode"){Text("Analytics și tracking rămân dezactivate până la integrarea sistemului nativ de consimțământ.",fontSize=11.sp,color=C114Muted);listOf("Analytics","Personalizare","Publicitate").forEach{label->Row(Modifier.fillMaxWidth().padding(vertical=3.dp),verticalAlignment=Alignment.CenterVertically){Text(label,Modifier.weight(1f),fontWeight=FontWeight.SemiBold,color=C114Ink);Switch(false,{},enabled=false)}}}}}
            }
'''
s=s[:start]+replacement+s[end:]
UI.write_text(s)
print('Applied readable Android v1.0.15: Credential Manager Google, single checkout totals, signup Google and new account menu')
