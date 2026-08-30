package ro.autoid.app

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import ro.autoid.app.data.AutoIdApi
import ro.autoid.app.data.CatalogFacets
import ro.autoid.app.data.FacetItem
import ro.autoid.app.data.ProductCategory

private val F113Ink = Color(0xFF101828)
private val F113Muted = Color(0xFF667085)
private val F113Orange = Color(0xFFF7630C)
private val F113Border = Color(0xFFEAECF0)
private val F113Soft = Color(0xFFF8F9FB)
private val F113Selected = Color(0xFFFFF1E8)

private fun leiV113(value: Float): String =
    java.text.NumberFormat.getNumberInstance(java.util.Locale("ro", "RO")).apply {
        minimumFractionDigits = 0
        maximumFractionDigits = 0
    }.format(value)

@Composable
private fun FilterSectionV113(
    icon: ImageVector,
    title: String,
    subtitle: String? = null,
    content: @Composable ColumnScope.() -> Unit
) {
    Surface(
        shape = RoundedCornerShape(22.dp),
        color = Color.White,
        border = BorderStroke(1.dp, F113Border)
    ) {
        Column(Modifier.fillMaxWidth().padding(15.dp), verticalArrangement = Arrangement.spacedBy(11.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(shape = RoundedCornerShape(11.dp), color = F113Selected) {
                    Icon(icon, null, tint = F113Orange, modifier = Modifier.padding(8.dp).size(18.dp))
                }
                Spacer(Modifier.width(10.dp))
                Column(Modifier.weight(1f)) {
                    Text(title, fontWeight = FontWeight.ExtraBold, fontSize = 15.sp, color = F113Ink)
                    if (!subtitle.isNullOrBlank()) Text(subtitle, fontSize = 10.sp, color = F113Muted)
                }
            }
            content()
        }
    }
}

@Composable
private fun FacetGridV113(
    options: List<FacetItem>,
    selected: Long?,
    onSelected: (FacetItem?) -> Unit,
    hierarchy: Boolean = false,
    searchable: Boolean = false,
    initiallyVisible: Int = 8
) {
    var expanded by remember(options) { mutableStateOf(false) }
    var query by remember(options) { mutableStateOf("") }
    val filtered = remember(options, query) {
        if (query.isBlank()) options else options.filter { it.name.contains(query, ignoreCase = true) }
    }
    val limit = if (expanded || query.isNotBlank()) 30 else initiallyVisible
    val shown = filtered.take(limit)

    Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
        if (searchable && options.size > 8) {
            OutlinedTextField(
                value = query,
                onValueChange = { query = it },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                shape = RoundedCornerShape(15.dp),
                leadingIcon = { Icon(Icons.Default.Search, null, Modifier.size(18.dp)) },
                trailingIcon = {
                    if (query.isNotBlank()) IconButton(onClick = { query = "" }) {
                        Icon(Icons.Default.Close, "Șterge căutarea", Modifier.size(18.dp))
                    }
                },
                placeholder = { Text("Caută în ${options.size} opțiuni", fontSize = 12.sp) },
                textStyle = LocalTextStyle.current.copy(fontSize = 13.sp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = F113Orange,
                    unfocusedBorderColor = Color(0xFFE4E7EC)
                )
            )
        }

        val rows = (listOf<FacetItem?>(null) + shown).chunked(2)
        rows.forEach { row ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                row.forEach { item ->
                    val active = if (item == null) selected == null else selected == item.id
                    val prefix = if (hierarchy && item != null && item.depth > 1) "› ".repeat((item.depth - 1).coerceAtMost(2)) else ""
                    Surface(
                        onClick = { onSelected(item) },
                        modifier = Modifier.weight(1f).heightIn(min = 58.dp),
                        shape = RoundedCornerShape(16.dp),
                        color = if (active) F113Selected else Color(0xFFFAFAFB),
                        border = BorderStroke(if (active) 1.5.dp else 1.dp, if (active) F113Orange else Color(0xFFE4E7EC))
                    ) {
                        Row(Modifier.fillMaxWidth().padding(horizontal = 11.dp, vertical = 9.dp), verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text(
                                    if (item == null) "Toate" else prefix + item.name,
                                    maxLines = 2,
                                    overflow = TextOverflow.Ellipsis,
                                    fontSize = 11.sp,
                                    lineHeight = 14.sp,
                                    fontWeight = if (active) FontWeight.ExtraBold else FontWeight.SemiBold,
                                    color = F113Ink
                                )
                                if (item != null && item.count > 0) Text("${item.count} produse", fontSize = 9.sp, color = if (active) F113Orange else F113Muted)
                            }
                            if (active) Box(Modifier.size(20.dp).background(F113Orange, CircleShape), contentAlignment = Alignment.Center) {
                                Icon(Icons.Default.Check, null, tint = Color.White, modifier = Modifier.size(13.dp))
                            }
                        }
                    }
                }
                repeat(2 - row.size) { Spacer(Modifier.weight(1f)) }
            }
        }

        if (filtered.size > limit && query.isBlank()) {
            TextButton(onClick = { expanded = true }, contentPadding = PaddingValues(2.dp)) {
                Text("Vezi mai multe (${filtered.size - limit})", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = F113Orange)
                Icon(Icons.Default.ExpandMore, null, tint = F113Orange, modifier = Modifier.size(16.dp))
            }
        } else if (expanded && filtered.size > initiallyVisible && query.isBlank()) {
            TextButton(onClick = { expanded = false }, contentPadding = PaddingValues(2.dp)) {
                Text("Restrânge", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = F113Muted)
                Icon(Icons.Default.ExpandLess, null, tint = F113Muted, modifier = Modifier.size(16.dp))
            }
        }
        if ((expanded || query.isNotBlank()) && filtered.size > 30) {
            Text("Afișăm primele 30. Folosește căutarea pentru selecția exactă.", fontSize = 10.sp, color = F113Muted)
        }
    }
}

