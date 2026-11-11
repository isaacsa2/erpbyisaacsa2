"""Modelos do banco: cada classe db.Model corresponde a uma tabela SQL.
Column define uma coluna; primary_key é o ID; ForeignKey relaciona tabelas.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import func, case
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_login import UserMixin

# SQLAlchemy transforma objetos Python em registros do banco relacional.
db = SQLAlchemy()

models_page = 15

_fixed_costs_added = False

def add_monthly_fixed_costs():
    """Procura despesas fixas do dia para registrar lançamentos no mês."""
    global _fixed_costs_added
    if _fixed_costs_added:
        return  # já rodou, ignora

    today = datetime.today()
    day = today.day

    # busca custos fixos do dia
    costs_due = FixedCost.query.filter_by(due_day=day).all()
    
    for cost in costs_due:
        # verifica se já existe lançamento no TreasuryEntry neste mês
        exists = TreasuryEntry.query.filter(
            TreasuryEntry.origin == 'Custo Fixo',
            TreasuryEntry.description == cost.name,
            func.extract('month', TreasuryEntry.date) == today.month,
            func.extract('year', TreasuryEntry.date) == today.year
        ).first()
        if not exists:
            TreasuryEntry.add_fixedcosts(
                entry_type='Saida',
                amount=cost.amount,
                description=cost.name
            )
    
    _fixed_costs_added = True

def fmt(v):
    """Arredonda um valor para duas casas decimais."""
    if v is None:
        return 0.0
    return float(Decimal(v).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def calculate_abc_curve(top_per_category=3):
    """Classifica produtos segundo a participação acumulada nas vendas."""
    data = (
        db.session.query(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity * Product.price).label("total_sales")
        )
        .join(SaleItem)
        .group_by(Product.id)
        .order_by(func.sum(SaleItem.quantity * Product.price).desc())
        .all()
    )
    total_sales_value = sum(p.total_sales for p in data)
    cumulative = 0
    categorized = {"A": [], "B": [], "C": []}
    for p in data:
        cumulative += p.total_sales
        pct = cumulative / total_sales_value * 100
        if pct <= 80:
            category = "A"
        elif pct <= 95:
            category = "B"
        else:
            category = "C"
        if len(categorized[category]) < top_per_category:
            categorized[category].append({
                "product": p.name,
                "total_sales": p.total_sales,
                "category": category
            })
    abc_list = categorized["A"] + categorized["B"] + categorized["C"]
    return abc_list

def check_customer_defaulters():
    """Atualiza a situação de inadimplência conforme contas associadas."""
    today = date.today()
    defaulters = Customer.query.join(AccountReceivable).filter(
        AccountReceivable.status == 'Atrasado',
        Customer.is_defaulter == False
    ).all()
    
    for customer in defaulters:
        customer.is_defaulter = True
        customer.defaulter_since = today
        customer.default_reason = "Pagamento em atraso"
    
    regularized = Customer.query.join(AccountReceivable).filter(
        Customer.is_defaulter == True,
        ~AccountReceivable.status.in_(['Atrasado', 'Pendente'])
    ).group_by(Customer.id).having(
        func.sum(case((AccountReceivable.status.in_(['Atrasado', 'Pendente']), 1), else_=0)) == 0
    ).all()
    
    for customer in regularized:
        customer.is_defaulter = False
        customer.defaulter_since = None
        customer.default_reason = None
    
    db.session.commit()

def update_overdue_status():
    """Verifica contas pendentes que já ultrapassaram o vencimento."""
    today = date.today()
    
    overdue_receivables = AccountReceivable.query.filter(
        AccountReceivable.due_date < today,
        AccountReceivable.status == 'Pendente'
    ).all()
    
    for ar in overdue_receivables:
        ar.status = 'Atrasado'
    
    # Atualiza payables vencidos
    overdue_payables = AccountPayable.query.filter(
        AccountPayable.due_date < today,
        AccountPayable.status == 'Pendente'
    ).all()
    
    for ap in overdue_payables:
        ap.status = 'Atrasado'
    
    db.session.commit()
    
    check_customer_defaulters()

def get_cash_flow_summary(days=30):
    """Agrupa entradas e saídas por dia para gerar os gráficos."""
    today = datetime.today().date()
    start_date = today - timedelta(days=days-1)
    entries = TreasuryEntry.query.filter(TreasuryEntry.date >= start_date).all()
    
    cash_flow = {
        "labels": [(start_date + timedelta(days=i)).strftime("%d/%m") for i in range(days)],
        "inflows": [],
        "outflows": []
    }

    for i in range(days):
        day = start_date + timedelta(days=i)
        day_entries = [e for e in entries if e.date.date() == day]  # usa .date() pra comparar só a data
        inflow = sum(e.amount for e in day_entries if e.type == "Entrada")
        outflow = sum(e.amount for e in day_entries if e.type == "Saida")
        cash_flow["inflows"].append(fmt(inflow))
        cash_flow["outflows"].append(fmt(outflow))
    
    return cash_flow

# ATENÇÃO DIDÁTICA: esta segunda definição sobrescreve a função homônima anterior.
def update_overdue_status():
    """Verifica contas pendentes que já ultrapassaram o vencimento."""
    today = date.today()
    pending_ars = AccountReceivable.query.filter(AccountReceivable.status=="Pendente", AccountReceivable.due_date<today).all()
    pending_aps = AccountPayable.query.filter(AccountPayable.status=="Pendente", AccountPayable.due_date<today).all()
    for ar in pending_ars:
        ar.status = "Atrasado"
    for ap in pending_aps:
        ap.status = "Atrasado"

def add_treasury_entry(entry_type, amount, description='', origin=None, origin_id=None):
    """Prepara uma movimentação de caixa sem repetir uma origem identificada."""
    existing_entry = None
    if origin and origin_id:
        existing_entry = TreasuryEntry.query.filter_by(origin=origin, origin_id=origin_id).first()
    if existing_entry:
        return existing_entry

    te = TreasuryEntry(
        date=date.today(),
        type=entry_type,
        amount=fmt(amount),
        description=description,
        origin=origin,
        origin_id=origin_id
    )
    db.session.add(te)
    return te

def add_treasury_gen(entry_type, amount, description='', origin=None, origin_id=None, entry_date=None, commit=True):
    """Prepara um lançamento e permite confirmar imediatamente no banco."""


    if entry_date is None:
        entry_date = datetime.now()

    if origin and origin_id:
        existing_entry = TreasuryEntry.query.filter_by(origin=origin, origin_id=origin_id).first()
        if existing_entry:
            return existing_entry

    te = TreasuryEntry(
        date=entry_date,
        type=entry_type,
        amount=fmt(amount),
        description=description,
        origin=origin,
        origin_id=origin_id
    )
    db.session.add(te)
    if commit:
        db.session.commit()
    return te

# ----------------------------
# MODELOS ERP
# ----------------------------

class Customer(db.Model):
    """Cliente, ligado a vendas e contas a receber."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    is_defaulter = db.Column(db.Boolean, default=False)
    defaulter_since = db.Column(db.Date)
    default_reason = db.Column(db.Text)
    credit_limit = db.Column(db.Numeric(10, 2), default=0)
    credit_used = db.Column(db.Numeric(10, 2), default=0)
    
    # Relacionamentos
    # 1:N significa que um cliente pode ter várias vendas.
    sales = db.relationship('Sale', backref='customer', lazy=True)
    receivables = db.relationship('AccountReceivable', backref='customer', lazy=True)

