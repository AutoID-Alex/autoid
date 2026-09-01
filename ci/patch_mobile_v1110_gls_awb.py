from pathlib import Path
p=Path('wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php')
s=p.read_text()

def must(old,new,label):
    global s
    if old not in s: raise SystemExit(label+' anchor missing')
    s=s.replace(old,new,1)

must('Version: 1.1.9','Version: 1.1.10','plugin version')
must("'bridge_version'=>'1.1.9'","'bridge_version'=>'1.1.10'",'bridge version')
old="""    private static function order_tracking_payload($order) {
        $awb=trim((string)$order->get_meta('AWB_GLS',true));
        if($awb==='')$awb=trim((string)$order->get_meta('_AWB_GLS',true));
        if($awb==='')return ['carrier'=>'','tracking_number'=>'','tracking_url'=>''];
        return ['carrier'=>'GLS','tracking_number'=>$awb,'tracking_url'=>'https://gls-group.eu/RO/ro/urmarire-colet.html?match='.rawurlencode($awb)];
    }
"""
new="""    private static function order_tracking_payload($order) {
        $awb='';
        foreach(['GLS_AWB','_GLS_AWB','AWB_GLS','_AWB_GLS','gls_awb','_gls_awb'] as $key){
            $value=trim((string)$order->get_meta($key,true));
            if($value!==''){$awb=$value;break;}
        }
        if($awb==='')return ['carrier'=>'','tracking_number'=>'','tracking_url'=>''];
        return ['carrier'=>'GLS','tracking_number'=>$awb,'tracking_url'=>'https://gls-group.eu/RO/ro/urmarire-colet.html?match='.rawurlencode($awb)];
    }
"""
must(old,new,'GLS tracking helper')
p.write_text(s)
print('Patched AutoID Mobile v1.1.10: GLS_AWB and AWB_GLS tracking compatibility')
