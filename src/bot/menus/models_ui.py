from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.core.types import UserState


def _sel(label: str, active: bool) -> str:
    return f"[ {label} ]" if active else label


def get_nano_banana_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    model = state.model or "nano_banana_flash"
    model_label = "Nano Banana Pro" if model == "nano_banana_pro" else "Nano Banana 2"
    res = state.resolution or "1k"
    ratio = state.aspect_ratio or "portrait_9_16"
    ratio_label = "16:9" if ratio == "widescreen_16_9" else "9:16"

    message = (
        f"🍌 *KONFIGURASI NANO BANANA*\n\n"
        f"Model    : *{model_label}*\n"
        f"Resolusi : *{res.upper()}*\n"
        f"Ratio    : *{ratio_label}*\n\n"
        f"*Silakan atur parameter di bawah. Jika sudah sesuai, klik \"LANJUTKAN\".*"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(_sel("Nano Pro", model == "nano_banana_pro"), callback_data="nano_mod:pro"),
            InlineKeyboardButton(_sel("Nano 2", model == "nano_banana_flash"), callback_data="nano_mod:nano2"),
        ],
        [
            InlineKeyboardButton(_sel("1K", res == "1k"), callback_data="nano_res:1k"),
            InlineKeyboardButton(_sel("2K", res == "2k"), callback_data="nano_res:2k"),
            InlineKeyboardButton(_sel("4K", res == "4k"), callback_data="nano_res:4k"),
        ],
        [
            InlineKeyboardButton(_sel("16:9", ratio == "widescreen_16_9"), callback_data="nano_rat:widescreen_16_9"),
            InlineKeyboardButton(_sel("9:16", ratio == "portrait_9_16"), callback_data="nano_rat:portrait_9_16"),
        ],
        [InlineKeyboardButton("▶️ LANJUTKAN", callback_data="nano_continue")],
        [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_main")],
    ])
    return message, keyboard


def get_veo31_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    model = state.model or "veo_3_1_fast"
    model_label = "Fast" if "fast" in model else "Standard"
    res = state.resolution or "720"
    ratio = state.aspect_ratio or "portrait_9_16"
    ratio_label = "16:9" if ratio == "widescreen_16_9" else "9:16"
    dur = state.duration or "8"
    audio = "On" if state.generate_audio else "Off"

    message = (
        f"🎬 *KONFIGURASI VEO 3.1*\n\n"
        f"Model    : *{model_label}*\n"
        f"Resolusi : *{'4K' if res == '4k' else res + 'p'}*\n"
        f"Ratio    : *{ratio_label}*\n"
        f"Durasi   : *{dur}s*\n"
        f"Audio    : *{audio}*\n\n"
        f"*Silakan atur parameter di bawah. Jika sudah sesuai, klik \"LANJUTKAN\".*"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(_sel("Standard", "standard" in model), callback_data="veo31_mod:standard"),
            InlineKeyboardButton(_sel("Fast", "fast" in model), callback_data="veo31_mod:fast"),
        ],
        [
            InlineKeyboardButton(_sel("720p", res == "720"), callback_data="veo31_res:720"),
            InlineKeyboardButton(_sel("1080p", res == "1080"), callback_data="veo31_res:1080"),
            InlineKeyboardButton(_sel("4K", res == "4k"), callback_data="veo31_res:4k"),
        ],
        [
            InlineKeyboardButton(_sel("16:9", ratio == "widescreen_16_9"), callback_data="veo31_rat:widescreen_16_9"),
            InlineKeyboardButton(_sel("9:16", ratio == "portrait_9_16"), callback_data="veo31_rat:portrait_9_16"),
        ],
        [
            InlineKeyboardButton(_sel("4s", dur == "4"), callback_data="veo31_dur:4"),
            InlineKeyboardButton(_sel("6s", dur == "6"), callback_data="veo31_dur:6"),
            InlineKeyboardButton(_sel("8s", dur == "8"), callback_data="veo31_dur:8"),
        ],
        [
            InlineKeyboardButton(_sel("Audio On", state.generate_audio), callback_data="veo31_aud:on"),
            InlineKeyboardButton(_sel("Audio Off", not state.generate_audio), callback_data="veo31_aud:off"),
        ],
        [InlineKeyboardButton("▶️ LANJUTKAN", callback_data="veo31_continue")],
        [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_main")],
    ])
    return message, keyboard


def get_kling26_motion_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    orientation = state.orientation or "video"
    res = state.resolution or "720"

    message = (
        f"🎬 *KONFIGURASI KLING 2.6 MOTION*\n\n"
        f"Orientasi : *{'Video' if orientation == 'video' else 'Image'}*\n"
        f"Resolusi : *{res}p*\n\n"
        f"*Pilih parameter di bawah. Jika sudah sesuai, klik \"LANJUTKAN\".*"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(_sel("Video", orientation == "video"), callback_data="k26m_ori:video"),
            InlineKeyboardButton(_sel("Image", orientation == "image"), callback_data="k26m_ori:image"),
        ],
        [
            InlineKeyboardButton(_sel("720p", res == "720"), callback_data="k26m_res:720"),
            InlineKeyboardButton(_sel("1080p", res == "1080"), callback_data="k26m_res:1080"),
        ],
        [InlineKeyboardButton("▶️ LANJUTKAN", callback_data="k26m_continue")],
        [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_main")],
    ])
    return message, keyboard