class Supplier(db.Model):
    """Fornecedor, ligado a contas a pagar."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    cnpj = db.Column(db.String(200))
    payables = db.relationship('AccountPayable', backref='supplier', lazy=True)

class Product(db.Model):
    """Produto com preço, custo e estoque."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    cost = db.Column(db.Float, nullable=False, default=0.0)   
    stock = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(50))
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)
        
    @property
    def margin_percent(self):
        """Calcula a porcentagem da margem de lucro sobre a venda."""
        if self.price > 0:
            return round((self.price - self.cost) / self.price * 100, 2)
        return 0

class Sale(db.Model):
    """Venda vinculada a um cliente e a vários itens."""
    id = db.Column(db.Integer, primary_key=True)
    # ForeignKey liga uma venda ao identificador de um cliente.
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pendente')
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade="all, delete-orphan")
    receivable = db.relationship('AccountReceivable', backref='sale', uselist=False)

    @property
    def total(self):
        """Soma o subtotal de cada item vinculado à venda."""
        return sum(item.subtotal for item in self.items)

    def cancel(self):
        """Devolve unidades ao estoque e cancela a venda."""
        if self.status == "Cancelado":
            return
        for item in self.items:
            item.product.stock += item.quantity
        self.status = "Cancelado"

        if self.receivable:
            if self.receivable.status == "Pago":
                add_treasury_entry("Saida", self.receivable.amount, description=f"Reversão AR#{self.receivable.id}")
            self.receivable.status = "Cancelado"
        db.session.commit()

    def redo(self):
        """Reativa a venda se houver estoque suficiente."""
        if self.status != "Cancelado":
            return
        if any(item.product.stock < item.quantity for item in self.items):
            raise ValueError("Estoque insuficiente para refazer a venda.")
        for item in self.items:
            item.product.stock -= item.quantity
        self.status = "Pendente"
        if self.receivable:
            self.receivable.status = "Pendente"
        db.session.commit()

