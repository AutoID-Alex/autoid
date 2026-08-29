from pathlib import Path

p = Path('ci/apply_v103.py')
s = p.read_text()

old = '''home_start = s.find('@Composable fun HomeV100(')\nif home_start < 0:\n    raise SystemExit('HomeV100 declaration missing')\nhero_start = s.find('@Composable private fun Hero(', home_start)\nif hero_start < 0:\n    raise SystemExit('Legacy Hero declaration missing')\nhero_end = s.find('@Composable private fun QuickCategory', hero_start)\nif hero_end < 0:\n    raise SystemExit('QuickCategory anchor missing')\n'''

new = '''home_fn = s.find('fun HomeV100(')\nif home_fn < 0:\n    raise SystemExit('HomeV100 declaration missing')\nhome_start = s.rfind('@Composable', 0, home_fn)\nif home_start < 0:\n    raise SystemExit('HomeV100 @Composable anchor missing')\n\nhero_fn = s.find('private fun Hero(', home_fn)\nif hero_fn < 0:\n    raise SystemExit('Legacy Hero declaration missing')\nhero_start = s.rfind('@Composable', home_fn, hero_fn)\nif hero_start < 0:\n    raise SystemExit('Legacy Hero @Composable anchor missing')\n\nquick_fn = s.find('private fun QuickCategory', hero_fn)\nif quick_fn < 0:\n    raise SystemExit('QuickCategory anchor missing')\nhero_end = s.rfind('@Composable', hero_fn, quick_fn)\nif hero_end < 0:\n    raise SystemExit('QuickCategory @Composable anchor missing')\n'''

if old not in s:
    raise SystemExit('v1.0.3 Home/Hero anchor block not found in migration script')

s = s.replace(old, new, 1)
p.write_text(s)
print('Normalized v1.0.3 Home/Hero migration anchors')
