"""Testes do exercício de modelagem pedido nos slides: vendas, N:N e PK/FK."""
import sys
from pathlib import Path
import sqlite3
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'exemplos'))
from modelagem_vendas import criar_banco, CONSULTAS


class TesteModelagemVendas(unittest.TestCase):
    def setUp(self):
        self.con = criar_banco()

    def tearDown(self):
        self.con.close()

    def test_todas_as_seis_tabelas(self):
        nomes = {linha[0] for linha in self.con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(nomes, {'cliente','vendedor','prateleira','produto','venda','item_venda'})

    def test_relacionamento_venda_produto_e_total(self):
        linhas = self.con.execute(CONSULTAS['Vendas com cliente, vendedor e total (JOIN / GROUP BY / SUM)']).fetchall()
        self.assertEqual([l[-1] for l in linhas], [1150, 1450, 2100])
        self.assertEqual([l[0] for l in linhas], [1, 2, 3])

    def test_fk_impede_item_com_produto_inexistente(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO item_venda VALUES (1, 900, 1, 100)")

    def test_check_rejeita_quantidade_zero(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO item_venda VALUES (2, 2, 0, 850)")

    def test_nao_duplica_produto_na_mesma_venda(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO item_venda VALUES (1, 1, 1, 100)")

    def test_produto_em_varias_vendas(self):
        linhas = self.con.execute(CONSULTAS['Produtos presentes em mais de uma venda (N:N / HAVING)']).fetchall()
        self.assertEqual(len(linhas), 3)
        self.assertTrue(all(l[1] == 2 for l in linhas))


if __name__ == '__main__': unittest.main()
