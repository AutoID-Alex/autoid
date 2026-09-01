from pathlib import Path
ROOT=Path('.')
APP=ROOT/'android-v0.1/app'; SRC=APP/'src/main/java/ro/autoid/app'
GRADLE=APP/'build.gradle.kts'; API=SRC/'data/AutoIdApi.kt'; MANIFEST=APP/'src/main/AndroidManifest.xml'; V114=SRC/'V114CommerceUx.kt'; TARGET=SRC/'V120OrderDetail.kt'; TEMPLATE=ROOT/'ci/v120/V120OrderDetail.kt'

def must(s,old,new,label):
    if old not in s: raise SystemExit(label+' anchor missing')
    return s.replace(old,new,1)

s=GRADLE.read_text(); s=must(s,'versionCode = 12200','versionCode = 12300','versionCode'); s=must(s,'versionName = "1.0.19"','versionName = "1.0.20"','versionName'); GRADLE.write_text(s)
s=API.read_text(); s=must(s,'AutoID-Android/1.0.19','AutoID-Android/1.0.20','user agent'); API.write_text(s)
s=MANIFEST.read_text(); s=must(s,'<activity android:name=".MainActivity" android:exported="true">','<activity android:name=".MainActivity" android:exported="true" android:configChanges="orientation|screenSize|screenLayout|smallestScreenSize|keyboardHidden">','rotation config'); MANIFEST.write_text(s)
if not TEMPLATE.exists(): raise SystemExit('V120 order detail template missing')
order_source=TEMPLATE.read_text()
order_source=must(order_source,'@Composable\nfun OrderDetailV120(','@OptIn(ExperimentalMaterial3Api::class)\n@Composable\nfun OrderDetailV120(','Material3 TopAppBar opt-in')
TARGET.write_text(order_source)

s=V114.read_text()
s=must(s,'var panel by remember{mutableStateOf("dashboard")};val accountScope=rememberCoroutineScope();val uriHandler=LocalUriHandler.current','var panel by remember{mutableStateOf("dashboard")};var selectedOrderId by remember{mutableStateOf<Long?>(null)};val accountScope=rememberCoroutineScope();val uriHandler=LocalUriHandler.current','account route state')
anchor='''    LaunchedEffect(busy){if(busy){if(mode=="register")'''
route='''    selectedOrderId?.let{id->val t=token;if(t!=null){OrderDetailV120(api,t,id,onBack={selectedOrderId=null;panel="orders"});return}}\n    LaunchedEffect(busy){if(busy){if(mode=="register")'''
s=must(s,anchor,route,'order route entry')
s=must(s,'LatestOrderCardV119(o,onTrack={if(o.trackingUrl.isNotBlank())uriHandler.openUri(o.trackingUrl)},onView={panel="orders"})','LatestOrderCardV119(o,onTrack={if(o.trackingUrl.isNotBlank())uriHandler.openUri(o.trackingUrl)},onView={selectedOrderId=o.id})','dashboard order detail')
old='''                "orders"->{item{Text("Comenzi",Modifier.padding(horizontal=16.dp),fontSize=18.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink)};if(orders.isEmpty())item{Box(Modifier.padding(horizontal=14.dp)){Surface(shape=RoundedCornerShape(18.dp),color=Color.White){Text("Nu ai încă comenzi disponibile.",Modifier.fillMaxWidth().padding(17.dp),color=C114Muted,fontSize=11.sp)}}}else items(orders,key={it.id}){o->Box(Modifier.padding(horizontal=14.dp)){ElevatedCard(shape=RoundedCornerShape(18.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Row(Modifier.fillMaxWidth().padding(15.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.Inventory2,null,tint=AutoIdOrange);Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)){Text("Comanda #${o.number}",fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(o.dateCreated,fontSize=9.sp,color=C114Muted)};Column(horizontalAlignment=Alignment.End){Text(o.status,fontSize=9.sp,fontWeight=FontWeight.Bold,color=C114Good);Text(o.total,fontWeight=FontWeight.ExtraBold,color=C114Ink,fontSize=12.sp)}}}}}}'''
new='''                "orders"->{item{Text("Comenzi",Modifier.padding(horizontal=16.dp),fontSize=18.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink)};if(orders.isEmpty())item{Box(Modifier.padding(horizontal=14.dp)){Surface(shape=RoundedCornerShape(18.dp),color=Color.White){Text("Nu ai încă comenzi disponibile.",Modifier.fillMaxWidth().padding(17.dp),color=C114Muted,fontSize=11.sp)}}}else items(orders,key={it.id}){o->Box(Modifier.padding(horizontal=14.dp)){ElevatedCard(modifier=Modifier.fillMaxWidth().clickable{selectedOrderId=o.id},shape=RoundedCornerShape(18.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){Row(Modifier.fillMaxWidth().padding(15.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.Inventory2,null,tint=AutoIdOrange);Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)){Text("Comanda #${o.number}",fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(o.dateCreated,fontSize=9.sp,color=C114Muted);if(o.trackingNumber.isNotBlank())Text("GLS · AWB ${o.trackingNumber}",fontSize=9.sp,color=C114Muted)};Column(horizontalAlignment=Alignment.End){Text(o.status,fontSize=9.sp,fontWeight=FontWeight.Bold,color=C114Good);Text(o.total,fontWeight=FontWeight.ExtraBold,color=C114Ink,fontSize=12.sp);Icon(Icons.Default.ChevronRight,null,tint=C114Muted,modifier=Modifier.size(18.dp))}}}}}}'''
s=must(s,old,new,'orders clickable cards')
V114.write_text(s)
print('Applied Android v1.0.20: rotation persistence and native vezi-comanda/{order_id}/ route')
