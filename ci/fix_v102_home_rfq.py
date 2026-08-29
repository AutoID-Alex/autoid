from pathlib import Path
import re

p=Path('android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt')
s=p.read_text()

# Root HomeV100 call: add RFQ callback after the cart callback, independent of formatting.
# Scope the replacement to the first HomeV100 invocation so ProductV100/HomeCard calls are untouched.
root_pos=s.find('HomeV100(')
if root_pos < 0:
    raise SystemExit('HomeV100 root invocation missing')
root_end=s.find('V100Tab.Categories', root_pos)
if root_end < 0:
    root_end=min(len(s), root_pos+5000)
root=s[root_pos:root_end]
if '{addRfq(it)}' not in root:
    root2,n=re.subn(r'(\{\s*addCart\(it\)\s*\}\s*,)', r'\1{addRfq(it)},', root, count=1)
    if n==0:
        raise SystemExit('HomeV100 root cart callback missing')
    s=s[:root_pos]+root2+s[root_end:]

# HomeV100 declaration: add onRfq between onCart and onAi, tolerating whitespace/newlines.
fn_pos=s.find('fun HomeV100(')
if fn_pos < 0:
    raise SystemExit('HomeV100 declaration missing')
fn_body=s.find('{', fn_pos)
if fn_body < 0:
    raise SystemExit('HomeV100 declaration body missing')
head=s[fn_pos:fn_body]
if 'onRfq:' not in head:
    head2,n=re.subn(
        r'(onCart\s*:\s*\(Product\)\s*->\s*Unit\s*,\s*)(onAi\s*:)',
        r'\1onRfq:(Product)->Unit,\2',
        head,
        count=1
    )
    if n==0:
        raise SystemExit('HomeV100 onCart/onAi signature region missing')
    s=s[:fn_pos]+head2+s[fn_body:]

# HomeCard declaration created by apply_v102: add onRfq after onCart.
hc_pos=s.find('private fun HomeCard(')
if hc_pos < 0:
    raise SystemExit('HomeCard declaration missing')
hc_body=s.find('{', hc_pos)
head=s[hc_pos:hc_body]
if 'onRfq:' not in head:
    head2,n=re.subn(
        r'(onCart\s*:\s*\(\)\s*->\s*Unit\s*)(\n?\s*\))',
        r'\1,\n    onRfq: () -> Unit\2',
        head,
        count=1
    )
    if n==0:
        raise SystemExit('HomeCard onCart signature region missing')
    s=s[:hc_pos]+head2+s[hc_body:]

# Inside HomeV100 only, append RFQ callback to HomeCard calls that currently end with onCart.
fn_pos=s.find('fun HomeV100(')
next_fn=s.find('@Composable', fn_body+1)
# HomeV100 is compact/large; use the section up to the next top-level helper after its declaration.
if next_fn < 0:
    next_fn=len(s)
section=s[fn_pos:next_fn]
section=re.sub(
    r'(HomeCard\([^\n]*?\{onCart\(p\)\})(\s*\)))',
    lambda m: m.group(1)[:-1] + ',{onRfq(p)})',
    section
)
s=s[:fn_pos]+section+s[next_fn:]

# Also handle multiline/compact HomeCard calls globally where the final callback is exactly {onCart(p)}.
s=s.replace('{onFavorite(p)},{onCart(p)})','{onFavorite(p)},{onCart(p)},{onRfq(p)})')
s=s.replace('{ onFavorite(p) }, { onCart(p) })','{ onFavorite(p) }, { onCart(p) }, { onRfq(p) })')

# The RFQ button in HomeCard must invoke the RFQ callback, not open the product.
hc_pos=s.find('private fun HomeCard(')
hc_end=s.find('@Composable', hc_pos+20)
if hc_end < 0:
    hc_end=len(s)
hc=s[hc_pos:hc_end]
if 'Text("Cerere ofertă"' in hc:
    # Replace the OutlinedButton action nearest the Cerere ofertă label.
    pattern=r'OutlinedButton\(onClick\s*=\s*onClick([^\{]*\{\s*Text\("Cerere ofertă")'
    hc2,n=re.subn(pattern, r'OutlinedButton(onClick = onRfq\1{\n                    Text("Cerere ofertă")', hc, count=1, flags=re.S)
    if n==0:
        hc2=hc.replace('OutlinedButton(onClick = onClick, modifier = Modifier.weight(1f).height(44.dp)', 'OutlinedButton(onClick = onRfq, modifier = Modifier.weight(1f).height(44.dp)', 1)
    hc=hc2
s=s[:hc_pos]+hc+s[hc_end:]

# Related products in ProductV100 need a concrete RFQ callback as well.
s=s.replace(
    'HomeCard(r,commerce.isFavorite(r.id),{onOpen(r)},{onFavorite(r)},{onCart(r,1)})',
    'HomeCard(r,commerce.isFavorite(r.id),{onOpen(r)},{onFavorite(r)},{onCart(r,1)},{onRfq(r,1)})'
)
s=s.replace(
    'HomeCard(r, commerce.isFavorite(r.id), { onOpen(r) }, { onFavorite(r) }, { onCart(r,1) })',
    'HomeCard(r, commerce.isFavorite(r.id), { onOpen(r) }, { onFavorite(r) }, { onCart(r,1) }, { onRfq(r,1) })'
)

p.write_text(s)
print('Wired v1.0.2 Home RFQ callbacks with anchor-safe patching')
