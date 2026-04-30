from __future__ import annotations

import logging
import random
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot.handlers.commands import handle_start_command
from src.bot.menus.admin_ui import (
    get_admin_keyboard,
    get_api_key_dashboard,
    get_backup_management_keyboard,
    get_home_page_keyboard,
    get_landing_page_keyboard,
    get_limit_page_keyboard,
    get_manage_keys_keyboard,
    get_manage_models_keyboard,
    get_manage_proxies_keyboard,
    get_member_dashboard,
    get_message_management_keyboard,
    get_model_management_keyboard,
    get_payment_page_keyboard,
    get_price_page_keyboard,
    get_proxy_dashboard,
    get_stats_menu_keyboard,
    get_usage_history_message,
)
from src.bot.menus.main import get_main_keyboard
from src.bot.menus.models_ui import (
    get_kling21_config_keyboard,
    get_kling25_turbo_config_keyboard,
    get_kling26_motion_config_keyboard,
    get_kling26_pro_config_keyboard,
    get_nano_banana_config_keyboard,
    get_veo31_config_keyboard,
)
from src.bot.panels.kling_v3_panel import (
    get_kv3_state,
    render_kling_v3_panel,
)
from src.bot.state import get_or_create_state, is_user_admin, user_state
from src.database.apikeys import api_key_manager
from src.database.members import member_manager
from src.database.models import model_manager
from src.database.proxies import proxy_manager
from src.database.settings import landing_page_manager
from src.database.usage import usage_manager
from src.database.users import user_manager
from src.core.queue import add_job, add_check_single_key_job

_last_key_check = {}
from src.services.polling import mark_buttons_used
from src.services.stats import global_logs, global_stats

