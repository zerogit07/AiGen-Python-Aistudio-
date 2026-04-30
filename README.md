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
- Melakukan validasi awal: kelayakan akun (pakah free trial, lite, pro, ultra), serta batasan antrean harian dan serentak (*concurrency*).
- Menyimpan State sementara (Gambar Referensi, Parameter Multi-shot) ke state internal per user.
- **Tidak mengeksekusi HTTP request Freepik**. Sebaliknya, hanya membungkus _intent_ user ke sebuah struktur job, lalu melempar ke Redis (via `ARQ`).

### 2. Job Queue & Scatter-Gather (Redis + ARQ)
- Jembatan komunikasi asinkron antara Bot dan barisan Worker.
- **Generate API**: Job masuk, Worker mengambil job satu-persatu secara teratur, memproses rendering dengan HTTP polling berdurasi lama, tanpa menghalangi (blocking) interface bot.
- **Check API Key (Scatter-Gather Strategy)**: Apabila admin memencet tombol "Cek Semua Key", bot akan membuat N job terpisah ke queue (satu per key) dan MENGHUBUNGKAN semuanya dengan `batch_id`. Worker mengeksekusi pengecekan per-key lalu menggunakan kunci atomic Redis (seperti `INCR` pada `HLEN`) untuk mencegah "race condition". Saat semua selesai (atau di-_fallback_ oleh job timeout selama 10 menit), Redis menyatukan seluruh laporan dalam 1 pesan ke Admin.

### 3. Background Worker Process (`worker.py`)
- Pemproses _background_ terpisah (`arq worker.WorkerSettings`) yang mengeksekusi pekerjaan berat sekuensial atau delay tinggi.
- Mengatur konkurensi aman (**Limit 5 Job Paralel**) per instance agar eksekusi proxy tidak seperti serangan *DDoS* dari satu node. Jeda acak antar tugas `random.uniform(1, 5)` membuat laju eksekusi tetap humanis dan aman bagi target server.

### 4. Smart Triple Pool & Wajib Proxy (`src/core/triple_pool.py`)
- Komponen anti-blokir _Zero-Trust_ yang mengamankan proxy ban/rate limits. 
- **Mode Wajib Proxy**: Mulai versi terbaru, sistem tidak akan berjalan (*crash-fail-safe*) jika tidak ada minimal 1 proxy tersetting aktif di menu admin. Proxy adalah identitas sakral.
- Secara cerdas membentuk kumpulan sesi independen (disebut `TripleSet`) yang berisi:
  **1 API Key Teruji** + **1 Proxy Spesifik** + **1 Browser Fingerprint/User Agent Unik**.
- **Lock & Burn System**: Sebuah `TripleSet` dipinjam oleh satu job Worker dan dikunci (locked). Jika Worker menemukan koneksi mati, blokir IP, atau Rate Limit, worker memanggil flag `mark_burned(triple_set)`, memicu Triple Pool membuang proxy itu/memberikan jeda cooldown otomatis agar key tak digunakan berulang kali sampai hancur kredibilitasnya. Tiap Worker Job dipastikan memakai TripleSet yang saling berbeda (selama stoknya di pool memenuhi).

### 5. Resilient Request Engine (`src/services/request_engine.py`)
- Klien HTTP cerdas yang mampu melakukan operasi "Terbang Di Tengah Badai". 
- Melakukan *Auto-Retry* mandiri dengan mencari `TripleSet` pengganti baru jika TripleSet lama gagal tanpa sepengetahuan logic atas (selagi batas coba proxy dalam logic belum mencapai maksimal).
- Jika ada key yang tewas terkena *Error 401*, engine ini yang mengirim *Query* ke Supabase Database langsung untuk men-drop key itu jadi flag `Dead`. 

### 6. Centralized Storage & Quota Logic (Supabase)
Sistem ini tak sekadar menabung data; dia memproteksi aturan bisnis utama:
- **Rule of Memberships**: Quota diperiksa `video_today < Plan Limit`. (ex. 10 jika Lite). Validasi dilakukan di Bot, increment Usage dieksekusi sebelum job dikirim, agar spammers tak melebihi kuota saat jeda request ke Worker. 
- **Rule of Restraints**: Quota _trial_ otomatis berkurang permanen. Sistem menyimpan *Timestamp Reset Bulanan / Harian* dan dieksekusi secara pasif setiap ada user request di hari/bulan baru. 
- **Shared States**: Supabase juga berfungsi merapikan config model (`models_status`) secara global agar jika di admin bot diset Non-aktif, seluruh bot klien seketika mencegah render ke parameter list tersebut.

### 7. Multi-shot Scene Logic (Kling V3)
Bot ini memiliki menu merangkai 10 Video (Scene) dari model Kling V3 yang kompleks:
- Bot telegram merangkai input User -> array parameter prompt & durasi menjadi State User `state._shots`.
- Worker akan mengeksekusi scene berurutan. Setelah scene-1 dirender oleh API (dengan memakan 1 sesi delay rendering lama), Worker menggunakan hasil render image-nya untuk dikombinasikan dengan scene-2. 
- Logika sekuensial (Sequential) dijamin konsisten dan apabila terjadi error di scene ke-7, User tidak kehilangan 6 video scene awal.


## Tech Stack

- Python 3.10+
- python-telegram-bot 21.5
- Supabase Python SDK
- httpx (async HTTP)
- Redis & ARQ (Background Job Queue)
- python-dotenv