class SaleItem(db.Model):
    """Item que relaciona venda, produto, quantidade e subtotal."""
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

class AccountReceivable(db.Model):
    """Valor que o cliente ainda precisa pagar."""
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pendente')
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.String(250))

class AccountPayable(db.Model):
    """Valor que a empresa precisa pagar ao fornecedor."""
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    description = db.Column(db.String(250))
    due_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pendente')
    payment_date = db.Column(db.Date)
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.String(250))

class TreasuryEntry(db.Model):
    """Entrada ou saída de dinheiro registrada no caixa."""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(10), nullable=False)  # Entrada ou Saida
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(250))
    origin = db.Column(db.String(50))
    origin_id = db.Column(db.Integer)

    @staticmethod
    def global_balance():
        """Soma todas as entradas e subtrai todas as saídas."""
        return db.session.query(
            func.sum(
                case(
                    (TreasuryEntry.type == 'Entrada', TreasuryEntry.amount),
                    else_=-TreasuryEntry.amount
                )
            )
        ).scalar() or 0
    
    @staticmethod

    def add_manual(entry_type, amount, description):
        """Cria uma entrada ou saída manual do caixa."""
        te = TreasuryEntry(
            date=datetime.now(),
            type=entry_type,
            amount=fmt(amount),
            description=description,
            origin='Automatico via Sistema'
        )
        db.session.add(te)
        db.session.commit()
        return te
    
    def add_fixedcosts(entry_type, amount, description):
        """Grava no caixa uma despesa fixa."""
        te = TreasuryEntry(
            date=datetime.now(),
            type=entry_type,
            amount=fmt(amount),
            description=description,
            origin='Custo Fixo'
        )
        db.session.add(te)
        db.session.commit()
        return te
    
class FixedCost(db.Model):
    """Despesa recorrente, como aluguel ou energia."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_day = db.Column(db.Integer, default=5)


# ----------------------------
# MODELOS DE SEGURANÇA
# ----------------------------

class Role(db.Model):
    """Perfil de permissão do usuário: Admin, Gerente ou Caixa."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)  # Admin, Gerente, Caixa

class User(db.Model, UserMixin):
    """Usuário autenticado, com hash da senha e perfil de acesso."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(255))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role')

    def set_password(self, password):
        """Transforma a senha em hash antes de armazenar."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Compara a senha enviada com o hash guardado."""
        return check_password_hash(self.password_hash, password)


