package ro.autoid.app.data

data class Product(
    val id: Long,
    val name: String,
    val sku: String,
    val permalink: String,
    val imageUrl: String?,
    val images: List<String> = emptyList(),
    val price: String,
    val regularPrice: String = "",
    val salePrice: String = "",
    val currency: String = "RON",
    val onSale: Boolean = false,
    val stockLabel: String,
    val inStock: Boolean = true,
    val description: String,
    val category: String = "",
    val brand: String = "",
    val supportQuery: String = "",
    val attributes: List<ProductAttribute> = emptyList()
)

data class ProductAttribute(val name: String, val values: List<String>)
data class ProductCategory(val id: Long, val name: String, val count: Int, val imageUrl: String? = null)
data class SupportResource(val id: Long, val title: String, val url: String, val type: String, val summary: String)
data class Order(val id:Long,val number:String,val status:String,val total:String,val dateCreated:String)
data class Customer(val id:Long?=null,val name:String="",val email:String="")
data class LoginResult(val accessToken:String,val refreshToken:String?=null,val customer:Customer?=null)
data class CartLine(val product: Product, val quantity: Int)
data class AiMessage(val fromUser: Boolean, val text: String, val productIds: List<Long> = emptyList())
