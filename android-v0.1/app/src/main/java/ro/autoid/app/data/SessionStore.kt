package ro.autoid.app.data

import android.content.Context

class SessionStore(context: Context) {
    private val prefs=context.getSharedPreferences("autoid_session",Context.MODE_PRIVATE)
    var accessToken:String? get()=prefs.getString("access_token",null); set(v){prefs.edit().putString("access_token",v).apply()}
    var refreshToken:String? get()=prefs.getString("refresh_token",null); set(v){prefs.edit().putString("refresh_token",v).apply()}
    var customerEmail:String get()=prefs.getString("customer_email","")?:""; set(v){prefs.edit().putString("customer_email",v).apply()}
    fun saveLogin(r:LoginResult){ accessToken=r.accessToken; refreshToken=r.refreshToken; r.customer?.let{customerEmail=it.email} }
    fun clear(){prefs.edit().clear().apply()}
}
