# AiGen Studio Bot - Python Edition

Bot Telegram yang menghubungkan Freepik AI API untuk generate video dan gambar AI. Versi Python dari AiGen Studio.

## Fitur

- **Multi-Model AI** - Kling V3, V2.6, V2.5, V2.1, O1, Veo 3.1, Nano Banana
- **API Key Rotation** - Otomatis rotasi dan retry antar API key
- **Proxy Support** - Rotasi proxy dengan health check otomatis
- **Subscription System** - Lite, Pro, Ultra, dan Free Trial
- **Admin Panel** - Manajemen key (dengan fitur cek keys tersinkron), proxy, model, member, landing page
- **Queue System** - Background processing stabil menggunakan Redis & ARQ untuk task berat dan API checking
- **Usage Tracking** - Tracking harian dan bulanan per user
- **Multi-shot** - Kling V3 multi-shot video generation
- **Broadcast** - Kirim pesan ke semua user / member / trial
- **Chat Personal** - Admin bisa chat langsung dengan user

## Setup

### 1. Clone Repository

```bash
git clone https://github.com/zerogit07/AiGen-Python-Aistudio-.git
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
REDIS_URL=redis://localhost:6379
```

### 4. Setup Redis (Wajib)

Pastikan Redis server sudah berjalan di lokal atau remote (sesuai `REDIS_URL`).

### 5. Jalankan Bot dan Worker

Aplikasi ini menggunakan sistem worker untuk proses yang berat. Jalankan kedua service berikut di terminal yang berbeda:

**Terminal 1 (Jalankan Bot Telegram):**
```bash
python server.py
```

**Terminal 2 (Jalankan ARQ Worker):**
```bash
arq worker.WorkerSettings
```

## Struktur Project

```
server.py                   # Entry point (Telegram Bot)
worker.py                   # ARQ Worker (Background Tasks processing)
src/
  core/
    constants.py            # Model config (30+ AI models)
    types.py                # Dataclass definitions
    queue.py                # ARQ Redis Queue interface
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

Bot membutuhkan tabel-tabel berikut di Supabase sebagai *Single Source of Truth*:

### 1. `api_keys` — Daftar API Key Freepik

| Kolom | Tipe | Keterangan |
|---|---|---|
| `key` | text (PK) | API key Freepik (contoh: `FPSX3332bc...`) |
| `active` | boolean | `true` = aktif, `false` = nonaktif/dead |
| `cooldown_until` | bigint | Timestamp cooldown (0 = tidak cooldown) |
| `added_at` | timestamp | Tanggal key ditambahkan |
| `dead_reason` | text | Alasan key mati (null = belum mati) |
| `last_error_code` | int | Kode error terakhir (401, 500, dll) |
| `last_error_at` | timestamp | Waktu error terakhir |
| `needs_topup` | boolean | `true` = kuota habis, perlu topup |

### 2. `members` — Data Member/Langganan

| Kolom | Tipe | Keterangan |
|---|---|---|
| `user_id` | bigint (PK) | Telegram user ID |
| `plan` | text | Paket: `lite`, `pro`, `ultra`, `testing` |
| `expired` | date | Tanggal expired langganan (contoh: `2026-05-25`) |
| `active` | boolean | `true` = member aktif |
| `testing_quota` | int | Sisa kuota trial (0 = habis) |
| `current_process` | int | Jumlah proses yang sedang berjalan |

### 3. `users` — Data User Telegram

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | bigint (PK) | Telegram user ID |
| `username` | text | Username Telegram (tanpa @) |
| `first_name` | text | Nama depan |
| `last_name` | text | Nama belakang |
| `joined_at` | timestamp | Tanggal pertama kali pakai bot |

### 4. `models_status` — Status Model AI (Aktif/Nonaktif)

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | text (PK) | ID model (contoh: `kling_v3_pro`, `veo_3_1`) |
| `active` | boolean | `true` = model aktif, `false` = dimatikan admin |

**Daftar model:**
```
kling_v3_pro, kling_v3_std, kling_v3_motion_pro, kling_v3_motion_std,
kling_v3_omni_pro, kling_v3_omni_std, kling_2_6_pro, kling_2_6_motion_pro,
kling_2_6_motion_std, kling_2_5_turbo, kling_2_1_pro, kling_2_1_std,
kling_o1_pro, kling_o1_std, veo_3_1, veo_3_1_fast,
nano_banana_pro, nano_banana_flash, ... (30 total)
```

### 5. `usage` — Penggunaan Harian & Bulanan

| Kolom | Tipe | Keterangan |
|---|---|---|
| `user_id` | bigint (PK) | Telegram user ID |
| `video_today` | int | Jumlah video hari ini |
| `last_reset` | date | Tanggal terakhir reset harian |
| `video_month` | int | Jumlah video bulan ini |
| `last_month_reset` | text | Bulan terakhir reset (contoh: `2026-04`) |

### 6. `proxies` — Daftar Proxy Server

| Kolom | Tipe | Keterangan |
|---|---|---|
| `proxy` | text (PK) | URL proxy (contoh: `http://user:pass@proxy.com:8080`) |
| `active` | boolean | `true` = aktif, `false` = mati/cooldown |
| `cooldown_until` | bigint | Timestamp cooldown (0 = tidak cooldown) |
| `added_at` | timestamp | Tanggal proxy ditambahkan |

