# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

```text
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')
```

---

## 2. Tiga kasus di mana regex salah

Untuk tiap kasus: SQL-nya, kesalahan regex, dan mengapa parser benar (kaitkan dengan konsep
lexing, parsing, atau resolusi).

### Kasus 1: Komentar yang Memuat Kata Kunci Perintah SQL
- **Potongan SQL** (`laporan_penjualan.sql` baris 2 & `pemeliharaan.sql` baris 2):
  ```sql
  -- DELETE FROM pelanggan   (baris ini komentar, bukan perintah)
  /* Catatan lama: UPDATE pelanggan_lama sudah tidak dipakai. */
  ```
- **Kesalahan regex**:
  Regex naif memindai pola teks mentah dengan ekspresi reguler `\bDELETE\s+FROM\s+([A-Za-z_]\w*)` dan `\bUPDATE\s+([A-Za-z_]\w*)`. Karena regex tidak memiliki konsep konteks komentar, regex salah menganggap teks di dalam komentar sebagai statement aktif, menghasilkan False Positive (`'pelanggan', 'D'` dan `'pelanggan_lama', 'U'`).
- **Mengapa parser benar (Konsep Lexing/Scanning - Bab 4)**:
  Pada arsitektur compiler, tahap pertama adalah **Lexer (Scanning)**. Lexer mengenali token awalan `--` dan `/* ... */` sebagai komentar non-semantik dan langsung membuang karakter tersebut tanpa menghasilkan token apa pun ke dalam aliran token (*token stream*). Akibatnya, parser hanya menerima token dari kode SQL yang sesungguhnya dan tidak pernah mengeksekusi operasi palsu dari komentar.

### Kasus 2: String Literal yang Berisi Kata Kunci SQL
- **Potongan SQL** (`laporan_penjualan.sql` baris 6):
  ```sql
  WHERE o.status = 'LUNAS' AND o.catatan <> 'FROM rahasia'
  ```
- **Kesalahan regex**:
  Pola regex `\bFROM\s+([A-Za-z_]\w*)` mencocokkan substring `'FROM rahasia'` yang berada di dalam tanda kutip tunggal. Akibatnya, regex mengira kata `rahasia` adalah sebuah nama tabel dan melabelinya sebagai operasi baca (`R`) secara salah (False Positive).
- **Mengapa parser benar (Konsep Lexing & Grammar - Bab 4 & 5)**:
  Lexer mengisolasi teks `'FROM rahasia'` sebagai satu kesatuan literal `TokenType.STRING` bernilai `"FROM rahasia"`. Ketika token ini diteruskan ke Parser, token tersebut berada di dalam pohon ekspresi biner (`ast.BinaryOp` dengan operator `<>`) sebagai literal nilai operan. Parser hanya mencari nama tabel pada aturan grammar klausa `FROM table_ref`, sehingga string literal di dalam klausa `WHERE` tidak akan pernah dianggap sebagai referensi tabel.

### Kasus 3: Tabel Kedua pada Klausa FROM Multitabel Terlewat
- **Potongan SQL** (`audit.sql` baris 2–3):
  ```sql
  SELECT p.id, p.nama
  FROM pelanggan p, pesanan o
  WHERE o.pelanggan_id = p.id ...
  ```
- **Kesalahan regex**:
  Pola regex hanya mencocokkan `\bFROM\s+([A-Za-z_]\w*)`, yang hanya mengambil kata pertama setelah keyword `FROM`, yaitu `pelanggan`. Tabel kedua setelah koma (`pesanan o`) tidak tertangkap sama sekali oleh regex, menghasilkan False Negative (`('audit.sql', 2, 'pesanan', 'R')` terlewat).
- **Mengapa parser benar (Konsep Parsing Recursive Descent - Bab 6)**:
  Parser mengimplementasikan aturan grammar context-free:
  `select_stmt = ... "FROM" table_ref { "," table_ref }`.
  Fungsi `_select()` mem-parse `sources = [self._table_ref()]` lalu menjalankan perulangan `while self._match(T.COMMA): sources.append(self._table_ref())`. Dengan demikian, berapa pun banyaknya tabel yang digabungkan dengan tanda koma di klausa `FROM` akan seluruhnya diurai ke dalam node AST dan diteruskan ke Resolver & Analyzer untuk dicatat operasinya.

---

## 3. Batas pendekatan kami

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

### Batas 1: Common Table Expressions (CTE) dengan Klausa `WITH`
- **Contoh SQL / Situasi**:
  ```sql
  WITH ringkasan_pesanan AS (
      SELECT pelanggan_id, SUM(total) AS total_belanja
      FROM pesanan
      GROUP BY pelanggan_id
  )
  SELECT p.nama, r.total_belanja
  FROM pelanggan p
  JOIN ringkasan_pesanan r ON r.pelanggan_id = p.id;
  ```
- **Akibat pada CRUD matrix**:
  Pada pipeline saat ini, klausa `WITH` berada di luar grammar yang didukung (SPESIFIKASI.md §9). Parser akan mengalami `ParseError` karena tidak mengenali token awal `WITH`. Jika pun kata kunci `WITH` diabaikan, `ringkasan_pesanan` akan salah dicatat sebagai tabel fisik database yang dibaca (`R`), padahal ia hanyalah view sementara dalam memori (*transient result set*).
- **Informasi yang dibutuhkan untuk mengatasinya**:
  Dibutuhkan perluasan produksi grammar untuk aturan `with_clause`, serta modifikasi pada Resolver untuk mencatat tabel CTE sebagai *virtual table scope* lokal sehingga Analyzer tidak mendaftarkannya sebagai tabel fisik database.

