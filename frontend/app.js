/**
 * RAGMind Web Frontend
 * Main Application Logic
 */

// Configuration
let API_BASE_URL = (localStorage.getItem('ragmind_api_base_url') || 'http://52.188.226.80:8000').replace(/\/+$/, '');

// Translations
const i18n = {
    ar: {
        nav_dashboard: "لوحة التحكم",
        nav_security_center: "Security Center",
        nav_projects: "المشاريع",
        nav_chat: "المحادثة الذكية",
        nav_bot: "إعدادات البوت",
        nav_ai_config: "إعدادات الذكاء الاصطناعي",
        nav_account_settings: "إعدادات الحساب",
        status_online: "متصل",
        stat_projects: "إجمالي المشاريع",
        stat_docs: "المستندات",
        stat_chunks: "القطع النصية",
        security_section_title: "Security Center",
        security_section_overview_title: "Security Overview",
        security_total_events: "Total Events",
        security_login_failures: "Login Failures",
        security_blocked_attacks: "Blocked Attacks",
        security_brute_force_alerts: "Brute Force Alerts",
        security_open_incidents: "الحوادث المفتوحة",
        security_high_severity_incidents: "حوادث شدة عالية",
        security_active_users: "المستخدمون النشطون",
        security_suspended_users: "المستخدمون الموقوفون",
        security_blocked_users: "المستخدمون المحظورون",
        security_user_actions_title: "إجراءات حالة المستخدم",
        security_duration_minutes_label: "مدة الإيقاف (دقيقة)",
        security_suspend_btn: "تعليق",
        security_block_btn: "حظر",
        security_restore_btn: "استعادة",
        security_admin_only_actions: "فقط المشرف يمكنه تنفيذ هذه الإجراءات.",
        security_action_user_id_required: "أدخل معرف مستخدم صالح",
        security_action_reason_required: "السبب مطلوب للتعليق أو الحظر",
        security_action_duration_invalid: "مدة التعليق يجب أن تكون بين 1 و 10080 دقيقة",
        security_action_suspend_success: "تم تعليق المستخدم بنجاح",
        security_action_block_success: "تم حظر المستخدم بنجاح",
        security_action_restore_success: "تمت استعادة المستخدم بنجاح",
        security_events_title: "Security Events Feed",
        security_col_timestamp: "Timestamp",
        security_col_username: "Actor",
        security_col_event_type: "Event Type",
        security_col_severity: "Severity",
        security_col_message: "Message",
        security_events_empty: "No security events yet",
        security_live_feed_title: "Live Feed",
        security_live_feed_empty: "No live events right now",
        security_load_error: "Failed to load security data",
        security_simulate_btn: "Start Attack Simulation",
        security_simulate_running: "Running simulation...",
        security_simulate_success: "Simulation events generated",
        security_simulate_escalation_blocked: "Simulation escalated: user blocked",
        security_simulation_reset_btn: "Reset Simulation View",
        security_simulation_reset_running: "Clearing simulation feed...",
        security_simulation_reset_success: "Simulation feed cleared",
        security_simulation_reset_confirm: "This will clear simulated events from the feed.\nIncidents and system metrics will NOT be affected.\nContinue?",
        security_access_denied: "غير مسموح: Security Center متاح فقط لـ Cybersecurity Engineer",
        security_tab_events: "سجل الأحداث",
        security_tab_incidents: "Incidents",
        security_incidents_title: "Incidents",
        incident_col_id: "Incident ID",
        incident_col_type: "Type",
        incident_col_severity: "Severity",
        incident_col_status: "Status",
        incident_col_created_at: "Created At",
        incident_col_false_positive: "False Positive",
        incident_empty: "No incidents yet",
        incident_filter_all_status: "All Status",
        incident_filter_all_severity: "All Severity",
        incident_filter_false_positive: "False Positive",
        incident_filter_fp_all: "All",
        incident_filter_fp_true: "True",
        incident_filter_fp_false: "False",
        incident_refresh_btn: "Refresh",
        incident_refresh_success: "تم تحديث الحوادث",
        incident_back_to_events_btn: "الرجوع إلى سجل الأحداث",
        incident_details_title: "Incident Details",
        incident_label_id: "Incident ID",
        incident_label_type: "Type",
        incident_label_severity: "Severity",
        incident_label_status: "Status",
        incident_label_created_at: "Created At",
        incident_label_false_positive: "False Positive",
        incident_actor_title: "Actor Info",
        incident_notes_title: "Investigation Notes",
        incident_notes_placeholder: "Add investigation details, evidence, and conclusions...",
        incident_notes_save_btn: "Save Notes",
        incident_actions_title: "Actions",
        incident_action_reason_label: "سبب الإجراء",
        incident_action_suspend_minutes_label: "مدة الإيقاف (دقيقة)",
        incident_action_reason_required: "السبب مطلوب لتنفيذ هذا الإجراء",
        incident_action_suspend_minutes_invalid: "مدة الإيقاف يجب أن تكون بين 1 و 10080 دقيقة",
        incident_assign_btn: "Assign to me",
        incident_mark_investigating_btn: "Mark as Investigating",
        incident_resolve_btn: "Resolve",
        incident_close_btn: "Close",
        incident_mark_false_positive_btn: "Mark False Positive",
        incident_clear_false_positive_btn: "Clear False Positive",
        incident_block_user_btn: "Block User",
        incident_suspend_user_btn: "Suspend User",
        incident_reactivate_user_btn: "إعادة تفعيل المستخدم",
        incident_ignore_btn: "Ignore (false positive)",
        incident_timeline_title: "Timeline",
        incident_timeline_empty: "No logs yet",
        incident_timeline_timestamp: "Timestamp",
        incident_timeline_action: "Action",
        incident_timeline_result: "Result",
        incident_timeline_metadata: "Metadata",
        incident_result_success: "Success",
        incident_result_failed: "Failed",
        incident_select_first: "اختر incident أولًا",
        incident_load_error: "Failed to load incidents",
        incident_action_assign_success: "Incident assigned to you",
        incident_action_status_success: "Incident status updated",
        incident_action_apply_success: "Incident action applied",
        incident_action_reactivate_success: "تمت إعادة تفعيل المستخدم",
        incident_notes_saved: "Incident notes updated",
        incident_false_positive_marked: "Incident marked as false positive",
        incident_false_positive_cleared: "False-positive flag cleared",
        incident_new_alert_single: "تم اكتشاف حادثة جديدة",
        incident_new_alert_multiple: "حوادث جديدة تم اكتشافها",
        incident_actor_unknown: "Unknown",
        incident_actor_label: "Actor",
        incident_assigned_label: "Assigned",
        incident_created_by_label: "Created by",
        incident_false_positive_label: "False Positive",
        incident_false_positive_yes: "Yes",
        incident_false_positive_no: "No",
        incident_status_open: "OPEN",
        incident_status_investigating: "INVESTIGATING",
        incident_status_resolved: "RESOLVED",
        incident_status_closed: "CLOSED",
        recent_projects: "المشاريع الأخيرة",
        view_all: "عرض الكل",
        your_projects: "مشاريعك",
        welcome_title: "مرحباً بك في RAGMind",
        project_name_ph: "مثلاً: أبحاث الذكاء الاصطناعي",
        project_desc_ph: "وصف مختصر للمشروع...",
        create_project_btn: "إنشاء المشروع",
        upload_title: "رفع مستندات جديدة",
        upload_desc: "اسحب الملفات هنا أو اضغط للاختيار",
        docs_title: "المستندات الحالية",
        bot_settings_title: "إعدادات بوت التليجرام",
        bot_active_project: "المشروع النشط",
        bot_active_project_desc: "اختر المشروع الذي سيقوم البوت بالإجابة منه.",
        save_settings: "حفظ الإعدادات",
        bot_profile: "ملف البوت",
        bot_profile_desc: "تحديث اسم البوت على تليجرام.",
        bot_name: "اسم البوت",
        update_profile: "تحديث الملف الشخصي",
        processing_label: "جار المعالجة",
        stage_chunking: "تجزئة النص",
        stage_embedding: "تضمين النص",
        stage_indexing: "فهرسة المتجهات",
        ai_settings_title: "إعدادات النماذج",
        ai_settings_desc: "اختر مزود التوليد ومزود التضمين.",
        retrieval_top_k_label: "عدد المقاطع المسترجعة",
        retrieval_top_k_desc: "عدد المقاطع المستخدمة للإجابة.",
        chunk_strategy_label: "استراتيجية التجزئة",
        chunk_strategy_parent: "أب/ابن (من الصغير للكبير)",
        chunk_strategy_simple: "بسيطة",
        chunk_size_label: "حجم المقطع",
        chunk_overlap_label: "تداخل المقاطع",
        parent_chunk_size_label: "حجم المقطع الأب",
        parent_chunk_overlap_label: "تداخل المقطع الأب",
        retrieval_candidate_k_label: "عدد المرشحين الأولي",
        hybrid_enabled_label: "البحث الهجين",
        hybrid_alpha_label: "وزن الدلالي",
        rewrite_enabled_label: "إعادة صياغة الاستعلام",
        rerank_enabled_label: "إعادة الترتيب",
        rerank_top_k_label: "عدد إعادة الترتيب",
        gen_provider_label: "مزود التوليد",
        embed_provider_label: "مزود التضمين",
        select_project_ph: "اختر مشروعاً...",
        chat_responding_status: "الوكيل يرد الآن...",
        chat_stop_response: "إيقاف الرد",
        chat_response_stopped: "تم إيقاف الرد",
        delete_confirm: "هل أنت متأكد؟",
        success_saved: "تم الحفظ بنجاح",
        error_generic: "حدث خطأ ما",
        vector_db_label: "قاعدة المتجهات",
        embedding_size_label: "أبعاد التضمين",
        config_group_providers: "المزودون",
        config_group_chunking: "التجزئة",
        config_group_retrieval: "الاسترجاع",
        search_placeholder: "ابحث عن مشروع أو مستند...",
        empty_projects: "لا توجد مشاريع بعد",
        empty_projects_desc: "أنشئ أول مشروع لك وابدأ في رفع المستندات.",
        empty_docs: "لا توجد مستندات بعد",
        empty_docs_desc: "ارفع ملفات PDF أو TXT أو DOCX لبدء المعالجة.",
        copy_btn: "نسخ",
        copied_btn: "تم النسخ!",
        logout_btn: "تسجيل الخروج",
        account_settings_title: "إعدادات الحساب",
        account_settings_desc: "إدارة إعدادات الأمان والتفضيلات الشخصية.",
        account_profile_title: "الملف الشخصي",
        account_username_label: "اسم المستخدم",
        account_role_label: "الدور",
        account_created_label: "تاريخ الإنشاء",
        account_session_expires_label: "انتهاء الجلسة",
        account_preferences_title: "تفضيلات احترافية",
        account_language_label: "لغة الواجهة",
        account_theme_label: "المظهر",
        account_api_base_label: "رابط واجهة API",
        account_api_base_desc: "استخدمه لتبديل البيئة بسهولة (Local/Staging/Production).",
        account_save_preferences_btn: "حفظ التفضيلات",
        account_password_title: "تغيير كلمة المرور",
        account_password_desc: "حدّث كلمة مرورك بشكل دوري لحماية حسابك.",
        account_current_password_label: "كلمة المرور الحالية",
        account_new_password_label: "كلمة المرور الجديدة",
        account_confirm_password_label: "تأكيد كلمة المرور الجديدة",
        account_change_password_btn: "تحديث كلمة المرور",
        account_role_user: "مستخدم",
        account_role_admin: "مدير",
        account_role_security_engineer: "مهندس أمن",
        account_role_cybersecurity_engineer: "مهندس أمن سيبراني",
        language_ar: "العربية",
        language_en: "English",
        theme_dark: "داكن",
        theme_light: "فاتح",
        account_preferences_saved: "تم حفظ تفضيلات الحساب",
        account_api_unreachable: "تعذر الوصول إلى عنوان API المدخل",
        account_password_required: "يرجى ملء جميع حقول كلمة المرور",
        account_password_mismatch: "كلمة المرور الجديدة وتأكيدها غير متطابقين",
        account_password_updated: "تم تحديث كلمة المرور بنجاح",
        account_show_passwords: "إظهار كلمات المرور",
        account_password_strength_label: "قوة كلمة المرور",
        account_password_strength_empty: "-",
        account_password_strength_very_weak: "ضعيفة جدا",
        account_password_strength_weak: "ضعيفة",
        account_password_strength_fair: "متوسطة",
        account_password_strength_good: "جيدة",
        account_password_strength_strong: "قوية",
        account_password_endpoint_missing: "خدمة تغيير كلمة المرور غير متاحة حاليا. أعد تشغيل الباك-إند ثم جرّب مرة أخرى"
    },
    en: {
        nav_dashboard: "Dashboard",
        nav_security_center: "Security Center",
        nav_projects: "Projects",
        nav_chat: "Smart Chat",
        nav_bot: "Bot Settings",
        nav_ai_config: "AI Settings",
        nav_account_settings: "Account Settings",
        status_online: "Online",
        stat_projects: "Total Projects",
        stat_docs: "Documents",
        stat_chunks: "Text Chunks",
        security_section_title: "Security Center",
        security_section_overview_title: "Security Overview",
        security_total_events: "Total Events",
        security_login_failures: "Login Failures",
        security_blocked_attacks: "Blocked Attacks",
        security_brute_force_alerts: "Brute Force Alerts",
        security_open_incidents: "Open Incidents",
        security_high_severity_incidents: "High Severity Incidents",
        security_active_users: "Active Users",
        security_suspended_users: "Suspended Users",
        security_blocked_users: "Blocked Users",
        security_user_actions_title: "User Status Actions",
        security_duration_minutes_label: "Suspend Duration (minutes)",
        security_suspend_btn: "Suspend",
        security_block_btn: "Block",
        security_restore_btn: "Restore",
        security_admin_only_actions: "Only admin users can run these actions.",
        security_action_user_id_required: "Enter a valid user ID",
        security_action_reason_required: "Reason is required for suspend/block actions",
        security_action_duration_invalid: "Suspend duration must be between 1 and 10080 minutes",
        security_action_suspend_success: "User suspended successfully",
        security_action_block_success: "User blocked successfully",
        security_action_restore_success: "User restored successfully",
        security_events_title: "Security Events Feed",
        security_col_timestamp: "Timestamp",
        security_col_username: "Actor",
        security_col_event_type: "Event Type",
        security_col_severity: "Severity",
        security_col_message: "Message",
        security_events_empty: "No security events yet",
        security_live_feed_title: "Live Feed",
        security_live_feed_empty: "No live events right now",
        security_load_error: "Failed to load security data",
        security_simulate_btn: "Start Attack Simulation",
        security_simulate_running: "Running simulation...",
        security_simulate_success: "Simulation events generated",
        security_simulate_escalation_blocked: "Simulation escalated: user blocked",
        security_simulation_reset_btn: "Reset Simulation View",
        security_simulation_reset_running: "Clearing simulation feed...",
        security_simulation_reset_success: "Simulation feed cleared",
        security_simulation_reset_confirm: "This will clear simulated events from the feed.\nIncidents and system metrics will NOT be affected.\nContinue?",
        security_access_denied: "Access denied: Security Center is only for Cybersecurity Engineer",
        security_tab_events: "Events Feed",
        security_tab_incidents: "Incidents",
        security_incidents_title: "Incidents",
        incident_col_id: "Incident ID",
        incident_col_type: "Type",
        incident_col_severity: "Severity",
        incident_col_status: "Status",
        incident_col_created_at: "Created At",
        incident_col_false_positive: "False Positive",
        incident_empty: "No incidents yet",
        incident_filter_all_status: "All Status",
        incident_filter_all_severity: "All Severity",
        incident_filter_false_positive: "False Positive",
        incident_filter_fp_all: "All",
        incident_filter_fp_true: "True",
        incident_filter_fp_false: "False",
        incident_refresh_btn: "Refresh",
        incident_refresh_success: "Incidents refreshed",
        incident_back_to_events_btn: "Back to Events Feed",
        incident_details_title: "Incident Details",
        incident_label_id: "Incident ID",
        incident_label_type: "Type",
        incident_label_severity: "Severity",
        incident_label_status: "Status",
        incident_label_created_at: "Created At",
        incident_label_false_positive: "False Positive",
        incident_actor_title: "Actor Info",
        incident_notes_title: "Investigation Notes",
        incident_notes_placeholder: "Add investigation details, evidence, and conclusions...",
        incident_notes_save_btn: "Save Notes",
        incident_actions_title: "Actions",
        incident_action_reason_label: "Action Reason",
        incident_action_suspend_minutes_label: "Suspend Duration (minutes)",
        incident_action_reason_required: "Reason is required for this action",
        incident_action_suspend_minutes_invalid: "Suspend duration must be between 1 and 10080 minutes",
        incident_assign_btn: "Assign to me",
        incident_mark_investigating_btn: "Mark as Investigating",
        incident_resolve_btn: "Resolve",
        incident_close_btn: "Close",
        incident_mark_false_positive_btn: "Mark False Positive",
        incident_clear_false_positive_btn: "Clear False Positive",
        incident_block_user_btn: "Block User",
        incident_suspend_user_btn: "Suspend User",
        incident_reactivate_user_btn: "Restore User",
        incident_ignore_btn: "Ignore (false positive)",
        incident_timeline_title: "Timeline",
        incident_timeline_empty: "No logs yet",
        incident_timeline_timestamp: "Timestamp",
        incident_timeline_action: "Action",
        incident_timeline_result: "Result",
        incident_timeline_metadata: "Metadata",
        incident_result_success: "Success",
        incident_result_failed: "Failed",
        incident_select_first: "Select an incident first",
        incident_load_error: "Failed to load incidents",
        incident_action_assign_success: "Incident assigned to you",
        incident_action_status_success: "Incident status updated",
        incident_action_apply_success: "Incident action applied",
        incident_action_reactivate_success: "User restored successfully",
        incident_notes_saved: "Incident notes updated",
        incident_false_positive_marked: "Incident marked as false positive",
        incident_false_positive_cleared: "False-positive flag cleared",
        incident_new_alert_single: "New incident detected",
        incident_new_alert_multiple: "new incidents detected",
        incident_actor_unknown: "Unknown",
        incident_actor_label: "Actor",
        incident_assigned_label: "Assigned",
        incident_created_by_label: "Created by",
        incident_false_positive_label: "False Positive",
        incident_false_positive_yes: "Yes",
        incident_false_positive_no: "No",
        incident_status_open: "OPEN",
        incident_status_investigating: "INVESTIGATING",
        incident_status_resolved: "RESOLVED",
        incident_status_closed: "CLOSED",
        recent_projects: "Recent Projects",
        view_all: "View All",
        your_projects: "Your Projects",
        welcome_title: "Welcome to RAGMind",
        project_name_ph: "Ex: AI Research",
        project_desc_ph: "Short description...",
        create_project_btn: "Create Project",
        upload_title: "Upload New Documents",
        upload_desc: "Drag files here or click to select",
        docs_title: "Current Documents",
        bot_settings_title: "Telegram Bot Settings",
        bot_active_project: "Active Project",
        bot_active_project_desc: "Select the project the bot will answer from.",
        save_settings: "Save Settings",
        bot_profile: "Bot Profile",
        bot_profile_desc: "Update Bot Name on Telegram.",
        bot_name: "Bot Name",
        update_profile: "Update Profile",
        processing_label: "Processing",
        stage_chunking: "Chunking",
        stage_embedding: "Embedding",
        stage_indexing: "Indexing",
        ai_settings_title: "Model Settings",
        ai_settings_desc: "Select generation and embedding providers.",
        retrieval_top_k_label: "Retrieved chunks",
        retrieval_top_k_desc: "Number of chunks used to answer.",
        chunk_strategy_label: "Chunking strategy",
        chunk_strategy_parent: "Parent/child (small-to-big)",
        chunk_strategy_simple: "Simple",
        chunk_size_label: "Chunk size",
        chunk_overlap_label: "Chunk overlap",
        parent_chunk_size_label: "Parent chunk size",
        parent_chunk_overlap_label: "Parent overlap",
        retrieval_candidate_k_label: "Candidate pool",
        hybrid_enabled_label: "Hybrid search",
        hybrid_alpha_label: "Dense weight",
        rewrite_enabled_label: "Query rewriting",
        rerank_enabled_label: "Reranking",
        rerank_top_k_label: "Rerank top K",
        gen_provider_label: "Generation Provider",
        embed_provider_label: "Embedding Provider",
        select_project_ph: "Select a project...",
        chat_responding_status: "Agent is responding...",
        chat_stop_response: "Stop Response",
        chat_response_stopped: "Response stopped",
        delete_confirm: "Are you sure?",
        success_saved: "Saved successfully",
        error_generic: "Something went wrong",
        vector_db_label: "Vector Database",
        embedding_size_label: "Embedding Dimensions",
        config_group_providers: "Providers",
        config_group_chunking: "Chunking",
        config_group_retrieval: "Retrieval",
        search_placeholder: "Search projects or documents...",
        empty_projects: "No projects yet",
        empty_projects_desc: "Create your first project and start uploading documents.",
        empty_docs: "No documents yet",
        empty_docs_desc: "Upload PDF, TXT, or DOCX files to start processing.",
        copy_btn: "Copy",
        copied_btn: "Copied!",
        logout_btn: "Logout",
        account_settings_title: "Account Settings",
        account_settings_desc: "Manage security controls and personal preferences.",
        account_profile_title: "Profile",
        account_username_label: "Username",
        account_role_label: "Role",
        account_created_label: "Created At",
        account_session_expires_label: "Session Expires",
        account_preferences_title: "Professional Preferences",
        account_language_label: "Interface Language",
        account_theme_label: "Theme",
        account_api_base_label: "API Base URL",
        account_api_base_desc: "Use it to switch quickly between Local/Staging/Production.",
        account_save_preferences_btn: "Save Preferences",
        account_password_title: "Change Password",
        account_password_desc: "Rotate your password regularly to keep your account secure.",
        account_current_password_label: "Current Password",
        account_new_password_label: "New Password",
        account_confirm_password_label: "Confirm New Password",
        account_change_password_btn: "Update Password",
        account_role_user: "User",
        account_role_admin: "Administrator",
        account_role_security_engineer: "Security Engineer",
        account_role_cybersecurity_engineer: "Cybersecurity Engineer",
        language_ar: "Arabic",
        language_en: "English",
        theme_dark: "Dark",
        theme_light: "Light",
        account_preferences_saved: "Account preferences saved",
        account_api_unreachable: "The provided API endpoint is unreachable",
        account_password_required: "Please fill in all password fields",
        account_password_mismatch: "New password and confirmation do not match",
        account_password_updated: "Password updated successfully",
        account_show_passwords: "Show passwords",
        account_password_strength_label: "Password strength",
        account_password_strength_empty: "-",
        account_password_strength_very_weak: "Very weak",
        account_password_strength_weak: "Weak",
        account_password_strength_fair: "Fair",
        account_password_strength_good: "Good",
        account_password_strength_strong: "Strong",
        account_password_endpoint_missing: "Password update endpoint is unavailable. Restart the backend and try again"
    }
};

