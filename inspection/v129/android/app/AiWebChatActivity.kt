package ro.autoid.app

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.CookieManager
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import ro.autoid.app.ui.theme.AutoIdTheme

class AiWebChatActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent { AutoIdTheme { AiWebChatScreen { finish() } } }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@SuppressLint("SetJavaScriptEnabled")
@Composable
private fun AiWebChatScreen(onBack: () -> Unit) {
    var loading by remember { mutableStateOf(true) }
    Scaffold(topBar = { TopAppBar(title = { Text("AutoID AI") }, navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "Înapoi") } }) }) { pad ->
        Box(Modifier.padding(pad).fillMaxSize()) {
            AndroidView(modifier = Modifier.fillMaxSize(), factory = { context ->
                WebView(context).apply {
                    settings.javaScriptEnabled = true
                    settings.domStorageEnabled = true
                    settings.userAgentString = settings.userAgentString + " AutoID-Android/0.5.0"
                    CookieManager.getInstance().setAcceptCookie(true)
                    webChromeClient = WebChromeClient()
                    webViewClient = object : WebViewClient() { override fun onPageFinished(view: WebView?, url: String?) { loading = false } }
                    loadUrl("https://www.autoid.ro/support/?autoid_app=android")
                }
            })
            if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
        }
    }
}