### Batas 2: Resolusi Kolom Ambigu Tanpa Skema Database
- **Contoh SQL / Situasi**:
  ```sql
  SELECT id, nama
  FROM pelanggan p
  JOIN pengguna u ON p.user_id = u.id;
  ```
- **Akibat pada CRUD matrix & Column Usage**:
  Menurut batasan arsitektur (SPESIFIKASI.md §7 butir 4), tool bekerja murni dari teks query tanpa koneksi ke database (*schemaless*). Ketika terdapat query multi-tabel dan kolom ditulis tanpa *qualifier* (misal `nama`), Resolver tidak dapat menentukan apakah `nama` milik tabel `pelanggan` atau `pengguna`. Sesuai aturan §4.3, kolom dibiarkan `resolved = None` dengan warning ambigu, sehingga relasi kolom-ke-tabel pada opsi `--kolom` menjadi tidak tercatat untuk kolom tersebut.
- **Informasi yang dibutuhkan untuk mengatasinya**:
  Dibutuhkan skema database (*database catalog / schema metadata / DDL script*) yang memuat daftar nama kolom valid untuk setiap tabel fisik guna menyelesaikan disosiasi kepemilikan kolom (*semantic disambiguation*).

### Batas 3: Pernyataan DDL, TRUNCATE, dan SQL Dinamis
- **Contoh SQL / Situasi**:
  ```sql
  TRUNCATE TABLE sesi_aktif;
  EXECUTE ('DELETE FROM ' + @nama_tabel + ' WHERE id = 1');
  ```
- **Akibat pada CRUD matrix**:
  Tool ini dirancang khusus untuk Static AST Analysis pada subset perintah DML terstruktur (`SELECT`, `INSERT`, `UPDATE`, `DELETE`). Perintah seperti `TRUNCATE TABLE` (yang secara semantik merupakan operasi Delete `D`) akan ditolak oleh parser sebagai syntax error. Begitu pula string SQL dinamis yang dirangkai saat runtime tidak dapat dianalisis secara statis sehingga tabel targetnya tidak terdeteksi sama sekali di matrix.
- **Informasi yang dibutuhkan untuk mengatasinya**:
  Untuk DDL/TRUNCATE dibutuhkan penambahan grammar parsing statement DDL ke dalam AST. Untuk dynamic query dibutuhkan pelacak aliran data dinamis (*dataflow / taint analysis*) atau evaluasi ekspresi runtime simbolik (*symbolic execution*).

---

## 4. Pembagian kerja

Siapa mengerjakan apa, dan bagaimana kalian memastikan keduanya memahami seluruh kode.

### Pembagian Tugas
- **Iryansyah**:
  - **Fase Lexer**: Implementasi `TODO(T3)` komentar blok `/* ... */`, perbaikan Bug 1 (normalisasi huruf besar keyword), Bug 2 (maximal munch operator `<>`), dan Bug 3 (penanganan escape `''` dalam string).
  - **Fase Analyzer**: Perbaikan Bug 4 (subquery pada `UPDATE` ditandai `R`, bukan `U`) dan Bug 10 (traversal ekspresi `column_usage` untuk baris nilai `INSERT VALUES`).
  - **Dokumentasi & Kasus Tepi**: Pengisian awal entri Bug 1–4 di `LAPORAN_BUG.md`, perancangan awal 5 keputusan desain di `KARTU_DESAIN.md`, serta pembuatan 5 tes kasus tepi di `test_tambahan.py`.

- **Salman**:
  - **Fase Parser**: Implementasi `TODO(T1)` sintaks `INSERT INTO ... SELECT ...`, perbaikan Bug 5 (presedensi operator `AND` lebih tinggi daripada `OR`), Bug 6 (dukungan kata kunci opsional `OUTER` pada `LEFT JOIN`), dan Bug 7 (panic mode error recovery `_synchronize()` yang berhenti di batas `;`).
  - **Fase Resolver**: Implementasi `TODO(T2)` resolusi kolom tanpa qualifier pada scope terdalam, perbaikan Bug 8 (kebocoran scope statement `DELETE` karena ketiadaan `_pop()`), dan Bug 9 (pembetulan arah rantai pencarian `_lookup()` untuk lexical shadowing subquery).
  - **Ground Truth & Integrasi Evaluasi**: Pelabelan manual 17 triple di `data/ground_truth.csv` untuk `audit.sql` dan `pemeliharaan.sql`, pengujian metrik evaluasi `evaluate.py` (mencapai F1 = 1.00), serta pelengkapan analisis pada `LAPORAN_AKHIR.md` dan `LAPORAN_BUG.md`.

### Memastikan Pemahaman Seluruh Kode (Persiapan Demo)
Meskipun modul implementasi dibagi berdasarkan fokus pipeline, kedua anggota memastikan pemahaman utuh terhadap seluruh sistem melalui:
1. **Pair-Programming & Code Review**: Setiap perbaikan modul diuji silang melalui penelaahan kode bersama (*peer review*) saat integrasi branch Git.
2. **Simulasi Prediksi AST & Resolusi**: Melatih kemampuan memprediksi pohon sintaks keluaran CLI `--ast` secara manual tanpa bantuan komputer untuk query-query kompleks (seperti correlated subquery dan nested expression).
3. **Simulasi Demo Lisan Mandiri**: Saling memberikan pertanyaan konsep berdasarkan buku *Crafting Interpreters* (Bab 4, 6, dan 11), seperti menjelaskan prinsip *maximal munch*, *stratified grammar*, *panic mode recovery*, hingga rantai *environment lexical scoping*, guna memastikan kesiapan menghadapi sesi uji individu oleh dosen pengampu.