@Composable
private fun PriceBoxV113(label: String, value: String, modifier: Modifier = Modifier) {
    Surface(modifier, RoundedCornerShape(14.dp), Color(0xFFFAFAFB), border = BorderStroke(1.dp, Color(0xFFE4E7EC))) {
        Column(Modifier.padding(11.dp)) {
            Text(label, fontSize = 9.sp, fontWeight = FontWeight.Bold, color = F113Muted)
            Text(value, fontSize = 14.sp, fontWeight = FontWeight.ExtraBold, color = F113Ink)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FilterSheetV113(
    api: AutoIdApi,
    f: CatalogFacets?,
    category: ProductCategory,
    selectedCategory: Long?,
    brand: Long?,
    model: Long?,
    min: Double?,
    max: Double?,
    onApply: (Long?, Long?, Long?, Double?, Double?) -> Unit,
    onClear: () -> Unit,
    onAi: () -> Unit,
    onDismiss: () -> Unit
) {
    var c by remember(category.id, selectedCategory) { mutableStateOf(selectedCategory) }
    var b by remember(category.id, brand) { mutableStateOf(brand) }
    var m by remember(category.id, model) { mutableStateOf(model) }
    var live by remember(category.id) { mutableStateOf(f) }
    var facetLoading by remember { mutableStateOf(false) }

    LaunchedEffect(category.id, c, b, m) {
        delay(90)
        facetLoading = true
        runCatching { withContext(Dispatchers.IO) { api.catalogFacets(category.id, c, b, m) } }
            .onSuccess { fresh ->
                live = fresh
                val cats = if (fresh.specialCategory == "liquidation") fresh.liquidationCategories else fresh.categoryHierarchy
                if (c != null && cats.none { it.id == c }) c = null
                if (b != null && fresh.brands.none { it.id == b }) b = null
                if (m != null && fresh.models.none { it.id == m }) m = null
            }
        facetLoading = false
    }

    val source = live ?: f
    val categories = if (source?.specialCategory == "liquidation") source.liquidationCategories else source?.categoryHierarchy.orEmpty()
    val facetMin = (source?.minPrice ?: 0.0).coerceAtLeast(0.0).toFloat()
    val facetMax = (source?.maxPrice ?: 0.0).coerceAtLeast(0.0).toFloat()
    val sliderMax = if (facetMax > facetMin) facetMax else facetMin + 1f
    val initialStart = (min?.toFloat() ?: facetMin).coerceIn(facetMin, sliderMax)
    val initialEnd = (max?.toFloat() ?: facetMax.takeIf { it > facetMin } ?: sliderMax).coerceIn(initialStart, sliderMax)
    var range by remember(category.id, min, max) { mutableStateOf(initialStart..initialEnd) }
    var priceTouched by remember(category.id) { mutableStateOf(min != null || max != null) }

    LaunchedEffect(facetMin, facetMax) {
        if (facetMax > facetMin) {
            range = if (!priceTouched) facetMin..facetMax else {
                val rs = range.start.coerceIn(facetMin, facetMax)
                val re = range.endInclusive.coerceIn(rs, facetMax)
                rs..re
            }
        }
    }

    val priceAvailable = source != null && facetMax > facetMin
    val priceActive = priceAvailable && (range.start > facetMin + .5f || range.endInclusive < facetMax - .5f)
    val activeCount = listOf(c, b, m).count { it != null } + if (priceActive) 1 else 0
    val cName = categories.firstOrNull { it.id == c }?.name
    val bName = source?.brands.orEmpty().firstOrNull { it.id == b }?.name
    val mName = source?.models.orEmpty().firstOrNull { it.id == m }?.name

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = F113Soft,
        shape = RoundedCornerShape(topStart = 30.dp, topEnd = 30.dp),
        dragHandle = { Box(Modifier.padding(top = 10.dp, bottom = 6.dp).width(42.dp).height(4.dp).background(Color(0xFFD0D5DD), CircleShape)) }
    ) {
        Column(Modifier.fillMaxWidth().fillMaxHeight(.94f)) {
            Row(Modifier.fillMaxWidth().padding(start = 18.dp, end = 8.dp, bottom = 10.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Filtre produse", fontSize = 24.sp, fontWeight = FontWeight.ExtraBold, color = F113Ink)
                        if (activeCount > 0) {
                            Spacer(Modifier.width(8.dp))
                            Surface(shape = CircleShape, color = F113Orange) {
                                Text(activeCount.toString(), Modifier.padding(horizontal = 8.dp, vertical = 3.dp), color = Color.White, fontSize = 10.sp, fontWeight = FontWeight.ExtraBold)
                            }
                        }
                    }
                    Text(category.name, fontSize = 11.sp, color = F113Muted, maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
                Surface(onClick = onAi, shape = RoundedCornerShape(50), color = F113Selected) {
                    Row(Modifier.padding(horizontal = 10.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.SmartToy, null, tint = F113Orange, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(5.dp))
                        Text("AutoID AI", fontSize = 10.sp, fontWeight = FontWeight.ExtraBold, color = F113Orange)
                    }
                }
                IconButton(onClick = onDismiss) { Icon(Icons.Default.Close, "Închide filtrele") }
            }
            if (facetLoading) LinearProgressIndicator(Modifier.fillMaxWidth().height(2.dp), color = F113Orange, trackColor = Color.Transparent)

            if (activeCount > 0) {
                LazyRow(contentPadding = PaddingValues(horizontal = 18.dp), horizontalArrangement = Arrangement.spacedBy(7.dp), modifier = Modifier.padding(vertical = 8.dp)) {
                    cName?.let { value -> item { InputChip(true, { c = null }, { Text(value, fontSize = 10.sp) }, trailingIcon = { Icon(Icons.Default.Close, null, Modifier.size(14.dp)) }) } }
                    bName?.let { value -> item { InputChip(true, { b = null }, { Text(value, fontSize = 10.sp) }, trailingIcon = { Icon(Icons.Default.Close, null, Modifier.size(14.dp)) }) } }
                    mName?.let { value -> item { InputChip(true, { m = null }, { Text(value, fontSize = 10.sp) }, trailingIcon = { Icon(Icons.Default.Close, null, Modifier.size(14.dp)) }) } }
                    if (priceActive) item { InputChip(true, { priceTouched = false; range = facetMin..facetMax }, { Text("${leiV113(range.start)}–${leiV113(range.endInclusive)} lei", fontSize = 10.sp) }, trailingIcon = { Icon(Icons.Default.Close, null, Modifier.size(14.dp)) }) }
                }
            }

            HorizontalDivider(color = F113Border)
            LazyColumn(
                Modifier.weight(1f).fillMaxWidth().padding(horizontal = 14.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(top = 14.dp, bottom = 20.dp)
            ) {
                item {
                    FilterSectionV113(Icons.Default.Payments, "Preț", if (priceAvailable) "Interval pentru selecția curentă" else "Interval indisponibil") {
                        if (priceAvailable) {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                                PriceBoxV113("MINIM", "${leiV113(range.start)} lei", Modifier.weight(1f))
                                PriceBoxV113("MAXIM", "${leiV113(range.endInclusive)} lei", Modifier.weight(1f))
                            }
                            RangeSlider(
                                value = range,
                                onValueChange = { priceTouched = true; range = it },
                                valueRange = facetMin..sliderMax,
                                modifier = Modifier.fillMaxWidth(),
                                colors = SliderDefaults.colors(activeTrackColor = F113Orange, thumbColor = F113Orange)
                            )
                        } else Text("Nu există suficiente date de preț pentru selecția curentă.", fontSize = 11.sp, color = F113Muted)
                    }
                }

                if (categories.isNotEmpty()) item {
                    FilterSectionV113(Icons.Default.AccountTree, "Categorie", "Se actualizează după Brand și Model") {
                        FacetGridV113(categories, c, { item -> c = item?.id }, hierarchy = source?.specialCategory != "liquidation", searchable = categories.size > 10)
                    }
                }

                if (source?.brands.orEmpty().isNotEmpty()) item {
                    FilterSectionV113(Icons.Default.Storefront, "Brand", "Doar branduri cu produse în categoria selectată") {
                        FacetGridV113(source?.brands.orEmpty(), b, { item -> b = item?.id }, searchable = true)
                    }
                }

                if (source?.models.orEmpty().isNotEmpty()) item {
                    FilterSectionV113(Icons.Default.ViewInAr, "Model", "Doar modele compatibile cu selecția curentă") {
                        FacetGridV113(source?.models.orEmpty(), m, { item ->
                            m = item?.id
                            if (item != null) {
                                if (item.brandId > 0) b = item.brandId
                                if (item.categoryId > 0) c = item.categoryId
                            }
                        }, searchable = true, initiallyVisible = 6)
                    }
                }
            }

            Surface(shadowElevation = 12.dp, color = Color.White) {
                Row(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 11.dp).navigationBarsPadding(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    OutlinedButton(onClick = onClear, enabled = activeCount > 0, modifier = Modifier.weight(.82f).height(54.dp), shape = RoundedCornerShape(17.dp)) {
                        Icon(Icons.Default.RestartAlt, null, Modifier.size(17.dp)); Spacer(Modifier.width(5.dp)); Text("Resetează", fontWeight = FontWeight.Bold)
                    }
                    Button(
                        onClick = {
                            val appliedMin = if (priceAvailable && priceTouched && range.start > facetMin + .5f) range.start.toDouble() else null
                            val appliedMax = if (priceAvailable && priceTouched && range.endInclusive < facetMax - .5f) range.endInclusive.toDouble() else null
                            onApply(c, b, m, appliedMin, appliedMax)
                        },
                        modifier = Modifier.weight(1.18f).height(54.dp),
                        shape = RoundedCornerShape(17.dp)
                    ) {
                        Text(if (activeCount > 0) "Aplică $activeCount filtre" else "Vezi produsele", fontWeight = FontWeight.ExtraBold)
                        Spacer(Modifier.width(6.dp)); Icon(Icons.Default.ArrowForward, null, Modifier.size(17.dp))
                    }
                }
            }
        }
    }
}
