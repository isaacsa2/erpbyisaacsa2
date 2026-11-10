from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort
from datetime import datetime, date, timedelta
from sqlalchemy import func, case
from sqlalchemy.exc import SQLAlchemyError
from models import db, fmt, models_page, Customer, Supplier, Product, Sale, SaleItem, AccountReceivable, AccountPayable, TreasuryEntry, FixedCost, User, Role # Modelos
from models import add_treasury_entry, update_overdue_status, calculate_abc_curve, get_cash_flow_summary, add_monthly_fixed_costs # Funções auxiliares
from functools import wraps

erp_bp = Blueprint('erp', __name__, url_prefix='')

# ----------------------------
# FUNÇÕES AUXILIARES
# ----------------------------

PER_PAGE = models_page

def get_fixed_costs_total(start_date, end_date):
    costs = TreasuryEntry.query.filter(
        TreasuryEntry.type == "Saida",
        TreasuryEntry.origin == "Custo Fixo",
        TreasuryEntry.date >= start_date,
        TreasuryEntry.date <= end_date
    ).all()
    return fmt(sum(c.amount for c in costs))

def roles_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Você precisa estar logado.", "warning")
                return redirect(url_for("erp.login"))
            if current_user.role.name not in allowed_roles:
                flash("Você não tem permissão para acessar esta página.", "danger")
                return abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator

def create_receivable_from_sale(sale: Sale, days_until_due=7):
    if sale.receivable:
        return sale.receivable
    due = datetime.now().date() + timedelta(days=days_until_due)
    ar = AccountReceivable(
        sale_id=sale.id,
        customer_id=sale.customer_id,
        due_date=due,
        amount=sale.total,
        status='Pendente'
    )
    db.session.add(ar)
    return ar

def calculate_treasury_balance(entries):
    return sum(e.amount if e.type == 'Entrada' else -e.amount for e in entries)

def get_global_treasury_balance():
    return TreasuryEntry.global_balance()

def sum_fixed_costs(days=30):
    today = datetime.today().date()
    start_date = today - timedelta(days=days-1)
    
    total = db.session.query(
        func.sum(TreasuryEntry.amount)
    ).filter(
        TreasuryEntry.type == "Saida",
        TreasuryEntry.origin == "Custo Fixo",
        func.date(TreasuryEntry.date) >= start_date,
        func.date(TreasuryEntry.date) <= today
    ).scalar() or 0
    
    return fmt(total)

# ----------------------------
# Dashboard Data
# ----------------------------

def get_dashboard_data(days=30):
    # Dashboard é consulta; não executa lançamentos financeiros em GET.

    today = datetime.today().date()
    start_date = today - timedelta(days=days-1)

    # ----------------------
    # Indicadores principais
    # ----------------------
    total_sales = sum(s.total for s in Sale.query.all())
    total_paid_sales = sum(s.total for s in Sale.query.filter_by(status="Pago").all())

    total_ar_pending = sum(
        ar.amount for ar in AccountReceivable.query.filter(AccountReceivable.status != "Pago").all()
    )

    total_ap_pending = sum(
        ap.amount for ap in AccountPayable.query.filter(AccountPayable.status != "Pago").all()
    )

    # Custos fixos do período filtrado
    total_fixed_costs = db.session.query(func.sum(TreasuryEntry.amount)).filter(
        TreasuryEntry.type == "Saida",
        TreasuryEntry.origin == "Custo Fixo",
        func.date(TreasuryEntry.date) >= start_date,
        func.date(TreasuryEntry.date) <= today
    ).scalar() or 0
    
    defaulters_count = Customer.query.filter_by(is_defaulter=True).count()
    total_debt = db.session.query(
        func.sum(AccountReceivable.amount)
    ).filter(
        AccountReceivable.status.in_(['Atrasado', 'Pendente'])
    ).scalar() or 0
    


    low_stock = Product.query.order_by(Product.stock.asc()).limit(3).all()
    last_sales = Sale.query.order_by(Sale.date.desc()).limit(5).all()
    treasury_balance = fmt(get_global_treasury_balance())
    cash_flow = get_cash_flow_summary(days)
    abc_products = calculate_abc_curve()

    sales_status_counts = {
        "Pago": Sale.query.filter_by(status="Pago").count(),
        "Pendente": Sale.query.filter_by(status="Pendente").count(),
        "Cancelado": Sale.query.filter_by(status="Cancelado").count()
    }

    top_products = (
        db.session.query(Product.name, func.sum(SaleItem.quantity).label("sold_qty"))
        .join(SaleItem)
        .group_by(Product.id)
        .order_by(func.sum(SaleItem.quantity).desc())
        .limit(5)
        .all()
    )

    return {"defaulters_count": defaulters_count, "total_debt": fmt(total_debt),"days": days, "total_fixed_costs": total_fixed_costs, "total_sales": total_sales, "total_paid_sales": total_paid_sales, "total_ar_pending": total_ar_pending, "total_ap_pending": total_ap_pending, "low_stock": low_stock, "treasury_balance": treasury_balance, "last_sales": last_sales, "sales_status": sales_status_counts, "top_products": [{"name": p.name, "sold_qty": p.sold_qty} for p in top_products], "cash_flow": cash_flow, "abc_products": abc_products}

