# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: (judul singkat)

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---

## Bug 1: Keyword tidak dinormalisasi ke huruf besar

**Ditemukan oleh:** (Iryansyah) · **Diperbaiki oleh:** (Iryansyah)

**Gejala.** Keyword huruf kecil seperti `select` atau `Select` tidak dikenali sebagai
`KEYWORD`, melainkan sebagai `IDENT`. Menurut SPESIFIKASI.md §2.2, keyword tidak peka
huruf besar/kecil dan nilai token keyword selalu dinormalisasi ke huruf besar.

**Reproduksi minimal.**

```sql
select id from t
```

**Akar masalah.** Di `_word()`, teks asli (`text`) dibandingkan langsung dengan `KEYWORDS`
yang isinya huruf besar semua, lalu teks asli juga yang disimpan sebagai nilai token.
Ini melanggar prinsip *scanning* (Crafting Interpreters Bab 4) bahwa lexer bertanggung
jawab menormalisasi representasi token sebelum diteruskan ke parser.

**Perbaikan.** File `crud/lexer.py`, fungsi `_word()`. Variabel `upper_text` sudah
dihitung tapi tidak dipakai sebagai nilai token — cukup ganti `text` menjadi `upper_text`
pada `_add()`. Alternatif yang ditolak: normalisasi di parser — ditolak karena parser
tidak seharusnya tahu detail representasi teks mentah SQL.

**Test regresi.** `test_regresi_keyword_huruf_campur`

**Peran AI.** (Verifikasi bug, syntax dan konsep)

---

## Bug 2: Komentar blok `/* */` selalu throw error

**Ditemukan oleh:** (Iryansyah) · **Diperbaiki oleh:** (Iryansyah)

**Gejala.** Input apapun yang mengandung `/*` langsung menghasilkan `LexError("komentar
blok belum didukung")`, padahal menurut SPESIFIKASI.md §2.3 komentar blok harus diproses
dan tidak menghasilkan token. Hanya komentar yang tidak ditutup yang boleh `LexError`.

**Reproduksi minimal.**

```sql
/* komentar */ SELECT id FROM t
```

**Akar masalah.** Implementasi hanya berisi `raise LexError` tanpa memproses karakter
apapun — fitur belum diimplementasi sama sekali. Ini melanggar prinsip *scanning*
(Crafting Interpreters Bab 4) bahwa lexer harus mengonsumsi seluruh karakter yang
membentuk satu lexeme sebelum menghasilkan token (atau tidak menghasilkan token untuk
komentar).

**Perbaikan.** File `crud/lexer.py`, fungsi `_scan_token()`. Loop karakter per karakter
ditambahkan untuk mengonsumsi isi komentar sampai ditemukan `*/`, dengan `raise LexError`
hanya jika EOF tercapai sebelum penutup. Alternatif yang ditolak: `str.find("*/")` —
ditolak karena tidak bisa melacak `\n` untuk memperbarui posisi baris dan kolom.

**Test regresi.** `test_regresi_komentar_blok_valid`

**Peran AI.** (Verifikasi bug, syntax dan konsep)

---

## Bug 3: Operator `<>` tidak dikenali

**Ditemukan oleh:** (Iryansyah) · **Diperbaiki oleh:** (Iryansyah)

**Gejala.** Input `a <> b` menghasilkan token `OP(<)` lalu `OP(>)` sebagai dua token
terpisah, bukan satu token `OP(<>)`. Menurut SPESIFIKASI.md §2.5, lexer harus mengambil
operator terpanjang yang cocok (maximal munch).

**Reproduksi minimal.**

```sql
SELECT id FROM t WHERE a <> b
```

**Akar masalah.** Blok `if ch == "<"` hanya mengecek `<=` tapi tidak mengecek `<>`,
sehingga `>` setelah `<` tidak dikonsumsi dan menjadi token tersendiri. Ini melanggar
prinsip *maximal munch* dalam scanning (Crafting Interpreters Bab 4).

**Perbaikan.** File `crud/lexer.py`, fungsi `_scan_token()`. Ditambahkan pengecekan
`_match(">")` sebelum `_match("=")` pada blok `<`. Alternatif yang ditolak: menangani
`<>` sebagai dua token di parser — ditolak karena tanggung jawab pengenalan operator ada
di lexer, bukan parser.

**Test regresi.** `test_regresi_operator_tidak_sama`

**Peran AI.** (Verifikasi bug, syntax dan konsep)

---

## Bug 4: Escape `''` dalam string tidak ditangani

**Ditemukan oleh:** (Iryansyah) · **Diperbaiki oleh:** (Iryansyah)

**Gejala.** Input `'O''Brien'` menghasilkan token `STRING` bernilai `O` dan menyisakan
`'Brien'` sebagai token berikutnya, bukan satu token `STRING` bernilai `O'Brien`.
Menurut SPESIFIKASI.md §2.4, dua kutip berturut-turut di dalam string mewakili satu
karakter kutip.

**Reproduksi minimal.**

```sql
SELECT 'O''Brien'
```

**Akar masalah.** Di `_string()`, begitu ditemukan karakter `'`, loop langsung `break`
tanpa mengecek apakah kutip berikutnya juga `'`. Ini melanggar aturan escape string SQL
(Crafting Interpreters Bab 4 — literal string dengan karakter escape).

**Perbaikan.** File `crud/lexer.py`, fungsi `_string()`. Ditambahkan pengecekan
`_peek() == "'"` setelah menemukan kutip — jika iya, kutip kedua dikonsumsi dan `'`
ditambahkan ke `chars`. Alternatif yang ditolak: post-processing string setelah lexing —
ditolak karena informasi posisi karakter sudah tidak akurat setelah lexer selesai.

**Test regresi.** `test_regresi_string_kutip_ganda`

**Peran AI.** (Verifikasi bug, syntax dan konsep)

---

## Bug 5: Subquery di `SET`/`WHERE` UPDATE ditandai `U`, seharusnya `R`

**Ditemukan oleh:** (Iryansyah) · **Diperbaiki oleh:** (Iryansyah)

**Gejala.** Tabel yang dibaca lewat subquery di dalam `SET` atau `WHERE` pada statement
`UPDATE` mendapat operasi `U`, padahal menurut SPESIFIKASI.md §5 subquery selalu
menghasilkan `R` apapun jenis statement luarnya.

**Reproduksi minimal.**

```sql
UPDATE pelanggan SET poin = 0 WHERE id IN (SELECT id FROM blacklist)
```

**Akar masalah.** Di `analyze_statement()`, `_collect()` untuk `SET` dan `WHERE` pada
`Update` dipanggil dengan operasi `"U"` — operasi statement luar diwariskan ke subquery.
Ini melanggar aturan §5 bahwa subquery selalu merupakan operasi baca.

**Perbaikan.** File `crud/analyzer.py`, fungsi `analyze_statement()` blok `Update`.
Argumen `op` pada pemanggilan `_collect()` untuk assignments dan where diubah dari `"U"`
menjadi `"R"`. Alternatif yang ditolak: mendeteksi subquery di dalam `_collect()` dan
memaksa `R` di sana — ditolak karena lebih rumit dan melanggar prinsip bahwa operasi
ditentukan di `analyze_statement`, bukan di helper.

**Test regresi.** `test_regresi_update_subquery_where`

**Peran AI.** (Verifikasi bug, syntax dan konsep)
