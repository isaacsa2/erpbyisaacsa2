-- GUIA: DML modifica registros depois da criação das tabelas.
-- INSERT adiciona linhas, UPDATE altera linhas, DELETE remove linhas.
-- WHERE limita quais registros serão alterados ou removidos.
-- Atenção: sem WHERE, UPDATE e DELETE podem afetar TODAS as linhas.
-- Os dados deste exemplo são fictícios.
INSERT INTO cliente (id, nome, email) VALUES
 (1, 'Ana (fictícia)', 'ana@exemplo.invalid'),
 (2, 'Bruno (fictício)', 'bruno@exemplo.invalid');

INSERT INTO produto (id, nome, preco_centavos, estoque) VALUES
 (1, 'Sequilho', 600, 30),
 (2, 'Bolo', 2500, 12),
 (3, 'Suco', 850, 20),
 (99, 'Produto temporário', 100, 1);

-- WHERE impede alterações em todos os registros.
UPDATE produto SET estoque = 25 WHERE id = 1;
DELETE FROM produto WHERE id = 99;

INSERT INTO venda (id, cliente_id, data) VALUES
 (1, 1, '2026-11-10'),
 (2, 2, '2026-11-10');
INSERT INTO item_venda (id, venda_id, produto_id, quantidade) VALUES
 (1, 1, 1, 3), (2, 1, 2, 1), (3, 2, 1, 2), (4, 2, 3, 2);
