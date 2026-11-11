"""Testa a conta pública Admin, operações de escrita e reset do banco de demonstração."""
import os
import unittest

os.environ["ERP_DEMO_MODE"] = "1"
os.environ["ERP_DEMO_ADMIN_MODE"] = "1"
os.environ["ERP_DEMO_PASSWORD"] = "admin"
os.environ["ERP_SECRET_KEY"] = "chave-usada-apenas-nos-testes"
os.environ["DATABASE_URL"] = "sqlite:///banco_externo_que_nao_deve_ser_utilizado.db"

from app import app, initialize_storage
from models import db, Product, User


class DemoAdminTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.ctx = app.app_context()
        self.ctx.push()
        initialize_storage()
        self.client = app.test_client()
        self.client.get("/login")
        with self.client.session_transaction() as session:
            self.csrf = session["_csrf_token"]

    def tearDown(self):
        db.session.remove()
        self.ctx.pop()

    def login(self):
        r = self.client.post("/login", data={"_csrf_token": self.csrf, "username": "admin", "password": "admin"})
        self.assertEqual(r.status_code, 302)

    def test_admin_pode_cadastrar_e_resetar(self):
        self.assertEqual(app.config["SQLALCHEMY_DATABASE_URI"], "sqlite:///erp_demo_publica.db")
        self.assertEqual(User.query.filter_by(username="admin").one().role.name, "Admin")
        self.login()
        initial = Product.query.count()
        r = self.client.post("/products", data={"_csrf_token": self.csrf, "name": "Caderno da turma",
            "category": "Aula", "price": "12.5", "cost_price": "4.5", "stock": "10"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Product.query.count(), initial+1)
        initialize_storage()
        self.assertEqual(Product.query.count(), initial)
        self.assertIsNone(Product.query.filter_by(name="Caderno da turma").first())

    def test_admin_pode_gerenciar_usuarios(self):
        self.login()
        r=self.client.post("/register", json={"username":"aluno_ficticio",
            "password":"senha-de-teste-123","role":"Caixa"},headers={"X-CSRF-Token":self.csrf})
        self.assertEqual(r.status_code,201)
        self.assertEqual(User.query.filter_by(username="aluno_ficticio").one().role.name,"Caixa")
