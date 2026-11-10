"""Testes de integração: executados no CI após instalar requirements.txt."""
import os
import unittest

# Sempre isola os testes: nenhuma conexão com o arquivo de uso do estudante.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ERP_SECRET_KEY"] = "somente-testes-nao-usar-em-producao"

from app import app
from models import db, User, Role, Customer, Product, TreasuryEntry, Sale


class TestWebERP(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.context = app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()
        admin = Role(name="Admin")
        caixa = Role(name="Caixa")
        db.session.add_all([admin, caixa, Role(name="Gerente")])
        db.session.flush()
        user = User(username="admin_teste", role=admin)
        user.set_password("teste-super-seguro-123")
        db.session.add_all([user,
            Customer(name="Cliente fictício", email="exemplo@exemplo.invalid"),
            Product(name="Sequilho teste", price=6.0, cost=3.0, stock=10)])
        db.session.commit()
        self.client = app.test_client()
        self.token = "token-de-teste"
        with self.client.session_transaction() as sess:
            sess["_csrf_token"] = self.token

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def login(self):
        result = self.client.post('/login', data={
            '_csrf_token': self.token, 'username':'admin_teste',
            'password':'teste-super-seguro-123'})
        self.assertEqual(result.status_code, 302)

    def test_login_e_laboratorio_sql(self):
        self.assertEqual(self.client.get('/login').status_code, 200)
        self.assertEqual(self.client.get('/aulas').status_code, 302)  # protegido
        self.login()
        response = self.client.get('/aulas')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'GROUP BY', response.data)
        self.assertIn(b'Sequilho teste', response.data)

    def test_protecao_csrf(self):
        self.login()
        response = self.client.post('/products', data={"name": "Produto sem CSRF"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Product.query.count(), 1)

    def test_estoque_zero_nao_muda(self):
        self.login()
        result = self.client.post('/pdv/add', data={
            '_csrf_token':self.token, 'product_id':1,'quantity':0})
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Product.query.first().stock,10)
        self.assertEqual(Sale.query.count(),0)

    def test_pdv_fim_a_fim(self):
        self.login()
        resp = self.client.post('/pdv/add', data={
            '_csrf_token': self.token,'product_id':1,'quantity':2})
        self.assertEqual(resp.status_code,302)
        self.assertEqual(Product.query.first().stock,8)
        resp = self.client.post('/pdv/finish', data={
            '_csrf_token': self.token,'customer_id':1,'payment_method':'Dinheiro'})
        self.assertEqual(resp.status_code,302)
        self.assertEqual(Sale.query.first().status,'Pago')
        self.assertEqual(TreasuryEntry.query.count(),1)
        self.assertEqual(TreasuryEntry.query.first().amount,12)

    def test_nao_pode_remover_item_de_outra_sessao(self):
        self.login()
        self.client.post('/pdv/add', data={
            '_csrf_token':self.token,'product_id':1,'quantity':1})
        with self.client.session_transaction() as sess:
            sess.pop('current_sale',None)
        self.assertEqual(self.client.post('/pdv/remove/1', data={'_csrf_token':self.token}).status_code,403)


if __name__ == '__main__':
    unittest.main()
