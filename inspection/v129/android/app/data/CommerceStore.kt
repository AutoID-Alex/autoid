package ro.autoid.app.data

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.setValue
import org.json.JSONArray
import org.json.JSONObject

class CommerceStore(context: Context) {
    private val prefs = context.getSharedPreferences("autoid_commerce_v03", Context.MODE_PRIVATE)
    private var cartRevisionState by mutableIntStateOf(0)
    private var favoriteRevisionState by mutableIntStateOf(0)
    val cartRevision: Int get() = cartRevisionState
    val favoriteRevision: Int get() = favoriteRevisionState

    fun cart(): List<CartLine> {
        cartRevisionState
        return readArray("cart").mapNotNull { o ->
        val p = decodeProduct(o.optJSONObject("product") ?: return@mapNotNull null) ?: return@mapNotNull null
        CartLine(p, o.optInt("quantity", 1).coerceAtLeast(1))
        }
    }

    fun addToCart(product: Product, qty: Int = 1) {
        val current = cart().toMutableList()
        val i = current.indexOfFirst { it.product.id == product.id }
        if (i >= 0) current[i] = current[i].copy(quantity = current[i].quantity + qty)
        else current += CartLine(product, qty.coerceAtLeast(1))
        saveCart(current)
    }

    fun changeQty(productId: Long, qty: Int) {
        val lines = cart().mapNotNull {
            if (it.product.id != productId) it else if (qty <= 0) null else it.copy(quantity = qty)
        }
        saveCart(lines)
    }

    fun removeFromCart(productId: Long) = saveCart(cart().filterNot { it.product.id == productId })
    fun clearCart() { prefs.edit().remove("cart").apply(); cartRevisionState++ }
    fun cartCount(): Int { cartRevisionState; return cart().sumOf { it.quantity } }

    fun wishlistIds(): Set<Long> {
        favoriteRevisionState
        return prefs.getStringSet("wishlist", emptySet()).orEmpty().mapNotNull { it.toLongOrNull() }.toSet()
    }
    fun isFavorite(id: Long) = wishlistIds().contains(id)
    fun toggleFavorite(id: Long): Boolean {
        val ids = wishlistIds().toMutableSet()
        val added = if (ids.contains(id)) { ids.remove(id); false } else { ids.add(id); true }
        prefs.edit().putStringSet("wishlist", ids.map(Long::toString).toSet()).apply()
        favoriteRevisionState++
        return added
    }

    fun addRecent(product: Product) {
        val rows = recent().filterNot { it.id == product.id }.toMutableList()
        rows.add(0, product)
        prefs.edit().putString("recent", JSONArray(rows.take(12).map(::encodeProduct)).toString()).apply()
    }
    fun recent(): List<Product> = readArray("recent").mapNotNull(::decodeProduct)

    private fun saveCart(lines: List<CartLine>) {
        val a = JSONArray()
        lines.forEach { a.put(JSONObject().put("product", encodeProduct(it.product)).put("quantity", it.quantity)) }
        prefs.edit().putString("cart", a.toString()).apply()
        cartRevisionState++
    }
    private fun readArray(key: String): List<JSONObject> = runCatching {
        val a = JSONArray(prefs.getString(key, "[]")); (0 until a.length()).mapNotNull(a::optJSONObject)
    }.getOrDefault(emptyList())
    private fun encodeProduct(p: Product) = JSONObject()
        .put("id",p.id).put("name",p.name).put("sku",p.sku).put("permalink",p.permalink)
        .put("image",p.imageUrl).put("price",p.price).put("regular",p.regularPrice).put("sale",p.salePrice)
        .put("currency",p.currency).put("stock",p.stockLabel).put("in_stock",p.inStock)
        .put("description",p.description).put("category",p.category).put("brand",p.brand).put("support",p.supportQuery)
    private fun decodeProduct(o: JSONObject?): Product? = o?.let {
        val id=it.optLong("id"); if(id<=0) return@let null
        Product(id,it.optString("name"),it.optString("sku"),it.optString("permalink"),it.optString("image").ifBlank{null},
            price=it.optString("price"),regularPrice=it.optString("regular"),salePrice=it.optString("sale"),currency=it.optString("currency","RON"),
            stockLabel=it.optString("stock"),inStock=it.optBoolean("in_stock",true),description=it.optString("description"),category=it.optString("category"),brand=it.optString("brand"),supportQuery=it.optString("support"))
    }
}
