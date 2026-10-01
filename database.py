"""Database JurusanKu.

Sumber kebenaran data ada di folder data/*.json (mudah Anda edit). Saat aplikasi start,
file SQLite dibangun ulang dari JSON tersebut. Jadi tidak ada data yang "tertinggal"
dan cara kerjanya sama persis di komputer lokal, Vercel, Render, maupun PythonAnywhere.
"""

import json
import os
import re
import sqlite3
from contextlib import contextmanager

from settings import DIMS, KAMPUS_TIPE, RUMPUN

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Di Vercel hanya /tmp yang bisa ditulis. Di tempat lain, file ada di folder proyek.
_default = "/tmp/jurusanku.db" if os.environ.get("VERCEL") else os.path.join(BASE_DIR, "jurusanku.db")
DB_PATH = os.environ.get("DATABASE_PATH", _default)

SCHEMA = """
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, dim TEXT NOT NULL, text TEXT NOT NULL
);
CREATE TABLE campuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL, city TEXT DEFAULT '', website TEXT DEFAULT ''
);
CREATE TABLE majors (
    id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT UNIQUE NOT NULL, name TEXT NOT NULL, rumpun TEXT NOT NULL,
    r INTEGER, i INTEGER, a INTEGER, s INTEGER, e INTEGER, c INTEGER,
    description TEXT, courses TEXT, careers TEXT, salary_min REAL, salary_max REAL, pros TEXT, cons TEXT
);
CREATE TABLE major_campuses (
    major_id INTEGER NOT NULL, campus_id INTEGER NOT NULL, PRIMARY KEY (major_id, campus_id)
);
"""


class DataError(Exception):
    def __init__(self, problems):
        super().__init__("Data tidak valid:\n- " + "\n- ".join(problems))
        self.problems = problems


# ---------- Membaca & memvalidasi data JSON ----------
def _read(name, problems):
    try:
        with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        problems.append(f"{name}: file tidak ditemukan di folder data/")
        return []
    except json.JSONDecodeError as e:
        problems.append(
            f"{name}: format JSON salah di baris {e.lineno}, kolom {e.colno} ({e.msg}). "
            "Biasanya karena koma kurang/berlebih atau tanda kutip hilang."
        )
        return []
    if not isinstance(data, list):
        problems.append(f"{name}: isi file harus berupa daftar yang diawali [ dan diakhiri ]")
        return []
    return data


def _text(v):  # teks tidak kosong dan tidak memakai karakter '|'
    return isinstance(v, str) and v.strip() != "" and "|" not in v


