"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""

import pytest

from crud.lexer import LexError, TokenType as T, tokenize
from crud.analyzer import analyze_statement
from crud.parser import parse_sql


def types(src):
    return [t.type for t in tokenize(src)]


def values(src):
    return [t.value for t in tokenize(src) if t.type != T.EOF]


def crud(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    return analyze_statement(script.statements[0])


# =============================================================================
# TEST REGRESI — satu per bug
# =============================================================================

# Bug 1: keyword tidak dinormalisasi ke huruf besar
def test_regresi_keyword_huruf_campur():
    toks = tokenize("SeLeCt iD fRoM t")
    assert toks[0].type == T.KEYWORD and toks[0].value == "SELECT"
    assert toks[2].type == T.KEYWORD and toks[2].value == "FROM"


# Bug 2: komentar blok /* */ selalu throw error
def test_regresi_komentar_blok_valid():
    toks = tokenize("/* komentar */ SELECT id FROM t")
    assert toks[0].type == T.KEYWORD and toks[0].value == "SELECT"


# Bug 3: operator <> tidak dikenali
def test_regresi_operator_tidak_sama():
    assert values("a <> b") == ["a", "<>", "b"]


# Bug 4: escape '' dalam string tidak ditangani
def test_regresi_string_kutip_ganda():
    toks = tokenize("'O''Brien'")
    assert toks[0].type == T.STRING and toks[0].value == "O'Brien"


# Bug 5: subquery di SET/WHERE UPDATE ditandai U, seharusnya R
def test_regresi_update_subquery_where():
    result = crud("UPDATE pelanggan SET poin = 0 WHERE id IN (SELECT id FROM blacklist)")
    assert result == {"pelanggan": {"U"}, "blacklist": {"R"}}


# Bug 6: column_usage INSERT reads(stmt.values) pada list of list
def test_regresi_column_usage_insert_values():
    script = parse_sql("INSERT INTO log (id, nama) VALUES (1, 'test')")
    assert script.errors == []
    from crud.analyzer import column_usage
    result = column_usage(script.statements[0])
    assert ("log", "id", "C") in result
    assert ("log", "nama", "C") in result


# =============================================================================
# TEST KASUS TEPI
# =============================================================================

# Kasus tepi 1: komentar blok tidak ditutup harus LexError
# Berisiko karena loop bisa jalan terus tanpa error kalau kondisi tidak ditutup dengan benar
def test_tepi_komentar_blok_tidak_ditutup():
    with pytest.raises(LexError) as info:
        tokenize("/* komentar tidak ditutup")
    assert info.value.line == 1


# Kasus tepi 2: komentar blok berisi tanda * tunggal
# Berisiko karena * bisa disalahartikan sebagai penutup /* */
def test_tepi_komentar_blok_berisi_bintang():
    toks = tokenize("/* 2 * 2 = 4 */ SELECT")
    assert toks[0].value == "SELECT"


# Kasus tepi 3: string kosong ''
# Berisiko karena dua kutip berturut-turut bisa disalahartikan sebagai escape ''
def test_tepi_string_kosong():
    toks = tokenize("''")
    assert toks[0].type == T.STRING and toks[0].value == ""


# Kasus tepi 4: UPDATE dengan subquery di SET dan WHERE sekaligus
# Berisiko karena dua tempat berbeda yang sama-sama harus menghasilkan R
def test_tepi_update_subquery_set_dan_where():
    result = crud(
        "UPDATE pesanan SET harga = (SELECT harga FROM katalog WHERE id = 1) "
        "WHERE id IN (SELECT id FROM blacklist)"
    )
    assert result == {"pesanan": {"U"}, "katalog": {"R"}, "blacklist": {"R"}}


# Kasus tepi 5: keyword yang diawali nama keyword, misal 'selection' atau 'fromage'
# Berisiko karena lexer bisa salah mengenali sebagai keyword SELECT/FROM
def test_tepi_ident_diawali_keyword():
    toks = tokenize("SELECT selection, fromage FROM t")
    assert toks[1].type == T.IDENT and toks[1].value == "selection"
    assert toks[3].type == T.IDENT and toks[3].value == "fromage"