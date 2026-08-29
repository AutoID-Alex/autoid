from pathlib import Path

p = Path('android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt')
s = p.read_text()


def call_end(text: str, open_idx: int) -> int:
    depth = 0
    quote = None
    escaped = False
    for i in range(open_idx, len(text)):
        ch = text[i]
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if ch in ('"', "'"):
            quote = ch
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return i + 1
    raise SystemExit('unterminated call')


def call_slice(text: str, start: int, call_name: str):
    open_idx = text.find('(', start + len(call_name))
    if open_idx < 0:
        raise SystemExit(f'{call_name} open parenthesis missing')
    end = call_end(text, open_idx)
    return open_idx, end, text[start:end]


def replace_call_at(text: str, start: int, call_name: str, replacement: str) -> str:
    _, end, _ = call_slice(text, start, call_name)
    return text[:start] + replacement + text[end:]


def top_level_args(call_text: str):
    open_idx = call_text.find('(')
    close_idx = len(call_text) - 1
    body = call_text[open_idx + 1:close_idx]
    args = []
    start = 0
    depth = 0
    quote = None
    escaped = False
    for i, ch in enumerate(body):
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if ch in ('"', "'"):
            quote = ch
        elif ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
        elif ch == ',' and depth == 0:
            args.append(body[start:i].strip())
            start = i + 1
    tail = body[start:].strip()
    if tail:
        args.append(tail)
    return args


home_call = '''HomeV100(
    api = api,
    commerce = commerce,
    onMenu = { menu = true },
    onSearch = { value ->
        search = value
        category = ProductCategory(0, "Rezultate", 0)
    },
    onCategory = ::openCategory,
    onProduct = ::openProduct,
    onFavorite = { product ->
        commerce.toggleFavorite(product.id)
        favTick++
    },
    onCart = { product -> addCart(product) },
    onRfq = { product -> addRfq(product) },
    onAi = { ai = true },
    onConsult = { consult = true },
    onFavorites = { favorites = true },
    onNotifications = { notifications = true },
    onFullCart = { tab = V100Tab.Cart },
    mini = miniCart,
    onMini = { value -> miniCart = value },
    scan = scan,
    cartTick = cartTick
)'''

selected_category_call = '''CatalogV100(
    api = api,
    commerce = commerce,
    category = category!!,
    initialSearch = search,
    onBack = { category = null },
    onSubcategory = ::openCategory,
    onProduct = ::openProduct,
    onFavorite = { product ->
        commerce.toggleFavorite(product.id)
        favTick++
    },
    onCart = { product -> addCart(product) },
    onRfq = { product -> addRfq(product) },
    onAi = { ai = true },
    onFavorites = { favorites = true },
    onHeaderCart = {
        tab = V100Tab.Cart
        category = null
    },
    scan = scan
)'''

home_decl = s.find('fun HomeV100(')
if home_decl < 0:
    raise SystemExit('HomeV100 declaration missing')
home_root = s.find('HomeV100(')
if home_root < 0 or home_root >= home_decl:
    raise SystemExit('HomeV100 root invocation missing')
s = replace_call_at(s, home_root, 'HomeV100', home_call)

catalog_decl = s.find('fun CatalogV100(')
if catalog_decl < 0:
    raise SystemExit('CatalogV100 declaration missing')

roots = []
pos = 0
while True:
    pos = s.find('CatalogV100(', pos, catalog_decl)
    if pos < 0:
        break
    _, end, body = call_slice(s, pos, 'CatalogV100')
    roots.append((pos, body))
    pos = end

if not roots:
    raise SystemExit('No root CatalogV100 invocation found')

for start, body in reversed(roots):
    args = top_level_args(body)
    third = args[2].replace(' ', '') if len(args) > 2 else ''
    if third == 'null' or third.endswith('=null'):
        raise SystemExit('Unexpected nullable CatalogV100 root route after v1.0.1 migration')
    s = replace_call_at(s, start, 'CatalogV100', selected_category_call)

# HomeV100 was rewritten in v1.0.3, while SmartSearch already has the newer
# signature from v1.0.1: api, query, onQueryChange, onSubmit, onProduct, scan.
# Supply the missing product callback before scan.
smart_old = 'SmartSearch(api, q, { q = it }, { onSearch(it) }, scan)'
smart_new = 'SmartSearch(api, q, { q = it }, { onSearch(it) }, onProduct, scan)'
if smart_old not in s:
    if smart_new not in s:
        raise SystemExit('Home SmartSearch invocation missing')
else:
    s = s.replace(smart_old, smart_new, 1)

p.write_text(s)

lines = s.splitlines()
for i, line in enumerate(lines, 1):
    if 'CatalogV100(' in line and 'fun CatalogV100(' not in line:
        print(f'CatalogV100 call at generated line {i}: {line.strip()}')
    if 'SmartSearch(' in line and 'fun SmartSearch(' not in line:
        print(f'SmartSearch call at generated line {i}: {line.strip()}')
print(f'Normalized v1.0.3 root calls: Home=1, Catalog roots={len(roots)}; wired onSubcategory and SmartSearch onProduct')
