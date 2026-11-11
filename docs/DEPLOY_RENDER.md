# Publicação na Render: ERP público administrável (somente dados fictícios)

Serviço existente: **erpbyisaacsa2**.
Site: https://erpbyisaacsa2.onrender.com
Painel: https://dashboard.render.com/web/srv-dbq4nvbl550s739ikua0

## Credenciais de exercício

- **Usuário:** `admin`
- **Senha:** `admin`
- **Perfil:** `Admin` — permite as ações administrativas já existentes no ERP.

Qualquer visitante pode utilizar a conta e modificar, excluir, vender ou cadastrar registros. O banco é compartilhado durante a execução e os dados não devem ser usados para trabalhos permanentes.

## Reset seguro em cada inicialização

Com `ERP_DEMO_MODE=1` e `ERP_DEMO_ADMIN_MODE=1`, o Flask força o URI `sqlite:///erp_demo_publica.db`. O `DATABASE_URL` fornecido por engano é ignorado **nesse modo**. A função `initialize_storage` executa `db.drop_all()` e `db.create_all()` **apenas nesse SQLite isolado**, depois recria os perfis, a conta admin e os registros de exemplo. A execução normal ou somente leitura não apaga banco existente.

**Render:** use um worker Gunicorn, por exemplo `gunicorn app:app` com `WEB_CONCURRENCY=1`. Cada boot, novo deploy e eventual reinício de worker pode apagar os exercícios. Não há cron de reset nem persistência garantida.

## Variáveis configuradas no serviço existente

| Chave | Valor |
| --- | --- |
| `ERP_DEMO_MODE` | `1` |
| `ERP_DEMO_ADMIN_MODE` | `1` |
| `ERP_DEMO_PASSWORD` | `admin` |
| `ERP_COOKIE_SECURE` | `1` |
| `ERP_SECRET_KEY` | chave aleatória secreta |

O serviço antigo chamado `ERP` na Render, ligado a outro repositório, não deve ser alterado.

## Validando

A CI testa o modo leitura sem poderes de escrita e o modo Admin isolado com cadastro de produto, criação de usuário e reset explícito. O modo de produção local continua com senha de administrador escolhida pelo operador.