// State Management
const state = {
    currentView: 'dashboard',
    projects: [],
    stats: null,
    securitySimulationReset: null,
    currentUser: null,
    selectedProject: null,
    chatMessages: [],
    chatRequestInProgress: false,
    chatAbortController: null,
    chatThinkingMessageId: null,
    isUploading: false,
    retrievalTopK: null,
    docPoller: null,
    securityStreamAbortController: null,
    securityStreamReconnectTimer: null,
    securityEventsRefreshController: null,
    securityEventsRefreshInProgress: false,
    securityEventsRefreshTimer: null,
    securityEventsLabelTimer: null,
    securityEventsLastUpdatedAt: 0,
    securityEventsLastInteractionAt: 0,
    securityEvents: [],
    incidentOverviewTimer: null,
    incidentOverviewRefreshTimer: null,
    securityUsersRefreshTimer: null,
    securityActiveTab: 'events',
    securityIncidents: [],
    latestIncidentSeenId: 0,
    incidentBaselineInitialized: false,
    unseenIncidentCount: 0,
    selectedIncident: null,
    incidentDetailsRequestToken: 0,
    incidentDetailsCloseTimer: null,
    incidentPanelOutsideClickHandler: null,
    incidentPanelKeydownHandler: null,
    incidentBackToEventsScrollHandler: null,
    lang: localStorage.getItem('lang') || 'ar',
    theme: localStorage.getItem('theme') || 'dark'
};

// DOM Elements
const elements = {
    viewContainer: document.getElementById('view-container'),
    navItems: document.querySelectorAll('.sidebar-nav li'),
    newProjectBtn: document.getElementById('new-project-btn'),
    modalOverlay: document.getElementById('modal-overlay'),
    modalTitle: document.getElementById('modal-title'),
    modalBody: document.getElementById('modal-body'),
    closeModalBtn: document.querySelector('.close-modal'),
    themeToggle: document.getElementById('theme-toggle'),
    langToggle: document.getElementById('lang-toggle'),
    logoutBtn: document.getElementById('logout-btn'),
    userNameLabel: document.querySelector('.user-info .name'),
    userAvatar: document.querySelector('.user-info .avatar')
};

const ACTIVE_DOC_STATUSES = new Set(['uploaded', 'queued', 'pending', 'processing']);
const ACCESS_TOKEN_KEY = 'access_token';
const SECURITY_STREAM_RECONNECT_MS = 1500;
const INCIDENT_OVERVIEW_POLL_MS = 7000;
const INCIDENT_OVERVIEW_STREAM_SYNC_DELAY_MS = 1200;
const SECURITY_USERS_REFRESH_DELAY_MS = 1200;
const SECURITY_EVENTS_AUTO_REFRESH_MS = 8000;
const SECURITY_EVENTS_INTERACTION_GRACE_MS = 2500;
const INCIDENT_PANEL_CLOSE_ANIMATION_MS = 180;
const SIMULATION_RESET_STATE_KEY = 'ragmind_security_simulation_reset_state';
const ROLE_USER = 'user';
const ROLE_ADMIN = 'admin';
const ROLE_SECURITY_ENGINEER = 'security_engineer';
const ROLE_CYBERSECURITY_ENGINEER = 'cybersecurity_engineer';

function getAccessToken() {
    return (localStorage.getItem(ACCESS_TOKEN_KEY) || '').trim();
}

function parseJwtPayload(token) {
    try {
        const parts = String(token || '').split('.');
        if (parts.length !== 3) return null;
        const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
        const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
        const json = atob(padded);
        return JSON.parse(json);
    } catch (_) {
        return null;
    }
}

function isTokenExpired(token) {
    const payload = parseJwtPayload(token);
    if (!payload || typeof payload.exp !== 'number') return true;
    return Date.now() >= payload.exp * 1000;
}

function getSimulationResetState() {
    // Design decision: "Reset Simulation View" no longer applies a global tombstone.
    // Keep this helper as a safe no-op reader to avoid rebase regressions in shared paths.
    if (state && state.securitySimulationReset && typeof state.securitySimulationReset === 'object') {
        return state.securitySimulationReset;
    }

    try {
        const raw = localStorage.getItem(SIMULATION_RESET_STATE_KEY);
        if (!raw) {
            return { active: false, reset_at: null, removed_event_ids: [], removed_incident_ids: [], stats_delta: {}, incident_delta: {} };
        }

        const parsed = JSON.parse(raw);
        return {
            active: false,
            reset_at: typeof parsed.reset_at === 'string' ? parsed.reset_at : null,
            removed_event_ids: [],
            removed_incident_ids: [],
            stats_delta: {},
            incident_delta: {},
        };
    } catch (_) {
        return { active: false, reset_at: null, removed_event_ids: [], removed_incident_ids: [], stats_delta: {}, incident_delta: {} };
    }
}

function setSimulationResetState(nextState) {
    const normalizedState = nextState && nextState.active
        ? {
            active: true,
            reset_at: typeof nextState.reset_at === 'string' ? nextState.reset_at : new Date().toISOString(),
            removed_event_ids: Array.isArray(nextState.removed_event_ids) ? nextState.removed_event_ids : [],
            removed_incident_ids: Array.isArray(nextState.removed_incident_ids) ? nextState.removed_incident_ids : [],
            stats_delta: nextState.stats_delta && typeof nextState.stats_delta === 'object' && !Array.isArray(nextState.stats_delta) ? nextState.stats_delta : {},
            incident_delta: nextState.incident_delta && typeof nextState.incident_delta === 'object' && !Array.isArray(nextState.incident_delta) ? nextState.incident_delta : {},
        }
        : { active: false, reset_at: null, removed_event_ids: [], removed_incident_ids: [], stats_delta: {}, incident_delta: {} };

    state.securitySimulationReset = normalizedState;

    if (!normalizedState.active) {
        localStorage.removeItem(SIMULATION_RESET_STATE_KEY);
        return;
    }

    localStorage.setItem(SIMULATION_RESET_STATE_KEY, JSON.stringify(normalizedState));
}

function isSimulationResetActive() {
    return Boolean(getSimulationResetState().active);
}

function redirectToLogin(reason = '') {
    if (reason) {
        window.location.replace(`login.html?reason=${encodeURIComponent(reason)}`);
        return;
    }
    window.location.replace('login.html');
}

function clearAuthAndRedirect(reason = 'expired') {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    redirectToLogin(reason);
}

function logoutUser() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    redirectToLogin();
}

function withAuthHeaders(extraHeaders = {}) {
    const token = getAccessToken();
    const headers = { ...extraHeaders };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    return headers;
}

function normalizeBaseUrl(url) {
    if (!url) return '';
    return String(url)
        .trim()
        .replace(/\^+$/, '')
        .replace(/\/+$/, '');
}

function isDocumentActive(status) {
    return ACTIVE_DOC_STATUSES.has(String(status || '').toLowerCase());
}

function getApiBaseCandidates() {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = normalizeBaseUrl(params.get('api'));
    const host = window.location.hostname || '52.188.226.80';
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';

    const candidates = [
        fromQuery,
        normalizeBaseUrl(localStorage.getItem('ragmind_api_base_url')),
        normalizeBaseUrl(API_BASE_URL),
        `${protocol}//${host}:8000`,
        `${protocol}//${host}:8101`,
        `${protocol}//${host}:8001`
    ].filter(Boolean);

    return [...new Set(candidates)];
}

async function canReachApi(baseUrl) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 2000);

    try {
        const response = await fetch(`${baseUrl}/health`, { signal: controller.signal });
        return response.ok;
    } catch (_) {
        return false;
    } finally {
        clearTimeout(timeout);
    }
}

async function resolveApiBaseUrl(maxAttempts = 8) {
    const candidates = getApiBaseCandidates();

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        for (const candidate of candidates) {
            if (await canReachApi(candidate)) {
                API_BASE_URL = candidate;
                localStorage.setItem('ragmind_api_base_url', API_BASE_URL);
                return true;
            }
        }

        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    return false;
}

function isAuthEndpoint(endpoint) {
    return /^\/auth\/(login|me|change-password)(?:\/|$)/i.test(String(endpoint || '').trim());
}

async function fetchWithApiRecovery(endpoint, options = {}, retries = 1) {
    let lastError = null;
    const effectiveRetries = isAuthEndpoint(endpoint) ? 0 : retries;

    for (let attempt = 0; attempt <= effectiveRetries; attempt++) {
        try {
            return await fetch(`${API_BASE_URL}${endpoint}`, options);
        } catch (error) {
            lastError = error;
            const message = String(error && error.message ? error.message : '').toLowerCase();
            const isNetworkFailure = message.includes('failed to fetch');

            if (!isNetworkFailure || attempt >= effectiveRetries) {
                break;
            }

            const recovered = await resolveApiBaseUrl(20);
            if (!recovered) {
                break;
            }
        }
    }

    throw lastError || new Error('Failed to fetch');
}

function isNetworkError(error) {
    const message = String(error && error.message ? error.message : '').toLowerCase();
    return error instanceof TypeError || message.includes('failed to fetch');
}

function evaluatePasswordStrength(password) {
    const value = String(password || '');
    if (!value) {
        return {
            level: 0,
            tone: 'none',
            labelKey: 'account_password_strength_empty'
        };
    }

    let score = 0;
    if (value.length >= 8) score += 1;
    if (value.length >= 12) score += 1;
    if (/[a-z]/.test(value) && /[A-Z]/.test(value)) score += 1;
    if (/\d/.test(value)) score += 1;
    if (/[^A-Za-z0-9]/.test(value)) score += 1;

    if (score <= 1) {
        return { level: 1, tone: 'very-weak', labelKey: 'account_password_strength_very_weak' };
    }
    if (score === 2) {
        return { level: 2, tone: 'weak', labelKey: 'account_password_strength_weak' };
    }
    if (score === 3) {
        return { level: 3, tone: 'fair', labelKey: 'account_password_strength_fair' };
    }
    if (score === 4) {
        return { level: 4, tone: 'good', labelKey: 'account_password_strength_good' };
    }

    return { level: 4, tone: 'strong', labelKey: 'account_password_strength_strong' };
}

function renderPasswordStrengthIndicator(password) {
    const meter = document.getElementById('password-strength-meter');
    const text = document.getElementById('password-strength-text');
    if (!meter || !text) return;

    const t = i18n[state.lang];
    const strength = evaluatePasswordStrength(password);
    meter.dataset.level = String(strength.level);
    text.dataset.strength = strength.tone;
    text.textContent = t[strength.labelKey] || '-';
}

