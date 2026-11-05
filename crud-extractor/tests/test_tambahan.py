"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest

from crud import ast_nodes as ast
from crud.lexer import LexError, TokenType as T, tokenize
from crud.parser import parse_sql


# =========================================================================
# 1. TEST REGRESI (BUG FIXES & TODO)
# =========================================================================


# test parser.py (Fase 3) ---

def test_regresi_parser_insert_into_select():
    """TODO(T1): Parser harus mendukung sintaks INSERT INTO ... SELECT ..."""
    sql = "INSERT INTO arsip (id) SELECT id FROM pesanan WHERE total > 10;"
    script = parse_sql(sql)
    assert script.errors == []
    assert len(script.statements) == 1
    stmt = script.statements[0]
    assert isinstance(stmt, ast.Insert)
    assert stmt.table.name == "arsip"
    assert stmt.columns == ["id"]
    assert stmt.values == []
    assert isinstance(stmt.query, ast.Select)
    assert stmt.query.sources[0].name == "pesanan"


def test_regresi_parser_presedensi_and_over_or():
    """Bug Parser: AND harus memiliki presedensi lebih tinggi daripada OR.
    'a = 1 OR b = 2 AND c = 3' harus diparse sebagai 'a = 1 OR (b = 2 AND c = 3)'.
    """
    sql = "SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3;"
    script = parse_sql(sql)
    assert script.errors == []
    stmt = script.statements[0]
    where = stmt.where
    # Operator tingkat paling atas harus OR, bukan AND
    assert isinstance(where, ast.BinaryOp)
    assert where.op == "OR", f"Diharapkan akar ekspresi OR, tetapi didapat {where.op}"
    # Sisi kanan OR adalah (b = 2 AND c = 3)
    assert isinstance(where.right, ast.BinaryOp)
    assert where.right.op == "AND"


def test_regresi_parser_left_outer_join():
    """Bug Parser: Klausa LEFT JOIN dengan kata opsional OUTER harus didukung."""
    sql = "SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id;"
    script = parse_sql(sql)
    assert script.errors == []
    stmt = script.statements[0]
    assert len(stmt.joins) == 1
    join = stmt.joins[0]
    assert join.kind == "LEFT"
    assert join.source.name == "b"


def test_regresi_parser_panic_mode_recovery():
    """Bug Parser: Error recovery (panic mode) harus membuang token sampai ';' berikutnya,
    sehingga statement valid setelah statement rusak tetap diproses.
    """
    sql = """
    SELECT id nama, FROM pesanan;
    UPDATE produk SET stok = stok - 1 WHERE id = :id;
    """
    script = parse_sql(sql)
    # Harus ada 1 error pada statement pertama
    assert len(script.errors) == 1
    # Statement kedua yang valid harus tetap berhasil masuk AST
    assert len(script.statements) == 1
    assert isinstance(script.statements[0], ast.Update)
    assert script.statements[0].table.name == "produk"
