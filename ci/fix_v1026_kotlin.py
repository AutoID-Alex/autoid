from pathlib import Path
p=Path('android-v0.1/app/src/main/java/ro/autoid/app/V100Screens.kt')
s=p.read_text()
s=s.replace('''    val homeDisk=remember{HomeDiskCacheV126(LocalContext.current,api)}''','''    val homeContextV126=LocalContext.current
    val homeDisk=remember(homeContextV126,api){HomeDiskCacheV126(homeContextV126,api)}''')
s=s.replace('familyCategory=0}', 'familyCategory=0L}')
s=s.replace('familyCategory==0,', 'familyCategory==0L,')
p.write_text(s)
print('fixed v1.0.26 Compose context and Long category IDs')
