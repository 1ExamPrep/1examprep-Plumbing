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

  function start() {
    if (document.documentElement.getAttribute("data-design") !== "7") return;
    var hero = document.querySelector("main .hero");
    if (hero) water(hero);
    reveal();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
