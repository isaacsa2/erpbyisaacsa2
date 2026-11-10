import os
import secrets
import click
from datetime import datetime, date
from flask import Flask, abort, render_template, request, session
from flask_login import LoginManager
from flask_migrate import Migrate
from erp import erp_bp
from models import db, User, Role, fmt

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///erp_estudos.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.environ.get("ERP_SECRET_KEY") or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("ERP_COOKIE_SECURE") == "1",
)
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.login_view = "erp.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None

app.register_blueprint(erp_bp)

def csrf_token():
    token = session.get("_csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token

@app.before_request
def enforce_csrf():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        expected = session.get("_csrf_token")
        provided = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
        if not expected or not provided or not secrets.compare_digest(expected, provided):
            abort(400, description="Token de formulário ausente ou inválido.")

@app.context_processor
def inject_globals():
    return {"now": datetime.now(), "date": date, "csrf_token": csrf_token, "fmt": fmt}

@app.template_filter("fmt")
def jinja_fmt(v):
    if v is None: return "0,00"
    return f"{fmt(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@app.template_filter("datetime_fmt")
def datetime_fmt(value, fmt="%d/%m/%Y %H:%M"):
    if not value: return "Não pago ainda"
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())
    return value.strftime(fmt)

@app.template_filter("date_fmt")
def date_fmt(value, fmt="%d/%m/%Y"):
    return value.strftime(fmt) if value else "-"

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

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
