from pathlib import Path
import re

APP = Path('android-v0.1/app')

# 1) Product model: expose all category slugs so the client can enforce strict Home sections.
p = APP / 'src/main/java/ro/autoid/app/data/Models.kt'
s = p.read_text()
if 'val categorySlugs:' not in s:
    old = '    val saleInclVatDisplay: String = ""\n)'
    new = '    val saleInclVatDisplay: String = "",\n    val categorySlugs: List<String> = emptyList()\n)'
    if old not in s:
        raise SystemExit('Models Product tail not found')
    s = s.replace(old, new, 1)
p.write_text(s)

# 2) API: parse category slugs, bust stale Home caches, and guard Home data client-side.
p = APP / 'src/main/java/ro/autoid/app/data/AutoIdApi.kt'
s = p.read_text()
if 'val categoryTerms=' not in s:
    s = s.replace(
        'val attrs=o.optJSONArray("attributes")?:JSONArray();val images=o.optJSONArray("images")?:JSONArray();val children=o.optJSONArray("grouped_child_ids")?:JSONArray()',
        'val attrs=o.optJSONArray("attributes")?:JSONArray();val images=o.optJSONArray("images")?:JSONArray();val children=o.optJSONArray("grouped_child_ids")?:JSONArray();val categoryTerms=o.optJSONArray("categories")?:JSONArray()',
        1
    )
old_tail = 'regularInclVatDisplay=html(o.optString("regular_price_incl_vat_display")),saleInclVatDisplay=html(o.optString("sale_price_incl_vat_display")))'
new_tail = 'regularInclVatDisplay=html(o.optString("regular_price_incl_vat_display")),saleInclVatDisplay=html(o.optString("sale_price_incl_vat_display")),categorySlugs=(0 until categoryTerms.length()).mapNotNull{i->categoryTerms.optJSONObject(i)?.optString("slug")?.takeIf(String::isNotBlank)})'
if old_tail in s:
    s = s.replace(old_tail, new_tail, 1)
elif 'categorySlugs=' not in s:
    raise SystemExit('AutoIdApi Product tail not found')

s = s.replace('JSONObject(get("$MOBILE/home"))', 'JSONObject(get("$MOBILE/home?app_version=1.0.3"))')
old_return = 'return HomeV100Data(sections,ps("recommended"),ps("offers"),cats)'
new_return = '''val recommended=ps("recommended").filter{(it.stockAutoId?:0)>0}\n        val liquidations=ps("offers").filter{it.categorySlugs.any{slug->slug.equals("lichidari-de-stoc",ignoreCase=true)}}\n        return HomeV100Data(sections,recommended,liquidations,cats)'''
if old_return in s:
    s = s.replace(old_return, new_return, 1)
elif 'val liquidations=ps("offers")' not in s:
    raise SystemExit('homeData return anchor not found')
s = s.replace('AutoID-Android/1.0.1', 'AutoID-Android/1.0.3').replace('AutoID-Android/1.0.2', 'AutoID-Android/1.0.3')
p.write_text(s)

# 3) Exact shared loop pricing and CTAs.
p = APP / 'src/main/java/ro/autoid/app/V100Screens.kt'
s = p.read_text()

