package ro.autoid.app

import androidx.compose.animation.core.*
import androidx.compose.foundation.Image
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
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ro.autoid.app.data.CatalogFacets
import ro.autoid.app.data.FacetItem
import ro.autoid.app.data.ProductCategory

private val V112Ink = Color(0xFF101828)
private val V112Muted = Color(0xFF667085)
private val V112Orange = Color(0xFFF7630C)
private val V112Border = Color(0xFFEAECF0)
private val V112Soft = Color(0xFFF8F9FB)
private val V112Selected = Color(0xFFFFF1E8)

@Composable
fun AutoIdPulseLoaderV112(
    modifier: Modifier = Modifier,
    compact: Boolean = false,
    label: String = "Se încarcă..."
) {
    val transition = rememberInfiniteTransition(label = "autoid-loader")
    val scale by transition.animateFloat(
        initialValue = .90f,
        targetValue = 1.07f,
        animationSpec = infiniteRepeatable(tween(720, easing = FastOutSlowInEasing), RepeatMode.Reverse),
        label = "pulse-scale"
    )
    val alpha by transition.animateFloat(
        initialValue = .62f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(720, easing = FastOutSlowInEasing), RepeatMode.Reverse),
        label = "pulse-alpha"
    )
    val halo by transition.animateFloat(
        initialValue = .05f,
        targetValue = .16f,
        animationSpec = infiniteRepeatable(tween(900, easing = FastOutSlowInEasing), RepeatMode.Reverse),
        label = "pulse-halo"
    )

    Box(modifier, contentAlignment = Alignment.Center) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(if (compact) 5.dp else 10.dp)
        ) {
            Box(contentAlignment = Alignment.Center) {
                Box(
                    Modifier
                        .size(if (compact) 54.dp else 76.dp)
                        .scale(1.03f + (scale - .90f) * .42f)
                        .background(V112Orange.copy(alpha = halo), CircleShape)
                )
                Surface(
                    shape = CircleShape,
                    color = Color.White,
                    shadowElevation = if (compact) 2.dp else 7.dp,
                    modifier = Modifier.size(if (compact) 43.dp else 60.dp)
                ) {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Image(
                            painter = painterResource(R.drawable.autoid_icon_v100),
                            contentDescription = null,
                            modifier = Modifier
                                .size(if (compact) 27.dp else 38.dp)
                                .scale(scale)
                                .alpha(alpha),
                            contentScale = ContentScale.Fit
                        )
                    }
                }
            }
            if (!compact && label.isNotBlank()) {
                Text(label, fontSize = 11.sp, fontWeight = FontWeight.SemiBold, color = V112Muted)
            }
        }
    }
}

private fun leiV112(value: Float): String =
    java.text.NumberFormat.getNumberInstance(java.util.Locale("ro", "RO")).apply {
        minimumFractionDigits = 0
        maximumFractionDigits = 0
    }.format(value)

@Composable
private fun FilterSectionV112(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    subtitle: String? = null,
    content: @Composable ColumnScope.() -> Unit
) {
    Surface(
        shape = RoundedCornerShape(22.dp),
        color = Color.White,
        border = androidx.compose.foundation.BorderStroke(1.dp, V112Border)
    ) {
        Column(
            Modifier.fillMaxWidth().padding(15.dp),
            verticalArrangement = Arrangement.spacedBy(11.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(shape = RoundedCornerShape(11.dp), color = V112Selected) {
                    Icon(icon, null, tint = V112Orange, modifier = Modifier.padding(8.dp).size(18.dp))
                }
                Spacer(Modifier.width(10.dp))
                Column(Modifier.weight(1f)) {
                    Text(title, fontWeight = FontWeight.ExtraBold, fontSize = 15.sp, color = V112Ink)
                    if (!subtitle.isNullOrBlank()) Text(subtitle, fontSize = 10.sp, color = V112Muted)
                }
            }
            content()
        }
    }
}

