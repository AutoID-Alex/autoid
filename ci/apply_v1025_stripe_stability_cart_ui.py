from pathlib import Path

root=Path('android-v0.1')
ux=root/'app/src/main/java/ro/autoid/app/V114CommerceUx.kt'
screens=root/'app/src/main/java/ro/autoid/app/V100Screens.kt'
api=root/'app/src/main/java/ro/autoid/app/data/AutoIdApi.kt'
gradle=root/'app/build.gradle.kts'
plugin=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
styles=root/'app/src/main/res/values/stripe_autoid_v124.xml'

g=gradle.read_text().replace('versionCode = 12700','versionCode = 12800').replace('versionName = "1.0.24"','versionName = "1.0.25"')
gradle.write_text(g)

a=api.read_text().replace('AutoID-Android/1.0.24','AutoID-Android/1.0.25')
api.write_text(a)

p=plugin.read_text().replace('Version: 1.1.13','Version: 1.1.14',1)
plugin.write_text(p)

st=styles.read_text()
if 'Theme.AutoIDStripeCard' not in st:
    st=st.replace('</resources>','''    <style name="Theme.AutoIDStripeCard" parent="Theme.MaterialComponents.Light.NoActionBar">
        <item name="colorPrimary">#F7630C</item>
        <item name="colorPrimaryVariant">#D94F00</item>
        <item name="colorSecondary">#F7630C</item>
        <item name="android:windowLightStatusBar">true</item>
        <item name="android:fontFamily">sans</item>
    </style>
</resources>''')
styles.write_text(st)

s=ux.read_text()
if 'import android.view.ContextThemeWrapper' not in s:
    s=s.replace('package ro.autoid.app\n','package ro.autoid.app\n\nimport android.view.ContextThemeWrapper\n',1)

# Google Pay should always be visible as an option. Readiness controls whether it can actually launch.
s=s.replace('''StripeChoiceV124("card","Card",stripePaymentChoice,{stripePaymentChoice=it},Modifier.weight(1f));if(googlePayReady)StripeChoiceV124("google_pay","Google Pay",stripePaymentChoice,{stripePaymentChoice=it},Modifier.weight(1f))''',
'''StripeChoiceV124("card","Card",stripePaymentChoice,{stripePaymentChoice=it},Modifier.weight(1f));StripeChoiceV124("google_pay","Google Pay",stripePaymentChoice,{stripePaymentChoice=it},Modifier.weight(1f))''',1)

# Runtime-safe Stripe View: wrap Stripe's Material Components view in a dedicated MaterialComponents theme.
old='''AndroidView(factory={ctx->CardInputWidget(ctx).apply{postalCodeEnabled=false;setCardValidCallback{validCard,_->stripeCardValid=validCard};stripeCardWidget=this}},update={stripeCardWidget=it},modifier=Modifier.fillMaxWidth().heightIn(min=58.dp))'''
new='''AndroidView(factory={ctx->val themed=ContextThemeWrapper(ctx,R.style.Theme_AutoIDStripeCard);CardInputWidget(themed).apply{postalCodeEnabled=false;postalCodeRequired=false;setCardValidCallback{validCard,_->stripeCardValid=validCard};stripeCardWidget=this}},update={stripeCardWidget=it},modifier=Modifier.fillMaxWidth().heightIn(min=58.dp))'''
assert old in s, 'CardInputWidget anchor not found'
s=s.replace(old,new,1)

# Explain Google Pay state instead of silently hiding the method.
s=s.replace('''Text("Plata se deschide în Google Pay. Nu solicităm din nou adresa sau datele de contact.",fontSize=9.sp,color=C114Muted)''',
'''Text(if(googlePayReady)"Disponibil pe acest dispozitiv · plata se deschide securizat în Google Pay." else "Google Pay este activat, dar acest dispozitiv/cont nu este momentan ready pentru plată.",fontSize=9.sp,color=if(googlePayReady)Color(0xFF16794B) else C114Muted);Text("Nu solicităm din nou adresa sau datele de contact.",fontSize=9.sp,color=C114Muted)''',1)
ux.write_text(s)

