"""Garante que cada função, template e modelo do Modo Aprendiz é real."""
import unittest
from pathlib import Path
from aprendiz import CATALOG, real_python, real_text

class RealCodeTests(unittest.TestCase):
    def test_catalogo_mapeia_codigo_real(self):
        for page, (title, function, template, models, explanation) in CATALOG.items():
            with self.subTest(page=page):
                self.assertIn("def "+function, real_python("erp.py",function)["codigo"])
                self.assertTrue(real_text("templates/"+template)["codigo"])
                for model in models:
                    self.assertIn("class "+model,real_python("models.py",model,"class")["codigo"])
