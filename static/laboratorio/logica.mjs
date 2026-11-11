/**
 * FUNÇÕES DOS EXERCÍCIOS
 * Este arquivo contém somente os cálculos. Não depende dos botões HTML.
 * Cada função recebe uma entrada, executa uma regra e devolve o resultado.
 * O app.mjs usa import para acessar estas funções.
 * Veja docs/GUIA_PARA_INICIANTES.md para acompanhar um exemplo completo.
 */
// Os campos HTML fornecem texto. Convertemos para número e validamos.
export function numero(valor) {
  if (valor === null || String(valor).trim() === "") throw new Error("Informe um número.");
  // Aceita o formato brasileiro: "2,5" vira "2.5" antes da conversão.
  const n = Number(String(valor).replace(",", "."));
  if (!Number.isFinite(n)) throw new Error("Use um número válido.");
  return n;
}

// Soma dois números. Sem conversão, "2" + "3" seria o texto "23".
export function somar(a, b) {
  return numero(a) + numero(b);
}

// Datas: apenas subtrair os anos não basta; conferimos o aniversário.
export function idade(dataISO, hoje = new Date()) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dataISO)) throw new Error("Escolha uma data de nascimento.");
  const [ano, mes, dia] = dataISO.split("-").map(Number);
  const data = new Date(ano, mes - 1, dia);
  if (data.getFullYear() !== ano || data.getMonth() !== mes - 1 || data.getDate() !== dia)
    throw new Error("Data de nascimento inválida.");
  const hojeDia = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  if (data > hojeDia) throw new Error("A data não pode estar no futuro.");
  let anos = hoje.getFullYear() - ano;
  if (hoje.getMonth() + 1 < mes || (hoje.getMonth() + 1 === mes && hoje.getDate() < dia)) anos--;
  return anos;
}

// Decisão: valida os três lados antes de classificar o triângulo.
export function classificarTriangulo(a, b, c) {
  const lados = [numero(a), numero(b), numero(c)];
  if (lados.some(n => n <= 0)) throw new Error("Os três lados devem ser positivos.");
  lados.sort((x, y) => x - y);
  if (lados[0] + lados[1] <= lados[2]) return "Não forma um triângulo";
  if (lados[0] === lados[2]) return "Equilátero";
  if (lados[0] === lados[1] || lados[1] === lados[2]) return "Isósceles";
  return "Escaleno";
}

// Repetição: construímos dez linhas sem copiar e colar dez multiplicações.
export function tabuada(valor) {
  const n = numero(valor);
  if (!Number.isSafeInteger(n) || Math.abs(n) > 1000) throw new Error("Use um número inteiro entre -1000 e 1000.");
  return Array.from({ length: 10 }, (_, idx) => ({ fator: idx + 1, resultado: n * (idx + 1) }));
}

// Parcelamento fictício: cada plano possui quantidade de parcelas e taxa fixa.
// Usamos centavos inteiros para não perder um centavo ao dividir os valores.
export function parcelas(principalReais) {
  const p = numero(principalReais);
  if (!(p > 0) || p > 1000000) throw new Error("Informe valor maior que zero e até R$ 1.000.000.");
  const centavos = Math.round((p + Number.EPSILON) * 100);
  return [[3, 10], [6, 15], [9, 20], [12, 25]].map(([n, taxa]) => {
    // Juros simples fixos para cada plano. Parcelas inteiras em centavos.
    const total = Math.round(centavos * (1 + taxa / 100));
    const valorBase = Math.floor(total / n);
    const resto = total % n;
    const prestacoes = Array.from({length:n},(_,i)=>valorBase+(i<resto?1:0));
    return { n, taxa, total, prestacoes };
  });
}

// PDV: R$ 1,10 é guardado como 110 centavos para evitar erros de precisão.
export function precoCentavos(reais) {
  const n = numero(reais);
  if (n < 0 || n > 1000000) throw new Error("Preço fora do limite do exercício.");
  return Math.round((n + Number.EPSILON) * 100);
}

// reduce percorre os itens e soma: quantidade × preço de cada produto.
export function totalCarrinho(itens) {
  return itens.reduce((acc, item) => {
    if (!Number.isSafeInteger(item.quantidade) || item.quantidade <= 0 ||
        !Number.isSafeInteger(item.preco) || item.preco < 0)
      throw new Error("Item inválido no carrinho.");
    return acc + item.quantidade * item.preco;
  }, 0);
}

export function trocoCentavos(pagoEmReais, total) {
  const pago = precoCentavos(pagoEmReais);
  if (!Number.isSafeInteger(total) || total < 0) throw new Error("Total inválido.");
  if (pago < total) throw new Error("O valor recebido é menor que o total.");
  return pago - total;
}

// Condições encadeadas: exemplo apenas didático, não substitui avaliação clínica.
export function imc(peso, altura) {
  const p = numero(peso), h = numero(altura);
  if (p <= 0 || h <= 0 || h > 3 || p > 500) throw new Error("Confira peso (kg) e altura (m).");
  const valor = p / (h * h);
  const categoria = valor < 18.5 ? "Baixo peso" : valor < 25 ? "Peso normal" :
    valor < 30 ? "Sobrepeso" : valor < 35 ? "Obesidade grau 1" :
    valor < 40 ? "Obesidade grau 2" : "Obesidade grau 3";
  return { valor, categoria };
}

// Array é uma lista: calculamos total, média, maior e menor de seus elementos.
export function resumoArray(valores) {
  if (!valores.length) return { total: 0, media: null, maior: null, menor: null };
  return { total: valores.reduce((a,b)=>a+b,0), media: valores.reduce((a,b)=>a+b,0)/valores.length,
    maior: Math.max(...valores), menor: Math.min(...valores) };
}
