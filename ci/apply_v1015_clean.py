from pathlib import Path

ROOT=Path('.')
APP=ROOT/'android-v0.1/app'
SRC=APP/'src/main/java/ro/autoid/app'
MODELS=SRC/'data/Models.kt'
API=SRC/'data/AutoIdApi.kt'
UI=SRC/'V100Screens.kt'
GRADLE=APP/'build.gradle.kts'
TEMPLATE=ROOT/'ci/V115AccountCheckout.kt'
TARGET=SRC/'V115AccountCheckout.kt'

if not TEMPLATE.exists():
    raise SystemExit('Missing ci/V115AccountCheckout.kt')
TARGET.write_text(TEMPLATE.read_text())

s=GRADLE.read_text()
s=s.replace('versionCode = 11700','versionCode = 11800',1)
s=s.replace('versionName = "1.0.14"','versionName = "1.0.15"',1)
anchor='    implementation("com.google.android.gms:play-services-auth:21.2.0")\n'
extra='''    implementation("androidx.credentials:credentials:1.6.0")\n    implementation("androidx.credentials:credentials-play-services-auth:1.6.0")\n    implementation("com.google.android.libraries.identity.googleid:googleid:1.2.0")\n'''
if 'androidx.credentials:credentials:1.6.0' not in s:
    if anchor not in s: raise SystemExit('Gradle dependency anchor missing')
    s=s.replace(anchor,anchor+extra,1)
GRADLE.write_text(s)

s=MODELS.read_text()
if 'data class AccountProfile(' not in s:
    insert='''\n\ndata class AccountProfile(val id:Long,val email:String,val firstName:String="",val lastName:String="",val company:String="")\ndata class AccountAddress(val firstName:String="",val lastName:String="",val company:String="",val address1:String="",val address2:String="",val city:String="",val state:String="",val postcode:String="",val country:String="RO",val phone:String="",val email:String="")\ndata class AccountAddresses(val billing:AccountAddress=AccountAddress(),val shipping:AccountAddress=AccountAddress())\ndata class SavedPaymentMethod(val id:Long,val type:String,val label:String,val isDefault:Boolean=false)\n'''
    pos=s.index('\n\ndata class FacetItem')
    s=s[:pos]+insert+s[pos:]
MODELS.write_text(s)

s=API.read_text().replace('AutoID-Android/1.0.14','AutoID-Android/1.0.15')
if 'fun accountProfile(token:String)' not in s:
    anchor='    fun orders(token:String):List<Order>{'
    idx=s.index(anchor)
    block='''    fun accountProfile(token:String):AccountProfile{\n        val raw=JSONObject(get("$MOBILE/me/profile",token));val o=raw.optJSONObject("profile")?:raw.optJSONObject("customer")?:raw\n        return AccountProfile(o.optLong("id"),o.optString("email"),o.optString("first_name"),o.optString("last_name"),o.optString("company"))\n    }\n\n    fun saveAccountProfile(token:String,first:String,last:String,company:String):AccountProfile{\n        val body=JSONObject().put("first_name",first).put("last_name",last).put("company",company)\n        val raw=JSONObject(post("$MOBILE/me/profile",body.toString(),token));val o=raw.optJSONObject("profile")?:raw.optJSONObject("customer")?:raw\n        return AccountProfile(o.optLong("id"),o.optString("email"),o.optString("first_name"),o.optString("last_name"),o.optString("company"))\n    }\n\n    private fun accountAddress(o:JSONObject)=AccountAddress(o.optString("first_name"),o.optString("last_name"),o.optString("company"),o.optString("address_1"),o.optString("address_2"),o.optString("city"),o.optString("state"),o.optString("postcode"),o.optString("country","RO"),o.optString("phone"),o.optString("email"))\n\n    fun accountAddresses(token:String):AccountAddresses{\n        val raw=JSONObject(get("$MOBILE/me/addresses",token));return AccountAddresses(accountAddress(raw.optJSONObject("billing")?:JSONObject()),accountAddress(raw.optJSONObject("shipping")?:JSONObject()))\n    }\n\n    fun saveAccountAddresses(token:String,addresses:AccountAddresses):AccountAddresses{\n        fun obj(a:AccountAddress)=JSONObject().put("first_name",a.firstName).put("last_name",a.lastName).put("company",a.company).put("address_1",a.address1).put("address_2",a.address2).put("city",a.city).put("state",a.state).put("postcode",a.postcode).put("country",a.country).put("phone",a.phone).put("email",a.email)\n        val raw=JSONObject(post("$MOBILE/me/addresses",JSONObject().put("billing",obj(addresses.billing)).put("shipping",obj(addresses.shipping)).toString(),token));return AccountAddresses(accountAddress(raw.optJSONObject("billing")?:JSONObject()),accountAddress(raw.optJSONObject("shipping")?:JSONObject()))\n    }\n\n    fun savedPaymentMethods(token:String):List<SavedPaymentMethod>{\n        val raw=JSONObject(get("$MOBILE/me/payment-methods",token));val a=raw.optJSONArray("methods")?:JSONArray();return (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{o->SavedPaymentMethod(o.optLong("id"),o.optString("type"),o.optString("label"),o.optBoolean("is_default"))}}\n    }\n\n'''
    s=s[:idx]+block+s[idx:]
API.write_text(s)

s=UI.read_text()
s=s.replace('CheckoutV114(','CheckoutV115(',1)
s=s.replace('AccountV114(','AccountV115(',1)
UI.write_text(s)

print('Applied clean Android v1.0.15: Credential Manager Google Sign-In, fixed checkout summary, redesigned account control panel')
