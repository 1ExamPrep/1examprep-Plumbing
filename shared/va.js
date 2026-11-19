/* Small page behaviour for the listing pages: footer year, one FAQ open at a time. */
(function(){
  "use strict";
  document.querySelectorAll("[data-year]").forEach(function(el){el.textContent=new Date().getFullYear();});
  document.querySelectorAll(".faq details").forEach(function(d){d.addEventListener("toggle",function(){if(d.open)d.parentNode.querySelectorAll("details").forEach(function(o){if(o!==d)o.open=false;});});});
})();
/* Two-step license finder on the home page: pick a type, then a license, and go straight to its page. */
(function(){
  var f=document.querySelector("[data-finder]");if(!f)return;
  var g=f.querySelector("[data-fg]"),l=f.querySelector("[data-fl]"),all=[].slice.call(l.options);
  function fill(){var v=g.value;l.innerHTML="";all.forEach(function(o){if(o.getAttribute("data-g")===v)l.appendChild(o);});}
  g.addEventListener("change",fill);fill();
  f.addEventListener("submit",function(e){e.preventDefault();if(l.value)location.href=l.value;});
})();
/* Mark the current license in the side index. */
(function(){var p=location.pathname.replace(/index\.html$/,"");document.querySelectorAll(".tx-rail a").forEach(function(a){var h=a.pathname.replace(/index\.html$/,"");if(h!=="/"&&p.indexOf(h)===0)a.setAttribute("aria-current","page");});})();
/* State card pictures come from the store; show the logo mark if one fails to load. */
(function(){document.querySelectorAll(".hv-st-img img").forEach(function(i){function f(){if(i.dataset.fb)return;i.dataset.fb=1;i.src="/shared/logo-mark.png";}i.addEventListener("error",f);if(i.complete&&!i.naturalWidth)f();});})();
/* Español / English switch: opens this page through Google Translate, and back. */
(function(){var a=document.querySelectorAll("[data-lang]");if(!a.length)return;var h=location.hostname,p=location.pathname+location.hash;
var home="passyourplumbingexam.com",inGT=/\.translate\.goog$/.test(h);
a.forEach(function(el){var t=el.querySelector("span");
 if(inGT){el.href="https://"+home+p;el.removeAttribute("hreflang");el.lang="en";el.setAttribute("aria-label","View this page in English");if(t)t.textContent="English";}
 else{var host=(h&&h.indexOf(".")>0&&!/^(localhost|127\.)/.test(h))?h:home;
  el.href="https://"+host.replace(/-/g,"--").replace(/\./g,"-")+".translate.goog"+location.pathname+"?_x_tr_sl=en&_x_tr_tl=es&_x_tr_hl=es"+location.hash;}});})();
