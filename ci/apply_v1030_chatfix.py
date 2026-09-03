#!/usr/bin/env python3
"""Finalize AutoID Mobile v1.1.23 Support Center chat compatibility hotfix."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    text = PLUGIN.read_text()
    text = once(text, " * Version: 1.1.22", " * Version: 1.1.23", "plugin version")
    text = once(text, "            'version'=>'1.1.22',", "            'version'=>'1.1.23',", "health version")
    text = text.replace("AutoID-Mobile-WordPress/1.1.22", "AutoID-Mobile-WordPress/1.1.23")
    if "support_center_compat_v130" not in text:
        raise RuntimeError("Support Center compatibility bridge is missing from generated plugin")
    if "support_center_rest_scan_v130" not in text or "support_center_ajax_scan_v130" not in text:
        raise RuntimeError("Support Center REST/AJAX compatibility scans are missing")
    PLUGIN.write_text(text)
    print("Applied AutoID Mobile v1.1.23 Support Center chat compatibility hotfix")


if __name__ == "__main__":
    main()
