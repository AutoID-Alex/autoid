package ro.autoid.app.data

import android.text.Html
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URI
import java.net.URLEncoder
import java.nio.charset.StandardCharsets

class AutoIdApi {
    companion object { const val BASE="https://www.autoid.ro"; const val MOBILE="$BASE/wp-json/autoid-app/v1" }

    fun health()=runCatching{get("$MOBILE/health");true}.getOrDefault(false)
    fun pushConfigV128():PushConfigV128{val o=JSONObject(get("$MOBILE/push/config"));return PushConfigV128(o.optBoolean("enabled"),o.optString("project_id"),o.optString("application_id"),o.optString("api_key"),o.optString("sender_id"))}
    fun registerPushV128(token:String,fcmToken:String,prefs:PrivacyPrefsV128):Boolean{val b=JSONObject().put("token",fcmToken).put("platform","android").put("transactional_notifications",prefs.transactionalNotifications).put("analytics",prefs.analytics).put("personalization",prefs.personalization).put("marketing",prefs.marketing);return JSONObject(post("$MOBILE/push/register",b.toString(),token)).optBoolean("registered")}
    fun unregisterPushV128(token:String,fcmToken:String):Boolean{val b=JSONObject().put("token",fcmToken);return JSONObject(post("$MOBILE/push/unregister",b.toString(),token)).optBoolean("unregistered")}
    fun privacyV128(token:String):PrivacyPrefsV128{val o=JSONObject(get("$MOBILE/me/privacy",token));return PrivacyPrefsV128(o.optBoolean("transactional_notifications",true),o.optBoolean("analytics"),o.optBoolean("personalization"),o.optBoolean("marketing"))}
    fun savePrivacyV128(token:String,v:PrivacyPrefsV128):PrivacyPrefsV128{val b=JSONObject().put("transactional_notifications",v.transactionalNotifications).put("analytics",v.analytics).put("personalization",v.personalization).put("marketing",v.marketing);val o=JSONObject(post("$MOBILE/me/privacy",b.toString(),token));return PrivacyPrefsV128(o.optBoolean("transactional_notifications",true),o.optBoolean("analytics"),o.optBoolean("personalization"),o.optBoolean("marketing"))}

