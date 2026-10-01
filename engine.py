"""Algoritma rekomendasi JurusanKu. Murni perhitungan, tanpa akses Flask/database."""

from settings import DIMS, POTENTIALS


def pearson(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** 0.5
    return num / den if den else 0.0


def match_pct(profile, major):
    """Kecocokan 0-100%: korelasi Pearson antara profil siswa [R,I,A,S,E,C] dan profil minat jurusan."""
    vec = [major[k.lower()] for k in DIMS]
    return round((pearson(profile, vec) + 1) / 2 * 100)


def potentials_from(scores):
    """Skor RIASEC (dict 0-100) -> potensi untuk grafik radar."""
    return {name: round(sum(scores[k] * w for k, w in ws.items())) for name, ws in POTENTIALS.items()}


def rank(scores, majors, top=5):
    """Urutkan jurusan (list dict) dari yang paling cocok. Return list [(jurusan, persen), ...]."""
    profile = [scores[k] for k in DIMS]
    ranked = sorted(((m, match_pct(profile, m)) for m in majors), key=lambda x: -x[1])
    return ranked[:top]
