# WebGIS Penyakit Menular Semarang

Aplikasi WebGIS untuk mengeksplorasi sebaran kasus DBD, leptospirosis, dan TB baru di Kota Semarang serta melihat aksesibilitas fasilitas kesehatan. Aplikasi menyediakan peta interaktif, ringkasan dan tren kasus, pelaporan warga, serta alur administrasi untuk memverifikasi laporan dan memperbarui data.

## Fitur

- Peta choropleth kasus dan kepadatan kasus menurut wilayah.
- Popup informasi wilayah dan grafik tren kasus bulanan.
- Layer lokasi rumah sakit dan zona jarak akses: kurang dari 1 km, 1–3 km, 3–5 km, dan lebih dari 5 km.
- Data peta dan grafik untuk DBD, leptospirosis, dan TB baru, termasuk data tahunan 2019–2026.
- Formulir laporan warga serta halaman admin untuk masuk, memverifikasi laporan, dan memperbarui data.
- Asisten percakapan berbasis AI melalui Supabase Edge Function.

## Teknologi

- HTML, CSS, dan JavaScript tanpa framework aplikasi atau bundler.
- Leaflet dan hasil ekspor qgis2web untuk peta.
- Turf.js untuk operasi geometri, serta Chart.js untuk grafik.
- Supabase untuk autentikasi/data aplikasi dan Edge Function untuk layanan chatbot.
- Server pengembangan Node.js berbasis modul bawaan untuk menyajikan file statis dan endpoint chatbot lama.

## Struktur Proyek

| Lokasi | Keterangan |
| --- | --- |
| `index.html` | Halaman utama |
| `map.html` | Halaman peta interaktif |
| `report.html` | Formulir pelaporan |
| `login.html` | Halaman masuk admin |
| `verify.html` | Halaman verifikasi laporan |
| `update.html` | Halaman pembaruan data |
| `admin-dashboard.html` | Dashboard peta admin versi terpisah/lama |
| `js/` | Logika aplikasi, integrasi Supabase, peta, dan pustaka JavaScript |
| `css/` | Stylesheet |
| `data/` | Data JSON/GeoJSON dan geometri untuk peta |
| `assests/`, `webfonts/` | Ikon, gambar, dan font lokal |
| `supabase/functions/ai-chat/` | Kode Supabase Edge Function untuk chatbot |
| `.github/workflows/deploy-pages.yml` | Workflow deployment GitHub Pages |

## Persyaratan

- Node.js versi **20.6.0 atau lebih baru** untuk menjalankan server lokal.
- Koneksi internet untuk tile peta, pustaka yang dimuat dari CDN, dan layanan Supabase.
- Proyek Supabase yang telah dikonfigurasi dengan tabel, kolom, dan kebijakan akses yang sesuai. Skema/migrasi database tidak disertakan dalam repositori ini.

## Menjalankan Secara Lokal

Jalankan perintah berikut dari folder proyek:

```sh
npm start
```

Server berjalan pada `http://localhost:3000` secara default. Buka `http://localhost:3000/map.html` untuk melihat peta. Untuk mengubah port, atur variabel `PORT`.

Server membaca berkas `.env` menggunakan dukungan `--env-file` Node.js. Salin `.env.example` menjadi `.env`, lalu atur nilai yang diperlukan:

```dotenv
PORT=3000
GROQ_API_KEY=isi_dengan_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

`GROQ_API_KEY` pada konfigurasi server digunakan oleh endpoint chatbot lama di server Node. Jangan masukkan API key rahasia ke kode frontend atau repositori.

> `.env.example` adalah templat dan tidak otomatis dibaca oleh server. Buat `.env` sebelum menjalankan server apabila konfigurasi endpoint chatbot lama dibutuhkan.

## Supabase dan Chatbot

Frontend menggunakan URL proyek Supabase dan publishable key dari `js/supabase-client.js`. Data kasus dibaca dari tabel `cases`, laporan menggunakan tabel `reports`, dan proses masuk admin membaca tabel `admins`. Pastikan tabel, kolom, autentikasi, dan Row Level Security (RLS) dikonfigurasi sesuai operasi yang digunakan aplikasi.

Chatbot pada halaman peta memanggil Supabase Edge Function `ai-chat`. Konfigurasikan secret berikut di lingkungan Supabase:

- `GROQ_API_KEY` — wajib untuk mengakses penyedia model.
- `ALLOWED_ORIGINS` — daftar origin yang diizinkan.
- `GROQ_MODEL` — opsional; model bawaan adalah `openai/gpt-oss-120b`.

Edge Function perlu di-deploy secara terpisah dari situs. Nilai konfigurasi server Node dalam `.env` tidak menggantikan secret Edge Function.

## Deployment

Workflow GitHub Pages yang tersedia melakukan deployment situs saat ada push ke branch `main`. GitHub Pages hanya menyediakan file statis; layanan Supabase dan Edge Function harus dikonfigurasi serta di-deploy secara terpisah. Pastikan pengaturan Supabase mengizinkan origin situs yang telah di-deploy.

## Catatan Keamanan dan Data

- Pemeriksaan akses admin pada antarmuka browser bukan pengganti kontrol akses database. Lindungi operasi data dengan kebijakan RLS dan validasi sisi server yang sesuai.
- Pengaturan CORS/`ALLOWED_ORIGINS` mengendalikan origin yang diizinkan, tetapi bukan mekanisme autentikasi.
- Aplikasi memuat tile peta satelit dari Google dan beberapa pustaka eksternal, sehingga fitur terkait memerlukan koneksi internet.
- Data kasus DBD mencantumkan sumber HEWS. Sumber untuk seluruh set data penyakit lainnya tidak dapat dipastikan dari dokumentasi/berkas yang tersedia.
- Skrip `upload_cases_to_supabase.py` disebut dalam konfigurasi proyek, tetapi tidak disertakan dalam repositori.
