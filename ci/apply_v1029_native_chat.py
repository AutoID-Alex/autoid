#!/usr/bin/env python3
"""Apply the auditable v1.0.29 native-chat patch to generated v1.0.28 sources."""

from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "android-v0.1/app/src/main/java/ro/autoid/app"
API = APP / "data/AutoIdApi.kt"
MAIN = APP / "MainActivity.kt"
GRADLE = ROOT / "android-v0.1/app/build.gradle.kts"
PLUGIN = ROOT / "wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php"
ASSETS = ROOT / "ci/v129"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    first = text.find(start)
    last = text.find(end, first + len(start))
    if first < 0 or last < 0:
        raise RuntimeError(f"{label}: anchors not found")
    return text[:first] + replacement.rstrip() + "\n\n" + text[last:]


def patch_plugin() -> None:
    text = PLUGIN.read_text()
    text = replace_once(text, " * Version: 1.1.17", " * Version: 1.1.21", "plugin header")
    text = replace_once(
        text,
        "        register_rest_route(self::NS, '/ai/chat', $public + ['methods'=>'POST','callback'=>[__CLASS__,'ai_chat']]);",
        "        register_rest_route(self::NS, '/ai/token', $public + ['methods'=>'POST','callback'=>[__CLASS__,'ai_token_v129']]);\n"
        "        register_rest_route(self::NS, '/ai/chat', $public + ['methods'=>'POST','callback'=>[__CLASS__,'ai_chat']]);",
        "chat routes",
    )
    text = replace_between(
        text,
        "    public static function ai_chat(WP_REST_Request $r) {",
        "    private static function support_center_info() {",
        (ASSETS / "autoid_chat_v129.php.inc").read_text(),
        "chat backend",
    )
    text = replace_once(text, "            'version'=>'1.1.12',", "            'version'=>'1.1.21',", "health version")
    PLUGIN.write_text(text)


def patch_api() -> None:
    text = API.read_text()
    text = replace_once(
        text,
        "class AutoIdApi {",
        "data class ChatSessionV129(val token:String,val expiresAt:Long)\n"
        "class AutoIdHttpExceptionV129(val status:Int,message:String):RuntimeException(message)\n\n"
        "class AutoIdApi {",
        "chat API models",
    )
    text = replace_once(
        text,
        '    fun aiChat(message:String,productId:Long?=null):String{val b=JSONObject().put("message",message);productId?.let{b.put("product_id",it)};return html(JSONObject(post("$MOBILE/ai/chat",b.toString())).optString("answer")).ifBlank{error("Asistentul AI nu a returnat răspuns.")}}',
        '    fun chatTokenV129(deviceId:String):ChatSessionV129{val b=JSONObject().put("device_id",deviceId).put("platform","android").put("app_version","1.0.29");val o=JSONObject(post("$MOBILE/ai/token",b.toString()));val token=o.optString("token");if(token.isBlank())error("Serverul nu a emis sesiunea temporară de chat.");return ChatSessionV129(token,o.optLong("expires_at"))}\n'
        '    fun aiChatV129(message:String,productId:Long?,deviceId:String,chatToken:String):String{val b=JSONObject().put("message",message).put("device_id",deviceId);productId?.let{b.put("product_id",it)};return html(JSONObject(post("$MOBILE/ai/chat",b.toString(),chatToken)).optString("answer")).ifBlank{error("Asistentul AutoID nu a returnat răspuns.")}}\n'
        '    @Deprecated("Use the short-lived chat session flow") fun aiChat(message:String,productId:Long?=null):String{val b=JSONObject().put("message",message);productId?.let{b.put("product_id",it)};return html(JSONObject(post("$MOBILE/ai/chat",b.toString())).optString("answer")).ifBlank{error("Asistentul AutoID nu a returnat răspuns.")}}',
        "chat API calls",
    )
    text = replace_once(text, 'AutoID-Android/1.0.28', 'AutoID-Android/1.0.29', "user agent")
    text = replace_once(
        text,
        'if(status !in 200..299)error(runCatching{JSONObject(text).optString("message",text)}.getOrDefault(text).ifBlank{"HTTP $status"});return text',
        'if(status !in 200..299)throw AutoIdHttpExceptionV129(status,runCatching{JSONObject(text).optString("message",text)}.getOrDefault(text).ifBlank{"HTTP $status"});return text',
        "HTTP status errors",
    )
    API.write_text(text)


def patch_android() -> None:
    gradle = GRADLE.read_text()
    gradle = replace_once(gradle, "versionCode = 13100", "versionCode = 13200", "version code")
    gradle = replace_once(gradle, 'versionName = "1.0.28"', 'versionName = "1.0.29"', "version name")
    GRADLE.write_text(gradle)

    main = MAIN.read_text()
    main = replace_once(main, "fun NativeAiChatScreen(api:AutoIdApi,productId:Long?,onBack:()->Unit){", "fun LegacyNativeAiChatScreenV128(api:AutoIdApi,productId:Long?,onBack:()->Unit){", "legacy chat name")
    MAIN.write_text(main)

    shutil.copyfile(ASSETS / "V129NativeChat.kt", APP / "V129NativeChat.kt")


def main() -> None:
    patch_plugin()
    patch_api()
    patch_android()
    print("Applied AutoID Android v1.0.29 RC1 + WordPress plugin v1.1.21 native chat patch")


if __name__ == "__main__":
    main()
