// ===== Penyimpanan di browser (localStorage): jurusan impian & kampus target =====
// Disimpan per-perangkat sehingga bekerja di hosting apa pun (termasuk Vercel) tanpa database.
const $ = (id) => document.getElementById(id);
const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const Store = {
  get(key, fallback) {
    try {
      return JSON.parse(localStorage.getItem(key)) ?? fallback;
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {}
  },
  bookmarks() {
    return this.get("jk_bookmarks", []);
  },
  toggleBookmark(slug) {
    const list = this.bookmarks();
    const i = list.indexOf(slug);
    if (i >= 0) list.splice(i, 1);
    else list.unshift(slug);
    this.set("jk_bookmarks", list);
    return i < 0; // true = sekarang tersimpan
  },
  targets() {
    return this.get("jk_targets", []);
  },
  addTarget(t) {
    const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    this.set("jk_targets", [{ id, ...t }, ...this.targets()]);
  },
  removeTarget(id) {
    this.set("jk_targets", this.targets().filter((t) => t.id !== id));
  },
};

// Tombol "Simpan" mengikuti status di localStorage
function paintBookmarks(root = document) {
  const saved = new Set(Store.bookmarks());
  root.querySelectorAll("[data-bookmark]").forEach((b) => {
    const on = saved.has(b.dataset.bookmark);
    b.classList.toggle("btn-warning", on);
    b.classList.toggle("btn-outline-warning", !on);
    b.textContent = on ? "★ Tersimpan" : "☆ Simpan";
  });
}

// Daftar kampus target (halaman detail jurusan & halaman Jurusan Impian)
function renderTargets() {
  const all = Store.targets();

  const list = $("targetList");
  if (list) {
    const items = all.filter((t) => t.slug === list.dataset.slug);
    list.innerHTML = items.length
      ? items
          .map(
            (t) => `<li class="list-group-item px-0 d-flex justify-content-between gap-2">
              <div><b>${esc(t.campus)}</b> <span class="badge text-bg-secondary">${esc(t.type)}</span>
                <div class="small text-muted">${esc(t.path)}${t.note ? " · " + esc(t.note) : ""}</div></div>
              <button class="btn btn-sm btn-outline-danger align-self-start" data-del-target="${esc(t.id)}" aria-label="Hapus">🗑️</button>
            </li>`
          )
          .join("")
      : '<li class="list-group-item px-0 text-muted small">Belum ada kampus target untuk jurusan ini.</li>';
  }

  const rows = $("targetRows");
  if (rows) {
    $("targetWrap").classList.toggle("d-none", !all.length);
    $("noTargets").classList.toggle("d-none", all.length > 0);
    rows.innerHTML = all
      .map(
        (t) => `<tr>
          <td><b>${esc(t.campus)}</b> <span class="badge text-bg-secondary">${esc(t.type)}</span></td>
          <td><a class="text-decoration-none" href="/major/${encodeURIComponent(t.slug)}">${esc(t.major_name)}</a></td>
          <td>${esc(t.path)}</td>
          <td class="small text-muted">${esc(t.note || "")}</td>
          <td><button class="btn btn-sm btn-outline-danger" data-del-target="${esc(t.id)}" aria-label="Hapus">🗑️</button></td>
        </tr>`
      )
      .join("");
  }
}

// Halaman Jurusan Impian: ambil kartu jurusan dari server berdasarkan slug yang tersimpan
async function loadSavedPage() {
  const box = $("bmList");
  if (!box) return;
  const slugs = Store.bookmarks();
  if (!slugs.length) return $("bmEmpty").classList.remove("d-none");
  try {
    const res = await fetch("/api/kartu?slugs=" + encodeURIComponent(slugs.join(",")));
    box.innerHTML = await res.text();
    paintBookmarks(box);
    if (!box.children.length) $("bmEmpty").classList.remove("d-none");
  } catch {
    box.innerHTML = '<p class="text-danger">Gagal memuat daftar. Coba muat ulang halaman.</p>';
  }
}

document.addEventListener("click", (e) => {
  // Simpan / lepas jurusan
  const bm = e.target.closest("[data-bookmark]");
  if (bm) {
    const nowSaved = Store.toggleBookmark(bm.dataset.bookmark);
    if (!nowSaved && bm.hasAttribute("data-remove")) {
      bm.closest(".col-md-6")?.remove();
      if (!$("bmList").children.length) $("bmEmpty").classList.remove("d-none");
    }
    return paintBookmarks();
  }

  // Hapus kampus target
  const del = e.target.closest("[data-del-target]");
  if (del && confirm("Hapus kampus target ini?")) {
    Store.removeTarget(del.dataset.delTarget);
    return renderTargets();
  }

  // Tombol "+ Target" pada daftar kampus unggulan: isi otomatis form
  const pf = e.target.closest("[data-prefill-campus]");
  if (pf) {
    const f = $("targetForm").elements;
    f.campus.value = pf.dataset.prefillCampus;
    f.campus_type.value = pf.dataset.prefillType;
    $("targetForm").scrollIntoView({ behavior: "smooth", block: "center" });
    f.path.focus();
  }
});

const tf = $("targetForm");
if (tf) {
  const f = tf.elements;
  // Pilih kampus yang sudah dikenal -> tipe PTN/PTS terisi otomatis
  f.campus.addEventListener("input", () => {
    const opt = [...document.querySelectorAll("#kampus option")].find((o) => o.value === f.campus.value);
    if (opt) f.campus_type.value = opt.dataset.type;
  });
  tf.addEventListener("submit", (e) => {
    e.preventDefault();
    const campus = f.campus.value.trim();
    if (!campus) return;
    Store.addTarget({
      slug: f.slug.value,
      major_name: f.major_name.value,
      campus,
      type: f.campus_type.value,
      path: f.path.value,
      note: f.note.value.trim(),
    });
    f.campus.value = "";
    f.note.value = "";
    renderTargets();
  });
}

paintBookmarks();
renderTargets();
loadSavedPage();
