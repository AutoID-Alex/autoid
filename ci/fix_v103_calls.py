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

categories_tab_call = '''CatalogV100(
    api = api,
    commerce = commerce,
    category = null,
    initialSearch = search,
    onBack = { tab = V100Tab.Home },
    onProduct = ::openProduct,
    onFavorite = { product ->
        commerce.toggleFavorite(product.id)
        favTick++
    },
    onCart = { product -> addCart(product) },
    onRfq = { product -> addRfq(product) },
    onAi = { ai = true },
    onFavorites = { favorites = true },
    onHeaderCart = { tab = V100Tab.Cart },
    scan = scan
)'''

# Normalize the single root Home invocation before its declaration.
home_decl = s.find('fun HomeV100(')
if home_decl < 0:
    raise SystemExit('HomeV100 declaration missing')
home_root = s.find('HomeV100(')
if home_root < 0 or home_root >= home_decl:
    raise SystemExit('HomeV100 root invocation missing')
s = replace_call_at(s, home_root, 'HomeV100', home_call)

# Normalize every CatalogV100 invocation that exists before the declaration.
# Depending on earlier migrations there can legitimately be one or two root
# invocations, so do not fail merely because one route was consolidated.
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
    compact = ''.join(body.split())
    is_categories_tab = (
        'category=null' in compact or
        'CatalogV100(api,commerce,null,' in compact or
        'onBack={tab=V100Tab.Home}' in compact
    )
    replacement = categories_tab_call if is_categories_tab else selected_category_call
    s = replace_call_at(s, start, 'CatalogV100', replacement)

p.write_text(s)
print(f'Normalized v1.0.3 root calls: Home=1, Catalog={len(roots)}')
