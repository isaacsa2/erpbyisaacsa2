"""Gerador de dados fictícios para experimentar o ERP.
Use somente em banco de testes e verifique os parâmetros antes de executar.
"""

import math
import random
from datetime import datetime, timedelta, date
from faker import Faker
from app import app, db
from models import (
    Customer, Product, Sale, SaleItem,
    AccountReceivable, AccountPayable,
    TreasuryEntry, Supplier, fmt
)

# Faker cria nomes e endereços inventados; não use dados reais das pessoas.
fake = Faker("pt_BR")

# -------------------------------------------------------
# Constantes
# -------------------------------------------------------
VENDAS_POR_DIA = 15

PRODUTOS = [
    {"name": "Sequilho Tradicional 100g",        "category": "Principal", "cost": 3.80, "price": 6.00,  "stock": 10000},
    {"name": "Sequilho Tradicional 250g",        "category": "Principal", "cost": 8.81, "price": 13.00, "stock": 10000},
    {"name": "Sequilho com Coco 100g",           "category": "Principal", "cost": 3.75, "price": 6.00,  "stock": 10000},
    {"name": "Sequilho com Goiabada 100g",       "category": "Principal", "cost": 3.95, "price": 6.00,  "stock": 10000},
    {"name": "Sequilhos Premium (Castanha) 100g","category": "Principal", "cost": 5.45, "price": 8.90,  "stock": 10000},
]

DESPESAS_FIXAS = [
    ("Aluguel",          1200.00, 1200.00),
    ("Energia Elétrica",  180.00,  320.00),
    ("Água e Esgoto",      60.00,  100.00),
    ("Internet",           99.90,   99.90),
    ("Contador",          350.00,  350.00),
    ("Telefone",           79.90,  120.00),
]

FORNECEDORES = [
    {"name": "Distribuidora Grão & Cia",      "contact": "Carlos Mendes",  "phone": "71 99001-1234", "cnpj": "12.345.678/0001-90"},
    {"name": "Ingredientes do Nordeste Ltda", "contact": "Patrícia Lima",  "phone": "71 98712-4567", "cnpj": "98.765.432/0001-10"},
    {"name": "Embalagens Rápidas ME",         "contact": "Roberto Souza",  "phone": "71 99345-8901", "cnpj": "11.222.333/0001-44"},
]

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
BATCH_SIZE = 500  # commit a cada N registros pesados

def _commit_batch(contador, label="registros"):
    """Commita e imprime progresso a cada BATCH_SIZE."""
    if contador % BATCH_SIZE == 0:
        db.session.commit()
        print(f"   ↳ {contador} {label} inseridos...", flush=True)

# -------------------------------------------------------
# seed_fornecedores
# -------------------------------------------------------
def seed_fornecedores():
    """Insere fornecedores inventados se o CNPJ ainda não estiver cadastrado."""
    criados = 0
    for f in FORNECEDORES:
        if not Supplier.query.filter_by(cnpj=f["cnpj"]).first():
            db.session.add(Supplier(
                name=f["name"], contact=f["contact"],
                phone=f["phone"], cnpj=f["cnpj"],
                address=fake.address()
            ))
            criados += 1
    db.session.commit()
    print(f"✅ {criados} fornecedor(es) criado(s).")

# -------------------------------------------------------
# seed_products
# -------------------------------------------------------
def seed_products():
    """Insere produtos demonstrativos sem repetir os existentes."""
    criados = 0
    for p in PRODUTOS:
        if not Product.query.filter_by(name=p["name"]).first():
            db.session.add(Product(
                name=p["name"], category=p["category"],
                cost=p["cost"], price=p["price"], stock=p["stock"]
            ))
            criados += 1
    db.session.commit()
    print(f"✅ {criados} produto(s) criado(s).")

# -------------------------------------------------------
# seed_customers_only
# -------------------------------------------------------
def seed_customers_only(num_customers=150):
    """Cria clientes fictícios para testes de cadastro e listagem."""
    used_emails = set()
    objs = []
    for _ in range(num_customers):
        email = fake.email()
        while email in used_emails or Customer.query.filter_by(email=email).first():
            email = fake.email()
        used_emails.add(email)
        objs.append(Customer(
            name=fake.name(), email=email,
            phone=fake.phone_number(), address=fake.address()
        ))

    # bulk_save_objects é muito mais rápido que add() em loop
    db.session.bulk_save_objects(objs)
    db.session.commit()
    print(f"✅ {len(objs)} clientes criados.")

# -------------------------------------------------------
# seed_despesas_fixas
# -------------------------------------------------------
def seed_despesas_fixas(dias):
    """Simula despesas recorrentes no período solicitado."""
    today = datetime.now()
    start = today - timedelta(days=dias - 1)
    current = start.replace(day=1)
    meses = 0
    objs = []

    while current <= today:
        for descricao, vmin, vmax in DESPESAS_FIXAS:
            dia_vcto = random.randint(5, 10)
            try:
                lancamento = current.replace(day=dia_vcto)
            except ValueError:
                lancamento = current
            if start <= lancamento <= today:
                objs.append(TreasuryEntry(
                    date=lancamento,
                    type="Saida",
                    amount=fmt(round(random.uniform(vmin, vmax), 2)),
                    description=descricao,
                    origin="Despesa Fixa"
                ))
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
        meses += 1

    db.session.bulk_save_objects(objs)
    db.session.commit()
    print(f"✅ Despesas fixas lançadas em {meses} mês(es). ({len(objs)} registros)")

