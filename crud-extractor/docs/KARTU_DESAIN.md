# Kartu Desain

Tuliskan lima keputusan desain penting dalam pekerjaan kalian. Untuk tiap keputusan, sebutkan
alternatif yang ditolak dan alasannya. Contoh topik (boleh memilih yang lain):

- bagaimana parser membedakan `*` sebagai "semua kolom" dan sebagai perkalian;
- di mana dan bagaimana presedensi `AND`/`OR` dinyatakan;
- mengapa error recovery berhenti di `;`, bukan di keyword `SELECT` berikutnya;
- urutan pencarian scope dan akibatnya pada shadowing serta correlated subquery;
- mengapa kolom tanpa qualifier hanya dilihat di scope terdalam, dan apa kelemahannya;
- bagaimana implementasi `INSERT ... SELECT` atau komentar blok kalian.

| No | Keputusan | Alternatif yang ditolak | Alasan |
| --- | --- | --- | --- |
| 1 | Keyword dinormalisasi ke huruf besar saat di-lex, bukan saat di-parse | Normalisasi dilakukan di parser | Lexer adalah satu-satunya tempat yang memproses teks mentah, lebih konsisten jika normalisasi dilakukan di sana sebelum token diteruskan ke parser |
| 2 | Komentar blok `/* */` diproses dengan loop karakter per karakter | Regex atau `str.find("*/")` | Loop karakter per karakter konsisten dengan cara lexer memproses token lain, dan mudah melacak posisi baris/kolom untuk `LexError` |
| 3 | Escape `''` di dalam string ditangani di lexer, nilai token sudah berisi karakter asli | Menyimpan teks mentah dan unescape di parser | Parser tidak perlu tahu detail encoding string SQL, cukup menerima nilai yang sudah bersih dari lexer |
| 4 | Subquery di `SET`/`WHERE` UPDATE selalu ditandai `R`, bukan mengikuti operasi statement luar | Mewarisi operasi `U` dari statement luar | Spesifikasi §5 menyatakan subquery selalu R — tabel yang dibaca di subquery tidak dimodifikasi oleh statement luar |
| 5 | Operator `<>` diprioritaskan sebelum `<` dengan maximal munch | Memecah menjadi dua token `<` dan `>` | Sesuai §2.5, lexer selalu mengambil operator terpanjang yang cocok sehingga `<>` adalah satu token `OP` |
