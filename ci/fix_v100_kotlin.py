from pathlib import Path

p=Path('android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt')
s=p.read_text()
start=s.index('@Composable private fun V100Bottom')
end=s.index('@Composable private fun V100Menu', start)
replacement='''@Composable
private fun V100Bottom(tab: V100Tab, count: Int, onTab: (V100Tab) -> Unit) {
    NavigationBar(
        containerColor = Color.White,
        tonalElevation = 10.dp,
        modifier = Modifier.navigationBarsPadding()
    ) {
        V100Tab.entries.forEach { item ->
            NavigationBarItem(
                selected = tab == item,
                onClick = { onTab(item) },
                icon = {
                    if (item == V100Tab.Ai) {
                        Surface(
                            shape = CircleShape,
                            color = AutoIdOrange,
                            shadowElevation = 5.dp,
                            modifier = Modifier.size(48.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(Icons.Default.SmartToy, contentDescription = "AI", tint = Color.White)
                            }
                        }
                    } else {
                        BadgedBox(
                            badge = {
                                if (item == V100Tab.Cart && count > 0) {
                                    Badge(containerColor = AutoIdOrange) { Text(count.toString()) }
                                }
                            }
                        ) {
                            val icon = when (item) {
                                V100Tab.Home -> Icons.Default.Home
                                V100Tab.Categories -> Icons.Default.GridView
                                V100Tab.Cart -> Icons.Default.ShoppingCart
                                V100Tab.Account -> Icons.Default.Person
                                V100Tab.Ai -> Icons.Default.SmartToy
                            }
                            Icon(icon, contentDescription = item.label)
                        }
                    }
                },
                label = { Text(if (item == V100Tab.Ai) "AI" else item.label, fontSize = 10.sp) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = AutoIdOrange,
                    selectedTextColor = AutoIdOrange,
                    indicatorColor = Color(0xFFFFF1E8)
                )
            )
        }
    }
}

'''
s=s[:start]+replacement+s[end:]
p.write_text(s)
print('Fixed V100Bottom Kotlin parser issue')
