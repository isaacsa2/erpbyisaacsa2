# ERP by Isaac — projeto didático para a faculdade

Projeto de estudo de um **ERP (Enterprise Resource Planning)** para uma padaria fictícia, com interface em português do Brasil. Desenvolvido em **Python, Flask, SQLAlchemy, SQLite, HTML, CSS e Bootstrap**.

> **Uso educacional e local.** Este projeto é uma base para aprender e experimentar, **não é um sistema de produção**. Não publique na Internet sem realizar uma auditoria de segurança, privacidade, regras fiscais e testes adicionais. A tela chamada "NF-e" é uma simulação de comprovante: **não emite nota fiscal autorizada pela SEFAZ**.

## Primeiro contato: um guia para quem está aprendendo

**Não precisa saber Python para começar.** Leia o [Guia para iniciantes](docs/GUIA_PARA_INICIANTES.md) e experimente o laboratório de HTML, CSS e JavaScript no navegador.

O código do laboratório tem comentários em português explicando as partes principais; os exercícios SQL também trazem notas sobre DDL, DML, filtros, tabelas e relacionamentos. Os comentários não mudam a execução: servem para entender como cada passo funciona.

## Entenda o código do ERP principal

Além do laboratório de exercícios, o ERP principal contém comentários para iniciantes em `app.py`, `erp.py`, `models.py`, `seed_data.py`, nas telas e no CSS. Veja o **[guia para ler o ERP](docs/COMO_LER_O_ERP.md)** para acompanhar uma venda do formulário HTML até o banco de dados.

## Modo Aprendiz: código REAL na própria tela

Após o login, clique no botão **Modo Aprendiz** para ver as funções Python, templates HTML/Jinja, classes SQLAlchemy e CSS da versão em execução. Cada trecho aponta para seu arquivo e linha no GitHub; não são snippets inventados. Veja [o guia](docs/MODO_APRENDIZ.md).

## Demonstração na Render (somente leitura)

O arquivo [render.yaml](render.yaml) configura uma demo do ERP na Render, usando dados simulados. Para a turma visualizar: **usuário `admin` / senha `admin`**, sem acesso à escrita (não é uma conta administrativa real). Veja [como publicar na Render](docs/DEPLOY_RENDER.md). A instância Free perde o banco SQLite quando reinicia: não use para armazenar trabalhos.

## Funcionalidades para estudar

- Cadastro de **clientes, fornecedores e produtos**, incluindo estoque;
- **PDV** (ponto de venda), carrinho, vendas e histórico;
- Contas **a pagar e a receber**, tesouraria e custos fixos;
- **Dashboard** com indicadores e relatórios;
- **Laboratório SQL** com `SELECT`, `WHERE`, `JOIN`, `SUM` e `GROUP BY`;
- Controle de acesso por **Administrador, Gerente e Caixa**;
- Banco relacional com **SQLite e SQLAlchemy**;
- Dados fictícios opcionais para praticar consultas.

## Comece pelo laboratório sem instalar nada

Para praticar os comandos da aula em **banco isolado** (somente Python 3.11+):

```bash
python exemplos/executar.py
python exemplos/algoritmos.py
python -m unittest discover -s tests -v
```

Os exemplos estão explicados em [`docs/EXEMPLOS.md`](docs/EXEMPLOS.md) e [`docs/KANBAN.md`](docs/KANBAN.md). Há também uma aba **Laboratório SQL** dentro do ERP, que mostra o resultado de consultas de leitura.

## Novidade: Laboratório das aulas (23 PDFs mapeados)

O pacote de aulas da faculdade foi revisado por assunto: 16 PDFs de Algoritmos/Web/JavaScript e 7 de Banco de Dados/Modelagem. Os exemplos originais foram **adaptados para exercícios novos e testáveis**, sem redistribuir os PDFs.

