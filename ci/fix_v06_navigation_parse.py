from pathlib import Path

p = Path('android-v0.1/app/src/main/java/ro/autoid/app/data/AutoIdApi.kt')
s = p.read_text()
old = '''        fun parse(a:JSONArray):List<NavItem>=(0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{o->NavItem(o.optLong("id"),o.optLong("parent"),html(o.optString("title")),o.optString("url"),parse(o.optJSONArray("children")?:JSONArray()))}}
'''
new = '''        fun parse(a: JSONArray): List<NavItem> {
            val out = mutableListOf<NavItem>()
            for (i in 0 until a.length()) {
                val o = a.optJSONObject(i) ?: continue
                out += NavItem(
                    id = o.optLong("id"),
                    parent = o.optLong("parent"),
                    title = html(o.optString("title")),
                    url = o.optString("url"),
                    children = parse(o.optJSONArray("children") ?: JSONArray())
                )
            }
            return out
        }
'''
if old not in s:
    raise RuntimeError('v0.6 navigation parser pattern missing')
p.write_text(s.replace(old, new, 1))
print('v0.6 navigation parser fixed')
