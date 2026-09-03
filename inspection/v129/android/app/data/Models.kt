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
    val shortDescription: String = "",
    val descriptionHtml: String = "",
    val youtubeIds: List<String> = emptyList(),
    val category: String = "",
    val brand: String = "",
    val model: String = "",
    val deliveryLabel: String = "",
    val stockAutoId: Int? = null,
    val stockDistributor: Int? = null,
    val groupedStockAutoId: Int? = null,
    val msrpEuro: String = "",
    val autoIdEuro: String = "",
    val regularInclVat: String = "",
    val currentInclVat: String = "",
    val priceRangeExVat: String = "",
    val priceRangeInclVat: String = "",
    val groupedParentId: Long = 0,
    val groupedChildIds: List<Long> = emptyList(),
    val rating: Double = 0.0,
    val reviewCount: Int = 0,
    val supportQuery: String = "",
    val attributes: List<ProductAttribute> = emptyList(),
    val productType: String = "simple",
    val brandLogoUrl: String? = null,
    val groupedStockDistributor: Int? = null,
    val msrpEuroValue: Double = 0.0,
    val autoIdEuroValue: Double = 0.0,
    val regularInclVatDisplay: String = "",
    val saleInclVatDisplay: String = "",
    val categories: List<FacetItem> = emptyList()
)

data class ProductAttribute(val name: String, val values: List<String>)
data class ProductCategory(val id: Long, val name: String, val count: Int, val imageUrl: String? = null, val parent: Long = 0, val slug: String = "")
data class HomeSection(val category: ProductCategory, val products: List<Product>, val totalGrouped: Int)
data class SupportResource(val id: Long, val title: String, val url: String, val type: String, val summary: String)
data class FamilyGroup(val key: String, val label: String, val count: Int)
data class FamilyFacet(val id:Long,val name:String,val count:Int)
data class FamilyProductsPage(val products:List<Product>,val filters:List<FamilyFacet>,val selectedCategory:Long=0)
data class ProductFamily(val productId: Long, val model: String, val groups: List<FamilyGroup>, val supportAvailable: Boolean)
data class ProductReview(val id:Long,val author:String,val rating:Int,val content:String,val dateCreated:String,val verified:Boolean=false)
data class ProductReviews(val average:Double,val count:Int,val reviews:List<ProductReview>)
data class SupportSection(val key: String, val label: String, val count: Int, val resources: List<SupportResource>)
data class Order(val id:Long,val number:String,val status:String,val total:String,val dateCreated:String,val statusCode:String="",val trackingNumber:String="",val trackingUrl:String="",val carrier:String="",val reviewConsent:Boolean=false,val canPay:Boolean=false,val canCancel:Boolean=false)
data class Customer(val id:Long?=null,val name:String="",val email:String="")
data class LoginResult(val accessToken:String,val refreshToken:String?=null,val customer:Customer?=null)
data class CartLine(val product: Product, val quantity: Int)
data class AiMessage(val fromUser: Boolean, val text: String, val productIds: List<Long> = emptyList())
data class NavItem(val id:Long,val parent:Long,val title:String,val url:String,val objectType:String="",val objectId:Long=0,val nativeKind:String="none",val children:List<NavItem> = emptyList())
data class NativeContent(val id:Long,val title:String,val type:String,val content:String,val url:String)
data class PaymentMethod(val id:String,val title:String,val description:String,val enabled:Boolean=true)
data class ShippingConfig(
    val flatRateInclVat: Double = 30.25,
    val freeShippingMin: Double = 593.0,
    val taxRate: Double = 21.0,
    val title: String = "Livrare"
)
data class CheckoutConfig(
    val currency:String,
    val country:String,
    val payments:List<PaymentMethod>,
    val shipping:ShippingConfig = ShippingConfig(),
    val googleClientId:String = "",
    val stripePublishableKey:String = "",
    val stripeMode:String = ""
)
data class CheckoutResult(val orderId:Long,val number:String,val status:String,val total:String,val currency:String,val paymentMethod:String,val requiresPayment:Boolean,val accessToken:String?=null,val customer:Customer?=null,val accountCreated:Boolean=false,val stripePublishableKey:String="",val stripeClientSecret:String="",val stripePaymentIntentId:String="",val stripePaymentToken:String="",val stripeMode:String="")
data class RegistrationResult(val created:Boolean,val customerId:Long,val email:String)
data class AccountAddress(val firstName:String="",val lastName:String="",val company:String="",val address1:String="",val address2:String="",val city:String="",val state:String="",val postcode:String="",val country:String="RO",val phone:String="",val email:String="")
data class AccountAddresses(val billing:AccountAddress=AccountAddress(),val shipping:AccountAddress=AccountAddress(),val vatNumber:String="")
data class AccountProfile(val id:Long=0,val email:String="",val firstName:String="",val lastName:String="")
data class SavedPaymentMethod(val id:Long,val type:String,val label:String,val isDefault:Boolean=false)
data class OrderLineItem(val productId:Long,val name:String,val quantity:Int,val total:String,val imageUrl:String?=null)
data class OrderNote(val content:String,val createdAt:String="")
data class OrderDetail(
    val id:Long,val number:String,val status:String,val statusLabel:String,val total:String,val currency:String,val createdAt:String,
    val subtotal:String,val discountTotal:String,val shippingTotal:String,val taxTotal:String,val paymentMethod:String,val shippingMethod:String,
    val customerNote:String,val carrier:String="",val trackingNumber:String="",val trackingUrl:String="",val reviewConsent:Boolean=false,val canPay:Boolean=false,val canCancel:Boolean=false,val billing:AccountAddress,val shipping:AccountAddress,val items:List<OrderLineItem>,val notes:List<OrderNote>
)


data class FacetItem(val id:Long,val name:String,val slug:String="",val count:Int=0,val parentId:Long=0,val depth:Int=0,val brandId:Long=0,val categoryId:Long=0)
data class CatalogFacets(val minPrice:Double,val maxPrice:Double,val brands:List<FacetItem>,val models:List<FacetItem>,val subcategories:List<ProductCategory>,val liquidationCategories:List<FacetItem> = emptyList(),val specialCategory:String = "",val categoryHierarchy:List<FacetItem> = emptyList())
data class HomeV100Data(val sections:List<HomeSection>,val recommended:List<Product>,val offers:List<Product>,val categories:List<ProductCategory>,val liquidationCategory:ProductCategory? = null)


data class HeroSlideV103(
    val id: String,
    val title: String,
    val description: String,
    val imageUrl: String? = null,
    val primaryLabel: String = "",
    val primaryType: String = "",
    val primaryTargetId: Long = 0,
    val secondaryLabel: String = "",
    val secondaryType: String = "",
    val secondaryTargetId: Long = 0,
    val eyebrow: String = "",
    val background: String = "#229ff2",
    val intervalMs: Long = 5500,
    val style: String = "card"
)

data class OrderPaymentSessionV127(val orderId:Long,val clientSecret:String,val paymentIntentId:String,val paymentToken:String,val publishableKey:String,val mode:String="test")


data class PushConfigV128(val enabled:Boolean=false,val projectId:String="",val applicationId:String="",val apiKey:String="",val senderId:String="")
data class PrivacyPrefsV128(val transactionalNotifications:Boolean=true,val analytics:Boolean=false,val personalization:Boolean=false,val marketing:Boolean=false)