start = s.index('@Composable\nprivate fun LoopPriceBlock')
end = s.index('@Composable\nprivate fun CatalogCard', start)
loop_helpers = r'''@Composable
private fun LoopPriceBlock(p: Product) {
    val grouped = isGrouped(p)
    val msrp = p.msrpEuroValue
    val autoId = p.autoIdEuroValue
    val euroDiscount = msrp > 0 && autoId > 0 && msrp > autoId + 0.005

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(3.dp)
    ) {
        if (msrp > 0) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("MSRP: ", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Ink)
                Text(
                    "${euro(msrp)} €",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = Ink,
                    textDecoration = if (euroDiscount) androidx.compose.ui.text.style.TextDecoration.LineThrough else null
                )
            }
        }

        if (autoId > 0 && (msrp <= 0 || euroDiscount)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("AutoID: ", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Ink)
                Text("${euro(autoId)}", fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = AutoIdOrange)
                Text(" € ex. TVA", fontSize = 10.sp, color = Muted)
            }
        } else if (msrp > 0) {
            Text("ex. TVA", fontSize = 10.sp, color = Muted)
        }

        if (grouped) {
            val range = p.priceRangeInclVat
                .ifBlank { p.currentInclVat.ifBlank { p.price } }
                .replace(Regex("(?i)\\s*incl\\.?\\s*TVA\\s*$"), "")
                .trim()
            if (range.isNotBlank()) {
                Row(verticalAlignment = Alignment.Bottom) {
                    Text(
                        range,
                        modifier = Modifier.weight(1f, fill = false),
                        fontSize = 13.sp,
                        fontWeight = FontWeight.ExtraBold,
                        color = Ink,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                    Spacer(Modifier.width(4.dp))
                    Text("incl. TVA", fontSize = 10.sp, color = Muted)
                }
            }
        } else {
            val regular = p.regularInclVatDisplay.ifBlank { p.regularInclVat }
            val current = p.saleInclVatDisplay
                .ifBlank { p.currentInclVat.ifBlank { p.price } }
            val discounted = regular.isNotBlank() && current.isNotBlank() && regular != current
            Row(verticalAlignment = Alignment.Bottom) {
                if (discounted) {
                    Text(
                        regular,
                        fontSize = 11.sp,
                        color = Muted,
                        textDecoration = androidx.compose.ui.text.style.TextDecoration.LineThrough,
                        maxLines = 1
                    )
                    Spacer(Modifier.width(6.dp))
                }
                Text(
                    current,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.ExtraBold,
                    color = Ink,
                    maxLines = 1
                )
                Spacer(Modifier.width(4.dp))
                Text("incl. TVA", fontSize = 10.sp, color = Muted)
            }
        }
    }
}

@Composable
private fun LoopProductActions(
    p: Product,
    onProduct: () -> Unit,
    onCart: () -> Unit,
    onRfq: () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(7.dp)
    ) {
        if (isGrouped(p)) {
            Button(
                onClick = onProduct,
                modifier = Modifier.weight(1f).height(46.dp),
                contentPadding = PaddingValues(horizontal = 5.dp)
            ) {
                Text("Detalii produs", fontSize = 10.sp, maxLines = 1)
            }
        } else {
            Button(
                onClick = onCart,
                modifier = Modifier.weight(1f).height(46.dp),
                contentPadding = PaddingValues(horizontal = 5.dp)
            ) {
                Text("Adaugă în coș", fontSize = 10.sp, maxLines = 1)
            }
        }
        OutlinedButton(
            onClick = onRfq,
            modifier = Modifier.weight(1f).height(46.dp),
            contentPadding = PaddingValues(horizontal = 5.dp)
        ) {
            Text("Cerere de ofertă", fontSize = 10.sp, maxLines = 1)
        }
    }
}

'''
s = s[:start] + loop_helpers + s[end:]

# Catalog card: fixed height and exact shared CTA block.
start = s.index('@Composable\nprivate fun CatalogCard')
end = s.index('@Composable fun ProductV100', start)
catalog = r'''@Composable
private fun CatalogCard(
    p: Product,
    favorite: Boolean,
    onProduct: () -> Unit,
    onFavorite: () -> Unit,
    onCart: () -> Unit,
    onRfq: () -> Unit
) {
    ElevatedCard(
        modifier = Modifier.fillMaxWidth().height(458.dp),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(Modifier.fillMaxSize().padding(10.dp)) {
            Box(Modifier.fillMaxWidth().height(132.dp).clickable(onClick = onProduct)) {
                AsyncImage(p.imageUrl, p.name, Modifier.fillMaxSize(), contentScale = ContentScale.Fit)
                DiscountChip(p, Modifier.align(Alignment.TopStart))
                IconButton(onClick = onFavorite, modifier = Modifier.align(Alignment.TopEnd)) {
                    Icon(
                        if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                        contentDescription = "Favorite",
                        tint = if (favorite) AutoIdOrange else Ink
                    )
                }
            }
            Text(p.brand.ifBlank { p.category }, fontSize = 10.sp, color = Muted, maxLines = 1)
            Text(
                p.name,
                modifier = Modifier.heightIn(min = 38.dp),
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
                fontWeight = FontWeight.Bold,
                fontSize = 13.sp
            )
            RatingLine(p, true)
            Text("SKU: ${p.sku.ifBlank { "—" }}", fontSize = 9.sp, color = Muted, maxLines = 1)
            Spacer(Modifier.height(6.dp))
            LoopPriceBlock(p)
            Spacer(Modifier.height(7.dp))
            StockLine(p, true)
            Spacer(Modifier.weight(1f))
            LoopProductActions(p, onProduct, onCart, onRfq)
        }
    }
}

'''
s = s[:start] + catalog + s[end:]