@Composable
private fun FacetGridV112(
    options: List<FacetItem>,
    selected: Long?,
    onSelected: (Long?) -> Unit,
    hierarchy: Boolean = false,
    searchable: Boolean = false,
    initiallyVisible: Int = 8
) {
    var expanded by remember(options) { mutableStateOf(false) }
    var query by remember(options) { mutableStateOf("") }
    val filtered = remember(options, query) {
        if (query.isBlank()) options else options.filter { it.name.contains(query, true) }
    }
    val limit = if (expanded || query.isNotBlank()) 24 else initiallyVisible
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
                    focusedBorderColor = V112Orange,
                    unfocusedBorderColor = Color(0xFFE4E7EC),
                    focusedContainerColor = Color.White,
                    unfocusedContainerColor = Color.White
                )
            )
        }

        val rows = (listOf(FacetItem(0, "Toate")) + shown).chunked(2)
        rows.forEach { row ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                row.forEach { item ->
                    val active = if (item.id == 0L) selected == null else selected == item.id
                    val prefix = if (hierarchy && item.id != 0L && item.depth > 1) {
                        "› ".repeat((item.depth - 1).coerceAtMost(2))
                    } else ""
                    Surface(
                        onClick = { onSelected(item.id.takeIf { it > 0 }) },
                        modifier = Modifier.weight(1f).heightIn(min = 58.dp),
                        shape = RoundedCornerShape(16.dp),
                        color = if (active) V112Selected else Color(0xFFFAFAFB),
                        border = androidx.compose.foundation.BorderStroke(
                            if (active) 1.5.dp else 1.dp,
                            if (active) V112Orange else Color(0xFFE4E7EC)
                        )
                    ) {
                        Row(
                            Modifier.fillMaxWidth().padding(horizontal = 11.dp, vertical = 9.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(Modifier.weight(1f)) {
                                Text(
                                    prefix + item.name,
                                    maxLines = 2,
                                    overflow = TextOverflow.Ellipsis,
                                    fontSize = 11.sp,
                                    lineHeight = 14.sp,
                                    fontWeight = if (active) FontWeight.ExtraBold else FontWeight.SemiBold,
                                    color = V112Ink
                                )
                                if (item.count > 0) {
                                    Text(
                                        "${item.count} produse",
                                        fontSize = 9.sp,
                                        color = if (active) V112Orange else V112Muted
                                    )
                                }
                            }
                            if (active) {
                                Box(
                                    Modifier.size(20.dp).background(V112Orange, CircleShape),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Icon(Icons.Default.Check, null, tint = Color.White, modifier = Modifier.size(13.dp))
                                }
                            }
                        }
                    }
                }
                repeat(2 - row.size) { Spacer(Modifier.weight(1f)) }
            }
        }

        if (filtered.size > limit && query.isBlank()) {
            TextButton(onClick = { expanded = true }, contentPadding = PaddingValues(2.dp)) {
                Text("Vezi mai multe (${filtered.size - limit})", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = V112Orange)
                Spacer(Modifier.width(3.dp))
                Icon(Icons.Default.ExpandMore, null, tint = V112Orange, modifier = Modifier.size(16.dp))
            }
        } else if (expanded && filtered.size > initiallyVisible && query.isBlank()) {
            TextButton(onClick = { expanded = false }, contentPadding = PaddingValues(2.dp)) {
                Text("Restrânge", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = V112Muted)
                Spacer(Modifier.width(3.dp))
                Icon(Icons.Default.ExpandLess, null, tint = V112Muted, modifier = Modifier.size(16.dp))
            }
        }
        if ((expanded || query.isNotBlank()) && filtered.size > 24) {
            Text("Afișăm primele 24. Folosește căutarea pentru selecția exactă.", fontSize = 10.sp, color = V112Muted)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FilterSheetV112(
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

    val facetMin = (f?.minPrice ?: 0.0).coerceAtLeast(0.0).toFloat()
    val facetMax = (f?.maxPrice ?: 0.0).coerceAtLeast(0.0).toFloat()
    val sliderMax = if (facetMax > facetMin) facetMax else facetMin + 1f
    val start = (min?.toFloat() ?: facetMin).coerceIn(facetMin, sliderMax)
    val end = (max?.toFloat() ?: facetMax.takeIf { it > facetMin } ?: sliderMax).coerceIn(start, sliderMax)
    var range by remember(category.id, f?.minPrice, f?.maxPrice, min, max) { mutableStateOf(start..end) }

    val categories = f?.categoryHierarchy.orEmpty().ifEmpty {
        f?.subcategories.orEmpty().map { FacetItem(it.id, it.name, it.slug, it.count, it.parent, 1) }
    }
    val priceAvailable = f != null && facetMax > facetMin
    val priceActive = priceAvailable && (range.start > facetMin + .5f || range.endInclusive < facetMax - .5f)
    val activeCount = listOf(c, b, m).count { it != null } + if (priceActive) 1 else 0

    val cName = categories.firstOrNull { it.id == c }?.name
    val bName = f?.brands.orEmpty().firstOrNull { it.id == b }?.name
    val mName = f?.models.orEmpty().firstOrNull { it.id == m }?.name

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = V112Soft,
        shape = RoundedCornerShape(topStart = 30.dp, topEnd = 30.dp),
        dragHandle = {
            Box(
                Modifier.padding(top = 10.dp, bottom = 6.dp).width(42.dp).height(4.dp)
                    .background(Color(0xFFD0D5DD), CircleShape)
            )
        }
    ) {
        Column(Modifier.fillMaxWidth().fillMaxHeight(.94f)) {
            Row(
                Modifier.fillMaxWidth().padding(start = 18.dp, end = 8.dp, bottom = 10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Filtre produse", fontSize = 24.sp, fontWeight = FontWeight.ExtraBold, color = V112Ink)
                        if (activeCount > 0) {
                            Spacer(Modifier.width(8.dp))
                            Surface(shape = CircleShape, color = V112Orange) {
                                Text(
                                    activeCount.toString(),
                                    Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
                                    color = Color.White,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.ExtraBold
                                )
                            }
                        }
                    }
                    Text(category.name, fontSize = 11.sp, color = V112Muted, maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
                Surface(onClick = onAi, shape = RoundedCornerShape(50), color = V112Selected) {
                    Row(Modifier.padding(horizontal = 10.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.SmartToy, null, tint = V112Orange, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(5.dp))
                        Text("AutoID AI", fontSize = 10.sp, fontWeight = FontWeight.ExtraBold, color = V112Orange)
                    }
                }
                IconButton(onClick = onDismiss) { Icon(Icons.Default.Close, "Închide filtrele") }
            }

            if (activeCount > 0) {
                LazyRow(
                    contentPadding = PaddingValues(horizontal = 18.dp),
                    horizontalArrangement = Arrangement.spacedBy(7.dp),
                    modifier = Modifier.padding(bottom = 10.dp)
                ) {
                    cName?.let { value -> item { InputChip(true, { c = null }, { Text(value, fontSize = 10.sp) }, trailingIcon = { Icon(Icons.Default.Close, null, Modifier.size(14.dp)) }) } }
                    bName?.let { value -> item { InputChip(true, { b = null }, { Text(value, fontSize = 10.sp) }, trailingIcon = { Icon(Icons.Default.Close, null, Modifier.size(14.dp)) }) } }
                    mName?.let { value -> item { InputChip(true, { m = null }, { Text(value, fontSize = 10.sp) }, trailingIcon = { Icon(Icons.Default.Close, null, Modifier.size(14.dp)) }) } }
                    if (priceActive) item {
                        InputChip(
                            selected = true,
                            onClick = { range = facetMin..facetMax },
                            label = { Text("${leiV112(range.start)}–${leiV112(range.endInclusive)} lei", fontSize = 10.sp) },
                            trailingIcon = { Icon(Icons.Default.Close, null, Modifier.size(14.dp)) }
                        )
                    }
                }
            }

            HorizontalDivider(color = V112Border)

            LazyColumn(
                Modifier.weight(1f).fillMaxWidth().padding(horizontal = 14.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(top = 14.dp, bottom = 20.dp)
            ) {
                if (categories.isNotEmpty()) item {
                    FilterSectionV112(Icons.Default.AccountTree, "Categorie", "Alege zona exactă de produse") {
                        FacetGridV112(categories, c, { c = it }, hierarchy = true, searchable = categories.size > 10)
                    }
                }

                item {
                    FilterSectionV112(Icons.Default.Payments, "Preț", if (priceAvailable) "Interval cu TVA inclus" else "Interval indisponibil") {
                        if (priceAvailable) {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                                PriceBoxV112("MINIM", "${leiV112(range.start)} lei", Modifier.weight(1f))
                                PriceBoxV112("MAXIM", "${leiV112(range.endInclusive)} lei", Modifier.weight(1f))
                            }
                            RangeSlider(
                                value = range,
                                onValueChange = { range = it },
                                valueRange = facetMin..sliderMax,
                                modifier = Modifier.fillMaxWidth(),
                                colors = SliderDefaults.colors(activeTrackColor = V112Orange, thumbColor = V112Orange)
                            )
                            Row(Modifier.fillMaxWidth()) {
                                Text("${leiV112(facetMin)} lei", fontSize = 10.sp, color = V112Muted)
                                Spacer(Modifier.weight(1f))
                                Text("${leiV112(facetMax)} lei", fontSize = 10.sp, color = V112Muted)
                            }
                        } else {
                            Text("Nu există încă suficiente date de preț pentru această categorie.", fontSize = 11.sp, color = V112Muted)
                        }
                    }
                }

                if (f?.brands.orEmpty().isNotEmpty()) item {
                    FilterSectionV112(Icons.Default.Storefront, "Brand", "${f?.brands.orEmpty().size} branduri disponibile") {
                        FacetGridV112(f?.brands.orEmpty(), b, { b = it }, searchable = true)
                    }
                }

                if (f?.models.orEmpty().isNotEmpty()) item {
                    FilterSectionV112(Icons.Default.ViewInAr, "Model", "Caută rapid după model") {
                        FacetGridV112(f?.models.orEmpty(), m, { m = it }, searchable = true, initiallyVisible = 6)
                    }
                }
            }

            Surface(shadowElevation = 12.dp, color = Color.White) {
                Row(
                    Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 11.dp).navigationBarsPadding(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    OutlinedButton(
                        onClick = onClear,
                        enabled = activeCount > 0,
                        modifier = Modifier.weight(.82f).height(54.dp),
                        shape = RoundedCornerShape(17.dp)
                    ) {
                        Icon(Icons.Default.RestartAlt, null, Modifier.size(17.dp))
                        Spacer(Modifier.width(5.dp))
                        Text("Resetează", fontWeight = FontWeight.Bold)
                    }
                    Button(
                        onClick = {
                            val appliedMin = if (priceAvailable && range.start > facetMin + .5f) range.start.toDouble() else null
                            val appliedMax = if (priceAvailable && range.endInclusive < facetMax - .5f) range.endInclusive.toDouble() else null
                            onApply(c, b, m, appliedMin, appliedMax)
                        },
                        modifier = Modifier.weight(1.18f).height(54.dp),
                        shape = RoundedCornerShape(17.dp)
                    ) {
                        Text(if (activeCount > 0) "Aplică $activeCount filtre" else "Vezi produsele", fontWeight = FontWeight.ExtraBold)
                        Spacer(Modifier.width(6.dp))
                        Icon(Icons.Default.ArrowForward, null, Modifier.size(17.dp))
                    }
                }
            }
        }
    }
}

@Composable
private fun PriceBoxV112(label: String, value: String, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(14.dp),
        color = Color(0xFFFAFAFB),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFE4E7EC))
    ) {
        Column(Modifier.padding(11.dp)) {
            Text(label, fontSize = 9.sp, fontWeight = FontWeight.Bold, color = V112Muted)
            Text(value, fontSize = 14.sp, fontWeight = FontWeight.ExtraBold, color = V112Ink)
        }
    }
}