def _text_list(v):
    return isinstance(v, list) and len(v) > 0 and all(_text(x) for x in v)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def load_data():
    """Baca dan validasi semua file di data/. Melempar DataError berisi daftar masalah jika ada."""
    problems = []
    questions = _read("pertanyaan.json", problems)
    before = len(problems)
    campuses = _read("kampus.json", problems)
    campuses_ok = len(problems) == before  # kalau kampus.json rusak, lewati cek nama kampus di jurusan
    majors = _read("jurusan.json", problems)

    # --- pertanyaan ---
    per_dim = {k: 0 for k in DIMS}
    for n, q in enumerate(questions, 1):
        w = f"pertanyaan.json #{n}"
        if not isinstance(q, dict):
            problems.append(f"{w}: harus berupa objek {{...}}")
            continue
        if not _text(q.get("kategori")):
            problems.append(f"{w}: 'kategori' wajib diisi (tanpa karakter |)")
        if q.get("dimensi") not in per_dim:
            problems.append(f"{w}: 'dimensi' harus salah satu dari {', '.join(DIMS)}")
        else:
            per_dim[q["dimensi"]] += 1
        if not isinstance(q.get("teks"), str) or not q["teks"].strip():
            problems.append(f"{w}: 'teks' wajib diisi")
    for k, n in per_dim.items():
        if n == 0 and questions:
            problems.append(f"pertanyaan.json: dimensi {k} belum punya pertanyaan (minimal 1, disarankan 3)")

    # --- kampus ---
    names = set()
    for n, c in enumerate(campuses, 1):
        w = f"kampus.json #{n}"
        if not isinstance(c, dict):
            problems.append(f"{w}: harus berupa objek {{...}}")
            continue
        if not _text(c.get("nama")):
            problems.append(f"{w}: 'nama' wajib diisi (tanpa karakter |)")
        elif c["nama"] in names:
            problems.append(f"{w}: nama kampus '{c['nama']}' dobel")
        else:
            names.add(c["nama"])
        if c.get("tipe") not in KAMPUS_TIPE:
            problems.append(f"{w} ({c.get('nama')}): 'tipe' harus {' atau '.join(KAMPUS_TIPE)}")
        if not isinstance(c.get("kota", ""), str):
            problems.append(f"{w} ({c.get('nama')}): 'kota' harus berupa teks")
        site = c.get("situs", "")
        if not isinstance(site, str) or (site and not site.startswith(("http://", "https://"))):
            problems.append(f"{w} ({c.get('nama')}): 'situs' harus diawali http:// atau https://")

    # --- jurusan ---
    slugs = set()
    for n, m in enumerate(majors, 1):
        if not isinstance(m, dict):
            problems.append(f"jurusan.json #{n}: harus berupa objek {{...}}")
            continue
        w = f"jurusan.json '{m.get('slug', f'#{n}')}'"
        slug = m.get("slug")
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9-]+", slug):
            problems.append(f"{w}: 'slug' wajib huruf kecil/angka/tanda minus saja, contoh: teknik-kimia")
        elif slug in slugs:
            problems.append(f"{w}: slug dobel")
        else:
            slugs.add(slug)
        for field in ("nama", "deskripsi"):
            if not _text(m.get(field)):
                problems.append(f"{w}: '{field}' wajib diisi (tanpa karakter |)")
        if m.get("rumpun") not in RUMPUN:
            problems.append(f"{w}: 'rumpun' harus salah satu dari {', '.join(RUMPUN)}")
        minat = m.get("minat")
        if not isinstance(minat, dict) or any(
            not isinstance(minat.get(k), int) or isinstance(minat.get(k), bool) or not 0 <= minat[k] <= 5 for k in DIMS
        ):
            problems.append(f"{w}: 'minat' harus memuat {', '.join(DIMS)} masing-masing angka bulat 0-5")
        for field in ("mata_kuliah", "karier", "plus", "minus"):
            if not _text_list(m.get(field)):
                problems.append(f"{w}: '{field}' harus daftar teks yang tidak kosong (tanpa karakter |)")
        gaji = m.get("gaji_juta")
        if not (isinstance(gaji, list) and len(gaji) == 2 and all(_num(x) for x in gaji) and 0 <= gaji[0] <= gaji[1]):
            problems.append(f"{w}: 'gaji_juta' harus [min, maks] dengan min <= maks, contoh: [4, 8]")
        kampus = m.get("kampus", [])
        if not isinstance(kampus, list) or not all(isinstance(x, str) for x in kampus):
            problems.append(f"{w}: 'kampus' harus daftar nama kampus")
        else:
            for x in kampus:
                if campuses_ok and x not in names:
                    problems.append(f"{w}: kampus '{x}' belum ada di kampus.json (tambahkan dulu, atau periksa ejaan)")
            if len(set(kampus)) != len(kampus):
                problems.append(f"{w}: ada kampus yang ditulis dobel di daftar 'kampus'")

    if problems:
        raise DataError(problems)
    return {"pertanyaan": questions, "kampus": campuses, "jurusan": majors}


# ---------- SQLite ----------
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Bangun ulang database dari data/*.json (ke file sementara, lalu ditukar secara atomik)."""
    data = load_data()
    tmp = DB_PATH + ".new"
    if os.path.exists(tmp):
        os.remove(tmp)
    conn = sqlite3.connect(tmp)
    try:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT INTO questions (category, dim, text) VALUES (?,?,?)",
            [(q["kategori"], q["dimensi"], q["teks"].strip()) for q in data["pertanyaan"]],
        )
        conn.executemany(
            "INSERT INTO campuses (name, type, city, website) VALUES (?,?,?,?)",
            [(c["nama"], c["tipe"], c.get("kota", ""), c.get("situs", "")) for c in data["kampus"]],
        )
        cid = {name: i for i, name in conn.execute("SELECT id, name FROM campuses")}
        for m in data["jurusan"]:
            v, g = m["minat"], m["gaji_juta"]
            cur = conn.execute(
                "INSERT INTO majors (slug,name,rumpun,r,i,a,s,e,c,description,courses,careers,"
                "salary_min,salary_max,pros,cons) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (m["slug"], m["nama"], m["rumpun"], v["R"], v["I"], v["A"], v["S"], v["E"], v["C"],
                 m["deskripsi"], "|".join(m["mata_kuliah"]), "|".join(m["karier"]), g[0], g[1],
                 "|".join(m["plus"]), "|".join(m["minus"])),
            )
            conn.executemany(
                "INSERT INTO major_campuses (major_id, campus_id) VALUES (?,?)",
                [(cur.lastrowid, cid[n]) for n in m.get("kampus", [])],
            )
        conn.commit()
    finally:
        conn.close()
    os.replace(tmp, DB_PATH)
