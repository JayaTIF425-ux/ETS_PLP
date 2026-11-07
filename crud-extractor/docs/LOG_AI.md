# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Salman & Iryansyah | Membaca deskripsi tugas ETS dan memetakan struktur kode serta baseline failure | Diterima | Membantu menyusun roadmap pengerjaan 6 jam dan memetakan seluruh modul | Menjalankan `pytest` awal dan mencatat 5 kegagalan awal pada test suite terlihat |
| 2 | Iryansyah | Memeriksa aturan scanning lexer untuk kata kunci, operator `<>`, escape quote, dan komentar blok | Diterima | Memberikan petunjuk implementasi `_scan_token()` dan penanganan maximal munch | Menjalankan `test_lexer.py` dan membuat test regresi di `test_tambahan.py` |
| 3 | Salman | Merancang hierarki recursive descent untuk presedensi `AND` vs `OR` dan klausul `LEFT OUTER JOIN` | Diterima | Mengusulkan pemisahan `_or_expr()` dan `_and_expr()` sesuai kaidah stratified grammar Bab 6 | Menguji ekspresi majemuk pada `test_regresi_parser_presedensi_and_over_or` |
| 4 | Salman | Menemukan penyebab terlewatnya statement valid setelah statement cacat pada panic mode | Diterima | Memperjelas bahwa synchronization point SQL berada pada batas delimiter titik koma (`;`) | Menjalankan `campuran_error.sql` dan memastikan statement valid sesudahnya tetap masuk AST |
| 5 | Salman | Menganalisis penyebab kebocoran alias statement `DELETE` dan kegagalan shadowing subquery | Diterima | Menemukan ketiadaan `_pop()` di `_delete()` dan kesalahan `reversed(chain)` pada `_lookup()` | Memeriksa hasil `--ast data/sample/audit.sql` dan memastikan alias terikat ke tabel lokal subquery |
| 6 | Salman | Merumuskan pelabelan manual untuk `audit.sql` dan `pemeliharaan.sql` di `ground_truth.csv` | Diterima dengan modifikasi | Membantu mengecek baris awal statement dan pemetaan relasi C/R/U/D | Menjalankan `evaluate.py` hingga mencapai Precision 1.00, Recall 1.00, dan F1 1.00 |
| 7 | Salman | Menyatukan entri TODO ke dalam daftar laporan bug | Ditolak | TODO adalah kelengkapan tugas bawaan berbobot terpisah (15%), bukan bug logika tersembunyi | Menata ulang laporan bug agar murni hanya berisi 10 bug dan menguji 1:1 di `test_tambahan.py` |
| 5 | Iryansyah | Membuat `tests/test_tambahan.py` (regresi + 5 kasus tepi) | Diterima dengan modifikasi | AI membuat draf mengikuti pola `test_lexer.py` dan `test_analyzer.py` | Menjalankan pytest, memeriksa tiap test regresi gagal pada kode lama |

**Refleksi (3-5 kalimat).**
AI sangat membantu dalam mempercepat identifikasi celah semantik yang samar, seperti rantai pencarian scope terbalik pada resolver dan pemisahan hierarki fungsi recursive descent untuk presedensi operator logika. Namun, interaksi dengan AI menuntut kehati-hatian karena AI sempat mengusulkan untuk memasukkan tugas kelengkapan fitur (TODO) ke dalam daftar laporan bug tersembunyi, yang langsung kami tolak dan koreksi agar sesuai rubrik penilaian. Seluruh saran kode, logika pohon AST, dan analisis teori selalu diverifikasi secara independen melalui pengujian regresi lokal (`pytest`) dan inspeksi visual keluaran `--ast` sebelum diintegrasikan ke repositori.
