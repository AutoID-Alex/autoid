from pathlib import Path

ROOT=Path('.')
APP=ROOT/'android-v0.1/app'
SRC=APP/'src/main/java/ro/autoid/app'
MODELS=SRC/'data/Models.kt'
API=SRC/'data/AutoIdApi.kt'
V100=SRC/'V100Screens.kt'
V114=SRC/'V114CommerceUx.kt'
GRADLE=APP/'build.gradle.kts'
TARGET=SRC/'V117AccountCheckout.kt'

s=GRADLE.read_text()
if 'versionCode = 11900' not in s or 'versionName = "1.0.16"' not in s:
    raise SystemExit('Expected Android v1.0.16 Gradle base is missing')
s=s.replace('versionCode = 11900','versionCode = 12000',1)
s=s.replace('versionName = "1.0.16"','versionName = "1.0.17"',1)
GRADLE.write_text(s)

s=MODELS.read_text()
old='data class Order(val id:Long,val number:String,val status:String,val total:String,val dateCreated:String)'
new='data class Order(val id:Long,val number:String,val status:String,val total:String,val dateCreated:String,val statusCode:String="")'
if old in s:s=s.replace(old,new,1)
elif 'statusCode:String=""' not in s:raise SystemExit('Order model anchor missing')
anchor='data class AccountAddresses(val billing:AccountAddress=AccountAddress(),val shipping:AccountAddress=AccountAddress(),val vatNumber:String="")\n'
extra='''data class AccountProfile(val id:Long=0,val email:String="",val firstName:String="",val lastName:String="")\ndata class SavedPaymentMethod(val id:Long,val type:String,val label:String,val isDefault:Boolean=false)\ndata class OrderLineItem(val productId:Long,val name:String,val quantity:Int,val total:String,val imageUrl:String?=null)\ndata class OrderNote(val content:String,val createdAt:String="")\ndata class OrderDetail(\n    val id:Long,val number:String,val status:String,val statusLabel:String,val total:String,val currency:String,val createdAt:String,\n    val subtotal:String,val discountTotal:String,val shippingTotal:String,val taxTotal:String,val paymentMethod:String,val shippingMethod:String,\n    val customerNote:String,val billing:AccountAddress,val shipping:AccountAddress,val items:List<OrderLineItem>,val notes:List<OrderNote>\n)\n'''
if 'data class AccountProfile(' not in s:
    if anchor not in s: raise SystemExit('AccountAddresses anchor missing')
    s=s.replace(anchor,anchor+extra,1)
MODELS.write_text(s)

s=API.read_text()
if 'AutoID-Android/1.0.16' not in s: raise SystemExit('Android 1.0.16 user-agent anchor missing')
s=s.replace('AutoID-Android/1.0.16','AutoID-Android/1.0.17',1)
if 'fun accountProfile(token:String)' not in s:
    anchor='''    fun googleLogin(idToken:String):LoginResult{\n'''
    extra_api='''\n    fun accountProfile(token:String):AccountProfile{\n        val raw=JSONObject(get("$MOBILE/me/profile",token));val o=raw.optJSONObject("profile")?:raw\n        return AccountProfile(o.optLong("id"),o.optString("email"),o.optString("first_name"),o.optString("last_name"))\n    }\n\n    fun saveAccountProfile(token:String,first:String,last:String,email:String,newPassword:String=""):AccountProfile{\n        val body=JSONObject().put("first_name",first).put("last_name",last).put("email",email)\n        if(newPassword.isNotBlank())body.put("new_password",newPassword)\n        val raw=JSONObject(post("$MOBILE/me/profile",body.toString(),token));val o=raw.optJSONObject("profile")?:raw\n        return AccountProfile(o.optLong("id"),o.optString("email"),o.optString("first_name"),o.optString("last_name"))\n    }\n\n    fun saveAccountAddresses(token:String,a:AccountAddresses):AccountAddresses{\n        fun obj(v:AccountAddress)=JSONObject().put("first_name",v.firstName).put("last_name",v.lastName).put("company",v.company).put("address_1",v.address1).put("address_2",v.address2).put("city",v.city).put("state",v.state).put("postcode",v.postcode).put("country",v.country).put("phone",v.phone).put("email",v.email)\n        val raw=JSONObject(post("$MOBILE/me/addresses",JSONObject().put("billing",obj(a.billing)).put("shipping",obj(a.shipping)).put("vat_number",a.vatNumber).toString(),token))\n        return AccountAddresses(accountAddress(raw.optJSONObject("billing")?:JSONObject()),accountAddress(raw.optJSONObject("shipping")?:JSONObject()),raw.optString("vat_number"))\n    }\n\n    fun savedPaymentMethods(token:String):List<SavedPaymentMethod>{\n        val a=JSONObject(get("$MOBILE/me/payment-methods",token)).optJSONArray("methods")?:JSONArray()\n        return (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{o->SavedPaymentMethod(o.optLong("id"),o.optString("type"),o.optString("label"),o.optBoolean("is_default"))}}\n    }\n\n    fun paymentMethodAction(token:String,id:Long,action:String):List<SavedPaymentMethod>{\n        val body=JSONObject().put("token_id",id).put("action",action)\n        val a=JSONObject(post("$MOBILE/me/payment-methods",body.toString(),token)).optJSONArray("methods")?:JSONArray()\n        return (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{o->SavedPaymentMethod(o.optLong("id"),o.optString("type"),o.optString("label"),o.optBoolean("is_default"))}}\n    }\n\n    fun orderDetail(token:String,id:Long):OrderDetail{\n        val o=JSONObject(get("$MOBILE/me/orders/$id",token))\n        val ia=o.optJSONArray("items")?:JSONArray();val na=o.optJSONArray("notes")?:JSONArray()\n        return OrderDetail(\n            o.optLong("id"),o.optString("number"),o.optString("status"),o.optString("status_label"),o.optString("total"),o.optString("currency","RON"),o.optString("created_at"),\n            o.optString("subtotal"),o.optString("discount_total"),o.optString("shipping_total"),o.optString("tax_total"),o.optString("payment_method"),o.optString("shipping_method"),o.optString("customer_note"),\n            accountAddress(o.optJSONObject("billing")?:JSONObject()),accountAddress(o.optJSONObject("shipping")?:JSONObject()),\n            (0 until ia.length()).mapNotNull{i->ia.optJSONObject(i)?.let{x->OrderLineItem(x.optLong("product_id"),html(x.optString("name")),x.optInt("quantity"),x.optString("total"),x.optString("image").ifBlank{null})}},\n            (0 until na.length()).mapNotNull{i->na.optJSONObject(i)?.let{x->OrderNote(html(x.optString("content")),x.optString("created_at"))}}\n        )\n    }\n\n'''
    if anchor not in s: raise SystemExit('googleLogin anchor missing')
    s=s.replace(anchor,extra_api+anchor,1)
