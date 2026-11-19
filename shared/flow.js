/* Plumbing Flow (design 7): moving water behind the page hero, and sections that rise into view.
   Decoration only: every word on the page is in the HTML, so the page reads the same with this script off.
   Respects prefers-reduced-motion (one still frame, no reveal animation) and pauses when the hero is off screen. */
(function () {
  var still = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  function water(hero) {
    var cv = hero.querySelector(".pf-water");
    if (!cv) { cv = document.createElement("canvas"); cv.className = "pf-water"; cv.setAttribute("aria-hidden", "true"); hero.insertBefore(cv, hero.firstChild); }
    var gl = cv.getContext("webgl", { antialias: false, premultipliedAlpha: false });
    if (!gl) return;
    var vs = "attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}";
    var fs = "precision highp float;uniform vec2 r;uniform float t;uniform vec2 m;" +
      "void main(){vec2 uv=gl_FragCoord.xy/r;uv.x*=r.x/r.y;uv+=m*.04;" +
      "float tt=t*.35+23.;vec2 p=mod(uv*5.2,6.28318)-250.;vec2 i=p;float c=1.;float inten=.005;" +
      "for(int n=0;n<5;n++){float t2=tt*(1.-(3.5/float(n+1)));i=p+vec2(cos(t2-i.x)+sin(t2+i.y),sin(t2-i.y)+cos(t2+i.x));" +
      "c+=1./length(vec2(p.x/(sin(i.x+t2)/inten),p.y/(cos(i.y+t2)/inten)));}" +
      "c/=5.;c=1.17-pow(c,1.4);float k=pow(abs(c),8.);" +
      "vec2 q=gl_FragCoord.xy/r;vec3 base=mix(vec3(.008,.05,.11),vec3(.02,.2,.38),q.y*.8+q.x*.3);" +
      "gl_FragColor=vec4(base+vec3(.3,.78,1.)*clamp(k,0.,1.)*1.1,1.);}";
    function sh(type, src) { var o = gl.createShader(type); gl.shaderSource(o, src); gl.compileShader(o); return o; }
    var pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return;
    gl.useProgram(pr);
    var b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(pr, "p"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    var ur = gl.getUniformLocation(pr, "r"), ut = gl.getUniformLocation(pr, "t"), um = gl.getUniformLocation(pr, "m");
    var mx = 0, my = 0, tx = 0, ty = 0, vis = true, t0 = performance.now();
    window.addEventListener("pointermove", function (e) { tx = e.clientX / innerWidth - .5; ty = e.clientY / innerHeight - .5; }, { passive: true });
    function size() { var d = Math.min(window.devicePixelRatio || 1, 1.5) * .6; cv.width = Math.max(1, cv.clientWidth * d); cv.height = Math.max(1, cv.clientHeight * d); gl.viewport(0, 0, cv.width, cv.height); }
    size(); window.addEventListener("resize", size);
    if ("IntersectionObserver" in window) new IntersectionObserver(function (es) { vis = es[0].isIntersecting; }).observe(cv);
    function frame(now) {
      if (vis) {
        mx += (tx - mx) * .04; my += (ty - my) * .04;
        gl.uniform2f(ur, cv.width, cv.height); gl.uniform1f(ut, (now - t0) / 1000); gl.uniform2f(um, mx, -my);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
      }
      if (!still) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
    setTimeout(function () { cv.classList.add("on"); }, 80);
  }

  function reveal() {
    if (still || !("IntersectionObserver" in window)) return;
    var els = document.querySelectorAll("main > section:not(.hero), main > aside.takeaways");
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("pf-in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    Array.prototype.forEach.call(els, function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < innerHeight) return; // already on screen: leave it alone
      el.classList.add("pf-rise"); io.observe(el);
    });
  }


  /* Custom dropdowns for the finder, styled like the site. The real <select> stays in the form (hidden) and keeps
     the value, so filtering in va.js and submitting work as before; the list is rebuilt whenever its options change. */
  var CHEV = '<svg viewBox="0 0 12 8" width="12" height="8" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M1 1.5l5 5 5-5"/></svg>';
  var TICK = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 8.5l3.2 3.2L13 5"/></svg>';
  var uid = 0, openOne = null;
  function dropdown(sel) {
    if (sel.dataset.pfDone) return; sel.dataset.pfDone = "1";
    var n = ++uid, label = sel.closest("label"), cap = label && label.querySelector("span");
    if (cap && !cap.id) cap.id = "pf-cap-" + n;
    var box = document.createElement("div"); box.className = "pf-select";
    var btn = document.createElement("button"); btn.type = "button"; btn.className = "pf-sel-btn";
    btn.setAttribute("aria-haspopup", "listbox"); btn.setAttribute("aria-expanded", "false");
    var list = document.createElement("ul"); list.className = "pf-sel-list"; list.id = "pf-list-" + n; list.setAttribute("role", "listbox"); list.tabIndex = -1;
    if (cap) { btn.setAttribute("aria-labelledby", cap.id + " pf-val-" + n); list.setAttribute("aria-labelledby", cap.id); }
    btn.setAttribute("aria-controls", list.id);
    btn.innerHTML = '<span class="pf-sel-val" id="pf-val-' + n + '"></span><span class="pf-sel-chev">' + CHEV + "</span>";
    sel.classList.add("pf-native"); sel.tabIndex = -1; sel.setAttribute("aria-hidden", "true");
    sel.parentNode.insertBefore(box, sel); box.appendChild(btn); box.appendChild(list); box.appendChild(sel);
    if (label) label.addEventListener("click", function (e) { if (e.target === label || e.target === cap) { e.preventDefault(); btn.focus(); } });
    var active = -1, typed = "", typedAt = 0;
    function opts() { return [].slice.call(sel.options).filter(function (o) { return !o.hidden && !o.disabled; }); }
    function build() {
      var os = opts();
      list.innerHTML = os.map(function (o, i) {
        return '<li role="option" id="pf-o-' + n + "-" + i + '" data-i="' + i + '" aria-selected="' + (o.selected ? "true" : "false") + '"><span>' + o.text.replace(/&/g, "&amp;").replace(/</g, "&lt;") + "</span>" + TICK + "</li>";
      }).join("");
      var cur = sel.options[sel.selectedIndex];
      btn.querySelector(".pf-sel-val").textContent = cur ? cur.text : "";
      btn.disabled = !os.length;
    }
    function mark(i) {
      var items = list.children; if (!items.length) return;
      active = Math.max(0, Math.min(items.length - 1, i));
      [].forEach.call(items, function (li, k) { li.classList.toggle("on", k === active); });
      list.setAttribute("aria-activedescendant", items[active].id);
      var li = items[active], top = li.offsetTop, bot = top + li.offsetHeight;
      if (top < list.scrollTop) list.scrollTop = top; else if (bot > list.scrollTop + list.clientHeight) list.scrollTop = bot - list.clientHeight;
    }
    function place() {
      var r = btn.getBoundingClientRect(), hero = box.closest(".hero"), limit = innerHeight;
      if (hero) limit = Math.min(limit, hero.getBoundingClientRect().bottom);
      var below = limit - r.bottom - 12, above = r.top - (hero ? Math.max(0, hero.getBoundingClientRect().top) : 0) - 12;
      var want = Math.min(320, list.scrollHeight + 2), up = below < Math.min(want, 220) && above > below;
      box.classList.toggle("up", up);
      list.style.maxHeight = Math.max(160, Math.min(320, up ? above : below)) + "px";
    }
    function open() {
      if (openOne && openOne !== close) openOne();
      build(); box.classList.add("open"); btn.setAttribute("aria-expanded", "true"); place();
      mark(Math.max(0, opts().indexOf(sel.options[sel.selectedIndex]))); list.focus({ preventScroll: true }); openOne = close;
    }
    function close(focusBtn) {
      if (!box.classList.contains("open")) return;
      box.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); list.removeAttribute("aria-activedescendant");
      if (openOne === close) openOne = null; if (focusBtn) btn.focus({ preventScroll: true });
    }
    function choose(i) {
      var o = opts()[i]; if (!o) return;
      if (sel.value !== o.value) { sel.value = o.value; sel.dispatchEvent(new Event("change", { bubbles: true })); }
      build(); close(true);
    }
    btn.addEventListener("click", function () { box.classList.contains("open") ? close(true) : open(); });
    btn.addEventListener("keydown", function (e) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].indexOf(e.key) > -1) { e.preventDefault(); open(); }
    });
    list.addEventListener("click", function (e) { var li = e.target.closest("li"); if (li) choose(+li.dataset.i); });
    list.addEventListener("mousemove", function (e) { var li = e.target.closest("li"); if (li && +li.dataset.i !== active) mark(+li.dataset.i); });
    list.addEventListener("keydown", function (e) {
      var k = e.key, len = list.children.length;
      if (k === "ArrowDown") { e.preventDefault(); mark(active + 1); }
      else if (k === "ArrowUp") { e.preventDefault(); mark(active - 1); }
      else if (k === "Home") { e.preventDefault(); mark(0); }
      else if (k === "End") { e.preventDefault(); mark(len - 1); }
      else if (k === "PageDown") { e.preventDefault(); mark(active + 6); }
      else if (k === "PageUp") { e.preventDefault(); mark(active - 6); }
      else if (k === "Enter" || k === " ") { e.preventDefault(); choose(active); }
      else if (k === "Escape") { e.preventDefault(); close(true); }
      else if (k === "Tab") { close(false); }
      else if (k.length === 1 && /\S/.test(k)) {  // type to jump: "ne" goes to Nebraska, "new m" to New Mexico
        var now = Date.now(); typed = (now - typedAt < 700 ? typed : "") + k.toLowerCase(); typedAt = now;
        var os = opts(), hit = os.findIndex(function (o) { return o.text.toLowerCase().indexOf(typed) === 0; });
        if (hit > -1) mark(hit);
      }
    });
    document.addEventListener("pointerdown", function (e) { if (!box.contains(e.target)) close(false); });
    window.addEventListener("resize", function () { if (box.classList.contains("open")) place(); });
    new MutationObserver(build).observe(sel, { childList: true, subtree: true, attributes: true });
    sel.addEventListener("change", build);
    build();
  }

  function start() {
    if (document.documentElement.getAttribute("data-design") !== "7") return;
    var hero = document.querySelector("main .hero");
    if (hero) water(hero);
    reveal();
    [].forEach.call(document.querySelectorAll(".tx-finder select"), dropdown);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
