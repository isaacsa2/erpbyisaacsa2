# ERP by Isaac na Render — demonstração pública editável

Serviço existente (não crie outro): **https://erpbyisaacsa2.onrender.com**  
Painel: https://dashboard.render.com/web/srv-dbq4nvbl550s739ikua0  
Código: https://github.com/isaacsa2/erpbyisaacsa2 (`main`).

## Acesso para a turma

- Usuário: `admin`
- Senha: `admin`
- Perfil: **Admin** com permissão de criar, editar, remover, vender e testar as rotas administrativas.
- **NUNCA cadastre dados reais:** qualquer pessoa com essas credenciais pode ver, modificar ou excluir tudo.

## Reset automático do ambiente fictício

Quando `ERP_DEMO_MODE=1`:
1. O Flask **ignora `DATABASE_URL`**, mesmo que esteja definida no serviço.
2. Usa exclusivamente o arquivo `instance/erp_demo_faculdade.sqlite3`.
3. Na inicialização do processo, executa `db.drop_all()`, `db.create_all()` e `initialize_demo()`.
4. Os registros anteriores (inclusive usuários criados pela turma) desaparecem, e o `admin/admin` é recriado com papel **Admin**.
5. A Render Free mantém um sistema de arquivos efêmero, mas o reset acima é **explícito**: acontece no boot mesmo se o arquivo SQLite anterior ainda existir.

Use **somente um worker Gunicorn** no serviço (`WEB_CONCURRENCY=1`) para evitar dois processos reinicializando a mesma base ao mesmo tempo.

## Configuração do serviço já criado

- Repositório: `isaacsa2/erpbyisaacsa2`, branch `main`.
- Build: `pip install -r requirements.txt`.
- Start: `gunicorn app:app` com `WEB_CONCURRENCY=1`.
- Ambiente: `ERP_DEMO_MODE=1`, `ERP_DEMO_PASSWORD=admin`, `ERP_COOKIE_SECURE=1` e uma `ERP_SECRET_KEY` aleatória.
- Health: `GET /healthz`.

O modo demo é **desativado por padrão** em instalações locais. Fora dele, o ERP usa a variável `DATABASE_URL` normalmente e **não apaga os dados ao iniciar**.

## Limites e responsabilidade

Este é um projeto didático, não um produto comercial ou fiscal. O login compartilhado significa que os colegas podem interferir nos exercícios uns dos outros. Se houver uso malicioso, reinicie o serviço para limpar os dados. Nunca vincule dados de produção, serviços externos com credenciais reais ou informações pessoais. O Modo Aprendiz mostra arquivos de código da versão que está sendo executada.
