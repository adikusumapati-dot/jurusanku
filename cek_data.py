"""Periksa file di folder data/ sebelum di-push:  python cek_data.py

Menampilkan pesan yang jelas kalau ada yang salah (koma kurang, nama kampus salah eja, dll.),
sehingga situs yang sedang live tidak rusak karena salah edit.
"""

import sys

from database import DataError, load_data

try:
    data = load_data()
except DataError as e:
    print("GAGAL - ada masalah pada data:\n")
    for p in e.problems:
        print(" -", p)
    print("\nPerbaiki dulu, lalu jalankan lagi: python cek_data.py")
    sys.exit(1)

print(
    f"OK - data valid: {len(data['jurusan'])} jurusan, "
    f"{len(data['kampus'])} kampus, {len(data['pertanyaan'])} pertanyaan."
)
