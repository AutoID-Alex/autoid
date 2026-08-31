#!/usr/bin/env bash
set -euo pipefail

python3 ci/apply_v05.py
python3 ci/fix_v05_experimental.py
python3 ci/apply_v06.py
python3 ci/fix_v06_navigation_parse.py
python3 ci/apply_v07.py
python3 ci/apply_v08.py
python3 - <<'PY'
from pathlib import Path
p=Path('ci/apply_v100.py'); s=p.read_text(); a=s.index("# Replace the v0.8 bridge"); b=s.index("# Product model:",a); p.write_text(s[:a]+s[b:])
PY
python3 ci/apply_v100.py
python3 ci/fix_v100_kotlin.py
python3 ci/patch_bridge_v100.py
python3 ci/apply_v101.py
python3 ci/patch_bridge_v101.py
python3 - <<'PY'
from pathlib import Path
p=Path('ci/apply_v102.py'); s=p.read_text()
s=s.replace("anchor='@Composable private fun CatalogCard('\nidx=s.index(anchor)","anchor='private fun CatalogCard('\nidx=s.rfind('@Composable',0,s.index(anchor))")
s=s.replace("start=s.index('@Composable private fun CatalogCard(')\nend=s.index('@Composable fun ProductV100',start)","catalog_fn=s.index('private fun CatalogCard(')\nstart=s.rfind('@Composable',0,catalog_fn)\nproduct_fn=s.index('fun ProductV100',catalog_fn)\nend=s.rfind('@Composable',catalog_fn,product_fn)")
s=s.replace("start=s.index('@Composable private fun HomeCard(')\nend=s.index('@Composable private fun DiscountChip',start)","home_fn=s.index('private fun HomeCard(')\nstart=s.rfind('@Composable',0,home_fn)\ndiscount_fn=s.index('private fun DiscountChip',home_fn)\nend=s.rfind('@Composable',home_fn,discount_fn)")
p.write_text(s)
PY
python3 ci/apply_v102.py
python3 ci/fix_v102_home_rfq.py
python3 ci/patch_bridge_v102.py
python3 ci/patch_bridge_v103.py
python3 ci/fix_v103_anchors.py
python3 ci/apply_v103.py
python3 ci/fix_v103_calls.py
python3 ci/fix_v104_anchors.py
python3 ci/apply_v104.py
python3 ci/fix_v104_root.py
python3 ci/fix_v104_button_dimensions.py
python3 ci/patch_bridge_v104.py
python3 ci/apply_v1042.py
python3 ci/patch_bridge_v1042.py
python3 ci/fix_v1043_ui.py
python3 ci/patch_bridge_v1043.py
python3 ci/apply_v105_filters.py
python3 ci/patch_bridge_v105_filters.py
python3 ci/apply_v106_home_hero.py
python3 ci/patch_bridge_v106_mega_hero.py
python3 ci/apply_v107_payload.py
python3 ci/apply_v107_infinite_legacy.py
python3 ci/apply_v108.py
python3 ci/patch_unified_mobile_v110.py
python3 ci/apply_v109_hero_studio.py
python3 ci/patch_unified_mobile_v111_hero_studio.py
python3 ci/apply_v110_live_hero.py
python3 ci/patch_unified_mobile_v112_live_hero.py
python3 ci/apply_v1011_hero_loading_perf.py
python3 ci/patch_unified_mobile_v113_hero_perf.py
python3 ci/apply_v1012_loader_filters.py
python3 ci/apply_v1013_dynamic_filters_product_content.py
python3 ci/patch_unified_mobile_v114_dynamic_facets_product_content.py
python3 - <<'PY'
from pathlib import Path
import base64,zlib
raw=Path('ci/v114_patch_payload.b64').read_text().strip()
Path('/tmp/apply_v1014.py').write_bytes(zlib.decompress(base64.b64decode(raw)))
PY
python3 /tmp/apply_v1014.py
python3 ci/apply_v1015_clean.py
python3 ci/fix_v1015_panel_scope.py
python3 ci/patch_mobile_v116_account.py

echo 'Prepared AutoID Android v1.0.15 + AutoID Mobile v1.1.6'
