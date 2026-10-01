# JurusanKu

Website rekomendasi jurusan kuliah untuk siswa SMA: tes minat (Holland Code / RIASEC), rekomendasi top 5 jurusan
dengan persentase kecocokan, grafik potensi, katalog jurusan + kampus PTN/PTS unggulan, perbandingan 2 jurusan,
serta jurusan impian dan kampus target.

Teknologi: Python Flask, SQLite, Bootstrap 5, Chart.js.

## Struktur

```
jurusanku/
├── app.py            # Halaman & API (Flask)
├── engine.py         # Algoritma kecocokan jurusan
├── database.py       # Membangun SQLite dari data/*.json + validasi
├── settings.py       # Dimensi RIASEC, bobot potensi, daftar jalur masuk
├── cek_data.py       # Pemeriksa data sebelum push
├── data/
│   ├── jurusan.json      # <- EDIT di sini untuk jurusan
│   ├── kampus.json       # <- EDIT di sini untuk kampus
│   └── pertanyaan.json   # <- EDIT di sini untuk pertanyaan tes
├── templates/        # Halaman HTML (Jinja)
├── public/           # CSS & JS (disajikan langsung oleh Vercel)
├── requirements.txt  # Dependensi
└── Procfile          # Untuk Render (opsional)
```

## Menjalankan di komputer

```
python -m venv venv
venv\Scripts\activate            # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```

Buka http://127.0.0.1:5000

## Mengubah data (tanpa coding)

Edit file di folder `data/`, lalu jalankan `python cek_data.py` untuk memastikan tidak ada yang salah.
Cara lengkapnya ada di **PANDUAN.md**.

## Deploy: GitHub lalu Vercel

1. Buat repository kosong di github.com (tanpa README), lalu di folder proyek:
   ```
   git init
   git add .
   git commit -m "Versi awal JurusanKu"
   git branch -M main
   git remote add origin https://github.com/USERNAME/jurusanku.git
   git push -u origin main
   ```
2. Di vercel.com, login dengan GitHub, klik **Add New > Project**, pilih repo `jurusanku`, lalu **Import**.
3. Di **Environment Variables** tambahkan `SECRET_KEY` berisi teks acak panjang
   (buat dengan `python -c "import secrets; print(secrets.token_hex(32))"`).
4. Klik **Deploy**. Setiap `git push` berikutnya otomatis memperbarui situs.

## Catatan penting

- Data jurusan/kampus/pertanyaan dibaca dari `data/*.json` setiap aplikasi start, jadi mengubahnya = edit file lalu push.
- Jurusan impian dan kampus target pengguna disimpan di browser mereka (localStorage), bukan di server.
- Informasi gaji dan daftar kampus unggulan adalah kurasi awal/estimasi. Verifikasi ke sumber resmi (BAN-PT/LAM, SNPMB, situs kampus).
"# jurusanku" 
