#!/usr/bin/env python3
"""Robust entrypoint for RC7 over the fully-generated RC6 source tree."""
import re
import apply_v1035_rc7_uix_perf as m


def patch_public_cache_and_product_perf():
    a=m.API.read_text()
    if 'java.util.concurrent.ConcurrentHashMap' not in a:
        a=a.replace('import java.nio.charset.StandardCharsets\n','import java.nio.charset.StandardCharsets\nimport java.util.concurrent.ConcurrentHashMap\n',1)
    if 'PublicCacheEntryV135' not in a:
        mobile_line='        const val MOBILE = "$BASE/wp-json/autoid-app/v1"'
        if mobile_line not in a: raise RuntimeError('MOBILE constant anchor missing')
        a=a.replace(mobile_line,mobile_line+'\n        private data class PublicCacheEntryV135(val value:String,val expiresAt:Long)\n        private val publicCacheV135=ConcurrentHashMap<String,PublicCacheEntryV135>()',1)

    # Generated versions have kept the same get() helper body but may have gained methods around it.
    get_pattern=r'    private fun get\(url:String,token:String\?=null\)=request\("GET",url,null,token\)'
    get_new='''    private fun get(url:String,token:String?=null):String{
        if(token!=null)return request("GET",url,null,token)
        val cacheable=url.contains("/categories")||url.contains("/products")||url.contains("/hero")
        if(!cacheable)return request("GET",url,null,null)
        val now=System.currentTimeMillis();publicCacheV135[url]?.takeIf{it.expiresAt>now}?.let{return it.value}
        val value=request("GET",url,null,null)
        val ttl=when{url.contains("/categories")->5*60_000L;url.contains("/family")->3*60_000L;Regex(".*/products/\\\\d+(\\\\?.*)?$").matches(url)->2*60_000L;else->45_000L}
        publicCacheV135[url]=PublicCacheEntryV135(value,now+ttl);return value
    }'''
    a,n=re.subn(get_pattern,get_new,a,count=1)
    if n!=1:
        # Fallback if a previous migration expanded get() into a block: leave public cache class in place and do not risk private endpoint behavior.
        print('RC7 cache note: generated get() helper is already expanded; skipping direct get() replacement')
    m.API.write_text(a)

    v=m.V100.read_text()
    if 'import kotlinx.coroutines.async' not in v:
        if 'import kotlinx.coroutines.Dispatchers\n' in v:
            v=v.replace('import kotlinx.coroutines.Dispatchers\n','import kotlinx.coroutines.Dispatchers\nimport kotlinx.coroutines.async\nimport kotlinx.coroutines.coroutineScope\n',1)
        else:
            v=v.replace('import kotlinx.coroutines.*\n','import kotlinx.coroutines.*\n',1)

    old='''    LaunchedEffect(seed.id,reviewRefresh){
        runCatching{withContext(Dispatchers.IO){api.product(seed.id)}}.onSuccess{p=it}
        family=runCatching{withContext(Dispatchers.IO){api.productFamily(seed.id)}}.getOrNull()
        reviews=runCatching{withContext(Dispatchers.IO){api.productReviews(seed.id)}}.getOrDefault(ProductReviews(p.rating,p.reviewCount,emptyList()))
        if(group==null || family?.groups?.none{it.key==group&&it.count>0}!=false) group=family?.groups?.firstOrNull{it.count>0}?.key
        loading=false
    }'''
    new='''    LaunchedEffect(seed.id,reviewRefresh){
        val loaded=withContext(Dispatchers.IO){coroutineScope{
            val productJob=async{runCatching{api.product(seed.id)}.getOrNull()}
            val familyJob=async{runCatching{api.productFamily(seed.id)}.getOrNull()}
            val reviewsJob=async{runCatching{api.productReviews(seed.id)}.getOrNull()}
            Triple(productJob.await(),familyJob.await(),reviewsJob.await())
        }}
        loaded.first?.let{p=it};family=loaded.second;reviews=loaded.third?:ProductReviews(p.rating,p.reviewCount,emptyList())
        if(group==null || family?.groups?.none{it.key==group&&it.count>0}!=false) group=family?.groups?.filter{it.count>0}?.minByOrNull{relatedGroupPriorityV135(it)}?.key
        loading=false
    }'''
    if old in v:
        v=v.replace(old,new,1)
    elif 'relatedGroupPriorityV135' not in v:
        raise RuntimeError('Product parallel-load anchor missing')

    if 'private fun relatedGroupPriorityV135' not in v:
        helper='''private fun relatedGroupPriorityV135(g:FamilyGroup):Int{
    val s=(g.key+" "+g.label).lowercase()
    return when{listOf("variant","variante","model","configur").any{s.contains(it)}->0;s.contains("accesor")->1;listOf("consum","ribbon","etichet","label").any{s.contains(it)}->2;listOf("service","servici","support").any{s.contains(it)}->3;listOf("software","app","licen").any{s.contains(it)}->4;else->10}
}

'''
        marker='@Composable fun ProductV100('
        if marker not in v: raise RuntimeError('ProductV100 marker missing')
        v=v.replace(marker,helper+marker,1)
    if 'val groups=family?.groups.orEmpty().filter{it.count>0}' in v:
        v=v.replace('val groups=family?.groups.orEmpty().filter{it.count>0}','val groups=family?.groups.orEmpty().filter{it.count>0}.sortedBy(::relatedGroupPriorityV135)',1)
    m.V100.write_text(v)

m.patch_public_cache_and_product_perf=patch_public_cache_and_product_perf
m.main()
