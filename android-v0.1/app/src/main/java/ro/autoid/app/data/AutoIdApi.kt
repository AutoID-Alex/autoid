package ro.autoid.app.data

import android.text.Html
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URI
import java.net.URLEncoder
import java.nio.charset.StandardCharsets

class AutoIdApi {
    companion object {
        const val BASE = "https://www.autoid.ro"
        const val MOBILE_V1 = "$BASE/wp-json/autoid-app/v1"
        const val MOBILE_V2 = "$BASE/wp-json/autoid-app/v2"
    }

    fun health() = runCatching { get("$MOBILE_V1/health"); true }.getOrDefault(false)

    fun products(search: String = "", category: Long? = null): List<Product> {
        val qs = mutableListOf("per_page=24")
        if (search.isNotBlank()) qs += "search=${enc(search)}"
        category?.let { qs += "category=$it" }
        val raw = get("$MOBILE_V2/products?${qs.joinToString("&")}")
        val root = if (raw.trimStart().startsWith("[")) null else JSONObject(raw)
        val arr = root?.optJSONArray("products") ?: JSONArray(raw)
        return (0 until arr.length()).mapNotNull { arr.optJSONObject(it)?.let(::product) }
    }

    fun categories(): List<ProductCategory> {
        val raw = get("$MOBILE_V2/categories")
        val root = if (raw.trimStart().startsWith("[")) null else JSONObject(raw)
        val arr = root?.optJSONArray("categories") ?: JSONArray(raw)
        return (0 until arr.length()).mapNotNull { i ->
            arr.optJSONObject(i)?.let { ProductCategory(it.optLong("id"), html(it.optString("name")), it.optInt("count")) }
        }
    }

    fun support(search: String): List<SupportResource> {
        if (search.isBlank()) return emptyList()
        val raw = get("$MOBILE_V2/support?search=${enc(search)}&per_page=30")
        val root = if (raw.trimStart().startsWith("[")) null else JSONObject(raw)
        val arr = root?.optJSONArray("resources") ?: JSONArray(raw)
        return (0 until arr.length()).mapNotNull { i ->
            arr.optJSONObject(i)?.let {
                SupportResource(
                    it.optLong("id"), html(it.optString("title")), it.optString("url"),
                    it.optString("type", "Resursă"), html(it.optString("summary"))
                )
            }
        }
    }

    fun login(login:String,password:String):LoginResult {
        val body=JSONObject().put("login",login).put("username",login).put("email",login).put("password",password)
        val root=JSONObject(post("$MOBILE_V1/auth/login",body.toString()))
        val d=root.optJSONObject("data")?:root
        val token=d.optString("access_token",d.optString("token"))
        if(token.isBlank()) error(d.optString("message","Autentificare eșuată"))
        val u=d.optJSONObject("customer")?:d.optJSONObject("user")
        return LoginResult(token,d.optString("refresh_token").ifBlank{null},u?.let{Customer(if(it.has("id"))it.optLong("id") else null, listOf(it.optString("first_name"),it.optString("last_name")).filter(String::isNotBlank).joinToString(" ").ifBlank{it.optString("name")},it.optString("email"))})
    }

    fun orders(token:String):List<Order> {
        val raw=get("$MOBILE_V1/me/orders",token)
        val a=if(raw.trimStart().startsWith("[")) JSONArray(raw) else JSONObject(raw).optJSONArray("orders")?:JSONObject(raw).optJSONObject("data")?.optJSONArray("orders")?:JSONArray()
        return (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{Order(it.optLong("id"),it.optString("number",it.optLong("id").toString()),it.optString("status"),total(it),it.optString("date_created"))}}
    }

    private fun product(o:JSONObject)=Product(
        o.optLong("id"), html(o.optString("name")), o.optString("sku"), o.optString("permalink", o.optString("url")),
        o.optString("image").ifBlank { o.optString("image_url") }.ifBlank { null },
        o.optString("price_display", o.optString("price", "Preț la cerere")),
        o.optString("stock_label", if(o.optBoolean("in_stock",true)) "În stoc / disponibil" else "Stoc epuizat"),
        html(o.optString("short_description",o.optString("description"))), html(o.optString("category")), html(o.optString("brand")), o.optString("support_query", o.optString("sku"))
    )

    private fun total(o:JSONObject)=o.optString("total")+if(o.optString("currency","RON")=="EUR")" €" else " lei"
    private fun html(s:String)=Html.fromHtml(s,Html.FROM_HTML_MODE_LEGACY).toString().replace(Regex("\\s+")," ").trim()
    private fun enc(v:String)=URLEncoder.encode(v,"UTF-8")
    private fun get(url:String,token:String?=null)=request("GET",url,null,token)
    private fun post(url:String,body:String)=request("POST",url,body,null)
    private fun request(method:String,url:String,body:String?,token:String?):String {
        val c=URI(url).toURL().openConnection() as HttpURLConnection
        c.requestMethod=method;c.connectTimeout=12000;c.readTimeout=18000
        c.setRequestProperty("Accept","application/json")
        c.setRequestProperty("User-Agent","AutoID-Android/0.2.0")
        token?.let{c.setRequestProperty("Authorization","Bearer $it")}
        if(body!=null){c.doOutput=true;c.setRequestProperty("Content-Type","application/json");c.outputStream.use{it.write(body.toByteArray(StandardCharsets.UTF_8))}}
        val status=c.responseCode
        val text=(if(status in 200..299)c.inputStream else c.errorStream)?.bufferedReader()?.use{it.readText()}.orEmpty()
        c.disconnect()
        if(status !in 200..299) error(runCatching{JSONObject(text).optString("message",text)}.getOrDefault(text).ifBlank{"HTTP $status"})
        return text
    }
}
