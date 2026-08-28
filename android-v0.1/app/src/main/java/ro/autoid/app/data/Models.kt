package ro.autoid.app.data

data class Product(
    val id: Long,
    val name: String,
    val sku: String,
    val permalink: String,
    val imageUrl: String?,
    val price: String,
    val stockLabel: String,
    val description: String,
    val category: String = "",
    val brand: String = "",
    val supportQuery: String = ""
)

data class ProductCategory(val id: Long, val name: String, val count: Int)
data class SupportResource(val id: Long, val title: String, val url: String, val type: String, val summary: String)
data class Order(val id:Long,val number:String,val status:String,val total:String,val dateCreated:String)
data class Customer(val id:Long?=null,val name:String="",val email:String="")
data class LoginResult(val accessToken:String,val refreshToken:String?=null,val customer:Customer?=null)