# ----------------------------
# Rotas API
# ----------------------------


@erp_bp.route("/register", methods=["POST"])
@roles_required("Admin")
@login_required
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    role_name = data.get("role", "Caixa")

    if not username or not password or len(password) < 10:
        return jsonify({"error": "Username e password são obrigatórios"}), 400

    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return jsonify({"error": f"Role '{role_name}' não existe"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Usuário já existe"}), 400

    user = User(username=username, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Mantém a sessão do administrador atual; não autentica como a nova conta.
    return jsonify({
        "message": f"Usuário {username} registrado com sucesso!",
        "role": role.name
    }), 201

@erp_bp.route("/pdv/add", methods=["POST"])
@roles_required("Caixa", "Admin", "Gerente")
@login_required
def pdv_add_item():
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", type=int, default=1)

    product = Product.query.get(product_id)
    if not product:
        flash("Produto não encontrado!", "danger")
        return redirect(url_for("erp.pdv"))

    if quantity < 1:
        flash("Quantidade inválida.", "danger")
        return redirect(url_for("erp.pdv"))

    if product.stock < quantity:
        flash(f"Estoque insuficiente para {product.name}. Estoque atual: {product.stock}", "warning")
        return redirect(url_for("erp.pdv"))

    sale_id = session.get("current_sale")
    if not sale_id:
        default_customer = Customer.query.first()
        if not default_customer:
            flash("Nenhum cliente cadastrado. Cadastre um cliente primeiro!", "danger")
            return redirect(url_for("erp.customers"))
            
        new_sale = Sale(
            customer_id=default_customer.id,
            status="Em andamento", 
            date=datetime.now()
        )
        db.session.add(new_sale)
        db.session.flush()
        session["current_sale"] = new_sale.id
        sale_id = new_sale.id

    sale_item = SaleItem.query.filter_by(sale_id=sale_id, product_id=product.id).first()
    if sale_item:
        sale_item.quantity += quantity
        sale_item.subtotal = fmt(sale_item.quantity * product.price)
    else:
        sale_item = SaleItem(
            sale_id=sale_id,
            product_id=product.id,
            quantity=quantity,
            subtotal=fmt(product.price * quantity)
        )
        db.session.add(sale_item)

    product.stock -= quantity
    db.session.commit()

    flash(f"{quantity}x {product.name} adicionado à venda!", "success")
    return redirect(url_for("erp.pdv"))

@erp_bp.route("/pdv/finish", methods=["POST"])
@roles_required("Caixa", "Admin", "Gerente")
@login_required
def pdv_finish():
    sale_id = session.get("current_sale")
    if not sale_id:
        flash("Nenhuma venda em andamento!", "danger")
        return redirect(url_for("erp.pdv"))

    sale = Sale.query.get_or_404(sale_id)
    customer_id = request.form.get("customer_id", type=int)
    payment_method = request.form.get("payment_method") or "Desconhecido"

    if not customer_id:
        flash("Selecione um cliente antes de finalizar!", "danger")
        return redirect(url_for("erp.pdv"))

    if not sale.items:
        flash("Não é possível finalizar uma venda sem itens!", "warning")
        return redirect(url_for("erp.pdv"))

    if db.session.get(Customer, customer_id) is None:
        flash("Cliente não encontrado!", "danger")
        return redirect(url_for("erp.pdv"))

    sale.customer_id = customer_id
    sale.status = "Pago"
    sale.date = datetime.now()

    total = sum(i.subtotal for i in sale.items)

    add_treasury_entry(
        "Entrada",
        total,
        description=f"Venda PDV #{sale.id} ({payment_method})",
        origin="sale",
        origin_id=sale.id
    )

    db.session.commit()
    session.pop("current_sale", None)

    flash(f"Venda #{sale.id} concluída com sucesso! Total R${fmt(total):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), "success")
    return redirect(url_for("erp.nfe", sale_id=sale.id))

@erp_bp.route("/pdv/cancel", methods=["POST"])
@roles_required("Caixa", "Admin", "Gerente")
@login_required
def pdv_cancel():
    sale_id = session.get("current_sale")
    if sale_id:
        sale = Sale.query.get(sale_id)
        if sale:
            for item in sale.items:
                product = Product.query.get(item.product_id)
                product.stock += item.quantity
                db.session.delete(item)
            db.session.delete(sale)
            db.session.commit()
        session.pop("current_sale", None)
    
    flash("Venda cancelada!", "info")
    return redirect(url_for("erp.pdv"))

@erp_bp.route("/pdv/remove/<int:item_id>", methods=["POST"])
@roles_required("Caixa", "Admin", "Gerente")
@login_required
def pdv_remove_item(item_id):
    item = SaleItem.query.get_or_404(item_id)
    if item.sale_id != session.get("current_sale"):
        abort(403)
    product = Product.query.get(item.product_id)
    
    product.stock += item.quantity
    
    sale_id = item.sale_id
    db.session.delete(item)
    
    remaining_items = SaleItem.query.filter_by(sale_id=sale_id).count()
    if remaining_items == 0:
        sale = Sale.query.get(sale_id)
        db.session.delete(sale)
        session.pop("current_sale", None)
    
    db.session.commit()
    flash("Item removido da venda!", "success")
    return redirect(url_for("erp.pdv"))

@erp_bp.route("/pdv/change_customer", methods=["POST"])
@roles_required("Caixa", "Admin", "Gerente")
@login_required
def pdv_change_customer():
    sale_id = session.get("current_sale")
    if not sale_id:
        flash("Nenhuma venda em andamento!", "danger")
        return redirect(url_for("erp.pdv"))
    
    customer_id = request.form.get("customer_id", type=int)
    if not customer_id:
        flash("Selecione um cliente válido!", "danger")
        return redirect(url_for("erp.pdv"))
    
    sale = Sale.query.get_or_404(sale_id)
    if db.session.get(Customer, customer_id) is None:
        flash("Cliente não encontrado!", "danger")
        return redirect(url_for("erp.pdv"))
    sale.customer_id = customer_id
    db.session.commit()
    
    flash("Cliente alterado com sucesso!", "success")
    return redirect(url_for("erp.pdv"))

@erp_bp.route("/customers/defaulter/<int:customer_id>", methods=["POST"])
@roles_required("Admin", "Gerente")
@login_required
def mark_as_defaulter(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    reason = request.form.get("reason", "")
    
    customer.is_defaulter = True
    customer.defaulter_since = date.today()
    customer.default_reason = reason
    
    db.session.commit()
    flash(f"Cliente {customer.name} marcado como inadimplente.", "warning")
    return redirect(url_for("erp.customers"))

@erp_bp.route("/customers/regularize/<int:customer_id>", methods=["POST"])
@roles_required("Admin", "Gerente")
@login_required
def regularize_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    customer.is_defaulter = False
    customer.defaulter_since = None
    customer.default_reason = None
    
    db.session.commit()
    flash(f"Cliente {customer.name} regularizado com sucesso.", "success")
    return redirect(url_for("erp.customers"))


@erp_bp.route("/sales/cancel/<int:sale_id>", methods=["POST"])
@roles_required("Admin", "Gerente")
@login_required
def cancel_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    if sale.status != "Cancelado":
        sale.cancel()
        db.session.commit()
        flash(f"Venda {sale.id} cancelada e estoque atualizado!", "success")
    else:
        flash("Venda já está cancelada.", "info")
    return redirect(url_for("erp.sales"))

@erp_bp.route("/sales/undo/<int:sale_id>", methods=["POST"])
@roles_required("Admin", "Gerente")
@login_required
def undo_cancel_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    if sale.status != "Pendente":
        try:
            sale.redo()
            db.session.commit()
            flash(f"Venda {sale.id} refeita e estoque atualizado!", "success")
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
    else:
        flash("Venda já está correta.", "info")
    return redirect(url_for("erp.sales"))

@erp_bp.route("/receivables/pay/<int:ar_id>", methods=["POST"])
@roles_required("Admin", "Gerente")
@login_required
def receivables_pay(ar_id):
    ar = AccountReceivable.query.get_or_404(ar_id)
    if ar.status == "Pago":
        flash("Já está marcado como pago.", "warning")
        return redirect(url_for("erp.receivables"))

    pay_date_str = request.form.get("payment_date")
    method = request.form.get("payment_method") or "Desconhecido"
    try:
        pay_date = datetime.strptime(pay_date_str, "%Y-%m-%d").date() if pay_date_str else date.today()
    except:
        pay_date = date.today()


    ar.status = "Pago"
    ar.payment_date = datetime.combine(pay_date, datetime.min.time())
    ar.payment_method = method
    if ar.sale:
        ar.sale.status = "Pago"

    add_treasury_entry(
        'Entrada',
        ar.amount,
        description=f"Recebimento AR#{ar.id} - {ar.customer.name}",
        origin='receivable',
        origin_id=ar.id
    )
    db.session.commit()
    flash("Conta a receber baixada e Entrada registrada no caixa.", "success")
    return redirect(url_for("erp.receivables"))

@erp_bp.route("/payables/pay/<int:ap_id>", methods=["POST"])
@roles_required("Admin", "Gerente")
@login_required
def payables_pay(ap_id):
    ap = AccountPayable.query.get_or_404(ap_id)
    if ap.status == "Pago":
        flash("Já está marcado como pago.", "warning")
        return redirect(url_for("erp.payables"))

    pay_date_str = request.form.get("payment_date")
    method = request.form.get("payment_method") or "Desconhecido"
    try:
        pay_date = datetime.strptime(pay_date_str, "%Y-%m-%d").date() if pay_date_str else date.today()
    except:
        pay_date = date.today()

    ap.status = "Pago"
    ap.payment_date = pay_date
    ap.payment_method = method

    add_treasury_entry(
        'Saida',
        ap.amount,
        description=f"Pagamento AP#{ap.id} - {ap.supplier.name}",
        origin='payable',
        origin_id=ap.id
    )
    db.session.commit()
    flash("Conta a pagar baixada e saída registrada no caixa.", "success")
    return redirect(url_for("erp.payables"))

# ----------------------------
# Rotas HTML
# ----------------------------

@erp_bp.route("/")
@login_required
def dashboard():
    if current_user.role.name == "Caixa":
        return redirect(url_for("erp.pdv"))
    else: 
        days = request.args.get("days", 30, type=int)
        days = days if days in (1, 7, 14, 30, 60, 120) else 30
        data = get_dashboard_data(days=days)
        return render_template("erp/dash.html", data=data)


@erp_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first() if username else None
        if username and password and user and user.check_password(password):
            login_user(user)
            flash("Login realizado com sucesso!", "success")

            # Redireciona pelo role
            role_redirect = {
                "Caixa": "erp.pdv",
                "Admin": "erp.dashboard",
                "Gerente": "erp.dashboard"
            }
            return redirect(url_for(role_redirect.get(user.role.name, "erp.dashboard")))
        else:
            flash("Usuário ou senha incorretos!", "danger")
    return render_template("erp/login.html")

@erp_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Logout realizado!", "info")
    return redirect(url_for("erp.login"))


@erp_bp.route("/customers", methods=["GET", "POST"])
@roles_required("Admin", "Gerente")
@login_required
def customers():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        if not name:
            flash("Nome é obrigatório!", "danger")
        else:
            db.session.add(Customer(name=name, email=email, phone=phone, address=address))
            db.session.commit()
            flash("Cliente adicionado com sucesso!", "success")
            return redirect(url_for("erp.customers"))

    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    qry = Customer.query
    if q:
        qry = qry.filter(
            (Customer.name.ilike(f"%{q}%")) |
            (Customer.email.ilike(f"%{q}%")) |
            (Customer.phone.ilike(f"%{q}%"))
        )
    pagination = qry.order_by(Customer.name).paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template("erp/clientes.html", customers=pagination.items, pagination=pagination, q=q)

@erp_bp.route("/suppliers", methods=["GET", "POST"])
@roles_required("Admin", "Gerente")
@login_required
def suppliers():
    if request.method == "POST":
        name = request.form["name"].strip()
        contact = request.form.get("contact")
        phone = request.form.get("phone")
        address = request.form.get("address")
        cnpj = request.form.get("cnpj")
        if not name:
            flash("Nome do fornecedor é obrigatório!", "danger")
        else:
            db.session.add(Supplier(name=name, contact=contact, phone=phone, address=address, cnpj=cnpj))
            db.session.commit()
            flash("Fornecedor adicionado com sucesso!", "success")
            return redirect(url_for("erp.suppliers"))

    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    qry = Supplier.query
    if q:
        qry = qry.filter(
            (Supplier.name.ilike(f"%{q}%")) |
            (Supplier.contact.ilike(f"%{q}%")) |
            (Supplier.cnpj.ilike(f"%{q}%"))
        )
    pagination = qry.order_by(Supplier.name).paginate(page=page, per_page=PER_PAGE, error_out=False)  # Ordenar por nome
    return render_template("erp/fornecedores.html", suppliers=pagination.items, pagination=pagination, q=q)

@erp_bp.route("/products", methods=["GET", "POST"])
@roles_required("Admin", "Gerente")
@login_required
def products():
    if request.method == "POST":
        name = request.form["name"].strip()
        category = request.form.get("category")
        try:
            price = float(request.form.get("price", 0))
            cost = float(request.form.get("cost_price", 0))  # Novo campo
            stock = int(request.form.get("stock", 0))
        except (ValueError, TypeError):
            flash("Preço, custo ou estoque inválido!", "danger")
            return redirect(url_for("erp.products"))

        if not name or not all(map(__import__("math").isfinite, (price, cost))) or price < 0 or cost < 0 or stock < 0:
            flash("Dados inválidos!", "danger")
        else:
            db.session.add(Product(
                name=name, price=fmt(price), cost=fmt(cost), stock=stock, category=category
            ))
            db.session.commit()
            flash("Produto adicionado com sucesso!", "success")
            return redirect(url_for("erp.products"))

    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    qry = Product.query
    if q:
        qry = qry.filter(Product.name.ilike(f"%{q}%"))
    pagination = qry.order_by(Product.name).paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template("erp/produtos.html", products=pagination.items, pagination=pagination, q=q)

@erp_bp.route("/sales", methods=["GET", "POST"])
@roles_required("Admin", "Gerente")
@login_required
def sales():
    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.order_by(Product.name).all()

    if request.method == "POST":
        try:
            customer_id = request.form.get("customer", type=int)
            if not customer_id:
                flash("Selecione um cliente!", "danger")
                return redirect(url_for("erp.sales"))

            sale = Sale(customer_id=customer_id)
            db.session.add(sale)
            db.session.flush() 

            total_items = 0
            for product in products:
                qty = request.form.get(f"product_{product.id}", type=int, default=0)
                if qty and qty > 0:
                    if product.stock < qty:
                        raise ValueError(f"Estoque insuficiente para {product.name}")
                    subtotal = fmt(qty * product.price)
                    db.session.add(SaleItem(sale_id=sale.id, product_id=product.id, quantity=qty, subtotal=subtotal))
                    product.stock -= qty
                    total_items += 1

            if total_items == 0:
                raise ValueError("Selecione pelo menos um produto!")

            if request.form.get("create_ar") == "on":
                s = Sale.query.get(sale.id)
                create_receivable_from_sale(s, days_until_due=int(request.form.get("due_days", 7)))

            db.session.commit()
            flash("Venda registrada com sucesso!", "success")

        except (SQLAlchemyError, ValueError) as e:
            db.session.rollback()
            flash(str(e), "danger")

        return redirect(url_for("erp.sales"))

    sales_list = Sale.query.order_by(Sale.id.desc()).all()
    return render_template("erp/vendas.html", sales=sales_list, customers=customers, products=products)

@erp_bp.route("/treasury", methods=["GET", "POST"])
@roles_required("Admin", "Gerente")
@login_required
def treasury():
    page = request.args.get("page", 1, type=int)
    qry = TreasuryEntry.query

    if request.method == "POST":
        typ = request.form.get("type")
        amount = request.form.get("amount")
        desc = request.form.get("description")
        if not typ or not amount:
            flash("Tipo e valor são obrigatórios.", "danger")
            return redirect(url_for("erp.treasury"))

        try:
            amt = float(amount)
            if amt <= 0:
                raise ValueError()
        except:
            flash("Valor inválido.", "danger")
            return redirect(url_for("erp.treasury"))

        add_treasury_entry(
            'Entrada' if typ == 'Entrada' else 'Saida',
            amt,
            description=desc,
            origin=f'Manual - Motivo: {desc}',
        )
        db.session.commit()
        flash("Lançamento adicionado.", "success")
        return redirect(url_for("erp.treasury"))

    entries_paginated = qry.order_by(TreasuryEntry.date.desc()).paginate(page=page, per_page=PER_PAGE)
    saldo_global = fmt(TreasuryEntry.global_balance())
    return render_template("erp/tesouro.html", entries=entries_paginated, saldo_global=saldo_global)

@erp_bp.route("/receivables", methods=["GET", "POST"])
@roles_required("Admin", "Gerente")
@login_required
def receivables():
    customers = Customer.query.order_by(Customer.name).all()

    if request.method == "POST":
        customer_id = request.form.get("customer", type=int)
        due_date_str = request.form.get("due_date")
        amount = request.form.get("amount")
        notes = request.form.get("notes")
        sale_id = request.form.get("sale_id", type=int)

        if not customer_id or not due_date_str or not amount:
            flash("Campos obrigatórios faltando.", "danger")
            return redirect(url_for("erp.receivables"))

        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            amt = float(amount)
            if amt <= 0:
                raise ValueError()
        except:
            flash("Data ou valor inválido.", "danger")
            return redirect(url_for("erp.receivables"))

        ar = AccountReceivable(
            sale_id=sale_id if sale_id else None,
            customer_id=customer_id,
            due_date=due_date,
            amount=fmt(amt),
            status='Pendente',
            notes=notes
        )
        db.session.add(ar)
        db.session.commit()
        flash("Conta a receber criada.", "success")
        return redirect(url_for("erp.receivables"))

    receivables_list = AccountReceivable.query.order_by(AccountReceivable.due_date).all()
    return render_template("erp/recebimento.html", receivables=receivables_list, customers=customers, now=datetime.now())

@erp_bp.route("/payables", methods=["GET", "POST"])
@roles_required("Admin", "Gerente")
@login_required
def payables():
    suppliers = Supplier.query.order_by(Supplier.name).all()

    if request.method == "POST":
        supplier_id = request.form.get("supplier", type=int)
        due_date_str = request.form.get("due_date")
        amount = request.form.get("amount")
        desc = request.form.get("description")
        
        if not supplier_id or not due_date_str or not amount:
            flash("Campos obrigatórios faltando!", "danger")
            return redirect(url_for("erp.payables"))
        
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            amt = float(amount)
            if amt <= 0:
                raise ValueError()
        except:
            flash("Data ou valor inválido.", "danger")
            return redirect(url_for("erp.payables"))
        
        ap = AccountPayable(
            supplier_id=supplier_id,
            description=desc,
            due_date=due_date,
            amount=fmt(amt),
            status='Pendente'
        )
        db.session.add(ap)
        db.session.commit()
        flash("Conta a pagar criada.", "success")
        return redirect(url_for("erp.payables"))

    payables_list = AccountPayable.query.order_by(AccountPayable.due_date).all()
    return render_template("erp/pagamentos.html", payables=payables_list, suppliers=suppliers, now=datetime.now())

@erp_bp.route("/pdv", methods=["GET"])
@roles_required("Caixa", "Admin", "Gerente")
@login_required
def pdv():
    sale_id = session.get("current_sale")
    sale = None
    sale_items = []
    
    if sale_id:
        sale = Sale.query.get(sale_id)
        if sale:
            sale_items = db.session.query(SaleItem, Product.name).join(Product, SaleItem.product_id == Product.id).filter(SaleItem.sale_id == sale_id).all()
    
    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.order_by(Product.name).all()
    total = sale.total if sale else 0
    
    return render_template(
        "erp/pdv.html", 
        sale=sale, 
        sale_items=sale_items,
        customers=customers, 
        products=products,
        total=total
    )

@erp_bp.route("/nfe/<int:sale_id>")
@roles_required("Caixa", "Admin", "Gerente")
@login_required
def nfe(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    if not sale.customer:
        flash("Venda sem cliente associado!", "warning")
        return redirect(url_for("erp.pdv"))

    nfe_data = {
        "nfe_id": f"NFE{sale.id:06d}",
        "date": sale.date.strftime("%d/%m/%Y %H:%M"),
        "customer": {
            "name": sale.customer.name,
            "email": sale.customer.email or "Não informado",
            "phone": sale.customer.phone or "Não informado",
            "address": sale.customer.address or "Não informado"
        },
        "sale_items": [
            {
                "name": item.product.name,
                "qty": item.quantity,
                "unit_price": fmt(item.product.price),
                "subtotal": fmt(item.subtotal)
            } for item in sale.items
        ],
        "total": fmt(sum(item.subtotal for item in sale.items)),
        "status": sale.status
    }

    return render_template("erp/nfe.html", nfe_data=nfe_data)

@erp_bp.route("/fixed_costs", methods=["GET", "POST"])
@roles_required("Admin", "Gerente")
@login_required
def fixed_costs():
    if request.method == "POST":
        name = request.form["name"].strip()
        description = request.form.get("descricao", "").strip()
        try:
            amount = float(request.form.get("amount", 0))
            due_day = int(request.form.get("due_day", 1))
        except ValueError:
            flash("Valor ou dia inválido!", "danger")
            return redirect(url_for("erp.fixed_costs"))

        if not name or amount <= 0 or due_day < 1 or due_day > 28:
            flash("Dados inválidos!", "danger")
        else:
            db.session.add(FixedCost(name=name, description=description, amount=fmt(amount), due_day=due_day))
            db.session.commit()
            flash("Custo fixo adicionado com sucesso!", "success")
            return redirect(url_for("erp.fixed_costs"))
        
    costs = FixedCost.query.order_by(FixedCost.due_day).all()
    return render_template("erp/custos_fixos.html", costs=costs)

@erp_bp.route("/defaulters")
@roles_required("Admin", "Gerente")
@login_required
def defaulters_report():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    
    qry = Customer.query.filter_by(is_defaulter=True)
    
    if q:
        qry = qry.filter(Customer.name.ilike(f"%{q}%"))
    
    pagination = qry.order_by(Customer.defaulter_since.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )
    
    total_debt = db.session.query(
        func.sum(AccountReceivable.amount)
    ).join(Customer).filter(
        Customer.is_defaulter == True,
        AccountReceivable.status.in_(['Atrasado', 'Pendente'])
    ).scalar() or 0
    
    return render_template(
        "erp/inadimplentes.html",
        customers=pagination.items,
        pagination=pagination,
        q=q,
        total_debt=fmt(total_debt)
    )

@erp_bp.route("/aulas")
@roles_required("Admin", "Gerente")
@login_required
def aulas():
    """Roteiro demonstrativo: apenas SELECTs predefinidos, sem SQL arbitrário."""
    from sqlalchemy import text
    queries = [
        ("SELECT / ORDER BY", "SELECT id, name, price, stock FROM product ORDER BY price DESC LIMIT 8"),
        ("WHERE: estoque baixo", "SELECT id, name, stock FROM product WHERE stock < 10 ORDER BY stock, name LIMIT 8"),
        ("JOIN: venda, item e produto", "SELECT s.id AS venda, p.name AS produto, si.quantity AS quantidade FROM sale s JOIN sale_item si ON si.sale_id = s.id JOIN product p ON p.id = si.product_id LIMIT 8"),
        ("GROUP BY / SUM", "SELECT p.name AS produto, SUM(si.quantity) AS unidades FROM sale_item si JOIN product p ON p.id = si.product_id JOIN sale s ON s.id = si.sale_id WHERE s.status != 'Cancelado' GROUP BY p.id, p.name ORDER BY unidades DESC LIMIT 8"),
    ]
    outputs=[]
    for topic, sql in queries:
        result = db.session.execute(text(sql))
        outputs.append({"topic":topic, "sql":sql, "columns":list(result.keys()), "rows":result.fetchall()})
    return render_template("erp/aulas.html", outputs=outputs)