v=screens.read_text()
oldmini='''@Composable private fun MiniCart(commerce:CommerceStore,open:Boolean,onDismiss:()->Unit,onCart:()->Unit,tick:Int){DropdownMenu(expanded=open,onDismissRequest=onDismiss,modifier=Modifier.width(330.dp).background(Color.White)){val lines=commerce.cart();Row(Modifier.fillMaxWidth().padding(horizontal=14.dp,vertical=8.dp),verticalAlignment=Alignment.CenterVertically){Text("Coșul meu (${commerce.cartCount()})",fontWeight=FontWeight.ExtraBold,modifier=Modifier.weight(1f));TextButton(onClick={commerce.clearCart();onDismiss()}){Text("Șterge")}};HorizontalDivider();if(lines.isEmpty())DropdownMenuItem(text={Text("Coșul este gol",color=Muted)},onClick={}) else lines.take(4).forEach{l->DropdownMenuItem(text={Row(verticalAlignment=Alignment.CenterVertically){AsyncImage(l.product.imageUrl,l.product.name,Modifier.size(46.dp));Spacer(Modifier.width(8.dp));Column(Modifier.weight(1f)){Text(l.product.name,maxLines=1,overflow=TextOverflow.Ellipsis,fontWeight=FontWeight.SemiBold);Text("${l.quantity} × ${l.product.currentInclVat.ifBlank{l.product.price}}",fontSize=11.sp,color=Muted)}}},onClick={})};if(lines.isNotEmpty()){HorizontalDivider();Button(onClick={onDismiss();onCart()},modifier=Modifier.fillMaxWidth().padding(12.dp)){Text("Vezi coșul")}}}}'''
newmini='''private fun miniCartPriceV125(raw:String):String=raw.replace("&amp;nbsp;"," ",true).replace("&nbsp;"," ",true).replace("&#160;"," ",true).replace("&#xA0;"," ",true).replace('\\u00A0',' ').replace(Regex("<[^>]+>"),"").replace(Regex("\\\\s+")," ").trim()
@Composable private fun MiniCart(commerce:CommerceStore,open:Boolean,onDismiss:()->Unit,onCart:()->Unit,tick:Int){DropdownMenu(expanded=open,onDismissRequest=onDismiss,modifier=Modifier.width(344.dp).clip(RoundedCornerShape(16.dp)).background(Color.White)){val lines=commerce.cart();Column(Modifier.fillMaxWidth().padding(horizontal=14.dp,vertical=10.dp),verticalArrangement=Arrangement.spacedBy(9.dp)){Row(verticalAlignment=Alignment.CenterVertically){Column(Modifier.weight(1f)){Text("Coșul meu",fontSize=17.sp,fontWeight=FontWeight.ExtraBold,color=Ink);Text("${commerce.cartCount()} produse",fontSize=10.sp,color=Muted)};if(lines.isNotEmpty())TextButton(onClick={commerce.clearCart();onDismiss()}){Text("Golește",fontSize=11.sp,color=AutoIdOrange)}};HorizontalDivider(color=Color(0xFFE8EAED));if(lines.isEmpty()){Box(Modifier.fillMaxWidth().padding(vertical=20.dp),contentAlignment=Alignment.Center){Text("Coșul este gol",color=Muted)}}else lines.take(4).forEach{l->Surface(shape=RoundedCornerShape(12.dp),color=Color(0xFFF8F9FB)){Row(Modifier.fillMaxWidth().padding(9.dp),verticalAlignment=Alignment.CenterVertically){AsyncImage(l.product.imageUrl,l.product.name,Modifier.size(48.dp).clip(RoundedCornerShape(9.dp)).background(Color.White).padding(3.dp),contentScale=ContentScale.Fit);Spacer(Modifier.width(9.dp));Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(3.dp)){Text(l.product.name,maxLines=2,overflow=TextOverflow.Ellipsis,fontSize=11.sp,fontWeight=FontWeight.Bold,color=Ink);Text("Cantitate: ${l.quantity}",fontSize=9.sp,color=Muted)};Spacer(Modifier.width(6.dp));Text(miniCartPriceV125(l.product.currentInclVat.ifBlank{l.product.price}),fontSize=11.sp,fontWeight=FontWeight.ExtraBold,color=AutoIdOrange)}}};if(lines.size>4)Text("+ ${lines.size-4} alte produse",fontSize=9.sp,color=Muted,modifier=Modifier.padding(start=4.dp));if(lines.isNotEmpty())Button(onClick={onDismiss();onCart()},modifier=Modifier.fillMaxWidth().height(48.dp),shape=RoundedCornerShape(10.dp)){Text("Vezi coșul",fontWeight=FontWeight.ExtraBold)}}}}'''
assert oldmini in v, 'MiniCart anchor not found'
v=v.replace(oldmini,newmini,1)
screens.write_text(v)
print('Applied AutoID v1.0.25 Stripe runtime stability, Google Pay visibility and mini-cart UX')
