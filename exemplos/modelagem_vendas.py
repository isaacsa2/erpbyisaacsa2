"""Executa o exercício da aula de modelo relacional inteiramente em SQLite RAM."""
from pathlib import Path
import sqlite3

ARQUIVO = Path(__file__).with_name("04_modelagem_vendas.sql")

CONSULTAS = {
    "Catálogo e prateleira (JOIN / relacionamento 1:N)": """
        SELECT p.nome, pr.codigo, p.preco_centavos
        FROM produto p JOIN prateleira pr ON pr.id = p.prateleira_id
        ORDER BY p.id;
    """,
    "Vendas com cliente, vendedor e total (JOIN / GROUP BY / SUM)": """
        SELECT v.id, c.nome AS cliente, ve.nome AS vendedor,
               SUM(i.quantidade * i.preco_unitario_centavos) AS total_centavos
        FROM venda v
        JOIN cliente c ON c.id = v.cliente_id
        JOIN vendedor ve ON ve.id = v.vendedor_id
        JOIN item_venda i ON i.venda_id = v.id
        GROUP BY v.id, c.nome, ve.nome
        ORDER BY v.id;
    """,
    "Produtos presentes em mais de uma venda (N:N / HAVING)": """
        SELECT p.nome, COUNT(DISTINCT i.venda_id) AS numero_de_vendas
        FROM produto p JOIN item_venda i ON i.produto_id = p.id
        GROUP BY p.id, p.nome
        HAVING COUNT(DISTINCT i.venda_id) > 1
        ORDER BY p.nome;
    """,
}


def criar_banco():
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(ARQUIVO.read_text(encoding="utf-8"))
    return con


def executar():
    with criar_banco() as con:
        for titulo, sql in CONSULTAS.items():
            cursor = con.execute(sql)
            print(f"\n{titulo}\n{'-' * len(titulo)}")
            print(" | ".join(c[0] for c in cursor.description))
            for linha in cursor.fetchall():
                print(" | ".join(str(v) for v in linha))


if __name__ == "__main__":
    executar()
