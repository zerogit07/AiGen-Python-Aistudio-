from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.core.types import ProxyEntry


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f511 Manajemen API Key", callback_data="api_mgmt_menu"),
            InlineKeyboardButton("\U0001f310 Manajemen Proxy", callback_data="admin_proxy"),
        ],
        [
            InlineKeyboardButton("\U0001f9e0 Manajemen Model", callback_data="admin_model"),
            InlineKeyboardButton("\U0001f465 Manajemen Member", callback_data="admin_member"),
        ],
        [
            InlineKeyboardButton("\U0001f5bc Landing Page", callback_data="admin_landing_page"),
            InlineKeyboardButton("\u2699\ufe0f Manajemen Limit", callback_data="admin_lp_limits"),
        ],
        [
            InlineKeyboardButton("\U0001f4e9 Manajemen Pesan", callback_data="admin_msg_mgmt"),
            InlineKeyboardButton("\U0001f4be Manajemen Backup", callback_data="admin_backup_mgmt"),
        ],
        [
            InlineKeyboardButton("\U0001f6aa Logout", callback_data="admin_logout"),
            InlineKeyboardButton("\U0001f4ca Statistik", callback_data="admin_stats"),
        ],
    ])


def get_backup_management_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f465 Backup Data Member", callback_data="admin_backup_members")],
        [InlineKeyboardButton("\U0001f511 Backup Data API Key", callback_data="admin_backup_keys")],
        [InlineKeyboardButton("\U0001f310 Backup Data Proxy", callback_data="admin_backup_proxies")],
        [InlineKeyboardButton("\U0001f4e6 Backup Semua Data", callback_data="admin_backup")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_panel")],
    ])


def get_message_management_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f4e2 Broadcast Global", callback_data="admin_broadcast_all")],
        [InlineKeyboardButton("\U0001f465 Broadcast Member", callback_data="admin_broadcast_member")],
        [InlineKeyboardButton("\U0001f331 Broadcast Trial", callback_data="admin_broadcast_trial")],
        [InlineKeyboardButton("\U0001f4ac Chat Personal", callback_data="admin_chat_personal")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])


def get_stats_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f4cb Daftar User Trial", callback_data="admin_stats_trial")],
        [InlineKeyboardButton("\U0001f48e Daftar User Member", callback_data="admin_stats_member")],
        [InlineKeyboardButton("\U0001f552 Log Aktivitas Terbaru", callback_data="admin_stats_logs")],
        [InlineKeyboardButton("\U0001f50d Cek Akun", callback_data="admin_stats_check_user")],
        [InlineKeyboardButton("\U0001f4ca Statistik Bot Lengkap", callback_data="admin_stats_full")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])


def get_landing_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f3e0 Halaman Awal", callback_data="admin_lp_home")],
        [InlineKeyboardButton("\U0001f4b3 Halaman Payment", callback_data="admin_lp_payment")],
        [InlineKeyboardButton("\U0001f4b0 Manajemen Harga", callback_data="admin_lp_prices")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])


def get_limit_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f331 Limit Lite", callback_data="edit_limit_lite")],
        [InlineKeyboardButton("\u2b50 Limit Pro", callback_data="edit_limit_pro")],
        [InlineKeyboardButton("\U0001f48e Limit Ultra", callback_data="edit_limit_ultra")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])


def get_home_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f5bc Gambar Banner", callback_data="edit_lp_banner_img")],
        [InlineKeyboardButton("\U0001f4dd Deskripsi Banner", callback_data="edit_lp_banner_desc")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_landing_page")],
    ])


def get_payment_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f4f8 Gambar Payment", callback_data="edit_lp_pay_img")],
        [InlineKeyboardButton("\U0001f331 Deskripsi AiGen Lite", callback_data="edit_lp_pay_desc_lite")],
        [InlineKeyboardButton("\u2b50 Deskripsi AiGen Pro", callback_data="edit_lp_pay_desc_pro")],
        [InlineKeyboardButton("\U0001f48e Deskripsi AiGen Ultra", callback_data="edit_lp_pay_desc_ultra")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_landing_page")],
    ])


def get_price_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f331 Harga Lite", callback_data="edit_lp_price_lite")],
        [InlineKeyboardButton("\u2b50 Harga Pro", callback_data="edit_lp_price_pro")],
        [InlineKeyboardButton("\U0001f48e Harga Ultra", callback_data="edit_lp_price_ultra")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_landing_page")],
    ])


def get_proxy_dashboard(all_proxies: list[ProxyEntry]) -> tuple[str, InlineKeyboardMarkup]:
    active_count = sum(1 for p in all_proxies if p.active)
    message = (
        "\U0001f310 *Manajemen Proxy*\n\n"
        "\U0001f4ca *Statistik:*\n"
        f"- Total Proxy: {len(all_proxies)}\n"
        f"- Aktif: \U0001f7e2 {active_count}\n"
        f"- Mati/Nonaktif: \U0001f534 {len(all_proxies) - active_count}\n\n"
        "Pilih menu di bawah untuk mengelola proxy."
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\u2795 Tambah Proxy", callback_data="add_proxy_btn"),
            InlineKeyboardButton("\U0001f504 Cek Semua", callback_data="check_proxy_btn"),
        ],
        [
            InlineKeyboardButton("\U0001f4cb Lihat Daftar", callback_data="list_proxy_btn"),
            InlineKeyboardButton("\U0001f510 Manajemen", callback_data="manage_proxies"),
        ],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])
    return message, keyboard


