#!/usr/bin/env python3
"""Wire AutoID Mobile v1.1.24 directly to AutoID Support Center v2 chat/session REST."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php"
BRIDGE = ROOT / "ci/v131/autoid_support_v2_bridge.php.inc"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    text = PLUGIN.read_text()
    text = once(text, " * Version: 1.1.23", " * Version: 1.1.24", "plugin version")
    text = once(text, "            'version'=>'1.1.23',", "            'version'=>'1.1.24',", "health version")
    text = text.replace("AutoID-Mobile-WordPress/1.1.23", "AutoID-Mobile-WordPress/1.1.24")

    direct_anchor = "        $answer=self::support_app_api_v129($message,$product_id,$context);\n        if($answer!=='') return rest_ensure_response(['answer'=>$answer,'source'=>'autoid-support-api','support_center'=>$context['support_center']]);\n"
    direct_patch = direct_anchor + "\n        // Direct AutoID Support Center v2 contract: create/resume a Support Center\n        // session first, then send the chat message through its canonical REST route.\n        $support_v2=self::support_center_v2_chat_v131($message,$product_id,$context);\n        if(is_array($support_v2) && trim((string)($support_v2['answer']??''))!=='') {\n            return rest_ensure_response([\n                'answer'=>trim((string)$support_v2['answer']),\n                'source'=>'autoid-support-v2',\n                'handler'=>'/autoid-support/v2/chat',\n                'bridge'=>'v131-direct-rest',\n                'support_center'=>$context['support_center'],\n            ]);\n        }\n        $support_v2_diagnostic=is_array($support_v2)?sanitize_text_field((string)($support_v2['diagnostic']??'')):'';\n"
    text = once(text, direct_anchor, direct_patch, "direct Support Center v2 call")

    marker = "    private static function support_center_info() {"
    helpers = BRIDGE.read_text().rstrip() + "\n\n"
    text = once(text, marker, helpers + marker, "Support Center v2 helpers")

    old_error = "        return new WP_Error('autoid_support_ai_adapter_missing','AutoID Support Center este detectat, dar handler-ul său AI nu a putut fi apelat din aplicația mobilă.',['status'=>503,'support_center'=>$context['support_center'],'bridge'=>'compat-v130']);"
    new_error = "        return new WP_Error('autoid_support_ai_adapter_missing','AutoID Support Center este detectat, dar API-ul său AI nu a putut finaliza conversația din aplicația mobilă.',['status'=>503,'support_center'=>$context['support_center'],'bridge'=>'v131-direct-rest','support_v2'=>$support_v2_diagnostic]);"
    text = once(text, old_error, new_error, "diagnostic error")

    for required in [
        "support_center_v2_chat_v131",
        "/autoid-support/v2/chat/session",
        "/autoid-support/v2/chat",
        "support_v2_diagnostic",
        "v131-direct-rest",
    ]:
        if required not in text:
            raise RuntimeError(f"Missing generated Support Center v2 contract: {required}")

    PLUGIN.write_text(text)
    print("Applied AutoID Mobile v1.1.24 direct AutoID Support Center v2 chat/session bridge")


if __name__ == "__main__":
    main()
