from __future__ import annotations

import logging
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot.handlers.commands import handle_start_command
from src.bot.menus.admin_ui import (
    get_home_page_keyboard,
    get_limit_page_keyboard,
    get_payment_page_keyboard,
    get_price_page_keyboard,
)
from src.bot.panels.kling_v3_panel import get_kv3_state, render_kling_v3_panel
from src.bot.state import (
    ADMIN_IDS,
    get_or_create_state,
    is_user_admin,
    user_state,
)
from src.database.apikeys import api_key_manager
from src.database.members import member_manager
from src.database.models import model_manager
from src.database.proxies import proxy_manager
from src.database.settings import landing_page_manager
from src.database.users import user_manager
from src.core.queue import add_job

logger = logging.getLogger(__name__)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all text messages."""
    user = update.effective_user
    if not user or not update.message or not update.message.text:
        return

    user_id = user.id
    chat_id = update.effective_chat.id
    text = update.message.text

    # Intercept for Kling V3 Panel inputs
    kv3 = get_kv3_state(user_id)
    if kv3.awaiting_input:
        if kv3.awaiting_input == "single_prompt":
            kv3.prompt = text
        elif kv3.awaiting_input.startswith("shot_prompt_"):
            idx = int(kv3.awaiting_input.replace("shot_prompt_", ""))
            if 0 <= idx < len(kv3.shots):
                kv3.shots[idx]["prompt"] = text
        elif kv3.awaiting_input == "element":
            await update.message.reply_text(
                "Input tidak valid. Kirimkan file gambar (bukan teks) untuk Referensi Karakter (Element)."
            )
            return

        if kv3.awaiting_input != "element":
            kv3.awaiting_input = None
            await update.message.reply_text("Input diterima.", parse_mode="Markdown")
            await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=False, force_model=kv3.model_type)
            return

    state = await get_or_create_state(user_id, user.username, user.first_name, user.last_name)

    # Maintenance Check
    if model_manager.is_maintenance() and not is_user_admin(user_id, state):
        await update.message.reply_text(
            "*BOT MAINTENANCE*\n\nBot sedang dalam perawatan rutin untuk peningkatan kualitas. "
            "Silakan kembali lagi nanti ya, Bosku!",
            parse_mode="Markdown",
        )
        return

    # Admin chat start
    if state.waiting_chat_id:
        state.waiting_chat_id = False
        try:
            target_id = int(text)
        except ValueError:
            await update.message.reply_text("User ID harus berupa angka.")
            return
        state.chatting_with = target_id
        state.step = "IN_CHAT"
        await update.message.reply_text(
            f"*CHAT DIMULAI*\n\nAnda sekarang terhubung dengan User ID: `{target_id}`.\n\n"
            f"Semua pesan yang Anda ketik akan dikirim ke user tersebut.\n\n"
            f"Klik tombol di bawah untuk berhenti:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Tutup Chat", callback_data="close_chat")]
            ]),
        )
        return

    # Admin chat in progress
    if state.chatting_with and state.step == "IN_CHAT":
        try:
            await context.bot.send_message(
                chat_id=state.chatting_with,
                text=f"*PESAN DARI ADMIN:*\n\n{text}",
                parse_mode="Markdown",
            )
            await update.message.reply_text(
                "Pesan terkirim.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Tutup Chat", callback_data="close_chat")]
                ]),
            )
        except Exception as exc:
            await update.message.reply_text(f"Gagal mengirim pesan: {exc}")
        return

    # Check if user is replying to admin chat
    for admin_id, admin_state in user_state.items():
        if admin_state.chatting_with == user_id and admin_state.step == "IN_CHAT":
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"*BALASAN DARI USER* (`{user_id}`):\n\n{text}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Tutup Chat", callback_data="close_chat")]
                ]),
            )
            await update.message.reply_text("Balasan Anda telah dikirim ke Admin.")
            return

    # LP settings handlers
    lp_handlers = {
        "waiting_lp_banner_img": ("bannerImage", "Gambar Banner diperbarui!", "url"),
        "waiting_lp_banner_desc": ("bannerDescription", "Deskripsi Banner diperbarui!", "text"),
        "waiting_lp_pay_img": ("paymentImage", "Gambar Payment diperbarui!", "url"),
        "waiting_lp_pay_desc_lite": ("paymentDescriptionLite", "Deskripsi Lite diperbarui!", "text"),
        "waiting_lp_pay_desc_pro": ("paymentDescriptionPro", "Deskripsi Pro diperbarui!", "text"),
        "waiting_lp_pay_desc_ultra": ("paymentDescriptionUltra", "Deskripsi Ultra diperbarui!", "text"),
        "waiting_lp_limit_lite": ("limitLite", None, "number"),
        "waiting_lp_limit_pro": ("limitPro", None, "number"),
        "waiting_lp_limit_ultra": ("limitUltra", None, "number"),
        "waiting_lp_price_lite": ("priceLite", None, "price"),
        "waiting_lp_price_pro": ("pricePro", None, "price"),
        "waiting_lp_price_ultra": ("priceUltra", None, "price"),
    }

    for attr, (setting_key, success_msg, val_type) in lp_handlers.items():
        if getattr(state, attr, False):
            setattr(state, attr, False)
            if val_type == "url" and not text.startswith("http"):
                await update.message.reply_text("Link tidak valid.")
                return
            if val_type == "number":
                try:
                    int(text)
                except ValueError:
                    await update.message.reply_text("Input harus berupa angka.")
                    return
                await landing_page_manager.set_setting(setting_key, text)
                await update.message.reply_text(
                    f"Limit diperbarui menjadi {text} video/hari!",
                    reply_markup=get_limit_page_keyboard(),
                )
                return
            if val_type == "price":
                price = re.sub(r"\D", "", text)
                try:
                    int(price)
                except ValueError:
                    await update.message.reply_text("Input harus berupa angka.")
                    return
                await landing_page_manager.set_setting(setting_key, price)
                formatted = f"{int(price):,}".replace(",", ".")
                await update.message.reply_text(
                    f"Harga diperbarui menjadi Rp{formatted}!",
                    reply_markup=get_price_page_keyboard(),
                )
                return
            await landing_page_manager.set_setting(setting_key, text)
            await update.message.reply_text(success_msg or "Diperbarui!")
            return

    # API Key input
    if state.awaiting_api_key:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        added = 0
        invalid = 0
        for key in lines:
            if key.upper().startswith("FPSX") or len(key) >= 20:
                await api_key_manager.add_key(key)
                added += 1
            else:
                invalid += 1
        state.awaiting_api_key = False
        response = f"Berhasil menambahkan {added} key baru ke pool global."
        if invalid > 0:
            response += f"\n{invalid} key tidak valid (harus diawali 'FPSX')."
        response += f"\nTotal key tersimpan: {len(api_key_manager.get_all_keys())}"
        await update.message.reply_text(response)
        return

    # Proxy input
    if state.waiting_proxy:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for proxy in lines:
            await proxy_manager.add_proxy(proxy)
        state.waiting_proxy = False
        await update.message.reply_text(f"Berhasil menambahkan {len(lines)} proxy.")
        return

    # Add member
    if state.waiting_add_member:
        state.waiting_add_member = False
        parts = text.split()
        if len(parts) < 3:
            await update.message.reply_text("Format: USER_ID PLAN HARI\nContoh: 123456789 pro 30")
            return
        try:
            target_uid = int(parts[0])
            plan = parts[1].lower()
            days = int(parts[2])
        except (ValueError, IndexError):
            await update.message.reply_text("Format tidak valid.")
            return
        if plan not in ("lite", "pro", "ultra", "testing"):
            await update.message.reply_text("Plan harus: lite, pro, ultra, atau testing")
            return
        await member_manager.add_member(target_uid, plan, days)
        await update.message.reply_text(
            f"Member ditambahkan!\nUser: `{target_uid}`\nPlan: {plan}\nDurasi: {days} hari",
            parse_mode="Markdown",
        )
        return

    # Broadcast
    if state.waiting_broadcast:
        state.waiting_broadcast = False
        target = state.broadcast_target or "all"
        users_to_send: list[str] = []
        if target == "all":
            users_to_send = user_manager.get_all_users()
        elif target == "member":
            users_to_send = [
                uid for uid, m in member_manager.get_all_members().items()
                if m.plan in ("lite", "pro", "ultra")
            ]
        elif target == "trial":
            users_to_send = member_manager.get_members_by_plan("testing")

        sent = 0
        failed = 0
        for uid in users_to_send:
            try:
                await context.bot.send_message(chat_id=int(uid), text=text, parse_mode="Markdown")
                sent += 1
            except Exception:
                failed += 1
        await update.message.reply_text(
            f"*Broadcast Selesai*\n- Terkirim: {sent}\n- Gagal: {failed}",
            parse_mode="Markdown",
        )
        return

    # Check user
    if state.waiting_check_user:
        state.waiting_check_user = False
        try:
            target_uid = int(text)
        except ValueError:
            await update.message.reply_text("User ID harus angka.")
            return
        member = member_manager.get_member_data(target_uid)
        user_data = await user_manager.get_user_data(target_uid)
        if not member and not user_data:
            await update.message.reply_text(f"User `{target_uid}` tidak ditemukan.", parse_mode="Markdown")
            return
        info = f"*Info User `{target_uid}`*\n\n"
        if user_data:
            info += f"Username: {user_data.get('username', '-')}\n"
            info += f"Nama: {user_data.get('full_name', '-')}\n"
        if member:
            info += f"Plan: {member.plan}\n"
            info += f"Aktif: {member.active}\n"
            info += f"Expired: {member.expire_date or '-'}\n"
        await update.message.reply_text(info, parse_mode="Markdown")
        return

    # Payment proof
    if state.waiting_payment_proof:
        state.waiting_payment_proof = False
        # Notify admins
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Setujui", callback_data=f"approve_{user_id}_{state.temp_plan}"),
                InlineKeyboardButton("❌ Tolak", callback_data=f"reject_{user_id}")
            ]
        ])
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"*BUKTI PEMBAYARAN BARU*\n\n"
                        f"User: `{user_id}`\n"
                        f"Plan: {state.temp_plan}\n"
                        f"Kode Unik: {state.temp_unique_code}\n\n"
                        f"Pesan: {text}"
                    ),
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            except Exception:
                pass
        await update.message.reply_text(
            "*Bukti pembayaran diterima!*\n\nAdmin akan memverifikasi pembayaran Anda. Mohon tunggu.",
            parse_mode="Markdown",
        )
        return

    # ─── Prompt Input (Generate) ─────────────────────────
    if state.step == "WAIT_PROMPT" and state.model:
        state.temp_prompt = text
        state.step = None
        job_id = await add_job(
            user_id=user_id,
            chat_id=chat_id,
            prompt=text,
            model_id=state.model,
            state=state,
        )
        await update.message.reply_text(f"Permintaanmu masuk antrian. ID job: #{job_id}")
        return


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo messages (for image upload in various flows)."""
    user = update.effective_user
    if not user or not update.message or not update.message.photo:
        return

    user_id = user.id
    chat_id = update.effective_chat.id

    # Get best quality photo
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_url = file.file_path

    # KV3 panel image upload
    kv3 = get_kv3_state(user_id)
    if kv3.awaiting_input:
        if kv3.awaiting_input == "first_frame":
            kv3.first_frame_url = file_url
            kv3.awaiting_input = None
            await update.message.reply_text("First Frame diterima!")
            await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=False, force_model=kv3.model_type)
            return
        elif kv3.awaiting_input == "end_frame":
            kv3.end_frame_url = file_url
            kv3.awaiting_input = None
            await update.message.reply_text("End Frame diterima!")
            await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=False, force_model=kv3.model_type)
            return
        elif kv3.awaiting_input == "element":
            if len(kv3.element_urls) < 3:
                kv3.element_urls.append(file_url)
                await update.message.reply_text(f"Element {len(kv3.element_urls)}/3 diterima!")
                if len(kv3.element_urls) >= 3:
                    kv3.awaiting_input = None
                    await render_kling_v3_panel(context.bot, chat_id, user_id, is_edit=False, force_model=kv3.model_type)
            return

    state = await get_or_create_state(user_id, user.username, user.first_name, user.last_name)

    # Payment proof as photo
    if state.waiting_payment_proof:
        state.waiting_payment_proof = False
        caption = update.message.caption or ""
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Setujui", callback_data=f"approve_{user_id}_{state.temp_plan}"),
                InlineKeyboardButton("❌ Tolak", callback_data=f"reject_{user_id}")
            ]
        ])
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=photo.file_id,
                    caption=(
                        f"*BUKTI PEMBAYARAN BARU*\n\n"
                        f"User: `{user_id}`\n"
                        f"Plan: {state.temp_plan}\n"
                        f"Kode Unik: {state.temp_unique_code}\n"
                        f"Keterangan: {caption}"
                    ),
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            except Exception:
                pass
        await update.message.reply_text(
            "*Bukti pembayaran diterima!*\n\nAdmin akan memverifikasi pembayaran Anda.",
            parse_mode="Markdown",
        )
        return

    # Image for generate (prompt with image)
    if state.step == "WAIT_PROMPT" and state.model:
        state.temp_image_url = file_url
        caption = update.message.caption or ""
        if caption:
            state.temp_prompt = caption
            state.step = None
            job_id = await add_job(
                user_id=user_id,
                chat_id=chat_id,
                prompt=caption,
                model_id=state.model,
                state=state,
            )
            await update.message.reply_text(f"Permintaanmu masuk antrian. ID job: #{job_id}")
        else:
            await update.message.reply_text("🖼 Gambar diterima! Sekarang kirimkan prompt teks Anda:")
        return
