-- DDL: Data Definition Language — criar tabelas e restrições
PRAGMA foreign_keys = ON;
CREATE TABLE cliente (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT UNIQUE
);
CREATE TABLE produto (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    preco_centavos INTEGER NOT NULL CHECK (preco_centavos >= 0),
    estoque INTEGER NOT NULL CHECK (estoque >= 0)
);
CREATE TABLE venda (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    data TEXT NOT NULL
);
CREATE TABLE item_venda (
    id INTEGER PRIMARY KEY,
    venda_id INTEGER NOT NULL REFERENCES venda(id),
    produto_id INTEGER NOT NULL REFERENCES produto(id),
    quantidade INTEGER NOT NULL CHECK (quantidade > 0)
);