logger = logging.getLogger(__name__)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    user_id = query.from_user.id
    data = query.data
    chat_id = update.effective_chat.id
    logger.info("[CallbackQuery] User: %d, Data: %s", user_id, data)
    state = await get_or_create_state(user_id, query.from_user.username, query.from_user.first_name, query.from_user.last_name)

    # ─── KV3 Panel Callbacks ─────────────────────────────
    kv3 = get_kv3_state(user_id)

    if data == "kv3_use_again":
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=False)
        return

    if data == "ko1_use_again":
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=False, force_model="kling_o1")
        return

    if data == "kv3_edit_prompt":
        kv3.awaiting_input = "single_prompt"
        await context.bot.send_message(chat_id=chat_id, text="📝 Kirimkan prompt teks Anda:")
        return

    if data == "kv3_upload_first_frame":
        kv3.awaiting_input = "first_frame"
        await context.bot.send_message(chat_id=chat_id, text="🖼 Kirimkan gambar untuk First Frame:")
        return

    if data == "kv3_upload_end_frame":
        kv3.awaiting_input = "end_frame"
        await context.bot.send_message(chat_id=chat_id, text="🖼 Kirimkan gambar untuk End Frame:")
        return

    if data == "kv3_upload_element":
        kv3.awaiting_input = "element"
        await context.bot.send_message(chat_id=chat_id, text="🖼 Kirimkan file gambar untuk Referensi Karakter (Element). Maks 3 gambar.")
        return

    if data == "kv3_change_duration":
        kv3.panel_view = "choose_main_duration"
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=True)
        return

    if data == "kv3_change_resolution":
        kv3.panel_view = "choose_resolution"
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=True)
        return

    if data == "kv3_change_ratio":
        kv3.panel_view = "choose_ratio"
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=True)
        return

    if data == "kv3_toggle_audio":
        kv3.audio = not kv3.audio
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=True)
        return

    if data == "kv3_multishot_on":
        kv3.multi_shot_on = True
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=True)
        return

    if data == "kv3_multishot_off":
        kv3.multi_shot_on = False
        kv3.shots = []
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=True)
        return

    if data == "kv3_add_shot":
        kv3.shots.append({"prompt": "", "duration": 5})
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=True)
        return

    if data == "kv3_close_subpanel":
        kv3.panel_view = "main"
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=True)
        return

    if data.startswith("kv3_set_main_dur_"):
        dur = data.replace("kv3_set_main_dur_", "")
        kv3.duration = f"{dur}s"
        kv3.panel_view = "main"
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=True)
        return

    if data.startswith("kv3_set_res_"):
        kv3.resolution = data.replace("kv3_set_res_", "")
        kv3.panel_view = "main"
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=True)
        return

    if data.startswith("kv3_set_ratio_"):
        kv3.ratio = data.replace("kv3_set_ratio_", "")
        kv3.panel_view = "main"
        await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=True)
        return

    if data == "kv3_generate":
        if not kv3.prompt:
            await context.bot.send_message(chat_id=chat_id, text="❌ Prompt masih kosong! Silakan isi prompt terlebih dahulu.")
            return
        # Map KV3 state to UserState and finalize
        state.model = kv3.model_type
        state.temp_prompt = kv3.prompt
        state.duration = kv3.duration.replace("s", "")
        state.resolution = kv3.resolution.replace("p", "")
        state.aspect_ratio = (
            "widescreen_16_9" if kv3.ratio == "16:9"
            else "portrait_9_16" if kv3.ratio == "9:16"
            else "square_1_1"
        )
        state.generate_audio = kv3.audio
        state.temp_image_url = kv3.first_frame_url
        state.temp_image_url_last = kv3.end_frame_url
        state.temp_image_refs = kv3.element_urls
        state.shots = []
        if kv3.multi_shot_on and kv3.shots:
            from src.core.types import Shot
            state.shots = [Shot(prompt=s.get("prompt", ""), duration=s.get("duration", 5)) for s in kv3.shots]
            state.kling3_mode = "multi_customize"
        else:
            state.kling3_mode = "single"

        job_id = await add_job(
            user_id=user_id,
            chat_id=chat_id,
            prompt=kv3.prompt,
            model_id=kv3.model_type,
            state=state,
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Permintaanmu masuk antrian. ID job: #{job_id}",
        )
        return

    # ─── Use Again Callbacks ─────────────────────────────
    if data == "k26m_use_again":
        state.orientation = "video"
        state.resolution = "720"
        state.step = "WAIT_ORIENTATION"
        msg, kb = get_kling26_motion_config_keyboard(state)
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "nano_banana_flash":
        state.model = "nano_banana_flash"
        state.resolution = "1k"
        state.aspect_ratio = "portrait_9_16"
        state.step = "WAIT_RESOLUTION"
        msg, kb = get_nano_banana_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "nano_use_again":
        state.model = "nano_banana_flash"
        state.resolution = "1k"
        state.aspect_ratio = "portrait_9_16"
        state.step = "WAIT_RESOLUTION"
        msg, kb = get_nano_banana_config_keyboard(state)
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "veo31_use_again":
        state.model = "veo_3_1_fast"
        state.resolution = "720"
        state.aspect_ratio = "portrait_9_16"
        state.duration = "8"
        state.generate_audio = True
        state.step = "WAIT_RESOLUTION"
        msg, kb = get_veo31_config_keyboard(state)
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "k21_use_again":
        state.resolution = "720"
        state.duration = "5"
        state.aspect_ratio = "portrait_9_16"
        state.step = "WAIT_RESOLUTION"
        msg, kb = get_kling21_config_keyboard(state)
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "k21_change_model" or data == "finish_change":
        if query.message:
            mark_buttons_used(query.message.message_id, chat_id)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        await handle_start_command(update, context, is_edit=False)
        return

    # ─── Finish Again Routing ────────────────────────────
    if data.startswith("finish_again:"):
        if query.message:
            mark_buttons_used(query.message.message_id, chat_id)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        model_id = data.split(":")[1]
        state.model = model_id
        state.total_duration = 0
        state.current_shot_index = 0
        state.shots = []
        state.temp_prompt = None
        state.temp_image_url = None
        state.temp_image_url_last = None
        state.temp_video_url = None
        state.temp_image_refs = []

        if model_id == "kling_2_5_turbo":
            state.resolution = "1080"
            state.duration = "5"
            state.aspect_ratio = "portrait_9_16"
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_kling25_turbo_config_keyboard(state)
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif model_id == "kling_2_6_pro":
            state.resolution = "1080"
            state.duration = "5"
            state.generate_audio = True
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_kling26_pro_config_keyboard(state)
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif "kling_2_6_motion" in model_id:
            state.orientation = "video"
            state.resolution = "720"
            state.step = "WAIT_ORIENTATION"
            msg, kb = get_kling26_motion_config_keyboard(state)
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif "kling_v3" in model_id:
            await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=False, force_model=model_id)
        elif "kling_o1" in model_id:
            await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=False, force_model="kling_o1")
        elif "veo_3_1" in model_id:
            state.model = "veo_3_1_fast"
            state.resolution = "720"
            state.aspect_ratio = "portrait_9_16"
            state.duration = "8"
            state.step = "WAIT_MODEL_TYPE"
            msg, kb = get_veo31_config_keyboard(state)
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif "nano_" in model_id:
            state.model = "nano_banana_flash"
            state.resolution = "1k"
            state.aspect_ratio = "portrait_9_16"
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_nano_banana_config_keyboard(state)
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        else:
            state.resolution = "720"
            state.duration = "5"
            state.aspect_ratio = "portrait_9_16"
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_kling21_config_keyboard(state)
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    # ─── Model Selection ─────────────────────────────────
    if data.startswith("model:"):
        model_id = data.split(":")[1]
        state.model = model_id
        state.temp_prompt = None
        state.temp_image_url = None
        state.temp_image_url_last = None
        state.temp_video_url = None
        state.temp_image_refs = []
        state.shots = []

        if model_id in ("kling_v3", "kling_v3_omni"):
            await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=False, force_model=model_id)
        elif model_id == "kling_o1":
            await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=False, force_model="kling_o1")
        elif model_id == "nano_banana_flash":
            state.resolution = "1k"
            state.aspect_ratio = "portrait_9_16"
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_nano_banana_config_keyboard(state)
            try:
                await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif model_id == "veo_3_1":
            state.model = "veo_3_1_fast"
            state.resolution = "720"
            state.aspect_ratio = "portrait_9_16"
            state.duration = "8"
            state.generate_audio = True
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_veo31_config_keyboard(state)
            try:
                await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif "kling_2_6_motion" in model_id:
            state.orientation = "video"
            state.resolution = "720"
            state.step = "WAIT_ORIENTATION"
            msg, kb = get_kling26_motion_config_keyboard(state)
            try:
                await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif model_id == "kling_2_6_pro":
            state.resolution = "1080"
            state.duration = "5"
            state.generate_audio = True
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_kling26_pro_config_keyboard(state)
            try:
                await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        elif model_id == "kling_2_5_turbo":
            state.resolution = "1080"
            state.duration = "5"
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_kling25_turbo_config_keyboard(state)
            try:
                await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        else:
            # Default Kling 2.1
            state.resolution = "720"
            state.duration = "5"
            state.aspect_ratio = "portrait_9_16"
            state.step = "WAIT_RESOLUTION"
            msg, kb = get_kling21_config_keyboard(state)
            try:
                await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    # ─── Config Callbacks (Nano, Veo, Kling) ─────────────
    if data.startswith("nano_mod:"):
        val = data.split(":")[1]
        state.model = "nano_banana_pro" if val == "pro" else "nano_banana_flash"
        msg, kb = get_nano_banana_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("nano_res:"):
        state.resolution = data.split(":")[1]
        msg, kb = get_nano_banana_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("nano_rat:"):
        state.aspect_ratio = data.split(":")[1]
        msg, kb = get_nano_banana_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "nano_continue":
        state.step = "WAIT_PROMPT"
        await context.bot.send_message(chat_id=chat_id, text="📝 Kirimkan prompt teks Anda untuk generate gambar:")
        return

    if data.startswith("veo31_mod:"):
        val = data.split(":")[1]
        state.model = "veo_3_1_standard" if val == "standard" else "veo_3_1_fast"
        msg, kb = get_veo31_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("veo31_res:"):
        state.resolution = data.split(":")[1]
        msg, kb = get_veo31_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("veo31_rat:"):
        state.aspect_ratio = data.split(":")[1]
        msg, kb = get_veo31_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("veo31_dur:"):
        state.duration = data.split(":")[1]
        msg, kb = get_veo31_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("veo31_aud:"):
        state.generate_audio = data.split(":")[1] == "on"
        msg, kb = get_veo31_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "veo31_continue":
        state.step = "WAIT_PROMPT"
        await context.bot.send_message(chat_id=chat_id, text="📝 Kirimkan prompt teks Anda untuk generate video:")
        return

    if data.startswith("k26m_ori:"):
        state.orientation = data.split(":")[1]
        msg, kb = get_kling26_motion_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("k26m_res:"):
        state.resolution = data.split(":")[1]
        msg, kb = get_kling26_motion_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "k26m_continue":
        state.step = "WAIT_PROMPT"
        await context.bot.send_message(chat_id=chat_id, text="📝 Kirimkan prompt dan gambar Anda untuk generate:")
        return

    # Kling 2.1 config
    if data.startswith("k21_res:"):
        state.resolution = data.split(":")[1]
        msg, kb = get_kling21_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("k21_dur:"):
        state.duration = data.split(":")[1]
        msg, kb = get_kling21_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("k21_rat:"):
        state.aspect_ratio = data.split(":")[1]
        msg, kb = get_kling21_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "k21_continue":
        state.step = "WAIT_PROMPT"
        await context.bot.send_message(chat_id=chat_id, text="📝 Kirimkan prompt teks Anda:")
        return

    # Kling 2.6 Pro / 2.5 Turbo config
    if data.startswith("k26p_res:") or data.startswith("k25t_res:"):
        state.resolution = data.split(":")[1]
        if data.startswith("k26p"):
            msg, kb = get_kling26_pro_config_keyboard(state)
        else:
            msg, kb = get_kling25_turbo_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data.startswith("k26p_dur:") or data.startswith("k25t_dur:"):
        state.duration = data.split(":")[1]
        if data.startswith("k26p"):
            msg, kb = get_kling26_pro_config_keyboard(state)
        else:
            msg, kb = get_kling25_turbo_config_keyboard(state)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data in ("k26p_continue", "k25t_continue"):
        state.step = "WAIT_PROMPT"
        await context.bot.send_message(chat_id=chat_id, text="📝 Kirimkan prompt dan gambar Anda:")
        return

    # ─── Subscription / Payment ──────────────────────────
    if data in ("lite", "pro", "ultra"):
        state.temp_plan = data
        unique_code = random.randint(1, 999)
        state.temp_unique_code = unique_code

        key_map = {"lite": "priceLite", "pro": "pricePro", "ultra": "priceUltra"}
        base_price = int(landing_page_manager.get_setting(key_map[data]) or "0")
        total_price = base_price + unique_code
        formatted = f"{total_price:,}".replace(",", ".")

        desc_map = {"lite": "paymentDescriptionLite", "pro": "paymentDescriptionPro", "ultra": "paymentDescriptionUltra"}
        description = landing_page_manager.get_setting(desc_map[data])
        payment_image = landing_page_manager.get_setting("paymentImage")

        message = (
            f"*PEMBAYARAN PAKET {data.upper()}*\n\n"
            f"{description}\n\n"
            f"*PENTING:*\n"
            f"Silakan transfer sebesar:\n"
            f"*Rp {formatted}*\n\n"
            f"_(Mohon transfer tepat hingga 3 angka terakhir agar verifikasi otomatis lebih cepat)_\n\n"
            f"Silahkan scan QRIS diatas untuk pembayaran lalu kirim bukti pembayaran"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Kirim Bukti Transfer", callback_data="confirm_payment")],
            [InlineKeyboardButton("Kembali", callback_data="back_to_banner")],
        ])

        try:
            await query.edit_message_media(
                media={"type": "photo", "media": payment_image, "caption": message, "parse_mode": "Markdown"},
                reply_markup=keyboard,
            )
        except Exception:
            await context.bot.send_photo(chat_id=chat_id, photo=payment_image, caption=message, parse_mode="Markdown", reply_markup=keyboard)
        return

    if data == "back_to_banner":
        await handle_start_command(update, context, is_edit=True)
        return

    if data == "free_trial":
        existing = await member_manager.sync_member(user_id)
        if existing:
            await context.bot.send_message(chat_id=chat_id, text="\u274c Anda sudah pernah menggunakan Free Trial.")
            return
        await member_manager.add_member(user_id, "testing", days=30, testing_quota=3)
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_message(chat_id=chat_id, text="\U0001f381 *FREE TRIAL AKTIF!*\n\nAnda mendapat 3 kuota percobaan gratis.", parse_mode="Markdown")
        await handle_start_command(update, context, is_edit=False)
        return

    if data == "confirm_payment":
        state.waiting_payment_proof = True
        await context.bot.send_message(chat_id=chat_id, text="📸 Silakan kirim screenshot/bukti transfer Anda:")
        return

    if data == "show_plans":
        banner_url = landing_page_manager.get_setting("bannerImage")
        description = landing_page_manager.get_setting("bannerDescription")
        existing = await member_manager.sync_member(user_id)
        bottom_row = []
        if not existing:
            bottom_row.append(InlineKeyboardButton("\U0001f381 Free Trial", callback_data="free_trial"))
        bottom_row.append(InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="back_main"))
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("\U0001f331 Lite", callback_data="lite"),
                InlineKeyboardButton("\u2b50 Pro", callback_data="pro"),
                InlineKeyboardButton("\U0001f48e Ultra", callback_data="ultra"),
            ],
            bottom_row,
        ])
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=banner_url,
            caption=description,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
        return

    if data == "back_main":
        await handle_start_command(update, context, is_edit=True)
        return

    # ─── Admin Panel ─────────────────────────────────────
    if data == "admin_panel" or data == "admin_panel_back":
        if is_user_admin(user_id, state):
            try:
                await query.edit_message_text(text="🛠 *Admin Panel*", parse_mode="Markdown", reply_markup=get_admin_keyboard())
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text="🛠 *Admin Panel*", parse_mode="Markdown", reply_markup=get_admin_keyboard())
        return

    if data == "admin_logout":
        state.is_admin = False
        state.is_admin_panel = False
        await handle_start_command(update, context, is_edit=True)
        return

    # API Key Management
    if data == "api_mgmt_menu":
        if not is_user_admin(user_id, state):
            return
        keys = api_key_manager.get_all_keys()
        now = int(time.time() * 1000)
        active = sum(1 for k in keys if k.active and k.cooldown_until < now)
        cooldown = sum(1 for k in keys if k.active and k.cooldown_until >= now)
        dead = sum(1 for k in keys if not k.active)
        msg, kb = get_api_key_dashboard(keys, active, cooldown, dead)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "add_key_btn":
        state.awaiting_api_key = True
        await context.bot.send_message(chat_id=chat_id, text="🔑 Kirimkan API Key Freepik (satu per baris):")
        return

    if data == "test_keys_btn":
        if not is_user_admin(user_id, state):
            return
            
        now = time.time()
        if user_id in _last_key_check and now - _last_key_check[user_id] < 120:
            await context.bot.send_message(chat_id=chat_id, text="⏳ Harap tunggu 120 detik sebelum melakukan cek key lagi.")
            return
        
        _last_key_check[user_id] = now
        
        keys = api_key_manager.get_all_keys()
        if not keys:
            await context.bot.send_message(chat_id=chat_id, text="❌ Tidak ada API key untuk diuji.")
            return

        batch_id = f"batch_keys_{user_id}_{int(time.time())}"
        from src.core.queue import init_key_check_batch, _get_redis_pool
        await init_key_check_batch(batch_id, len(keys))
            
        count = 0
        for i, k in enumerate(keys, 1):
            key_label = f"Key #{i}"
            try:
                await add_check_single_key_job(admin_id=user_id, chat_id=chat_id, api_key=k.key, key_label=key_label, batch_id=batch_id)
                count += 1
            except Exception as e:
                logger.error("Gagal enqueue %s: %s", key_label, e)
                # Ensure the total count is still met by pushing a failure directly
                try:
                    redis = await _get_redis_pool()
                    if len(k.key) >= 8:
                        masked = f"{k.key[:4]}****{k.key[-4:]}"
                    else:
                        masked = "****"
                    await redis.rpush(f"check_batch_results:{batch_id}", f"🔑 {key_label} (`{masked}`): ❌ Failed (Enqueue Error)")
                except Exception:
                    pass
                
        await context.bot.send_message(chat_id=chat_id, text=f"⏳ {count} permintaan cek API key masuk antrian. Hasil akan direkap dalam satu laporan setelah semua selesai.")
        return

    if data == "enable_all_keys":
        await api_key_manager.enable_all()
        keys = api_key_manager.get_all_keys()
        now = int(time.time() * 1000)
        active = sum(1 for k in keys if k.active and k.cooldown_until < now)
        cooldown = sum(1 for k in keys if k.active and k.cooldown_until >= now)
        dead = sum(1 for k in keys if not k.active)
        msg, kb = get_api_key_dashboard(keys, active, cooldown, dead)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="🟢 Semua key diaktifkan!")
        return

    if data == "manage_keys":
        try:
            await query.edit_message_text(text="🔑 *Manajemen Key*", parse_mode="Markdown", reply_markup=get_manage_keys_keyboard())
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="🔑 *Manajemen Key*", parse_mode="Markdown", reply_markup=get_manage_keys_keyboard())
        return

    if data == "list_keys_btn":
        keys = api_key_manager.get_all_keys()
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="api_mgmt_menu")]])
        if not keys:
            try:
                await query.edit_message_text(text="❌ Tidak ada API key tersimpan.", reply_markup=back_kb)
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text="❌ Tidak ada API key tersimpan.", reply_markup=back_kb)
            return
        now = int(time.time() * 1000)
        lines = ["*Daftar API Key:*\n"]
        for i, k in enumerate(keys, 1):
            status = "ON" if k.active and k.cooldown_until < now else ("CD" if k.active else "OFF")
            lines.append(f"{i}. `{k.key[:12]}...` [{status}]")
        try:
            await query.edit_message_text(text="\n".join(lines), parse_mode="Markdown", reply_markup=back_kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="\n".join(lines), parse_mode="Markdown", reply_markup=back_kb)
        return

    # Proxy Management
    if data == "admin_proxy":
        if not is_user_admin(user_id, state):
            return
        msg, kb = get_proxy_dashboard(proxy_manager.get_all_proxies())
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "add_proxy_btn":
        state.waiting_proxy = True
        await context.bot.send_message(chat_id=chat_id, text="🌐 Kirimkan proxy (satu per baris, format: http://user:pass@host:port):")
        return

    if data == "check_proxy_btn":
        await context.bot.send_message(chat_id=chat_id, text="⏳ Sedang mengecek semua proxy...")
        result = await proxy_manager.check_all_proxies()
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🌐 *Hasil Cek Proxy:*\n- Aktif: 🟢 {result['active_count']}\n- Mati: 🔴 {result['dead_count']}\n- Total: {result['total']}",
            parse_mode="Markdown",
        )
        return

    if data == "manage_proxies":
        try:
            await query.edit_message_text(text="🌐 *Manajemen Proxy*", parse_mode="Markdown", reply_markup=get_manage_proxies_keyboard())
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="🌐 *Manajemen Proxy*", parse_mode="Markdown", reply_markup=get_manage_proxies_keyboard())
        return

    if data == "enable_all_proxies":
        await proxy_manager.enable_all()
        msg, kb = get_proxy_dashboard(proxy_manager.get_all_proxies())
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="🟢 Semua proxy diaktifkan!")
        return

    if data == "disable_all_proxies":
        await proxy_manager.disable_all()
        msg, kb = get_proxy_dashboard(proxy_manager.get_all_proxies())
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="🔴 Semua proxy dinonaktifkan!")
        return

    if data == "delete_all_proxies":
        await proxy_manager.delete_all()
        msg, kb = get_proxy_dashboard(proxy_manager.get_all_proxies())
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="🗑 Semua proxy dihapus!")
        return

    # Model Management
    if data == "admin_model":
        if not is_user_admin(user_id, state):
            return
        try:
            await query.edit_message_text(text="\U0001f9e0 *Manajemen Model*", parse_mode="Markdown", reply_markup=get_model_management_keyboard())
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="\U0001f9e0 *Manajemen Model*", parse_mode="Markdown", reply_markup=get_model_management_keyboard())
        return

    if data == "toggle_model_btn":
        if not is_user_admin(user_id, state):
            return
        msg, kb = get_manage_models_keyboard(model_manager.get_all_models_with_status())
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data.startswith("toggle_model:"):
        model_id = data.split(":")[1]
        await model_manager.toggle_model(model_id)
        msg, kb = get_manage_models_keyboard(model_manager.get_all_models_with_status())
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if data == "toggle_maintenance":
        new_state = await model_manager.toggle_maintenance()
        try:
            status = "\U0001f7e2 ON" if new_state else "\U0001f534 OFF"
            await query.edit_message_text(text=f"\U0001f9e0 *Manajemen Model*\n\n\U0001f6a7 *Maintenance Mode:* {status}", parse_mode="Markdown", reply_markup=get_model_management_keyboard())
        except Exception:
            status = "\U0001f7e2 ON" if new_state else "\U0001f534 OFF"
            await context.bot.send_message(chat_id=chat_id, text=f"\U0001f6a7 *Maintenance Mode:* {status}", parse_mode="Markdown")
        return

    # Member Management
    if data == "admin_member":
        if not is_user_admin(user_id, state):
            return
        members = member_manager.get_all_members()
        member_count = sum(1 for m in members.values() if m.plan in ("lite", "pro", "ultra"))
        trial_count = sum(1 for m in members.values() if m.plan == "testing")
        msg, kb = get_member_dashboard(members, member_count, trial_count)
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=kb)
        return

    if data == "add_member_btn":
        state.waiting_add_member = True
        await context.bot.send_message(
            chat_id=chat_id,
            text="👥 Kirimkan dalam format:\n`USER_ID PLAN HARI`\n\nContoh: `123456789 pro 30`",
            parse_mode="Markdown",
        )
        return

    # Stats
    if data == "admin_stats":
        if not is_user_admin(user_id, state):
            return
        try:
            await query.edit_message_text(text="📊 *Statistik*", parse_mode="Markdown", reply_markup=get_stats_menu_keyboard())
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="📊 *Statistik*", parse_mode="Markdown", reply_markup=get_stats_menu_keyboard())
        return

    if data == "admin_stats_full":
        usage_today = usage_manager.get_total_usage_today()
        usage_month = usage_manager.get_total_usage_month()
        msg = get_usage_history_message(usage_today, usage_month)
        msg += f"\n\n*Global Stats:*\n- Total video: {global_stats.total_videos}\n"
        for m_id, count in global_stats.model_usage.items():
            msg += f"  - {m_id}: {count}\n"
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="admin_stats")]])
        try:
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=back_kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", reply_markup=back_kb)
        return

    if data == "admin_stats_logs":
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="admin_stats")]])
        if not global_logs:
            try:
                await query.edit_message_text(text="📋 Belum ada log aktivitas.", reply_markup=back_kb)
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text="📋 Belum ada log aktivitas.", reply_markup=back_kb)
            return
        lines = ["*Log Aktivitas Terbaru:*\n"]
        for log in global_logs[:20]:
            lines.append(f"- User `{log.user_id}` | {log.model_id} | {log.prompt[:30]}")
        try:
            await query.edit_message_text(text="\n".join(lines), parse_mode="Markdown", reply_markup=back_kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="\n".join(lines), parse_mode="Markdown", reply_markup=back_kb)
        return

    if data == "admin_stats_check_user":
        state.waiting_check_user = True
        await context.bot.send_message(chat_id=chat_id, text="🔍 Kirimkan User ID yang ingin dicek:")
        return

    # Landing Page
    if data == "admin_landing_page":
        if not is_user_admin(user_id, state):
            return
        try:
            await query.edit_message_text(text="🖼 *Landing Page*", parse_mode="Markdown", reply_markup=get_landing_page_keyboard())
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="🖼 *Landing Page*", parse_mode="Markdown", reply_markup=get_landing_page_keyboard())
        return

    if data == "admin_lp_home":
        try:
            await query.edit_message_text(text="🏠 *Halaman Awal*", parse_mode="Markdown", reply_markup=get_home_page_keyboard())
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="🏠 *Halaman Awal*", parse_mode="Markdown", reply_markup=get_home_page_keyboard())
        return

    if data == "admin_lp_payment":
        try:
            await query.edit_message_text(text="💳 *Halaman Payment*", parse_mode="Markdown", reply_markup=get_payment_page_keyboard())
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="💳 *Halaman Payment*", parse_mode="Markdown", reply_markup=get_payment_page_keyboard())
        return

    if data == "admin_lp_prices":
        try:
            await query.edit_message_text(text="💰 *Manajemen Harga*", parse_mode="Markdown", reply_markup=get_price_page_keyboard())
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="💰 *Manajemen Harga*", parse_mode="Markdown", reply_markup=get_price_page_keyboard())
        return

    if data == "admin_lp_limits":
        try:
            await query.edit_message_text(text="⚙️ *Manajemen Limit*", parse_mode="Markdown", reply_markup=get_limit_page_keyboard())
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="⚙️ *Manajemen Limit*", parse_mode="Markdown", reply_markup=get_limit_page_keyboard())
        return

    # Edit LP settings
    lp_edit_map = {
        "edit_lp_banner_img": ("waiting_lp_banner_img", "Kirimkan URL gambar banner baru:"),
        "edit_lp_banner_desc": ("waiting_lp_banner_desc", "Kirimkan deskripsi banner baru (Markdown):"),
        "edit_lp_pay_img": ("waiting_lp_pay_img", "Kirimkan URL gambar payment baru:"),
        "edit_lp_pay_desc_lite": ("waiting_lp_pay_desc_lite", "Kirimkan deskripsi paket Lite baru:"),
        "edit_lp_pay_desc_pro": ("waiting_lp_pay_desc_pro", "Kirimkan deskripsi paket Pro baru:"),
        "edit_lp_pay_desc_ultra": ("waiting_lp_pay_desc_ultra", "Kirimkan deskripsi paket Ultra baru:"),
        "edit_limit_lite": ("waiting_lp_limit_lite", "Kirimkan limit harian baru untuk Lite (angka):"),
        "edit_limit_pro": ("waiting_lp_limit_pro", "Kirimkan limit harian baru untuk Pro (angka):"),
        "edit_limit_ultra": ("waiting_lp_limit_ultra", "Kirimkan limit harian baru untuk Ultra (angka):"),
        "edit_lp_price_lite": ("waiting_lp_price_lite", "Kirimkan harga baru untuk Lite (angka):"),
        "edit_lp_price_pro": ("waiting_lp_price_pro", "Kirimkan harga baru untuk Pro (angka):"),
        "edit_lp_price_ultra": ("waiting_lp_price_ultra", "Kirimkan harga baru untuk Ultra (angka):"),
    }

    if data in lp_edit_map:
        attr, prompt_text = lp_edit_map[data]
        setattr(state, attr, True)
        await context.bot.send_message(chat_id=chat_id, text=prompt_text)
        return

    # Message Management
    if data == "admin_msg_mgmt":
        if not is_user_admin(user_id, state):
            return
        try:
            await query.edit_message_text(text="📩 *Manajemen Pesan*", parse_mode="Markdown", reply_markup=get_message_management_keyboard())
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="📩 *Manajemen Pesan*", parse_mode="Markdown", reply_markup=get_message_management_keyboard())
        return

    if data in ("admin_broadcast_all", "admin_broadcast_member", "admin_broadcast_trial"):
        state.waiting_broadcast = True
        target_map = {"admin_broadcast_all": "all", "admin_broadcast_member": "member", "admin_broadcast_trial": "trial"}
        state.broadcast_target = target_map[data]
        await context.bot.send_message(chat_id=chat_id, text=f"Kirimkan pesan broadcast untuk target *{state.broadcast_target}*:", parse_mode="Markdown")
        return

    if data == "admin_chat_personal":
        state.waiting_chat_id = True
        await context.bot.send_message(chat_id=chat_id, text="💬 Kirimkan User ID yang ingin Anda ajak chat:")
        return

    if data == "close_chat":
        state.chatting_with = None
        state.step = None
        await context.bot.send_message(chat_id=chat_id, text="🚪 Chat ditutup.")
        return

    # Backup Management
    if data == "admin_backup_mgmt":
        if not is_user_admin(user_id, state):
            return
        try:
            await query.edit_message_text(text="💾 *Manajemen Backup*", parse_mode="Markdown", reply_markup=get_backup_management_keyboard())
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="💾 *Manajemen Backup*", parse_mode="Markdown", reply_markup=get_backup_management_keyboard())
        return

    if data == "admin_backup":
        members = member_manager.get_all_members()
        keys = api_key_manager.get_all_keys()
        proxies = proxy_manager.get_all_proxies()
        backup = f"Members: {len(members)}\nKeys: {len(keys)}\nProxies: {len(proxies)}"
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="admin_backup_mgmt")]])
        try:
            await query.edit_message_text(text=f"*Backup Data:*\n\n{backup}", parse_mode="Markdown", reply_markup=back_kb)
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text=f"*Backup Data:*\n\n{backup}", parse_mode="Markdown", reply_markup=back_kb)
        return
