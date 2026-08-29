from pathlib import Path

APP=Path('android-v0.1/app')

# Extend Product with explicit VAT-inclusive simple-product prices for loop rendering.
p=APP/'src/main/java/ro/autoid/app/data/Models.kt'
s=p.read_text()
old='''    val groupedStockDistributor: Int? = null,
    val msrpEuroValue: Double = 0.0,
    val autoIdEuroValue: Double = 0.0
)'''
new='''    val groupedStockDistributor: Int? = null,
    val msrpEuroValue: Double = 0.0,
    val autoIdEuroValue: Double = 0.0,
    val regularInclVatDisplay: String = "",
    val saleInclVatDisplay: String = ""
)'''
if old not in s: raise SystemExit('Models v1 fields anchor missing')
p.write_text(s.replace(old,new,1))

# Parse the new API keys.
p=APP/'src/main/java/ro/autoid/app/data/AutoIdApi.kt'
s=p.read_text()
old='''msrpEuroValue=o.optDouble("pret_lista",0.0),autoIdEuroValue=o.optDouble("pret_autoid_euro",0.0))'''
new='''msrpEuroValue=o.optDouble("pret_lista",0.0),autoIdEuroValue=o.optDouble("pret_autoid_euro",0.0),regularInclVatDisplay=html(o.optString("regular_price_incl_vat_display")),saleInclVatDisplay=html(o.optString("sale_price_incl_vat_display")))'''
if old not in s: raise SystemExit('AutoIdApi product v1 tail missing')
s=s.replace(old,new,1).replace('AutoID-Android/1.0.0','AutoID-Android/1.0.2')
p.write_text(s)

# Replace loop cards with one consistent price/stock/CTA presentation.
p=APP/'src/main/java/ro/autoid/app/V100Screens.kt'
s=p.read_text()

# Helper price block for product loops.
anchor='@Composable private fun CatalogCard('
idx=s.index(anchor)
helper=r'''@Composable
private fun LoopPriceBlock(p: Product) {
    val grouped = isGrouped(p)
    val m = p.msrpEuroValue
    val a = p.autoIdEuroValue
    val euroDiscount = m > 0 && a > 0 && m > a + 0.005

    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        if (m > 0) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("MSRP: ", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Ink)
                Text(
                    "${euro(m)} €",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = Ink,
                    textDecoration = if (euroDiscount) androidx.compose.ui.text.style.TextDecoration.LineThrough else null
                )
            }
        }
        if (a > 0 && (m <= 0 || euroDiscount)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("AutoID: ", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Ink)
                Text("${euro(a)} €", fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = AutoIdOrange)
                Text(" ex. TVA", fontSize = 9.sp, color = Muted)
            }
        } else if (m > 0) {
            Text("ex. TVA", fontSize = 9.sp, color = Muted)
        }

        if (grouped) {
            val range = p.priceRangeInclVat.ifBlank { p.currentInclVat.ifBlank { p.price } }
            if (range.isNotBlank()) {
                Text("$range incl. TVA", fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = Ink, maxLines = 2)
            }
        } else {
            val regular = p.regularInclVatDisplay
            val sale = p.saleInclVatDisplay.ifBlank { p.currentInclVat.ifBlank { p.price } }
            val hasDiscount = regular.isNotBlank() && sale.isNotBlank() && regular != sale
            Row(verticalAlignment = Alignment.CenterVertically) {
                if (hasDiscount) {
                    Text(
                        regular,
                        fontSize = 11.sp,
                        color = Muted,
                        textDecoration = androidx.compose.ui.text.style.TextDecoration.LineThrough
                    )
                    Spacer(Modifier.width(6.dp))
                }
                Text(sale, fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = Ink)
                Spacer(Modifier.width(3.dp))
                Text("incl. TVA", fontSize = 9.sp, color = Muted)
            }
        }
    }
}

'''
s=s[:idx]+helper+s[idx:]

