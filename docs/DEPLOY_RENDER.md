# Publicando o ERP na Render — modo demonstração

A URL real só será conhecida **depois** que você criar o serviço na sua conta Render.

1. Acesse [Render Dashboard](https://dashboard.render.com/) e conecte seu GitHub.
2. Escolha **New → Blueprint**, selecione `isaacsa2/erpbyisaacsa2` e a branch `main`.
3. Confirme a configuração de `render.yaml`: serviço web Python, plano Free, nome `erp-by-isaac-demo`.
4. A Render instala as dependências e inicia o `gunicorn`. O endpoint `/healthz` deve retornar status 200.
5. Quando o deploy ficar **Live**, use a URL `https://...onrender.com` exibida na sua conta e compartilhe com a turma.
6. Login da demo: **admin/admin**. O papel interno é **Gerente**, e todas as rotas de escrita são bloqueadas no servidor, mesmo com requisições manuais.

## O que o modo demo não faz

- Não salva cadastro, estoque ou venda. É **somente visualização**. Explore telas, laboratório SQL e exercícios.
- Não deve conter clientes, credenciais, dados financeiros ou documentos reais.
- Não substitui autenticação individual, proteção contra abuso, auditoria de segurança ou infraestrutura de produção.

## Por que os dados reiniciam?

No plano Free, o SQLite local fica num **sistema de arquivos efêmero**. Reinícios, novos deploys e suspensão apagam alterações. O Flask cria uma base de demonstração com registros fictícios ao iniciar. Para persistência, planeje PostgreSQL e usuários próprios. Os bancos PostgreSQL Free da Render também têm expiração.

## Configuração técnica

- Build: `pip install -r requirements.txt`.
- Start: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 app:app`.
- Health: `GET /healthz`.
- Vars: `ERP_DEMO_MODE=1`, `ERP_COOKIE_SECURE=1` e `ERP_SECRET_KEY` (gerada automaticamente).

Para executar normalmente na máquina, mantenha `ERP_DEMO_MODE=0`, rode `flask --app app init-admin` e escolha uma senha própria forte.
