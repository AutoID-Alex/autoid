from pathlib import Path

ROOT=Path('.')
APP=ROOT/'android-v0.1/app'
SRC=APP/'src/main/java/ro/autoid/app'
GRADLE=APP/'build.gradle.kts'
API=SRC/'data/AutoIdApi.kt'
V114=SRC/'V114CommerceUx.kt'
V120=SRC/'V120OrderDetail.kt'
STATUS_TEMPLATE=ROOT/'ci/v121/V121OrderStatus.kt'
STATUS_TARGET=SRC/'V121OrderStatus.kt'

def must(s,old,new,label):
    if old not in s:
        raise SystemExit(label+' anchor missing')
    return s.replace(old,new,1)

# Version bump.
s=GRADLE.read_text()
s=must(s,'versionCode = 12300','versionCode = 12400','versionCode')
s=must(s,'versionName = "1.0.20"','versionName = "1.0.21"','versionName')
GRADLE.write_text(s)

s=API.read_text()
s=must(s,'AutoID-Android/1.0.20','AutoID-Android/1.0.21','user agent')
API.write_text(s)

if not STATUS_TEMPLATE.exists():
    raise SystemExit('V121 shared status template missing')
STATUS_TARGET.write_text(STATUS_TEMPLATE.read_text())

# Unify dashboard latest-order progress bar and visual status.
s=V114.read_text()
old_helper='''@Composable
private fun LatestOrderCardV119(o:Order,onTrack:()->Unit,onView:()->Unit){
    val terminal=o.statusCode in listOf("cancelled","failed","refunded")
    val stage=when{terminal->0;o.statusCode=="completed"->3;o.trackingNumber.isNotBlank()->2;else->1}
    ElevatedCard(shape=RoundedCornerShape(20.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)){Column(Modifier.fillMaxWidth().padding(16.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){Text("ULTIMA COMANDĂ",fontSize=9.sp,fontWeight=FontWeight.ExtraBold,color=C114Muted);Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text("Comanda: #${o.number}",fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(o.dateCreated,fontSize=9.sp,color=C114Muted)};OutlinedButton(onClick=onTrack,enabled=o.trackingUrl.isNotBlank(),contentPadding=PaddingValues(horizontal=9.dp,vertical=0.dp)){Text("Urmărește",fontSize=9.sp,fontWeight=FontWeight.Bold)};Spacer(Modifier.width(5.dp));Button(onClick=onView,contentPadding=PaddingValues(horizontal=9.dp,vertical=0.dp)){Text("Vezi comanda",fontSize=9.sp,fontWeight=FontWeight.Bold)}};Text("Total: ${o.total}",fontSize=14.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text("incl. TVA",fontSize=9.sp,color=C114Muted);if(terminal){Surface(shape=RoundedCornerShape(12.dp),color=Color(0xFFFFF1F0)){Text(o.status,Modifier.fillMaxWidth().padding(10.dp),fontSize=10.sp,fontWeight=FontWeight.Bold,color=MaterialTheme.colorScheme.error)}}else{LinearProgressIndicator(progress={stage/3f},modifier=Modifier.fillMaxWidth().height(6.dp).clip(RoundedCornerShape(50)),color=AutoIdOrange,trackColor=Color(0xFFEFF1F4));Row(Modifier.fillMaxWidth()){Text("Procesare",Modifier.weight(1f),fontSize=8.sp,color=C114Muted);Text("Livrare",Modifier.weight(1f),fontSize=8.sp,textAlign=TextAlign.Center,color=C114Muted);Text("Comanda finalizată",Modifier.weight(1f),fontSize=8.sp,textAlign=TextAlign.End,color=C114Muted)};if(o.trackingNumber.isNotBlank())Text("${o.carrier.ifBlank{"GLS"}} · AWB ${o.trackingNumber}",fontSize=9.sp,color=C114Muted)}}}}
}
'''
new_helper='''@Composable
private fun LatestOrderCardV119(o:Order,onTrack:()->Unit,onView:()->Unit){
    val terminal=orderIsTerminalV121(o.statusCode)
    val visualStatus=orderDisplayStatusV121(o.statusCode,o.trackingNumber,o.status)
    ElevatedCard(shape=RoundedCornerShape(20.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White),elevation=CardDefaults.elevatedCardElevation(defaultElevation=1.dp)){Column(Modifier.fillMaxWidth().padding(16.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){Text("ULTIMA COMANDĂ",fontSize=9.sp,fontWeight=FontWeight.ExtraBold,color=C114Muted);Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text("Comanda: #${o.number}",fontWeight=FontWeight.ExtraBold,color=C114Ink);Text(o.dateCreated,fontSize=9.sp,color=C114Muted);Text(visualStatus,fontSize=10.sp,fontWeight=FontWeight.ExtraBold,color=if(terminal)MaterialTheme.colorScheme.error else C114Good)};OutlinedButton(onClick=onTrack,enabled=o.trackingUrl.isNotBlank(),contentPadding=PaddingValues(horizontal=9.dp,vertical=0.dp)){Text("Urmărește",fontSize=9.sp,fontWeight=FontWeight.Bold)};Spacer(Modifier.width(5.dp));Button(onClick=onView,contentPadding=PaddingValues(horizontal=9.dp,vertical=0.dp)){Text("Vezi comanda",fontSize=9.sp,fontWeight=FontWeight.Bold)}};Text("Total: ${o.total}",fontSize=14.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink);Text("incl. TVA",fontSize=9.sp,color=C114Muted);if(terminal){Surface(shape=RoundedCornerShape(12.dp),color=Color(0xFFFFF1F0)){Text(visualStatus,Modifier.fillMaxWidth().padding(10.dp),fontSize=10.sp,fontWeight=FontWeight.Bold,color=MaterialTheme.colorScheme.error)}}else{OrderStatusProgressV121(o.statusCode,o.trackingNumber);if(o.trackingNumber.isNotBlank())Text("${o.carrier.ifBlank{"GLS"}} · AWB ${o.trackingNumber}",fontSize=9.sp,color=C114Muted)}}}}
}
'''
s=must(s,old_helper,new_helper,'latest order status helper')

