#!/usr/bin/env python3
from pathlib import Path

p=Path('android-v0.1/app/src/main/java/ro/autoid/app/V114CommerceUx.kt')
s=p.read_text()

# RC8 was intentionally written in semantic names; map only its save block to
# the actual compact field names used by the stable generated checkout.
replacements={
    'color=C114Orange':'color=AutoIdOrange',
    'firstName=bFirst':'firstName=billingFirst',
    'lastName=bLast':'lastName=billingLast',
    'address1=bAddress1':'address1=billingA1',
    'address2=bAddress2':'address2=billingA2',
    'city=bCity':'city=billingCity',
    'state=bState':'state=billingState',
    'postcode=bPostcode':'postcode=billingPost',
    'country=bCountry':'country=billingCountry',
    'bFirst=saved.billing.firstName':'bf=saved.billing.firstName',
    'bLast=saved.billing.lastName':'bl=saved.billing.lastName',
    'bAddress1=saved.billing.address1':'ba1=saved.billing.address1',
    'bAddress2=saved.billing.address2':'ba2=saved.billing.address2',
    'bCity=saved.billing.city':'bcity=saved.billing.city',
    'bState=saved.billing.state':'bstate=saved.billing.state',
    'bPostcode=saved.billing.postcode':'bpost=saved.billing.postcode',
    'bCountry=saved.billing.country':'bcountry=saved.billing.country',
    'sFirst=saved.shipping.firstName':'sf=saved.shipping.firstName',
    'sLast=saved.shipping.lastName':'sl=saved.shipping.lastName',
    'sAddress1=saved.shipping.address1':'sa1=saved.shipping.address1',
    'sAddress2=saved.shipping.address2':'sa2=saved.shipping.address2',
    'sCity=saved.shipping.city':'scity=saved.shipping.city',
    'sState=saved.shipping.state':'sstate=saved.shipping.state',
    'sPostcode=saved.shipping.postcode':'spost=saved.shipping.postcode',
    'sCountry=saved.shipping.country':'scountry=saved.shipping.country',
}
for old,new in replacements.items():
    s=s.replace(old,new)

# The prefix replacement above must not rename the existing soft-orange token.
s=s.replace('AutoIdOrangeSoft','C114OrangeSoft')
# RC8 success state uses the established success color token.
s=s.replace('C114Green','C114Good')

# Shipping always remains the shipping address. sameBilling affects the billing
# address derivation, not which address is stored as shipping in WooCommerce.
semantic='val shippingSave=if(sameBilling)billingSave.copy(company="") else AccountAddress(firstName=sFirst,lastName=sLast,address1=sAddress1,address2=sAddress2,city=sCity,state=sState,postcode=sPostcode,country=sCountry)'
mapped='val shippingSave=if(sameBilling)billingSave.copy(company="") else AccountAddress(firstName=sf,lastName=sl,address1=sa1,address2=sa2,city=scity,state=sstate,postcode=spost,country=scountry)'
new='val shippingSave=AccountAddress(firstName=sf,lastName=sl,address1=sa1,address2=sa2,city=scity,state=sstate,postcode=spost,country=scountry)'
if semantic in s:s=s.replace(semantic,new,1)
elif mapped in s:s=s.replace(mapped,new,1)

# Validate only the generated CheckoutV114 block; other legacy components may
# legitimately use similarly named constants.
i=s.find('fun CheckoutV114')
if i<0:raise SystemExit('RC8 checkout function missing after patch')
j=s.find('\n@Composable',i+10)
checkout=s[i:j if j>0 else len(s)]
for bad in ['bFirst','bLast','bAddress1','bAddress2','bCity','bState','bPostcode','bCountry','sFirst','sLast','sAddress1','sAddress2','sCity','sState','sPostcode','sCountry','AutoIdOrangeSoft','C114Green']:
    if bad in checkout:
        raise SystemExit('RC8 checkout semantic placeholder remains: '+bad)
for required in ['api.saveAccountAddresses','firstName=billingFirst','firstName=sf','bf=saved.billing.firstName','sf=saved.shipping.firstName','Salvează adresele','C114Good']:
    if required not in checkout:
        raise SystemExit('RC8 checkout final contract missing: '+required)

p.write_text(s)
print('RC8 checkout save mapped to stable generated field names and color tokens')
print('--- RC8 generated V114 lines 285-305 ---')
for n,line in enumerate(s.splitlines(),1):
    if 285 <= n <= 305:
        print(f'{n:04d}: {line}')
print('--- end RC8 generated V114 diagnostics ---')