# -------------------------------------------------------
# seed_compras_estoque
# -------------------------------------------------------
def seed_compras_estoque(dias, inadimplencia_rate=0.05):
    """Gera compras e movimentações fictícias de estoque."""
    today = datetime.now()
    start = today - timedelta(days=dias - 1)

    fornecedores = Supplier.query.all()
    produtos = Product.query.all()
    if not fornecedores or not produtos:
        print("⚠️ Sem fornecedores/produtos para gerar compras.")
        return

    datas_compra = []
    current = start
    while current <= today:
        datas_compra.append(current)
        current += timedelta(days=random.randint(10, 18))

    payables = []
    treasury = []

    for data_compra in datas_compra:
        supplier = random.choice(fornecedores)
        produto = random.choice(produtos)
        quantidade = random.randint(50, 300)
        valor_total = fmt(round(produto.cost * quantidade, 2))
        due = (data_compra + timedelta(days=30)).date()
        pago = random.random() > inadimplencia_rate

        payables.append(AccountPayable(
            supplier_id=supplier.id,
            description=f"Compra: {quantidade}x {produto.name}",
            due_date=due,
            amount=valor_total,
            status="Pago" if pago else "Pendente",
            payment_date=due if pago else None,
            payment_method="Transferência" if pago else None
        ))

        if pago:
            data_pgto = data_compra + timedelta(days=random.randint(25, 35))
            if data_pgto > today:
                data_pgto = today
            treasury.append(TreasuryEntry(
                date=data_pgto,
                type="Saida",
                amount=valor_total,
                description=f"Compra estoque: {produto.name} ({quantidade} un.) — {supplier.name}",
                origin="Compra Estoque"
            ))

    db.session.bulk_save_objects(payables)
    db.session.bulk_save_objects(treasury)
    db.session.commit()
    print(f"✅ {len(payables)} compra(s) de estoque gerada(s).")

# -------------------------------------------------------
# seed_sales_last_n_days  ← parte mais pesada, usa batch
# -------------------------------------------------------
def seed_sales_last_n_days(num_sales=100, inadimplencia_rate=0.10):
    """Simula um histórico de vendas para relatórios."""
    customers = Customer.query.all()
    products  = Product.query.all()

    if not customers or not products:
        print("⚠️ Cadastre clientes e produtos antes de gerar vendas!")
        return

    dias = max(30, math.ceil(num_sales / VENDAS_POR_DIA))
    meses = round(dias / 30)
    print(f"📅 Distribuindo {num_sales} vendas em {dias} dias (~{meses} {'mês' if meses == 1 else 'meses'})...")

    today = datetime.now()
    vendas_criadas = 0

    for i in range(num_sales):
        customer   = random.choice(customers)
        sale_date  = today - timedelta(days=random.randint(0, dias - 1))
        a_vista    = random.random() < 0.8

        sale = Sale(
            customer_id=customer.id,
            status="Pago" if a_vista else "Pendente",
            date=sale_date
        )
        db.session.add(sale)
        db.session.flush()  # precisa do sale.id para os items

        chosen = random.sample(products, min(random.randint(1, 4), len(products)))
        total = 0

        items = []
        for product in chosen:
            qty = random.randint(1, 5)
            if product.stock >= qty:
                subtotal = product.price * qty
                items.append(SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=qty,
                    subtotal=subtotal
                ))
                product.stock -= qty
                total += subtotal

        if not items or total == 0:
            continue

        db.session.bulk_save_objects(items)

        if a_vista:
            db.session.add(TreasuryEntry(
                date=sale_date, type="Entrada",
                amount=fmt(total),
                description=f"Venda PDV #{sale.id}",
                origin="sale", origin_id=sale.id
            ))
        else:
            due_date = sale_date + timedelta(days=random.choice([15, 30]))
            recebido = random.random() > inadimplencia_rate
            db.session.add(AccountReceivable(
                customer_id=customer.id,
                sale_id=sale.id,
                amount=total,
                due_date=due_date.date(),
                status="Pago" if recebido else "Pendente"
            ))
            if recebido:
                pgto = due_date + timedelta(days=random.randint(-2, 3))
                db.session.add(TreasuryEntry(
                    date=pgto, type="Entrada",
                    amount=fmt(total),
                    description=f"Recebimento venda #{sale.id}",
                    origin="sale", origin_id=sale.id
                ))

        vendas_criadas += 1

        # Commit em lote para não acumular tudo na memória
        if vendas_criadas % BATCH_SIZE == 0:
            db.session.commit()
            print(f"   ↳ {vendas_criadas}/{num_sales} vendas...", flush=True)

    db.session.commit()
    print(f"✅ {vendas_criadas} vendas simuladas.")

# -------------------------------------------------------
# seed_all
# -------------------------------------------------------
def seed_all(num_customers=150, num_sales=300, reset_db=False):
    """Executa as etapas de geração de dados; confira a opção reset_db."""
    if reset_db:
        db.drop_all()
        db.create_all()
        print("🗑️  Banco resetado.")

    dias = max(30, math.ceil(num_sales / VENDAS_POR_DIA))

    seed_customers_only(num_customers)
    seed_fornecedores()
    seed_products()
    seed_sales_last_n_days(num_sales)
    seed_despesas_fixas(dias)
    seed_compras_estoque(dias)
    print("🎉 Seed concluído!")

if __name__ == "__main__":
    with app.app_context():
        seed_all(num_customers=20, num_sales=40, reset_db=False)
