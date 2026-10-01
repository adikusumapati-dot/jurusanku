import os
from datetime import timedelta

from flask import Flask, abort, jsonify, render_template, request, session, url_for
from itsdangerous import BadSignature, URLSafeSerializer

from database import get_db, init_db
from engine import match_pct, potentials_from, rank
from settings import DIM_NAMES, DIM_SHORT, DIMS, GROWTH, JALUR, KAMPUS_TIPE, RUMPUN

# File statis ada di folder "public" agar cocok dengan Vercel (isi public/ disajikan CDN di alamat root).
app = Flask(__name__, static_folder="public", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-ganti-di-produksi")
app.permanent_session_lifetime = timedelta(days=365)
app.config.update(SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")))
signer = URLSafeSerializer(app.secret_key, salt="hasil-tes")

init_db()  # bangun database dari data/*.json


# ---------- Helper ----------
def my_scores():
    """Skor RIASEC tes terakhir (token bertanda tangan di cookie sesi), atau None."""
    try:
        return signer.loads(session["hasil"])["s"]
    except (KeyError, BadSignature):
        return None


def with_campuses(majors):
    """Tambahkan m['campuses'] (kampus unggulan, PTN dulu lalu PTS) ke setiap jurusan (list dict)."""
    ids = [m["id"] for m in majors]
    found = {i: [] for i in ids}
    if ids:
        with get_db() as db:
            rows = db.execute(
                "SELECT mc.major_id, c.* FROM major_campuses mc JOIN campuses c ON c.id = mc.campus_id "
                f"WHERE mc.major_id IN ({','.join('?' * len(ids))}) ORDER BY c.type, c.name",
                ids,
            ).fetchall()
        for r in rows:
            found[r["major_id"]].append(dict(r))
    for m in majors:
        m["campuses"] = found[m["id"]]
    return majors


# ---------- Halaman ----------
@app.route("/")
def index():
    last = session.get("hasil") if my_scores() else None
    with get_db() as db:
        n_major = db.execute("SELECT COUNT(*) FROM majors").fetchone()[0]
    return render_template("index.html", last=last, n_major=n_major)


@app.route("/quiz")
def quiz():
    with get_db() as db:
        qs = [dict(q) for q in db.execute("SELECT id, category, text FROM questions ORDER BY id")]
    return render_template("quiz.html", questions=qs)


@app.get("/result/<token>")
def result(token):
    """Hasil tes dibaca dari token bertanda tangan di URL, jadi tahan di hosting serverless."""
    try:
        data = signer.loads(token)
        scores = dict(zip(DIMS, data["s"]))
        nickname = data["n"]
    except (BadSignature, KeyError, TypeError):
        abort(404)
    with get_db() as db:
        majors = [dict(m) for m in db.execute("SELECT * FROM majors")]
    top = rank(scores, majors, 5)
    with_campuses([m for m, _ in top])
    code = "".join(sorted(DIMS, key=lambda k: -scores[k])[:3])
    return render_template(
        "result.html",
        nickname=nickname,
        scores=scores,
        potentials=potentials_from(scores),
        code=code,
        top=top,
        dim_names=DIM_NAMES,
        dim_short=DIM_SHORT,
    )


@app.get("/explore")
def explore():
    q = request.args.get("q", "").strip()
    rumpun = request.args.get("rumpun", "")
    sql, params = "SELECT * FROM majors WHERE 1=1", []
    if q:
        sql += " AND (name LIKE ? OR careers LIKE ? OR description LIKE ? OR courses LIKE ?)"
        params += [f"%{q}%"] * 4
    if rumpun in RUMPUN:
        sql += " AND rumpun=?"
        params.append(rumpun)
    with get_db() as db:
        majors = [dict(m) for m in db.execute(sql + " ORDER BY name", params)]
    return render_template("explore.html", majors=majors, q=q, rumpun=rumpun, rumpun_list=RUMPUN)


@app.get("/major/<slug>")
def major(slug):
    with get_db() as db:
        m = db.execute("SELECT * FROM majors WHERE slug=?", (slug,)).fetchone()
        if not m:
            abort(404)
        all_campuses = [dict(c) for c in db.execute("SELECT name, type FROM campuses ORDER BY name")]
    m = with_campuses([dict(m)])[0]
    sim = {
        "labels": ["Fresh grad"] + [f"{y} tahun" for y, _ in GROWTH[1:]],
        "min": [round(m["salary_min"] * g, 1) for _, g in GROWTH],
        "max": [round(m["salary_max"] * g, 1) for _, g in GROWTH],
    }
    return render_template(
        "major.html", m=m, sim=sim, jalur=JALUR, tipe_list=KAMPUS_TIPE, all_campuses=all_campuses
    )


@app.get("/compare")
def compare():
    with get_db() as db:
        allm = [dict(m) for m in db.execute("SELECT * FROM majors ORDER BY name")]
    by_slug = {m["slug"]: m for m in allm}
    a, b = by_slug.get(request.args.get("a")), by_slug.get(request.args.get("b"))
    chosen = with_campuses([m for m in (a, b) if m])
    me = my_scores()
    if me:
        for m in chosen:
            m["match"] = match_pct(me, m)
    return render_template(
        "compare.html", allm=allm, a=a, b=b, me=me, labels=[DIM_SHORT[k] for k in DIMS], dims=DIMS
    )


@app.get("/saved")
def saved():
    # Daftar jurusan impian & kampus target disimpan di browser (localStorage) dan digambar oleh public/app.js.
    return render_template("saved.html")


# ---------- API ----------
@app.get("/api/kartu")
def kartu():
    """Potongan HTML kartu jurusan untuk slug yang diberikan (dipakai halaman Jurusan Impian)."""
    slugs = [s for s in request.args.get("slugs", "").split(",") if s][:60]
    rows = []
    if slugs:
        with get_db() as db:
            rows = db.execute(
                f"SELECT * FROM majors WHERE slug IN ({','.join('?' * len(slugs))})", slugs
            ).fetchall()
    majors = sorted((dict(r) for r in rows), key=lambda m: slugs.index(m["slug"]))
    return render_template("_kartu.html", majors=majors)


@app.post("/api/quiz/submit")
def submit_quiz():
    d = request.get_json(silent=True) or {}
    answers = d.get("answers") or {}
    nickname = (d.get("nickname") or "").strip()[:30] or "Pelajar"
    with get_db() as db:
        qs = db.execute("SELECT id, dim FROM questions").fetchall()

    by_dim = {k: [] for k in DIMS}
    for q in qs:
        try:
            v = int(answers.get(str(q["id"])))
        except (TypeError, ValueError):
            return jsonify(error="Jawaban belum lengkap."), 400
        if not 1 <= v <= 5:
            return jsonify(error="Jawaban tidak valid."), 400
        by_dim[q["dim"]].append(v)

    scores = {k: round((sum(v) / len(v) - 1) / 4 * 100) if v else 0 for k, v in by_dim.items()}
    # Hasil dibawa lewat token bertanda tangan (URL + cookie), bukan lewat database.
    token = signer.dumps({"n": nickname, "s": [scores[k] for k in DIMS]})
    session["hasil"] = token
    session.permanent = True
    return jsonify(url=url_for("result", token=token))


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