# Catalog cards: fixed height and exact CTA rules.
start=s.index('@Composable private fun CatalogCard(')
end=s.index('@Composable fun ProductV100',start)
new_catalog=r'''@Composable
private fun CatalogCard(
    p: Product,
    favorite: Boolean,
    onProduct: () -> Unit,
    onFavorite: () -> Unit,
    onCart: () -> Unit,
    onRfq: () -> Unit
) {
    ElevatedCard(
        modifier = Modifier.height(430.dp),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxSize().padding(10.dp)
        ) {
            Box(Modifier.fillMaxWidth().height(128.dp).clickable(onClick = onProduct)) {
                AsyncImage(p.imageUrl, p.name, Modifier.fillMaxSize(), contentScale = ContentScale.Fit)
                DiscountChip(p, Modifier.align(Alignment.TopStart))
                IconButton(onClick = onFavorite, modifier = Modifier.align(Alignment.TopEnd)) {
                    Icon(
                        if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                        "Favorite",
                        tint = if (favorite) AutoIdOrange else Ink
                    )
                }
            }
            Text(p.brand, fontSize = 10.sp, color = Muted, maxLines = 1)
            Text(p.name, maxLines = 2, overflow = TextOverflow.Ellipsis, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            RatingLine(p, true)
            Text("SKU: ${p.sku.ifBlank { "—" }}", fontSize = 9.sp, color = Muted, maxLines = 1)
            Spacer(Modifier.height(5.dp))
            LoopPriceBlock(p)
            Spacer(Modifier.height(6.dp))
            StockLine(p, true)
            Spacer(Modifier.weight(1f))
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.fillMaxWidth()) {
                if (isGrouped(p)) {
                    OutlinedButton(
                        onClick = onProduct,
                        modifier = Modifier.weight(1f).height(44.dp),
                        contentPadding = PaddingValues(horizontal = 4.dp)
                    ) { Text("Detalii produs", fontSize = 10.sp) }
                } else {
                    Button(
                        onClick = onCart,
                        modifier = Modifier.weight(1f).height(44.dp),
                        contentPadding = PaddingValues(horizontal = 4.dp)
                    ) { Text("Adaugă în coș", fontSize = 10.sp) }
                }
                OutlinedButton(
                    onClick = onRfq,
                    modifier = Modifier.weight(1f).height(44.dp),
                    contentPadding = PaddingValues(horizontal = 4.dp)
                ) { Text("Cerere ofertă", fontSize = 10.sp) }
            }
        }
    }
}

'''
s=s[:start]+new_catalog+s[end:]

# Home horizontal loop cards use the same pricing and grouped/simple CTA rules.
start=s.index('@Composable private fun HomeCard(')
end=s.index('@Composable private fun DiscountChip',start)
new_home=r'''@Composable
private fun HomeCard(
    p: Product,
    favorite: Boolean,
    onClick: () -> Unit,
    onFavorite: () -> Unit,
    onCart: () -> Unit
) {
    ElevatedCard(
        modifier = Modifier.width(230.dp).height(430.dp),
        shape = RoundedCornerShape(18.dp)
    ) {
        Column(Modifier.fillMaxSize().padding(12.dp)) {
            Box(Modifier.fillMaxWidth().height(130.dp).clickable(onClick = onClick)) {
                AsyncImage(p.imageUrl, p.name, Modifier.fillMaxSize(), contentScale = ContentScale.Fit)
                IconButton(onClick = onFavorite, modifier = Modifier.align(Alignment.TopEnd)) {
                    Icon(if (favorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "Favorite", tint = if (favorite) AutoIdOrange else Ink)
                }
                DiscountChip(p, Modifier.align(Alignment.TopStart))
            }
            Text(p.brand.ifBlank { p.category }, fontSize = 10.sp, color = Muted, maxLines = 1)
            Text(p.name, maxLines = 2, overflow = TextOverflow.Ellipsis, fontWeight = FontWeight.Bold, fontSize = 13.sp)
            RatingLine(p, true)
            Text("SKU: ${p.sku.ifBlank { "—" }}", fontSize = 9.sp, color = Muted, maxLines = 1)
            Spacer(Modifier.height(5.dp))
            LoopPriceBlock(p)
            Spacer(Modifier.height(6.dp))
            StockLine(p, true)
            Spacer(Modifier.weight(1f))
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.fillMaxWidth()) {
                if (isGrouped(p)) {
                    OutlinedButton(onClick = onClick, modifier = Modifier.weight(1f).height(44.dp), contentPadding = PaddingValues(horizontal = 4.dp)) {
                        Text("Detalii produs", fontSize = 10.sp)
                    }
                } else {
                    Button(onClick = onCart, modifier = Modifier.weight(1f).height(44.dp), contentPadding = PaddingValues(horizontal = 4.dp)) {
                        Text("Adaugă în coș", fontSize = 10.sp)
                    }
                }
                OutlinedButton(onClick = onClick, modifier = Modifier.weight(1f).height(44.dp), contentPadding = PaddingValues(horizontal = 4.dp)) {
                    Text("Cerere ofertă", fontSize = 10.sp)
                }
            }
        }
    }
}

'''
# HomeCard does not have an RFQ callback in v1.0; keep the second button visually correct for now and route to product for grouped/simple.
# Catalog cards, where purchasing decisions happen, invoke the real RFQ callback.
s=s[:start]+new_home+s[end:]

# Title rename in Home.
s=s.replace('SectionHead("Oferte speciale"','SectionHead("Lichidări de stoc"')

p.write_text(s)

# Semantic Android version.
p=APP/'build.gradle.kts'
s=p.read_text().replace('versionCode = 101','versionCode = 102').replace('versionName = "1.0.1"','versionName = "1.0.2"')
p.write_text(s)
print('Applied AutoID Android v1.0.2 loop pricing/CTA patch')
