#!/usr/bin/env python3
"""AutoID Mobile 1.1.29: claim legacy/guest RFQs by authenticated account email."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLUGIN=ROOT/'wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php'

s=PLUGIN.read_text()

# Store normalized requester email directly for new guest/account RFQs.
# Patch only inside rfq_create_v130 so formatting changes from later generators
# cannot break the release again.
create_start=s.find('    public static function rfq_create_v130(WP_REST_Request $r) {')
if create_start<0:
    raise SystemExit('RFQ create function missing')
create_end=s.find('\n    private static function ',create_start+10)
if create_end<0:
    raise SystemExit('RFQ create function boundary missing')
create_block=s[create_start:create_end]
email_meta="'_autoid_rfq_email'=>strtolower(trim($email))"
if email_meta not in create_block:
    owner_meta="'_autoid_rfq_user_id'=>$uid,"
    if owner_meta not in create_block:
        raise SystemExit('RFQ create user meta anchor missing')
    create_block=create_block.replace(owner_meta,owner_meta+email_meta+',',1)
    s=s[:create_start]+create_block+s[create_end:]

# Add claim helper before the ownership check. Existing RFQs are supported by
# exact comparison against requester[email]; _autoid_rfq_email is only an index.
anchor='''    private static function rfq_owner_v130($rfq_id,$user_id) {\n'''
helper='''    private static function rfq_claim_guest_by_email_v131($user_id,$only_rfq_id=0) {
        $user_id=absint($user_id);$only_rfq_id=absint($only_rfq_id);
        if($user_id<=0||!post_type_exists('autoid_rfq'))return 0;
        $user=get_userdata($user_id);if(!$user||!is_email($user->user_email))return 0;
        $email=strtolower(trim((string)$user->user_email));if($email==='')return 0;

        $args=['post_type'=>'autoid_rfq','post_status'=>['private','publish'],'fields'=>'ids','posts_per_page'=>-1,'no_found_rows'=>true,
            'meta_query'=>['relation'=>'OR',
                ['key'=>'_autoid_rfq_email','value'=>$email,'compare'=>'='],
                ['key'=>'_autoid_rfq_requester','value'=>$email,'compare'=>'LIKE'],
            ]];
        if($only_rfq_id>0)$args['post__in']=[$only_rfq_id];
        $q=new WP_Query($args);$claimed=0;
        foreach((array)$q->posts as $rfq_id){
            $rfq_id=absint($rfq_id);if($rfq_id<=0)continue;
            $stored=absint(get_post_meta($rfq_id,'_autoid_rfq_user_id',true));
            $requester=get_post_meta($rfq_id,'_autoid_rfq_requester',true);if(!is_array($requester))continue;
            $legacy_owner=absint($requester['user_id']??0);
            if($stored>0||$legacy_owner>0)continue;
            $requester_email=strtolower(trim((string)($requester['email']??'')));
            if($requester_email===''||!hash_equals($email,$requester_email))continue;
            $requester['user_id']=$user_id;
            update_post_meta($rfq_id,'_autoid_rfq_user_id',$user_id);
            update_post_meta($rfq_id,'_autoid_rfq_requester',$requester);
            update_post_meta($rfq_id,'_autoid_rfq_email',$email);
            update_post_meta($rfq_id,'_autoid_rfq_claimed_at',current_time('mysql',true));
            update_post_meta($rfq_id,'_autoid_rfq_claim_method','authenticated_email_match');
            $claimed++;
        }
        return $claimed;
    }

'''
if 'private static function rfq_claim_guest_by_email_v131(' not in s:
    if anchor not in s:
        raise SystemExit('RFQ owner anchor missing')
    s=s.replace(anchor,helper+anchor,1)

# Any direct RFQ access can claim one matching guest record after authentication.
old_owner='''    private static function rfq_owner_v130($rfq_id,$user_id) {
        if($rfq_id<=0||$user_id<=0||get_post_type($rfq_id)!=='autoid_rfq')return false;
        $stored=absint(get_post_meta($rfq_id,'_autoid_rfq_user_id',true));
        if($stored>0)return $stored===$user_id;
        $r=get_post_meta($rfq_id,'_autoid_rfq_requester',true);
        return is_array($r)&&absint($r['user_id']??0)===$user_id;
    }'''
new_owner='''    private static function rfq_owner_v130($rfq_id,$user_id) {
        if($rfq_id<=0||$user_id<=0||get_post_type($rfq_id)!=='autoid_rfq')return false;
        $stored=absint(get_post_meta($rfq_id,'_autoid_rfq_user_id',true));
        if($stored>0)return $stored===$user_id;
        $r=get_post_meta($rfq_id,'_autoid_rfq_requester',true);
        $legacy_owner=is_array($r)?absint($r['user_id']??0):0;
        if($legacy_owner>0)return $legacy_owner===$user_id;
        self::rfq_claim_guest_by_email_v131($user_id,$rfq_id);
        $stored=absint(get_post_meta($rfq_id,'_autoid_rfq_user_id',true));
        return $stored===$user_id;
    }'''
if new_owner not in s:
    if old_owner not in s:
        raise SystemExit('RFQ owner function exact anchor missing')
    s=s.replace(old_owner,new_owner,1)

# Claim all matching guest RFQs before the account list query runs.
old_list='''    public static function rfq_list_v130(WP_REST_Request $r) {
        $uid=absint($r->get_param('_autoid_user_id'));$page=max(1,absint($r->get_param('page')));$per=max(1,min(30,absint($r->get_param('per_page'))?:10));'''
new_list='''    public static function rfq_list_v130(WP_REST_Request $r) {
        $uid=absint($r->get_param('_autoid_user_id'));self::rfq_claim_guest_by_email_v131($uid);$page=max(1,absint($r->get_param('page')));$per=max(1,min(30,absint($r->get_param('per_page'))?:10));'''
if new_list not in s:
    if old_list not in s:
        raise SystemExit('RFQ list anchor missing')
    s=s.replace(old_list,new_list,1)

# Distinct backend release.
for oldv,newv in [
    (' * Version: 1.1.28',' * Version: 1.1.29'),
    ("'version'=>'1.1.28',","'version'=>'1.1.29',"),
    ('AutoID-Mobile-WordPress/1.1.28','AutoID-Mobile-WordPress/1.1.29'),
]:
    if oldv in s:s=s.replace(oldv,newv)

for required in [
    'rfq_claim_guest_by_email_v131','_autoid_rfq_email','authenticated_email_match',
    "self::rfq_claim_guest_by_email_v131($uid)",' * Version: 1.1.29'
]:
    if required not in s:raise SystemExit('RFQ guest claim contract missing: '+required)

PLUGIN.write_text(s)
print('AutoID Mobile 1.1.29: guest RFQs are claimed by authenticated account email')