async function submitPasswordChangeWithFallback(payload) {
    const token = getAccessToken();
    if (!token) {
        clearAuthAndRedirect('expired');
        throw new Error('Unauthorized');
    }

    const endpointCandidates = ['/auth/change-password', '/auth/update-password'];
    const baseCandidates = [API_BASE_URL, ...getApiBaseCandidates().filter(base => base !== API_BASE_URL)];

    let lastNetworkError = null;

    for (const baseUrl of baseCandidates) {
        let baseUnreachable = false;

        for (const endpoint of endpointCandidates) {
            let response;

            try {
                response = await fetch(`${baseUrl}${endpoint}`, {
                    method: 'POST',
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
            } catch (error) {
                if (isNetworkError(error)) {
                    lastNetworkError = error;
                    baseUnreachable = true;
                    break;
                }
                throw error;
            }

            if (response.status === 401) {
                clearAuthAndRedirect('expired');
                throw new Error('Unauthorized');
            }

            if (response.status === 404) {
                continue;
            }

            let responseData = {};
            try {
                responseData = await response.json();
            } catch (_) {
                responseData = {};
            }

            if (!response.ok) {
                const apiError = new Error(responseData.detail || 'Error');
                apiError.status = response.status;
                throw apiError;
            }

            if (API_BASE_URL !== baseUrl) {
                API_BASE_URL = baseUrl;
                localStorage.setItem('ragmind_api_base_url', API_BASE_URL);
            }

            return responseData;
        }

        if (baseUnreachable) {
            continue;
        }
    }

    if (lastNetworkError) {
        throw lastNetworkError;
    }

    const endpointError = new Error(i18n[state.lang].account_password_endpoint_missing);
    endpointError.status = 404;
    throw endpointError;
}

// --- API Client ---

const api = {
    async get(endpoint) {
        try {
            const response = await fetchWithApiRecovery(endpoint, {
                headers: withAuthHeaders()
            });
            if (response.status === 401) {
                clearAuthAndRedirect('expired');
                throw new Error('Unauthorized');
            }
            if (!response.ok) {
                let errorData = {};
                try {
                    errorData = await response.json();
                } catch (_) {
                    errorData = {};
                }
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API Get Error (${endpoint}):`, error);
            if (error.message !== 'Unauthorized') {
                const message = error.message === 'Failed to fetch'
                    ? (state.lang === 'ar' ? 'خطأ في الاتصال بالسيرفر' : 'Server Connection Error')
                    : error.message;
                showNotification(message, 'error');
            }
            throw error;
        }
    },

    async post(endpoint, data, isFormData = false) {
        try {
            const options = {
                method: 'POST',
                body: isFormData ? data : JSON.stringify(data)
            };
            options.headers = withAuthHeaders(
                isFormData ? {} : { 'Content-Type': 'application/json' }
            );

            const response = await fetchWithApiRecovery(endpoint, options);
            if (response.status === 401) {
                clearAuthAndRedirect('expired');
                throw new Error('Unauthorized');
            }
            if (!response.ok) {
                let errorData = {};
                try {
                    errorData = await response.json();
                } catch (_) {
                    errorData = {};
                }
                const apiError = new Error(errorData.detail || 'Error');
                apiError.status = response.status;
                throw apiError;
            }
            return await response.json();
        } catch (error) {
            console.error(`API Post Error (${endpoint}):`, error);
            if (error.message !== 'Unauthorized') {
                showNotification(error.message, 'error');
            }
            throw error;
        }
    },

    async patch(endpoint, data) {
        try {
            const response = await fetchWithApiRecovery(endpoint, {
                method: 'PATCH',
                headers: withAuthHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify(data || {})
            });

            if (response.status === 401) {
                clearAuthAndRedirect('expired');
                throw new Error('Unauthorized');
            }

            if (!response.ok) {
                let errorData = {};
                try {
                    errorData = await response.json();
                } catch (_) {
                    errorData = {};
                }
                const apiError = new Error(errorData.detail || 'Error');
                apiError.status = response.status;
                throw apiError;
            }

            return await response.json();
        } catch (error) {
            console.error(`API Patch Error (${endpoint}):`, error);
            if (error.message !== 'Unauthorized') {
                showNotification(error.message, 'error');
            }
            throw error;
        }
    },

    async delete(endpoint) {
        try {
            const response = await fetchWithApiRecovery(endpoint, {
                method: 'DELETE',
                headers: withAuthHeaders()
            });
            if (response.status === 401) {
                clearAuthAndRedirect('expired');
                throw new Error('Unauthorized');
            }
            if (!response.ok) throw new Error('Delete failed');
            return true;
        } catch (error) {
            console.error(`API Delete Error (${endpoint}):`, error);
            if (error.message !== 'Unauthorized') {
                showNotification(error.message, 'error');
            }
            throw error;
        }
    }
};

function normalizeProjectsResponse(payload) {
    if (Array.isArray(payload)) return payload;
    if (payload && Array.isArray(payload.items)) return payload.items;
    return [];
}

async function getCurrentUser() {
    if (state.currentUser) {
        updateSidebarUserInfo(state.currentUser);
        applySecurityCenterNavAccess();
        return state.currentUser;
    }

    state.currentUser = await api.get('/auth/me');
    updateSidebarUserInfo(state.currentUser);
    applySecurityCenterNavAccess();
    return state.currentUser;
}

function updateSidebarUserInfo(user) {
    const fallbackName = state.lang === 'ar' ? 'المستخدم' : 'User';
    const rawName = user && user.username ? String(user.username).trim() : '';
    const displayName = rawName || fallbackName;

    if (elements.userNameLabel) {
        elements.userNameLabel.textContent = displayName;
    }

    if (elements.userAvatar) {
        const firstChar = displayName.charAt(0) || 'U';
        elements.userAvatar.textContent = firstChar.toUpperCase();
    }
}

function normalizeUserRoles(user) {
    const normalizedRoles = [];

    const appendRole = (rawRole) => {
        const role = String(rawRole || '').trim().toLowerCase();
        if (!role) return;

        // Keep both engineer role names for backward compatibility.
        if (role === ROLE_SECURITY_ENGINEER && !normalizedRoles.includes(ROLE_CYBERSECURITY_ENGINEER)) {
            normalizedRoles.push(ROLE_CYBERSECURITY_ENGINEER);
        }
        if (role === ROLE_CYBERSECURITY_ENGINEER && !normalizedRoles.includes(ROLE_SECURITY_ENGINEER)) {
            normalizedRoles.push(ROLE_SECURITY_ENGINEER);
        }

        if (!normalizedRoles.includes(role)) {
            normalizedRoles.push(role);
        }
    };

    if (user && Array.isArray(user.roles)) {
        user.roles.forEach(appendRole);
    }

    if (user && typeof user.role === 'string') {
        appendRole(user.role);
    }

    if (normalizedRoles.length === 0) {
        normalizedRoles.push(ROLE_USER);
    } else if (!normalizedRoles.includes(ROLE_USER)) {
        normalizedRoles.push(ROLE_USER);
    }

    return normalizedRoles;
}

function formatPrimaryRoleLabel(user = state.currentUser) {
    const t = i18n[state.lang];
    const roles = normalizeUserRoles(user);
    const primaryRole = roles[0] || ROLE_USER;

    if (primaryRole === ROLE_SECURITY_ENGINEER || primaryRole === ROLE_CYBERSECURITY_ENGINEER) {
        return t.account_role_security_engineer || t.account_role_cybersecurity_engineer || primaryRole;
    }

    if (primaryRole === ROLE_ADMIN) {
        return t.account_role_admin || primaryRole;
    }

    return t.account_role_user || primaryRole;
}

function formatLocaleDateTime(value, locale = null) {
    if (!value) return '-';

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return '-';
    }

    const resolvedLocale = locale || (state.lang === 'ar' ? 'ar-EG' : 'en-US');
    return date.toLocaleString(resolvedLocale);
}

function getSessionExpiryLabel() {
    const payload = parseJwtPayload(getAccessToken());
    if (!payload || typeof payload.exp !== 'number') {
        return '-';
    }

    return formatLocaleDateTime(payload.exp * 1000);
}

function canAccessSecurityCenter(user = state.currentUser) {
    const roles = normalizeUserRoles(user);
    return roles.includes(ROLE_SECURITY_ENGINEER) || roles.includes(ROLE_CYBERSECURITY_ENGINEER) || roles.includes(ROLE_ADMIN);
}

function applySecurityCenterNavAccess() {
    const navItem = document.querySelector('.sidebar-nav li[data-view="securityCenter"]');
    if (!navItem) return;

    navItem.style.display = canAccessSecurityCenter() ? '' : 'none';
}

async function fetchUserProjects() {
    const [projectsPayload, currentUser] = await Promise.all([
        api.get('/projects/'),
        getCurrentUser()
    ]);

    const projects = normalizeProjectsResponse(projectsPayload);

    // Defensive filtering in case owner_id is present in response payload.
    if (projects.length > 0 && projects.some(project => typeof project.owner_id !== 'undefined')) {
        return projects.filter(project => project.owner_id === currentUser.id);
    }

    return projects;
}

function sumProjectMetric(projects, fieldName) {
    return projects.reduce((sum, project) => {
        const value = Number(project && project[fieldName]);
        return sum + (Number.isFinite(value) ? value : 0);
    }, 0);
}

function normalizeSecurityStats(payload) {
    const data = payload && typeof payload === 'object' ? payload : {};
    const toCount = (value) => {
        const numeric = Number(value);
        if (!Number.isFinite(numeric) || numeric < 0) return 0;
        return Math.floor(numeric);
    };

    return {
        total_events: toCount(data.total_events),
        login_failures: toCount(data.login_failures),
        brute_force_attempts: toCount(data.brute_force_attempts),
        blocked_uploads: toCount(data.blocked_uploads)
    };
}

function normalizeSecurityUserStatusSummary(payload) {
    const data = payload && typeof payload === 'object' ? payload : {};
    const toCount = (value) => {
        const numeric = Number(value);
        if (!Number.isFinite(numeric) || numeric < 0) return 0;
        return Math.floor(numeric);
    };

    return {
        total_active: toCount(data.total_active),
        total_suspended: toCount(data.total_suspended),
        total_blocked: toCount(data.total_blocked)
    };
}

function formatSecurityEventsLastUpdatedLabel(timestamp) {
    const numericTimestamp = Number(timestamp);
    if (!Number.isFinite(numericTimestamp) || numericTimestamp <= 0) {
        return 'Last updated • just now';
    }

    const elapsedSeconds = Math.max(0, Math.floor((Date.now() - numericTimestamp) / 1000));
    if (elapsedSeconds < 5) {
        return 'Last updated • just now';
    }
    if (elapsedSeconds < 60) {
        return `Last updated • ${elapsedSeconds}s ago`;
    }

    const elapsedMinutes = Math.floor(elapsedSeconds / 60);
    if (elapsedMinutes < 60) {
        return `Last updated • ${elapsedMinutes}m ago`;
    }

    const elapsedHours = Math.floor(elapsedMinutes / 60);
    return `Last updated • ${elapsedHours}h ago`;
}

function updateSecurityEventsLastUpdatedLabel() {
    const label = document.getElementById('security-events-last-updated');
    if (!label) return;

    label.textContent = formatSecurityEventsLastUpdatedLabel(state.securityEventsLastUpdatedAt);
    const numericTimestamp = Number(state.securityEventsLastUpdatedAt);
    const isStale = Number.isFinite(numericTimestamp)
        && numericTimestamp > 0
        && (Date.now() - numericTimestamp) >= 5000;
    label.classList.toggle('is-stale', isStale);
}

function markSecurityEventsFeedUpdated(timestamp = Date.now()) {
    state.securityEventsLastUpdatedAt = Number(timestamp) || Date.now();
    updateSecurityEventsLastUpdatedLabel();
}

function markSecurityEventsFeedInteraction() {
    state.securityEventsLastInteractionAt = Date.now();
}

function isSecurityEventsAutoRefreshAllowed() {
    if (!isSecurityCenterView() || state.securityActiveTab !== 'events') return false;
    if (document.visibilityState && document.visibilityState !== 'visible') return false;

    return Date.now() - Number(state.securityEventsLastInteractionAt || 0) >= SECURITY_EVENTS_INTERACTION_GRACE_MS;
}

function setSecurityEventsRefreshButtonLoading(isLoading) {
    const button = document.getElementById('security-events-refresh-btn');
    if (!button) return;

    button.disabled = Boolean(isLoading);
    button.classList.toggle('is-loading', Boolean(isLoading));

    const icon = button.querySelector('i');
    if (icon) {
        icon.className = isLoading ? 'fas fa-spinner' : 'fas fa-arrows-rotate';
    }
}

function preserveElementScrollState(element) {
    return element && typeof element.scrollTop === 'number' ? element.scrollTop : 0;
}

function restoreElementScrollState(element, scrollTop) {
    if (element && typeof element.scrollTop === 'number') {
        element.scrollTop = scrollTop;
    }
}

async function fetchSecurityJson(endpoint, options = {}) {
    const response = await fetchWithApiRecovery(endpoint, {
        headers: withAuthHeaders(),
        ...options
    });

    if (response.status === 401) {
        clearAuthAndRedirect('expired');
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
        let errorData = {};
        try {
            errorData = await response.json();
        } catch (_) {
            errorData = {};
        }
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
}

async function fetchSecurityDashboardData(limit = 20, options = {}) {
    const safeLimit = limit === 50 ? 50 : 20;
    const [statsPayload, eventsPayload] = await Promise.all([
        fetchSecurityJson('/security/stats', options),
        fetchSecurityJson(`/security/events?limit=${safeLimit}`, options)
    ]);

    // The dashboard fetch is the broadest API hydration path, so it must
    // apply the reset filter before any view renders from the returned events.
    const filtered = filterSimulationPayload(eventsPayload, []);

    return {
        stats: normalizeSecurityStats(statsPayload),
        events: Array.isArray(filtered.events) ? filtered.events : []
    };
}

async function fetchSecurityUserStatusData() {
    const summaryPayload = await fetchSecurityJson('/security/users/status-summary');

    return {
        summary: normalizeSecurityUserStatusSummary(summaryPayload)
    };
}

function getSecuritySeverityClass(severity) {
    switch (String(severity || '').toUpperCase()) {
        case 'LOW':
            return 'security-severity-low';
        case 'MEDIUM':
            return 'security-severity-medium';
        case 'HIGH':
            return 'security-severity-high';
        case 'CRITICAL':
            return 'security-severity-critical';
        default:
            return 'security-severity-medium';
    }
}

function formatSecurityTimestamp(timestamp) {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) {
        return '-';
    }
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

function formatSecurityClockTime(timestamp) {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) {
        return '--:--:--';
    }

    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

function getSortTimestampValue(value) {
    const parsed = Date.parse(String(value || ''));
    if (!Number.isFinite(parsed)) {
        return 0;
    }
    return parsed;
}

function scrollSecurityTableToTop(tableBody) {
    if (!tableBody) return;
    const tableWrap = tableBody.closest('.security-events-table-wrap');
    if (tableWrap) {
        tableWrap.scrollTop = 0;
    }
}

function syncSecurityStickyFirstRowOffset(tableBody) {
    if (!tableBody) return;

    const tableWrap = tableBody.closest('.security-events-table-wrap');
    const table = tableBody.closest('table');
    if (!tableWrap || !table) return;

    const headerRow = table.querySelector('thead tr');
    if (!headerRow) return;

    const headerHeight = Math.ceil(headerRow.getBoundingClientRect().height || 0);
    if (headerHeight > 0) {
        tableWrap.style.setProperty('--security-header-sticky-offset', `${headerHeight}px`);
    }
}

function extractSecurityEventUser(event) {
    const directUsername = String(event && event.username ? event.username : '').trim();
    if (directUsername) {
        return directUsername;
    }

    const metadataUsername = String(
        event && event.metadata && event.metadata.username ? event.metadata.username : ''
    ).trim();
    if (metadataUsername) {
        return metadataUsername;
    }

    const userId = Number(event && event.user_id);
    if (Number.isFinite(userId) && userId > 0) {
        return `user_${userId}`;
    }

    return 'System';
}

function getSecurityCenterTranslations() {
    const currentView = state.currentView;
    const securityView = currentView === 'securityCenter' || currentView === 'security-center';
    return securityView ? i18n.en : i18n[state.lang];
}

function renderSecurityLiveFeed(events) {
    const feedList = document.getElementById('security-live-feed-list');
    if (!feedList) return;
    const t = getSecurityCenterTranslations();

    if (!Array.isArray(events) || events.length === 0) {
        feedList.innerHTML = `<li class="security-live-feed-empty">${escapeHtml(t.security_live_feed_empty)}</li>`;
        return;
    }

    feedList.innerHTML = events.slice(0, 8).map((event) => {
        const eventType = String(event && event.event_type ? event.event_type : 'UNKNOWN').toUpperCase();
        const message = String(event && event.message ? event.message : '-');
        const userLabel = extractSecurityEventUser(event);
        const line = `[${formatSecurityClockTime(event && event.timestamp ? event.timestamp : '')}] ${eventType} [Actor: ${userLabel}] - ${message}`;

        return `<li class="security-live-feed-item"><span class="security-live-feed-line">${escapeHtml(line)}</span></li>`;
    }).join('');
}

function renderSecurityCounters(stats, shouldAnimate = false) {
    const safeStats = normalizeSecurityStats(stats || {});

    if (shouldAnimate) {
        animateCounter('security-stat-total-events', safeStats.total_events);
        animateCounter('security-stat-login-failures', safeStats.login_failures);
        animateCounter('security-stat-blocked-attacks', safeStats.blocked_uploads);
        animateCounter('security-stat-brute-force', safeStats.brute_force_attempts);
        return;
    }

    const setCounter = (id, value) => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = Number(value || 0).toLocaleString();
        }
    };

    setCounter('security-stat-total-events', safeStats.total_events);
    setCounter('security-stat-login-failures', safeStats.login_failures);
    setCounter('security-stat-blocked-attacks', safeStats.blocked_uploads);
    setCounter('security-stat-brute-force', safeStats.brute_force_attempts);
}

function renderSecurityUserStatusCounters(summary, shouldAnimate = false) {
    const safeSummary = normalizeSecurityUserStatusSummary(summary || {});

    if (shouldAnimate) {
        animateCounter('security-stat-active-users', safeSummary.total_active);
        animateCounter('security-stat-suspended-users', safeSummary.total_suspended);
        animateCounter('security-stat-blocked-users', safeSummary.total_blocked);
        return;
    }

    const setCounter = (id, value) => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = Number(value || 0).toLocaleString();
        }
    };

    setCounter('security-stat-active-users', safeSummary.total_active);
    setCounter('security-stat-suspended-users', safeSummary.total_suspended);
    setCounter('security-stat-blocked-users', safeSummary.total_blocked);
}

function renderSecurityEventsTable(events, options = {}) {
    const tableBody = document.getElementById('security-events-body');
    if (!tableBody) return;
    const t = getSecurityCenterTranslations();
    const preserveScroll = Boolean(options.preserveScroll);

    syncSecurityStickyFirstRowOffset(tableBody);

    if (!Array.isArray(events) || events.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" class="security-empty-row">${escapeHtml(t.security_events_empty)}</td></tr>`;
        if (!preserveScroll) {
            scrollSecurityTableToTop(tableBody);
        }
        return;
    }

    const orderedEvents = [...events].sort((left, right) => {
        const rightTs = getSortTimestampValue(right && right.timestamp ? right.timestamp : '');
        const leftTs = getSortTimestampValue(left && left.timestamp ? left.timestamp : '');
        return rightTs - leftTs;
    });

    tableBody.innerHTML = orderedEvents.map((event) => {
        const eventType = String(event && event.event_type ? event.event_type : 'UNKNOWN').toUpperCase();
        const severity = String(event && event.severity ? event.severity : 'MEDIUM').toUpperCase();
        const username = extractSecurityEventUser(event);
        const message = String(event && event.message ? event.message : '-');
        const timestamp = formatSecurityTimestamp(event && event.timestamp ? event.timestamp : '');
        const severityClass = getSecuritySeverityClass(severity);

        return `
            <tr>
                <td class="security-col-time">${escapeHtml(timestamp)}</td>
                <td class="security-col-username">${escapeHtml(username)}</td>
                <td><span class="security-event-type">${escapeHtml(eventType)}</span></td>
                <td><span class="security-severity ${severityClass}">${escapeHtml(severity)}</span></td>
                <td class="security-col-message">${escapeHtml(message)}</td>
            </tr>
        `;
    }).join('');

    if (!preserveScroll) {
        scrollSecurityTableToTop(tableBody);
    }
}

function hasSimulationMarkerInMetadata(metadata) {
    if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata)) {
        return false;
    }

    const marker = metadata.simulation;
    if (marker === true) {
        return true;
    }

    return String(marker || '').trim().toLowerCase() === 'true';
}

function isSimulatedSecurityEvent(event) {
    if (!event || typeof event !== 'object') return false;

    const eventType = String(event.event_type || '').trim().toUpperCase();
    const message = String(event.message || '').trim().toLowerCase();

    return (
        hasSimulationMarkerInMetadata(event.metadata)
        || eventType === 'ATTACK_SIMULATION'
        || message.includes('(simulation)')
    );
}

function isSimulatedIncident(incident) {
    if (!incident || typeof incident !== 'object') return false;

    const description = String(incident.description || '').trim().toLowerCase();
    if (description.includes('(simulation)')) {
        return true;
    }

    const logs = Array.isArray(incident.logs) ? incident.logs : [];
    return logs.some((entry) => {
        const metadata = entry && entry.extra_metadata;
        return hasSimulationMarkerInMetadata(metadata);
    });
}

function getSecurityEntryTimestampMs(entry) {
    const candidate = entry && (entry.timestamp || entry.created_at || entry.createdAt || entry.created);
    const parsed = Date.parse(candidate);
    return Number.isFinite(parsed) ? parsed : null;
}

function summarizeSimulationEventDelta(events) {
    const summary = {
        total_events: 0,
        login_failures: 0,
        brute_force_attempts: 0,
        blocked_uploads: 0
    };

    for (const event of Array.isArray(events) ? events : []) {
        if (!isSimulatedSecurityEvent(event)) {
            continue;
        }

        summary.total_events += 1;

        const eventType = String(event && event.event_type ? event.event_type : '').trim().toUpperCase();
        if (eventType === 'LOGIN_FAIL') {
            summary.login_failures += 1;
        }
        if (eventType === 'BRUTE_FORCE') {
            summary.brute_force_attempts += 1;
        }
        if (eventType === 'FILE_UPLOAD_BLOCKED') {
            summary.blocked_uploads += 1;
        }
    }

    return summary;
}

function summarizeSimulationIncidentDelta(incidents) {
    return calculateIncidentMetrics((Array.isArray(incidents) ? incidents : []).filter(isSimulatedIncident));
}

function filterSimulationPayload(events, incidents) {
    const resetState = getSimulationResetState();
    const removedEventIds = new Set((resetState.removed_event_ids || []).map((value) => String(value)));
    const removedIncidentIds = new Set((resetState.removed_incident_ids || []).map((value) => String(value)));
    const resetCutoffMs = resetState.reset_at ? Date.parse(resetState.reset_at) : null;

    const safeEvents = Array.isArray(events) ? events : [];
    const safeIncidents = Array.isArray(incidents) ? incidents : [];

    if (!resetState.active) {
        return { events: safeEvents, incidents: safeIncidents };
    }

    // API and stream payloads must be filtered here so stale simulation rows
    // cannot rehydrate the UI after reset, tab switch, or refresh.
    return {
        events: safeEvents.filter((event) => {
            const eventId = String(event && event.id ? event.id : '');
            if (eventId && removedEventIds.has(eventId)) {
                return false;
            }

            const eventTime = getSecurityEntryTimestampMs(event);
            if (Number.isFinite(resetCutoffMs) && Number.isFinite(eventTime) && eventTime <= resetCutoffMs && isSimulatedSecurityEvent(event)) {
                return false;
            }

            return true;
        }),
        incidents: safeIncidents.filter((incident) => {
            const incidentId = String(incident && incident.id ? incident.id : '');
            if (incidentId && removedIncidentIds.has(incidentId)) {
                return false;
            }

            const incidentTime = getSecurityEntryTimestampMs(incident);
            if (Number.isFinite(resetCutoffMs) && Number.isFinite(incidentTime) && incidentTime <= resetCutoffMs && isSimulatedIncident(incident)) {
                return false;
            }

            return true;
        })
    };
}

function applySimulationResetToStats(stats) {
    const resetState = getSimulationResetState();
    const baseStats = normalizeSecurityStats(stats || {});
    if (!resetState.active) {
        return baseStats;
    }

    const delta = resetState.stats_delta || {};
    const subtract = (value, removed) => Math.max(0, Number(value || 0) - Number(removed || 0));

    return {
        total_events: subtract(baseStats.total_events, delta.total_events),
        login_failures: subtract(baseStats.login_failures, delta.login_failures),
        brute_force_attempts: subtract(baseStats.brute_force_attempts, delta.brute_force_attempts),
        blocked_uploads: subtract(baseStats.blocked_uploads, delta.blocked_uploads)
    };
}

function syncSecurityOverviewFromCurrentState() {
    // Recompute overview metrics from the currently filtered in-memory dataset
    // instead of reusing cached totals, otherwise reset can resurrect old counts.
    const fallbackStats = {
        total_events: Array.isArray(state.securityEvents) ? state.securityEvents.length : 0,
        login_failures: Array.isArray(state.securityEvents)
            ? state.securityEvents.filter((event) => String(event && event.event_type || '').toUpperCase() === 'LOGIN_FAIL').length
            : 0,
        brute_force_attempts: Array.isArray(state.securityEvents)
            ? state.securityEvents.filter((event) => String(event && event.event_type || '').toUpperCase() === 'BRUTE_FORCE').length
            : 0,
        blocked_uploads: Array.isArray(state.securityEvents)
            ? state.securityEvents.filter((event) => String(event && event.event_type || '').toUpperCase() === 'FILE_UPLOAD_BLOCKED').length
            : 0,
    };

    renderSecurityCounters(applySimulationResetToStats(state.stats || fallbackStats), false);
    renderIncidentCounters(calculateIncidentMetrics(state.securityIncidents), false);
}

function appendSimulationResetAuditEvent() {
    const actor = String(state.currentUser && state.currentUser.username ? state.currentUser.username : 'system').trim() || 'system';
    const auditEvent = {
        id: `ui-sim-reset-${Date.now()}`,
        timestamp: new Date().toISOString(),
        event_type: 'SIMULATION_RESET',
        severity: 'LOW',
        user_id: Number(state.currentUser && state.currentUser.id) || null,
        username: actor,
        ip_address: null,
        message: 'Simulation feed cleared by user',
        metadata: {
            source: 'ui_simulation_control',
            audit_only: true,
        }
    };

    state.securityEvents = [auditEvent, ...state.securityEvents].slice(0, 5000);
    console.info('Simulation feed cleared by user');
}

function clearSimulationFeedLocally() {
    const currentEvents = Array.isArray(state.securityEvents) ? state.securityEvents : [];
    // Simulation reset is intentionally scoped to transient event streams.
    // Incidents represent tracked security cases and must persist for investigation.
    // Security Overview reflects aggregated/historical metrics and is not cleared by simulation reset.
    state.securityEvents = currentEvents.filter((event) => !isSimulatedSecurityEvent(event));
    renderSecurityEventViews(state.securityEvents, { preserveScroll: true });
    markSecurityEventsFeedUpdated();

    // Clear any legacy tombstone from earlier full-reset behavior to prevent
    // accidental cross-layer filtering after moving to feed-only reset.
    setSimulationResetState(null);
}

async function refreshSecurityUserStatusPanel(options = {}) {
    const animateCounters = Boolean(options.animateCounters);
    const payload = await fetchSecurityUserStatusData();
    renderSecurityUserStatusCounters(payload.summary, animateCounters);
}

async function refreshSecurityEventsFeed(options = {}) {
    const source = String(options.source || 'manual');
    const silent = Boolean(options.silent);
    const force = Boolean(options.force);

    if (!isSecurityCenterView() || state.securityActiveTab !== 'events') {
        return null;
    }

    if (!force && !isSecurityEventsAutoRefreshAllowed()) {
        return null;
    }

    if (state.securityEventsRefreshInProgress) {
        if (source === 'manual' && state.securityEventsRefreshController) {
            state.securityEventsRefreshController.abort();
        } else {
            return null;
        }
    }

    const controller = new AbortController();
    state.securityEventsRefreshController = controller;
    state.securityEventsRefreshInProgress = true;

    const eventsTableWrap = document.querySelector('#security-events-panel .security-events-table-wrap');
    const liveFeedList = document.getElementById('security-live-feed-list');
    const eventsTableScrollTop = preserveElementScrollState(eventsTableWrap);
    const liveFeedScrollTop = preserveElementScrollState(liveFeedList);

    if (source === 'manual') {
        setSecurityEventsRefreshButtonLoading(true);
    }

    try {
        const payload = await fetchSecurityDashboardData(20, { signal: controller.signal });

        if (controller.signal.aborted || state.securityEventsRefreshController !== controller) {
            return null;
        }

        const filtered = filterSimulationPayload(payload.events, state.securityIncidents);
        state.securityEvents = filtered.events;
        state.stats = payload && payload.stats ? normalizeSecurityStats(payload.stats) : state.stats || normalizeSecurityStats({});

        renderSecurityEventViews(state.securityEvents, { preserveScroll: true });
        syncSecurityOverviewFromCurrentState();
        restoreElementScrollState(eventsTableWrap, eventsTableScrollTop);
        restoreElementScrollState(liveFeedList, liveFeedScrollTop);
        markSecurityEventsFeedUpdated();

        return payload;
    } catch (error) {
        if (!controller.signal.aborted && error && error.message !== 'Unauthorized' && !silent) {
            console.error('Security events refresh failed:', error);
        }
        return null;
    } finally {
        if (state.securityEventsRefreshController === controller) {
            state.securityEventsRefreshController = null;
        }
        state.securityEventsRefreshInProgress = false;
        if (source === 'manual') {
            setSecurityEventsRefreshButtonLoading(false);
        }
    }
}

function clearSecurityEventsRefreshTimers() {
    if (state.securityEventsRefreshTimer) {
        clearInterval(state.securityEventsRefreshTimer);
        state.securityEventsRefreshTimer = null;
    }

    if (state.securityEventsLabelTimer) {
        clearInterval(state.securityEventsLabelTimer);
        state.securityEventsLabelTimer = null;
    }
}

function stopSecurityEventsRefreshSystem() {
    clearSecurityEventsRefreshTimers();

    if (state.securityEventsRefreshController) {
        state.securityEventsRefreshController.abort();
        state.securityEventsRefreshController = null;
    }

    state.securityEventsRefreshInProgress = false;
    state.securityEventsLastInteractionAt = 0;
}

function setupSecurityEventsRefreshAction() {
    const refreshButton = document.getElementById('security-events-refresh-btn');
    if (!refreshButton) return;

    if (refreshButton.dataset.refreshBound === 'true') {
        return;
    }

    refreshButton.addEventListener('click', () => {
        markSecurityEventsFeedInteraction();
        refreshSecurityEventsFeed({ source: 'manual', force: true, silent: false }).then((result) => {
            if (!result) {
                showNotification('Unable to refresh security events right now.', 'warning');
            }
        });
    });
    refreshButton.dataset.refreshBound = 'true';
}

function startSecurityEventsRefreshSystem() {
    stopSecurityEventsRefreshSystem();

    if (!isSecurityCenterView() || state.securityActiveTab !== 'events') {
        updateSecurityEventsLastUpdatedLabel();
        return;
    }

    const registerInteraction = () => {
        markSecurityEventsFeedInteraction();
    };

    const eventsPanel = document.getElementById('security-events-panel');
    const liveFeedList = document.getElementById('security-live-feed-list');
    const eventsTableWrap = document.querySelector('#security-events-panel .security-events-table-wrap');

    if (eventsPanel && !eventsPanel.dataset.refreshInteractionBound) {
        eventsPanel.addEventListener('pointerdown', registerInteraction, { passive: true });
        eventsPanel.addEventListener('wheel', registerInteraction, { passive: true });
        eventsPanel.addEventListener('touchstart', registerInteraction, { passive: true });
        eventsPanel.addEventListener('keydown', registerInteraction);
        eventsPanel.dataset.refreshInteractionBound = 'true';
    }

    if (liveFeedList && !liveFeedList.dataset.refreshScrollBound) {
        liveFeedList.addEventListener('scroll', registerInteraction, { passive: true });
        liveFeedList.dataset.refreshScrollBound = 'true';
    }

    if (eventsTableWrap && !eventsTableWrap.dataset.refreshScrollBound) {
        eventsTableWrap.addEventListener('scroll', registerInteraction, { passive: true });
        eventsTableWrap.dataset.refreshScrollBound = 'true';
    }

    updateSecurityEventsLastUpdatedLabel();

    state.securityEventsRefreshTimer = setInterval(() => {
        if (!isSecurityEventsAutoRefreshAllowed()) {
            return;
        }
        refreshSecurityEventsFeed({ source: 'auto', silent: true });
    }, SECURITY_EVENTS_AUTO_REFRESH_MS);

    state.securityEventsLabelTimer = setInterval(() => {
        updateSecurityEventsLastUpdatedLabel();
    }, 5000);

    updateSecurityEventsLastUpdatedLabel();
}

function normalizeIncidentSeverity(severity) {
    const normalized = String(severity || 'MEDIUM').trim().toUpperCase();
    if (normalized === 'HIGH' || normalized === 'LOW') {
        return normalized;
    }
    return 'MEDIUM';
}

function calculateIncidentMetrics(incidents) {
    const items = Array.isArray(incidents) ? incidents : [];

    return items.reduce((acc, incident) => {
        const status = normalizeIncidentStatus(incident && incident.status ? incident.status : 'OPEN');
        const severity = normalizeIncidentSeverity(incident && incident.severity ? incident.severity : 'MEDIUM');

        if (status === 'OPEN') {
            acc.open_incidents += 1;
        }
        if (severity === 'HIGH') {
            acc.high_severity_incidents += 1;
        }

        return acc;
    }, {
        open_incidents: 0,
        high_severity_incidents: 0
    });
}

function renderIncidentCounters(metrics, shouldAnimate = false) {
    const safeMetrics = metrics && typeof metrics === 'object' ? metrics : {};
    const openIncidents = Number.isFinite(Number(safeMetrics.open_incidents))
        ? Number(safeMetrics.open_incidents)
        : 0;
    const highSeverity = Number.isFinite(Number(safeMetrics.high_severity_incidents))
        ? Number(safeMetrics.high_severity_incidents)
        : 0;

    const setCounter = (id, value) => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = Number(value || 0).toLocaleString();
        }
    };

    if (shouldAnimate) {
        animateCounter('security-stat-open-incidents', openIncidents);
        animateCounter('security-stat-high-severity-incidents', highSeverity);
        return;
    }

    setCounter('security-stat-open-incidents', openIncidents);
    setCounter('security-stat-high-severity-incidents', highSeverity);
}

