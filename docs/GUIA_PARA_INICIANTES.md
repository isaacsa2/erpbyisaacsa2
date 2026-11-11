# Guia para iniciantes — como estudar com o ERP

Este material foi feito para quem **ainda não tem prática com programação**. Não precisa entender o ERP inteiro. Comece por um exercício pequeno, leia os comentários nos arquivos, mude um valor e veja a saída.

## 1. O que cada arquivo faz?

| Arquivo | Função |
| --- | --- |
| `static/laboratorio/index.html` | Cria títulos, campos, botões e espaços para as respostas (HTML). |
| `static/laboratorio/styles.css` | Define a aparência: cores, tamanho e posição dos elementos (CSS). |
| `static/laboratorio/app.mjs` | Escuta cliques, lê o que foi digitado e atualiza o texto na tela (JavaScript + DOM). |
| `static/laboratorio/logica.mjs` | Contém as regras de cálculo (JavaScript). |
| `static/laboratorio/testes.mjs` | Verifica se as funções calculam os valores esperados. |
| `exemplos/01_ddl.sql` até `04_modelagem_vendas.sql` | Prática com criação, alteração e consulta de tabelas. |
| `app.py`, `erp.py`, `models.py` | Parte Python do ERP completo; estude depois. |

## 2. Como abrir os exercícios sem instalar o ERP

Abra um terminal na pasta do repositório e execute:

```bash
python -m http.server --bind 127.0.0.1 8000
```

Depois acesse `http://127.0.0.1:8000/static/laboratorio/`. É preciso ter Python instalado apenas para servir os arquivos; o laboratório não exige Flask, login nem banco de dados. Evite abrir o HTML diretamente pelo endereço `file://`, pois o navegador pode bloquear módulos JavaScript.

## 3. Como a calculadora funciona?

1. No `index.html`, procure `<form id="form-soma">`. Ele contém dois campos e um botão.
2. No `app.mjs`, procure `ligar('form-soma','submit', ...)`. Esse trecho é executado ao enviar o formulário.
3. O código lê `.value` dos campos e chama a função `somar()`.
4. Em `logica.mjs`, `somar()` converte os valores em números e devolve a soma.
5. De volta ao `app.mjs`, o texto vai para `<output id="resultado-soma">`. O CSS define a aparência.

Exemplo simplificado (não substitui o arquivo real):

```js
const primeiro = 2;         // const guarda um valor.
const segundo = 3;
const total = primeiro + segundo;
console.log(total);        // Exibe 5.
```

**Dicionário rápido:** `let` é uma variável que pode mudar; `const` não pode ser reatribuída; `if` verifica uma condição; `for` repete instruções; `[]` é uma lista (array); `return` devolve o resultado de uma função; `document.getElementById` localiza um elemento; `addEventListener` reage a um evento.

## 4. Atividades fáceis para alterar o código

| O que testar | Onde mexer | Resultado esperado |
| --- | --- | --- |
| Trocar os dois valores iniciais por 10 e 7 | `index.html`, atributos `value` de `soma-a` e `soma-b` | Soma 17. |
| Trocar o texto do botão Somar | `index.html`, texto dentro do `button` | O botão muda de nome. |
| Mudar a cor do botão | `styles.css`, regra `.btn` | A aparência muda. |
| Adicionar um valor ao array inicial | `app.mjs`, `let valores = [12, 8, 25]` | Soma, média e quantidade se atualizam. |
| Alterar estoque simulado do pão | `app.mjs`, lista `produtos` | O PDV respeita o novo limite. |
| Filtrar produtos de estoque baixo | `exemplos/03_consultas.sql` | Mude o valor de `WHERE estoque < 20`. |

Mude **uma coisa por vez** e atualize a página. Se não funcionar, desfaça a última alteração e leia o erro no Console (`F12`).

## 5. Banco de dados na prática

- **DDL:** `CREATE TABLE` define estrutura e regras.
- **DML:** `INSERT`, `UPDATE` e `DELETE` alteram linhas. Cuidado com `WHERE`!
- **Consultas:** `SELECT` lê dados, `JOIN` conecta tabelas, `GROUP BY` agrupa e `HAVING` filtra grupos.
- **Chaves:** `PRIMARY KEY` identifica uma linha; `REFERENCES` relaciona tabelas.

Execute `python exemplos/executar.py` e `python exemplos/modelagem_vendas.py` para ver dados fictícios. Esses exercícios não alteram o banco do ERP principal.

## 6. Como saber se não quebrou?

```bash
node --test static/laboratorio/testes.mjs
```

Esse comando verifica a lógica JavaScript. Para os testes Python e Flask, veja o `README.md` e instale as dependências. Um teste passando só garante os casos cobertos pelos testes.

**Avisos:** o laboratório é uma simulação local. Não use dados reais, CPF, senha, notas privadas ou dados de clientes. Não publique os PDFs dos professores sem autorização. O código do projeto é distribuído conforme a licença AGPL-3.0.
