"""Testes da demonstração pública: Admin completo e SQLite recriado no boot."""
import os
import unittest

# Mesmo que DATABASE_URL aponte para outro banco, a demo usa seu próprio SQLite.
os.environ["DATABASE_URL"] = "sqlite:///nao_apagar_erp_real.sqlite3"
os.environ["ERP_DEMO_MODE"] = "1"
os.environ["ERP_DEMO_PASSWORD"] = "admin"
os.environ["ERP_SECRET_KEY"] = "chave-apenas-para-testes"

from app import app, initialize_demo, reset_demo_database
from models import db, User, Product


class DemoRenderTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.ctx = app.app_context()
        self.ctx.push()
        reset_demo_database()
        self.client = app.test_client()
        self.client.get("/login")
        with self.client.session_transaction() as sess:
            self.csrf = sess["_csrf_token"]

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def login(self):
        return self.client.post("/login", data={
            "_csrf_token": self.csrf, "username": "admin", "password": "admin"
        })

    def test_banco_exclusivo_nao_usa_database_url(self):
        self.assertEqual(db.engine.url.get_backend_name(), "sqlite")
        self.assertIn("erp_demo_faculdade.sqlite3", str(db.engine.url))
        self.assertNotIn("nao_apagar_erp_real", str(db.engine.url))

    def test_admin_pode_cadastrar_e_gerenciar(self):
        self.assertEqual(self.client.get("/healthz").status_code, 200)
        self.assertEqual(self.login().status_code, 302)
        admin = User.query.filter_by(username="admin").first()
        self.assertEqual(admin.role.name, "Admin")
        self.assertTrue(admin.check_password("admin"))
        self.assertEqual(self.client.get("/products").status_code, 200)
        self.assertEqual(self.client.get("/aulas").status_code, 200)
        before = Product.query.count()
        response = self.client.post("/products", data={
            "_csrf_token": self.csrf, "name": "Produto da turma",
            "category": "Aula", "price": "25", "cost_price": "11", "stock": "7"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.query.count(), before + 1)
        self.assertIsNotNone(Product.query.filter_by(name="Produto da turma").first())

        # Esta rota exige Admin e agora aceita cadastro de usuários na demo.
        r = self.client.post("/register", json={
            "username": "colega", "password": "senha-didatica-123", "role": "Caixa"
        }, headers={"X-CSRF-Token": self.csrf})
        self.assertEqual(r.status_code, 201)
        self.assertIsNotNone(User.query.filter_by(username="colega").first())

    def test_reinicio_apaga_edicoes_e_recria_admin(self):
        self.assertEqual(self.login().status_code, 302)
        self.client.post("/products", data={
            "_csrf_token": self.csrf, "name": "Vai desaparecer",
            "category": "Teste", "price": "5", "cost_price": "2", "stock": "4"
        })
        self.assertIsNotNone(Product.query.filter_by(name="Vai desaparecer").first())
        reset_demo_database()
        self.assertIsNone(Product.query.filter_by(name="Vai desaparecer").first())
        self.assertGreater(Product.query.count(), 0)
        admin = User.query.filter_by(username="admin").first()
        self.assertEqual(admin.role.name, "Admin")
        self.assertTrue(admin.check_password("admin"))

    def test_csrf_ainda_exigido(self):
        self.login()
        before = Product.query.count()
        r = self.client.post("/products", data={"name": "sem token", "price": "1"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Product.query.count(), before)
