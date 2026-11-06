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

---

## Bug 6: Presedensi operator logika `AND` dan `OR` disatukan di satu level

**Ditemukan oleh:** (Salman) · **Diperbaiki oleh:** (Salman)

**Gejala.** Ekspresi logika seperti `a = 1 OR b = 2 AND c = 3` diparse sebagai `(a = 1 OR b = 2) AND c = 3`. Menurut SPESIFIKASI.md §3.1, `AND` memiliki tingkat presedensi 2 (lebih tinggi) dibandingkan `OR` yang berada di tingkat 1, sehingga seharusnya dievaluasi sebagai `a = 1 OR (b = 2 AND c = 3)`.

**Reproduksi minimal.**

```sql
SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3
```

**Akar masalah.** Di fungsi `_logical()`, perulangan `while self._check_kw("AND", "OR")` memproses kedua operator logika secara sejajar dalam satu loop dari kiri ke kanan. Ini melanggar aturan *Stratified Grammar* pada recursive descent parser (*Crafting Interpreters* Bab 6 — Operator Precedence), di mana setiap tingkat presedensi harus dipisahkan ke dalam fungsi berbeda agar operator berpresedensi lebih tinggi dievaluasi terlebih dahulu.

**Perbaikan.** File `crud/parser.py`. Memecah `_logical()` menjadi dua metode berjenjang: `_or_expr()` yang memanggil `_and_expr()`, dan `_and_expr()` yang memanggil `_not()`. Alternatif yang ditolak: merestrukturisasi pohon AST setelah parsing selesai (*tree rewiring*) — ditolak karena membuat kode rumit dan melanggar prinsip *single-pass recursive descent*.

**Test regresi.** `test_regresi_parser_presedensi_and_over_or`

**Peran AI.** (Verifikasi pemisahan hierarki fungsi recursive descent untuk grammar presedensi)

---

## Bug 7: Klausa `LEFT JOIN` menolak kata kunci opsional `OUTER`

**Ditemukan oleh:** (Salman) · **Diperbaiki oleh:** (Salman)

**Gejala.** Query yang memuat klausul `LEFT OUTER JOIN` menghasilkan `ParseError: diharapkan JOIN, ditemukan 'OUTER'`. Menurut SPESIFIKASI.md §3, grammar klausul join memperbolehkan token opsional `OUTER`: `[ "INNER" | "LEFT" [ "OUTER" ] ] "JOIN"`.

**Reproduksi minimal.**

```sql
SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id
```

**Akar masalah.** Di fungsi `_join()`, setelah mencocokkan kata kunci `LEFT`, parser langsung memanggil `self._expect_kw("JOIN")` tanpa memeriksa kemungkinan adanya token opsional `OUTER`. Ini melanggar aturan produksi grammar untuk klausul join (*Crafting Interpreters* Bab 6 — Parsing Grammar Productions).

**Perbaikan.** File `crud/parser.py`, fungsi `_join()`. Menambahkan `self._match_kw("OUTER")` setelah pencocokan `LEFT` untuk mengonsumsi token `OUTER` jika ada. Alternatif yang ditolak: menggabungkan `"LEFT OUTER"` menjadi satu token di lexer — ditolak karena `LEFT` dan `OUTER` adalah dua lexeme terpisah yang masing-masing merupakan keyword mandiri.

**Test regresi.** `test_regresi_parser_left_outer_join`

**Peran AI.** (Verifikasi aturan produksi grammar SQL pada klausa join)

---

## Bug 8: Panic mode error recovery membuang seluruh sisa token hingga EOF

**Ditemukan oleh:** (Salman) · **Diperbaiki oleh:** (Salman)

**Gejala.** Jika sebuah file SQL memiliki lebih dari satu statement dan salah satu statement mengandung kesalahan sintaks, seluruh statement valid berikutnya ikut terbuang dan tidak menghasilkan keluaran di CRUD matrix. Menurut SPESIFIKASI.md §6, panic mode harus membuang token sampai dan termasuk `;` berikutnya, lalu melanjutkan parsing statement berikutnya.

**Reproduksi minimal.**

```sql
SELECT id nama, FROM pesanan;
UPDATE produk SET stok = stok - 1 WHERE id = :id;
```

**Akar masalah.** Fungsi `_synchronize()` mengonsumsi token dengan loop `while not self._at_end(): self._advance()`, yang membuang semua token hingga akhir file (`EOF`). Ini melanggar konsep *Panic Mode Error Recovery* (*Crafting Interpreters* Bab 6 — Panic Mode Recovery), di mana parser harus menyinkronkan diri pada batas statement terdekat (*synchronization point*, yaitu titik koma `;`).

**Perbaikan.** File `crud/parser.py`, fungsi `_synchronize()`. Mengubah loop agar berhenti begitu mengonsumsi token `T.SEMICOLON` (`if self._advance().type == T.SEMICOLON: return`). Alternatif yang ditolak: sinkronisasi berbasis kata kunci statement (`SELECT`, `UPDATE`) — ditolak karena SPESIFIKASI.md §6 secara eksplisit mewajibkan sinkronisasi sampai dan termasuk `;` berikutnya.

**Test regresi.** `test_regresi_parser_panic_mode_recovery`