def get_kling21_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    res = state.resolution or "720"
    dur = state.duration or "5"
    ratio = state.aspect_ratio or "portrait_9_16"
    ratio_label = "16:9" if ratio == "widescreen_16_9" else "9:16" if ratio == "portrait_9_16" else "1:1"

    message = (
        f"🎬 *KONFIGURASI KLING 2.1*\n\n"
        f"Resolusi : *{res}p*\n"
        f"Durasi   : *{dur}s*\n"
        f"Ratio    : *{ratio_label}*\n\n"
        f"*Pilih parameter di bawah. Jika sudah sesuai, klik \"LANJUTKAN\".*"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(_sel("720p", res == "720"), callback_data="k21_res:720"),
            InlineKeyboardButton(_sel("1080p", res == "1080"), callback_data="k21_res:1080"),
        ],
        [
            InlineKeyboardButton(_sel("5s", dur == "5"), callback_data="k21_dur:5"),
            InlineKeyboardButton(_sel("10s", dur == "10"), callback_data="k21_dur:10"),
        ],
        [
            InlineKeyboardButton(_sel("16:9", ratio == "widescreen_16_9"), callback_data="k21_rat:widescreen_16_9"),
            InlineKeyboardButton(_sel("9:16", ratio == "portrait_9_16"), callback_data="k21_rat:portrait_9_16"),
            InlineKeyboardButton(_sel("1:1", ratio == "square_1_1"), callback_data="k21_rat:square_1_1"),
        ],
        [InlineKeyboardButton("▶️ LANJUTKAN", callback_data="k21_continue")],
        [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_main")],
    ])
    return message, keyboard


def get_kling26_pro_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    res = state.resolution or "1080"
    dur = state.duration or "5"

    message = (
        f"🎬 *KONFIGURASI KLING 2.6 PRO*\n\n"
        f"Resolusi : *{res}p*\n"
        f"Durasi   : *{dur}s*\n\n"
        f"*Pilih parameter di bawah. Jika sudah sesuai, klik \"LANJUTKAN\".*"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(_sel("720p", res == "720"), callback_data="k26p_res:720"),
            InlineKeyboardButton(_sel("1080p", res == "1080"), callback_data="k26p_res:1080"),
        ],
        [
            InlineKeyboardButton(_sel("5s", dur == "5"), callback_data="k26p_dur:5"),
            InlineKeyboardButton(_sel("10s", dur == "10"), callback_data="k26p_dur:10"),
        ],
        [InlineKeyboardButton("▶️ LANJUTKAN", callback_data="k26p_continue")],
        [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_main")],
    ])
    return message, keyboard


def get_kling25_turbo_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    res = state.resolution or "1080"
    dur = state.duration or "5"

    message = (
        f"🎬 *KONFIGURASI KLING 2.5 TURBO*\n\n"
        f"Resolusi : *{res}p*\n"
        f"Durasi   : *{dur}s*\n\n"
        f"*Pilih parameter di bawah. Jika sudah sesuai, klik \"LANJUTKAN\".*"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(_sel("720p", res == "720"), callback_data="k25t_res:720"),
            InlineKeyboardButton(_sel("1080p", res == "1080"), callback_data="k25t_res:1080"),
        ],
        [
            InlineKeyboardButton(_sel("5s", dur == "5"), callback_data="k25t_dur:5"),
            InlineKeyboardButton(_sel("10s", dur == "10"), callback_data="k25t_dur:10"),
        ],
        [InlineKeyboardButton("▶️ LANJUTKAN", callback_data="k25t_continue")],
        [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_main")],
    ])
    return message, keyboard


def get_kling_v3_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    res = state.resolution or "720"
    dur = state.duration or "5"

    message = (
        f"🎬 *KONFIGURASI KLING V3*\n\n"
        f"Resolusi : *{res}p*\n"
        f"Durasi   : *{dur}s*\n\n"
        f"*Pilih parameter di bawah.*"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(_sel("720p", res == "720"), callback_data="kv3_res:720"),
            InlineKeyboardButton(_sel("1080p", res == "1080"), callback_data="kv3_res:1080"),
        ],
        [InlineKeyboardButton("▶️ LANJUTKAN", callback_data="kv3_continue")],
        [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_main")],
    ])
    return message, keyboard


def get_kling_o1_config_keyboard(state: UserState) -> tuple[str, InlineKeyboardMarkup]:
    res = state.resolution or "720"

    message = (
        f"🎬 *KONFIGURASI KLING O1*\n\n"
        f"Resolusi : *{res}p*\n\n"
        f"*Pilih parameter di bawah.*"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(_sel("720p", res == "720"), callback_data="ko1_res:720"),
            InlineKeyboardButton(_sel("1080p", res == "1080"), callback_data="ko1_res:1080"),
        ],
        [InlineKeyboardButton("▶️ LANJUTKAN", callback_data="ko1_continue")],
        [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_main")],
    ])
    return message, keyboard