def get_manage_proxies_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f7e2 Aktifkan Semua", callback_data="enable_all_proxies")],
        [InlineKeyboardButton("\U0001f534 Nonaktifkan Semua", callback_data="disable_all_proxies")],
        [InlineKeyboardButton("\U0001f5d1 Hapus Semua", callback_data="delete_all_proxies")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_proxy")],
    ])


def get_member_dashboard(members: dict, member_count: int, trial_count: int) -> tuple[str, InlineKeyboardMarkup]:
    message = (
        "\U0001f465 *Manajemen Member*\n\n"
        "\U0001f4ca *Statistik:*\n"
        f"- Total Member: {member_count}\n"
        f"- Trial: {trial_count}\n\n"
        "Pilih menu di bawah:"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\u2795 Tambah Member", callback_data="add_member_btn")],
        [InlineKeyboardButton("\U0001f4cb Lihat Member", callback_data="list_member_btn")],
        [InlineKeyboardButton("\U0001f5d1 Hapus Member", callback_data="remove_member_btn")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])
    return message, keyboard


def get_manage_members_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_member")],
    ])


import math

def get_member_list_keyboard(members_list: list, page: int = 1, per_page: int = 15) -> tuple[str, InlineKeyboardMarkup]:
    total = len(members_list)
    total_pages = math.ceil(total / per_page)
    if total_pages == 0:
        total_pages = 1
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
        
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_items = members_list[start_idx:end_idx]
    
    message = f"\U0001f465 *Daftar Member (Halaman {page}/{total_pages})*\n\n"
    
    keyboard = []
    for uid, m in page_items:
        uid_str = str(uid)
        status_icon = "\U0001f7e2" if m.active else "\U0001f534"
        uid_short = uid_str[:8] + ".." if len(uid_str) > 8 else uid_str
        
        row = [
            InlineKeyboardButton(f"\U0001f464 {uid_short}", callback_data=f"v_mem:{uid_str}"),
            InlineKeyboardButton("\U0001f441\ufe0f", callback_data=f"v_mem:{uid_str}"),
            InlineKeyboardButton(status_icon, callback_data=f"t_mem:{uid_str}"),
            InlineKeyboardButton("\U0001f5d1\ufe0f", callback_data=f"d_mem:{uid_str}"),
        ]
        keyboard.append(row)
        
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("\u2b05\ufe0f Prev", callback_data=f"p_mem:{page-1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("Next \u27a1\ufe0f", callback_data=f"p_mem:{page+1}"))
        
    if nav_row:
        keyboard.append(nav_row)
        
    keyboard.append([InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_member")])
    
    return message, InlineKeyboardMarkup(keyboard)


def get_model_management_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f504 Toggle Model", callback_data="toggle_model_btn")],
        [InlineKeyboardButton("\U0001f6a7 Toggle Maintenance", callback_data="toggle_maintenance")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])


def get_manage_models_keyboard(models: list[dict]) -> tuple[str, InlineKeyboardMarkup]:
    lines = ["\U0001f9e0 *Status Model:*\n"]
    buttons: list[list[InlineKeyboardButton]] = []
    for m in models:
        status_icon = "\U0001f7e2 ON" if m["active"] else "\U0001f534 OFF"
        lines.append(f"- {m['name']}: {status_icon}")
        buttons.append([
            InlineKeyboardButton(
                f"{'\U0001f534 OFF' if m['active'] else '\U0001f7e2 ON'} {m['name']}",
                callback_data=f"toggle_model:{m['id']}",
            )
        ])
    buttons.append([InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_model")])
    return "\n".join(lines), InlineKeyboardMarkup(buttons)


def get_api_key_dashboard(keys: list, active_count: int, cooldown_count: int, dead_count: int) -> tuple[str, InlineKeyboardMarkup]:
    message = (
        "\U0001f511 *Manajemen API Key*\n\n"
        "\U0001f4ca *Statistik:*\n"
        f"- Total Key: {len(keys)}\n"
        f"- Aktif: \U0001f7e2 {active_count}\n"
        f"- Cooldown: \U0001f7e1 {cooldown_count}\n"
        f"- Mati: \U0001f534 {dead_count}\n\n"
        "Pilih menu di bawah:"
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\u2795 Tambah Key", callback_data="add_key_btn"),
            InlineKeyboardButton("\U0001f504 Cek Semua", callback_data="test_keys_btn"),
        ],
        [
            InlineKeyboardButton("\U0001f4cb Lihat Daftar", callback_data="list_keys_btn"),
            InlineKeyboardButton("\U0001f510 Manajemen", callback_data="manage_keys"),
        ],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="admin_panel_back")],
    ])
    return message, keyboard


def get_manage_keys_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f7e2 Aktifkan Semua", callback_data="enable_all_keys")],
        [InlineKeyboardButton("\U0001f534 Nonaktifkan Semua", callback_data="disable_all_keys")],
        [InlineKeyboardButton("\U0001f5d1 Hapus Semua", callback_data="delete_all_keys")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="api_mgmt_menu")],
    ])


def get_manage_categorized_keys_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="api_mgmt_menu")],
    ])


def get_usage_history_message(usage_today: int, usage_month: int) -> str:
    return (
        "\U0001f4ca *Statistik Penggunaan*\n\n"
        f"- Hari ini: {usage_today} video\n"
        f"- Bulan ini: {usage_month} video"
    )
