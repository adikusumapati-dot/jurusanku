# Panduan Menambah & Mengedit JurusanKu

## 1. Peta kode: file mana untuk apa?

| Mau mengubah...                                   | Buka file                         |
|---------------------------------------------------|-----------------------------------|
| Isi/jumlah jurusan, kampus unggulan per jurusan   | `data/jurusan.json`               |
| Daftar kampus (nama, PTN/PTS, kota, situs)        | `data/kampus.json`                |
| Pertanyaan tes                                    | `data/pertanyaan.json`            |
| Bobot potensi radar, rumpun, jalur masuk          | `settings.py`                     |
| Rumus kecocokan jurusan                           | `engine.py`                       |
| Halaman & alamat URL baru                         | `app.py` + `templates/`           |
| Struktur tabel / pembacaan data                   | `database.py`                     |
| Warna & tampilan                                  | `public/style.css`, `templates/`  |
| Perilaku tombol simpan / kampus target            | `public/app.js`                   |

## 2. Mengedit data (paling sering dipakai)

Alurnya selalu sama:

1. Edit file di folder `data/` memakai VS Code.
2. Jalankan `python cek_data.py`. Jika ada salah, pesan di layar menunjukkan file dan bagian yang harus diperbaiki.
3. Coba di lokal: `python app.py`.
4. `git add .` -> `git commit -m "Tambah jurusan Teknik Kimia"` -> `git push`. Vercel memperbarui situs otomatis.

### Menambah jurusan

Salin satu blok `{ ... }` di `data/jurusan.json`, tempel di bawahnya (jangan lupa koma di antara blok), lalu ubah isinya:

```json
{
  "slug": "teknik-kimia",
  "nama": "Teknik Kimia",
  "rumpun": "Saintek",
  "minat": {"R": 4, "I": 5, "A": 1, "S": 1, "E": 2, "C": 3},
  "deskripsi": "Mempelajari proses mengubah bahan baku menjadi produk bernilai.",
  "mata_kuliah": ["Kimia Fisika", "Termodinamika", "Perpindahan Panas"],
  "karier": ["Process Engineer", "Quality Engineer"],
  "gaji_juta": [5, 10],
  "plus": ["Dibutuhkan di banyak industri"],
  "minus": ["Materi kimia dan matematika berat"],
  "kampus": ["Institut Teknologi Bandung", "Universitas Gadjah Mada"]
}
```

Aturan penting:

- `slug`: huruf kecil, angka, dan tanda minus saja. Harus unik. Jangan diubah setelah dipakai pengguna, karena jurusan impian tersimpan berdasarkan slug.
- `rumpun`: `Saintek`, `Soshum`, atau `Campuran`.
- `minat`: seberapa kuat tiap tipe kepribadian cocok dengan jurusan itu, angka 0 sampai 5.
  R = praktis/teknis, I = penyelidik/analitis, A = kreatif, S = sosial/membantu, E = memimpin/berbisnis, C = teratur/detail.
  Beri angka 4-5 pada 2-3 tipe yang paling menonjol dan angka rendah pada sisanya. Profil yang bervariasi membuat rekomendasi lebih tajam.
- `gaji_juta`: `[minimum, maksimum]` estimasi gaji awal per bulan dalam juta rupiah.
- `kampus`: harus sama persis dengan `nama` di `kampus.json`.
- Jangan memakai karakter `|` di dalam teks.

### Menghapus / mengubah jurusan

Hapus atau ubah blok terkait. Ingat: blok terakhir tidak boleh diakhiri koma.

### Menambah kampus

Tambah satu baris di `data/kampus.json`:

```json
{"nama": "Universitas Contoh", "tipe": "PTS", "kota": "Bandung", "situs": "https://contoh.ac.id"},
```

Lalu tuliskan namanya di daftar `"kampus"` pada jurusan yang relevan. `situs` boleh dikosongkan (`""`).

### Menambah pertanyaan

Tambah satu baris di `data/pertanyaan.json`:

```json
{"kategori": "Hobi", "dimensi": "I", "teks": "Saya senang membaca artikel sains populer."}
```

`dimensi` adalah R, I, A, S, E, atau C. Usahakan tiap dimensi punya jumlah pertanyaan yang sama agar skor adil.

## 3. Menambah fitur baru (kode)

Prinsip: ubah sedikit-sedikit, uji di lokal, baru push.

**Halaman baru** (contoh: halaman "Tentang"):

1. `templates/tentang.html`: salin kerangka dari `templates/saved.html` (mulai dengan `{% extends "base.html" %}`).
2. Di `app.py` tambahkan:
   ```python
   @app.route("/tentang")
   def tentang():
       return render_template("tentang.html")
   ```
3. Di `templates/base.html`, tambahkan `('tentang','Tentang')` pada daftar menu navbar.

**Kolom data baru pada jurusan** (contoh: "biaya kuliah"):

1. Tambah field di `data/jurusan.json`.
2. `database.py`: tambah kolom di `CREATE TABLE majors`, di `INSERT INTO majors`, dan (opsional) aturan validasinya di `load_data`.
3. Tampilkan di `templates/major.html` memakai `{{ m.nama_kolom }}`.

**Mengubah rumus rekomendasi:** `engine.py` (fungsi `match_pct`). **Mengubah bobot grafik radar:** `settings.py` (`POTENTIALS`).

## 4. Alur Git yang aman

Untuk perubahan besar, jangan langsung ke `main`:

```
git checkout -b fitur-baru
# ...ubah kode, uji...
git add . && git commit -m "Jelaskan perubahan"
git push -u origin fitur-baru
```

Vercel otomatis membuat alamat pratinjau untuk branch itu. Jika sudah bagus, gabungkan lewat tombol **Merge** di GitHub (Pull Request). Jika ada yang salah, situs utama tidak terpengaruh.

## 5. Masalah umum

| Gejala                                         | Penyebab & solusi                                                                 |
|------------------------------------------------|-----------------------------------------------------------------------------------|
| Situs error 500 setelah edit data              | Jalankan `python cek_data.py`, perbaiki sesuai pesan, push lagi.                  |
| Edit data tidak muncul di lokal                | Hentikan (`Ctrl+C`) dan jalankan ulang `python app.py`. Data dibaca saat start.   |
| Tampilan polos (CSS tidak muncul)              | Pastikan `style.css` dan `app.js` ada di folder `public/`, bukan `static/`.       |
| Jurusan impian "hilang"                        | Disimpan per browser. Berganti HP/browser atau menghapus data situs menghilangkannya. |
| `git push` ditolak                             | Jalankan `git pull --rebase`, lalu `git push` lagi.                               |

## 6. Minta bantuan AI

Anda bisa menempelkan isi file yang relevan ke Claude beserta permintaan yang spesifik, misalnya:
"Di proyek Flask ini, tambahkan filter rentang gaji di halaman Jelajah Jurusan. Berikut `app.py` dan `templates/explore.html`: ..."
