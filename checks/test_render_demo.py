"""Testes específicos do modo de visualização pública da Render."""
import os
import unittest

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ERP_DEMO_MODE"] = "1"
os.environ["ERP_SECRET_KEY"] = "teste-exclusivo-do-ci"
from app import app, initialize_demo
from models import db, User, Product

class DemoRenderTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.ctx = app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        initialize_demo()
        self.client = app.test_client()
        self.client.get("/login")
        with self.client.session_transaction() as session:
            self.csrf = session["_csrf_token"]

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_somente_consulta(self):
        self.assertEqual(self.client.get("/healthz").status_code, 200)
        self.assertEqual(self.client.get("/login").status_code, 200)
        self.assertEqual(self.client.post("/login", data={"_csrf_token": self.csrf,
            "username": "admin", "password": "admin"}).status_code, 302)
        self.assertEqual(User.query.filter_by(username="admin").first().role.name, "Gerente")
        self.assertEqual(self.client.get("/products").status_code, 200)
        self.assertEqual(self.client.get("/aulas").status_code, 200)
        count = Product.query.count()
        self.assertEqual(self.client.post("/products", data={
            "_csrf_token": self.csrf, "name": "não permitido"}).status_code, 403)
        self.assertEqual(self.client.post("/register", json={"username": "invasor"},
            headers={"X-CSRF-Token": self.csrf}).status_code, 403)
        self.assertEqual(Product.query.count(), count)
        self.assertEqual(self.client.post("/logout", data={"_csrf_token": self.csrf}).status_code, 302)
