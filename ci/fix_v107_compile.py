from pathlib import Path

p = Path('android-v0.1/app/src/main/java/ro/autoid/app/V08Screens.kt')
s = p.read_text()

imports = {
    'import androidx.compose.foundation.shape.CircleShape\n': 'import androidx.compose.foundation.shape.CircleShape\n',
    'import androidx.compose.ui.draw.clip\n': 'import androidx.compose.ui.draw.clip\n',
    'import androidx.compose.ui.layout.ContentScale\n': 'import androidx.compose.ui.layout.ContentScale\n',
}

anchor = 'import androidx.compose.foundation.shape.RoundedCornerShape\n'
if anchor not in s:
    raise SystemExit('RoundedCornerShape import anchor missing')
if 'import androidx.compose.foundation.shape.CircleShape\n' not in s:
    s = s.replace(anchor, anchor + 'import androidx.compose.foundation.shape.CircleShape\n', 1)

anchor = 'import androidx.compose.ui.Modifier\n'
if anchor not in s:
    raise SystemExit('Modifier import anchor missing')
if 'import androidx.compose.ui.draw.clip\n' not in s:
    s = s.replace(anchor, anchor + 'import androidx.compose.ui.draw.clip\n', 1)

# ContentScale normally sits near other androidx.compose.ui imports; add after Modifier block safely.
if 'import androidx.compose.ui.layout.ContentScale\n' not in s:
    clip_anchor = 'import androidx.compose.ui.draw.clip\n'
    s = s.replace(clip_anchor, clip_anchor + 'import androidx.compose.ui.layout.ContentScale\n', 1)

# Ink is private to V100Screens.kt. Keep the same visual value locally in checkout.
s = s.replace('color = Ink', 'color = Color(0xFF101828)')
s = s.replace('color=Ink', 'color=Color(0xFF101828)')
s = s.replace('else Ink', 'else Color(0xFF101828)')

p.write_text(s)
print('Fixed v1.0.7 checkout compile imports and private color reference')