- **Laboratório interativo de JavaScript:** nove exercícios (soma, idade, triângulos, IMC didático, tabuada, parcelamento, arrays, PDV e notas com `localStorage`). Abra `http://127.0.0.1:5000/static/laboratorio/index.html` depois de iniciar o Flask, ou use `python -m http.server 8000` para abrir `http://127.0.0.1:8000/static/laboratorio/`, sem instalar o ERP.
- **Modelagem de vendas:** exercício inspirado no sistema com clientes, vendedores, prateleiras, produtos e vendas, com chaves e integridade referencial em SQLite isolado: `python exemplos/modelagem_vendas.py`.
- **Mapa dos PDFs, atividades e DER:** [docs/MAPA_DAS_AULAS.md](docs/MAPA_DAS_AULAS.md).
- **Testes do JavaScript:** `node --test static/laboratorio/testes.mjs` (Node.js 20+).

Os exercícios didáticos não acessam o banco principal e o PDV web não gera vendas reais.

## Como executar (Windows, Linux e macOS)

É necessário **Python 3.11 ou superior** e Git (para clonar). No terminal, execute:

```bash
git clone https://github.com/isaacsa2/erpbyisaacsa2.git
cd erpbyisaacsa2
python -m venv .venv
```

Ative o ambiente virtual: Windows PowerShell: `.venv\Scripts\Activate.ps1`; Linux/macOS: `source .venv/bin/activate`. Em seguida:

```bash
python -m pip install -r requirements.txt
flask --app app init-admin
python seed_data.py
python app.py
```

No comando `init-admin`, escolha uma senha forte (não há senha-padrão). O `seed_data.py` é **opcional** e cria clientes, produtos e vendas fictícios. Se preferir banco vazio, pule essa etapa.

Acesse **http://127.0.0.1:5000/login** no navegador. O arquivo SQLite é criado em `instance/` e não deve entrar no Git. Para criar outras contas:

```bash
flask --app app create-user
```

**Dica:** em algumas distribuições use `python3` no lugar de `python`; no Windows, `py` também costuma funcionar. Se o PowerShell bloquear a ativação, é possível usar diretamente `.venv\Scripts\python.exe` nos comandos.

## Estrutura do projeto

| Arquivo / pasta | Papel no sistema |
| --- | --- |
| `app.py` | Configuração do Flask, login, inicialização e proteção básica de formulários |
| `erp.py` | Rotas HTTP e regras de aplicação (vendas, clientes, estoque, financeiro) |
| `models.py` | Entidades, tabelas, relacionamentos e operações financeiras |
| `seed_data.py` | Geração opcional de dados fictícios para exercício |
| `templates/` | Páginas HTML renderizadas pelo Jinja2 |
| `static/` | CSS e recursos visuais |
| `docs/EXERCICIOS.md` | Roteiro de exercícios práticos para a turma |
| `exemplos/` | Scripts SQLite e Algoritmos executáveis sem dependências |
| `tests/` | Testes SQLite e integração Flask no GitHub Actions |

## Testes automáticos

No GitHub, o workflow **Testes ERP educacional** instala as dependências e executa exemplos e testes de integração do Flask. Para executar na sua máquina após instalar os requisitos:

```bash
python -m unittest discover -s tests -v
```

## Segurança e privacidade

O arquivo original usado na preparação desta versão continha bancos de dados locais e valores fixos de autenticação. **Esses arquivos e credenciais não foram incluídos**. Esta versão usa configuração por variável de ambiente, inicialização de administrador via terminal, verificação de CSRF em formulários e execução somente em `127.0.0.1` por padrão. Isso **não significa que ela esteja pronta para a Internet**.

Antes de usar com dados reais, consulte [`docs/SEGURANCA.md`](docs/SEGURANCA.md). Não suba arquivos `.db`, `.env`, senhas, dados de clientes ou documentos de terceiros.

## Como ajudar

Faça um fork, crie uma branch, implemente um exercício e envie um **Pull Request**. Ao relatar bugs, informe passos para reproduzir, comportamento esperado e versão do Python, **sem expor dados pessoais**.

## Licença

Distribuído sob **GNU Affero General Public License v3.0 (AGPL-3.0)**, conforme o arquivo [`LICENSE`](LICENSE) deste repositório. Preserve os avisos de licença, os direitos dos autores e disponibilize o código-fonte quando exigido pela AGPL.

Projeto educacional mantido por [isaacsa2](https://github.com/isaacsa2). Não é afiliado a instituições de ensino ou serviços fiscais.
