# AiGen Studio Bot - Python Edition

Bot Telegram yang menghubungkan Freepik AI API untuk generate video dan gambar AI. Versi Python dari AiGen Studio.

## Fitur

- **Multi-Model AI** - Kling V3, V2.6, V2.5, V2.1, O1, Veo 3.1, Nano Banana
- **API Key Rotation** - Otomatis rotasi dan retry antar API key
- **Proxy Support** - Rotasi proxy dengan health check otomatis
- **Subscription System** - Lite, Pro, Ultra, dan Free Trial
- **Admin Panel** - Manajemen key, proxy, model, member, landing page
- **Usage Tracking** - Tracking harian dan bulanan per user
- **Multi-shot** - Kling V3 multi-shot video generation
- **Broadcast** - Kirim pesan ke semua user / member / trial
- **Chat Personal** - Admin bisa chat langsung dengan user

## Setup

### 1. Clone Repository

```bash
git clone https://github.com/abdulrozzaqkla45-ux/AiGen-Bot-Python.git
cd AiGen-Bot-Python
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Environment

Copy `.env.example` ke `.env` dan isi:

```bash
cp .env.example .env
```

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
ADMIN_IDS=123456789,987654321
```

### 4. Jalankan Bot

```bash
python server.py
```

## Struktur Project

```
server.py                   # Entry point
src/
  core/
    constants.py            # Model config (30+ AI models)
    types.py                # Dataclass definitions
  database/
    client.py               # Supabase client
    apikeys.py              # API key management
    members.py              # Member/subscription management
    models.py               # Model status management
    proxies.py              # Proxy management
    settings.py             # Landing page settings
    usage.py                # Usage tracking
    users.py                # User registration
  services/
    freepik_api.py          # Freepik API submission
    jobs.py                 # Job finalization
    polling.py              # Job status polling
    request_engine.py       # Resilient HTTP with key/proxy rotation
    stats.py                # Activity logging
  bot/
    state.py                # User state management
    handlers/
      callbacks.py          # Inline button handlers
      commands.py           # /start, /admin, /reset
      messages.py           # Text & photo message handlers
    menus/
      admin_ui.py           # Admin panel keyboards
      main.py               # Main menu keyboards
      models_ui.py          # Model config keyboards
    panels/
      kling_v3_panel.py     # Kling V3/Omni/O1 advanced panel
```

## Database (Supabase)

Bot membutuhkan tabel berikut di Supabase:

- `api_keys` - key, active, cooldown_until
- `proxies` - proxy, active, cooldown_until
- `members` - user_id, plan, expired, testing_quota, active, current_process
- `users` - user_id, username, full_name, joined_at
- `usage` - user_id, video_today, last_reset, video_month, last_month_reset
- `jobs` - job_id, user_id, model_id, status, created_at
- `models_status` - id, active
- `settings` - id, data (JSON)

## Tech Stack

- Python 3.10+
- python-telegram-bot 21.5
- Supabase Python SDK
- httpx (async HTTP)
- python-dotenv
