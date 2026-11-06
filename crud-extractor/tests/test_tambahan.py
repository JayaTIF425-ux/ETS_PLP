"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""

# =========================================================================
# 1. TEST REGRESI (BUG FIXES & TODO)
# =========================================================================

import pytest

from crud import ast_nodes as ast
from crud.analyzer import analyze_statement, column_usage
from crud.lexer import LexError, TokenType as T, tokenize
from crud.parser import parse_sql
from crud.resolver import Resolver


def types(src):
    return [t.type for t in tokenize(src)]


def values(src):
    return [t.value for t in tokenize(src) if t.type != T.EOF]


def crud(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    return analyze_statement(script.statements[0])


def resolve(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    diagnostics = Resolver().resolve_script(script)
    return script, diagnostics


def columns(node):
    return [n for n in ast.iter_nodes(node) if isinstance(n, ast.ColumnRef)]


# =============================================================================
# 1. TEST REGRESI — Satu test per bug (Total: 10 Bug)
# =============================================================================

# --- Bug 1: Keyword tidak dinormalisasi ke huruf besar (Lexer) ---
def test_regresi_keyword_huruf_campur():
    toks = tokenize("SeLeCt iD fRoM t")
    assert toks[0].type == T.KEYWORD and toks[0].value == "SELECT"
    assert toks[2].type == T.KEYWORD and toks[2].value == "FROM"


# --- Bug 2: Operator <> tidak dikenali sebagai satu token (Lexer) ---
def test_regresi_operator_tidak_sama():
    assert values("a <> b") == ["a", "<>", "b"]


# --- Bug 3: Escape '' dalam string tidak ditangani (Lexer) ---
def test_regresi_string_kutip_ganda():
    toks = tokenize("'O''Brien'")
    assert toks[0].type == T.STRING and toks[0].value == "O'Brien"


# --- Bug 4: Presedensi operator logika AND dan OR disatukan di satu level (Parser) ---
def test_regresi_parser_presedensi_and_over_or():
    sql = "SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3;"
    script = parse_sql(sql)
    assert script.errors == []
    stmt = script.statements[0]
    where = stmt.where
    assert isinstance(where, ast.BinaryOp)
    assert where.op == "OR", f"Diharapkan akar ekspresi OR, tetapi didapat {where.op}"
    assert isinstance(where.right, ast.BinaryOp)
    assert where.right.op == "AND"


# --- Bug 5: Klausa LEFT JOIN menolak kata kunci opsional OUTER (Parser) ---
def test_regresi_parser_left_outer_join():
    sql = "SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id;"
    script = parse_sql(sql)
    assert script.errors == []
    stmt = script.statements[0]
    assert len(stmt.joins) == 1
    join = stmt.joins[0]
    assert join.kind == "LEFT"
    assert join.source.name == "b"


# --- Bug 6: Panic mode recovery membuang seluruh sisa token hingga EOF (Parser) ---
def test_regresi_parser_panic_mode_recovery():
    sql = """
    SELECT id nama, FROM pesanan;
    UPDATE produk SET stok = stok - 1 WHERE id = :id;
    """
    script = parse_sql(sql)
    assert len(script.errors) == 1
    assert len(script.statements) == 1
    assert isinstance(script.statements[0], ast.Update)
    assert script.statements[0].table.name == "produk"


# --- Bug 7: Kebocoran scope (Scope Leak) pada statement DELETE (Resolver) ---
def test_regresi_resolver_scope_leak_delete():
    sql = """
    DELETE FROM sesi s WHERE s.id = 1;
    SELECT s.id FROM pengguna u WHERE u.aktif = 1;
    """
    script = parse_sql(sql)
    assert script.errors == []
    diags = Resolver().resolve_script(script)
    assert any(d.level == "error" and "'s'" in d.message for d in diags)


# --- Bug 8: Urutan pencarian scope terbalik pada _lookup() (Resolver) ---
def test_regresi_resolver_shadowing_dalam_ke_luar():
    sql = "SELECT x.id FROM pelanggan x WHERE x.id IN (SELECT x.pelanggan_id FROM pesanan x WHERE x.total > 500);"
    script, diags = resolve(sql)
    assert diags == []
    inner_cols = [c for c in columns(script.statements[0].where) if c.name == "pelanggan_id"]
    assert len(inner_cols) == 1
    assert inner_cols[0].resolved == "pesanan"


# --- Bug 9: Subquery di SET/WHERE UPDATE ditandai U, seharusnya R (Analyzer) ---
def test_regresi_update_subquery_where():
    result = crud("UPDATE pelanggan SET poin = 0 WHERE id IN (SELECT id FROM blacklist)")
    assert result == {"pelanggan": {"U"}, "blacklist": {"R"}}


# --- Bug 10: Traversal column_usage untuk baris data INSERT VALUES (Analyzer) ---
def test_regresi_column_usage_insert_values():
    script = parse_sql("INSERT INTO log (id, nama) VALUES (1, 'test')")
    assert script.errors == []
    result = column_usage(script.statements[0])
    assert ("log", "id", "C") in result
    assert ("log", "nama", "C") in result


# =============================================================================
# 2. TEST KASUS TEPI (Total: 5 Kasus Tepi)
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
