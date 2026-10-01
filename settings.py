"""Pengaturan inti JurusanKu (jarang diubah).

Data yang sering Anda edit (jurusan, kampus, pertanyaan) ada di folder data/.
"""

# Urutan dimensi minat Holland Code: Realistic, Investigative, Artistic, Social, Enterprising, Conventional
DIMS = "RIASEC"

DIM_NAMES = {
    "R": "Realistic (Praktis)",
    "I": "Investigative (Penyelidik)",
    "A": "Artistic (Kreatif)",
    "S": "Social (Sosial)",
    "E": "Enterprising (Pemimpin)",
    "C": "Conventional (Teratur)",
}
DIM_SHORT = {"R": "Praktis", "I": "Penyelidik", "A": "Kreatif", "S": "Sosial", "E": "Pemimpin", "C": "Teratur"}

# Potensi (grafik radar) dihitung dari skor RIASEC dengan bobot ini (jumlah bobot tiap potensi = 1).
POTENTIALS = {
    "Logika": {"R": 0.2, "I": 0.5, "C": 0.3},
    "Kreativitas": {"A": 0.7, "I": 0.15, "E": 0.15},
    "Komunikasi": {"S": 0.5, "E": 0.3, "A": 0.2},
    "Analitis": {"I": 0.6, "C": 0.4},
    "Kepemimpinan": {"E": 0.7, "S": 0.3},
}

RUMPUN = ["Saintek", "Soshum", "Campuran"]
KAMPUS_TIPE = ["PTN", "PTS"]
JALUR = ["SNBP", "SNBT (UTBK)", "Mandiri PTN", "Jalur PTS / Beasiswa", "Lainnya"]

# Asumsi pengali kenaikan gaji untuk grafik simulasi (tahun ke-0, 3, 5, 10). Hanya ilustrasi.
GROWTH = [(0, 1.0), (3, 1.4), (5, 1.9), (10, 3.0)]
