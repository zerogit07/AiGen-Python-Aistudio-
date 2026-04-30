from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.core.types import UserState


def get_main_keyboard(active_models: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(active_models), 2):
        row_models = active_models[i : i + 2]
        row = [
            InlineKeyboardButton(
                f"      {m['name']}      ", callback_data=f"model:{m['id']}"
            )
            for m in row_models
        ]
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def get_resolution_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f4fa 720p", callback_data="resolution:720"),
            InlineKeyboardButton("\U0001f4fa 1080p", callback_data="resolution:1080"),
        ],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="back_main")],
    ])


def get_orientation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f3ac Video (Max 30s)", callback_data="orientation:video"),
            InlineKeyboardButton("\U0001f5bc Image (Max 10s)", callback_data="orientation:image"),
        ],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="back_main")],
    ])


def get_o1_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f504 Mode Interpolasi", callback_data="o1_mode:interpolation"),
            InlineKeyboardButton("\U0001f465 Mode Reference", callback_data="o1_mode:reference"),
        ],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="back_main")],
    ])


def get_audio_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f50a Audio On", callback_data="audio:on"),
            InlineKeyboardButton("\U0001f507 Audio Off", callback_data="audio:off"),
        ],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="back_main")],
    ])


def get_use_image_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f5bc Ya (Gunakan Gambar)", callback_data="use_image:yes"),
            InlineKeyboardButton("\U0001f4dd Tidak (Teks Saja)", callback_data="use_image:no"),
        ],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="back_main")],
    ])


def get_kling3_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\u274c Tanpa Multi-shot", callback_data="kling3_mode:single"),
            InlineKeyboardButton("\U0001f916 Multi-shot Auto", callback_data="kling3_mode:multi_intelligence"),
        ],
        [InlineKeyboardButton("\U0001f6e0 Multi-shot Custom", callback_data="kling3_mode:multi_customize")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="back_main")],
    ])


def get_veo_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f4dd T2V (Text to Video)", callback_data="veo_mode:t2v")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="back_main")],
    ])


def get_aspect_ratio_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f4fa 16:9 (Widescreen)", callback_data="ratio:widescreen_16_9"),
            InlineKeyboardButton("\U0001f4f1 9:16 (Portrait)", callback_data="ratio:portrait_9_16"),
        ],
        [InlineKeyboardButton("\u2b1b\ufe0f 1:1 (Square)", callback_data="ratio:square_1_1")],
        [InlineKeyboardButton("\u2b05\ufe0f Kembali", callback_data="back_main")],
    ])
