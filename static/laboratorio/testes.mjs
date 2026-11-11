import assert from 'node:assert/strict';
import test from 'node:test';
import { somar, idade, classificarTriangulo, tabuada, parcelas, precoCentavos,
  totalCarrinho, trocoCentavos, imc, resumoArray } from './logica.mjs';

test('soma e validação de entrada', () => {
  assert.equal(somar('2,5','3'), 5.5);
  assert.throws(() => somar('', 3));
  assert.throws(() => somar('abc', 3));
});
test('idade desconta aniversário ainda não ocorrido', () => {
  assert.equal(idade('2000-12-30', new Date(2026, 10, 10)), 25);
  assert.equal(idade('2000-10-30', new Date(2026, 10, 10)), 26);
  assert.throws(() => idade('2027-01-01', new Date(2026,10,10)));
  assert.throws(() => idade('2026-02-30', new Date(2026,10,10)));
});
test('triângulos: validação e classificação', () => {
  assert.equal(classificarTriangulo(3,3,3), 'Equilátero');
  assert.equal(classificarTriangulo(3,3,4), 'Isósceles');
  assert.equal(classificarTriangulo(3,4,5), 'Escaleno');
  assert.equal(classificarTriangulo(1,1,3), 'Não forma um triângulo');
  assert.throws(() => classificarTriangulo(-1,3,3));
});
test('tabuada contém 10 operações', () => {
  assert.equal(tabuada(5).length,10);
  assert.equal(tabuada(5)[9].resultado, 50);
  assert.throws(() => tabuada('1.1'));
});
test('juros: parcelas distribuem centavos sem perda', () => {
  const planos = parcelas(1000);
  assert.deepEqual(planos.map(p=>p.total),[110000,115000,120000,125000]);
  for (const p of planos) assert.equal(p.prestacoes.reduce((a,b)=>a+b,0),p.total);
});
test('PDV em centavos evita erro de ponto flutuante', () => {
  assert.equal(precoCentavos('1,10'),110);
  assert.equal(totalCarrinho([{preco:110,quantidade:3},{preco:50,quantidade:1}]),380);
  assert.equal(trocoCentavos('5',380),120);
  assert.throws(() => trocoCentavos('3',380));
  assert.throws(() => totalCarrinho([{preco:100,quantidade:0}]));
});
test('IMC segue faixas didáticas dos slides, não diagnóstico', () => {
  assert.equal(imc(70,1.75).categoria,'Peso normal');
  assert.equal(imc(120,1.70).categoria,'Obesidade grau 3');
  assert.throws(() => imc(0,1.75));
});
test('arrays: reduções corretas e caso vazio', () => {
  assert.equal(resumoArray([2,4,6]).media,4);
  assert.equal(resumoArray([]).media,null);
});