# Orders list: AWB must visually override processing -> Livrare.
old_list='''Column(horizontalAlignment=Alignment.End){Text(o.status,fontSize=9.sp,fontWeight=FontWeight.Bold,color=C114Good);Text(o.total,fontWeight=FontWeight.ExtraBold,color=C114Ink,fontSize=12.sp);Icon(Icons.Default.ChevronRight,null,tint=C114Muted,modifier=Modifier.size(18.dp))}'''
new_list='''Column(horizontalAlignment=Alignment.End){val visualStatus=orderDisplayStatusV121(o.statusCode,o.trackingNumber,o.status);Text(visualStatus,fontSize=9.sp,fontWeight=FontWeight.Bold,color=if(orderIsTerminalV121(o.statusCode))MaterialTheme.colorScheme.error else C114Good);Text(o.total,fontWeight=FontWeight.ExtraBold,color=C114Ink,fontSize=12.sp);Icon(Icons.Default.ChevronRight,null,tint=C114Muted,modifier=Modifier.size(18.dp))}'''
s=must(s,old_list,new_list,'orders list visual status')
V114.write_text(s)

# Order detail: use exactly the same shared status engine and progress component.
s=V120.read_text()
old_status='''@Composable
private fun OrderStatusV120(d:OrderDetail){
    val terminal=d.status in listOf("cancelled","failed","refunded")
    val stage=when{
        terminal->0
        d.status=="completed"->4
        d.trackingNumber.isNotBlank()->3
        d.status in listOf("processing","on-hold")->2
        else->1
    }
    ElevatedCard(shape=RoundedCornerShape(22.dp),colors=CardDefaults.elevatedCardColors(containerColor=Color.White)){
        Column(Modifier.fillMaxWidth().padding(17.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){
            Text("Comanda #${d.number}",fontSize=20.sp,fontWeight=FontWeight.ExtraBold,color=OrderInk)
            Text(d.statusLabel.ifBlank{d.status},fontSize=11.sp,fontWeight=FontWeight.Bold,color=if(terminal)MaterialTheme.colorScheme.error else OrderGood)
            if(terminal){
                Surface(shape=RoundedCornerShape(14.dp),color=Color(0xFFFFF1F0)){
                    Text("Această comandă nu mai este activă.",Modifier.fillMaxWidth().padding(11.dp),fontSize=10.sp,color=MaterialTheme.colorScheme.error)
                }
            }else{
                LinearProgressIndicator(
                    progress={stage/4f},
                    modifier=Modifier.fillMaxWidth().height(7.dp).clip(RoundedCornerShape(50)),
                    color=AutoIdOrange,
                    trackColor=Color(0xFFEFF1F4)
                )
                Row(Modifier.fillMaxWidth()){
                    listOf("Comandă","Confirmată","Pregătire","Livrare").forEachIndexed{i,label->
                        Text(label,Modifier.weight(1f),fontSize=7.sp,textAlign=when(i){0->TextAlign.Start;3->TextAlign.End;else->TextAlign.Center},color=if(i<stage)OrderInk else OrderMuted,fontWeight=if(i<stage)FontWeight.Bold else FontWeight.Normal)
                    }
                }
            }
        }
    }
}
'''
new_status='''@Composable
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
'''
s=must(s,old_status,new_status,'order detail shared status')
V120.write_text(s)

print('Applied Android v1.0.21 unified order status: dashboard, order list and order detail')