function updateIncidentNewBadge() {
    const badge = document.getElementById('security-incidents-new-badge');
    if (!badge) return;

    const count = Number(state.unseenIncidentCount) || 0;
    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : String(count);
        badge.classList.remove('hidden');
        return;
    }

    badge.textContent = '0';
    badge.classList.add('hidden');
}

function acknowledgeIncidentNewAlerts() {
    state.unseenIncidentCount = 0;
    updateIncidentNewBadge();
}

function detectAndHandleNewIncidents(allIncidents, options = {}) {
    const announceNew = options.announceNew !== false;
    const items = Array.isArray(allIncidents) ? allIncidents : [];
    const incidentIds = items
        .map((incident) => Number(incident && incident.id))
        .filter((id) => Number.isFinite(id) && id > 0);

    const maxId = incidentIds.length > 0 ? Math.max(...incidentIds) : 0;
    if (!state.incidentBaselineInitialized) {
        state.latestIncidentSeenId = maxId;
        state.incidentBaselineInitialized = true;
        updateIncidentNewBadge();
        return;
    }

    if (maxId <= state.latestIncidentSeenId) {
        return;
    }

    const previousMax = state.latestIncidentSeenId;
    state.latestIncidentSeenId = maxId;

    const newCount = items.reduce((count, incident) => {
        const incidentId = Number(incident && incident.id);
        if (!Number.isFinite(incidentId) || incidentId <= previousMax) {
            return count;
        }
        return count + 1;
    }, 0);

    if (newCount <= 0) {
        return;
    }

    if (state.securityActiveTab === 'incidents') {
        acknowledgeIncidentNewAlerts();
    } else {
        state.unseenIncidentCount += newCount;
        updateIncidentNewBadge();
    }

    if (announceNew) {
        const t = getSecurityCenterTranslations();
        const message = newCount === 1
            ? (t.incident_new_alert_single || 'New incident detected')
            : `${newCount} ${t.incident_new_alert_multiple || 'new incidents detected'}`;
        showNotification(message, 'warning');
    }
}

async function refreshIncidentOverview(options = {}) {
    const announceNew = options.announceNew !== false;
    const animateCounters = Boolean(options.animateCounters);
    const incidentsPayload = await fetchSecurityJson('/incidents');
    const allIncidents = Array.isArray(incidentsPayload) ? incidentsPayload : [];
    const filtered = filterSimulationPayload([], allIncidents);

    renderIncidentCounters(calculateIncidentMetrics(filtered.incidents), animateCounters);
    detectAndHandleNewIncidents(filtered.incidents, { announceNew });
}

function normalizeIncidentStatus(status) {
    const normalized = String(status || '').trim().toUpperCase();
    if (normalized === 'INVESTIGATING' || normalized === 'RESOLVED' || normalized === 'CLOSED') {
        return normalized;
    }
    return 'OPEN';
}

function getIncidentStatusLabel(status) {
    const t = getSecurityCenterTranslations();
    const normalized = normalizeIncidentStatus(status);
    const keyMap = {
        OPEN: 'incident_status_open',
        INVESTIGATING: 'incident_status_investigating',
        RESOLVED: 'incident_status_resolved',
        CLOSED: 'incident_status_closed'
    };

    return t[keyMap[normalized]] || normalized;
}

function getIncidentStatusClass(status) {
    const normalized = normalizeIncidentStatus(status).toLowerCase();
    return `incident-status-${normalized}`;
}

function isIncidentFalsePositive(value) {
    if (typeof value === 'boolean') {
        return value;
    }

    const normalized = String(value || '').trim().toLowerCase();
    return normalized === 'true' || normalized === '1' || normalized === 'yes';
}

function getIncidentFalsePositiveLabel(value) {
    const t = getSecurityCenterTranslations();
    return isIncidentFalsePositive(value)
        ? (t.incident_false_positive_yes || 'Yes')
        : (t.incident_false_positive_no || 'No');
}

function renderIncidentFalsePositiveBadge(value) {
    const isTrue = isIncidentFalsePositive(value);
    const badgeClass = isTrue ? 'incident-fp-yes' : 'incident-fp-no';
    return `<span class="incident-fp-badge ${badgeClass}">${escapeHtml(getIncidentFalsePositiveLabel(isTrue))}</span>`;
}

function extractIncidentActorLabel(incident) {
    const username = String(incident && incident.actor_username ? incident.actor_username : '').trim();
    if (username) {
        return username;
    }

    const actorId = Number(incident && incident.actor_id);
    if (Number.isFinite(actorId) && actorId > 0) {
        return `user_${actorId}`;
    }

    return getSecurityCenterTranslations().incident_actor_unknown || 'Unknown';
}

