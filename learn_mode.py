"""Aulas ligadas a trechos reais do próprio código-fonte, sem executar código de alunos."""
from pathlib import Path
import ast
from flask import Blueprint, render_template, abort, request
from flask_login import login_required

ROOT = Path(__file__).resolve().parent
learn_bp = Blueprint("aprendiz", __name__)
TOPICS = [
  dict(id="login", title="Login: condições e formulários", category="Algoritmos", file="erp.py", symbol="login", description="Veja como if, senha e consulta ao banco funcionam.", task="Localize a condição que confere a senha."),
  dict(id="produtos", title="Cadastro de produtos", category="HTML / Banco de Dados", file="erp.py", symbol="products", description="O que acontece ao enviar o formulário de um produto?", task="Encontre request.form e db.session.commit()."),
  dict(id="tabela", title="Tabela e colunas de produto", category="Banco de Dados", file="models.py", symbol="Product", description="Uma classe db.Model se transforma numa tabela relacional.", task="Identifique a chave primária e os tipos das colunas."),
  dict(id="relacoes", title="Relacionamentos e chaves estrangeiras", category="Banco de Dados", file="models.py", symbol="SaleItem", description="Os itens ligam uma venda aos produtos.", task="Encontre sale_id e product_id e explique os vínculos."),
  dict(id="carrinho", title="PDV: adicionando itens", category="Algoritmos", file="erp.py", symbol="pdv_add_item", description="Validação, quantidade, cálculo e estoque.", task="Identifique a condição que impede venda sem estoque."),
  dict(id="venda", title="PDV: conclusão da venda", category="Algoritmos", file="erp.py", symbol="pdv_finish", description="Fluxo de controle e movimentação financeira.", task="Ache o trecho que registra a entrada no caixa."),
  dict(id="sql", title="SQL real do ERP", category="Banco de Dados", file="erp.py", symbol="aulas", description="SELECT, WHERE, JOIN e GROUP BY com as tabelas reais.", task="Identifique a consulta que relaciona vendas e produtos."),
  dict(id="dashboard", title="Dashboard: somas e filtros", category="Algoritmos", file="erp.py", symbol="get_dashboard_data", description="Como são calculados os indicadores do painel.", task="Encontre o cálculo de vendas pagas."),
  dict(id="repeticao", title="Repetições: dados fictícios", category="Algoritmos", file="seed_data.py", symbol="seed_products", description="Laços for, condições e dados de exemplo.", task="Localize o for que percorre os produtos."),
  dict(id="html", title="HTML e Jinja dos produtos", category="HTML / CSS", file="templates/erp/produtos.html", symbol=None, description="Veja o formulário real enviado ao servidor.", task="Encontre os atributos name dos campos."),
  dict(id="css", title="CSS e cores do ERP", category="HTML / CSS", file="static/erp_style.css", symbol=None, description="Variáveis CSS, seletores e propriedades visuais.", task="Encontre --primary-color e seus usos."),
]
def get_real_code(topic):
    """Lê apenas arquivos autorizados; usa AST para localizar a função/classe real."""
    path = ROOT / topic["file"]
    full = path.read_text(encoding="utf-8")
    if topic["symbol"] is None:
        return full[:18000], 1
    tree = ast.parse(full)
    node = next((n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == topic["symbol"]), None)
    if node is None:
        raise LookupError(topic["symbol"])
    first = min([node.lineno] + [d.lineno for d in getattr(node,"decorator_list",[])])
    return "".join(full.splitlines(keepends=True)[first-1:node.end_lineno]), first

@learn_bp.route("/aprendiz")
@login_required
def index():
    return render_template("aprendiz/index.html", topics=TOPICS)

@learn_bp.route("/aprendiz/<topic_id>")
@login_required
def topic_page(topic_id):
    topic = next((t for t in TOPICS if t["id"] == topic_id), None)
    if topic is None: abort(404)
    try:
        code, line = get_real_code(topic)
    except (OSError, SyntaxError, LookupError):
        abort(503)
    return render_template("aprendiz/topico.html", topic=topic, source=code, start_line=line,
        github_url="https://github.com/isaacsa2/erpbyisaacsa2/blob/main/"+topic["file"])

@learn_bp.app_context_processor
def inject_aprendiz():
    mapping = {"erp.dashboard":"dashboard","erp.pdv":"carrinho","erp.products":"produtos","erp.aulas":"sql",
        "erp.customers":"relacoes","erp.sales":"venda","erp.suppliers":"tabela","erp.treasury":"venda"}
    topic_id = mapping.get(request.endpoint)
    return {"aprendiz_suggestion":next((t for t in TOPICS if t["id"] == topic_id),None)}
