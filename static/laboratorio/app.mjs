import {
  somar, idade, classificarTriangulo, tabuada, parcelas, totalCarrinho,
  trocoCentavos, imc, numero, resumoArray
} from './logica.mjs';

const brl = cents => (cents / 100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
const decimal = value => Number(value).toLocaleString('pt-BR',{maximumFractionDigits:2});
const $ = id => document.getElementById(id);

function resultado(id, fn) {
  try { $(id).textContent = fn(); $(id).dataset.status = 'ok'; }
  catch (error) { $(id).textContent = error.message; $(id).dataset.status = 'erro'; }
}

function ligar(id, evento, callback) { $(id).addEventListener(evento,callback); }
function textoValidado(id) { return $(id).value; }

ligar('form-soma','submit', e => {
  e.preventDefault();
  resultado('resultado-soma',()=>`Resultado: ${decimal(somar(textoValidado('soma-a'),textoValidado('soma-b')))}`);
});
ligar('form-idade','submit', e => {
  e.preventDefault();
  resultado('resultado-idade',()=>`Idade: ${idade(textoValidado('nascimento'))} anos completos`);
});
ligar('form-triangulo','submit', e => {
  e.preventDefault();
  resultado('resultado-triangulo',()=>classificarTriangulo(textoValidado('lado-a'),textoValidado('lado-b'),textoValidado('lado-c')));
});
ligar('form-imc','submit', e => {
  e.preventDefault();
  resultado('resultado-imc',()=>{
    const r=imc(textoValidado('peso'),textoValidado('altura'));
    return `IMC: ${decimal(r.valor)} — ${r.categoria}. Apenas demonstração de lógica, não avaliação clínica.`;
  });
});
ligar('form-tabuada','submit',e => {
  e.preventDefault();
  resultado('resultado-tabuada',()=>tabuada(textoValidado('tabuada-numero'))
    .map(row=>`${decimal(numero(textoValidado('tabuada-numero')))} × ${row.fator} = ${decimal(row.resultado)}`).join('\n'));
});
ligar('form-parcelas','submit',e=>{
  e.preventDefault();
  resultado('resultado-parcelas',()=>parcelas(textoValidado('principal')).map(p=>
    `${p.n}x (juros fixos ${p.taxa}%): total ${brl(p.total)}; prestações ${p.prestacoes.map(brl).join(' + ')}`
  ).join('\n'));
});

// Exercício de arrays: os números ficam em estado temporário, sem banco.
let valores = [12, 8, 25];
function desenharArray() {
  $('array-valores').textContent = `[${valores.map(decimal).join(', ')}]`;
  const r = resumoArray(valores);
  $('resultado-array').textContent = valores.length ?
    `Quantidade: ${valores.length} | Soma: ${decimal(r.total)} | Média: ${decimal(r.media)} | Menor: ${decimal(r.menor)} | Maior: ${decimal(r.maior)}` : 'Array vazio. Adicione valores.';
}
ligar('form-array','submit',e=>{
  e.preventDefault(); resultado('aviso-array',()=>{
    if (valores.length >= 30) throw new Error('Máximo de 30 valores no exercício.');
    valores.push(numero(textoValidado('array-valor')));desenharArray();return 'Valor adicionado.';
  });
});
ligar('array-remover','click',()=>{valores.pop();desenharArray();$('aviso-array').textContent='Último item removido.';});
ligar('array-ordenar','click',()=>{valores.sort((a,b)=>a-b);desenharArray();$('aviso-array').textContent='Ordem numérica crescente.';});
ligar('array-limpar','click',()=>{valores=[];desenharArray();$('aviso-array').textContent='Array zerado.';});
desenharArray();

// PDV de estudos. Cálculo em centavos e estoque simulado, não realiza venda real.
const produtos = [
  {id:'pao',nome:'Pão',preco:100,estoque:12},
  {id:'suco',nome:'Suco',preco:850,estoque:8},
  {id:'bolo',nome:'Bolo',preco:1250,estoque:5},
  {id:'cafe',nome:'Café',preco:450,estoque:10},
];
let carrinho = [];
function desenharPDV() {
  const select = $('pdv-produto'), escolhido = select.value;
  select.replaceChildren();
  for (const produto of produtos) {
    const op = document.createElement('option');op.value=produto.id;
    op.textContent=`${produto.nome} — ${brl(produto.preco)} (estoque ${produto.estoque})`;
    select.append(op);
  }
  select.value = escolhido || produtos[0].id;
  const corpo = $('pdv-lista');corpo.replaceChildren();
  for (const [index,item] of carrinho.entries()) {
    const linha=document.createElement('li');linha.className='item-carrinho';
    const texto=document.createElement('span');texto.textContent=`${item.nome}: ${item.quantidade} × ${brl(item.preco)} = ${brl(item.preco*item.quantidade)}`;
    const btn=document.createElement('button');btn.type='button';btn.textContent='Remover';btn.className='btn btn-mini';
    btn.addEventListener('click',()=>{carrinho.splice(index,1);desenharPDV();});
    linha.append(texto,btn);corpo.append(linha);
  }
  if(!carrinho.length){const item=document.createElement('li');item.textContent='Nenhum produto no carrinho.';corpo.append(item);}
  $('pdv-total').textContent=brl(totalCarrinho(carrinho));
}
ligar('form-pdv','submit',e=>{
  e.preventDefault();resultado('resultado-pdv',()=>{
    const p = produtos.find(p=>p.id===$('pdv-produto').value);
    const qtd=numero($('pdv-quantidade').value);
    if(!Number.isSafeInteger(qtd)||qtd<1)throw new Error('Quantidade deve ser um inteiro positivo.');
    const noCarrinho=carrinho.find(x=>x.id===p.id);
    if(qtd+(noCarrinho?.quantidade||0)>p.estoque)throw new Error(`Estoque insuficiente de ${p.nome}.`);
    if(noCarrinho)noCarrinho.quantidade+=qtd;else carrinho.push({id:p.id,nome:p.nome,preco:p.preco,quantidade:qtd});
    desenharPDV();return `${qtd} unidade(s) adicionada(s).`;
  });
});
ligar('pdv-finalizar','click',()=>resultado('resultado-pdv',()=>{
  if(!carrinho.length) throw new Error('Adicione produtos antes de finalizar.');
  const total=totalCarrinho(carrinho);
  const recebido=textoValidado('pdv-pago');
  if(String(recebido).trim()==='') throw new Error('Informe o valor recebido.');
  const troco=trocoCentavos(recebido,total);
  for (const item of carrinho) produtos.find(p=>p.id===item.id).estoque-=item.quantidade;
  const quantidade=carrinho.reduce((acc,item)=>acc+item.quantidade,0);
  carrinho=[];desenharPDV();
  return `Venda simulada concluída: ${quantidade} itens, total ${brl(total)}. Troco: ${brl(troco)}.`;
}));
ligar('pdv-resetar','click',()=>{
  carrinho=[];
  produtos.forEach((p,i)=>p.estoque=[12,8,5,10][i]);
  desenharPDV();$('resultado-pdv').textContent='Estoque e carrinho reiniciados.';
});
desenharPDV();

// Tema 16: localStorage (persistência somente no navegador deste dispositivo).
const CHAVE = 'erp-isaac-aula16-notas-v1';
let notas = [];
let permitePersistencia = true;
try {
  const antigas = JSON.parse(localStorage.getItem(CHAVE) || '[]');
  if (Array.isArray(antigas)) notas=antigas.filter(v=>v&&typeof v.texto==='string'&&typeof v.id==='string').slice(0,100);
} catch { permitePersistencia=false; }
function salvarNotas(){
  if(!permitePersistencia)return;
  try {localStorage.setItem(CHAVE,JSON.stringify(notas));}
  catch {permitePersistencia=false;$('aviso-notas').textContent='Armazenamento local bloqueado; as anotações só duram até fechar a aba.';}
}
function desenharNotas(){
  const lista=$('lista-notas');lista.replaceChildren();
  for(const nota of notas){
    const linha=document.createElement('li');linha.className='nota';
    const texto=document.createElement('span');texto.textContent=nota.texto;
    const editar=document.createElement('button');editar.type='button';editar.textContent='Editar';editar.className='btn btn-mini';
    editar.addEventListener('click',()=>{
      $('nota-texto').value=nota.texto; $('nota-id').value=nota.id; $('nota-texto').focus();
    });
    const remover=document.createElement('button');remover.type='button';remover.textContent='Excluir';remover.className='btn btn-mini';
    remover.addEventListener('click',()=>{notas=notas.filter(n=>n.id!==nota.id);salvarNotas();desenharNotas();});
    const botoes=document.createElement('div');botoes.className='nota-botoes';botoes.append(editar,remover);
    linha.append(texto,botoes);lista.append(linha);
  }
  if(!notas.length){const item=document.createElement('li');item.textContent='Nenhuma nota salva ainda.';lista.append(item);}
}
ligar('form-nota','submit',e=>{
  e.preventDefault();resultado('aviso-notas',()=>{
    const texto=$('nota-texto').value.trim();
    if(texto.length<1||texto.length>500)throw new Error('A anotação precisa ter de 1 a 500 caracteres.');
    const id=$('nota-id').value;
    if(id){const antiga=notas.find(n=>n.id===id);if(antiga)antiga.texto=texto;}
    else {if(notas.length>=100)throw new Error('Limite de 100 notas.');notas.unshift({id:globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`,texto});}
    $('form-nota').reset();salvarNotas();desenharNotas();return permitePersistencia?'Anotação salva no navegador.':'Anotação salva só em memória.';
  });
});
ligar('nota-cancelar','click',()=>{$('form-nota').reset();$('aviso-notas').textContent='Edição cancelada.';});
desenharNotas();

// Filtro de módulos para facilitar o estudo e o trabalho em sala.
for(const botao of document.querySelectorAll('[data-filtro]')) {
  botao.addEventListener('click',()=>{
    const filtro=botao.dataset.filtro;
    document.querySelectorAll('[data-filtro]').forEach(b=>b.setAttribute('aria-pressed',String(b===botao)));
    for(const card of document.querySelectorAll('[data-categoria]')) card.hidden=filtro!=='todos'&&card.dataset.categoria!==filtro;
  });
}
