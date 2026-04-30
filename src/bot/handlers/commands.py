from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot.menus.admin_ui import get_admin_keyboard
from src.bot.menus.main import get_main_keyboard
from src.bot.state import get_or_create_state, is_user_admin
from src.database.members import member_manager
from src.database.models import model_manager
from src.database.settings import landing_page_manager
from src.database.usage import usage_manager

logger = logging.getLogger(__name__)


async def handle_start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    is_edit: bool = False,
) -> None:
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    state = await get_or_create_state(user_id, user.username, user.first_name, user.last_name)

    state.step = None
    state.model = None
    state.generate_audio = True
    state.use_image = False

    member_data = await member_manager.sync_member(user_id)
    is_trial_exhausted = (
        member_data
        and member_data.plan == "testing"
        and (member_data.testing_quota or 0) <= 0
    )
    is_expired = member_data and (member_data.is_expired or not member_data.active)

    if not member_data or is_trial_exhausted or is_expired:
        banner_url = landing_page_manager.get_setting("bannerImage")
        description = landing_page_manager.get_setting("bannerDescription")

        rows = [
            [
                InlineKeyboardButton("\U0001f331 Lite", callback_data="lite"),
                InlineKeyboardButton("\u2b50 Pro", callback_data="pro"),
                InlineKeyboardButton("\U0001f48e Ultra", callback_data="ultra"),
            ],
        ]
        if not member_data:
            rows.append([
                InlineKeyboardButton("\U0001f381 Free Trial", callback_data="free_trial"),
                InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="back_main"),
            ])
        else:
            rows.append([InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="back_main")])

        keyboard = InlineKeyboardMarkup(rows)

        if is_edit:
            try:
                await update.callback_query.message.delete()
            except Exception:
                pass

        if not banner_url:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=description,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        else:
            try:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=banner_url,
                    caption=description,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            except Exception:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=description,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
        return

    # User has active membership
    usage = await usage_manager.get_usage(user_id)
    active_processes = await member_manager.count_active_processes(user_id)
    max_process = member_manager.get_max_process(member_data.plan, user_id)
    daily_limit = member_manager.get_daily_limit(member_data.plan, user_id)

    plan_names = {
        "lite": "\U0001f331 AiGen Lite",
        "pro": "\u2b50 AiGen Pro",
        "ultra": "\U0001f48e AiGen Ultra",
    }
    plan_name = plan_names.get(member_data.plan, "\U0001f381 Free Trial")

    expire_string = "Expired"
    if member_data.expire_date:
        try:
            from datetime import datetime
            d = datetime.fromisoformat(member_data.expire_date.replace("Z", "+00:00"))
            expire_string = d.strftime("%d-%m-%Y")
        except Exception:
            pass

    message = (
        f"\U0001f464 *Id:* `{user_id}`\n"
        f"\U0001f4e6 *Paket:* {plan_name}\n"
        f"\U0001f5d3\ufe0f *Aktive:* (s/d {expire_string})\n"
        f"\U0001f916 *Status:* {active_processes}/{max_process} process\n"
        f"\U0001f4ca *Kuota:* {usage.video_today}/{daily_limit} daily"
    )

    keyboard = get_main_keyboard(model_manager.get_active_models())
    rows = list(keyboard.inline_keyboard)

    if member_data.plan == "testing":
        rows.append([InlineKeyboardButton("\U0001f48e Daftar Paket Lite / Pro / Ultra", callback_data="show_plans")])

    reply_markup = InlineKeyboardMarkup(rows)

    if is_edit:
        try:
            await update.callback_query.edit_message_text(
                text=message,
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )
            return
        except Exception:
            try:
                await update.callback_query.message.delete()
            except Exception:
                pass

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_start_command(update, context)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    state = await get_or_create_state(user_id, user.username, user.first_name, user.last_name)

    if is_user_admin(user_id, state):
        state.is_admin = True
        await update.message.reply_text(
            "\U0001f6e0 *Admin Panel*",
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard(),
        )
    else:
        await update.message.reply_text("\u274c Akses ditolak.")

