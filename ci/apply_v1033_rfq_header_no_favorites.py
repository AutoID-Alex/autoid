#!/usr/bin/env python3
"""AutoID Android v1.0.30 RC5: remove Favorites UI and promote RFQ to app headers."""

from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "android-v0.1/app/src/main/java/ro/autoid/app"
V100 = APP / "V100Screens.kt"
V114 = APP / "V114CommerceUx.kt"
GRADLE = ROOT / "android-v0.1/app/build.gradle.kts"
ASSET = ROOT / "ci/v133/RfqHeaderV133.kt"


def replace_required(text: str, old: str, new: str, label: str, minimum: int = 1) -> str:
    count = text.count(old)
    if count < minimum:
        raise RuntimeError(f"{label}: expected at least {minimum} match(es), found {count}")
    return text.replace(old, new)


def patch_v100() -> None:
    text = V100.read_text()

    # Drawer: RFQ replaces Favorites in the same position.
    text = replace_required(
        text,
        'MenuRow(Icons.Default.FavoriteBorder,"Favorite",onFavorites)',
        'MenuRow(Icons.Default.RequestQuote,"Cerere de ofertă",onFavorites)',
        "drawer RFQ entry",
    )

    # Header actions: use the current RFQ draft with a live product-count badge.
    header_patterns = [
        ('IconButton(onClick = onFav) { Icon(Icons.Default.FavoriteBorder, "Favorite") }', 'RfqHeaderActionV133(onFav)'),
        ('IconButton(onClick=onFavorites){Icon(Icons.Default.FavoriteBorder,"Favorite")}', 'RfqHeaderActionV133(onFavorites)'),
        ('IconButton(onClick = onFavorites) { Icon(Icons.Default.FavoriteBorder, "Favorite") }', 'RfqHeaderActionV133(onFavorites)'),
    ]
    replaced_headers = 0
    for old, new in header_patterns:
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            replaced_headers += n
    if replaced_headers < 3:
        raise RuntimeError(f"header RFQ actions: expected at least 3 replacements, found {replaced_headers}")

    # Product cards no longer expose any wishlist/favorite control.
    card_re = re.compile(
        r'\n\s*IconButton\(onClick\s*=\s*onFavorite,\s*modifier\s*=\s*Modifier\.align\(Alignment\.TopEnd\)\)\s*\{\s*'
        r'Icon\(if\s*\(favorite\)\s*Icons\.Default\.Favorite\s*else\s*Icons\.Default\.FavoriteBorder,\s*"Favorite"[^\n]*\)\s*\}',
        re.MULTILINE,
    )
    text, card_count = card_re.subn('', text)
    if card_count < 2:
        raise RuntimeError(f"product-card favorite removal: expected at least 2, found {card_count}")

    # Product page: the old heart position becomes the RFQ draft action.
    detail_old = 'IconButton(onClick={onFavorite(p)}){Icon(if(commerce.isFavorite(p.id))Icons.Default.Favorite else Icons.Default.FavoriteBorder,"Favorite",tint=if(commerce.isFavorite(p.id))AutoIdOrange else Ink)}'
    text = replace_required(text, detail_old, 'RfqHeaderActionV133({onFavorite(p)})', "product detail RFQ header")

    # All navigation callbacks that previously opened Favorites now open the current RFQ draft.
    text = text.replace('{ menu = false; favorites = true }', '{ menu = false; rfq = true }')
    text = text.replace('onFavorites = { favorites = true }', 'onFavorites = { rfq = true }')
    text = text.replace('{ favorites = true },', '{ rfq = true },')

    # Product detail's former favorite callback is now an RFQ-open callback.
    text = text.replace('{ commerce.toggleFavorite(it.id); favTick++ },', '{ _ -> rfq = true },')

    # Card callbacks are intentionally inert: RFQ is handled by the explicit RFQ CTA.
    text = re.sub(
        r'onFavorite\s*=\s*\{\s*product\s*->\s*commerce\.toggleFavorite\(product\.id\)\s*favTick\+\+\s*\},',
        'onFavorite = { _ -> Unit },',
        text,
        flags=re.MULTILINE,
    )

    # The floating RFQ chip from v1.0.30 is redundant once the header owns this function.
    floating = '''                if(rfqLines.isNotEmpty())Surface(
                    modifier=Modifier.align(Alignment.TopEnd).padding(12.dp).clickable{rfq=true},
                    shape=RoundedCornerShape(8.dp),color=RfqIndicatorOrangeV130,shadowElevation=5.dp
                ){Row(Modifier.padding(horizontal=12.dp,vertical=10.dp),verticalAlignment=Alignment.CenterVertically){Icon(Icons.Default.RequestQuote,null,tint=Color.White,modifier=Modifier.size(18.dp));Spacer(Modifier.width(6.dp));Text("Cerere ofertă · ${rfqLines.sumOf{it.quantity}}",color=Color.White,fontWeight=FontWeight.ExtraBold,fontSize=11.sp)}}
'''
    if floating in text:
        text = text.replace(floating, '')

    # Safety net: no heart vector remains in the active V100 UI.
    text = text.replace('Icons.Default.FavoriteBorder', 'Icons.Default.RequestQuote')
    text = text.replace('Icons.Default.Favorite', 'Icons.Default.RequestQuote')

    # Remove legacy Favorite screen precedence if somehow toggled by stale state.
    text = text.replace('                    favorites -> FavoritesV100(', '                    false && favorites -> FavoritesV100(')

    if 'Icons.Default.Favorite' in text or 'Icons.Default.FavoriteBorder' in text:
        raise RuntimeError('A heart icon still exists in V100Screens.kt')
    if 'MenuRow(Icons.Default.RequestQuote,"Cerere de ofertă",onFavorites)' not in text:
        raise RuntimeError('RFQ drawer entry is missing')
    if 'RfqHeaderActionV133' not in text:
        raise RuntimeError('RFQ header action is missing')

    V100.write_text(text)


def patch_v114() -> None:
    text = V114.read_text()
    text = replace_required(
        text,
        'IconButton(onClick=onFavorites){Icon(Icons.Default.FavoriteBorder,"Favorite",tint=C114Ink)}',
        'RfqHeaderActionV133(onFavorites,C114Ink)',
        "commerce/account RFQ header",
    )
    text = text.replace(
        'Comenzi, favorite și suport într-un singur loc.',
        'Comenzi, cereri de ofertă și suport într-un singur loc.',
    )
    text = text.replace('Icons.Default.FavoriteBorder', 'Icons.Default.RequestQuote')
    text = text.replace('Icons.Default.Favorite', 'Icons.Default.RequestQuote')
    if 'Icons.Default.Favorite' in text or 'Icons.Default.FavoriteBorder' in text:
        raise RuntimeError('A heart icon still exists in V114CommerceUx.kt')
    V114.write_text(text)


def patch_gradle() -> None:
    text = GRADLE.read_text()
    text = replace_required(text, 'versionCode = 13300', 'versionCode = 13301', 'RC5 version code')
    GRADLE.write_text(text)


def main() -> None:
    shutil.copyfile(ASSET, APP / 'RfqHeaderV133.kt')
    patch_v100()
    patch_v114()
    patch_gradle()
    print('Applied Android v1.0.30 RC5: Favorites removed, RFQ header badge enabled')


if __name__ == '__main__':
    main()
