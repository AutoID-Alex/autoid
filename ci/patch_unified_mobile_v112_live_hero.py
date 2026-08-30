from pathlib import Path

p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()

s=s.replace('Version: 1.1.1','Version: 1.1.2',1)
s=s.replace('final class AutoID_Mobile_111 {','final class AutoID_Mobile_112 {',1)
s=s.replace('AutoID_Mobile_111::boot();','AutoID_Mobile_112::boot();',1)
s=s.replace("'version'=>'1.1.1'", "'version'=>'1.1.2'")

route="        register_rest_route(self::NS, '/home', $public + ['methods'=>'GET','callback'=>[__CLASS__,'home']]);\n"
if route not in s:
    raise SystemExit('home route anchor missing')
hero_route="        register_rest_route(self::NS, '/hero', $public + ['methods'=>'GET','callback'=>[__CLASS__,'hero_live']]);\n"
if hero_route not in s:
    s=s.replace(route,route+hero_route,1)

home_start=s.index('    public static function home(WP_REST_Request $r) {')
home_end=s.index('\n    private static function home_stock_specs()',home_start)
home=s[home_start:home_end]
needle='        return rest_ensure_response([\n'
if needle not in home:
    raise SystemExit('home response anchor missing')
home=home.replace(needle,'        return self::live_response([\n',1)
s=s[:home_start]+home+s[home_end:]

anchor='    private static function native_hero_action_from_url($raw_url) {'
pos=s.index(anchor)
block=r'''    private static function live_response($data) {
        $response=rest_ensure_response($data);
        if($response instanceof WP_REST_Response){
            $response->header('Cache-Control','no-store, no-cache, must-revalidate, max-age=0');
            $response->header('Pragma','no-cache');
            $response->header('Expires','Wed, 11 Jan 1984 05:00:00 GMT');
            $response->header('Surrogate-Control','no-store');
            $response->header('X-AutoID-Live-Config','1');
        }
        return $response;
    }

    public static function hero_live(WP_REST_Request $r) {
        $settings=get_option('autoid_mega_menu_settings',[]);
        $fingerprint=substr(hash('sha256',wp_json_encode($settings)),0,16);
        return self::live_response([
            'hero_slides'=>self::hero_slides_public(),
            'revision'=>$fingerprint,
            'source'=>'autoid-mega-menu-app',
            'generated_at'=>gmdate('c'),
        ]);
    }

'''
s=s[:pos]+block+s[pos:]

save='''            $settings['slides']=$slides;\n            update_option('autoid_mega_menu_settings',$settings,false);\n            echo '<div class="notice notice-success is-dismissible"><p><strong>AutoID Hero App salvat.</strong> Setările website-ului au fost păstrate.</p></div>';'''
replace='''            $settings['slides']=$slides;\n            update_option('autoid_mega_menu_settings',$settings,false);\n            update_option('autoid_mobile_hero_last_saved',time(),false);\n            echo '<div class="notice notice-success is-dismissible"><p><strong>AutoID Hero App salvat.</strong> Configurația este live; aplicația o va reîncărca automat. Setările website-ului au fost păstrate.</p></div>';'''
if save not in s:
    raise SystemExit('Hero Studio save anchor missing')
s=s.replace(save,replace,1)

p.write_text(s)
print('Patched AutoID Mobile v1.1.2: live /hero endpoint, no-cache headers, live Home response')
