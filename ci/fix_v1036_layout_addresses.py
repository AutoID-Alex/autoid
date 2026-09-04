#!/usr/bin/env python3
"""RC7.2: remove duplicate top insets, add account dashboard header and rebuild address UX."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'android-v0.1/app/src/main/java/ro/autoid/app'
V100=APP/'V100Screens.kt'
ACCOUNT=APP/'V135AccountUx.kt'
GRADLE=ROOT/'android-v0.1/app/build.gradle.kts'

v=V100.read_text()
loading_keep='.background(Color.White).statusBarsPadding()'
drawer_keep='.padding(18.dp).statusBarsPadding()'
if loading_keep not in v:
    raise SystemExit('RC7.2 loading status inset anchor missing')
if drawer_keep not in v:
    raise SystemExit('RC7.2 drawer status inset anchor missing')

v=v.replace(loading_keep,'.background(Color.White).__AUTOID_KEEP_STATUS_V136__()',1)
v=v.replace(drawer_keep,'.padding(18.dp).__AUTOID_KEEP_STATUS_V136__()',1)
removed=v.count('.statusBarsPadding()')
if removed < 4:
    raise SystemExit(f'RC7.2 expected duplicate status inset on at least 4 Scaffold screens, found {removed}')
v=v.replace('.statusBarsPadding()','')
v=v.replace('.background(Color.White).__AUTOID_KEEP_STATUS_V136__()','.background(Color.White).statusBarsPadding()')
v=v.replace('.padding(18.dp).__AUTOID_KEEP_STATUS_V136__()','.padding(18.dp).statusBarsPadding()')
if '__AUTOID_KEEP_STATUS_V136__' in v:
    raise SystemExit('RC7.2 status inset sentinel remains')
V100.write_text(v)

a=ACCOUNT.read_text()
for anchor, imp in [
    ('import androidx.compose.foundation.background\n','import androidx.compose.foundation.Image\n'),
    ('import androidx.compose.ui.graphics.Color\n','import androidx.compose.ui.layout.ContentScale\nimport androidx.compose.ui.res.painterResource\n'),
]:
    if imp.strip() not in a:
        if anchor not in a: raise SystemExit('RC7.2 account import anchor missing: '+anchor.strip())
        a=a.replace(anchor,anchor+imp,1)

header='''@Composable private fun AccountDashboardHeaderV136(commerce:CommerceStore,onRfq:()->Unit,onNotifications:()->Unit,onCart:()->Unit){
    Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
        Image(painterResource(R.drawable.autoid_logo_transparent),"AutoID",Modifier.width(128.dp).height(46.dp),contentScale=ContentScale.Fit)
        Spacer(Modifier.weight(1f))
        RfqHeaderActionV133(onRfq)
        IconButton(onClick=onNotifications){BadgedBox(badge={Badge(containerColor=AutoIdOrange){Text("3")}}){Icon(Icons.Default.NotificationsNone,"Notificări",tint=A135Ink)}}
        IconButton(onClick=onCart){BadgedBox(badge={if(commerce.cartCount()>0)Badge(containerColor=AutoIdOrange){Text(commerce.cartCount().toString())}}){Icon(Icons.Default.ShoppingCart,"Coș",tint=A135Ink)}}
    }
}

'''
marker='@Composable fun AccountV135('
if 'AccountDashboardHeaderV136' not in a:
    if marker not in a: raise SystemExit('RC7.2 AccountV135 marker missing')
    a=a.replace(marker,header+marker,1)

hero_anchor='''    LazyColumn(Modifier.fillMaxSize().background(A135Soft),contentPadding=PaddingValues(horizontal=14.dp,vertical=12.dp),verticalArrangement=Arrangement.spacedBy(12.dp)){
        item{ElevatedCard(shape=RoundedCornerShape(12.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color(0xFF111827)))'''
hero_new='''    LazyColumn(Modifier.fillMaxSize().background(A135Soft),contentPadding=PaddingValues(horizontal=14.dp,vertical=8.dp),verticalArrangement=Arrangement.spacedBy(12.dp)){
        item{AccountDashboardHeaderV136(commerce,onFavorites,onNotifications,onCart)}
        item{ElevatedCard(shape=RoundedCornerShape(12.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color(0xFF111827)))'''
if hero_anchor not in a:
    raise SystemExit('RC7.2 account dashboard hero anchor missing')
a=a.replace(hero_anchor,hero_new,1)

start=a.find('@Composable private fun AddressSummaryV135')
end=a.find('@Composable private fun AccountPaymentsV135',start)
if start < 0 or end < 0:
    raise SystemExit('RC7.2 address block boundaries missing')

addresses=r'''@Composable private fun AddressPairReadV136(leftLabel:String,leftValue:String,rightLabel:String,rightValue:String){
    Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(10.dp)){
        Column(Modifier.weight(1f)){Text(leftLabel,fontSize=9.sp,fontWeight=FontWeight.Bold,color=A135Muted);Text(leftValue.ifBlank{"—"},fontSize=12.sp,fontWeight=FontWeight.SemiBold,color=A135Ink)}
        Column(Modifier.weight(1f)){Text(rightLabel,fontSize=9.sp,fontWeight=FontWeight.Bold,color=A135Muted);Text(rightValue.ifBlank{"—"},fontSize=12.sp,fontWeight=FontWeight.SemiBold,color=A135Ink)}
    }
}

@Composable private fun AddressFullReadV136(label:String,value:String,optional:Boolean=false){
    Column(Modifier.fillMaxWidth()){Text(label+(if(optional)" · opțional" else ""),fontSize=9.sp,fontWeight=FontWeight.Bold,color=A135Muted);Text(value.ifBlank{"—"},fontSize=12.sp,fontWeight=FontWeight.SemiBold,color=A135Ink)}
}

@Composable private fun AddressReadBlockV136(title:String,a:AccountAddress){
    Column(Modifier.fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(10.dp)){
        Text(title,fontSize=16.sp,fontWeight=FontWeight.ExtraBold,color=A135Ink)
        AddressPairReadV136("Nume",a.lastName,"Prenume",a.firstName)
        AddressFullReadV136("Strada, nr",a.address1)
        AddressFullReadV136("Linia 2 a adresei (Bloc, Scară, Apartament, alte detalii)",a.address2,true)
        AddressPairReadV136("Localitate",a.city,"Județ",a.state)
        AddressPairReadV136("Cod poștal",a.postcode,"Țară",a.country)
    }
}

@Composable private fun AddressEditBlockV136(title:String,a:AccountAddress,onChange:(AccountAddress)->Unit){
    Column(Modifier.fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(9.dp)){
        Text(title,fontSize=16.sp,fontWeight=FontWeight.ExtraBold,color=A135Ink)
        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){
            OutlinedTextField(a.lastName,{onChange(a.copy(lastName=it))},label={Text("Nume")},modifier=Modifier.weight(1f),singleLine=true)
            OutlinedTextField(a.firstName,{onChange(a.copy(firstName=it))},label={Text("Prenume")},modifier=Modifier.weight(1f),singleLine=true)
        }
        OutlinedTextField(a.address1,{onChange(a.copy(address1=it))},label={Text("Strada, nr")},modifier=Modifier.fillMaxWidth(),singleLine=true)
        OutlinedTextField(a.address2,{onChange(a.copy(address2=it))},label={Text("Linia 2 a adresei")},supportingText={Text("Bloc, Scară, Apartament, alte detalii (opțional)")},modifier=Modifier.fillMaxWidth(),singleLine=true)
        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){
            OutlinedTextField(a.city,{onChange(a.copy(city=it))},label={Text("Localitate")},modifier=Modifier.weight(1f),singleLine=true)
            OutlinedTextField(a.state,{onChange(a.copy(state=it))},label={Text("Județ")},modifier=Modifier.weight(1f),singleLine=true)
        }
        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){
            OutlinedTextField(a.postcode,{onChange(a.copy(postcode=it))},label={Text("Cod poștal")},modifier=Modifier.weight(1f),singleLine=true)
            OutlinedTextField(a.country,{onChange(a.copy(country=it.uppercase().take(2)))},label={Text("Țară")},modifier=Modifier.weight(1f),singleLine=true)
        }
    }
}

@Composable private fun AccountAddressesV135(api:AutoIdApi,token:String,onBack:()->Unit){
    var data by remember{mutableStateOf<AccountAddresses?>(null)}
    var editing by remember{mutableStateOf(false)}
    var billing by remember{mutableStateOf(AccountAddress())}
    var shipping by remember{mutableStateOf(AccountAddress())}
    var vat by remember{mutableStateOf("")}
    var msg by remember{mutableStateOf("")}
    var busy by remember{mutableStateOf(false)}
    val scope=rememberCoroutineScope()
    LaunchedEffect(token){
        runCatching{withContext(Dispatchers.IO){api.accountAddresses(token)}}
            .onSuccess{data=it;billing=it.billing;shipping=it.shipping;vat=it.vatNumber}
            .onFailure{msg=it.message?:"Adresele nu au putut fi încărcate."}
    }
    BackHandler(onBack=onBack)
    LazyColumn(Modifier.fillMaxSize().background(A135Soft),contentPadding=PaddingValues(bottom=24.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
        item{AccountBackV135("Adrese Facturare / Livrare",onBack)}
        item{ElevatedCard(Modifier.fillMaxWidth().padding(horizontal=14.dp),shape=RoundedCornerShape(14.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){
            Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(14.dp)){
                if(data==null&&msg.isBlank())CircularProgressIndicator(color=AutoIdOrange)
                else if(!editing){
                    AddressReadBlockV136("Adresa Livrare",shipping)
                    HorizontalDivider(color=A135Border)
                    AddressReadBlockV136("Adresa Facturare",billing)
                    HorizontalDivider(color=A135Border)
                    Text("Date facturare",fontSize=16.sp,fontWeight=FontWeight.ExtraBold,color=A135Ink)
                    AddressPairReadV136("Companie (opțional)",billing.company,"Cod TVA / CUI (opțional)",vat)
                    OutlinedButton(onClick={editing=true;msg=""},modifier=Modifier.fillMaxWidth()){Icon(Icons.Default.Edit,null);Spacer(Modifier.width(6.dp));Text("Editează adresele")}
                }else{
                    AddressEditBlockV136("Adresa Livrare",shipping){shipping=it}
                    HorizontalDivider(color=A135Border)
                    AddressEditBlockV136("Adresa Facturare",billing){billing=it}
                    HorizontalDivider(color=A135Border)
                    Text("Date facturare",fontSize=16.sp,fontWeight=FontWeight.ExtraBold,color=A135Ink)
                    Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){
                        OutlinedTextField(billing.company,{billing=billing.copy(company=it)},label={Text("Companie (opțional)")},modifier=Modifier.weight(1f),singleLine=true)
                        OutlinedTextField(vat,{vat=it},label={Text("Cod TVA / CUI (opțional)")},modifier=Modifier.weight(1f),singleLine=true)
                    }
                    Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){
                        OutlinedButton(onClick={editing=false;data?.let{billing=it.billing;shipping=it.shipping;vat=it.vatNumber};msg=""},modifier=Modifier.weight(1f),enabled=!busy){Text("Renunță")}
                        Button(onClick={scope.launch{
                            busy=true;msg=""
                            runCatching{withContext(Dispatchers.IO){api.saveAccountAddresses(token,AccountAddresses(billing,shipping,vat))}}
                                .onSuccess{data=it;billing=it.billing;shipping=it.shipping;vat=it.vatNumber;editing=false;msg="Adrese salvate."}
                                .onFailure{msg=it.message?:"Salvarea a eșuat."}
                            busy=false
                        }},modifier=Modifier.weight(1f),enabled=!busy){Text(if(busy)"Se salvează..." else "Salvează")}
                    }
                }
                if(msg.isNotBlank())Text(msg,fontSize=10.sp,color=if(msg=="Adrese salvate.")A135Good else MaterialTheme.colorScheme.error)
            }
        }}
    }
}

'''
a=a[:start]+addresses+a[end:]

for required in [
    'AccountDashboardHeaderV136','Adresa Livrare','Adresa Facturare','Date facturare',
    'Linia 2 a adresei','Bloc, Scară, Apartament, alte detalii (opțional)',
    'Cod TVA / CUI (opțional)','billing.copy(company=it)','shipping=it'
]:
    if required not in a: raise SystemExit('RC7.2 account/address contract missing '+required)
ACCOUNT.write_text(a)

g=GRADLE.read_text()
if 'versionCode = 13304' not in g:
    raise SystemExit('RC7.2 version code anchor missing')
g=g.replace('versionCode = 13304','versionCode = 13305',1)
GRADLE.write_text(g)

print(f'RC7.2 fixed duplicate top inset on {removed} Scaffold screens, added account header, rebuilt addresses; code 13305')
