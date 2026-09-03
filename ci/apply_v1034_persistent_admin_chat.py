#!/usr/bin/env python3
"""AutoID Android v1.0.30 RC6 / WordPress 1.1.26: persistent chat + human takeover."""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'android-v0.1/app/src/main/java/ro/autoid/app'
API = APP / 'data/AutoIdApi.kt'
V100 = APP / 'V100Screens.kt'
CHAT = APP / 'V129NativeChat.kt'
PLUGIN = ROOT / 'wordpress/autoid-mobile-commerce/autoid-mobile-commerce.php'
GRADLE = ROOT / 'android-v0.1/app/build.gradle.kts'
ASSET = ROOT / 'ci/v134/V134PersistentChat.kt'
PHP_HELPERS = ROOT / 'ci/v134/autoid_chat_persistence_v134.php.inc'


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected exactly one match, found {count}')
    return text.replace(old, new, 1)


def patch_plugin() -> None:
    text = PLUGIN.read_text()
    text = once(text, ' * Version: 1.1.25', ' * Version: 1.1.26', 'plugin version')
    text = once(text, "            'version'=>'1.1.25',", "            'version'=>'1.1.26',", 'health version')
    text = text.replace('AutoID-Mobile-WordPress/1.1.25', 'AutoID-Mobile-WordPress/1.1.26')

    boot_anchor = "        add_action('updated_post_meta',[__CLASS__,'rfq_meta_changed_v130'],40,4);"
    boot_patch = boot_anchor + "\n        add_action('init',[__CLASS__,'chat_register_post_type_v134']);\n        add_action('admin_menu',[__CLASS__,'chat_admin_menu_v134'],60);\n        add_action('admin_post_autoid_mobile_chat_action',[__CLASS__,'chat_admin_action_v134']);"
    text = once(text, boot_anchor, boot_patch, 'chat admin hooks')

    route_anchor = "        register_rest_route(self::NS, '/ai/token', $public + ['methods'=>'POST','callback'=>[__CLASS__,'ai_token_v129']]);"
    route_patch = route_anchor + "\n        register_rest_route(self::NS, '/ai/history', $public + ['methods'=>'GET','callback'=>[__CLASS__,'ai_history_v134']]);"
    text = once(text, route_anchor, route_patch, 'chat history route')

    helper_marker = '    private static function support_center_app_chat_v132($message,$product_id,$device_id,$context) {'
    helpers = PHP_HELPERS.read_text().rstrip() + '\n\n'
    text = once(text, helper_marker, helpers + helper_marker, 'persistent chat helpers')

    product_anchor = "        $product_id=absint($r->get_param('product_id'));\n        $context=["
    product_patch = """        $product_id=absint($r->get_param('product_id'));
        $thread_id=self::chat_thread_v134($device_id,$product_id,true);
        if($thread_id<=0) return new WP_Error('autoid_chat_thread_error','Conversația nu a putut fi inițializată.',['status'=>500]);
        $mode=self::chat_mode_v134($thread_id);
        if($mode==='closed') {
            self::chat_set_mode_v134($thread_id,'ai');
            self::chat_append_v134($thread_id,'system','Conversația a fost redeschisă de client.');
            $mode='ai';
        }
        self::chat_append_v134($thread_id,'user',$message);
        if($mode==='human') {
            return rest_ensure_response([
                'answer'=>'',
                'source'=>'autoid-human-support',
                'thread_id'=>$thread_id,
                'mode'=>'human',
                'human_mode'=>true,
                'pending'=>true,
            ]);
        }
        $context=["""
    text = once(text, product_anchor, product_patch, 'thread initialization')

    old_initial = "        if($answer!=='') return rest_ensure_response(['answer'=>$answer,'source'=>'autoid-support-api','support_center'=>$context['support_center']]);"
    new_initial = "        if($answer!=='') { self::chat_append_v134($thread_id,'ai',$answer); return rest_ensure_response(['answer'=>$answer,'source'=>'autoid-support-api','thread_id'=>$thread_id,'mode'=>'ai','pending'=>false,'support_center'=>$context['support_center']]); }"
    text = once(text, old_initial, new_initial, 'persist legacy app answer')

    old_official = """        if(is_array($official) && trim((string)($official['answer']??''))!=='') {
            return rest_ensure_response([
                'answer'=>trim((string)$official['answer']),
                'source'=>'autoid-support-app-api',"""
    new_official = """        if(is_array($official) && trim((string)($official['answer']??''))!=='') {
            $official_answer=trim((string)$official['answer']);
            self::chat_append_v134($thread_id,'ai',$official_answer);
            return rest_ensure_response([
                'answer'=>$official_answer,
                'thread_id'=>$thread_id,
                'mode'=>'ai',
                'pending'=>false,
                'source'=>'autoid-support-app-api',"""
    text = once(text, old_official, new_official, 'persist official answer')

    old_v2 = """        if(is_array($support_v2) && trim((string)($support_v2['answer']??''))!=='') {
            return rest_ensure_response([
                'answer'=>trim((string)$support_v2['answer']),"""
    new_v2 = """        if(is_array($support_v2) && trim((string)($support_v2['answer']??''))!=='') {
            $support_v2_answer=trim((string)$support_v2['answer']);
            self::chat_append_v134($thread_id,'ai',$support_v2_answer);
            return rest_ensure_response([
                'answer'=>$support_v2_answer,
                'thread_id'=>$thread_id,
                'mode'=>'ai',
                'pending'=>false,"""
    text = once(text, old_v2, new_v2, 'persist v2 answer')

    old_history = """        $state_key='autoid_sc_app_'.md5(hash('sha256',(string)$device_id));
        $state=get_transient($state_key);
        if(!is_array($state)) $state=[];
        $history=is_array($state['history']??null)?$state['history']:[];
        $history=array_slice($history,-12);"""
    new_history = """        $state_key='autoid_sc_app_'.md5(hash('sha256',(string)$device_id));
        $state=get_transient($state_key);
        if(!is_array($state)) $state=[];
        $persistent_thread_id=self::chat_thread_v134($device_id,$product_id,true);
        $history=$persistent_thread_id>0?self::chat_ai_history_v134($persistent_thread_id,12):[];
        if(!$history) $history=array_slice(is_array($state['history']??null)?$state['history']:[],-12);"""
    text = once(text, old_history, new_history, 'persistent AI history source')

    for required in [
        "'/ai/history'",
        'chat_register_post_type_v134',
        'chat_admin_menu_v134',
        'chat_admin_action_v134',
        'autoid_chat_thread',
        "'human_mode'=>true",
        'chat_ai_history_v134',
    ]:
        if required not in text:
            raise RuntimeError(f'Missing chat persistence contract: {required}')

    PLUGIN.write_text(text)