function setSecurityActiveTab(tabName, options = {}) {
    const normalizedTab = tabName === 'incidents' ? 'incidents' : 'events';
    const shouldScrollIntoView = Boolean(options && options.scrollIntoView);
    state.securityActiveTab = normalizedTab;

    const eventsTablePanel = document.getElementById('security-events-table-panel');
    const eventsPanel = document.getElementById('security-events-panel');
    const incidentsTablePanel = document.getElementById('security-incidents-table-panel');
    const incidentsPanel = document.getElementById('security-incidents-panel');
    if (eventsTablePanel) {
        eventsTablePanel.classList.toggle('hidden', normalizedTab !== 'events');
    }
    if (eventsPanel) {
        eventsPanel.classList.toggle('hidden', normalizedTab !== 'events');
    }
    if (incidentsTablePanel) {
        incidentsTablePanel.classList.toggle('hidden', normalizedTab !== 'incidents');
    }
    if (incidentsPanel) {
        incidentsPanel.classList.toggle('hidden', normalizedTab !== 'incidents');
    }

    document.querySelectorAll('.security-tab-btn').forEach((button) => {
        button.classList.toggle('is-active', button.dataset.tab === normalizedTab);
    });

    if (normalizedTab === 'incidents') {
        acknowledgeIncidentNewAlerts();
    }

    if (normalizedTab === 'events') {
        setupSecurityEventsRefreshAction();
        startSecurityEventsRefreshSystem();
        refreshSecurityEventsFeed({ source: 'manual', force: true, silent: true });
    } else {
        stopSecurityEventsRefreshSystem();
    }

    if (shouldScrollIntoView) {
        const targetPanel = normalizedTab === 'incidents' ? incidentsPanel : eventsPanel;
        const eventsTableTop = normalizedTab === 'events' ? eventsTablePanel : null;
        const incidentsTableTop = normalizedTab === 'incidents' ? incidentsTablePanel : null;
        const targetCard = targetPanel && normalizedTab !== 'incidents'
            ? targetPanel.querySelector('.security-events-card')
            : null;
        const scrollTarget = incidentsTableTop || eventsTableTop || targetCard || targetPanel;
        if (scrollTarget && typeof scrollTarget.scrollIntoView === 'function') {
            scrollTarget.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    updateIncidentBackToEventsFloatingButtonVisibility();
}

function setupSecurityCenterTabs() {
    const tabButtons = document.querySelectorAll('.security-tab-btn');
    tabButtons.forEach((button) => {
        button.onclick = () => {
            setSecurityActiveTab(button.dataset.tab || 'events', { scrollIntoView: true });
        };
    });

    setSecurityActiveTab(state.securityActiveTab, { scrollIntoView: false });
}

function renderSecurityIncidentsTable(incidents) {
    const tableBody = document.getElementById('security-incidents-body');
    if (!tableBody) return;
    const t = getSecurityCenterTranslations();

    syncSecurityStickyFirstRowOffset(tableBody);

    const items = Array.isArray(incidents) ? [...incidents] : [];
    items.sort((left, right) => {
        const rightTs = getSortTimestampValue(right && right.created_at ? right.created_at : '');
        const leftTs = getSortTimestampValue(left && left.created_at ? left.created_at : '');
        if (rightTs !== leftTs) {
            return rightTs - leftTs;
        }

        const rightId = Number(right && right.id);
        const leftId = Number(left && left.id);
        const safeRightId = Number.isFinite(rightId) ? rightId : 0;
        const safeLeftId = Number.isFinite(leftId) ? leftId : 0;
        return safeRightId - safeLeftId;
    });

    if (items.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="security-empty-row">${escapeHtml(t.incident_empty)}</td></tr>`;
        scrollSecurityTableToTop(tableBody);
        return;
    }

    tableBody.innerHTML = items.map((incident) => {
        const incidentId = Number(incident && incident.id);
        const typeLabel = String(incident && incident.type ? incident.type : '-');
        const severity = String(incident && incident.severity ? incident.severity : 'MEDIUM').toUpperCase();
        const status = normalizeIncidentStatus(incident && incident.status ? incident.status : 'OPEN');
        const isFalsePositive = isIncidentFalsePositive(incident && incident.is_false_positive);
        const createdAt = formatLocaleDateTime(
            incident && incident.created_at ? incident.created_at : null,
            'en-US'
        );
        const severityClass = getSecuritySeverityClass(severity);
        const statusClass = getIncidentStatusClass(status);
        const selectedIncidentId = Number(state.selectedIncident && state.selectedIncident.id);
        const selectedClass = incidentId === selectedIncidentId ? 'is-selected' : '';

        return `
            <tr class="security-incident-row ${selectedClass}" data-incident-id="${incidentId}">
                <td>#${escapeHtml(String(incidentId))}</td>
                <td>${escapeHtml(typeLabel)}</td>
                <td><span class="security-severity ${severityClass}">${escapeHtml(severity)}</span></td>
                <td><span class="incident-status-pill ${statusClass}">${escapeHtml(getIncidentStatusLabel(status))}</span></td>
                <td>${renderIncidentFalsePositiveBadge(isFalsePositive)}</td>
                <td class="security-col-time">${escapeHtml(createdAt)}</td>
            </tr>
        `;
    }).join('');

    scrollSecurityTableToTop(tableBody);
}

function renderSecurityEventViews(events, options = {}) {
    // Keep table and live-feed rendering in one place so rebase-era fixes do not
    // drift between the initial load, SSE updates, and simulation reset paths.
    renderSecurityEventsTable(events, options);
    renderSecurityLiveFeed(events);
}

function getSelectedIncidentId() {
    const incidentId = Number(state.selectedIncident && state.selectedIncident.id);
    if (!Number.isFinite(incidentId) || incidentId <= 0) {
        return null;
    }
    return incidentId;
}

function clearIncidentDetailsCloseTimer() {
    if (!state.incidentDetailsCloseTimer) return;
    clearTimeout(state.incidentDetailsCloseTimer);
    state.incidentDetailsCloseTimer = null;
}

function showIncidentDetailsPanel(detailsPanel) {
    if (!detailsPanel || !state.selectedIncident) return;

    clearIncidentDetailsCloseTimer();
    detailsPanel.classList.remove('hidden', 'is-closing');
    detailsPanel.scrollTop = 0;

    requestAnimationFrame(() => {
        detailsPanel.classList.add('is-open');
        detailsPanel.setAttribute('aria-hidden', 'false');
    });
}

function hideIncidentDetailsPanel(detailsPanel) {
    if (!detailsPanel) return;

    clearIncidentDetailsCloseTimer();

    const alreadyHidden = detailsPanel.classList.contains('hidden') && !detailsPanel.classList.contains('is-open');
    if (alreadyHidden) {
        detailsPanel.setAttribute('aria-hidden', 'true');
        return;
    }

    detailsPanel.classList.remove('is-open');
    detailsPanel.classList.add('is-closing');
    detailsPanel.setAttribute('aria-hidden', 'true');

    state.incidentDetailsCloseTimer = setTimeout(() => {
        detailsPanel.classList.add('hidden');
        detailsPanel.classList.remove('is-closing');
        state.incidentDetailsCloseTimer = null;
    }, INCIDENT_PANEL_CLOSE_ANIMATION_MS);
}

function clearIncidentDetailsPanel(options = {}) {
    const rerenderIncidents = options.rerenderIncidents !== false;
    state.incidentDetailsRequestToken += 1;
    state.selectedIncident = null;

    const detailsPanel = document.getElementById('incident-details-panel');
    if (detailsPanel) {
        hideIncidentDetailsPanel(detailsPanel);
    }

    const timeline = document.getElementById('incident-timeline-list');
    if (timeline) {
        timeline.innerHTML = `<li class="incident-timeline-empty">${escapeHtml(getSecurityCenterTranslations().incident_timeline_empty)}</li>`;
    }

    const detailsFalsePositive = document.getElementById('incident-details-false-positive');
    if (detailsFalsePositive) {
        detailsFalsePositive.textContent = '-';
    }

    const notesInput = document.getElementById('incident-notes-input');
    if (notesInput) {
        notesInput.value = '';
    }

    syncIncidentActionButtons(null);
    if (rerenderIncidents) {
        renderSecurityIncidentsTable(state.securityIncidents);
    }
    updateIncidentBackToEventsFloatingButtonVisibility();
}

function syncIncidentActionButtons(incident) {
    const assignBtn = document.getElementById('incident-assign-btn');
    const investigatingBtn = document.getElementById('incident-mark-investigating-btn');
    const resolveBtn = document.getElementById('incident-resolve-btn');
    const closeBtn = document.getElementById('incident-close-btn');
    const markFalsePositiveBtn = document.getElementById('incident-mark-false-positive-btn');
    const clearFalsePositiveBtn = document.getElementById('incident-clear-false-positive-btn');
    const saveNotesBtn = document.getElementById('incident-save-notes-btn');
    const blockBtn = document.getElementById('incident-block-user-btn');
    const suspendBtn = document.getElementById('incident-suspend-user-btn');
    const reactivateBtn = document.getElementById('incident-reactivate-user-btn');
    const ignoreBtn = document.getElementById('incident-ignore-btn');

    const allButtons = [
        assignBtn,
        investigatingBtn,
        resolveBtn,
        closeBtn,
        markFalsePositiveBtn,
        clearFalsePositiveBtn,
        saveNotesBtn,
        blockBtn,
        suspendBtn,
        reactivateBtn,
        ignoreBtn
    ].filter(Boolean);

    if (!incident) {
        allButtons.forEach((button) => {
            button.disabled = true;
        });
        return;
    }

    const currentStatus = normalizeIncidentStatus(incident.status);
    const hasActor = Number.isFinite(Number(incident.actor_id)) && Number(incident.actor_id) > 0;
    const falsePositive = isIncidentFalsePositive(incident.is_false_positive);

    if (assignBtn) assignBtn.disabled = false;
    if (investigatingBtn) investigatingBtn.disabled = currentStatus !== 'OPEN';
    if (resolveBtn) resolveBtn.disabled = currentStatus !== 'INVESTIGATING';
    if (closeBtn) closeBtn.disabled = currentStatus !== 'RESOLVED';
    if (markFalsePositiveBtn) markFalsePositiveBtn.disabled = falsePositive;
    if (clearFalsePositiveBtn) clearFalsePositiveBtn.disabled = !falsePositive;
    if (saveNotesBtn) saveNotesBtn.disabled = false;
    if (blockBtn) blockBtn.disabled = !hasActor;
    if (suspendBtn) suspendBtn.disabled = !hasActor;
    if (reactivateBtn) reactivateBtn.disabled = !hasActor;
    if (ignoreBtn) ignoreBtn.disabled = false;
}

function getIncidentLogResult(entry) {
    const metadata = entry && typeof entry.extra_metadata === 'object' && !Array.isArray(entry.extra_metadata)
        ? entry.extra_metadata
        : {};
    const explicitResult = String(
        entry && entry.result ? entry.result : (metadata.result || '')
    ).trim().toLowerCase();

    if (["failed", "failure", "error", "denied", "blocked", "false"].includes(explicitResult)) {
        return 'FAILED';
    }

    if (["success", "ok", "succeeded", "passed", "true"].includes(explicitResult)) {
        return 'SUCCESS';
    }

    const action = String(entry && entry.event_type ? entry.event_type : '').toUpperCase();
    if (/(FAIL|DENY|ERROR|INVALID)/.test(action)) {
        return 'FAILED';
    }

    return 'SUCCESS';
}

function formatIncidentLogMetadata(entry) {
    const metadata = entry && typeof entry.extra_metadata === 'object' && !Array.isArray(entry.extra_metadata)
        ? entry.extra_metadata
        : {};

    if (Object.keys(metadata).length === 0) {
        return '-';
    }

    return JSON.stringify(metadata, null, 2);
}

function getIncidentLogResultLabel(result) {
    const t = getSecurityCenterTranslations();
    if (result === 'FAILED') {
        return t.incident_result_failed || 'Failed';
    }
    return t.incident_result_success || 'Success';
}

function renderIncidentTimeline(logs) {
    const timeline = document.getElementById('incident-timeline-list');
    if (!timeline) return;
    const t = getSecurityCenterTranslations();

    const items = Array.isArray(logs) ? logs : [];
    if (items.length === 0) {
        timeline.innerHTML = `<li class="incident-timeline-empty">${escapeHtml(t.incident_timeline_empty)}</li>`;
        return;
    }

    const orderedItems = [...items].sort((a, b) => {
        const left = Date.parse(a && a.created_at ? a.created_at : '');
        const right = Date.parse(b && b.created_at ? b.created_at : '');
        const leftValue = Number.isFinite(left) ? left : 0;
        const rightValue = Number.isFinite(right) ? right : 0;
        return leftValue - rightValue;
    });

    timeline.innerHTML = orderedItems.map((entry) => {
        const action = String(entry && entry.event_type ? entry.event_type : 'LOG').toUpperCase();
        const timestamp = formatLocaleDateTime(entry && entry.created_at ? entry.created_at : null);
        const result = getIncidentLogResult(entry);
        const resultClass = result === 'FAILED' ? 'failed' : 'success';
        const resultLabel = getIncidentLogResultLabel(result);
        const metadataText = formatIncidentLogMetadata(entry);

        return `
            <li class="incident-timeline-item">
                <div class="incident-timeline-field">
                    <span class="incident-timeline-label">${escapeHtml(t.incident_timeline_timestamp || 'Timestamp')}</span>
                    <span class="incident-timeline-value">${escapeHtml(timestamp)}</span>
                </div>
                <div class="incident-timeline-field">
                    <span class="incident-timeline-label">${escapeHtml(t.incident_timeline_action || 'Action')}</span>
                    <span class="incident-timeline-value incident-timeline-action">${escapeHtml(action)}</span>
                </div>
                <div class="incident-timeline-field">
                    <span class="incident-timeline-label">${escapeHtml(t.incident_timeline_result || 'Result')}</span>
                    <span class="incident-log-result-badge ${resultClass}">${escapeHtml(resultLabel)}</span>
                </div>
                <div class="incident-timeline-field incident-timeline-field-wide">
                    <span class="incident-timeline-label">${escapeHtml(t.incident_timeline_metadata || 'Metadata')}</span>
                    <pre class="incident-timeline-metadata">${escapeHtml(metadataText)}</pre>
                </div>
            </li>
        `;
    }).join('');
}

function renderIncidentDetails(incident) {
    const detailsPanel = document.getElementById('incident-details-panel');
    if (!detailsPanel || !incident) return;

    const detailsId = document.getElementById('incident-details-id');
    const detailsType = document.getElementById('incident-details-type');
    const detailsSeverity = document.getElementById('incident-details-severity');
    const detailsStatus = document.getElementById('incident-details-status');
    const detailsFalsePositive = document.getElementById('incident-details-false-positive');
    const detailsCreatedAt = document.getElementById('incident-details-created-at');
    const actorInfo = document.getElementById('incident-actor-info');
    const notesInput = document.getElementById('incident-notes-input');

    const severity = String(incident.severity || 'MEDIUM').toUpperCase();
    const severityClass = getSecuritySeverityClass(severity);
    const status = normalizeIncidentStatus(incident.status || 'OPEN');
    const statusClass = getIncidentStatusClass(status);
    const falsePositive = isIncidentFalsePositive(incident.is_false_positive);
    const actorLabel = extractIncidentActorLabel(incident);
    const assigneeLabel = String(incident.assigned_to_username || '').trim() || '-';
    const createdByLabel = String(incident.created_by || '').trim() || 'system';
    const t = getSecurityCenterTranslations();

    if (detailsId) detailsId.textContent = `#${incident.id}`;
    if (detailsType) detailsType.textContent = String(incident.type || '-');
    if (detailsSeverity) {
        detailsSeverity.innerHTML = `<span class="security-severity ${severityClass}">${escapeHtml(severity)}</span>`;
    }
    if (detailsStatus) {
        detailsStatus.innerHTML = `<span class="incident-status-pill ${statusClass}">${escapeHtml(getIncidentStatusLabel(status))}</span>`;
    }
    if (detailsFalsePositive) {
        detailsFalsePositive.innerHTML = renderIncidentFalsePositiveBadge(falsePositive);
    }
    if (detailsCreatedAt) detailsCreatedAt.textContent = formatLocaleDateTime(incident.created_at);
    if (notesInput) {
        notesInput.value = String(incident && incident.notes ? incident.notes : '');
        notesInput.placeholder = t.incident_notes_placeholder || 'Add investigation notes...';
    }

    if (actorInfo) {
        actorInfo.textContent = `${t.incident_actor_label || 'Actor'}: ${actorLabel} | ${t.incident_assigned_label || 'Assigned'}: ${assigneeLabel} | ${t.incident_created_by_label || 'Created by'}: ${createdByLabel} | ${t.incident_false_positive_label || 'False Positive'}: ${getIncidentFalsePositiveLabel(falsePositive)}`;
    }

    renderIncidentTimeline(incident.logs || []);
    syncIncidentActionButtons(incident);
    showIncidentDetailsPanel(detailsPanel);
    updateIncidentBackToEventsFloatingButtonVisibility();
}

async function openIncidentDetails(incidentId, options = {}) {
    const numericId = Number(incidentId);
    if (!Number.isFinite(numericId) || numericId <= 0) return null;

    const silent = Boolean(options && options.silent);
    const shouldScrollIntoView = Boolean(options && options.scrollIntoView);
    const requestToken = state.incidentDetailsRequestToken + 1;
    state.incidentDetailsRequestToken = requestToken;

    state.selectedIncident = { id: numericId };
    renderSecurityIncidentsTable(state.securityIncidents);

    try {
        const details = await api.get(`/incidents/${numericId}`);

        if (state.incidentDetailsRequestToken !== requestToken) {
            return null;
        }

        if (getSelectedIncidentId() !== numericId) {
            return null;
        }

        state.selectedIncident = details;
        renderSecurityIncidentsTable(state.securityIncidents);
        renderIncidentDetails(details);

        if (shouldScrollIntoView) {
            const detailsPanel = document.getElementById('incident-details-panel');
            if (detailsPanel && typeof detailsPanel.scrollIntoView === 'function') {
                detailsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
                requestAnimationFrame(() => {
                    updateIncidentBackToEventsFloatingButtonVisibility();
                });
            }
        }

        return details;
    } catch (error) {
        console.error('Incident details load error:', error);
        clearIncidentDetailsPanel({ rerenderIncidents: true });
        if (!silent && error.message !== 'Unauthorized') {
            showNotification(getSecurityCenterTranslations().incident_load_error, 'warning');
        }
        return null;
    }
}

async function loadSecurityIncidents(options = {}) {
    const keepSelected = options.keepSelected !== false;
    const refreshOverview = options.refreshOverview !== false;
    const animateIncidentCounters = options.animateIncidentCounters === true;
    const announceNew = options.announceNew === true;
    const forceRefresh = options.forceRefresh === true;
    const statusFilter = document.getElementById('incident-filter-status');
    const severityFilter = document.getElementById('incident-filter-severity');
    const falsePositiveFilter = document.getElementById('incident-filter-false-positive');
    const query = new URLSearchParams();

    if (statusFilter && statusFilter.value) {
        query.set('status', String(statusFilter.value).trim().toUpperCase());
    }
    if (severityFilter && severityFilter.value) {
        query.set('severity', String(severityFilter.value).trim().toUpperCase());
    }
    if (falsePositiveFilter && falsePositiveFilter.value !== '') {
        query.set('false_positive', falsePositiveFilter.value === 'true' ? 'true' : 'false');
    }
    if (forceRefresh) {
        query.set('_ts', String(Date.now()));
    }

    const queryString = query.toString();
    const endpoint = queryString ? `/incidents?${queryString}` : '/incidents';
    const incidents = await api.get(endpoint);
    const filtered = filterSimulationPayload([], incidents);

    state.securityIncidents = Array.isArray(filtered.incidents) ? filtered.incidents : [];
    renderSecurityIncidentsTable(state.securityIncidents);

    if (!keepSelected) {
        clearIncidentDetailsPanel({ rerenderIncidents: true });
    } else {
        const selectedId = getSelectedIncidentId();
        if (Number.isFinite(selectedId) && selectedId > 0) {
            const exists = state.securityIncidents.some((item) => Number(item && item.id) === selectedId);
            if (exists) {
                await openIncidentDetails(selectedId, { silent: true });
            } else {
                clearIncidentDetailsPanel({ rerenderIncidents: true });
            }
        }
    }

    if (refreshOverview) {
        await refreshIncidentOverview({
            announceNew,
            animateCounters: animateIncidentCounters,
        }).catch((error) => {
            console.error('Incident overview refresh error:', error);
        });
    }
}

function setupIncidentFilters() {
    const filterToggleBtn = document.getElementById('incident-filter-toggle');
    const filterToggleArrow = document.getElementById('incident-filter-toggle-arrow');
    const filterContent = document.getElementById('incident-filter-content');
    const statusFilter = document.getElementById('incident-filter-status');
    const severityFilter = document.getElementById('incident-filter-severity');
    const falsePositiveFilter = document.getElementById('incident-filter-false-positive');
    const refreshBtn = document.getElementById('incident-filter-refresh');
    const refreshBtnIcon = refreshBtn ? refreshBtn.querySelector('i') : null;
    const defaultRefreshIconClass = refreshBtnIcon ? refreshBtnIcon.className : '';

    cleanupIncidentBackToEventsFloatingButton();

    const setFilterPanelExpanded = (isExpanded) => {
        if (!filterToggleBtn || !filterContent) return;

        filterContent.classList.toggle('is-collapsed', !isExpanded);
        filterToggleBtn.classList.toggle('is-expanded', isExpanded);
        filterToggleBtn.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');

        if (filterToggleArrow) {
            filterToggleArrow.textContent = isExpanded ? '▼' : '▶';
        }
    };

    if (filterToggleBtn && filterContent) {
        const startExpanded = filterToggleBtn.getAttribute('aria-expanded') === 'true';
        setFilterPanelExpanded(startExpanded);

        filterToggleBtn.onclick = () => {
            const expanded = filterToggleBtn.getAttribute('aria-expanded') === 'true';
            setFilterPanelExpanded(!expanded);
        };
    }

    const setRefreshLoading = (isLoading) => {
        if (!refreshBtn) return;
        refreshBtn.disabled = isLoading;
        if (refreshBtnIcon) {
            refreshBtnIcon.className = isLoading
                ? 'fas fa-spinner fa-spin'
                : defaultRefreshIconClass;
        }
    };

    const runLoad = async (options = {}) => {
        const triggeredByButton = options.triggeredByButton === true;
        const forceRefresh = options.forceRefresh === true;
        const t = getSecurityCenterTranslations();

        if (triggeredByButton) {
            setRefreshLoading(true);
        }

        try {
            await loadSecurityIncidents({
                keepSelected: true,
                forceRefresh,
                refreshOverview: true,
                announceNew: false,
            });

            if (triggeredByButton) {
                showNotification(
                    t.incident_refresh_success || 'Incidents refreshed',
                    'info'
                );
            }
        } catch (error) {
            console.error('Incident filter load error:', error);
            if (error && error.message !== 'Unauthorized') {
                showNotification(t.incident_load_error || 'Failed to load incidents', 'warning');
            }
        } finally {
            if (triggeredByButton) {
                setRefreshLoading(false);
            }
        }
    };

    if (statusFilter) {
        statusFilter.onchange = () => runLoad();
    }
    if (severityFilter) {
        severityFilter.onchange = () => runLoad();
    }
    if (falsePositiveFilter) {
        falsePositiveFilter.onchange = () => runLoad();
    }
    if (refreshBtn) {
        refreshBtn.onclick = () => runLoad({ triggeredByButton: true, forceRefresh: true });
    }

    setupIncidentBackToEventsFloatingButton();
}

function setupIncidentTableInteraction() {
    const incidentsBody = document.getElementById('security-incidents-body');
    if (!incidentsBody) return;

    incidentsBody.onclick = (event) => {
        const row = event.target.closest('tr[data-incident-id]');
        if (!row) return;
        const incidentId = Number(row.dataset.incidentId);

        const selectedId = getSelectedIncidentId();
        if (selectedId !== null && incidentId === selectedId) {
            clearIncidentDetailsPanel({ rerenderIncidents: true });
            return;
        }

        openIncidentDetails(incidentId);
    };
}

function cleanupIncidentDetailsDismissActions() {
    clearIncidentDetailsCloseTimer();

    const closeBtn = document.getElementById('incident-details-close-btn');
    if (closeBtn) {
        closeBtn.onclick = null;
    }

    if (state.incidentPanelOutsideClickHandler) {
        document.removeEventListener('pointerdown', state.incidentPanelOutsideClickHandler);
        state.incidentPanelOutsideClickHandler = null;
    }

    if (state.incidentPanelKeydownHandler) {
        document.removeEventListener('keydown', state.incidentPanelKeydownHandler);
        state.incidentPanelKeydownHandler = null;
    }
}

function setupIncidentDetailsDismissActions() {
    cleanupIncidentDetailsDismissActions();

    const detailsPanel = document.getElementById('incident-details-panel');
    const closeBtn = document.getElementById('incident-details-close-btn');
    if (!detailsPanel) return;

    if (closeBtn) {
        closeBtn.onclick = () => {
            clearIncidentDetailsPanel({ rerenderIncidents: true });
        };
    }

    const outsideClickHandler = (event) => {
        const panelOpen = Boolean(
            isSecurityCenterView()
            && state.securityActiveTab === 'incidents'
            && state.selectedIncident
            && detailsPanel.classList.contains('is-open')
            && !detailsPanel.classList.contains('hidden')
        );
        if (!panelOpen) return;

        const target = event.target;
        if (target instanceof Element && detailsPanel.contains(target)) {
            return;
        }
        if (target instanceof Element && target.closest('#security-incidents-body tr[data-incident-id]')) {
            return;
        }

        clearIncidentDetailsPanel({ rerenderIncidents: true });
    };

    const keydownHandler = (event) => {
        if (event.key !== 'Escape') return;
        if (!isSecurityCenterView()) return;
        if (state.securityActiveTab !== 'incidents') return;
        if (!state.selectedIncident) return;

        clearIncidentDetailsPanel({ rerenderIncidents: true });
    };

    state.incidentPanelOutsideClickHandler = outsideClickHandler;
    state.incidentPanelKeydownHandler = keydownHandler;

    document.addEventListener('pointerdown', outsideClickHandler);
    document.addEventListener('keydown', keydownHandler);
}

function setupIncidentActionHandlers() {
    const assignBtn = document.getElementById('incident-assign-btn');
    const investigatingBtn = document.getElementById('incident-mark-investigating-btn');
    const resolveBtn = document.getElementById('incident-resolve-btn');
    const closeBtn = document.getElementById('incident-close-btn');
    const markFalsePositiveBtn = document.getElementById('incident-mark-false-positive-btn');
    const clearFalsePositiveBtn = document.getElementById('incident-clear-false-positive-btn');
    const saveNotesBtn = document.getElementById('incident-save-notes-btn');
    const notesInput = document.getElementById('incident-notes-input');
    const blockBtn = document.getElementById('incident-block-user-btn');
    const suspendBtn = document.getElementById('incident-suspend-user-btn');
    const reactivateBtn = document.getElementById('incident-reactivate-user-btn');
    const ignoreBtn = document.getElementById('incident-ignore-btn');
    const actionReasonInput = document.getElementById('incident-action-reason-input');
    const suspendMinutesInput = document.getElementById('incident-suspend-minutes-input');
    const t = getSecurityCenterTranslations();

    const resolveSelectedIncidentId = () => {
        const incidentId = getSelectedIncidentId();
        if (!Number.isFinite(incidentId) || incidentId <= 0) {
            showNotification(t.incident_select_first, 'warning');
            return null;
        }
        return incidentId;
    };

    const runAction = async (executor, successMessage) => {
        const incidentId = resolveSelectedIncidentId();
        if (!incidentId) return;

        const buttons = Array.from(document.querySelectorAll('.incident-action-btn'));
        buttons.forEach((button) => {
            button.disabled = true;
        });

        try {
            await executor(incidentId);
            showNotification(successMessage, 'success');
            await loadSecurityIncidents({ keepSelected: true });
            await openIncidentDetails(incidentId, { silent: true });
        } catch (error) {
            console.error('Incident action error:', error);
        } finally {
            syncIncidentActionButtons(state.selectedIncident);
        }
    };

    const parseActionReason = () => {
        const reason = String(actionReasonInput && actionReasonInput.value ? actionReasonInput.value : '').trim();
        if (reason.length < 3) {
            showNotification(t.incident_action_reason_required || 'Reason is required for this action', 'warning');
            return null;
        }
        return reason;
    };

    const parseSuspendMinutes = () => {
        const value = Number(suspendMinutesInput && suspendMinutesInput.value);
        if (!Number.isInteger(value) || value < 1 || value > 10080) {
            showNotification(
                t.incident_action_suspend_minutes_invalid || 'Suspend duration must be between 1 and 10080 minutes',
                'warning'
            );
            return null;
        }
        return value;
    };

    if (assignBtn) {
        assignBtn.onclick = async () => {
            await runAction(
                (incidentId) => api.post(`/incidents/${incidentId}/assign`, {}),
                t.incident_action_assign_success
            );
        };
    }

    if (investigatingBtn) {
        investigatingBtn.onclick = async () => {
            await runAction(
                (incidentId) => api.patch(`/incidents/${incidentId}`, { status: 'INVESTIGATING' }),
                t.incident_action_status_success
            );
        };
    }

    if (resolveBtn) {
        resolveBtn.onclick = async () => {
            await runAction(
                (incidentId) => api.patch(`/incidents/${incidentId}`, { status: 'RESOLVED' }),
                t.incident_action_status_success
            );
        };
    }

    if (closeBtn) {
        closeBtn.onclick = async () => {
            await runAction(
                (incidentId) => api.patch(`/incidents/${incidentId}`, { status: 'CLOSED' }),
                t.incident_action_status_success
            );
        };
    }

    if (saveNotesBtn) {
        saveNotesBtn.onclick = async () => {
            await runAction(
                (incidentId) => api.patch(`/incidents/${incidentId}/notes`, {
                    notes: notesInput ? notesInput.value : '',
                    metadata: {
                        reason: 'manual investigation notes update'
                    }
                }),
                t.incident_notes_saved
            );
        };
    }

    if (markFalsePositiveBtn) {
        markFalsePositiveBtn.onclick = async () => {
            await runAction(
                (incidentId) => api.patch(`/incidents/${incidentId}/false-positive`, {
                    is_false_positive: true,
                    metadata: {
                        reason: 'marked false positive by analyst'
                    }
                }),
                t.incident_false_positive_marked
            );
        };
    }

    if (clearFalsePositiveBtn) {
        clearFalsePositiveBtn.onclick = async () => {
            await runAction(
                (incidentId) => api.patch(`/incidents/${incidentId}/false-positive`, {
                    is_false_positive: false,
                    metadata: {
                        reason: 'false positive cleared by analyst'
                    }
                }),
                t.incident_false_positive_cleared
            );
        };
    }

    if (blockBtn) {
        blockBtn.onclick = async () => {
            const reason = parseActionReason();
            if (!reason) return;

            await runAction(
                (incidentId) => api.post(`/incidents/${incidentId}/action`, {
                    action_type: 'block_user',
                    metadata: { reason }
                }),
                t.incident_action_apply_success
            );
        };
    }

    if (suspendBtn) {
        suspendBtn.onclick = async () => {
            const reason = parseActionReason();
            if (!reason) return;

            const suspensionMinutes = parseSuspendMinutes();
            if (!suspensionMinutes) return;

            await runAction(
                (incidentId) => api.post(`/incidents/${incidentId}/action`, {
                    action_type: 'suspend_user',
                    metadata: {
                        reason,
                        suspension_minutes: suspensionMinutes
                    }
                }),
                t.incident_action_apply_success
            );
        };
    }

    if (reactivateBtn) {
        reactivateBtn.onclick = async () => {
            const reason = parseActionReason();
            if (!reason) return;

            await runAction(
                (incidentId) => api.post(`/incidents/${incidentId}/action`, {
                    action_type: 'reactivate_user',
                    metadata: { reason }
                }),
                t.incident_action_reactivate_success
            );
        };
    }

    if (ignoreBtn) {
        ignoreBtn.onclick = async () => {
            const reason = parseActionReason();
            if (!reason) return;

            await runAction(
                (incidentId) => api.post(`/incidents/${incidentId}/action`, {
                    action_type: 'ignore',
                    metadata: { reason }
                }),
                t.incident_false_positive_marked
            );
        };
    }

    syncIncidentActionButtons(null);
}

function buildSecurityExportFilename() {
    const now = new Date();
    const pad = (value) => String(value).padStart(2, '0');
    const datePart = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}`;
    const timePart = `${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
    return `security-events-${datePart}_${timePart}.csv`;
}

function extractDownloadFilenameFromResponse(response) {
    const disposition = String(response && response.headers ? (response.headers.get('Content-Disposition') || '') : '').trim();
    if (!disposition) return '';

    const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
    if (utf8Match && utf8Match[1]) {
        try {
            return decodeURIComponent(String(utf8Match[1]).replace(/"/g, '').trim());
        } catch (_) {
            // Fall back to plain filename parsing.
        }
    }

    const plainMatch = disposition.match(/filename="?([^";]+)"?/i);
    if (plainMatch && plainMatch[1]) {
        return String(plainMatch[1]).trim();
    }

    return '';
}

function downloadBlobAsFile(blob, filename) {
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = objectUrl;
    anchor.download = filename;
    anchor.style.display = 'none';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();

    setTimeout(() => {
        URL.revokeObjectURL(objectUrl);
    }, 0);
}

function setupSecurityExportAction() {
    const exportButtons = [
        document.getElementById('security-export-logs-btn'),
        document.getElementById('security-events-export-btn')
    ].filter(Boolean);

    if (exportButtons.length === 0) return;

    exportButtons.forEach((button) => {
        const icon = button.querySelector('i');
        if (icon && !icon.dataset.defaultIconClass) {
            icon.dataset.defaultIconClass = icon.className;
        }
    });

    const setLoadingState = (isLoading) => {
        exportButtons.forEach((button) => {
            button.disabled = isLoading;
            button.classList.toggle('is-loading', isLoading);

            const icon = button.querySelector('i');
            if (!icon) return;

            const defaultClass = icon.dataset.defaultIconClass || 'fas fa-file-arrow-down';
            icon.className = isLoading ? 'fas fa-spinner fa-spin' : defaultClass;
        });
    };

    const runExport = async () => {
        if (exportButtons.some((button) => button.disabled)) return;

        setLoadingState(true);
        try {
            const response = await fetchWithApiRecovery('/security/events/export?limit=5000', {
                method: 'GET',
                headers: withAuthHeaders({ Accept: 'text/csv' })
            });

            if (response.status === 401) {
                clearAuthAndRedirect('expired');
                throw new Error('Unauthorized');
            }

            if (!response.ok) {
                let errorMessage = state.lang === 'ar'
                    ? 'فشل تصدير سجلات الأمان'
                    : 'Failed to export security logs';
                try {
                    const errorData = await response.json();
                    if (errorData && errorData.detail) {
                        errorMessage = String(errorData.detail);
                    }
                } catch (_) {
                    // Keep fallback error text.
                }
                throw new Error(errorMessage);
            }

            const payload = await response.blob();
            if (!payload || payload.size <= 0) {
                throw new Error(
                    state.lang === 'ar'
                        ? 'لا توجد سجلات متاحة للتصدير'
                        : 'No logs available to export'
                );
            }

            const filename = extractDownloadFilenameFromResponse(response) || buildSecurityExportFilename();
            downloadBlobAsFile(payload, filename);
            showNotification(
                state.lang === 'ar'
                    ? 'تم تصدير سجلات الأمان بنجاح'
                    : 'Security logs exported successfully',
                'success'
            );
        } catch (error) {
            console.error('Security logs export failed:', error);
            if (error && error.message !== 'Unauthorized') {
                showNotification(
                    error.message || (state.lang === 'ar' ? 'فشل تصدير سجلات الأمان' : 'Failed to export security logs'),
                    'error'
                );
            }
        } finally {
            setLoadingState(false);
        }
    };

    exportButtons.forEach((button) => {
        button.onclick = runExport;
    });
}

function setupSecuritySimulationAction() {
    const button = document.getElementById('security-simulate-btn');
    const resetButton = document.getElementById('security-reset-sim-btn');
    if (!button) return;

    const label = button.querySelector('span');
    const icon = button.querySelector('i');
    const defaultIconClass = icon ? icon.className : '';

    button.onclick = async () => {
        const t = getSecurityCenterTranslations();
        if (button.disabled) return;

        button.disabled = true;
        button.classList.add('is-loading');
        if (icon) {
            icon.className = 'fas fa-spinner fa-spin';
        }
        if (label) {
            label.textContent = t.security_simulate_running;
        }

        try {
            const payload = await api.post('/security/simulate', {});
            applySecurityStreamPayload(payload);
            // Pull user-status widgets immediately so block/suspend logs are
            // visible in the same interaction cycle during demos.
            await refreshSecurityUserStatusPanel({ animateCounters: false });

            const generatedCount = Number(payload && payload.generated_count);
            const suffix = Number.isFinite(generatedCount) && generatedCount > 0
                ? ` (${generatedCount})`
                : '';
            const escalationBlocked = Boolean(
                payload
                && payload.escalation_applied
                && String(payload.escalation_result || '').toLowerCase() === 'blocked'
            );

            if (escalationBlocked) {
                const targetUserId = Number(payload && payload.target_user_id);
                const targetSuffix = Number.isFinite(targetUserId) && targetUserId > 0
                    ? ` (user_id=${targetUserId})`
                    : '';
                showNotification(`${t.security_simulate_escalation_blocked}${targetSuffix}`, 'warning');
            }

            showNotification(`${t.security_simulate_success}${suffix}`, 'success');
        } catch (error) {
            console.error('Security simulation trigger failed:', error);
        } finally {
            button.disabled = false;
            button.classList.remove('is-loading');
            if (icon) {
                icon.className = defaultIconClass;
            }
            if (label) {
                label.textContent = t.security_simulate_btn;
            }
        }
    };

    if (!resetButton) return;

    const resetLabel = resetButton.querySelector('span');
    const resetIcon = resetButton.querySelector('i');
    const defaultResetIconClass = resetIcon ? resetIcon.className : '';

    resetButton.onclick = async () => {
        const t = getSecurityCenterTranslations();
        if (resetButton.disabled) return;

        const shouldReset = window.confirm(t.security_simulation_reset_confirm || 'This will clear simulated events from the feed.\nIncidents and system metrics will NOT be affected.\nContinue?');
        if (!shouldReset) {
            return;
        }

        resetButton.disabled = true;
        resetButton.classList.add('is-loading');
        if (resetIcon) {
            resetIcon.className = 'fas fa-spinner fa-spin';
        }
        if (resetLabel) {
            resetLabel.textContent = t.security_simulation_reset_running || 'Clearing simulation feed...';
        }

        try {
            // Rebase follow-up: this action is now view-only and clears the
            // simulation feed layer without touching incidents or overview data.
            clearSimulationFeedLocally();
            appendSimulationResetAuditEvent();
            showNotification(t.security_simulation_reset_success || 'Simulation feed cleared', 'success');
        } catch (error) {
            console.error('Simulation reset failed:', error);
            showNotification(error.message || 'Failed to clear simulation feed', 'error');
        } finally {
            resetButton.disabled = false;
            resetButton.classList.remove('is-loading');
            if (resetIcon) {
                resetIcon.className = defaultResetIconClass;
            }
            if (resetLabel) {
                resetLabel.textContent = t.security_simulation_reset_btn || 'Reset Simulation View';
            }
        }
    };
}

function isSecurityCenterView(viewName = state.currentView) {
    return viewName === 'securityCenter' || viewName === 'security-center';
}

function cleanupIncidentBackToEventsFloatingButton() {
    if (state.incidentBackToEventsScrollHandler && elements.viewContainer) {
        elements.viewContainer.removeEventListener('scroll', state.incidentBackToEventsScrollHandler);
    }

    state.incidentBackToEventsScrollHandler = null;

    const button = document.getElementById('incident-back-to-events-btn');
    if (button) {
        button.classList.remove('is-visible');
        button.setAttribute('aria-hidden', 'true');
    }
}

function updateIncidentBackToEventsFloatingButtonVisibility() {
    const button = document.getElementById('incident-back-to-events-btn');
    if (!button) return;

    const detailsPanel = document.getElementById('incident-details-panel');
    const detailsVisible = Boolean(
        detailsPanel
        && state.selectedIncident
        && detailsPanel.classList.contains('is-open')
        && !detailsPanel.classList.contains('hidden')
    );
    const containerRect = elements.viewContainer ? elements.viewContainer.getBoundingClientRect() : null;
    const detailsRect = detailsPanel && typeof detailsPanel.getBoundingClientRect === 'function'
        ? detailsPanel.getBoundingClientRect()
        : null;
    const shouldShow = isSecurityCenterView()
        && state.securityActiveTab === 'incidents'
        && detailsVisible
        && containerRect
        && detailsRect
        && detailsRect.bottom > containerRect.top
        && detailsRect.top < containerRect.bottom;

    button.classList.toggle('is-visible', shouldShow);
    button.setAttribute('aria-hidden', shouldShow ? 'false' : 'true');
}

function setupIncidentBackToEventsFloatingButton() {
    cleanupIncidentBackToEventsFloatingButton();

    const button = document.getElementById('incident-back-to-events-btn');
    if (!button || !elements.viewContainer) return;

    const handler = () => {
        updateIncidentBackToEventsFloatingButtonVisibility();
    };

    state.incidentBackToEventsScrollHandler = handler;
    elements.viewContainer.addEventListener('scroll', handler, { passive: true });
    button.onclick = () => {
        setSecurityActiveTab('events', { scrollIntoView: true });
    };

    updateIncidentBackToEventsFloatingButtonVisibility();
}

// --- View Rendering ---

const views = {
    async dashboard() {
        renderTemplate('dashboard-template');
        showLoader();

        try {
            const projects = await fetchUserProjects();

            state.projects = projects;

            // Keep dashboard counters scoped to authenticated user's projects.
            animateCounter('stat-projects', projects.length);
            animateCounter('stat-docs', sumProjectMetric(projects, 'document_count'));
            animateCounter('stat-chunks', sumProjectMetric(projects, 'chunk_count'));

            // Render recent projects
            const list = document.getElementById('recent-projects-list');
            list.innerHTML = '';
            if (projects.length === 0) {
                list.innerHTML = createEmptyState('fa-folder-open', 'empty_projects', 'empty_projects_desc');
            } else {
                projects.slice(0, 3).forEach(project => {
                    list.appendChild(createProjectCard(project));
                });
            }

            // View All link -> switch to projects
            const viewAllLink = document.querySelector('.section-header .link');
            if (viewAllLink) {
                viewAllLink.onclick = (e) => { e.preventDefault(); switchView('projects'); };
            }

            applyTranslations();
        } catch (error) {
            console.error('Dashboard Load Error:', error);
        } finally {
            hideLoader();
        }
    },

    async securityCenter() {
        renderTemplate('security-center-template');
        showLoader();
        const tSecurity = getSecurityCenterTranslations();

        try {
            const securityData = await fetchSecurityDashboardData(20).catch((error) => {
                console.error('Security Center Data Error:', error);
                if (error.message !== 'Unauthorized') {
                    showNotification(tSecurity.security_load_error, 'warning');
                }
                return {
                    stats: normalizeSecurityStats({}),
                    events: []
                };
            });

            state.stats = normalizeSecurityStats(securityData.stats);
            const filtered = filterSimulationPayload(securityData.events, []);
            state.securityEvents = filtered.events;
            renderSecurityEventViews(state.securityEvents);
            syncSecurityOverviewFromCurrentState();
            markSecurityEventsFeedUpdated();
            await refreshSecurityUserStatusPanel({ animateCounters: true }).catch((error) => {
                console.error('Security user status load error:', error);
                if (error.message !== 'Unauthorized') {
                    showNotification(tSecurity.security_load_error, 'warning');
                }
            });
            setupSecurityCenterTabs();
            setupIncidentFilters();
            setupIncidentTableInteraction();
            setupIncidentDetailsDismissActions();
            setupIncidentActionHandlers();
            state.selectedIncident = null;
            clearIncidentDetailsPanel({ rerenderIncidents: false });
            await loadSecurityIncidents({
                keepSelected: false,
                refreshOverview: true,
                animateIncidentCounters: true,
                announceNew: false,
            }).catch((error) => {
                console.error('Incident list load error:', error);
                if (error.message !== 'Unauthorized') {
                    showNotification(tSecurity.incident_load_error, 'warning');
                }
            });
            setSecurityActiveTab(state.securityActiveTab);
            startIncidentOverviewMonitor();
            startSecurityRealtimeStream();
            setupSecuritySimulationAction();
            setupSecurityExportAction();
            setupSecurityEventsRefreshAction();
            startSecurityEventsRefreshSystem();
            applyTranslations();
        } catch (error) {
            console.error('Security Center Load Error:', error);
        } finally {
            hideLoader();
        }
    },

    async projects() {
        renderTemplate('projects-template');
        showLoader();

        try {
            const projects = await fetchUserProjects();
            state.projects = projects;

            const list = document.getElementById('all-projects-list');
            list.innerHTML = '';
            if (projects.length === 0) {
                list.innerHTML = createEmptyState('fa-folder-open', 'empty_projects', 'empty_projects_desc');
            } else {
                projects.forEach(project => {
                    list.appendChild(createProjectCard(project));
                });
            }
            applyTranslations();
        } catch (error) {
            console.error('Projects Load Error:', error);
        } finally {
            hideLoader();
        }
    },

    async projectDetail(projectId) {
        renderTemplate('project-detail-template');
        showLoader();

        try {
            const project = await api.get(`/projects/${projectId}`);
            const docs = await api.get(`/projects/${projectId}/documents`);

            state.selectedProject = project;

            document.getElementById('project-name-title').textContent = project.name;

            renderDocsList(docs);
            startDocPolling(projectId, docs);

            // Setup Upload Zone
            setupUploadZone(projectId);

            document.getElementById('back-to-projects').onclick = () => switchView('projects');
            applyTranslations();
        } catch (error) {
            console.error('Project Detail Load Error:', error);
        } finally {
            hideLoader();
        }
    },

    async chat() {
        renderTemplate('chat-template');

        const select = document.getElementById('chat-project-select');
        const projects = await fetchUserProjects();

        projects.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name;
            select.appendChild(opt);
        });

        const sendBtn = document.getElementById('send-btn');
        const chatInput = document.getElementById('chat-input');
        const clearBtn = document.getElementById('clear-chat-btn');

        // Enable/disable send button based on input
        chatInput.oninput = () => {
            setChatRequestUiState(state.chatRequestInProgress);
            autoResizeTextarea(chatInput);
        };

        sendBtn.onclick = () => {
            if (state.chatRequestInProgress) {
                cancelCurrentChatRequest();
                return;
            }

            handleChatSubmit();
        };
        chatInput.onkeydown = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (state.chatRequestInProgress) return;
                if (chatInput.value.trim()) handleChatSubmit();
            }
        };

        // Clear chat handler
        if (clearBtn) {
            clearBtn.onclick = () => {
                const messagesContainer = document.getElementById('chat-messages');
                messagesContainer.innerHTML = `
                    <div class="welcome-msg-pro">
                        <div class="welcome-icon">
                            <i class="fas fa-robot"></i>
                        </div>
                        <h2>${state.lang === 'ar' ? 'كيف يمكنني مساعدتك اليوم؟' : 'How can I help you today?'}</h2>
                        <p>${state.lang === 'ar' ? 'اختر مشروعاً من الأعلى وابدأ في طرح الأسئلة حول مستنداتك.' : 'Select a project from above and start asking questions.'}</p>
                    </div>
                `;
            };
        }

        // Suggestion chips handler
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.onclick = () => {
                if (state.chatRequestInProgress) return;
                chatInput.value = chip.textContent;
                chatInput.oninput();
                chatInput.focus();
            };
        });

        setChatRequestUiState(state.chatRequestInProgress);
        autoResizeTextarea(chatInput);

        applyTranslations();
    },

    async 'bot-config'() {
        renderTemplate('bot-config-template');
        showLoader();

        try {
            const [projects, config] = await Promise.all([
                fetchUserProjects(),
                api.get('/bot/config')
            ]);

            const select = document.getElementById('bot-active-project');
            projects.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.name;
                if (config.active_project_id == p.id) opt.selected = true;
                select.appendChild(opt);
            });

            document.getElementById('save-bot-config-btn').onclick = async () => {
                const projectId = select.value;
                if (!projectId) return;
                try {
                    await api.post('/bot/config', { active_project_id: parseInt(projectId) });
                    showNotification(i18n[state.lang].success_saved, 'success');
                } catch (e) {
                    console.error(e);
                }
            };

            document.getElementById('update-bot-profile-btn').onclick = async () => {
                const name = document.getElementById('bot-name-input').value;
                if (!name) return;
                const formData = new FormData();
                formData.append('name', name);
                try {
                    await api.post('/bot/profile', formData, true);
                    showNotification(i18n[state.lang].success_saved, 'success');
                } catch (e) {
                    console.error(e);
                }
            };

            applyTranslations();
        } catch (error) {
            console.error('Bot Config Error:', error);
        } finally {
            hideLoader();
        }
    },

    async 'ai-config'() {
        renderTemplate('ai-config-template');
        showLoader();

        try {
            const config = await api.get('/config/providers');
            const genSelect = document.getElementById('ai-gen-provider');
            const embedSelect = document.getElementById('ai-embed-provider');
            const vectorDbSelect = document.getElementById('vector-db-provider');
            const embeddingSizeSelect = document.getElementById('embedding-size');
            const retrievalInput = document.getElementById('retrieval-top-k');
            const chunkStrategySelect = document.getElementById('chunk-strategy');
            const chunkSizeInput = document.getElementById('chunk-size');
            const chunkOverlapInput = document.getElementById('chunk-overlap');
            const parentChunkSizeInput = document.getElementById('parent-chunk-size');
            const parentChunkOverlapInput = document.getElementById('parent-chunk-overlap');
            const candidateInput = document.getElementById('retrieval-candidate-k');
            const hybridEnabledInput = document.getElementById('retrieval-hybrid-enabled');
            const hybridAlphaInput = document.getElementById('retrieval-hybrid-alpha');
            const rewriteEnabledInput = document.getElementById('query-rewrite-enabled');
            const rerankEnabledInput = document.getElementById('retrieval-rerank-enabled');
            const rerankTopKInput = document.getElementById('retrieval-rerank-top-k');

            const genProviders = config.available?.llm || [];
            const embedProviders = config.available?.embedding || [];
            const vectorProviders = config.available?.vector_db || [];


            const labelMap = {
                gemini: 'Gemini 2.5 Flash',
                'gemini-2.5-lite-flash': 'Gemini 2.5 Lite Flash',
                'openrouter-gemini-2.0-flash': 'OpenRouter: Gemini 2.0 Flash',
                'openrouter-free': 'OpenRouter: Free',
                'groq-llama-3.3-70b-versatile': 'Groq: Llama 3.3 70B Versatile',
                'groq-gpt-oss-120b': 'Groq: GPT-oss 120B',
                'cerebras-llama-3.3-70b': 'Cerebras: Llama 3.3 70B',
                'cerebras-llama-3.1-8b': 'Cerebras: Llama 3.1 8B',
                'cerebras-gpt-oss-120b': 'Cerebras: GPT-oss 120B',
                cohere: 'Cohere',
                voyage: 'Voyage AI',
                'bge-m3': 'BAAI/bge-m3 (local)',
                pgvector: 'pgvector',
                qdrant: 'Qdrant'
            };

            genProviders.forEach((name) => {
                const opt = document.createElement('option');
                opt.value = name;
                opt.textContent = labelMap[name] || name;
                if (config.llm_provider === name) opt.selected = true;
                genSelect.appendChild(opt);
            });

            embedProviders.forEach((name) => {
                const opt = document.createElement('option');
                opt.value = name;
                opt.textContent = labelMap[name] || name;
                if (config.embedding_provider === name) opt.selected = true;
                embedSelect.appendChild(opt);
            });

            vectorProviders.forEach((name) => {
                const opt = document.createElement('option');
                opt.value = name;
                opt.textContent = labelMap[name] || name;
                if (config.vector_db_provider === name) opt.selected = true;
                vectorDbSelect.appendChild(opt);
            });

            if (typeof config.retrieval_top_k === 'number') {
                retrievalInput.value = String(config.retrieval_top_k);
                state.retrievalTopK = config.retrieval_top_k;
            }

            if (typeof config.voyage_output_dimension === 'number') {
                embeddingSizeSelect.value = String(config.voyage_output_dimension);
            }

            if (config.chunk_strategy) chunkStrategySelect.value = config.chunk_strategy;
            if (typeof config.chunk_size === 'number') chunkSizeInput.value = String(config.chunk_size);
            if (typeof config.chunk_overlap === 'number') chunkOverlapInput.value = String(config.chunk_overlap);
            if (typeof config.parent_chunk_size === 'number') parentChunkSizeInput.value = String(config.parent_chunk_size);
            if (typeof config.parent_chunk_overlap === 'number') parentChunkOverlapInput.value = String(config.parent_chunk_overlap);
            if (typeof config.retrieval_candidate_k === 'number') candidateInput.value = String(config.retrieval_candidate_k);
            if (typeof config.retrieval_hybrid_enabled === 'boolean') hybridEnabledInput.checked = config.retrieval_hybrid_enabled;
            if (typeof config.retrieval_hybrid_alpha === 'number') hybridAlphaInput.value = String(config.retrieval_hybrid_alpha);
            if (typeof config.query_rewrite_enabled === 'boolean') rewriteEnabledInput.checked = config.query_rewrite_enabled;
            if (typeof config.retrieval_rerank_enabled === 'boolean') rerankEnabledInput.checked = config.retrieval_rerank_enabled;
            if (typeof config.retrieval_rerank_top_k === 'number') rerankTopKInput.value = String(config.retrieval_rerank_top_k);

            document.getElementById('save-ai-config-btn').onclick = async () => {
                try {
                    const retrievalValue = parseInt(retrievalInput.value, 10);
                    const embeddingSizeValue = parseInt(embeddingSizeSelect.value, 10);
                    const chunkSizeValue = parseInt(chunkSizeInput.value, 10);
                    const chunkOverlapValue = parseInt(chunkOverlapInput.value, 10);
                    const parentChunkSizeValue = parseInt(parentChunkSizeInput.value, 10);
                    const parentChunkOverlapValue = parseInt(parentChunkOverlapInput.value, 10);
                    const candidateValue = parseInt(candidateInput.value, 10);
                    const hybridAlphaValue = parseFloat(hybridAlphaInput.value);
                    const rerankTopKValue = parseInt(rerankTopKInput.value, 10);
                    await api.post('/config/providers', {
                        llm_provider: genSelect.value,
                        embedding_provider: embedSelect.value,
                        vector_db_provider: vectorDbSelect.value,
                        retrieval_top_k: Number.isFinite(retrievalValue) ? retrievalValue : undefined,
                        voyage_output_dimension: Number.isFinite(embeddingSizeValue) ? embeddingSizeValue : undefined,
                        chunk_strategy: chunkStrategySelect.value,
                        chunk_size: Number.isFinite(chunkSizeValue) ? chunkSizeValue : undefined,
                        chunk_overlap: Number.isFinite(chunkOverlapValue) ? chunkOverlapValue : undefined,
                        parent_chunk_size: Number.isFinite(parentChunkSizeValue) ? parentChunkSizeValue : undefined,
                        parent_chunk_overlap: Number.isFinite(parentChunkOverlapValue) ? parentChunkOverlapValue : undefined,
                        retrieval_candidate_k: Number.isFinite(candidateValue) ? candidateValue : undefined,
                        retrieval_hybrid_enabled: hybridEnabledInput.checked,
                        retrieval_hybrid_alpha: Number.isFinite(hybridAlphaValue) ? hybridAlphaValue : undefined,
                        query_rewrite_enabled: rewriteEnabledInput.checked,
                        retrieval_rerank_enabled: rerankEnabledInput.checked,
                        retrieval_rerank_top_k: Number.isFinite(rerankTopKValue) ? rerankTopKValue : undefined
                    });
                    if (Number.isFinite(retrievalValue)) {
                        state.retrievalTopK = retrievalValue;
                    }
                    showNotification(i18n[state.lang].success_saved, 'success');
                } catch (e) {
                    console.error(e);
                }
            };

            applyTranslations();
        } catch (error) {
            console.error('AI Config Error:', error);
        } finally {
            hideLoader();
        }
    },

    async 'account-settings'() {
        renderTemplate('account-settings-template');
        showLoader();

        try {
            const user = await getCurrentUser();

            const usernameValue = document.getElementById('account-username-value');
            const roleValue = document.getElementById('account-role-value');
            const createdValue = document.getElementById('account-created-value');
            const sessionExpiryValue = document.getElementById('account-session-expiry-value');

            const languageSelect = document.getElementById('account-language-select');
            const themeSelect = document.getElementById('account-theme-select');
            const apiBaseInput = document.getElementById('account-api-base-input');
            const savePreferencesBtn = document.getElementById('save-account-preferences-btn');

            const currentPasswordInput = document.getElementById('account-current-password');
            const newPasswordInput = document.getElementById('account-new-password');
            const confirmPasswordInput = document.getElementById('account-confirm-password');
            const showPasswordsToggle = document.getElementById('account-show-passwords');
            const changePasswordBtn = document.getElementById('change-password-btn');

            const passwordInputs = [
                currentPasswordInput,
                newPasswordInput,
                confirmPasswordInput
            ].filter(Boolean);

            if (showPasswordsToggle) {
                showPasswordsToggle.onchange = () => {
                    const inputType = showPasswordsToggle.checked ? 'text' : 'password';
                    passwordInputs.forEach((input) => {
                        input.type = inputType;
                    });
                };
            }

            if (newPasswordInput) {
                newPasswordInput.oninput = () => {
                    renderPasswordStrengthIndicator(newPasswordInput.value);
                };
                renderPasswordStrengthIndicator(newPasswordInput.value);
            }

            if (usernameValue) {
                usernameValue.textContent = user && user.username ? user.username : '-';
            }
            if (roleValue) {
                roleValue.textContent = formatPrimaryRoleLabel(user);
            }
            if (createdValue) {
                createdValue.textContent = formatLocaleDateTime(user && user.created_at ? user.created_at : null);
            }
            if (sessionExpiryValue) {
                sessionExpiryValue.textContent = getSessionExpiryLabel();
            }

            if (languageSelect) {
                languageSelect.value = state.lang;
            }
            if (themeSelect) {
                themeSelect.value = state.theme;
            }
            if (apiBaseInput) {
                apiBaseInput.value = API_BASE_URL;
            }

            if (savePreferencesBtn) {
                savePreferencesBtn.onclick = async () => {
                    const nextLanguage = languageSelect ? languageSelect.value : state.lang;
                    const nextTheme = themeSelect ? themeSelect.value : state.theme;
                    const requestedApiBase = normalizeBaseUrl(apiBaseInput ? apiBaseInput.value : API_BASE_URL);
                    const languageChanged = nextLanguage !== state.lang;
                    const themeChanged = nextTheme !== state.theme;
                    const apiChanged = Boolean(requestedApiBase) && requestedApiBase !== API_BASE_URL;

                    if (apiChanged) {
                        const reachable = await canReachApi(requestedApiBase);
                        if (!reachable) {
                            showNotification(i18n[state.lang].account_api_unreachable, 'warning');
                            return;
                        }

                        API_BASE_URL = requestedApiBase;
                        localStorage.setItem('ragmind_api_base_url', API_BASE_URL);
                    }

                    if (themeChanged) {
                        applyTheme(nextTheme);
                    }

                    if (languageChanged) {
                        state.lang = nextLanguage;
                        localStorage.setItem('lang', state.lang);
                    }

                    showNotification(i18n[state.lang].account_preferences_saved, 'success');

                    if (languageChanged) {
                        await switchView('account-settings');
                        return;
                    }

                    applyTranslations();
                };
            }

            if (changePasswordBtn) {
                changePasswordBtn.onclick = async () => {
                    const currentPassword = currentPasswordInput ? currentPasswordInput.value : '';
                    const newPassword = newPasswordInput ? newPasswordInput.value : '';
                    const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : '';

                    if (!currentPassword || !newPassword || !confirmPassword) {
                        showNotification(i18n[state.lang].account_password_required, 'warning');
                        return;
                    }

                    if (newPassword !== confirmPassword) {
                        showNotification(i18n[state.lang].account_password_mismatch, 'warning');
                        return;
                    }

                    try {
                        await submitPasswordChangeWithFallback({
                            current_password: currentPassword,
                            new_password: newPassword,
                            confirm_new_password: confirmPassword
                        });

                        if (currentPasswordInput) currentPasswordInput.value = '';
                        if (newPasswordInput) newPasswordInput.value = '';
                        if (confirmPasswordInput) confirmPasswordInput.value = '';
                        renderPasswordStrengthIndicator('');

                        showNotification(i18n[state.lang].account_password_updated, 'success');
                    } catch (error) {
                        console.error('Change Password Error:', error);
                        showNotification(error.message || i18n[state.lang].error_generic, 'error');
                    }
                };
            }

            applyTranslations();
            if (newPasswordInput) {
                renderPasswordStrengthIndicator(newPasswordInput.value);
            }
        } catch (error) {
            console.error('Account Settings Error:', error);
        } finally {
            hideLoader();
        }
    }
};

