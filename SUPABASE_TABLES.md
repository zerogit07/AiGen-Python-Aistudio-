# 📊 Struktur Tabel Supabase — AiGen Bot

## 1. `api_keys` — Daftar API Key Freepik

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

---

## 2. `members` — Data Member/Langganan

| Kolom | Tipe | Keterangan |
|---|---|---|
| `user_id` | bigint (PK) | Telegram user ID |
| `plan` | text | Paket: `lite`, `pro`, `ultra`, `testing` |
| `expired` | date | Tanggal expired langganan (contoh: `2026-05-25`) |
| `active` | boolean | `true` = member aktif |
| `testing_quota` | int | Sisa kuota trial (0 = habis) |
| `current_process` | int | Jumlah proses yang sedang berjalan |

---

## 3. `users` — Data User Telegram

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | bigint (PK) | Telegram user ID |
| `username` | text | Username Telegram (tanpa @) |
| `first_name` | text | Nama depan |
| `last_name` | text | Nama belakang |
| `joined_at` | timestamp | Tanggal pertama kali pakai bot |

---

## 4. `models_status` — Status Model AI (Aktif/Nonaktif)

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

---

## 5. `usage` — Penggunaan Harian & Bulanan

| Kolom | Tipe | Keterangan |
|---|---|---|
| `user_id` | bigint (PK) | Telegram user ID |
| `video_today` | int | Jumlah video hari ini |
| `last_reset` | date | Tanggal terakhir reset harian |
| `video_month` | int | Jumlah video bulan ini |
| `last_month_reset` | text | Bulan terakhir reset (contoh: `2026-04`) |

---

## 6. `proxies` — Daftar Proxy Server

| Kolom | Tipe | Keterangan |
|---|---|---|
| `proxy` | text (PK) | URL proxy (contoh: `http://user:pass@proxy.com:8080`) |
| `active` | boolean | `true` = aktif, `false` = mati/cooldown |
| `cooldown_until` | bigint | Timestamp cooldown (0 = tidak cooldown) |
| `added_at` | timestamp | Tanggal proxy ditambahkan |

---

## 7. `settings` — Pengaturan Bot (format JSON)

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

---

## Relasi Antar Tabel

```
users.id ←→ members.user_id ←→ usage.user_id
    │
    └── Satu user bisa punya 1 membership + 1 usage record
    
api_keys → dipakai oleh request_engine untuk semua model
proxies  → dipakai oleh request_engine sebagai tunnel
models_status → kontrol model mana yang aktif/nonaktif
settings → konfigurasi bot (landing page, maintenance, dll)
```
