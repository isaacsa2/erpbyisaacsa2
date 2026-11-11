-- GUIA: SELECT consulta dados; FROM indica a tabela;
-- WHERE filtra registros; ORDER BY define a ordem; DESC = decrescente.
-- Execute este arquivo depois do DDL e do DML nos dados fictícios.
SELECT nome, preco_centavos, estoque FROM produto ORDER BY preco_centavos DESC;
SELECT id, nome FROM produto WHERE estoque < 20 ORDER BY nome;

-- JOIN une dados de tabelas relacionadas; AS cria um apelido curto.
-- Aqui vamos de venda para cliente e de item_venda para produto.
SELECT v.id AS venda, c.nome AS cliente, p.nome AS produto, i.quantidade
FROM venda AS v
JOIN cliente AS c ON c.id = v.cliente_id
JOIN item_venda AS i ON i.venda_id = v.id
JOIN produto AS p ON p.id = i.produto_id
ORDER BY v.id, p.nome;

-- GROUP BY agrupa produtos; SUM soma unidades vendidas.
-- HAVING filtra grupos calculados (diferente de WHERE, que filtra linhas).
SELECT p.nome, SUM(i.quantidade) AS unidades
FROM item_venda AS i
JOIN produto AS p ON p.id = i.produto_id
GROUP BY p.id, p.nome
HAVING SUM(i.quantidade) >= 3
ORDER BY unidades DESC;