**Peran AI.** (Verifikasi perilaku pemulihan panic-mode pada batas delimiter statement)

---

## Bug 9: Kebocoran scope (*Scope Leak*) pada statement `DELETE`

**Ditemukan oleh:** (Salman) · **Diperbaiki oleh:** (Salman)

**Gejala.** Alias tabel dari statement `DELETE` masih terlihat dan dapat diakses oleh statement berikutnya. Menurut SPESIFIKASI.md §4.5, setiap statement berdiri sendiri dan alias dari statement sebelumnya tidak boleh terlihat oleh statement berikutnya.

**Reproduksi minimal.**

```sql
DELETE FROM sesi s WHERE s.id = 1;
SELECT s.id FROM pengguna u WHERE u.aktif = 1;
```

**Akar masalah.** Di `Resolver._delete()`, fungsi memanggil `self._push()` untuk membuka scope baru, namun lupa memanggil `self._pop()` saat selesai. Akibatnya, scope `DELETE` tidak pernah dihancurkan dan menjadi parent scope dari statement berikutnya (*Crafting Interpreters* Bab 11 — Resolving and Binding / Scope Management).

**Perbaikan.** File `crud/resolver.py`, fungsi `_delete()`. Menambahkan pemanggilan `self._pop()` di akhir blok `_delete()`. Alternatif yang ditolak: mereset `self.scope = None` di `resolve_statement()` — ditolak karena membiarkan inkonsistensi struktur push-pop di dalam blok fungsi statement.

**Test regresi.** `test_regresi_resolver_scope_leak_delete`

**Peran AI.** (Verifikasi siklus hidup scope push-pop pada AST resolver)

---

## Bug 10: Urutan pencarian scope terbalik pada `_lookup()` (Shadowing subquery rusak)

**Ditemukan oleh:** (Salman) · **Diperbaiki oleh:** (Salman)

**Gejala.** Pada correlated subquery yang mendeklarasikan alias yang sama dengan query luar, kolom di dalam subquery salah ter-resolve ke tabel luar. Menurut SPESIFIKASI.md §4.3, qualifier harus dicari mulai dari scope terdalam ke luar, sehingga alias di subquery harus membayangi (*shadowing*) alias luar.

**Reproduksi minimal.**

```sql
SELECT x.id FROM pelanggan x WHERE x.id IN (SELECT x.pelanggan_id FROM pesanan x WHERE x.total > 500);
```

**Akar masalah.** Di fungsi `_lookup()`, rantai scope dikumpulkan dari `self.scope` (terdalam) ke `scope.parent` (terluar), namun kemudian diiterasi dengan `for scope in reversed(chain)`. Hal ini menyebabkan pencarian berjalan dari scope terluar ke terdalam, sehingga alias luar menutupi alias subquery (*Crafting Interpreters* Bab 11 — Resolving and Binding / Lexical Scoping).

**Perbaikan.** File `crud/resolver.py`, fungsi `_lookup()`. Menghilangkan penggunaan array `chain` dan `reversed()`, lalu langsung menelusuri pointer rantai parent: `while scope is not None: if name in scope.entries: return ... scope = scope.parent`. Alternatif yang ditolak: menyimpan scope dalam stack dan indexing terbalik — ditolak karena struktur pointer linked-list parent chain lebih sederhana dan sesuai dengan pola buku teks.

**Test regresi.** `test_regresi_resolver_shadowing_dalam_ke_luar`

**Peran AI.** (Verifikasi arah traversal rantai lexical environment)

---

## Bug 11: Traversal `column_usage` untuk baris data `INSERT VALUES`

**Ditemukan oleh:** (Iryansyah) · **Diperbaiki oleh:** (Iryansyah)

**Gejala.** Pada statement `INSERT INTO ... VALUES (...)`, pemanggilan `reads(stmt.values)` pada struktur list-of-lists berpotensi tidak membaca ekspresi baris nilai secara deterministik jika node bukan merupakan dataclass datar. Menurut SPESIFIKASI.md §7 dan §8, penggunaan kolom harus mencatat kolom yang dibuat (`C`) dan dibaca (`R`).

**Reproduksi minimal.**

```sql
INSERT INTO log (id, nama) VALUES (1, 'test');
```

**Akar masalah.** Di fungsi `column_usage()`, argumen `stmt.values` diteruskan langsung ke `reads()`. Karena `values` adalah list of rows (`list[list[expr]]`), traversal lebih aman dan deterministik jika dilakukan per-baris dan per-ekspresi (*Crafting Interpreters* Bab 5 — Representing Code / AST Traversal).

**Perbaikan.** File `crud/analyzer.py`, fungsi `column_usage()`. Mengubah `reads(stmt.values)` menjadi loop eksplisit: `for row in stmt.values: for expr in row: reads(expr)`. Alternatif yang ditolak: memodifikasi utilitas umum `iter_nodes` — ditolak karena `iter_nodes` adalah API publik (SPESIFIKASI.md §7) yang tidak boleh diubah perilakunya.

**Test regresi.** `test_regresi_column_usage_insert_values`

**Peran AI.** (Verifikasi integritas API publik ast_nodes dan traversal nested list)