// --- Helpers ---

function resetViewContainerScroll() {
    if (!elements.viewContainer) return;
    elements.viewContainer.scrollTop = 0;

    if (typeof elements.viewContainer.scrollTo === 'function') {
        elements.viewContainer.scrollTo({ top: 0, left: 0, behavior: 'auto' });
    }
}

function renderTemplate(templateId) {
    const template = document.getElementById(templateId);
    const clone = template.content.cloneNode(true);
    elements.viewContainer.innerHTML = '';
    elements.viewContainer.appendChild(clone);
    resetViewContainerScroll();
}

function showLoader() {
    const loader = document.createElement('div');
    loader.className = 'loader-container';
    loader.innerHTML = '<div class="loader"></div>';
    elements.viewContainer.appendChild(loader);
}

function hideLoader() {
    const loader = elements.viewContainer.querySelector('.loader-container');
    if (loader) loader.remove();
}

function createProjectCard(project) {
    const card = document.createElement('div');
    card.className = 'project-card';
    const docCount = project.document_count || 0;
    card.innerHTML = `
        <h3>${escapeHtml(project.name)}</h3>
        <p>${escapeHtml(project.description || (state.lang === 'ar' ? 'لا يوجد وصف' : 'No description'))}</p>
        <div class="project-card-footer">
            <span class="project-card-date"><i class="far fa-calendar"></i> ${new Date(project.created_at).toLocaleDateString(state.lang === 'ar' ? 'ar-EG' : 'en-US')}</span>
            <div class="project-card-actions">
                <span class="doc-count-badge"><i class="fas fa-file-alt"></i> ${docCount}</span>
                <button class="delete-project-btn" data-id="${project.id}"><i class="fas fa-trash"></i></button>
            </div>
        </div>
    `;

    card.onclick = (e) => {
        if (e.target.closest('.delete-project-btn')) {
            handleDeleteProject(project.id);
            return;
        }
        switchView('projectDetail', project.id);
    };

    return card;
}

