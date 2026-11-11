# Render e Modo Aprendiz
O Modo Aprendiz lê funções/classes reais do repositório via AST do Python; HTML/CSS vêm de arquivos autorizados. Não executa código enviado pela turma.

## Render
- Runtime: Python.
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 90`
- Variáveis: `DEMO_PUBLIC=1`, `ERP_COOKIE_SECURE=1`, `ERP_SECRET_KEY` aleatória e mantida em segredo.
- No modo público, cria a conta compartilhada `admin/admin` **somente leitura** e produtos/clientes inventados. Todas as escritas HTTP dessa conta são bloqueadas no servidor.
- **Nunca** use `DEMO_PUBLIC=1` com informações pessoais ou dados empresariais. O papel Admin na tela não representa autorização de escrita.
- O SQLite usa armazenamento efêmero no plano gratuito; os dados podem desaparecer com reinicializações ou novos deploys.
- Para dados persistentes e cadastro individual de alunos, migrar para PostgreSQL e autenticação individual, com senha forte e limites de requisições.
- O comprovante NF-e no ERP é didático, não é documento fiscal autorizado.

## Como usar
Entre com admin/admin na demonstração, clique em Modo Aprendiz, escolha uma aula, compare as explicações com o trecho real e abra o mesmo arquivo no GitHub.
