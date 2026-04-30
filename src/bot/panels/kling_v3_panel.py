from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot.state import get_or_create_state
from src.services.jobs import finalize_job

logger = logging.getLogger(__name__)


@dataclass
class KlingV3State:
    model_type: str = "kling_v3"  # "kling_v3" | "kling_v3_omni" | "kling_o1"
    first_frame_url: Optional[str] = None
    end_frame_url: Optional[str] = None
    video_ref_url: Optional[str] = None
    element_urls: list[str] = field(default_factory=list)
    multi_shot_on: bool = False
    prompt: str = ""
    shots: list[dict] = field(default_factory=list)  # [{prompt, duration}]
    resolution: str = "720p"
    duration: str = "15s"
    ratio: str = "16:9"
    audio: bool = False
    awaiting_input: Optional[str] = None
    panel_view: str = "main"
    panel_message_id: Optional[int] = None


kv3_state: dict[int, KlingV3State] = {}


def get_kv3_state(user_id: int, force_model: str | None = None) -> KlingV3State:
    if user_id not in kv3_state or (force_model and kv3_state[user_id].model_type != force_model):
        existing = kv3_state.get(user_id)
        kv3_state[user_id] = KlingV3State(
            model_type=force_model or (existing.model_type if existing else "kling_v3"),
            multi_shot_on=existing.multi_shot_on if existing else False,
            prompt=existing.prompt if existing else "",
            shots=existing.shots if existing else [],
            resolution=existing.resolution if existing else "720p",
            duration=existing.duration if existing else ("5s" if force_model == "kling_o1" else "15s"),
            ratio=existing.ratio if existing else "16:9",
            audio=existing.audio if existing else False,
            first_frame_url=existing.first_frame_url if existing else None,
            end_frame_url=existing.end_frame_url if existing else None,
            video_ref_url=existing.video_ref_url if existing else None,
            element_urls=existing.element_urls if existing else [],
            panel_view="main",
        )
    return kv3_state[user_id]