### 7. `settings` — Pengaturan Bot (format JSON)

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | text (PK) | ID setting: `landing`, `maintenance`, `custom_limits` |
| `data` | jsonb | Data setting dalam format JSON |

**Row `landing`** — Pengaturan halaman utama bot:
```json
{
  "bannerImage": "https://...",
  "bannerDescription": "✨WELCOME TO AIGEN BOT...",
  "paymentImage": "https://...",
  "paymentDescriptionLite": "AIGEN LITE ...",
  "paymentDescriptionPro": "AIGEN PRO ...",
  "paymentDescriptionUltra": "AIGEN ULTRA ...",
  "limitLite": "30",
  "limitPro": "60",
  "limitUltra": "100",
  "priceLite": "99000",
  "pricePro": "199000",
  "priceUltra": "299000"
}
```

**Row `maintenance`** (opsional) — Mode maintenance:
```json
{
  "active": true/false
}
```

**Row `custom_limits`** (opsional) — Limit custom per user:
```json
{
  "user_id": {"daily": 50, "max": 5}
}
```

### Relasi Antar Tabel

```
users.id ←→ members.user_id ←→ usage.user_id
    │
    └── Satu user bisa punya 1 membership + 1 usage record
    
api_keys → dipakai oleh request_engine untuk semua model
proxies  → dipakai oleh request_engine sebagai tunnel
models_status → kontrol model mana yang aktif/nonaktif
settings → konfigurasi bot (landing page, maintenance, dll)
```

## Arsitektur Bot

AiGen Studio Bot dirancang dengan arsitektur terdistribusi (UI Terpisah dari Pemrosesan Berat) menggunakan kombinasi Polling Bot dan Background Worker untuk stabilitas.

### 1. Telegram Bot Client (`server.py`)
- Bertugas murni sebagai antarmuka Telegram (menangani pesan, _inline buttons_, navigasi panel).
- Melakukan validasi input pengguna dan mengecek batasan limit paket langganan.
- Tidak melakukan panggilan API Generate yang berat secara langsung. Sebaliknya, bot akan membungkus parameter request dan mengirimkannya ( _enqueue_ ) ke antrian **Redis**.

### 2. Job Queue (Redis & ARQ)
- Menyimpan antrian tugas-tugas ( _jobs_ ) yang diberikan oleh Bot.
- `src/core/queue.py` berfungsi sebagai jembatan agar Telegram client dapat melempar tugas ( _Generate video/image_, _Cek API Key_) ke Worker dengan aman.

### 3. Background Worker (`worker.py`)
- Proses terpisah (`arq worker.WorkerSettings`) yang mengambil pekerjaan dari antrian Redis.
- Menangani semua eksekusi koneksi ke API pihak ketiga (Freepik) dan tidak akan membuat Telegram Bot ikut hang / melambat ( _blocking_ ).

### 4. Smart Triple Pool (`src/core/triple_pool.py`)
Komponen keamanan tingkat tinggi untuk menghindari _Rate Limit_ (429) dan _IP Ban_ (403/401):
- Secara dinamis mengikat dan merotasi **1 API Key** + **1 Proxy** + **1 Browser Fingerprint** ke dalam sebuah **TripleSet**.
- Mengunci sebuah TripleSet agar tidak ditabrak oleh tugas paralel lain di Worker.
- Menerapkan _cooldown_ dan status _Burned_ otomatis jika sebuah koneksi Proxy atau Key dicurigai tertangkap radar blokir oleh target server.

### 5. Resilient Request Engine (`src/services/request_engine.py`)
- Klien HTTP cerdas yang memfasilitasi rotasi dan _auto-retry_ di pertengahan jalan.
- Jika sebuah request gagal di tengah proses karena limit, engine akan mencari proxy/key baru dari _Triple Pool_ dan mengulang kembali sisa request.
- Menyinkronisasi otomatis status mati (401) dan limit (429) API ke database agar tidak digunakan oleh proses lain selama masa _cooldown_.

### 6. Centralized Storage (Supabase)
Database PostgreSQL (via Supabase) menjadi komponen _Single Source of Truth_ yang mencatat:
- Status langganan _Members_ & Kuota _Usage_ per user secara realtime.
- Konfigurasi rotasi API Key & Proxy agar tersinkron di banyak _instance_ Worker atau Bot secara paralel.
- Konfigurasi menu UI Admin (Teks Landing Page, Limit, Harga) bersifat dinamis sepenuhnya.

## Tech Stack

- Python 3.10+
- python-telegram-bot 21.5
- Supabase Python SDK
- httpx (async HTTP)
- Redis & ARQ (Background Job Queue)
- python-dotenv
