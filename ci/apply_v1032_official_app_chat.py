#!/usr/bin/env python3
"""Finalize AutoID Mobile v1.1.25 using Support Center's official Android app API."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php"
HELPERS = ROOT / "ci/v132/autoid_support_app_api_bridge.php.inc"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    text = PLUGIN.read_text()
    text = once(text, " * Version: 1.1.24", " * Version: 1.1.25", "plugin version")
    text = once(text, "            'version'=>'1.1.24',", "            'version'=>'1.1.25',", "health version")
    text = text.replace("AutoID-Mobile-WordPress/1.1.24", "AutoID-Mobile-WordPress/1.1.25")

    anchor = "        $answer=self::support_app_api_v129($message,$product_id,$context);\n        if($answer!=='') return rest_ensure_response(['answer'=>$answer,'source'=>'autoid-support-api','support_center'=>$context['support_center']]);\n"
    patch = anchor + "\n        // Canonical native-app contract exposed by AutoID Support Center 2.28.2+.\n        // AUTOID_SUPPORT_APP_TOKEN stays server-side in wp-config.php/environment.\n        $official=self::support_center_app_chat_v132($message,$product_id,$device_id,$context);\n        if(is_array($official) && trim((string)($official['answer']??''))!=='') {\n            return rest_ensure_response([\n                'answer'=>trim((string)$official['answer']),\n                'source'=>'autoid-support-app-api',\n                'handler'=>'/autoid-support/v2/app/chat',\n                'bridge'=>'v132-official-app-api',\n                'phase'=>sanitize_key((string)($official['phase']??'')),\n                'model_id'=>absint($official['model_id']??0),\n                'resolved'=>!empty($official['resolved']),\n                'support_center'=>$context['support_center'],\n            ]);\n        }\n        $official_diagnostic=is_array($official)?sanitize_text_field((string)($official['diagnostic']??'')):'';\n"
    text = once(text, anchor, patch, "official Support Center app API call")

    marker = "    private static function support_center_v2_chat_v131($message,$product_id,$context) {"
    helpers = HELPERS.read_text().rstrip() + "\n\n"
    text = once(text, marker, helpers + marker, "official app API helpers")

    old_error = "        return new WP_Error('autoid_support_ai_adapter_missing','AutoID Support Center este detectat, dar API-ul său AI nu a putut finaliza conversația din aplicația mobilă.',['status'=>503,'support_center'=>$context['support_center'],'bridge'=>'v131-direct-rest','support_v2'=>$support_v2_diagnostic]);"
    new_error = "        return new WP_Error('autoid_support_ai_adapter_missing','AutoID Support Center este detectat, dar API-ul Android oficial nu a putut finaliza conversația.',['status'=>503,'support_center'=>$context['support_center'],'bridge'=>'v132-official-app-api','app_api'=>$official_diagnostic,'legacy_support_v2'=>$support_v2_diagnostic]);"
    text = once(text, old_error, new_error, "final diagnostic error")

    for required in [
        "support_center_app_chat_v132",
        "/autoid-support/v2/app/chat",
        "AUTOID_SUPPORT_APP_TOKEN",
        "v132-official-app-api",
        "APP_TOKEN_MISSING_OR_SHORT",
    ]:
        if required not in text:
            raise RuntimeError(f"Missing official Support Center app API contract: {required}")

    PLUGIN.write_text(text)
    print("Applied AutoID Mobile v1.1.25 official Support Center Android app API bridge")


if __name__ == "__main__":
    main()
