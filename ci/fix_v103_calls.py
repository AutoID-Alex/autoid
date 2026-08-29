from pathlib import Path
import re

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


def replace_call(text: str, marker_re: str, call_name: str, replacement: str, label: str) -> str:
    m = re.search(marker_re, text)
    if not m:
        raise SystemExit(f'{label} marker missing')
    start = text.find(call_name, m.start(), m.end())
    if start < 0:
        start = text.find(call_name, m.start())
    if start < 0:
        raise SystemExit(f'{label} call missing')
    open_idx = text.find('(', start + len(call_name))
    if open_idx < 0:
        raise SystemExit(f'{label} open paren missing')
    end = call_end(text, open_idx)
    return text[:start] + replacement + text[end:]


category_call = '''CatalogV100(
    api = api,
    commerce = commerce,
    category = category,
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

# Replace the selected-category Catalog route first so it cannot be confused
# with the Categories-tab call below.
s = replace_call(
    s,
    r'category\s*!=\s*null\s*->\s*CatalogV100\s*\(',
    'CatalogV100',
    category_call,
    'selected category CatalogV100'
)

s = replace_call(
    s,
    r'V100Tab\.Home\s*->\s*HomeV100\s*\(',
    'HomeV100',
    home_call,
    'HomeV100 root'
)

s = replace_call(
    s,
    r'V100Tab\.Categories\s*->\s*CatalogV100\s*\(',
    'CatalogV100',
    categories_tab_call,
    'Categories CatalogV100 root'
)

p.write_text(s)
print('Normalized v1.0.3 root Home/Catalog calls to named arguments')
