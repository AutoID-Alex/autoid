#!/usr/bin/env python3
"""RC7.1: restore RC6 privacy/consent behavior and fix /me/orders runtime fatal."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app'
ACCOUNT=APP/'V135AccountUx.kt'
PLUGIN=ROOT/'wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'

s=ACCOUNT.read_text()
if 'import androidx.compose.ui.platform.LocalContext' not in s:
    s=s.replace('import androidx.compose.ui.platform.LocalUriHandler\n','import androidx.compose.ui.platform.LocalContext\nimport androidx.compose.ui.platform.LocalUriHandler\n',1)

old='''@Composable private fun AccountPrivacyV135(onBack:()->Unit){val uri=LocalUriHandler.current;BackHandler(onBack=onBack);Column(Modifier.fillMaxSize().background(A135Soft)){AccountBackV135("Confidențialitate și consimțământ",onBack);ElevatedCard(Modifier.fillMaxWidth().padding(14.dp),shape=RoundedCornerShape(14.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){Icon(Icons.Default.PrivacyTip,null,tint=AutoIdOrange);Text("Confidențialitate și consimțământ",fontWeight=FontWeight.ExtraBold,color=A135Ink);Text("Poți consulta politica AutoID și opțiunile de confidențialitate asociate contului tău.",fontSize=11.sp,color=A135Muted);OutlinedButton(onClick={uri.openUri("https://www.autoid.ro/politica-de-confidentialitate/")}){Text("Politica de confidențialitate")}}}}
}'''
new='''@Composable private fun AccountPrivacyV135(api:AutoIdApi,session:SessionStore,token:String,onBack:()->Unit){
    val context=LocalContext.current
    val store=remember{PrivacyConsentStoreV128(context)}
    var prefs by remember{mutableStateOf(store.get())}
    var busy by remember{mutableStateOf(false)}
    var msg by remember{mutableStateOf("")}
    val scope=rememberCoroutineScope()
    BackHandler(onBack=onBack)
    LaunchedEffect(token){
        runCatching{withContext(Dispatchers.IO){api.privacyV128(token)}}.onSuccess{
            prefs=it
            store.save(it)
            FirebaseBootstrapV128.applyConsent(context,api,session,it)
        }
    }
    LazyColumn(Modifier.fillMaxSize().background(A135Soft),contentPadding=PaddingValues(bottom=24.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
        item{AccountBackV135("Confidențialitate și consimțământ",onBack)}
        item{ElevatedCard(Modifier.fillMaxWidth().padding(horizontal=14.dp),shape=RoundedCornerShape(14.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){
            Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){
                Icon(Icons.Default.PrivacyTip,null,tint=AutoIdOrange)
                Text("Confidențialitate și consimțământ",fontWeight=FontWeight.ExtraBold,color=A135Ink)
                Text("Control nativ · modificabil oricând",fontSize=10.sp,color=A135Muted)
                Text("Necesare",fontWeight=FontWeight.ExtraBold,color=A135Ink)
                Text("Funcții esențiale pentru cont, coș, checkout și securitate. Sunt întotdeauna active.",fontSize=10.sp,color=A135Muted)
                Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){Text("Necesare",Modifier.weight(1f),fontWeight=FontWeight.SemiBold,color=A135Ink);Switch(true,{},enabled=false)}
                HorizontalDivider(color=A135Border)
                Text("Preferințe opționale",fontWeight=FontWeight.ExtraBold,color=A135Ink)
                PrivacyPrefRowV135("Actualizări despre comenzi","AWB, status, finalizare și invitația de review.",prefs.transactionalNotifications){prefs=prefs.copy(transactionalNotifications=it)}
                PrivacyPrefRowV135("Analytics","Măsurarea utilizării aplicației. Dezactivat implicit.",prefs.analytics){prefs=prefs.copy(analytics=it)}
                PrivacyPrefRowV135("Personalizare","Conținut și recomandări adaptate. Dezactivat implicit.",prefs.personalization){prefs=prefs.copy(personalization=it)}
                PrivacyPrefRowV135("Marketing & promoții","Notificări comerciale și campanii. Dezactivat implicit.",prefs.marketing){prefs=prefs.copy(marketing=it)}
                Text("Poți retrage oricând consimțământul. AutoID nu activează Analytics sau Marketing înainte de acord.",fontSize=9.sp,color=A135Muted)
                Button(onClick={
                    store.save(prefs)
                    FirebaseBootstrapV128.applyConsent(context,api,session,prefs)
                    scope.launch{
                        busy=true
                        runCatching{withContext(Dispatchers.IO){api.savePrivacyV128(token,prefs)}}
                            .onSuccess{prefs=it;store.save(it);msg="Preferințele de confidențialitate au fost salvate."}
                            .onFailure{msg=it.message?:"Preferințele au fost salvate local."}
                        busy=false
                    }
                },enabled=!busy,modifier=Modifier.fillMaxWidth()){
                    Text(if(busy)"Se salvează..." else "Salvează preferințele")
                }
                if(msg.isNotBlank())Text(msg,fontSize=10.sp,color=A135Muted)
            }
        }}
    }
}

@Composable private fun PrivacyPrefRowV135(title:String,desc:String,checked:Boolean,onChecked:(Boolean)->Unit){
    Row(Modifier.fillMaxWidth().padding(vertical=7.dp),verticalAlignment=Alignment.CenterVertically){
        Column(Modifier.weight(1f)){Text(title,fontWeight=FontWeight.SemiBold,color=A135Ink,fontSize=12.sp);Text(desc,fontSize=9.sp,color=A135Muted)}
        Switch(checked,onChecked)
    }
}'''
if old not in s:
    raise SystemExit('simplified RC7 privacy page anchor missing')
s=s.replace(old,new,1)

old_call='"privacy"->{AccountPrivacyV135{page="dashboard"};return}'
new_call='"privacy"->{AccountPrivacyV135(api,session,token){page="dashboard"};return}'
if old_call not in s:
    raise SystemExit('privacy navigation anchor missing')
s=s.replace(old_call,new_call,1)

# Restore original FCM unregister-on-logout behavior while keeping RC7 navigation fallback.
if 'val accountContext=LocalContext.current' not in s:
    s=s.replace('var loggedOut by remember{mutableStateOf(false)}','val accountContext=LocalContext.current\n    var loggedOut by remember{mutableStateOf(false)}',1)
s=s.replace('OutlinedButton(onClick={session.clear();loggedOut=true}', 'OutlinedButton(onClick={FirebaseBootstrapV128.unregisterForLogout(accountContext,api,token);session.clear();loggedOut=true}',1)

for required in ['Actualizări despre comenzi','Analytics','Personalizare','Marketing & promoții','api.savePrivacyV128','FirebaseBootstrapV128.applyConsent','PrivacyConsentStoreV128']:
    if required not in s: raise SystemExit('privacy restore missing '+required)
ACCOUNT.write_text(s)

php=PLUGIN.read_text()
if 'self::order_tracking_payload_v119($o)' not in php:
    raise SystemExit('orders runtime fatal anchor missing')
php=php.replace('self::order_tracking_payload_v119($o)','self::order_tracking_payload($o)',1)
for oldv,newv in [
    (' * Version: 1.1.27',' * Version: 1.1.28'),
    ("'version'=>'1.1.27',","'version'=>'1.1.28',"),
    ('AutoID-Mobile-WordPress/1.1.27','AutoID-Mobile-WordPress/1.1.28'),
]:
    php=php.replace(oldv,newv)
if 'order_tracking_payload_v119' in php: raise SystemExit('undefined order helper still present')
if 'private static function order_tracking_payload($order)' not in php: raise SystemExit('real order helper missing')
PLUGIN.write_text(php)

g=GRADLE.read_text()
if 'versionCode = 13303' not in g: raise SystemExit('RC7 version code anchor missing')
g=g.replace('versionCode = 13303','versionCode = 13304',1)
GRADLE.write_text(g)

print('RC7.1 restored RC6 privacy controls and fixed /me/orders fatal; plugin 1.1.28, code 13304')
