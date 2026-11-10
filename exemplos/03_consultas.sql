-- SELECT, FROM, WHERE, ORDER BY e LIMIT
SELECT nome, preco_centavos, estoque FROM produto ORDER BY preco_centavos DESC;
SELECT id, nome FROM produto WHERE estoque < 20 ORDER BY nome;

-- JOIN e aliases: quem comprou o quê?
SELECT v.id AS venda, c.nome AS cliente, p.nome AS produto, i.quantidade
FROM venda AS v
JOIN cliente AS c ON c.id = v.cliente_id
JOIN item_venda AS i ON i.venda_id = v.id
JOIN produto AS p ON p.id = i.produto_id
ORDER BY v.id, p.nome;

-- GROUP BY, SUM e HAVING: produtos vendidos 3x ou mais
SELECT p.nome, SUM(i.quantidade) AS unidades
FROM item_venda AS i
JOIN produto AS p ON p.id = i.produto_id
GROUP BY p.id, p.nome
HAVING SUM(i.quantidade) >= 3
ORDER BY unidades DESC;