async def render_kling_v3_panel(
    bot,
    chat_id: int,
    user_id: int,
    is_edit: bool = True,
    force_model: str | None = None,
) -> None:
    state = get_kv3_state(user_id, force_model)
    is_omni = state.model_type in ("kling_v3_omni", "kling_o1")
    is_kling_o1 = state.model_type == "kling_o1"

    if is_kling_o1:
        state.multi_shot_on = False

    # Panel title
    if is_kling_o1:
        title = "🎬 KLING O1 GENERATOR"
    elif state.model_type == "kling_v3_omni":
        title = "🎬 KLING V3 OMNI GENERATOR"
    else:
        title = "🎬 KLING V3 GENERATOR"

    current_dur_num = int(state.duration.replace("s", "")) if state.duration else 5
    total_shot_dur = sum(s.get("duration", 0) for s in state.shots)

    # Duration picker sub-panel
    if state.panel_view == "choose_main_duration":
        text = f"*{title}*\n{'─' * 20}\n\n*PILIH DURASI UTAMA*\n"
        if not is_kling_o1 and state.multi_shot_on:
            text += f"Total durasi shot Anda saat ini: {total_shot_dur}s.\n"
            text += "*(Anda tidak bisa mengubah ke angka yang lebih kecil dari total durasi shot)*\n\n"
        else:
            text += "Silakan pilih total durasi video Anda:\n\n"

        buttons: list[list[InlineKeyboardButton]] = []
        if is_kling_o1:
            buttons.append([
                InlineKeyboardButton("5 Detik", callback_data="kv3_set_main_dur_5"),
                InlineKeyboardButton("10 Detik", callback_data="kv3_set_main_dur_10"),
            ])
        else:
            row: list[InlineKeyboardButton] = []
            for i in range(1, 16):
                row.append(InlineKeyboardButton(f"{i}s", callback_data=f"kv3_set_main_dur_{i}"))
                if len(row) == 5:
                    buttons.append(row)
                    row = []
            if row:
                buttons.append(row)
        buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="kv3_close_subpanel")])

        keyboard = InlineKeyboardMarkup(buttons)
        try:
            if is_edit and state.panel_message_id:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=state.panel_message_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            else:
                sent = await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
                state.panel_message_id = sent.message_id
        except Exception:
            pass
        return

    # Resolution picker
    if state.panel_view == "choose_resolution":
        text = f"*{title}*\n{'─' * 20}\n\n*PILIH RESOLUSI*\n"
        buttons = [
            [
                InlineKeyboardButton("720p", callback_data="kv3_set_res_720p"),
                InlineKeyboardButton("1080p", callback_data="kv3_set_res_1080p"),
            ],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="kv3_close_subpanel")],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        try:
            if is_edit and state.panel_message_id:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=state.panel_message_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            else:
                sent = await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
                state.panel_message_id = sent.message_id
        except Exception:
            pass
        return

    # Ratio picker
    if state.panel_view == "choose_ratio":
        text = f"*{title}*\n{'─' * 20}\n\n*PILIH ASPECT RATIO*\n"
        buttons = [
            [
                InlineKeyboardButton("16:9", callback_data="kv3_set_ratio_16:9"),
                InlineKeyboardButton("9:16", callback_data="kv3_set_ratio_9:16"),
                InlineKeyboardButton("1:1", callback_data="kv3_set_ratio_1:1"),
            ],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="kv3_close_subpanel")],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        try:
            if is_edit and state.panel_message_id:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=state.panel_message_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            else:
                sent = await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
                state.panel_message_id = sent.message_id
        except Exception:
            pass
        return

    # Main panel
    prompt_preview = state.prompt[:50] + "..." if len(state.prompt) > 50 else (state.prompt or "(kosong)")

    text = f"*{title}*\n{'─' * 20}\n\n"
    text += f"📝 Prompt: `{prompt_preview}`\n"
    text += f"📺 Resolusi: *{state.resolution}*\n"
    text += f"⏱ Durasi: *{state.duration}*\n"
    text += f"📐 Ratio: *{state.ratio}*\n"
    text += f"🔊 Audio: *{'On' if state.audio else 'Off'}*\n"

    if state.first_frame_url:
        text += "🖼 First Frame: Uploaded\n"
    if state.end_frame_url:
        text += "🖼 End Frame: Uploaded\n"
    if state.element_urls:
        text += f"🖼 Element: {len(state.element_urls)} gambar\n"

    if state.multi_shot_on and state.shots:
        text += f"\n*Multi-shot:* {len(state.shots)} shot(s)\n"
        for i, s in enumerate(state.shots):
            sp = s.get("prompt", "")[:30]
            text += f"  Shot {i + 1}: {s.get('duration', 5)}s - {sp or '(kosong)'}\n"

    text += f"\n{'─' * 20}\n"
    text += "🎯 Pilih opsi di bawah untuk mengatur parameter:"

    buttons: list[list[InlineKeyboardButton]] = []

    # Prompt button
    buttons.append([InlineKeyboardButton("📝 Edit Prompt", callback_data="kv3_edit_prompt")])

    # Media buttons
    media_row: list[InlineKeyboardButton] = []
    media_row.append(InlineKeyboardButton(
        "🖼 First Frame" if not state.first_frame_url else "🖼 First Frame ✅",
        callback_data="kv3_upload_first_frame",
    ))
    if not is_kling_o1:
        media_row.append(InlineKeyboardButton(
            "🖼 End Frame" if not state.end_frame_url else "🖼 End Frame ✅",
            callback_data="kv3_upload_end_frame",
        ))
    buttons.append(media_row)

    if not is_kling_o1:
        buttons.append([InlineKeyboardButton(
            f"Element ({len(state.element_urls)}/3)" if state.element_urls else "Element (0/3)",
            callback_data="kv3_upload_element",
        )])

    # Settings
    buttons.append([
        InlineKeyboardButton(f"Durasi: {state.duration}", callback_data="kv3_change_duration"),
        InlineKeyboardButton(f"Resolusi: {state.resolution}", callback_data="kv3_change_resolution"),
    ])
    buttons.append([
        InlineKeyboardButton(f"Ratio: {state.ratio}", callback_data="kv3_change_ratio"),
        InlineKeyboardButton(f"Audio: {'On' if state.audio else 'Off'}", callback_data="kv3_toggle_audio"),
    ])

    # Multi-shot (not for O1)
    if not is_kling_o1:
        if state.multi_shot_on:
            buttons.append([
                InlineKeyboardButton("Multi-shot OFF", callback_data="kv3_multishot_off"),
                InlineKeyboardButton("+ Tambah Shot", callback_data="kv3_add_shot"),
            ])
        else:
            buttons.append([InlineKeyboardButton("Multi-shot ON", callback_data="kv3_multishot_on")])

    # Generate & back
    buttons.append([InlineKeyboardButton("GENERATE", callback_data="kv3_generate")])
    buttons.append([InlineKeyboardButton("Kembali ke Menu Utama", callback_data="back_main")])

    keyboard = InlineKeyboardMarkup(buttons)

    try:
        if is_edit and state.panel_message_id:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=state.panel_message_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        else:
            sent = await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
            state.panel_message_id = sent.message_id
    except Exception:
        pass


def setup_kling_v3_actions() -> dict[str, str]:
    """Returns a mapping of callback patterns for the panel."""
    return {
        "kv3_": "kling_v3_panel",
        "ko1_": "kling_o1_panel",
    }
