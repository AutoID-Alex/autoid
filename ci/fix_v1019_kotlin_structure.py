from pathlib import Path
p=Path('android-v0.1/app/src/main/java/ro/autoid/app/V114CommerceUx.kt')
s=p.read_text()

old='''            item{SectionV114(Icons.Default.LocalShipping,"Livrare","Alege cum primești comanda"){Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(9.dp)){listOf("delivery" to "Livrare","pickup" to "Ridicare din Depozit").forEach{(id,label)->val selected=deliveryMode==id;OutlinedCard(modifier=Modifier.weight(1f).clickable{if(id=="pickup"&&deliveryMode!="pickup"){if(bf.isBlank()){bf=sf;bl=sl;ba1=sa1;ba2=sa2;bcity=scity;bstate=sstate;bpost=spost;bcountry=scountry};sameBilling=false};deliveryMode=id},shape=RoundedCornerShape(16.dp),colors=CardDefaults.outlinedCardColors(containerColor=if(selected)C114OrangeSoft else Color.White),border=BorderStroke(if(selected)2.dp else 1.dp,if(selected)AutoIdOrange else C114Border)){Column(Modifier.fillMaxWidth().padding(12.dp),horizontalAlignment=Alignment.CenterHorizontally){Icon(if(id=="delivery")Icons.Default.LocalShipping else Icons.Default.Storefront,null,tint=if(selected)AutoIdOrange else C114Muted);Spacer(Modifier.height(5.dp));Text(label,fontSize=10.sp,fontWeight=FontWeight.ExtraBold,color=C114Ink,textAlign=TextAlign.Center)}}};};if(deliveryMode=="pickup")Text("Ridicarea din depozit este gratuită. Primești confirmare când comanda este pregătită.",fontSize=10.sp,color=C114Muted)}}'''
new='''            item {
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
            }'''
if old not in s:
    raise SystemExit('delivery UI compact block missing')
s=s.replace(old,new,1)

start=s.find('@Composable\nprivate fun LatestOrderCardV119')
end=s.find('@Composable\nfun AccountV114',start)
if start<0 or end<0:
    raise SystemExit('LatestOrderCardV119 block missing')
helper='''@Composable
private fun LatestOrderCardV119(o: Order, onTrack: () -> Unit, onView: () -> Unit) {
    val terminal = o.statusCode in listOf("cancelled", "failed", "refunded")
    val stage = when {
        terminal -> 0
        o.statusCode == "completed" -> 3
        o.trackingNumber.isNotBlank() -> 2
        else -> 1
    }
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
                        o.status,
                        modifier = Modifier.fillMaxWidth().padding(10.dp),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.error
                    )
                }
            } else {
                LinearProgressIndicator(
                    progress = { stage / 3f },
                    modifier = Modifier.fillMaxWidth().height(6.dp).clip(RoundedCornerShape(50)),
                    color = AutoIdOrange,
                    trackColor = Color(0xFFEFF1F4)
                )
                Row(Modifier.fillMaxWidth()) {
                    Text("Procesare", Modifier.weight(1f), fontSize = 8.sp, color = C114Muted)
                    Text("Livrare", Modifier.weight(1f), fontSize = 8.sp, textAlign = TextAlign.Center, color = C114Muted)
                    Text("Comanda finalizată", Modifier.weight(1f), fontSize = 8.sp, textAlign = TextAlign.End, color = C114Muted)
                }
                if (o.trackingNumber.isNotBlank()) {
                    val carrierLabel = if (o.carrier.isBlank()) "GLS" else o.carrier
                    Text("$carrierLabel · AWB ${o.trackingNumber}", fontSize = 9.sp, color = C114Muted)
                }
            }
        }
    }
}

'''
s=s[:start]+helper+s[end:]
p.write_text(s)
print('Normalized v1.0.19 Kotlin structure for Compose compiler')