    fun products(search:String="",category:Long?=null,page:Int=1,orderBy:String="date"):List<Product>{
        val qs=mutableListOf("per_page=12","page=$page","orderby=${enc(orderBy)}")
        if(search.isNotBlank())qs+="search=${enc(search)}"; category?.takeIf{it>0}?.let{qs+="category=$it"}
        val a=JSONObject(get("$MOBILE/products?${qs.joinToString("&")}")).optJSONArray("products")?:JSONArray()
        return (0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::product)}
    }

    fun homeSections():List<HomeSection>{
        val a=JSONObject(get("$MOBILE/home")).optJSONArray("sections")?:JSONArray()
        return (0 until a.length()).mapNotNull{i->
            val o=a.optJSONObject(i)?:return@mapNotNull null
            val c=o.optJSONObject("category")?.let(::category)?:return@mapNotNull null
            val p=o.optJSONArray("products")?:JSONArray()
            HomeSection(c,(0 until p.length()).mapNotNull{j->p.optJSONObject(j)?.let(::product)},o.optInt("total_grouped"))
        }
    }

    fun heroSlidesJsonV126():String=get("$MOBILE/hero?_=${System.currentTimeMillis()}")
    fun heroSlidesFromJsonV126(raw:String):List<HeroSlideV103>{
        val root=JSONObject(raw)
        val a=root.optJSONArray("hero_slides")?:JSONArray()
        return (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{o->
            HeroSlideV103(
                id=o.optString("id","slide-$i"),
                title=html(o.optString("title")),
                description=html(o.optString("description")),
                imageUrl=o.optString("image").ifBlank{null},
                primaryLabel=html(o.optString("primary_label")),
                primaryType=o.optString("primary_type"),
                primaryTargetId=o.optLong("primary_target_id",0),
                secondaryLabel=html(o.optString("secondary_label")),
                secondaryType=o.optString("secondary_type"),
                secondaryTargetId=o.optLong("secondary_target_id",0),
                eyebrow=html(o.optString("eyebrow")),
                background=o.optString("background","#229ff2"),
                intervalMs=o.optLong("interval_ms",5500).coerceIn(2500,20000),
                style=o.optString("style","card").ifBlank { "card" }
            )
        }}
    }
    fun heroSlidesV103():List<HeroSlideV103> = heroSlidesFromJsonV126(heroSlidesJsonV126())

    fun homeDataJsonV126():String=get("$MOBILE/home")
    fun homeDataFromJsonV126(raw:String):HomeV100Data{
        val root=JSONObject(raw)
        fun ps(key:String):List<Product>{val a=root.optJSONArray(key)?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::product)}}
        val sa=root.optJSONArray("sections")?:JSONArray()
        val sections=(0 until sa.length()).mapNotNull{i->val o=sa.optJSONObject(i)?:return@mapNotNull null;val c=o.optJSONObject("category")?.let(::category)?:return@mapNotNull null;val a=o.optJSONArray("products")?:JSONArray();HomeSection(c,(0 until a.length()).mapNotNull{j->a.optJSONObject(j)?.let(::product)},o.optInt("total_grouped"))}
        val ca=root.optJSONArray("categories")?:JSONArray();val cats=(0 until ca.length()).mapNotNull{ca.optJSONObject(it)?.let(::category)}
        val liquidation=root.optJSONObject("liquidation_category")?.let(::category)
        return HomeV100Data(sections,ps("recommended"),ps("offers"),cats,liquidation)
    }
    fun homeData():HomeV100Data = homeDataFromJsonV126(homeDataJsonV126())

    fun catalogProducts(search:String="",category:Long?=null,page:Int=1,sort:String="stock_autoid",brand:Long?=null,model:Long?=null,minPrice:Double?=null,maxPrice:Double?=null,secondaryCategory:Long?=null):List<Product>{
        val q=mutableListOf("per_page=12","page=$page","orderby=${enc(sort)}")
        if(search.isNotBlank())q+="search=${enc(search)}";category?.takeIf{it>0}?.let{q+="category=$it"};secondaryCategory?.takeIf{it>0}?.let{q+="secondary_category=$it"};brand?.takeIf{it>0}?.let{q+="brand=$it"};model?.takeIf{it>0}?.let{q+="model=$it"};minPrice?.takeIf{it>0}?.let{q+="min_price=$it"};maxPrice?.takeIf{it>0}?.let{q+="max_price=$it"}
        val a=JSONObject(get("$MOBILE/products?${q.joinToString("&")}")).optJSONArray("products")?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::product)}
    }

    fun catalogFacets(category:Long?=null,secondaryCategory:Long?=null,brand:Long?=null,model:Long?=null):CatalogFacets{
        val q=mutableListOf<String>()
        category?.takeIf{it>0}?.let{q+="category=$it"}
        secondaryCategory?.takeIf{it>0}?.let{q+="secondary_category=$it"}
        brand?.takeIf{it>0}?.let{q+="brand=$it"}
        model?.takeIf{it>0}?.let{q+="model=$it"}
        val root=JSONObject(get("$MOBILE/catalog/facets"+(if(q.isEmpty())"" else "?"+q.joinToString("&"))))
        fun fs(key:String):List<FacetItem>{val a=root.optJSONArray(key)?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let{FacetItem(it.optLong("id"),html(it.optString("name")),it.optString("slug"),it.optInt("count",0),it.optLong("parent",0),it.optInt("depth",0),it.optLong("brand_id",0),it.optLong("category_id",0))}}}
        val pr=root.optJSONObject("price")?:JSONObject();val sc=root.optJSONArray("subcategories")?:JSONArray()
        return CatalogFacets(pr.optDouble("min",0.0),pr.optDouble("max",0.0),fs("brands"),fs("models"),(0 until sc.length()).mapNotNull{sc.optJSONObject(it)?.let(::category)},fs("liquidation_categories"),root.optString("special_category"),fs("category_hierarchy"))
    }

    fun sendRfq(name:String,email:String,company:String,phone:String,message:String,lines:List<CartLine>):Boolean{val a=JSONArray();lines.forEach{a.put(JSONObject().put("id",it.product.id).put("qty",it.quantity))};val b=JSONObject().put("name",name).put("email",email).put("company",company).put("phone",phone).put("message",message).put("products",a);return JSONObject(post("$MOBILE/rfq",b.toString())).optBoolean("sent")}
    fun requestConsultation(name:String,email:String,company:String,phone:String,message:String):Boolean{val b=JSONObject().put("name",name).put("email",email).put("company",company).put("phone",phone).put("message",message);return JSONObject(post("$MOBILE/consultation/request",b.toString())).optBoolean("sent")}

    fun product(id:Long)=product(JSONObject(get("$MOBILE/products/$id")))

    fun productFamily(id:Long):ProductFamily{
        val o=JSONObject(get("$MOBILE/products/$id/family"));val a=o.optJSONArray("groups")?:JSONArray()
        return ProductFamily(o.optLong("product_id",id),o.optJSONObject("model")?.optString("label").orEmpty(),(0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{FamilyGroup(it.optString("key"),html(it.optString("label")),it.optInt("count"))}},o.optBoolean("support_available"))
    }

    fun familyProductsPage(id:Long,group:String,page:Int=1,category:Long=0):FamilyProductsPage{val url="$MOBILE/products/$id/family/${enc(group)}?page=$page&per_page=50"+(if(category>0)"&category=$category" else "");val o=JSONObject(get(url));val a=o.optJSONArray("products")?:JSONArray();val f=o.optJSONArray("filters")?:JSONArray();return FamilyProductsPage((0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::product)},(0 until f.length()).mapNotNull{i->f.optJSONObject(i)?.let{FamilyFacet(it.optLong("id"),html(it.optString("name")),it.optInt("count"))}},o.optLong("selected_category",0))}
    fun familyProducts(id:Long,group:String,page:Int=1):List<Product> = familyProductsPage(id,group,page).products

    fun productReviews(id:Long,page:Int=1):ProductReviews{
        val o=JSONObject(get("$MOBILE/products/$id/reviews?page=$page&per_page=8"));val a=o.optJSONArray("reviews")?:JSONArray()
        return ProductReviews(o.optDouble("average",0.0),o.optInt("count",0),(0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{r->ProductReview(r.optLong("id"),html(r.optString("author")),r.optInt("rating"),html(r.optString("content")),r.optString("date_created"),r.optBoolean("verified"))}})
    }

    fun submitProductReview(id:Long,rating:Int,content:String,name:String="",email:String="",token:String?=null):Boolean{
        val b=JSONObject().put("rating",rating).put("content",content).put("name",name).put("email",email)
        return JSONObject(post("$MOBILE/products/$id/reviews",b.toString(),token)).optBoolean("created")
    }

    fun productSupport(id:Long):List<SupportSection>{
        val a=JSONObject(get("$MOBILE/products/$id/support")).optJSONArray("sections")?:JSONArray()
        return(0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{s->val r=s.optJSONArray("resources")?:JSONArray();SupportSection(s.optString("key"),html(s.optString("label")),s.optInt("count"),(0 until r.length()).mapNotNull{j->r.optJSONObject(j)?.let(::supportResource)})}}
    }

    fun searchSuggestions(query:String):List<Product>{if(query.length<2)return emptyList();val a=JSONObject(get("$MOBILE/search?q=${enc(query)}")).optJSONArray("suggestions")?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::product)}}

    fun navigation():List<NavItem>{
        val a=JSONObject(get("$MOBILE/navigation")).optJSONArray("items")?:JSONArray()
        fun parse(x:JSONArray):List<NavItem>{val out=mutableListOf<NavItem>();for(i in 0 until x.length()){val o=x.optJSONObject(i)?:continue;out+=NavItem(o.optLong("id"),o.optLong("parent"),html(o.optString("title")),o.optString("url"),o.optString("object"),o.optLong("object_id"),o.optString("native_kind","none"),parse(o.optJSONArray("children")?:JSONArray()))};return out}
        return parse(a)
    }

    fun content(id:Long):NativeContent{val o=JSONObject(get("$MOBILE/content?id=$id"));return NativeContent(o.optLong("id"),html(o.optString("title")),o.optString("type"),html(o.optString("content")),o.optString("url"))}
    fun aiChat(message:String,productId:Long?=null):String{val b=JSONObject().put("message",message);productId?.let{b.put("product_id",it)};return html(JSONObject(post("$MOBILE/ai/chat",b.toString())).optString("answer")).ifBlank{error("Asistentul AI nu a returnat răspuns.")}}

    fun categories(parent:Long?=null):List<ProductCategory>{val u=if(parent!=null&&parent>0)"$MOBILE/categories?parent=$parent" else "$MOBILE/categories";val a=JSONObject(get(u)).optJSONArray("categories")?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::category)}}

    fun checkoutConfig():CheckoutConfig{
        val o=JSONObject(get("$MOBILE/checkout/config"));val a=o.optJSONArray("payments")?:JSONArray();val sh=o.optJSONObject("shipping")?:JSONObject()
        return CheckoutConfig(
            o.optString("currency","RON"),
            o.optString("country","RO"),
            (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{PaymentMethod(it.optString("id"),html(it.optString("title")),html(it.optString("description")),it.optBoolean("enabled",true))}},
            ShippingConfig(sh.optDouble("flat_rate_incl_vat",30.25),sh.optDouble("free_shipping_min",593.0),sh.optDouble("tax_rate",21.0),html(sh.optString("title","Livrare"))),
            o.optString("google_client_id"),
            o.optString("stripe_publishable_key"),
            o.optString("stripe_mode")
        )
    }

    fun createOrder(lines:List<CartLine>,first:String,last:String,company:String,vat:String,email:String,phone:String,address1:String,address2:String,city:String,state:String,postcode:String,country:String,note:String,payment:String):CheckoutResult{
        val b=JSONObject().put("payment_method",payment).put("vat_number",vat).put("customer_note",note)
        b.put("billing",JSONObject().put("first_name",first).put("last_name",last).put("company",company).put("email",email).put("phone",phone).put("address_1",address1).put("address_2",address2).put("city",city).put("state",state).put("postcode",postcode).put("country",country))
        val a=JSONArray();lines.forEach{a.put(JSONObject().put("product_id",it.product.id).put("quantity",it.quantity))};b.put("line_items",a)
        val o=JSONObject(post("$MOBILE/checkout/order",b.toString()));return CheckoutResult(o.optLong("order_id"),o.optString("number"),o.optString("status"),o.optString("total"),o.optString("currency","RON"),o.optString("payment_method",payment),o.optBoolean("requires_payment"))
    }

    fun createOrderV114(
        lines:List<CartLine>, email:String, phone:String,
        shippingFirst:String, shippingLast:String, shippingAddress1:String, shippingAddress2:String, shippingCity:String, shippingState:String, shippingPostcode:String, shippingCountry:String,
        billingFirst:String, billingLast:String, billingCompany:String, billingAddress1:String, billingAddress2:String, billingCity:String, billingState:String, billingPostcode:String, billingCountry:String,
        vat:String, note:String, payment:String, reviewConsent:Boolean, createAccount:Boolean, deliveryMode:String="delivery", token:String?=null
    ):CheckoutResult{
        val b=JSONObject().put("payment_method",payment).put("vat_number",vat).put("customer_note",note).put("review_consent",reviewConsent).put("create_account",createAccount).put("delivery_mode",deliveryMode)
        b.put("shipping",JSONObject().put("first_name",shippingFirst).put("last_name",shippingLast).put("address_1",shippingAddress1).put("address_2",shippingAddress2).put("city",shippingCity).put("state",shippingState).put("postcode",shippingPostcode).put("country",shippingCountry))
        b.put("billing",JSONObject().put("first_name",billingFirst).put("last_name",billingLast).put("company",billingCompany).put("email",email).put("phone",phone).put("address_1",billingAddress1).put("address_2",billingAddress2).put("city",billingCity).put("state",billingState).put("postcode",billingPostcode).put("country",billingCountry))
        val a=JSONArray();lines.forEach{a.put(JSONObject().put("product_id",it.product.id).put("quantity",it.quantity))};b.put("line_items",a)
        val o=JSONObject(post("$MOBILE/checkout/order",b.toString(),token));val u=o.optJSONObject("customer");return CheckoutResult(o.optLong("order_id"),o.optString("number"),o.optString("status"),o.optString("total"),o.optString("currency","RON"),o.optString("payment_method",payment),o.optBoolean("requires_payment"),o.optString("access_token").ifBlank{null},u?.let{Customer(if(it.has("id"))it.optLong("id") else null,listOf(it.optString("first_name"),it.optString("last_name")).filter(String::isNotBlank).joinToString(" ").ifBlank{it.optString("name")},it.optString("email"))},o.optBoolean("account_created"),o.optString("stripe_publishable_key"),o.optString("stripe_client_secret"),o.optString("stripe_payment_intent_id"),o.optString("stripe_payment_token"),o.optString("stripe_mode"))
    }

    fun confirmStripePayment(orderId:Long,paymentIntentId:String,paymentToken:String,token:String?=null):Boolean{
        val b=JSONObject().put("order_id",orderId).put("payment_intent_id",paymentIntentId).put("payment_token",paymentToken)
        return JSONObject(post("$MOBILE/payments/stripe/confirm",b.toString(),token)).optBoolean("paid",false)
    }

    private fun accountAddress(o:JSONObject)=AccountAddress(o.optString("first_name"),o.optString("last_name"),o.optString("company"),o.optString("address_1"),o.optString("address_2"),o.optString("city"),o.optString("state"),o.optString("postcode"),o.optString("country","RO"),o.optString("phone"),o.optString("email"))

    fun accountAddresses(token:String):AccountAddresses{
        val o=JSONObject(get("$MOBILE/me/addresses",token));return AccountAddresses(accountAddress(o.optJSONObject("billing")?:JSONObject()),accountAddress(o.optJSONObject("shipping")?:JSONObject()),o.optString("vat_number"))
    }


    fun accountProfile(token:String):AccountProfile{
        val raw=JSONObject(get("$MOBILE/me/profile",token));val o=raw.optJSONObject("profile")?:raw
        return AccountProfile(o.optLong("id"),o.optString("email"),o.optString("first_name"),o.optString("last_name"))
    }

    fun saveAccountProfile(token:String,first:String,last:String,email:String,newPassword:String=""):AccountProfile{
        val body=JSONObject().put("first_name",first).put("last_name",last).put("email",email)
        if(newPassword.isNotBlank())body.put("new_password",newPassword)
        val raw=JSONObject(post("$MOBILE/me/profile",body.toString(),token));val o=raw.optJSONObject("profile")?:raw
        return AccountProfile(o.optLong("id"),o.optString("email"),o.optString("first_name"),o.optString("last_name"))
    }

    fun saveAccountAddresses(token:String,a:AccountAddresses):AccountAddresses{
        fun obj(v:AccountAddress)=JSONObject().put("first_name",v.firstName).put("last_name",v.lastName).put("company",v.company).put("address_1",v.address1).put("address_2",v.address2).put("city",v.city).put("state",v.state).put("postcode",v.postcode).put("country",v.country).put("phone",v.phone).put("email",v.email)
        val raw=JSONObject(post("$MOBILE/me/addresses",JSONObject().put("billing",obj(a.billing)).put("shipping",obj(a.shipping)).put("vat_number",a.vatNumber).toString(),token))
        return AccountAddresses(accountAddress(raw.optJSONObject("billing")?:JSONObject()),accountAddress(raw.optJSONObject("shipping")?:JSONObject()),raw.optString("vat_number"))
    }

    fun savedPaymentMethods(token:String):List<SavedPaymentMethod>{
        val a=JSONObject(get("$MOBILE/me/payment-methods",token)).optJSONArray("methods")?:JSONArray()
        return (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{o->SavedPaymentMethod(o.optLong("id"),o.optString("type"),o.optString("label"),o.optBoolean("is_default"))}}
    }

    fun paymentMethodAction(token:String,id:Long,action:String):List<SavedPaymentMethod>{
        val body=JSONObject().put("token_id",id).put("action",action)
        val a=JSONObject(post("$MOBILE/me/payment-methods",body.toString(),token)).optJSONArray("methods")?:JSONArray()
        return (0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{o->SavedPaymentMethod(o.optLong("id"),o.optString("type"),o.optString("label"),o.optBoolean("is_default"))}}
    }

    fun orderDetail(token:String,id:Long):OrderDetail{
        val o=JSONObject(get("$MOBILE/me/orders/$id",token))
        val ia=o.optJSONArray("items")?:JSONArray();val na=o.optJSONArray("notes")?:JSONArray()
        return OrderDetail(
            o.optLong("id"),o.optString("number"),o.optString("status"),o.optString("status_label"),o.optString("total"),o.optString("currency","RON"),o.optString("created_at"),
            o.optString("subtotal"),o.optString("discount_total"),o.optString("shipping_total"),o.optString("tax_total"),o.optString("payment_method"),o.optString("shipping_method"),o.optString("customer_note"),o.optString("carrier"),o.optString("tracking_number"),o.optString("tracking_url"),o.optBoolean("review_consent"),o.optBoolean("can_pay"),o.optBoolean("can_cancel"),
            accountAddress(o.optJSONObject("billing")?:JSONObject()),accountAddress(o.optJSONObject("shipping")?:JSONObject()),
            (0 until ia.length()).mapNotNull{i->ia.optJSONObject(i)?.let{x->OrderLineItem(x.optLong("product_id"),html(x.optString("name")),x.optInt("quantity"),x.optString("total"),x.optString("image").ifBlank{null})}},
            (0 until na.length()).mapNotNull{i->na.optJSONObject(i)?.let{x->OrderNote(html(x.optString("content")),x.optString("created_at"))}}
        )
    }


    fun orderActionV127(token:String,id:Long,action:String):OrderPaymentSessionV127?{
        val o=JSONObject(post("$MOBILE/me/orders/$id/action",JSONObject().put("action",action).toString(),token))
        if(action!="pay")return null
        return OrderPaymentSessionV127(o.optLong("order_id",id),o.optString("stripe_client_secret"),o.optString("stripe_payment_intent_id"),o.optString("stripe_payment_token"),o.optString("stripe_publishable_key"),o.optString("stripe_mode","test"))
    }

    fun googleLogin(idToken:String):LoginResult{
        val root=JSONObject(post("$MOBILE/auth/google",JSONObject().put("id_token",idToken).toString()));val d=root.optJSONObject("data")?:root
        val token=d.optString("access_token",d.optString("token"));if(token.isBlank())error(d.optString("message","Autentificare Google eșuată"))
        val u=d.optJSONObject("customer")?:d.optJSONObject("user")
        return LoginResult(token,d.optString("refresh_token").ifBlank{null},u?.let{Customer(if(it.has("id"))it.optLong("id") else null,listOf(it.optString("first_name"),it.optString("last_name")).filter(String::isNotBlank).joinToString(" ").ifBlank{it.optString("name")},it.optString("email"))})
    }

    fun register(email:String,password:String,first:String,last:String,company:String,vat:String):RegistrationResult{val b=JSONObject().put("email",email).put("password",password).put("first_name",first).put("last_name",last).put("company",company).put("vat_number",vat);val o=JSONObject(post("$MOBILE/register",b.toString()));return RegistrationResult(o.optBoolean("created"),o.optLong("customer_id"),o.optString("email"))}

    fun support(search:String):List<SupportResource>{if(search.isBlank())return emptyList();val a=JSONObject(get("$MOBILE/support?search=${enc(search)}")).optJSONArray("resources")?:JSONArray();return(0 until a.length()).mapNotNull{a.optJSONObject(it)?.let(::supportResource)}}

    fun login(login:String,password:String):LoginResult{val b=JSONObject().put("login",login).put("username",login).put("email",login).put("password",password);val root=JSONObject(post("$MOBILE/auth/login",b.toString()));val d=root.optJSONObject("data")?:root;val token=d.optString("access_token",d.optString("token"));if(token.isBlank())error(d.optString("message","Autentificare eșuată"));val u=d.optJSONObject("customer")?:d.optJSONObject("user");return LoginResult(token,d.optString("refresh_token").ifBlank{null},u?.let{Customer(if(it.has("id"))it.optLong("id") else null,listOf(it.optString("first_name"),it.optString("last_name")).filter(String::isNotBlank).joinToString(" ").ifBlank{it.optString("name")},it.optString("email"))})}

    fun orders(token:String):List<Order>{val raw=get("$MOBILE/me/orders",token);val a=if(raw.trimStart().startsWith("["))JSONArray(raw) else JSONObject(raw).optJSONArray("orders")?:JSONObject(raw).optJSONObject("data")?.optJSONArray("orders")?:JSONArray();return(0 until a.length()).mapNotNull{i->val o=a.optJSONObject(i)?:return@mapNotNull null;Order(o.optLong("id"),o.optString("number",o.optLong("id").toString()),o.optString("status_label",o.optString("status")),total(o),o.optString("created_at",o.optString("date_created")),o.optString("status"),o.optString("tracking_number"),o.optString("tracking_url"),o.optString("carrier"),o.optBoolean("review_consent"),o.optBoolean("can_pay"),o.optBoolean("can_cancel"))}}

    private fun category(o:JSONObject)=ProductCategory(o.optLong("id"),html(o.optString("name")),o.optInt("count"),o.optString("image").ifBlank{null},o.optLong("parent"),o.optString("slug"))
    private fun supportResource(o:JSONObject)=SupportResource(o.optLong("id"),html(o.optString("title")),o.optString("url"),o.optString("type","Resursă"),html(o.optString("summary")))
    private fun product(o:JSONObject):Product{
        val attrs=o.optJSONArray("attributes")?:JSONArray();val images=o.optJSONArray("images")?:JSONArray();val children=o.optJSONArray("grouped_child_ids")?:JSONArray();val cats=o.optJSONArray("categories")?:JSONArray();val youtube=o.optJSONArray("youtube_ids")?:JSONArray()
        return Product(id=o.optLong("id"),name=html(o.optString("name")),sku=o.optString("sku"),permalink=o.optString("permalink"),imageUrl=o.optString("image").ifBlank{null},images=(0 until images.length()).mapNotNull{images.optString(it).takeIf(String::isNotBlank)},price=o.optString("price_display",o.optString("price","Preț la cerere")),regularPrice=o.optString("regular_price"),salePrice=o.optString("sale_price"),currency=o.optString("currency","RON"),onSale=o.optBoolean("on_sale"),stockLabel=o.optString("stock_label"),inStock=o.optBoolean("in_stock",true),description=html(o.optString("description",o.optString("short_description"))),shortDescription=html(o.optString("short_description")),descriptionHtml=o.optString("description_html"),youtubeIds=(0 until youtube.length()).mapNotNull{youtube.optString(it).takeIf(String::isNotBlank)},category=html(o.optString("category")),brand=html(o.optString("brand")),model=html(o.optString("model")),deliveryLabel=html(o.optString("delivery_label")),stockAutoId=o.optInt("stock_autoid").takeIf{o.has("stock_autoid")&&!o.isNull("stock_autoid")},stockDistributor=o.optInt("stock_distributor").takeIf{o.has("stock_distributor")&&!o.isNull("stock_distributor")},groupedStockAutoId=o.optInt("grouped_stock_autoid").takeIf{o.has("grouped_stock_autoid")&&!o.isNull("grouped_stock_autoid")},msrpEuro=html(o.optString("pret_lista_display")),autoIdEuro=html(o.optString("pret_autoid_euro_display")),regularInclVat=html(o.optString("regular_incl_vat_display")),currentInclVat=html(o.optString("current_incl_vat_display")),priceRangeExVat=html(o.optString("price_range_ex_vat_display")),priceRangeInclVat=html(o.optString("price_range_incl_vat_display")),groupedParentId=o.optLong("grouped_parent_id"),groupedChildIds=(0 until children.length()).map{children.optLong(it)},rating=o.optDouble("rating",0.0),reviewCount=o.optInt("review_count",0),supportQuery=o.optString("support_query",o.optString("sku")),attributes=(0 until attrs.length()).mapNotNull{i->attrs.optJSONObject(i)?.let{a->val vals=a.optJSONArray("values")?:JSONArray();ProductAttribute(html(a.optString("name")),(0 until vals.length()).map{vals.optString(it)})}},productType=o.optString("product_type","simple"),brandLogoUrl=o.optString("brand_logo").ifBlank{null},groupedStockDistributor=o.optInt("grouped_stock_distributor").takeIf{o.has("grouped_stock_distributor")&&!o.isNull("grouped_stock_distributor")},msrpEuroValue=o.optDouble("pret_lista",0.0),autoIdEuroValue=o.optDouble("pret_autoid_euro",0.0),regularInclVatDisplay=html(o.optString("regular_price_incl_vat_display")),saleInclVatDisplay=html(o.optString("sale_price_incl_vat_display")),categories=(0 until cats.length()).mapNotNull{i->cats.optJSONObject(i)?.let{c->FacetItem(c.optLong("id"),html(c.optString("name")),c.optString("slug"))}})
    }

    private fun total(o:JSONObject)=o.optString("total")+if(o.optString("currency","RON")=="EUR")" €" else " lei"
    private fun html(s:String):String {
        var out=s
        repeat(2){ out=Html.fromHtml(out,Html.FROM_HTML_MODE_LEGACY).toString() }
        return out.replace("&amp;nbsp;"," ",ignoreCase=true).replace("&nbsp;"," ",ignoreCase=true).replace("&#160;"," ",ignoreCase=true).replace("&#xA0;"," ",ignoreCase=true).replace('\u00A0',' ').replace(Regex("\\s+")," ").trim()
    }
    private fun enc(v:String)=URLEncoder.encode(v,"UTF-8")
    private fun get(url:String,token:String?=null)=request("GET",url,null,token)
    private fun post(url:String,body:String,token:String?=null)=request("POST",url,body,token)
    private fun request(method:String,url:String,body:String?,token:String?):String{val c=URI(url).toURL().openConnection() as HttpURLConnection;c.requestMethod=method;c.connectTimeout=12000;c.readTimeout=25000;c.useCaches=false;c.setRequestProperty("Accept","application/json");c.setRequestProperty("Cache-Control","no-cache, no-store, max-age=0");c.setRequestProperty("Pragma","no-cache");c.setRequestProperty("User-Agent","AutoID-Android/1.0.28");token?.let{c.setRequestProperty("Authorization","Bearer $it")};if(body!=null){c.doOutput=true;c.setRequestProperty("Content-Type","application/json");c.outputStream.use{it.write(body.toByteArray(StandardCharsets.UTF_8))}};val status=c.responseCode;val text=(if(status in 200..299)c.inputStream else c.errorStream)?.bufferedReader()?.use{it.readText()}.orEmpty();c.disconnect();if(status !in 200..299)error(runCatching{JSONObject(text).optString("message",text)}.getOrDefault(text).ifBlank{"HTTP $status"});return text}
}