def patch_api() -> None:
    text = API.read_text()
    class_anchor = "data class ChatSessionV129(val token:String,val expiresAt:Long)\nclass AutoIdHttpExceptionV129(val status:Int,message:String):RuntimeException(message)"
    class_patch = class_anchor + "\ndata class ChatHistoryV134(val mode:String,val messages:List<AiMessage>)\ndata class ChatReplyV134(val answer:String,val mode:String,val pending:Boolean)"
    text = once(text, class_anchor, class_patch, 'chat API models')

    api_anchor = '    fun aiChatV129(message:String,productId:Long?,deviceId:String,chatToken:String):String{val b=JSONObject().put("message",message).put("device_id",deviceId);productId?.let{b.put("product_id",it)};return html(JSONObject(post("$MOBILE/ai/chat?device_id=${enc(deviceId)}",b.toString(),chatToken)).optString("answer")).ifBlank{error("Asistentul AutoID nu a returnat răspuns.")}}'
    api_patch = api_anchor + '''\n    fun aiHistoryV134(deviceId:String,chatToken:String):ChatHistoryV134{val o=JSONObject(get("$MOBILE/ai/history?device_id=${enc(deviceId)}",chatToken));val a=o.optJSONArray("messages")?:JSONArray();val messages=(0 until a.length()).mapNotNull{i->a.optJSONObject(i)?.let{m->val role=m.optString("role");val content=html(m.optString("content"));if(content.isBlank())null else AiMessage(role=="user",content)}};return ChatHistoryV134(o.optString("mode","ai"),messages)}\n    fun aiChatV134(message:String,productId:Long?,deviceId:String,chatToken:String):ChatReplyV134{val b=JSONObject().put("message",message).put("device_id",deviceId);productId?.let{b.put("product_id",it)};val o=JSONObject(post("$MOBILE/ai/chat?device_id=${enc(deviceId)}",b.toString(),chatToken));return ChatReplyV134(html(o.optString("answer")),o.optString("mode","ai"),o.optBoolean("pending",false))}'''
    text = once(text, api_anchor, api_patch, 'chat history API methods')
    API.write_text(text)


def patch_android() -> None:
    shutil.copyfile(ASSET, CHAT)
    text = V100.read_text()
    text = text.replace('NativeAiChatScreen(api, null)', 'PersistentAiChatScreenV134(api, null)')
    if 'PersistentAiChatScreenV134(api, null)' not in text:
        raise RuntimeError('Persistent chat screen call missing')
    V100.write_text(text)

    gradle = GRADLE.read_text()
    gradle = once(gradle, 'versionCode = 13301', 'versionCode = 13302', 'RC6 version code')
    GRADLE.write_text(gradle)


def main() -> None:
    patch_plugin()
    patch_api()
    patch_android()
    print('Applied RC6 / WordPress 1.1.26 persistent chat history + admin takeover')


if __name__ == '__main__':
    main()
