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
        const val MOBILE = "$BASE/wp-json/autoid-app/v1"
    }

    fun health() = runCatching { get("$MOBILE/health"); true }.getOrDefault(false)

    fun products(search: String = "", category: Long? = null, page: Int = 1, orderBy: String = "date"): List<Product> {
        val qs = mutableListOf("per_page=20", "page=$page", "orderby=${enc(orderBy)}")
        if (search.isNotBlank()) qs += "search=${enc(search)}"
        category?.let { qs += "category=$it" }
        val root = JSONObject(get("$MOBILE/products?${qs.joinToString("&")}"))
        val arr = root.optJSONArray("products") ?: JSONArray()
        return (0 until arr.length()).mapNotNull { arr.optJSONObject(it)?.let(::product) }
    }

    fun product(id: Long): Product = product(JSONObject(get("$MOBILE/products/$id")))

    fun productFamily(id: Long): ProductFamily {
        val root = JSONObject(get("$MOBILE/products/$id/family"))
        val model = root.optJSONObject("model")?.optString("label").orEmpty()
        val groups = root.optJSONArray("groups") ?: JSONArray()
        return ProductFamily(
            productId = root.optLong("product_id", id),
            model = model,
            groups = (0 until groups.length()).mapNotNull { i -> groups.optJSONObject(i)?.let {
                FamilyGroup(it.optString("key"), html(it.optString("label")), it.optInt("count"))
            } },
            supportAvailable = root.optBoolean("support_available")
        )
    }

    fun familyProducts(id: Long, group: String, page: Int = 1): List<Product> {
        val root = JSONObject(get("$MOBILE/products/$id/family/${enc(group)}?page=$page&per_page=20"))
        val arr = root.optJSONArray("products") ?: JSONArray()
        return (0 until arr.length()).mapNotNull { arr.optJSONObject(it)?.let(::product) }
    }

    fun productSupport(id: Long): List<SupportSection> {
        val root = JSONObject(get("$MOBILE/products/$id/support"))
        val sections = root.optJSONArray("sections") ?: JSONArray()
        return (0 until sections.length()).mapNotNull { i -> sections.optJSONObject(i)?.let { s ->
            val resources = s.optJSONArray("resources") ?: JSONArray()
            SupportSection(
                key = s.optString("key"),
                label = html(s.optString("label")),
                count = s.optInt("count"),
                resources = (0 until resources.length()).mapNotNull { j -> resources.optJSONObject(j)?.let(::supportResource) }
            )
        } }
    }

    fun categories(): List<ProductCategory> {
        val root = JSONObject(get("$MOBILE/categories"))
        val arr = root.optJSONArray("categories") ?: JSONArray()
        return (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let {
            ProductCategory(it.optLong("id"), html(it.optString("name")), it.optInt("count"), it.optString("image").ifBlank { null })
        } }
    }

    fun support(search: String): List<SupportResource> {
        if (search.isBlank()) return emptyList()
        val root = JSONObject(get("$MOBILE/support?search=${enc(search)}"))
        val arr = root.optJSONArray("resources") ?: JSONArray()
        return (0 until arr.length()).mapNotNull { i -> arr.optJSONObject(i)?.let(::supportResource) }
    }

    fun login(login:String,password:String):LoginResult {
        val body=JSONObject().put("login",login).put("username",login).put("email",login).put("password",password)
        val root=JSONObject(post("$MOBILE/auth/login",body.toString()))
        val d=root.optJSONObject("data")?:root
        val token=d.optString("access_token",d.optString("token"))
        if(token.isBlank()) error(d.optString("message","Autentificare eșuată"))
        val u=d.optJSONObject("customer")?:d.optJSONObject("user")
        return LoginResult(token,d.optString("refresh_token").ifBlank{null},u?.let{Customer(if(it.has("id"))it.optLong("id") else null, listOf(it.optString("first_name"),it.optString("last_name")).filter(String::isNotBlank).joinToString(" ").ifBlank{it.optString("name")},it.optString("email"))})
    }

    fun orders(token:String):List<Order> {
        val raw=get("$MOBILE/me/orders",token)
        val a=if(raw.trimStart().startsWith("[")) JSONArray(raw) else JSONObject(raw).optJSONArray("orders")?:JSONObject(raw).optJSONObject("data")?.optJSONArray("orders")?:JSONArray()
        return (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{Order(it.optLong("id"),it.optString("number",it.optLong("id").toString()),it.optString("status_label",it.optString("status")),total(it),it.optString("created_at",it.optString("date_created")))}}
    }

    private fun supportResource(o: JSONObject)=SupportResource(
        o.optLong("id"), html(o.optString("title")), o.optString("url"), o.optString("type", "Resursă"), html(o.optString("summary"))
    )

    private fun product(o:JSONObject): Product {
        val attrs = o.optJSONArray("attributes") ?: JSONArray()
        val images = o.optJSONArray("images") ?: JSONArray()
        return Product(
            id=o.optLong("id"), name=html(o.optString("name")), sku=o.optString("sku"), permalink=o.optString("permalink"),
            imageUrl=o.optString("image").ifBlank { null }, images=(0 until images.length()).mapNotNull{images.optString(it).takeIf(String::isNotBlank)},
            price=o.optString("price_display", o.optString("price","Preț la cerere")), regularPrice=o.optString("regular_price"), salePrice=o.optString("sale_price"),
            currency=o.optString("currency","RON"), onSale=o.optBoolean("on_sale"), stockLabel=o.optString("stock_label"), inStock=o.optBoolean("in_stock",true),
            description=html(o.optString("description",o.optString("short_description"))), category=html(o.optString("category")), brand=html(o.optString("brand")),
            model=html(o.optString("model")), deliveryLabel=html(o.optString("delivery_label")),
            stockAutoId=o.optInt("stock_autoid").takeIf { o.has("stock_autoid") && !o.isNull("stock_autoid") },
            stockDistributor=o.optInt("stock_distributor").takeIf { o.has("stock_distributor") && !o.isNull("stock_distributor") },
            rating=o.optDouble("rating",0.0), reviewCount=o.optInt("review_count",0),
            supportQuery=o.optString("support_query",o.optString("sku")), attributes=(0 until attrs.length()).mapNotNull { i -> attrs.optJSONObject(i)?.let { a ->
                val vals=a.optJSONArray("values")?:JSONArray(); ProductAttribute(html(a.optString("name")),(0 until vals.length()).map{vals.optString(it)})
            } }
        )
    }

    private fun total(o:JSONObject)=o.optString("total")+if(o.optString("currency","RON")=="EUR")" €" else " lei"
    private fun html(s:String)=Html.fromHtml(s,Html.FROM_HTML_MODE_LEGACY).toString().replace(Regex("\\s+")," ").trim()
    private fun enc(v:String)=URLEncoder.encode(v,"UTF-8")
    private fun get(url:String,token:String?=null)=request("GET",url,null,token)
    private fun post(url:String,body:String)=request("POST",url,body,null)
    private fun request(method:String,url:String,body:String?,token:String?):String {
        val c=URI(url).toURL().openConnection() as HttpURLConnection
        c.requestMethod=method;c.connectTimeout=12000;c.readTimeout=20000;c.setRequestProperty("Accept","application/json");c.setRequestProperty("User-Agent","AutoID-Android/0.4.0")
        token?.let{c.setRequestProperty("Authorization","Bearer $it")}
        if(body!=null){c.doOutput=true;c.setRequestProperty("Content-Type","application/json");c.outputStream.use{it.write(body.toByteArray(StandardCharsets.UTF_8))}}
        val status=c.responseCode;val text=(if(status in 200..299)c.inputStream else c.errorStream)?.bufferedReader()?.use{it.readText()}.orEmpty();c.disconnect()
        if(status !in 200..299) error(runCatching{JSONObject(text).optString("message",text)}.getOrDefault(text).ifBlank{"HTTP $status"})
        return text
    }
}
