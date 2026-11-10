# Segurança — restrições da versão acadêmica

## O que foi ajustado na publicação

- Não incluir arquivos SQLite preenchidos, `.env`, backups nem usuários anteriores;
- Não incluir senhas iniciais nem chave de sessão definida diretamente no código;
- Exigir administrador autenticado para a API de cadastro;
- Criar usuários pelo terminal com senha escolhida no momento;
- Proteger formulários POST com token CSRF e transformar ações de alteração em POST;
- Desativar exposição da aplicação na rede (`127.0.0.1` por padrão).

## O que ainda precisa melhorar antes de produção

- Revisão de autorização em **todos** os objetos e ações, com testes de acesso cruzado;
- Testes automatizados de fluxo (cadastro, estoque, cancelamento, financeiro);
- Rate limit, proteção contra força bruta, logs de auditoria, backup e recuperação;
- HTTPS, cookies seguros, gerenciamento de sessões, chave estável em segredo;
- Migrações de banco e transações robustas, inclusive concorrência e estoque;
- Validação consistente de entrada e tratamento de erros sem exposição de detalhes;
- Revisão de componentes front-end, conteúdo de terceiros e acessibilidade;
- Adequação à LGPD caso sejam processados dados pessoais;
- Revisão fiscal e contábil (não é emissor de NF-e real).

**Importante:** a chave aleatória gerada quando `ERP_SECRET_KEY` está ausente serve apenas para estudo local; ela muda entre reinicializações e invalida sessões. Para ambientes persistentes, defina `ERP_SECRET_KEY` em variável de ambiente, **sem publicar seu valor**. Não use `ERP_COOKIE_SECURE=1` sem HTTPS; com ela, o login via HTTP local não manterá o cookie.

O módulo experimental de banco e as bases antigas foram deixados fora deste pacote por não integrarem o ERP ativo e exigirem revisão própria de segurança.
