"""Exemplo extra de Algoritmos: decisão, repetição e funções de caixa."""
from decimal import Decimal, ROUND_HALF_UP


def calcular_total(itens):
    """Recebe pares (preço, quantidade) e devolve o total monetário."""
    total = Decimal("0.00")
    for preco, quantidade in itens:
        valor = Decimal(str(preco))
        if quantidade <= 0 or valor < 0:
            raise ValueError("Preço e quantidade devem ser válidos.")
        total += valor * quantidade
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def classificar_estoque(quantidade):
    if quantidade < 0:
        raise ValueError("Estoque não pode ser negativo")
    return "Reposição necessária" if quantidade < 10 else "Estoque suficiente"


if __name__ == "__main__":
    carrinho = [("6.00", 3), ("8.50", 2)]
    print("Carrinho:", carrinho)
    print("Total: R$", calcular_total(carrinho))
    print("Estoque de 4 unidades:", classificar_estoque(4))
