# WebGIS Semarang

## Menjalankan aplikasi

Chatbot memakai Supabase Edge Function dan koneksi internet, jadi halaman tidak dapat dibuka dengan klik dua kali (`file://`).

Untuk melihat aplikasi secara lokal, gunakan Node.js 20.6 atau lebih baru dan jalankan `npm.cmd start` dari folder proyek. Buka `http://localhost:3000/map.html`; tambahkan `http://localhost:3000` ke secret `ALLOWED_ORIGINS` Supabase jika ingin menguji chatbot dari lokal.

Jangan masukkan API key Groq ke `.env`, `.env.example`, atau Git. Simpan key sebagai secret di proyek Supabase. Tidak perlu memasang atau mengunduh model lokal.
Skrip lokal `upload_cases_to_supabase.py` sengaja tidak disertakan karena memuat service-role key; pindahkan key ke environment variable sebelum membagikan skrip tersebut.

## Konteks chatbot

Chatbot menggunakan filter penyakit/tahun aktif, ringkasan kasus per kecamatan, rincian jenis kelamin dan kematian, tren bulanan, serta zona aksesibilitas. Untuk pertanyaan di luar data peta, chatbot dapat menjawab sebagai pengetahuan umum dan menandai bahwa jawabannya bukan analisis data Semarang. Chatbot tidak memiliki akses pencarian web.

## Deploy

### Chatbot dengan Supabase Edge Functions

1. Cabut API key Groq yang pernah terekspos dan buat key baru.
2. Pastikan CLI sudah di-link ke project ref `qcjdstuwlaykxfbltzmp`. Jika belum, jalankan `npx.cmd supabase login`, lalu `npx.cmd supabase link --project-ref qcjdstuwlaykxfbltzmp` dari folder proyek.
3. Di Dashboard Supabase, buka **Edge Functions → Secrets** dan tambahkan `GROQ_API_KEY` dengan key baru serta `ALLOWED_ORIGINS` dengan nilai `https://arvaakhadi.github.io`. Untuk uji lokal, tambahkan origin lokal dengan koma, misalnya `https://arvaakhadi.github.io,http://localhost:3000`.
4. Deploy function: `npx.cmd supabase functions deploy ai-chat --no-verify-jwt`.
5. Di GitHub repo, buka **Settings → Pages**, pilih **GitHub Actions** pada Source.
6. Push ke branch `main` untuk menjalankan workflow Pages. Situs tersedia di `https://arvaakhadi.github.io/webgis-semarang/map.html`.

`GROQ_API_KEY` harus disimpan sebagai secret Supabase Edge Function, bukan GitHub Actions secret. Function chatbot tidak memakai verifikasi JWT bawaan karena aplikasi menggunakan public publishable key. CORS membatasi browser ke origin yang dikonfigurasi, tetapi CORS bukan pengganti autentikasi dan tidak menghentikan pemanggilan langsung di luar browser. Pantau batas penggunaan Groq dan Supabase. Jangan deploy `.env` atau membagikan API key di sisi browser.

`server.js` masih menyediakan endpoint Node.js lama `/api/chat`, tetapi halaman chatbot kini memanggil Edge Function Supabase.
