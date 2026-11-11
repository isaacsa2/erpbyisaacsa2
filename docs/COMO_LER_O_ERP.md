# Como ler o ERP — guia para iniciantes

Este ERP é um projeto de estudos. O comprovante chamado “NF-e” é didático e não é uma nota fiscal emitida pela SEFAZ.

## Entenda como a informação circula

1. O **HTML/Jinja** cria o formulário em `templates/erp/produtos.html`.
2. O **CSS** (`static/erp_style.css`) organiza cores, tamanhos e posições.
3. O navegador envia um formulário por **POST** para o servidor Flask.
4. Uma função em **`erp.py`** recebe os dados, valida e consulta o banco.
5. Uma classe em **`models.py`** representa a tabela, por exemplo `Product`.
6. O **SQLAlchemy** traduz operações Python para o **SQLite**.
7. O Flask devolve a página e o usuário vê o resultado.

| Arquivo | Para que serve |
| --- | --- |
| `app.py` | Prepara o servidor, login, banco, filtros e proteção de formulários |
| `erp.py` | Rotas, validações, cadastros, vendas e financeiro |
| `models.py` | Tabelas, colunas, chaves e relacionamentos |
| `seed_data.py` | Gera dados fictícios para praticar |
| `templates/base.html` | Layout compartilhado pelas telas |
| `templates/erp/*.html` | Formulários, listagens, loops e JavaScript das páginas |
| `static/erp_style.css` | Aparência das telas e temas |

## Estude uma venda no PDV

1. Em `templates/erp/pdv.html`, encontre o formulário de produto e quantidade.
2. O formulário envia **POST /pdv/add**.
3. Em `erp.py`, `pdv_add_item` verifica se o produto existe e se há estoque.
4. A função cria ou atualiza `Sale` e `SaleItem`; o carrinho atual fica identificado na sessão.
5. **O estoque já é descontado ao adicionar o item**; cancelamento ou remoção devolvem as unidades.
6. `pdv_finish` valida cliente e itens, marca a venda como paga, registra a entrada no caixa e limpa a sessão.

Aqui você vê na prática **variáveis, `if`, funções, listas, cálculos e relações entre tabelas**.

## Decifrando código real

- `def nome():` cria uma função Python. A indentação mostra o que pertence a ela.
- `request.form.get("name")` lê o campo `name` enviado pelo formulário.
- `db.Model` declara uma tabela, `db.Column` uma coluna e `primary_key=True` uma chave primária.
- `db.ForeignKey('customer.id')` liga a venda a um cliente.
- `db.session.add(...)` prepara a inserção; `db.session.commit()` confirma no banco.
- Em HTML/Jinja, chaves duplas exibem um valor, `for` repete registros e `if` decide o que mostrar.
- No CSS, `.classe` seleciona elementos e `--nome` declara variável de estilo.

## Exercícios simples para a turma

1. Altere um texto em `templates/erp/produtos.html` e atualize o navegador.
2. Troque uma cor em `static/erp_style.css` e observe a diferença.
3. Encontre o laço `for` em `templates/erp/clientes.html`.
4. Em `erp.py`, ache `products` e diferencie os trechos para GET e POST.
5. Em `models.py`, encontre as tabelas `Sale`, `SaleItem` e `Product`. Qual delas liga venda a produto?
6. Use os scripts de `exemplos/` para estudar DDL, DML e consultas em um banco separado.

**Proteção:** não retire o campo oculto `_csrf_token` dos formulários POST. Valide dados no servidor. Use somente dados fictícios e nunca publique arquivos `.db` nem senhas.

## Observações sobre o código existente

- `models.py` contém duas definições de `update_overdue_status`; Python mantém a última. Isso merece correção em uma PR separada.
- A página de NF-e é apenas uma simulação.
- `seed_data.py` pode criar muitos dados; leia seus parâmetros antes de executar.
- Estes comentários ajudam a entender o comportamento atual, não significam homologação para produção.