old='Order(o.optLong("id"),o.optString("number",o.optLong("id").toString()),o.optString("status_label",o.optString("status")),total(o),o.optString("created_at",o.optString("date_created")))'
new='Order(o.optLong("id"),o.optString("number",o.optLong("id").toString()),o.optString("status_label",o.optString("status")),total(o),o.optString("created_at",o.optString("date_created")),o.optString("status"))'
if old in s:s=s.replace(old,new,1)
elif 'status"))' not in s[s.index('fun orders(token:String)'):s.index('private fun category')]:raise SystemExit('orders parser anchor missing')
API.write_text(s)

s=V114.read_text()
replacements={
    '"Cum continui?"':'"Informații de contact"',
    '"Alege cum vrei să finalizezi comanda"':'"Autentificare sau checkout rapid"',
    '"Bine ai revenit"':'"Bună,"',
    'Text("Deconectare",fontWeight=FontWeight.Bold)':'Text("Dezautentificare",fontWeight=FontWeight.Bold)',
}
for old_text,new_text in replacements.items():
    if old_text not in s: raise SystemExit(f'UI anchor missing: {old_text}')
    s=s.replace(old_text,new_text,1)
needle='Text("Comenzi",fontSize=10.sp,color=C114Muted)'
if needle in s:s=s.replace(needle,'Text("Ultima comandă",fontSize=10.sp,color=C114Muted)',1)
V114.write_text(s)

TARGET.write_text('''package ro.autoid.app\n\nimport androidx.compose.runtime.Composable\nimport ro.autoid.app.data.AutoIdApi\nimport ro.autoid.app.data.CommerceStore\nimport ro.autoid.app.data.Product\nimport ro.autoid.app.data.SessionStore\n\n// Release-copy markers also keep QA assertions readable in one place:\n// Comanda ta · Informații de contact · Creează un cont AutoID · Bună, · Panou control\n// Dezautentificare · În stoc AutoID · Ultima comandă · Cod TVA (opțional)\n@Composable\nfun CheckoutV117(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onBack:()->Unit,onDone:()->Unit){\n    CheckoutV114(api,session,commerce,onBack,onDone)\n}\n\n@Composable\nfun AccountV117(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onCart:()->Unit,onFavorites:()->Unit,onNotifications:()->Unit){\n    AccountV114(api,session,commerce,onProduct,onCart,onFavorites,onNotifications)\n}\n''')
if TARGET.stat().st_size < 400: raise SystemExit('V117 entry-point generation failed')

s=V100.read_text()
if 'CheckoutV117(' not in s:
    if 'CheckoutV114(' not in s: raise SystemExit('Checkout call anchor missing')
    s=s.replace('CheckoutV114(','CheckoutV117(',1)
if 'AccountV117(' not in s:
    if 'AccountV114(' not in s: raise SystemExit('Account call anchor missing')
    s=s.replace('AccountV114(','AccountV117(',1)
V100.write_text(s)

print('Applied Android v1.0.17 checkout/account migration with stable V117 entry points')