function createDocItem(doc) {
    const item = document.createElement('div');
    item.className = 'doc-item';
    const isActiveStatus = isDocumentActive(doc.status);
    const statusClass = doc.status === 'completed' ? 'status-done' : (doc.status === 'failed' ? 'status-error' : 'status-processing');
    const statusIcon = doc.status === 'completed' ? 'fa-check-circle' : (doc.status === 'failed' ? 'fa-exclamation-circle' : (isActiveStatus ? 'fa-spinner fa-spin' : 'fa-clock'));
    const meta = doc.extra_metadata || {};
    const totalChunks = Number.isFinite(meta.total_chunks) ? meta.total_chunks : null;
    const processedChunks = Number.isFinite(meta.processed_chunks) ? meta.processed_chunks : null;
    const progressValue = Number.isFinite(meta.progress) ? meta.progress : null;
    const stageLabel = getStageLabel(meta.stage);
    const showProgress = isActiveStatus && totalChunks && totalChunks > 0;
    const progressPercent = progressValue != null
        ? Math.max(0, Math.min(100, progressValue))
        : Math.round((processedChunks || 0) / totalChunks * 100);

    const statusText = {
        uploaded: state.lang === 'ar' ? 'تم الرفع' : 'Uploaded',
        queued: state.lang === 'ar' ? 'في قائمة الانتظار' : 'Queued',
        pending: state.lang === 'ar' ? 'قيد الانتظار' : 'Pending',
        completed: state.lang === 'ar' ? 'مكتمل' : 'Completed',
        failed: state.lang === 'ar' ? 'فشل' : 'Failed',
        processing: state.lang === 'ar' ? 'جاري المعالجة' : 'Processing'
    };

    item.innerHTML = `
        <div class="doc-info">
            <i class="fas fa-file-pdf"></i>
            <div class="doc-details">
                <span class="doc-name">${doc.original_filename}</span>
                <span class="doc-size">${(doc.file_size / 1024).toFixed(1)} KB</span>
            </div>
        </div>
        <div class="doc-status ${statusClass}">
            <i class="fas ${statusIcon}"></i>
            <span>${statusText[doc.status] || doc.status}</span>
        </div>
        ${showProgress ? `
            <div class="doc-progress">
                <div class="doc-progress-header">
                    <span>${i18n[state.lang].processing_label}</span>
                    <span>${stageLabel}</span>
                    <span>${processedChunks || 0}/${totalChunks}</span>
                </div>
                <div class="doc-progress-track">
                    <div class="doc-progress-bar" style="width: ${progressPercent}%;"></div>
                </div>
            </div>
        ` : ''}
        <button class="delete-doc-btn" data-id="${doc.id}"><i class="fas fa-trash"></i></button>
    `;

    item.querySelector('.delete-doc-btn').onclick = () => handleDeleteDoc(doc.id);

    return item;
}

function renderDocsList(docs) {
    const docsList = document.getElementById('project-docs-list');
    if (!docsList) return;
    docsList.innerHTML = '';

    if (docs.length === 0) {
        docsList.innerHTML = createEmptyState('fa-file-circle-plus', 'empty_docs', 'empty_docs_desc');
        return;
    }

    docs.forEach(doc => {
        docsList.appendChild(createDocItem(doc));
    });
}

function startDocPolling(projectId, docs) {
    if (state.docPoller) {
        clearInterval(state.docPoller);
        state.docPoller = null;
    }

    const hasActiveDocs = docs.some(doc => isDocumentActive(doc.status));
    if (!hasActiveDocs) return;

    state.docPoller = setInterval(async () => {
        if (state.currentView !== 'projectDetail') {
            clearInterval(state.docPoller);
            state.docPoller = null;
            return;
        }

        try {
            const updated = await api.get(`/projects/${projectId}/documents`);
            renderDocsList(updated);
            const stillActive = updated.some(doc => isDocumentActive(doc.status));
            if (!stillActive) {
                clearInterval(state.docPoller);
                state.docPoller = null;
            }
        } catch (error) {
            console.error('Docs Poll Error:', error);
        }
    }, 3000);
}

function clearIncidentOverviewRefreshTimer() {
    if (state.incidentOverviewRefreshTimer) {
        clearTimeout(state.incidentOverviewRefreshTimer);
        state.incidentOverviewRefreshTimer = null;
    }
}

function stopIncidentOverviewMonitor() {
    clearIncidentOverviewRefreshTimer();

    if (state.incidentOverviewTimer) {
        clearInterval(state.incidentOverviewTimer);
        state.incidentOverviewTimer = null;
    }
}

function scheduleIncidentOverviewRefresh() {
    if (!isSecurityCenterView()) return;
    if (state.incidentOverviewRefreshTimer) return;

    state.incidentOverviewRefreshTimer = setTimeout(async () => {
        state.incidentOverviewRefreshTimer = null;
        try {
            await refreshIncidentOverview({
                announceNew: true,
                animateCounters: false,
            });
        } catch (error) {
            if (error && error.message !== 'Unauthorized') {
                console.error('Incident overview stream sync failed:', error);
            }
        }
    }, INCIDENT_OVERVIEW_STREAM_SYNC_DELAY_MS);
}

function startIncidentOverviewMonitor() {
    stopIncidentOverviewMonitor();
    if (!isSecurityCenterView()) return;

    state.incidentOverviewTimer = setInterval(async () => {
        try {
            await refreshIncidentOverview({
                announceNew: true,
                animateCounters: false,
            });
        } catch (error) {
            if (error && error.message !== 'Unauthorized') {
                console.error('Incident overview poll failed:', error);
            }
        }
    }, INCIDENT_OVERVIEW_POLL_MS);
}

function clearSecurityStreamReconnectTimer() {
    if (state.securityStreamReconnectTimer) {
        clearTimeout(state.securityStreamReconnectTimer);
        state.securityStreamReconnectTimer = null;
    }
}

function clearSecurityUsersRefreshTimer() {
    if (state.securityUsersRefreshTimer) {
        clearTimeout(state.securityUsersRefreshTimer);
        state.securityUsersRefreshTimer = null;
    }
}

function stopSecurityRealtimeStream() {
    clearSecurityStreamReconnectTimer();
    clearSecurityUsersRefreshTimer();

    if (state.securityStreamAbortController) {
        state.securityStreamAbortController.abort();
        state.securityStreamAbortController = null;
    }
}

function scheduleSecurityStreamReconnect() {
    if (!isSecurityCenterView()) return;
    if (state.securityStreamReconnectTimer) return;

    state.securityStreamReconnectTimer = setTimeout(() => {
        state.securityStreamReconnectTimer = null;
        startSecurityRealtimeStream();
    }, SECURITY_STREAM_RECONNECT_MS);
}

function scheduleSecurityUsersRefresh() {
    if (!isSecurityCenterView()) return;
    if (state.securityUsersRefreshTimer) return;

    state.securityUsersRefreshTimer = setTimeout(async () => {
        state.securityUsersRefreshTimer = null;
        try {
            await refreshSecurityUserStatusPanel({ animateCounters: false });
        } catch (error) {
            if (error && error.message !== 'Unauthorized') {
                console.error('Security user status refresh failed:', error);
            }
        }
    }, SECURITY_USERS_REFRESH_DELAY_MS);
}

function applySecurityStreamPayload(payload) {
    if (!payload || typeof payload !== 'object') return;

    const events = Array.isArray(payload.events) ? payload.events : [];
    const filtered = filterSimulationPayload(events, state.securityIncidents);
    state.securityEvents = filtered.events;
    state.stats = normalizeSecurityStats(payload.stats || state.stats || {});
    renderSecurityEventViews(state.securityEvents, { preserveScroll: true });
    syncSecurityOverviewFromCurrentState();
    scheduleIncidentOverviewRefresh();
    scheduleSecurityUsersRefresh();
    markSecurityEventsFeedUpdated();
}

async function startSecurityRealtimeStream() {
    stopSecurityRealtimeStream();

    if (!isSecurityCenterView()) return;

    const controller = new AbortController();
    state.securityStreamAbortController = controller;

    try {
        const response = await fetchWithApiRecovery('/security/events/stream?limit=20', {
            headers: withAuthHeaders({ Accept: 'text/event-stream' }),
            signal: controller.signal
        }, 0);

        if (response.status === 401) {
            clearAuthAndRedirect('expired');
            throw new Error('Unauthorized');
        }

        if (!response.ok || !response.body) {
            throw new Error(`Security stream failed (${response.status})`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (isSecurityCenterView() && !controller.signal.aborted) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');

            let boundary = buffer.indexOf('\n\n');
            while (boundary !== -1) {
                const rawEvent = buffer.slice(0, boundary).trim();
                buffer = buffer.slice(boundary + 2);

                if (rawEvent && !rawEvent.startsWith(':')) {
                    const lines = rawEvent.split('\n');
                    const dataLines = [];

                    for (const line of lines) {
                        if (line.startsWith('data:')) {
                            dataLines.push(line.slice(5).trim());
                        }
                    }

                    if (dataLines.length > 0) {
                        try {
                            applySecurityStreamPayload(JSON.parse(dataLines.join('\n')));
                        } catch (parseError) {
                            console.warn('Security stream payload parse error:', parseError);
                        }
                    }
                }

                boundary = buffer.indexOf('\n\n');
            }
        }

        try {
            await reader.cancel();
        } catch (_) {
            // Ignore cancellation errors on connection close.
        }
    } catch (error) {
        if (error && error.name === 'AbortError') {
            return;
        }

        if (error.message !== 'Unauthorized') {
            console.error('Security realtime stream error:', error);
        }
    } finally {
        if (state.securityStreamAbortController === controller) {
            state.securityStreamAbortController = null;
        }

        if (!controller.signal.aborted && isSecurityCenterView()) {
            scheduleSecurityStreamReconnect();
        }
    }
}

function getStageLabel(stage) {
    if (!stage) return '';
    const map = {
        chunking: i18n[state.lang].stage_chunking,
        embedding: i18n[state.lang].stage_embedding,
        indexing: i18n[state.lang].stage_indexing
    };
    return map[stage] || stage;
}

function showNotification(message, type = 'info') {
    const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-circle-exclamation',
        warning: 'fa-triangle-exclamation',
        info: 'fa-circle-info'
    };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<i class="fas ${iconMap[type] || iconMap.info} toast-icon"></i><span>${escapeHtml(message)}</span>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 50);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

function applyTranslations() {
    const t = i18n[state.lang];
    const forceSecurityEnglish = isSecurityCenterView();
    const tSecurity = i18n.en;

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (t[key]) el.textContent = t[key];
    });

    if (forceSecurityEnglish) {
        document.querySelectorAll('.security-center-view [data-i18n]').forEach(el => {
            const key = el.dataset.i18n;
            if (tSecurity[key]) el.textContent = tSecurity[key];
        });
    }

    // Update placeholders
    if (document.getElementById('new-project-name')) {
        document.getElementById('new-project-name').placeholder = t.project_name_ph;
        document.getElementById('new-project-desc').placeholder = t.project_desc_ph;
    }

    // Update Lang Button
    elements.langToggle.querySelector('.lang-code').textContent = state.lang === 'ar' ? 'EN' : 'AR';

    // Update Dir
    document.documentElement.dir = forceSecurityEnglish ? 'ltr' : (state.lang === 'ar' ? 'rtl' : 'ltr');
    document.documentElement.lang = forceSecurityEnglish ? 'en' : state.lang;

    // Update search placeholder
    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) searchInput.placeholder = t.search_placeholder;

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.title = t.logout_btn;
        logoutBtn.setAttribute('aria-label', t.logout_btn);
    }

    const incidentNotesInput = document.getElementById('incident-notes-input');
    if (incidentNotesInput) {
        const notesPlaceholderText = forceSecurityEnglish
            ? (tSecurity.incident_notes_placeholder || 'Add investigation notes...')
            : (t.incident_notes_placeholder || 'Add investigation notes...');
        incidentNotesInput.placeholder = notesPlaceholderText;
    }

    // Update back button icon direction
    const backBtn = document.getElementById('back-to-projects');
    if (backBtn) {
        const icon = backBtn.querySelector('i');
        if (icon) icon.className = state.lang === 'ar' ? 'fas fa-arrow-right' : 'fas fa-arrow-left';
    }

    if (state.currentView === 'chat') {
        setChatRequestUiState(state.chatRequestInProgress);
    }
}

function applyTheme(themeName) {
    state.theme = themeName === 'light' ? 'light' : 'dark';
    document.body.classList.toggle('light-theme', state.theme === 'light');
    document.body.classList.toggle('dark-theme', state.theme === 'dark');

    const icon = elements.themeToggle.querySelector('i');
    icon.className = state.theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';

    localStorage.setItem('theme', state.theme);
}

function toggleTheme() {
    applyTheme(state.theme === 'dark' ? 'light' : 'dark');
}

function toggleLang() {
    state.lang = state.lang === 'ar' ? 'en' : 'ar';
    localStorage.setItem('lang', state.lang);
    applyTranslations();
    switchView(state.currentView, state.selectedProject ? state.selectedProject.id : null);
}

// --- Event Handlers ---

async function switchView(viewName, params = null) {
    if (viewName === 'security-center') {
        viewName = 'securityCenter';
    }

    if (viewName === 'securityCenter' && !canAccessSecurityCenter()) {
        showNotification(i18n[state.lang].security_access_denied, 'warning');
        viewName = 'dashboard';
    }

    if (state.docPoller) {
        clearInterval(state.docPoller);
        state.docPoller = null;
    }

    if (state.currentView === 'chat' && viewName !== 'chat') {
        cancelCurrentChatRequest({ silent: true });
    }

    if (isSecurityCenterView(state.currentView) && !isSecurityCenterView(viewName)) {
        cleanupIncidentBackToEventsFloatingButton();
        cleanupIncidentDetailsDismissActions();
        stopSecurityEventsRefreshSystem();
    }

    stopSecurityRealtimeStream();
    stopIncidentOverviewMonitor();
    state.currentView = viewName;

    // Update Nav
    elements.navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });

    // Render View
    if (viewName === 'projectDetail') {
        await views.projectDetail(params);
    } else if (views[viewName]) {
        await views[viewName]();
    }
}