# Home card: same presentation and same CTA rules.
start = s.index('@Composable\nprivate fun HomeCard')
end = s.index('@Composable private fun DiscountChip', start)
home_card = r'''@Composable
private fun HomeCard(
    p: Product,
    favorite: Boolean,
    onClick: () -> Unit,
    onFavorite: () -> Unit,
    onCart: () -> Unit,
    onRfq: () -> Unit
) {
    ElevatedCard(
        modifier = Modifier.width(238.dp).height(458.dp),
        shape = RoundedCornerShape(18.dp)
    ) {
        Column(Modifier.fillMaxSize().padding(12.dp)) {
            Box(Modifier.fillMaxWidth().height(134.dp).clickable(onClick = onClick)) {
                AsyncImage(p.imageUrl, p.name, Modifier.fillMaxSize(), contentScale = ContentScale.Fit)
                IconButton(onClick = onFavorite, modifier = Modifier.align(Alignment.TopEnd)) {
                    Icon(
                        if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                        contentDescription = "Favorite",
                        tint = if (favorite) AutoIdOrange else Ink
                    )
                }
                DiscountChip(p, Modifier.align(Alignment.TopStart))
            }
            Text(p.brand.ifBlank { p.category }, fontSize = 10.sp, color = Muted, maxLines = 1)
            Text(
                p.name,
                modifier = Modifier.heightIn(min = 38.dp),
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
                fontWeight = FontWeight.Bold,
                fontSize = 13.sp
            )
            RatingLine(p, true)
            Text("SKU: ${p.sku.ifBlank { "—" }}", fontSize = 9.sp, color = Muted, maxLines = 1)
            Spacer(Modifier.height(6.dp))
            LoopPriceBlock(p)
            Spacer(Modifier.height(7.dp))
            StockLine(p, true)
            Spacer(Modifier.weight(1f))
            LoopProductActions(p, onClick, onCart, onRfq)
        }
    }
}

'''
s = s[:start] + home_card + s[end:]

# Favorites is also a product loop; its RFQ button must open the RFQ modal.
root_old = 'favorites->FavoritesV100(api,commerce,{favorites=false},::openProduct,{tab=V100Tab.Cart;favorites=false})'
root_new = 'favorites->FavoritesV100(api,commerce,{favorites=false},::openProduct,{p->addRfq(p)},{tab=V100Tab.Cart;favorites=false})'
if root_old in s:
    s = s.replace(root_old, root_new, 1)

fav_start = s.index('@Composable private fun FavoritesV100(')
fav_end = s.index('@Composable private fun NotificationsV100', fav_start)
fav = s[fav_start:fav_end]
fav = fav.replace(
    'onProduct:(Product)->Unit,onCart:()->Unit)',
    'onProduct:(Product)->Unit,onRfq:(Product)->Unit,onCart:()->Unit)'
)
fav = fav.replace(
    'CatalogCard(p,true,{onProduct(p)},{commerce.toggleFavorite(p.id)},{commerce.addToCart(p)},{})',
    'CatalogCard(p,true,{onProduct(p)},{commerce.toggleFavorite(p.id)},{commerce.addToCart(p)},{onRfq(p)})'
)
s = s[:fav_start] + fav + s[fav_end:]

p.write_text(s)

# 4) Semantic app version.
p = APP / 'build.gradle.kts'
s = p.read_text()
s = re.sub(r'versionCode\s*=\s*\d+', 'versionCode = 10300', s, count=1)
s = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "1.0.3"', s, count=1)
p.write_text(s)

print('Applied AutoID Android v1.0.3 exact loop UI and client guards')
