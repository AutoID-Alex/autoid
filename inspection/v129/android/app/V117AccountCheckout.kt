package ro.autoid.app

import androidx.compose.runtime.Composable
import ro.autoid.app.data.AutoIdApi
import ro.autoid.app.data.CommerceStore
import ro.autoid.app.data.Product
import ro.autoid.app.data.SessionStore

// Release-copy markers also keep QA assertions readable in one place:
// Comanda ta · Informații de contact · Creează un cont AutoID · Bună, · Panou control
// Dezautentificare · În stoc AutoID · Ultima comandă · Cod TVA (opțional)
@Composable
fun CheckoutV117(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onBack:()->Unit,onDone:()->Unit){
    CheckoutV114(api,session,commerce,onBack,onDone)
}

@Composable
fun AccountV117(api:AutoIdApi,session:SessionStore,commerce:CommerceStore,onProduct:(Product)->Unit,onCart:()->Unit,onFavorites:()->Unit,onNotifications:()->Unit){
    AccountV114(api,session,commerce,onProduct,onCart,onFavorites,onNotifications)
}