async function handleNewProject() {
    elements.modalTitle.textContent = i18n[state.lang].create_project_btn;
    elements.modalBody.innerHTML = `
        <div class="form-group">
            <label>${state.lang === 'ar' ? 'اسم المشروع' : 'Project Name'}</label>
            <input type="text" id="new-project-name" class="form-control">
        </div>
        <div class="form-group">
            <label>${state.lang === 'ar' ? 'الوصف' : 'Description'}</label>
            <textarea id="new-project-desc" class="form-control"></textarea>
        </div>
        <button id="save-project-btn" class="btn btn-primary w-100 mt-4">${i18n[state.lang].create_project_btn}</button>
    `;
    applyTranslations();

    elements.modalOverlay.classList.remove('hidden');

    document.getElementById('save-project-btn').onclick = async () => {
        const name = document.getElementById('new-project-name').value;
        const description = document.getElementById('new-project-desc').value;

        if (!name) {
            showNotification(state.lang === 'ar' ? 'يرجى إدخال اسم المشروع' : 'Please enter project name', 'warning');
            return;
        }

        try {
            await api.post('/projects/', { name, description });
            showNotification(i18n[state.lang].success_saved, 'success');
            elements.modalOverlay.classList.add('hidden');
            switchView(state.currentView); // Refresh current view
        } catch (error) {
            console.error('Create Project Error:', error);
        }
    };
}

async function handleDeleteProject(id) {
    if (confirm(i18n[state.lang].delete_confirm)) {
        try {
            await api.delete(`/projects/${id}`);
            showNotification(i18n[state.lang].success_saved, 'success');
            switchView(state.currentView);
        } catch (error) {
            console.error('Delete Project Error:', error);
        }
    }
}

async function handleDeleteDoc(id) {
    if (confirm(i18n[state.lang].delete_confirm)) {
        try {
            await api.delete(`/documents/${id}`);
            showNotification(i18n[state.lang].success_saved, 'success');
            if (state.selectedProject) {
                switchView('projectDetail', state.selectedProject.id);
            }
        } catch (error) {
            console.error('Delete Doc Error:', error);
        }
    }
}

function isAbortError(error) {
    if (!error) return false;
    if (error.name === 'AbortError') return true;
    const message = String(error.message || '').toLowerCase();
    return message.includes('aborted') || message.includes('aborterror');
}

function setChatRequestUiState(isInProgress) {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const statusEl = document.getElementById('chat-request-status');
    const clearBtn = document.getElementById('clear-chat-btn');
    const sendIcon = sendBtn ? sendBtn.querySelector('i') : null;

    if (input) {
        input.disabled = Boolean(isInProgress);
    }

    if (sendBtn && input) {
        sendBtn.disabled = isInProgress ? false : !input.value.trim();
        sendBtn.classList.toggle('is-stop', Boolean(isInProgress));

        if (sendIcon) {
            sendIcon.className = isInProgress ? 'fas fa-stop' : 'fas fa-arrow-up';
        }

        const sendLabel = state.lang === 'ar' ? 'إرسال' : 'Send';
        const actionLabel = isInProgress ? i18n[state.lang].chat_stop_response : sendLabel;
        sendBtn.title = actionLabel;
        sendBtn.setAttribute('aria-label', actionLabel);
    }

    if (statusEl) {
        statusEl.textContent = isInProgress ? i18n[state.lang].chat_responding_status : '';
        statusEl.classList.toggle('is-active', Boolean(isInProgress));
    }

    if (clearBtn) {
        clearBtn.disabled = Boolean(isInProgress);
    }
}

function cancelCurrentChatRequest(options = {}) {
    const { silent = false } = options;

    if (!state.chatAbortController) return;

    state.chatAbortController.abort();
    state.chatAbortController = null;
    state.chatRequestInProgress = false;
    setChatRequestUiState(false);

    const thinkingId = state.chatThinkingMessageId;
    if (thinkingId) {
        const msgDiv = document.getElementById(`msg-${thinkingId}`);
        if (msgDiv) {
            const indicator = msgDiv.querySelector('.typing-indicator-pro');
            if (indicator) indicator.remove();

            const textEl = msgDiv.querySelector('.msg-text');
            if (textEl && !String(textEl.textContent || '').trim()) {
                const stoppedText = i18n[state.lang].chat_response_stopped;
                textEl.textContent = stoppedText;
                textEl.dir = detectTextDirection(stoppedText);
            }
        }
        state.chatThinkingMessageId = null;
    }

    if (!silent) {
        showNotification(i18n[state.lang].chat_response_stopped, 'info');
    }
}

async function handleChatSubmit() {
    const input = document.getElementById('chat-input');
    const projectSelect = document.getElementById('chat-project-select');
    const langSelect = document.getElementById('chat-lang');
    if (!input || !projectSelect || !langSelect) return;

    if (state.chatRequestInProgress) return;

    const query = input.value.trim();
    const projectId = projectSelect.value;
    const language = langSelect.value;

    if (!query) return;
    if (!projectId) {
        showNotification(state.lang === 'ar' ? 'يرجى اختيار مشروع أولاً' : 'Select a project first', 'warning');
        return;
    }

    addChatMessage('user', query);
    input.value = '';
    input.style.height = 'auto';

    const controller = new AbortController();
    state.chatAbortController = controller;
    state.chatRequestInProgress = true;
    setChatRequestUiState(true);

    const thinkingId = addChatMessage('bot', '', true);
    state.chatThinkingMessageId = thinkingId;

    try {
        const payload = { query, language };
        if (Number.isInteger(state.retrievalTopK)) {
            payload.top_k = state.retrievalTopK;
        }

        // ── Stream via SSE (fetch + ReadableStream) ──
        const response = await fetchWithApiRecovery(`/projects/${projectId}/query/stream`, {
            method: 'POST',
            headers: withAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(payload),
            signal: controller.signal,
        });

        if (response.status === 401) {
            clearAuthAndRedirect('expired');
            throw new Error('Unauthorized');
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullAnswer = '';
        let sources = null;

        // Remove typing indicator as soon as first token arrives
        let indicatorRemoved = false;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // keep incomplete line in buffer

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const dataStr = line.slice(6).trim();
                if (dataStr === '[DONE]') continue;

                try {
                    const evt = JSON.parse(dataStr);

                    if (evt.type === 'sources') {
                        sources = evt.sources;
                    } else if (evt.type === 'token') {
                        if (!indicatorRemoved) {
                            const ind = document.querySelector(`#msg-${thinkingId} .typing-indicator-pro`);
                            if (ind) ind.remove();
                            indicatorRemoved = true;
                        }
                        fullAnswer += evt.token;
                        // Live-render the accumulated text
                        const textEl = document.querySelector(`#msg-${thinkingId} .msg-text`);
                        if (textEl) {
                            textEl.classList.add('streaming');
                            textEl.innerHTML = formatAnswerHtml(fullAnswer) || escapeHtml(fullAnswer);
                            textEl.dir = detectTextDirection(fullAnswer);
                        }
                        // Auto-scroll
                        const container = document.getElementById('chat-messages');
                        container.scrollTop = container.scrollHeight;
                    } else if (evt.type === 'error') {
                        fullAnswer = evt.message || i18n[state.lang].error_generic;
                    }
                } catch (_) { /* skip malformed JSON */ }
            }
        }

        // Finalize: attach sources + copy button
        finalizeBotMessage(thinkingId, fullAnswer, sources);
        state.chatThinkingMessageId = null;

    } catch (error) {
        if (error && error.message === 'Unauthorized') {
            return;
        }

        if (isAbortError(error) || controller.signal.aborted) {
            return;
        }

        // Fallback: try non-streaming endpoint
        console.warn('Stream failed, falling back to non-streaming:', error.message);
        try {
            const payload = { query, language };
            if (Number.isInteger(state.retrievalTopK)) {
                payload.top_k = state.retrievalTopK;
            }

            const response = await fetchWithApiRecovery(`/projects/${projectId}/query`, {
                method: 'POST',
                headers: withAuthHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify(payload),
                signal: controller.signal,
            });

            if (response.status === 401) {
                clearAuthAndRedirect('expired');
                throw new Error('Unauthorized');
            }

            if (!response.ok) {
                let errorData = {};
                try {
                    errorData = await response.json();
                } catch (_) {
                    errorData = {};
                }
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const result = await response.json();
            // Remove indicator
            const ind = document.querySelector(`#msg-${thinkingId} .typing-indicator-pro`);
            if (ind) ind.remove();
            finalizeBotMessage(thinkingId, result.answer, result.sources);
            state.chatThinkingMessageId = null;
        } catch (fallbackErr) {
            if (fallbackErr && fallbackErr.message === 'Unauthorized') {
                return;
            }

            if (isAbortError(fallbackErr) || controller.signal.aborted) {
                return;
            }

            const ind = document.querySelector(`#msg-${thinkingId} .typing-indicator-pro`);
            if (ind) ind.remove();
            finalizeBotMessage(thinkingId, i18n[state.lang].error_generic, null);
            state.chatThinkingMessageId = null;
        }
    } finally {
        if (state.chatAbortController === controller) {
            state.chatAbortController = null;
        }
        state.chatRequestInProgress = false;
        setChatRequestUiState(false);
        if (state.chatThinkingMessageId === thinkingId) {
            state.chatThinkingMessageId = null;
        }
    }
}

/**
 * Finalize a bot message by rendering text, attaching sources, and adding copy action.
 */
function finalizeBotMessage(id, text, sources) {
    const msgDiv = document.getElementById(`msg-${id}`);
    if (!msgDiv) return;

    const textEl = msgDiv.querySelector('.msg-text');
    textEl.classList.remove('streaming');
    textEl.innerHTML = formatAnswerHtml(text) || escapeHtml(text);
    textEl.dir = detectTextDirection(text);

    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'msg-sources-pro';
        sourcesDiv.innerHTML = `
            <div class="sources-header">
                <i class="fas fa-book-open"></i>
                <span>${state.lang === 'ar' ? 'المصادر المستخدمة' : 'Sources Used'}</span>
            </div>
        `;
        const list = document.createElement('ul');
        sources.slice(0, 5).forEach(s => {
            const li = document.createElement('li');
            li.innerHTML = `
                <i class="fas fa-file-alt"></i>
                <span>${escapeHtml(s.document_name)}</span>
                <span class="source-score">${(s.similarity * 100).toFixed(0)}%</span>
            `;
            list.appendChild(li);
        });
        sourcesDiv.appendChild(list);
        msgDiv.querySelector('.msg-body').appendChild(sourcesDiv);
    }

    // Copy button
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'msg-actions';
    actionsDiv.innerHTML = `
        <button class="msg-action-btn copy-msg-btn" title="${i18n[state.lang].copy_btn}">
            <i class="fas fa-copy"></i> ${i18n[state.lang].copy_btn}
        </button>
    `;
    actionsDiv.querySelector('.copy-msg-btn').onclick = () => {
        const plainText = textEl.innerText || textEl.textContent;
        navigator.clipboard.writeText(plainText).then(() => {
            const btn = actionsDiv.querySelector('.copy-msg-btn');
            btn.classList.add('copied');
            btn.innerHTML = `<i class="fas fa-check"></i> ${i18n[state.lang].copied_btn}`;
            setTimeout(() => {
                btn.classList.remove('copied');
                btn.innerHTML = `<i class="fas fa-copy"></i> ${i18n[state.lang].copy_btn}`;
            }, 2000);
        });
    };
    msgDiv.querySelector('.msg-body').appendChild(actionsDiv);

    const container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
}

function addChatMessage(role, text, isThinking = false) {
    const messagesContainer = document.getElementById('chat-messages');
    const welcome = messagesContainer.querySelector('.welcome-msg-pro');
    if (welcome) welcome.remove();

    const id = Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg-pro ${role}-msg-pro`;
    msgDiv.id = `msg-${id}`;

    const isUser = role === 'user';
    const authorName = isUser
        ? (state.lang === 'ar' ? 'أنت' : 'You')
        : 'RAGMind';

    // Detect text direction
    const textDir = detectTextDirection(text);

    msgDiv.innerHTML = `
        <div class="msg-inner">
            <div class="msg-avatar-pro">
                ${isUser ? 'U' : '<i class="fas fa-robot"></i>'}
            </div>
            <div class="msg-body">
                <div class="msg-author">${authorName}</div>
                <div class="msg-text" dir="${textDir}">${isUser ? escapeHtml(text) : ''}</div>
                ${isThinking ? '<div class="typing-indicator-pro"><span></span><span></span><span></span></div>' : ''}
            </div>
        </div>
    `;

    if (!isUser && !isThinking) {
        const msgText = msgDiv.querySelector('.msg-text');
        msgText.innerHTML = escapeHtml(text);
        msgText.dir = textDir;
    }

    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return id;
}

function escapeHtml(value) {
    if (value == null) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function detectTextDirection(text) {
    if (!text) return 'auto';
    // Check for Arabic/Hebrew/Persian characters
    const rtlChars = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u0590-\u05FF]/;
    const firstChars = text.trim().substring(0, 50);
    return rtlChars.test(firstChars) ? 'rtl' : 'ltr';
}

function formatAnswerHtml(text) {
    if (!text) return '';

    let cleaned = String(text).replace(/\r\n/g, '\n').trim();
    cleaned = cleaned.replace(/\s*(Source|Sources|المصدر|المصادر)\s*:.*/gi, '').trim();
    cleaned = cleaned.replace(/\s+\*\s+/g, '\n* ');
    cleaned = cleaned.replace(/\s+-\s+/g, '\n- ');

    const lines = cleaned.split('\n').map(line => line.trim()).filter(Boolean);
    if (lines.length === 0) return '';

    const parts = [];
    let listBuffer = [];

    const flushList = () => {
        if (listBuffer.length === 0) return;
        const items = listBuffer
            .map(item => `<li>${formatInlineMarkdown(item)}</li>`)
            .join('');
        parts.push(`<ul class="answer-list">${items}</ul>`);
        listBuffer = [];
    };

    lines.forEach(line => {
        if (/^[*-]\s+/.test(line)) {
            listBuffer.push(line.replace(/^[*-]\s+/, ''));
            return;
        }
        flushList();
        parts.push(`<p class="answer-paragraph">${formatInlineMarkdown(line)}</p>`);
    });

    flushList();
    return parts.join('');
}

function formatInlineMarkdown(value) {
    const escaped = escapeHtml(value);
    return escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
}

function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

// --- Animated Counter ---
function animateCounter(elementId, target) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const duration = 600;
    const start = performance.now();
    const from = 0;

    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // ease-out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(from + (target - from) * eased).toLocaleString();
        if (progress < 1) requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
}

// --- Empty State ---
function createEmptyState(icon, titleKey, descKey) {
    const t = i18n[state.lang];
    return `
        <div class="empty-state">
            <div class="empty-state-icon"><i class="fas ${icon}"></i></div>
            <h3>${t[titleKey] || ''}</h3>
            <p>${t[descKey] || ''}</p>
        </div>
    `;
}

// --- Search ---
function handleSearch(query) {
    const q = query.toLowerCase().trim();
    if (!q) {
        // Restore current view
        switchView(state.currentView, state.selectedProject ? state.selectedProject.id : null);
        return;
    }
    const filtered = state.projects.filter(p =>
        (p.name && p.name.toLowerCase().includes(q)) ||
        (p.description && p.description.toLowerCase().includes(q))
    );
    // Render inline results in current view container
    const list = document.getElementById('all-projects-list') || document.getElementById('recent-projects-list');
    if (list) {
        list.innerHTML = '';
        if (filtered.length === 0) {
            list.innerHTML = createEmptyState('fa-search', 'empty_projects', 'empty_projects_desc');
        } else {
            filtered.forEach(p => list.appendChild(createProjectCard(p)));
        }
    }
}

// --- Mobile Sidebar ---
function openMobileSidebar() {
    document.querySelector('.sidebar').classList.add('open');
    const overlay = document.getElementById('sidebar-overlay');
    overlay.style.display = 'block';
    requestAnimationFrame(() => overlay.classList.add('active'));
}

function closeMobileSidebar() {
    document.querySelector('.sidebar').classList.remove('open');
    const overlay = document.getElementById('sidebar-overlay');
    overlay.classList.remove('active');
    setTimeout(() => { overlay.style.display = 'none'; }, 300);
}

function escapeHtml(value) {
    if (value == null) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function detectTextDirection(text) {
    if (!text) return 'auto';
    // Check for Arabic/Hebrew/Persian characters
    const rtlChars = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u0590-\u05FF]/;
    const firstChars = text.trim().substring(0, 50);
    return rtlChars.test(firstChars) ? 'rtl' : 'ltr';
}

function formatAnswerHtml(text) {
    if (!text) return '';

    let cleaned = String(text).replace(/\r\n/g, '\n').trim();
    cleaned = cleaned.replace(/\s*(Source|Sources|المصدر|المصادر)\s*:.*/gi, '').trim();
    cleaned = cleaned.replace(/\s+\*\s+/g, '\n* ');
    cleaned = cleaned.replace(/\s+-\s+/g, '\n- ');

    const lines = cleaned.split('\n').map(line => line.trim()).filter(Boolean);
    if (lines.length === 0) return '';

    const parts = [];
    let listBuffer = [];

    const flushList = () => {
        if (listBuffer.length === 0) return;
        const items = listBuffer
            .map(item => `<li>${formatInlineMarkdown(item)}</li>`)
            .join('');
        parts.push(`<ul class="answer-list">${items}</ul>`);
        listBuffer = [];
    };

    lines.forEach(line => {
        if (/^[*-]\s+/.test(line)) {
            listBuffer.push(line.replace(/^[*-]\s+/, ''));
            return;
        }
        flushList();
        parts.push(`<p class="answer-paragraph">${formatInlineMarkdown(line)}</p>`);
    });

    flushList();
    return parts.join('');
}

function formatInlineMarkdown(value) {
    const escaped = escapeHtml(value);
    return escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
}

function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

function setupUploadZone(projectId) {
    const zone = document.getElementById('upload-zone');
    const input = document.getElementById('file-input');

    zone.onclick = () => input.click();

    zone.ondragover = (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    };

    zone.ondragleave = () => zone.classList.remove('dragover');

    zone.ondrop = (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files, projectId);
    };

    input.onchange = () => handleFiles(input.files, projectId);
}

async function handleFiles(files, projectId) {
    try {
        const health = await api.get('/health');
        if (health && health.celery_worker !== 'connected') {
            showNotification(
                state.lang === 'ar'
                    ? 'تنبيه: خدمة المعالجة قد تكون غير متصلة حاليًا. سيتم رفع الملف، لكن قد تتأخر المعالجة.'
                    : 'Warning: processing service may be offline. File upload will continue, but processing may be delayed.',
                'warning'
            );
        }
    } catch (_) {
        // If health check fails, proceed and let upload endpoint report specific errors.
    }

    for (const file of files) {
        const lowerName = file.name.toLowerCase();
        if (!lowerName.endsWith('.pdf') && !lowerName.endsWith('.txt') && !lowerName.endsWith('.docx')) {
            showNotification(
                state.lang === 'ar'
                    ? 'نوع الملف غير مدعوم. الملفات المدعومة: PDF, TXT, DOCX'
                    : 'Unsupported file type. Supported: PDF, TXT, DOCX',
                'warning'
            );
            continue;
        }
        const formData = new FormData();
        formData.append('file', file);

        showNotification(`${state.lang === 'ar' ? 'جاري رفع' : 'Uploading'} ${file.name}...`, 'info');

        try {
            await api.post(`/projects/${projectId}/documents`, formData, true);
            showNotification(`${state.lang === 'ar' ? 'تم رفع' : 'Uploaded'} ${file.name}`, 'success');
            switchView('projectDetail', projectId); // Refresh list
        } catch (error) {
            console.error('Upload Error:', error);
        }
    }
}

// --- Initialization ---

document.addEventListener('DOMContentLoaded', async () => {
    const authToken = getAccessToken();
    if (!authToken) {
        redirectToLogin();
        return;
    }
    if (isTokenExpired(authToken)) {
        clearAuthAndRedirect('expired');
        return;
    }

    // Nav Clicks
    elements.navItems.forEach(item => {
        item.onclick = () => {
            closeMobileSidebar();
            switchView(item.dataset.view);
        };
    });

    // New Project Click
    elements.newProjectBtn.onclick = handleNewProject;

    // Close Modal
    elements.closeModalBtn.onclick = () => elements.modalOverlay.classList.add('hidden');
    elements.modalOverlay.onclick = (e) => {
        if (e.target === elements.modalOverlay) elements.modalOverlay.classList.add('hidden');
    };

    // Theme & Lang
    elements.themeToggle.onclick = toggleTheme;
    elements.langToggle.onclick = toggleLang;
    if (elements.logoutBtn) {
        elements.logoutBtn.onclick = logoutUser;
    }

    // Search Bar
    const searchInput = document.querySelector('.search-bar input');
    let searchTimeout;
    if (searchInput) {
        searchInput.oninput = () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => handleSearch(searchInput.value), 300);
        };
        searchInput.onkeydown = (e) => {
            if (e.key === 'Escape') {
                searchInput.value = '';
                handleSearch('');
                searchInput.blur();
            }
        };
    }

    // Mobile Hamburger
    const hamburger = document.getElementById('mobile-hamburger');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    if (hamburger) hamburger.onclick = openMobileSidebar;
    if (sidebarOverlay) sidebarOverlay.onclick = closeMobileSidebar;

    // Keyboard Shortcut: Ctrl+K to focus search
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (searchInput) searchInput.focus();
        }
    });

    // Init State
    applyTheme(state.theme);

    // Initial View
    applyTranslations();
    // Render immediately; API discovery and user hydration continue in the background.
    switchView('dashboard');

    void (async () => {
        const apiReady = await resolveApiBaseUrl(1);
        if (!apiReady) {
            showNotification(state.lang === 'ar' ? 'يجري الاتصال بالخادم في الخلفية...' : 'Connecting to backend in the background...', 'info');
            const recovered = await resolveApiBaseUrl(1);
            if (!recovered) {
                return;
            }
        }

        try {
            await getCurrentUser();
        } catch (error) {
            console.error('Current user load error:', error);
        }
    })();
});
