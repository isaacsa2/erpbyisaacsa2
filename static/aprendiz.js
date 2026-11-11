// O código da API é tratado como TEXTO. Não executamos o código mostrado.
(() => {
  const root=document.getElementById("erp-aprendiz");
  if(!root)return;
  const open=root.querySelector("[data-aprendiz-open]");
  const close=root.querySelector("[data-aprendiz-close]");
  const panel=root.querySelector("[data-aprendiz-panel]");
  const tabs=root.querySelector("[data-aprendiz-tabs]");
  const code=root.querySelector("[data-aprendiz-code]");
  const title=root.querySelector("[data-aprendiz-title]");
  const concept=root.querySelector("[data-aprendiz-concept]");
  const path=root.querySelector("[data-aprendiz-path]");
  const link=root.querySelector("[data-aprendiz-github]");
  const copy=root.querySelector("[data-aprendiz-copy]");
  let sections=[], selected=0;
  function show(index){
    const s=sections[index];
    if(!s)return;
    selected=index;
    code.textContent=s.codigo;
    path.textContent=s.arquivo+" — linhas "+s.inicio+" a "+s.fim;
    link.href=s.github;
    [...tabs.children].forEach((el,i)=>el.setAttribute("aria-selected",String(i===index)));
  }
  open.addEventListener("click",async()=>{
    panel.hidden=false;
    open.setAttribute("aria-expanded","true");
    code.textContent="Lendo arquivos reais do ERP...";
    try{
      const url=new URL(root.dataset.api,window.location.href);
      url.searchParams.set("pagina",root.dataset.pagina);
      const res=await fetch(url.toString(),{credentials:"same-origin"});
      if(!res.ok)throw Error("HTTP "+res.status);
      const data=await res.json();
      title.textContent=data.pagina;
      concept.textContent=data.conceito+" "+data.aviso;
      tabs.replaceChildren();
      sections=data.secoes;
      sections.forEach((s,i)=>{
        const button=document.createElement("button");
        button.type="button";
        button.className="aprendiz-tab";
        button.textContent=s.titulo;
        button.setAttribute("role","tab");
        button.addEventListener("click",()=>show(i));
        tabs.appendChild(button);
      });
      show(0);
    }catch(e){code.textContent="Não foi possível mostrar o código desta tela."; }
    close.focus();
  });
  function hide(){panel.hidden=true;open.setAttribute("aria-expanded","false");open.focus();}
  close.addEventListener("click",hide);
  document.addEventListener("keydown",e=>{if(e.key==="Escape"&&!panel.hidden)hide();});
  copy.addEventListener("click",async()=>{
    if(!sections[selected])return;
    try{await navigator.clipboard.writeText(sections[selected].codigo);copy.textContent="Copiado!";}
    catch(e){copy.textContent="Selecione o código para copiar";}
  });
})();