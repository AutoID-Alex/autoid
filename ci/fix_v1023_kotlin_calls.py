from pathlib import Path

p=Path('android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt')
s=p.read_text()

# Undo the accidental SessionStore insertion into FavoritesV100.
s=s.replace('''                    favorites -> FavoritesV100(\n                        api,\n                        session,\n                        commerce,''','''                    favorites -> FavoritesV100(\n                        api,\n                        commerce,''',1)

# Pass SessionStore only to the product screen, where reviews need account identity.
s=s.replace('''                    selected != null -> ProductV100(\n                        selected!!,\n                        api,\n                        commerce,''','''                    selected != null -> ProductV100(\n                        selected!!,\n                        api,\n                        session,\n                        commerce,''',1)

# The first v1.0.23 replacement consumed these private helpers because its end anchor
# was RatingLine. Restore the original v1.0.22 gallery/brand helpers if absent.
if '@Composable private fun Gallery(p:Product)' not in s:
    anchor='@Composable private fun RatingLine'
    helpers='''@Composable private fun Gallery(p:Product){val imgs=(listOfNotNull(p.imageUrl)+p.images).distinct();val pager=rememberPagerState{imgs.size.coerceAtLeast(1)};Box{Column{HorizontalPager(pager,Modifier.fillMaxWidth().height(330.dp)){i->if(imgs.isNotEmpty())AsyncImage(imgs[i],p.name,Modifier.fillMaxSize().padding(8.dp),contentScale=ContentScale.Fit) else Box(Modifier.fillMaxSize().background(Soft))};if(imgs.size>1)Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.Center){repeat(imgs.size){i->Box(Modifier.padding(3.dp).size(if(pager.currentPage==i)9.dp else 7.dp).background(if(pager.currentPage==i)AutoIdOrange else Color(0xFFD0D5DD),CircleShape))}}};DiscountChip(p,Modifier.align(Alignment.TopStart).padding(8.dp))}}\n@Composable private fun Brand(p:Product){if(p.brandLogoUrl!=null)AsyncImage(p.brandLogoUrl,p.brand,Modifier.height(34.dp).widthIn(max=120.dp),contentScale=ContentScale.Fit) else if(p.brand.isNotBlank())Text(p.brand.uppercase(),fontSize=12.sp,fontWeight=FontWeight.ExtraBold,color=Muted)}\n'''
    assert anchor in s
    s=s.replace(anchor,helpers+anchor,1)

# Product-loop CTAs: Detalii produs / Adauga in cos / Cerere de oferta.
old='''        shape = RoundedCornerShape(24.dp),\n        color = bg,'''
new='''        shape = RoundedCornerShape(10.dp),\n        color = bg,'''
assert old in s
s=s.replace(old,new,1)

p.write_text(s)
print('fixed v1.0.23 product call, helpers and loop CTA radius')
