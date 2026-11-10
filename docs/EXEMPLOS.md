# Laboratórios executáveis — Banco de Dados e Algoritmos

## 1. Pré-requisitos

Os exemplos desta pasta usam **somente Python 3.11+ e SQLite integrado**. Não precisam de Flask e não conectam ao banco real do ERP.

```bash
python exemplos/executar.py
python exemplos/algoritmos.py
python -m unittest discover -s tests -v
```

## 2. DDL e DML

- [`01_ddl.sql`](../exemplos/01_ddl.sql): `CREATE TABLE`, `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE` e `CHECK`.
- [`02_dml.sql`](../exemplos/02_dml.sql): `INSERT`, `UPDATE`, `DELETE` e `WHERE`.
- [`03_consultas.sql`](../exemplos/03_consultas.sql): `SELECT`, `FROM`, `WHERE`, `ORDER BY`, `JOIN`, `GROUP BY`, `SUM`, `HAVING`.
- [`executar.py`](../exemplos/executar.py): executa os SQLs em **banco na memória** e mostra o resultado.

**Exemplo de resultado esperado:** `Sequilho` termina com estoque 25, e a soma vendida de Sequilho é 5 unidades. O cliente de identificador 1 efetuou a venda 1.

Os preços do laboratório são inteiros em **centavos**. No ERP legado os preços ainda estão em `Float`; a troca integral para `Numeric/Decimal` exigirá migração e revisão de todas as operações.

## 3. Algoritmos

[`algoritmos.py`](../exemplos/algoritmos.py) demonstra variáveis, funções, `for`, `if`, validação de parâmetros e cálculo de total usando `Decimal`. O carrinho com 3 itens de R$ 6,00 e 2 de R$ 8,50 totaliza **R$ 35,00**.

## 4. Consultas no próprio ERP

Depois de executar `python seed_data.py` e fazer login como administrador/gerente, abra **Laboratório SQL** no menu. Essa página mostra quatro consultas SELECT predefinidas com os resultados **do banco local atual**. O laboratório na pasta `exemplos/` é isolado e permite DML sem danificar o ERP.

## 5. Práticas extras sugeridas

1. Faça uma tabela `categoria` e crie chave estrangeira em `produto` (DDL).
2. Implemente cadastro com validação de email e teste de unicidade (DML e restrições).
3. Crie consulta para o total financeiro de cada cliente (`JOIN`, `SUM`, `GROUP BY`).
4. Crie um fluxo de testes para venda cancelada, estoque insuficiente e perfil sem autorização.
5. Em Gestão Ágil, crie issues e organize as tarefas no quadro de [`KANBAN.md`](KANBAN.md).

Nunca execute `DROP TABLE`, `UPDATE` ou `DELETE` sem condições em banco com informações importantes. Faça testes em banco isolado.
