"""Laboratório de Banco de Dados: usa SQLite em memória. Não altera o ERP."""
from pathlib import Path
import sqlite3

BASE = Path(__file__).resolve().parent


def criar_banco_demo():
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript((BASE / "01_ddl.sql").read_text(encoding="utf-8"))
    con.executescript((BASE / "02_dml.sql").read_text(encoding="utf-8"))
    return con


def executar():
    with criar_banco_demo() as con:
        sql = (BASE / "03_consultas.sql").read_text(encoding="utf-8")
        # Cada SELECT é exibido individualmente, sem SQL fornecido pelo usuário.
        for item in sql.split(";"):
            statement = item.strip()
            if not statement:
                continue
            result = con.execute(statement)
            print("\n" + "-" * 56)
            print(" | ".join(name[0] for name in result.description))
            for row in result.fetchall():
                print(" | ".join(str(value) for value in row))


if __name__ == "__main__":
    executar()
