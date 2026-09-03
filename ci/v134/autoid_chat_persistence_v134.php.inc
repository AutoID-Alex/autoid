    public static function chat_register_post_type_v134() {
        register_post_type('autoid_chat_thread',[
            'labels'=>['name'=>'AutoID Chat','singular_name'=>'Conversație AutoID'],
            'public'=>false,
            'show_ui'=>false,
            'show_in_menu'=>false,
            'exclude_from_search'=>true,
            'supports'=>['title'],
            'capability_type'=>'post',
            'map_meta_cap'=>true,
        ]);
    }

    public static function ai_history_v134(WP_REST_Request $r) {
        $device_id=self::chat_device_id_v129($r);
        if(is_wp_error($device_id)) return $device_id;
        $authorized=self::verify_chat_token_v129($r,$device_id);
        if(is_wp_error($authorized)) return $authorized;

        $thread_id=self::chat_thread_v134($device_id,0,false);
        if($thread_id<=0) {
            return rest_ensure_response([
                'thread_id'=>0,
                'mode'=>'ai',
                'human_mode'=>false,
                'messages'=>[],
            ]);
        }
        $mode=self::chat_mode_v134($thread_id);
        return rest_ensure_response([
            'thread_id'=>$thread_id,
            'mode'=>$mode,
            'human_mode'=>$mode==='human',
            'messages'=>self::chat_public_history_v134($thread_id,200),
        ]);
    }

    private static function chat_thread_v134($device_id,$product_id=0,$create=true) {
        $hash=hash('sha256',(string)$device_id);
        $ids=get_posts([
            'post_type'=>'autoid_chat_thread',
            'post_status'=>'private',
            'posts_per_page'=>1,
            'fields'=>'ids',
            'meta_key'=>'_autoid_chat_device_hash',
            'meta_value'=>$hash,
            'orderby'=>'ID',
            'order'=>'DESC',
            'suppress_filters'=>true,
        ]);
        $thread_id=!empty($ids)?absint($ids[0]):0;
        if($thread_id<=0 && $create) {
            $thread_id=wp_insert_post([
                'post_type'=>'autoid_chat_thread',
                'post_status'=>'private',
                'post_title'=>'AutoID Mobile Chat',
            ],true);
            if(is_wp_error($thread_id)) return 0;
            $thread_id=absint($thread_id);
            update_post_meta($thread_id,'_autoid_chat_device_hash',$hash);
            update_post_meta($thread_id,'_autoid_chat_device_short',substr($hash,0,12));
            update_post_meta($thread_id,'_autoid_chat_mode','ai');
            update_post_meta($thread_id,'_autoid_chat_created_at',current_time('mysql',true));
            wp_update_post(['ID'=>$thread_id,'post_title'=>'Chat #'.$thread_id.' · '.substr($hash,0,8)]);
        }
        if($thread_id>0 && absint($product_id)>0) update_post_meta($thread_id,'_autoid_chat_product_id',absint($product_id));
        return $thread_id;
    }

    private static function chat_mode_v134($thread_id) {
        $mode=sanitize_key((string)get_post_meta(absint($thread_id),'_autoid_chat_mode',true));
        return in_array($mode,['ai','human','closed'],true)?$mode:'ai';
    }

    private static function chat_set_mode_v134($thread_id,$mode,$admin_id=0) {
        $thread_id=absint($thread_id);
        $mode=sanitize_key((string)$mode);
        if($thread_id<=0 || !in_array($mode,['ai','human','closed'],true)) return false;
        update_post_meta($thread_id,'_autoid_chat_mode',$mode);
        if($admin_id>0) update_post_meta($thread_id,'_autoid_chat_admin_user_id',absint($admin_id));
        self::chat_touch_v134($thread_id);
        return true;
    }

    private static function chat_touch_v134($thread_id) {
        global $wpdb;
        $thread_id=absint($thread_id);
        if($thread_id<=0) return;
        $wpdb->update($wpdb->posts,[
            'post_modified'=>current_time('mysql'),
            'post_modified_gmt'=>current_time('mysql',true),
        ],['ID'=>$thread_id]);
        clean_post_cache($thread_id);
    }

    private static function chat_append_v134($thread_id,$role,$content,$actor_id=0) {
        $thread_id=absint($thread_id);
        $role=sanitize_key((string)$role);
        $content=trim(wp_strip_all_tags((string)$content));
        if($thread_id<=0 || $content==='') return 0;
        if(!in_array($role,['user','ai','admin','system'],true)) $role='system';
        $author=$role==='user'?'Client AutoID':($role==='admin'?'Consultant AutoID':($role==='ai'?'AutoID AI':'AutoID'));
        $comment_id=wp_insert_comment([
            'comment_post_ID'=>$thread_id,
            'comment_content'=>$content,
            'comment_type'=>'autoid_mobile_chat',
            'comment_approved'=>1,
            'comment_author'=>$author,
            'user_id'=>$role==='admin'?absint($actor_id):0,
            'comment_date'=>current_time('mysql'),
            'comment_date_gmt'=>current_time('mysql',true),
        ]);
        if($comment_id) {
            add_comment_meta($comment_id,'_autoid_chat_role',$role,true);
            update_post_meta($thread_id,'_autoid_chat_last_role',$role);
            update_post_meta($thread_id,'_autoid_chat_last_message_at',current_time('mysql',true));
            self::chat_touch_v134($thread_id);
        }
        return absint($comment_id);
    }

    private static function chat_comments_v134($thread_id,$limit=200) {
        return get_comments([
            'post_id'=>absint($thread_id),
            'status'=>'approve',
            'type'=>'autoid_mobile_chat',
            'orderby'=>'comment_ID',
            'order'=>'ASC',
            'number'=>max(1,min(500,absint($limit))),
        ]);
    }

    private static function chat_public_history_v134($thread_id,$limit=200) {
        $out=[];
        foreach(self::chat_comments_v134($thread_id,$limit) as $comment) {
            $role=sanitize_key((string)get_comment_meta($comment->comment_ID,'_autoid_chat_role',true));
            if(!in_array($role,['user','ai','admin','system'],true)) $role='system';
            $out[]=[
                'id'=>absint($comment->comment_ID),
                'role'=>$role,
                'content'=>(string)$comment->comment_content,
                'created_at'=>mysql2date('c',$comment->comment_date_gmt?:$comment->comment_date,false),
            ];
        }
        return $out;
    }

    private static function chat_ai_history_v134($thread_id,$limit=12) {
        $messages=self::chat_public_history_v134($thread_id,max(12,$limit*2));
        $out=[];
        foreach($messages as $row) {
            $role=(string)($row['role']??'');
            if($role==='user') $mapped='user';
            elseif($role==='ai' || $role==='admin') $mapped='assistant';
            else continue;
            $out[]=['role'=>$mapped,'content'=>(string)($row['content']??'')];
        }
        return array_slice($out,-absint($limit));
    }

    public static function chat_admin_menu_v134() {
        add_menu_page(
            'AutoID Chat',
            'AutoID Chat',
            'manage_woocommerce',
            'autoid-mobile-chat',
            [__CLASS__,'chat_admin_page_v134'],
            'dashicons-format-chat',
            56
        );
    }

    private static function chat_admin_capable_v134() {
        return current_user_can('manage_woocommerce') || current_user_can('manage_options');
    }

    public static function chat_admin_action_v134() {
        if(!self::chat_admin_capable_v134()) wp_die('Acces interzis.');
        check_admin_referer('autoid_mobile_chat_v134');
        $thread_id=absint($_POST['thread_id']??0);
        if($thread_id<=0 || get_post_type($thread_id)!=='autoid_chat_thread') wp_die('Conversație invalidă.');
        $action_type=sanitize_key((string)($_POST['action_type']??''));
        $admin_id=get_current_user_id();

        if($action_type==='takeover') {
            self::chat_set_mode_v134($thread_id,'human',$admin_id);
            self::chat_append_v134($thread_id,'system','Conversația a fost preluată de un consultant AutoID.',$admin_id);
        } elseif($action_type==='return_ai') {
            self::chat_set_mode_v134($thread_id,'ai',$admin_id);
            self::chat_append_v134($thread_id,'system','Conversația a fost predată asistentului AutoID AI.',$admin_id);
        } elseif($action_type==='close') {
            self::chat_set_mode_v134($thread_id,'closed',$admin_id);
            self::chat_append_v134($thread_id,'system','Conversația a fost închisă de consultantul AutoID.',$admin_id);
        } elseif($action_type==='reply') {
            $message=trim(sanitize_textarea_field((string)($_POST['message']??'')));
            if($message!=='') {
                self::chat_set_mode_v134($thread_id,'human',$admin_id);
                self::chat_append_v134($thread_id,'admin',$message,$admin_id);
            }
        }
        wp_safe_redirect(admin_url('admin.php?page=autoid-mobile-chat&thread='.$thread_id));
        exit;
    }

    public static function chat_admin_page_v134() {
        if(!self::chat_admin_capable_v134()) wp_die('Acces interzis.');
        $thread_id=absint($_GET['thread']??0);
        echo '<div class="wrap"><h1>AutoID Chat</h1>';
        echo '<style>.autoid-chat-grid{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:18px}.autoid-chat-box{background:#fff;border:1px solid #dcdcde;border-radius:10px;padding:16px}.autoid-chat-msg{max-width:760px;padding:10px 12px;margin:8px 0;border-radius:12px;background:#f6f7f7}.autoid-chat-msg.user{margin-left:auto;background:#fff1e8}.autoid-chat-msg.admin{background:#eaf4ff}.autoid-chat-msg.ai{background:#f4f4f5}.autoid-chat-msg.system{background:#fff8e5;font-size:12px}.autoid-chat-meta{font-size:11px;color:#646970;margin-bottom:4px}.autoid-chat-status{display:inline-block;padding:4px 8px;border-radius:999px;background:#f0f0f1;font-weight:600}.autoid-chat-list td{vertical-align:top}</style>';
        if($thread_id>0 && get_post_type($thread_id)==='autoid_chat_thread') self::chat_admin_thread_v134($thread_id);
        else self::chat_admin_list_v134();
        echo '</div>';
    }

    private static function chat_admin_list_v134() {
        $threads=get_posts([
            'post_type'=>'autoid_chat_thread',
            'post_status'=>'private',
            'posts_per_page'=>100,
            'orderby'=>'modified',
            'order'=>'DESC',
        ]);
        echo '<p>Conversațiile din aplicația AutoID. Deschide un thread pentru a-l prelua și a răspunde ca operator.</p>';
        echo '<table class="widefat striped autoid-chat-list"><thead><tr><th>Thread</th><th>Status</th><th>Ultimul mesaj</th><th>Actualizat</th></tr></thead><tbody>';
        if(!$threads) echo '<tr><td colspan="4">Nu există conversații încă.</td></tr>';
        foreach($threads as $thread) {
            $mode=self::chat_mode_v134($thread->ID);
            $comments=self::chat_comments_v134($thread->ID,1);
            $last='';
            if($comments) {
                $all=self::chat_public_history_v134($thread->ID,200);
                $row=$all?end($all):[];
                $last=wp_trim_words((string)($row['content']??''),16,'…');
            }
            $url=admin_url('admin.php?page=autoid-mobile-chat&thread='.$thread->ID);
            echo '<tr><td><a href="'.esc_url($url).'"><strong>#'.absint($thread->ID).'</strong></a><br><small>'.esc_html((string)get_post_meta($thread->ID,'_autoid_chat_device_short',true)).'</small></td>';
            echo '<td><span class="autoid-chat-status">'.esc_html($mode).'</span></td>';
            echo '<td>'.esc_html($last).'</td>';
            echo '<td>'.esc_html(get_date_from_gmt($thread->post_modified_gmt,'Y-m-d H:i:s')).'</td></tr>';
        }
        echo '</tbody></table>';
    }

    private static function chat_admin_thread_v134($thread_id) {
        $mode=self::chat_mode_v134($thread_id);
        $messages=self::chat_public_history_v134($thread_id,300);
        $product_id=absint(get_post_meta($thread_id,'_autoid_chat_product_id',true));
        echo '<p><a href="'.esc_url(admin_url('admin.php?page=autoid-mobile-chat')).'">← Toate conversațiile</a></p>';
        echo '<div class="autoid-chat-grid"><div class="autoid-chat-box"><h2>Conversația #'.absint($thread_id).'</h2>';
        echo '<p>Status: <span class="autoid-chat-status">'.esc_html($mode).'</span>'.($product_id?' · Produs #'.absint($product_id):'').'</p>';
        if(!$messages) echo '<p>Nu există mesaje.</p>';
        foreach($messages as $row) {
            $role=sanitize_html_class((string)($row['role']??'system'));
            $label=$role==='user'?'Client':($role==='admin'?'Consultant AutoID':($role==='ai'?'AutoID AI':'Sistem'));
            echo '<div class="autoid-chat-msg '.$role.'"><div class="autoid-chat-meta">'.esc_html($label).' · '.esc_html((string)($row['created_at']??'')).'</div>'.nl2br(esc_html((string)($row['content']??''))).'</div>';
        }
        echo '</div><div class="autoid-chat-box"><h2>Intervenție operator</h2>';
        self::chat_admin_button_v134($thread_id,'takeover','Preia conversația','button button-primary');
        echo ' ';
        self::chat_admin_button_v134($thread_id,'return_ai','Predă AI-ului','button');
        echo ' ';
        self::chat_admin_button_v134($thread_id,'close','Închide conversația','button');
        echo '<hr><form method="post" action="'.esc_url(admin_url('admin-post.php')).'">';
        echo '<input type="hidden" name="action" value="autoid_mobile_chat_action"><input type="hidden" name="action_type" value="reply"><input type="hidden" name="thread_id" value="'.absint($thread_id).'">';
        wp_nonce_field('autoid_mobile_chat_v134');
        echo '<p><label for="autoid-chat-reply"><strong>Răspuns consultant</strong></label></p><textarea id="autoid-chat-reply" name="message" rows="8" style="width:100%" required></textarea>';
        echo '<p><button class="button button-primary button-large" type="submit">Trimite în aplicație</button></p></form>';
        echo '<p><small>Un răspuns manual mută automat threadul în modul <strong>human</strong>; AI-ul nu va răspunde până când alegi „Predă AI-ului”.</small></p>';
        echo '</div></div>';
    }

    private static function chat_admin_button_v134($thread_id,$action_type,$label,$class) {
        echo '<form method="post" action="'.esc_url(admin_url('admin-post.php')).'" style="display:inline-block;margin:0 4px 6px 0">';
        echo '<input type="hidden" name="action" value="autoid_mobile_chat_action"><input type="hidden" name="action_type" value="'.esc_attr($action_type).'"><input type="hidden" name="thread_id" value="'.absint($thread_id).'">';
        wp_nonce_field('autoid_mobile_chat_v134');
        echo '<button class="'.esc_attr($class).'" type="submit">'.esc_html($label).'</button></form>';
    }
