package ro.autoid.app

import android.content.Intent
import android.graphics.Color as AndroidColor
import android.net.Uri
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import ro.autoid.app.data.Product

@Composable
fun ProductAboutV113(p: Product) {
    var expanded by remember(p.id) { mutableStateOf(false) }
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Row {
            Icon(Icons.Default.Info, null, tint = androidx.compose.ui.graphics.Color(0xFFF7630C), modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(8.dp))
            Text("Despre produs", fontSize = 19.sp, fontWeight = FontWeight.ExtraBold, color = androidx.compose.ui.graphics.Color(0xFF101828))
        }

        if (p.shortDescription.isNotBlank()) {
            Text(
                p.shortDescription,
                color = androidx.compose.ui.graphics.Color(0xFF344054),
                lineHeight = 21.sp,
                fontSize = 14.sp
            )
        }

        if (p.descriptionHtml.isNotBlank()) {
            Surface(
                onClick = { expanded = !expanded },
                shape = RoundedCornerShape(16.dp),
                color = androidx.compose.ui.graphics.Color(0xFFF8FAFC),
                border = BorderStroke(1.dp, androidx.compose.ui.graphics.Color(0xFFEAECF0)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(Modifier.padding(horizontal = 14.dp, vertical = 12.dp)) {
                    Text(
                        if (expanded) "Ascunde informațiile complete" else "Mai multe informații",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.ExtraBold,
                        fontSize = 13.sp,
                        color = androidx.compose.ui.graphics.Color(0xFFF7630C)
                    )
                    Icon(
                        if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                        contentDescription = null,
                        tint = androidx.compose.ui.graphics.Color(0xFFF7630C)
                    )
                }
            }
            if (expanded) RichProductHtmlV113(p.descriptionHtml, p.youtubeIds)
        }
    }
}

@Composable
private fun RichProductHtmlV113(html: String, youtubeIds: List<String>) {
    val context = LocalContext.current
    var measuredHeight by remember(html, youtubeIds) { mutableIntStateOf(420) }
    val safeHeight = measuredHeight.coerceIn(220, 5200)
    val videos = youtubeIds.distinct().joinToString("\n") { id ->
        """<section class="video-block"><div class="video-title">Video</div><div class="video-frame"><iframe src="https://www.youtube-nocookie.com/embed/$id" title="Video produs" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div></section>"""
    }
    val document = remember(html, videos) {
        """
        <!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
        <style>
        *{box-sizing:border-box} body{margin:0;padding:2px 1px 8px;background:#fff;color:#344054;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;font-size:15px;line-height:1.55;overflow:hidden}
        h1,h2,h3,h4{color:#101828;line-height:1.25;margin:22px 0 10px;font-weight:800} h1{font-size:24px} h2{font-size:21px} h3{font-size:18px} h4{font-size:16px}
        p{margin:0 0 12px} strong,b{color:#101828} ul,ol{padding-left:22px;margin:8px 0 16px} li{margin:5px 0}
        a{color:#f7630c;text-decoration:none;font-weight:650} img{max-width:100%;height:auto;border-radius:12px;margin:10px 0}
        table{width:100%;border-collapse:separate;border-spacing:0;margin:14px 0;border:1px solid #e4e7ec;border-radius:12px;overflow:hidden;font-size:13px} th{background:#f8fafc;color:#101828;font-weight:800;text-align:left} th,td{padding:10px;border-bottom:1px solid #eaecf0;vertical-align:top} tr:last-child td{border-bottom:0}
        blockquote{margin:14px 0;padding:12px 14px;border-left:3px solid #f7630c;background:#fff7f2;border-radius:0 12px 12px 0}
        .video-block{margin:20px 0 8px}.video-title{font-size:16px;font-weight:800;color:#101828;margin-bottom:8px}.video-frame{position:relative;width:100%;padding-top:56.25%;overflow:hidden;border-radius:14px;background:#101828}.video-frame iframe{position:absolute;inset:0;width:100%;height:100%}
        </style></head><body><article>$html</article>$videos</body></html>
        """.trimIndent()
    }

    AndroidView(
        modifier = Modifier.fillMaxWidth().height(safeHeight.dp),
        factory = { ctx ->
            WebView(ctx).apply {
                setBackgroundColor(AndroidColor.TRANSPARENT)
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                settings.loadWithOverviewMode = false
                settings.useWideViewPort = false
                settings.mediaPlaybackRequiresUserGesture = true
                isVerticalScrollBarEnabled = false
                isHorizontalScrollBarEnabled = false
                webChromeClient = WebChromeClient()
                webViewClient = object : WebViewClient() {
                    override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                        val url = request?.url?.toString().orEmpty()
                        if (url.isBlank() || url.contains("youtube-nocookie.com/embed/")) return false
                        runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url))) }
                        return true
                    }

                    override fun onPageFinished(view: WebView, url: String?) {
                        view.evaluateJavascript("(function(){return Math.max(document.body.scrollHeight,document.documentElement.scrollHeight);})()") { raw ->
                            val h = raw.trim('"').toDoubleOrNull()?.toInt()
                            if (h != null && h > 0) measuredHeight = h + 18
                        }
                    }
                }
                tag = document.hashCode()
                loadDataWithBaseURL("https://www.autoid.ro/", document, "text/html", "utf-8", null)
            }
        },
        update = { view ->
            if (view.tag != document.hashCode()) {
                view.tag = document.hashCode()
                view.loadDataWithBaseURL("https://www.autoid.ro/", document, "text/html", "utf-8", null)
            }
        }
    )
}
