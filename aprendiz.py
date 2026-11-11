"""Modo Aprendiz: exibe código real da versão instalada, sem executá-lo."""
import ast
import os
from pathlib import Path
from functools import lru_cache
from flask import Blueprint, jsonify, request
from flask_login import login_required

learn_bp = Blueprint("aprendiz", __name__)
ROOT = Path(__file__).resolve().parent

# Cada tela referencia arquivos e símbolos que já existem no ERP.
# Não armazenamos cópias manuais dos códigos das aulas neste arquivo.
CATALOG = {
    "erp.dashboard": ("Painel inicial", "dashboard", "erp/dash.html", ["Sale","Product","TreasuryEntry"], "Observe como a rota chama o cálculo dos indicadores e os envia ao HTML."),
    "erp.pdv": ("Ponto de venda", "pdv", "erp/pdv.html", ["Sale","SaleItem","Product"], "Uma venda possui vários itens. Investigue a relação com o estoque."),
    "erp.customers": ("Clientes", "customers", "erp/clientes.html", ["Customer"], "Compare GET (mostrar dados) e POST (receber formulário)."),
    "erp.suppliers": ("Fornecedores", "suppliers", "erp/fornecedores.html", ["Supplier"], "Um fornecedor pode estar ligado a várias contas a pagar."),
    "erp.products": ("Produtos", "products", "erp/produtos.html", ["Product"], "Observe preço, custo, estoque e validação antes de salvar."),
    "erp.sales": ("Vendas", "sales", "erp/vendas.html", ["Sale","SaleItem","Product"], "Encontre as chaves estrangeiras que associam venda, item e produto."),
    "erp.treasury": ("Tesouraria", "treasury", "erp/tesouro.html", ["TreasuryEntry"], "Uma Entrada aumenta o saldo e uma Saída diminui."),
    "erp.receivables": ("Recebimentos", "receivables", "erp/recebimento.html", ["AccountReceivable","Customer"], "Uma conta liga cliente, valor, vencimento e situação."),
    "erp.payables": ("Pagamentos", "payables", "erp/pagamentos.html", ["AccountPayable","Supplier"], "Observe a chave estrangeira da conta para o fornecedor."),
    "erp.fixed_costs": ("Custos fixos", "fixed_costs", "erp/custos_fixos.html", ["FixedCost"], "Veja a validação do valor e do dia de vencimento."),
    "erp.defaulters_report": ("Inadimplência", "defaulters_report", "erp/inadimplentes.html", ["Customer","AccountReceivable"], "Observe filtros, relacionamentos e consultas."),
    "erp.aulas": ("Laboratório SQL", "aulas", "erp/aulas.html", ["Product","SaleItem"], "Leia os SELECT, JOIN e GROUP BY que o ERP realmente executa."),
    "erp.nfe": ("Comprovante didático", "nfe", "erp/nfe.html", ["Sale","SaleItem"], "É uma simulação, não uma nota fiscal válida na SEFAZ."),
}

@lru_cache(maxsize=3)
def parse_file(filename):
    """O parâmetro filename é controlado no servidor, nunca pelo navegador."""
    return ast.parse((ROOT / filename).read_text(encoding="utf-8"))

def real_python(filename, name, kind="function"):
    """Extrai uma função/classe de verdade, com as linhas e os decoradores."""
    source = (ROOT / filename).read_text(encoding="utf-8").splitlines()
    kinds = ast.ClassDef if kind == "class" else (ast.FunctionDef, ast.AsyncFunctionDef)
    for node in parse_file(filename).body:
        if isinstance(node, kinds) and node.name == name:
            first = min([node.lineno] + [d.lineno for d in node.decorator_list])
            last = node.end_lineno
            return {"arquivo": filename, "inicio": first, "fim": last,
                    "codigo": "\n".join(f"{i:>4} | {source[i-1]}" for i in range(first,last+1))}
    raise LookupError(name)

def real_text(filename):
    """Lê o HTML ou o CSS exatos, sem executar trechos de código."""
    lines = (ROOT / filename).read_text(encoding="utf-8").splitlines()
    return {"arquivo": filename, "inicio": 1, "fim": len(lines),
            "codigo": "\n".join(f"{i:>4} | {line}" for i,line in enumerate(lines,1))}

@learn_bp.get("/aprendiz/api")
@login_required
def api():
    """Consulta didática autenticada: somente arquivos de uma lista fechada."""
    page = request.args.get("pagina", "")
    config = CATALOG.get(page)
    if not config:
        return jsonify({"erro": "Esta tela ainda não está mapeada."}), 404
    title, function_name, html, models, description = config
    try:
        sections = [
            {"titulo": "Python — rota real", "linguagem": "python", **real_python("erp.py",function_name)},
            {"titulo": "HTML/Jinja — arquivo real", "linguagem": "html", **real_text("templates/"+html)},
            *[{"titulo": "Modelo — "+name, "linguagem": "python", **real_python("models.py",name,"class")} for name in models],
            {"titulo": "CSS — arquivo real", "linguagem": "css", **real_text("static/erp_style.css")},
        ]
    except (OSError, LookupError, SyntaxError):
        return jsonify({"erro": "Não foi possível ler este trecho nesta versão."}), 503
    commit = os.environ.get("RENDER_GIT_COMMIT", "main")
    for part in sections:
        part["github"] = ("https://github.com/isaacsa2/erpbyisaacsa2/blob/"
                          +commit+"/"+part["arquivo"]+"#L"+str(part["inicio"]))
    response = jsonify({"pagina": title, "conceito": description, "secoes": sections,
                        "aviso": "Código extraído dos próprios arquivos desta versão, sem exemplos inventados."})
    response.headers["Cache-Control"] = "private, no-store"
    return response
