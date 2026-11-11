"""Ponto de entrada do ERP: configura Flask, banco de dados e autenticação.
O navegador acessa uma rota em erp.py, que utiliza as tabelas de models.py.
"""

import os
import secrets
import click
from datetime import datetime, date
from flask import Flask, abort, render_template, request, session, jsonify
from flask_login import LoginManager
from flask_migrate import Migrate
from erp import erp_bp
from aprendiz import learn_bp
from models import db, User, Role, fmt

# Modo de DEMONSTRAÇÃO: somente dados fictícios. A conta pública pode editar tudo.
# Para proteger bancos reais, este modo força um SQLite exclusivo e temporário.
# Ele fica desligado por padrão em instalações locais.
DEMO_MODE = os.environ.get("ERP_DEMO_MODE") == "1"

# Flask recebe as requisições HTTP e escolhe qual função responderá a cada URL.
app = Flask(__name__)
app.config.update(
    # Nunca usar DATABASE_URL da instalação real quando a demo pública está ativa.
    SQLALCHEMY_DATABASE_URI=(
        "sqlite:///erp_demo_faculdade.sqlite3" if DEMO_MODE
        else os.environ.get("DATABASE_URL", "sqlite:///erp_estudos.db")
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.environ.get("ERP_SECRET_KEY") or secrets.token_hex(32),
    DEMO_MODE=DEMO_MODE,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("ERP_COOKIE_SECURE") == "1",
)
# SQLAlchemy faz a ponte entre os objetos Python e o banco configurado.
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.login_view = "erp.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    """Recupera o usuário autenticado pelo ID guardado na sessão."""
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None

# As rotas (URLs) do ERP ficam organizadas no arquivo erp.py.
app.register_blueprint(erp_bp)
app.register_blueprint(learn_bp)

# O token CSRF impede que um terceiro envie um formulário em nome do usuário.
def csrf_token():
    """Cria um token de sessão para proteger o envio dos formulários."""
    token = session.get("_csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token

@app.before_request
def enforce_csrf():
    """Confere o token antes de aceitar uma alteração enviada pelo navegador."""
    # A turma pode fazer cadastros, vendas e exclusões na demo.
    # A proteção CSRF permanece ativa para todas as alterações HTTP.
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        expected = session.get("_csrf_token")
        provided = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
        if not expected or not provided or not secrets.compare_digest(expected, provided):
            abort(400, description="Token de formulário ausente ou inválido.")

@app.context_processor
def inject_globals():
    """Disponibiliza valores e funções para todas as páginas HTML."""
    return {"now": datetime.now(), "date": date, "csrf_token": csrf_token, "fmt": fmt}

@app.template_filter("fmt")
def jinja_fmt(v):
    """Converte números em texto com vírgula decimal."""
    if v is None: return "0,00"
    return f"{fmt(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@app.template_filter("datetime_fmt")
def datetime_fmt(value, fmt="%d/%m/%Y %H:%M"):
    """Transforma data e hora em texto legível para a página."""
    if not value: return "Não pago ainda"
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())
    return value.strftime(fmt)

@app.template_filter("date_fmt")
def date_fmt(value, fmt="%d/%m/%Y"):
    """Transforma uma data em texto no formato brasileiro."""
    return value.strftime(fmt) if value else "-"

@app.get("/healthz")
def healthz():
    """Health check usado pela Render para monitorar o servidor Flask."""
    return jsonify({"status": "ok"})

@app.errorhandler(400)
def bad_request(error): return render_template("erros/400.html"), 400
@app.errorhandler(401)
def unauthorized(error): return render_template("erros/403.html"), 401
@app.errorhandler(403)
def forbidden(error): return render_template("erros/403.html"), 403
@app.errorhandler(404)
def page_not_found(error): return render_template("erros/404.html"), 404
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("erros/500.html"), 500

@app.cli.command("init-admin")
@click.option("--username", default="admin", show_default=True)
@click.password_option(confirmation_prompt=True)
def init_admin(username, password):
    """Inicializa as tabelas e cria um administrador sem senha padrão."""
    if len(password) < 10: raise click.ClickException("Senha mínima: 10 caracteres.")
    db.create_all()
    for role_name in ("Admin", "Gerente", "Caixa"):
        if not Role.query.filter_by(name=role_name).first():
            db.session.add(Role(name=role_name))
    db.session.commit()
    if User.query.filter_by(username=username).first():
        raise click.ClickException("Usuário existente; nada foi alterado.")
    user = User(username=username, role=Role.query.filter_by(name="Admin").first())
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Administrador {username!r} criado.")

@app.cli.command("create-user")
@click.option("--username", prompt=True)
@click.option("--role", type=click.Choice(["Admin", "Gerente", "Caixa"]), prompt=True)
@click.password_option(confirmation_prompt=True)
def create_user(username, role, password):
    """Cria um usuário pelo terminal local."""
    if len(password) < 10: raise click.ClickException("Senha mínima: 10 caracteres.")
    if User.query.filter_by(username=username).first(): raise click.ClickException("Usuário existente.")
    role_obj = Role.query.filter_by(name=role).first()
    if not role_obj: raise click.ClickException("Execute init-admin primeiro.")
    user = User(username=username, role=role_obj)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Usuário {username!r} criado com perfil {role}.")

def initialize_demo():
    """Prepara uma pequena empresa fictícia para a turma explorar com segurança."""
    if not DEMO_MODE:
        return
    from models import Customer, Supplier, Product, Sale, SaleItem, TreasuryEntry, FixedCost
    for name in ("Admin", "Gerente", "Caixa"):
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name))
    db.session.flush()
    if not User.query.filter_by(username="admin").first():
        # A conta pública recebe Admin completo APENAS no SQLite temporário.
        demo = User(username="admin", role=Role.query.filter_by(name="Admin").first())
        demo.set_password(os.environ.get("ERP_DEMO_PASSWORD", "admin"))
        db.session.add(demo)
    if not Customer.query.first():
        db.session.add_all([
            Customer(name="Cliente Exemplo", email="cliente@exemplo.invalid"),
            Customer(name="Maria (personagem fictícia)", email="maria@exemplo.invalid")
        ])
    if not Supplier.query.first():
        db.session.add(Supplier(name="Fornecedor Didático", contact="Equipe da Aula", cnpj="00.000.000/0000-00"))
    if not Product.query.first():
        db.session.add_all([
            Product(name="Caderno de exercícios", category="Papelaria", cost=7, price=12, stock=20),
            Product(name="Caneta azul", category="Papelaria", cost=1.5, price=3, stock=60),
            Product(name="Bloco de notas", category="Papelaria", cost=4, price=8, stock=15)
        ])
    db.session.commit()
    if not Sale.query.first():
        sale = Sale(customer_id=Customer.query.first().id, status="Pago", date=datetime.now())
        db.session.add(sale)
        db.session.flush()
        db.session.add(SaleItem(sale_id=sale.id, product_id=Product.query.first().id, quantity=2, subtotal=24))
        db.session.add(TreasuryEntry(date=datetime.now(), type="Entrada", amount=24,
                                     description="Venda demonstrativa", origin="sale", origin_id=sale.id))
    if not FixedCost.query.first():
        db.session.add(FixedCost(name="Internet (exemplo)", description="Mensalidade simulada", amount=99.9, due_day=10))
    db.session.commit()


def reset_demo_database():
    """Descarta e recria os dados fictícios a cada inicialização da aplicação.

    A URL do banco no modo demo é forçada a SQLite separado, independente de
    DATABASE_URL. Portanto, este reset nunca toca o banco normal do ERP.
    Importante: a demonstração deve executar com um único worker Gunicorn.
    """
    if not DEMO_MODE:
        return
    if db.engine.url.get_backend_name() != "sqlite":
        raise RuntimeError("Reset demonstrativo só pode operar com SQLite.")
    db.session.remove()
    db.drop_all()
    db.create_all()
    initialize_demo()


with app.app_context():
    if DEMO_MODE:
        reset_demo_database()
    else:
        db.create_all()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
