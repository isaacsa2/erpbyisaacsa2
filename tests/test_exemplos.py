"""Testes executáveis sem Flask, usando somente a biblioteca padrão do Python."""
import sys
from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from exemplos.executar import criar_banco_demo
from exemplos.algoritmos import calcular_total, classificar_estoque


class TestAulasSQL(unittest.TestCase):
    def setUp(self):
        self.con = criar_banco_demo()
    def tearDown(self):
        self.con.close()
    def test_ddl_e_dml(self):
        rows = self.con.execute("SELECT nome, estoque FROM produto ORDER BY id").fetchall()
        self.assertEqual(rows, [("Sequilho",25),("Bolo",12),("Suco",20)])
    def test_join(self):
        n = self.con.execute("SELECT COUNT(*) FROM item_venda JOIN venda ON venda.id=item_venda.venda_id").fetchone()[0]
        self.assertEqual(n,4)
    def test_soma_agrupada(self):
        rows = self.con.execute("SELECT produto_id, SUM(quantidade) FROM item_venda GROUP BY produto_id").fetchall()
        self.assertEqual(rows, [(1,5),(2,1),(3,2)])
    def test_foreign_key(self):
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO item_venda(venda_id,produto_id,quantidade) VALUES (200,1,1)")
    def test_check(self):
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("UPDATE produto SET estoque=-1 WHERE id=1")

class TestAlgoritmos(unittest.TestCase):
    def test_total(self):
        self.assertEqual(str(calcular_total([("6.00",3),("8.50",2)])),"35.00")
    def test_validacao(self):
        with self.assertRaises(ValueError): calcular_total([("10",0)])
    def test_estoque(self):
        self.assertEqual(classificar_estoque(5),"Reposição necessária")
        self.assertEqual(classificar_estoque(10),"Estoque suficiente")

if __name__=="__main__": unittest.main()
