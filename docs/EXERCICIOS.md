# Exercícios: aprenda construindo um ERP

Este projeto foi disponibilizado para estudar **Python, programação web, SQL, modelagem e engenharia de software**. Use sempre dados fictícios.

## 1. Modelagem de dados (DER)

Abra `models.py`, identifique `Customer`, `Product`, `Sale` e `SaleItem` e desenhe o DER. Indique **chaves primárias, estrangeiras e cardinalidades**. Pergunta: uma venda possui quantos itens? Um item pode pertencer a duas vendas?

## 2. SQL / DDL

Inspecione o banco local, sem versioná-lo. Em um banco de testes separado, escreva um `CREATE TABLE` para `product`, respeitando `id`, `name`, `price` e `stock`. Compare sua tabela com a criada pelo SQLAlchemy.

## 3. SQL / DML

Faça um `INSERT` de produto de teste, um `SELECT` ordenando por preço, um `UPDATE` do estoque com `WHERE id = ...` e um `DELETE` **somente** do produto de teste. Explique por que esquecer o `WHERE` pode causar perda de dados.

## 4. Consultas com JOIN

Escreva uma consulta para exibir o número da venda, o produto e a quantidade vendida, fazendo `JOIN` de `sale`, `sale_item` e `product`. Depois agregue vendas por produto com `SUM` e `GROUP BY`.

## 5. API e HTTP

Localize as rotas em `erp.py` e compare `GET` e `POST`. Acrescente uma página que apenas **liste** os produtos com estoque abaixo de 10 unidades. Não altere dados durante uma requisição `GET`.

## 6. Regras de negócio

No PDV, teste quantidade zero, estoque insuficiente e cancelamento de venda. Descreva o que deveria acontecer com o estoque em cada operação. Implemente testes automatizados antes de alterar o código.

## 7. Segurança

Explique autenticação versus autorização, o papel do hash de senha, o risco do cadastro público de administradores, a função de um token CSRF e por que o banco `.db` não deve ser enviado ao Git.

## 8. Trabalho em equipe

Faça um fork e crie uma branch `feat/nome-da-melhoria`. Abra um Pull Request com problema, solução, passos de teste e capturas **sem informações pessoais**.

**Desafio extra:** separar a camada de serviços da camada HTTP, substituir valores monetários `float` por `Decimal` e criar migrações de esquema com Flask-Migrate. Registre testes e possíveis regressões.

## 9. Exemplos que já funcionam

Veja [`EXEMPLOS.md`](EXEMPLOS.md) com scripts completos de DDL, DML, consultas com JOIN e GROUP BY, algoritmo de caixa, testes automatizados e roteiro de Gestão Ágil. No ERP, use o item **Laboratório SQL** do menu para ver consultas executadas de verdade.
