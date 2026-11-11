-- GUIA: modelo relacional de sistema de vendas fictício.
-- Entidade vira tabela; PRIMARY KEY identifica cada linha;
-- REFERENCES indica a chave da tabela relacionada.
-- Venda N:N Produto precisa da tabela intermediária item_venda.
-- Executar somente em uma base nova/em memória, nunca no ERP real.
-- Exercício independente inspirado na atividade prática de sistema de vendas.
-- Fonte didática: Relational_Data_Foundations.pdf, atividade de modelagem (página 18).
-- SQLite: execute em uma base NOVA / em memória; nenhuma tabela do ERP é alterada.
PRAGMA foreign_keys = ON;

-- MODELO LÓGICO:
-- cliente 1:N venda | vendedor 1:N venda | prateleira 1:N produto
-- venda N:N produto, resolvida por item_venda (quantidade e preço histórico).
CREATE TABLE cliente (
  id INTEGER PRIMARY KEY,
  nome TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE
);
CREATE TABLE vendedor (
  id INTEGER PRIMARY KEY,
  nome TEXT NOT NULL
);
CREATE TABLE prateleira (
  id INTEGER PRIMARY KEY,
  codigo TEXT NOT NULL UNIQUE
);
CREATE TABLE produto (
  id INTEGER PRIMARY KEY,
  nome TEXT NOT NULL,
  preco_centavos INTEGER NOT NULL CHECK (preco_centavos >= 0),
  prateleira_id INTEGER NOT NULL REFERENCES prateleira(id)
);
CREATE TABLE venda (
  id INTEGER PRIMARY KEY,
  data_venda TEXT NOT NULL,
  cliente_id INTEGER NOT NULL REFERENCES cliente(id),
  vendedor_id INTEGER NOT NULL REFERENCES vendedor(id)
);
CREATE TABLE item_venda (
  venda_id INTEGER NOT NULL REFERENCES venda(id),
  produto_id INTEGER NOT NULL REFERENCES produto(id),
  quantidade INTEGER NOT NULL CHECK (quantidade > 0),
  preco_unitario_centavos INTEGER NOT NULL CHECK (preco_unitario_centavos >= 0),
  PRIMARY KEY (venda_id, produto_id)
);

INSERT INTO cliente VALUES
  (1, 'Ana - fictícia', 'ana@exemplo.invalid'),
  (2, 'Beto - fictício', 'beto@exemplo.invalid');
INSERT INTO vendedor VALUES (1, 'Carla - fictícia'), (2, 'Diego - fictício');
INSERT INTO prateleira VALUES (1, 'A-01'), (2, 'B-02');
INSERT INTO produto VALUES
  (1, 'Pão', 100, 1),
  (2, 'Suco', 850, 2),
  (3, 'Bolo', 1250, 1);
INSERT INTO venda VALUES
  (1, '2026-11-10', 1, 1),
  (2, '2026-11-10', 2, 2),
  (3, '2026-11-11', 1, 2);
INSERT INTO item_venda VALUES
  (1, 1, 3, 100),
  (1, 2, 1, 850),
  (2, 1, 2, 100),
  (2, 3, 1, 1250),
  (3, 2, 1, 850),
  (3, 3, 1, 1250);
