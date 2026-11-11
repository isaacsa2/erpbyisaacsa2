# Modo Aprendiz — código real do ERP

Ao entrar no ERP, abra **Modo Aprendiz** no canto inferior direito. O painel apresenta a função Flask, o template HTML/Jinja, as classes do banco SQLAlchemy e o CSS usados **na própria versão do sistema**. Você pode ler, copiar ou abrir o arquivo no GitHub com referência às linhas.

## Como funciona?

O endpoint autenticado `/aprendiz/api?pagina=erp.products` usa a biblioteca `ast` do Python para encontrar a função `products` diretamente em `erp.py`, e as classes diretamente em `models.py`. O HTML e o CSS também são lidos dos arquivos instalados. O navegador apenas exibe esses trechos como texto: ele não os executa.

A lista de páginas é fixa no servidor, impedindo que parâmetros enviados pelo navegador escolham arquivos arbitrários. A demonstração na Render continua somente leitura.

## Roteiro de estudo

1. Abra **Produtos** → Modo Aprendiz. Compare o formulário com `request.form` na rota real.
2. Examine `Product` e localize o estoque, preço e custo.
3. Abra **Vendas** → identifique o relacionamento entre `Sale`, `SaleItem` e `Product`.
4. Abra **Laboratório SQL** → confira os `JOIN` e `GROUP BY` reais.
5. Em um clone local, altere um texto no HTML e veja o novo resultado.

**Importante:** os trechos correspondem à versão em execução. Se a Render estiver em um commit antigo, o painel mostra esse código antigo, não uma atualização imaginária.
