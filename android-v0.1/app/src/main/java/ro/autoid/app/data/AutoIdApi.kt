package ro.autoid.app.data

import android.text.Html
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URI
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.text.NumberFormat
import java.util.Locale
import kotlin.math.pow

class AutoIdApi {
    companion object { const val BASE="https://www.autoid.ro"; const val MOBILE="$BASE/wp-json/autoid-app/v1"; const val STORE="$BASE/wp-json/wc/store/v1" }
    fun health() = runCatching { get("$MOBILE/health"); true }.getOrDefault(false)
    fun products(search:String=""):List<Product> { val q=if(search.isBlank()) "?per_page=20" else "?per_page=20&search=${URLEncoder.encode(search,"UTF-8")}"; val a=JSONArray(get("$STORE/products$q")); return (0 until a.length()).mapNotNull { a.optJSONObject(it)?.let(::product) } }
    fun login(login:String,password:String):LoginResult { val body=JSONObject().put("login",login).put("username",login).put("email",login).put("password",password); val root=JSONObject(post("$MOBILE/auth/login",body.toString())); val d=root.optJSONObject("data")?:root; val token=d.optString("access_token",d.optString("token")); if(token.isBlank()) error(d.optString("message","Autentificare eșuată")); val u=d.optJSONObject("customer")?:d.optJSONObject("user"); return LoginResult(token,d.optString("refresh_token").ifBlank{null},u?.let{Customer(if(it.has("id"))it.optLong("id") else null, listOf(it.optString("first_name"),it.optString("last_name")).filter(String::isNotBlank).joinToString(" ").ifBlank{it.optString("name")},it.optString("email"))}) }
    fun orders(token:String):List<Order> { val raw=get("$MOBILE/me/orders",token); val a=if(raw.trimStart().startsWith("[")) JSONArray(raw) else JSONObject(raw).optJSONArray("orders")?:JSONObject(raw).optJSONObject("data")?.optJSONArray("orders")?:JSONArray(); return (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{Order(it.optLong("id"),it.optString("number",it.optLong("id").toString()),it.optString("status"),total(it),it.optString("date_created"))}} }
    private fun product(o:JSONObject):Product { val prices=o.optJSONObject("prices"); val raw=prices?.optString("price").orEmpty(); val minor=prices?.optInt("currency_minor_unit",2)?:2; val value=raw.toDoubleOrNull()?.div(10.0.pow(minor)); val price=if(value==null) "Preț la cerere" else NumberFormat.getNumberInstance(Locale("ro","RO")).apply{minimumFractionDigits=minor.coerceAtMost(2);maximumFractionDigits=minor.coerceAtMost(2)}.format(value)+(if(prices?.optString("currency_code")=="EUR") " €" else " lei"); return Product(o.optLong("id"),html(o.optString("name")),o.optString("sku"),o.optString("permalink"),o.optJSONArray("images")?.optJSONObject(0)?.optString("src"),price,if(o.optBoolean("is_in_stock",true))"În stoc / disponibil" else "Stoc epuizat",html(o.optString("short_description"))) }
    private fun total(o:JSONObject)=o.optString("total")+if(o.optString("currency","RON")=="EUR")" €" else " lei"
    private fun html(s:String)=Html.fromHtml(s,Html.FROM_HTML_MODE_LEGACY).toString().replace(Regex("\\s+")," ").trim()
    private fun get(url:String,token:String?=null)=request("GET",url,null,token)
    private fun post(url:String,body:String)=request("POST",url,body,null)
    private fun request(method:String,url:String,body:String?,token:String?):String { val c=URI(url).toURL().openConnection() as HttpURLConnection; c.requestMethod=method;c.connectTimeout=12000;c.readTimeout=18000;c.setRequestProperty("Accept","application/json");c.setRequestProperty("User-Agent","AutoID-Android/0.1.0");token?.let{c.setRequestProperty("Authorization","Bearer $it")};if(body!=null){c.doOutput=true;c.setRequestProperty("Content-Type","application/json");c.outputStream.use{it.write(body.toByteArray(StandardCharsets.UTF_8))}};val status=c.responseCode;val text=(if(status in 200..299)c.inputStream else c.errorStream)?.bufferedReader()?.use{it.readText()}.orEmpty();c.disconnect();if(status !in 200..299) error(runCatching{JSONObject(text).optString("message",text)}.getOrDefault(text).ifBlank{"HTTP $status"});return text }
}
