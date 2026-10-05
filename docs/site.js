// The interactive figures of the project page, drawn in the style of the paper's figures:
// boxed axes, a Times-like serif, light grids, tab10 method colors and the paper's region shading.
(function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const COL = {
    poly: "#1f77b4", rff: "#d62728", gp: "#9467bd", mlp: "#ff7f0e", bound: "#2ca02c",
    P: "#e6eefc", Pedge: "#8fb0e3", Q: "#ededed", red: "#d62728", grey: "#595959"
  };
  const MODELS = ["poly", "rff", "gp", "mlp"];
  const NAMES = { poly: "Polynomial", rff: "RFF", gp: "GP", mlp: "MLP" };
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = id => document.getElementById(id);
  let uid = 0;

  function el(tag, attrs, parent) {
    const n = document.createElementNS(NS, tag);
    if (attrs) for (const k in attrs) if (attrs[k] != null) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  // SVG text with light markup: ~x~ italic, _x subscript, ^x superscript (braces for longer runs)
  function label(parent, x, y, spec, attrs) {
    const t = el("text", Object.assign({ x, y, "font-size": 13, fill: "#000" }, attrs || {}), parent);
    let shift = 0;
    for (const tok of String(spec).match(/~[^~]+~|[_^](?:\{[^}]*\}|[^\s~_^])|[^~_^]+/g) || []) {
      const s = el("tspan", {}, t);
      let text = tok, want = 0;
      if (tok[0] === "~") { text = tok.slice(1, -1); s.setAttribute("font-style", "italic"); }
      else if (tok[0] === "_" || tok[0] === "^") {
        text = tok.slice(1).replace(/^\{|\}$/g, ""); want = tok[0] === "_" ? 4 : -6;
        s.setAttribute("font-size", "72%");
      }
      if (want !== shift) { s.setAttribute("dy", want - shift); shift = want; }
      s.textContent = text;
    }
    return t;
  }
  function clip(svg, x, y, w, h) {
    const id = "clip" + (++uid), cp = el("clipPath", { id }, el("defs", {}, svg));
    el("rect", { x, y, width: w, height: h }, cp);
    return `url(#${id})`;
  }
  const pathOf = pts => pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
  function onView(node, cb, threshold) {
    if (!node) return;
    if (!("IntersectionObserver" in window)) { cb(true); return; }
    new IntersectionObserver(es => es.forEach(e => cb(e.isIntersecting)), { threshold: threshold || 0 }).observe(node);
  }
  const SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹";
  const supNum = n => String(n).split("").map(c => (c === "-" ? "⁻" : SUP[+c])).join("");
  function sci(v) {
    if (v < 1000) return v.toFixed(v < 10 ? 1 : 0);
    let e = Math.floor(Math.log10(v)), m = v / Math.pow(10, e);
    if (m.toFixed(1) === "10.0") { m = 1; e += 1; }
    return m.toFixed(1) + " × 10" + supNum(e);
  }
  const ease = p => (p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2);
  const svgX = (svg, e) => { const p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY; return p.matrixTransform(svg.getScreenCTM().inverse()).x; };

  // matplotlib-style axes: white plot area, light grid, outward ticks, black frame on top
  function axes(svg, o) {
    const { x0, x1, y0, y1 } = o;
    const fx = o.xlog ? Math.log10 : (v => v), fy = o.ylog ? Math.log10 : (v => v);
    const X = v => x0 + (fx(v) - fx(o.xlim[0])) / (fx(o.xlim[1]) - fx(o.xlim[0])) * (x1 - x0);
    const Y = v => y1 - (fy(v) - fy(o.ylim[0])) / (fy(o.ylim[1]) - fy(o.ylim[0])) * (y1 - y0);
    el("rect", { x: x0, y: y0, width: x1 - x0, height: y1 - y0, fill: "#fff" }, svg);
    const regions = el("g", {}, svg), grid = el("g", {}, svg);
    const data = el("g", { "clip-path": clip(svg, x0, y0, x1 - x0, y1 - y0) }, svg);
    const over = el("g", {}, svg), top = el("g", {}, svg);
    const tick = { stroke: "#000", "stroke-width": 0.9 }, fs = o.fs || 1;
    for (const t of o.xticks || []) {
      const x = X(t.v);
      if (o.grid) el("line", { x1: x, x2: x, y1: y0, y2: y1, stroke: "#000", "stroke-opacity": o.open ? 0.06 : 0.08 }, grid);
      el("line", Object.assign({ x1: x, x2: x, y1: y1, y2: y1 + 5 }, tick), top);
      label(top, x, y1 + 6 + 14 * fs, t.l, { "text-anchor": "middle", "font-size": 13 * fs });
    }
    for (const t of o.yticks || []) {
      const y = Y(t.v);
      if (o.grid) el("line", { x1: x0, x2: x1, y1: y, y2: y, stroke: "#000", "stroke-opacity": 0.08 }, grid);
      el("line", Object.assign({ x1: x0 - 5, x2: x0, y1: y, y2: y }, tick), top);
      label(top, x0 - 9, y + 4.5 * fs, t.l, { "text-anchor": "end", "font-size": 13 * fs });
    }
    if (o.xlabel) label(top, (x0 + x1) / 2, y1 + 12 + 33 * fs, o.xlabel, { "text-anchor": "middle", "font-size": 15 * fs });
    if (o.ylabel) label(top, o.ylabelX, (y0 + y1) / 2, o.ylabel, { "text-anchor": "middle", "font-size": 15 * fs, transform: `rotate(-90 ${o.ylabelX} ${(y0 + y1) / 2})` });
    const titleG = el("g", {}, top);
    const setTitle = s => { titleG.textContent = ""; label(titleG, (x0 + x1) / 2, y0 - 12, s, { "text-anchor": "middle", "font-size": 16 * fs }); };
    if (o.title) setTitle(o.title);
    if (o.open) el("path", { d: `M${x0} ${y0} L${x0} ${y1} L${x1} ${y1}`, fill: "none", stroke: "#000", "stroke-width": 0.9 }, top);
    else el("rect", { x: x0, y: y0, width: x1 - x0, height: y1 - y0, fill: "none", stroke: "#000", "stroke-width": 1 }, top);
    return { X, Y, regions, grid, data, over, top, setTitle, x0, x1, y0, y1 };
  }
  const ticks = (vs, fmt) => vs.map(v => ({ v, l: fmt ? fmt(v) : String(v) }));
  const one = v => (v < 0 ? "−" : "") + Math.abs(v).toFixed(1);

  // matplotlib-style legend; entries with a key toggle when clicked
  function legend(parent, x, y, items, opts) {
    const o = opts || {}, fs = o.fs || 1, rowH = 19 * fs, pad = 7 * fs, sample = 24 * fs, g = el("g", {}, parent);
    const box = el("rect", { x, y, rx: 3, fill: "#fff", "fill-opacity": 0.94, stroke: "#c8c8c8" }, g);
    const rows = items.map((it, i) => {
      const r = el("g", { class: it.key && o.onToggle ? "legend-hit" : null }, g), cy = y + pad + rowH * i + rowH / 2;
      if (it.area) el("rect", { x: x + pad, y: cy - 6 * fs, width: sample, height: 12 * fs, fill: it.color, stroke: it.edge }, r);
      else el("line", { x1: x + pad, x2: x + pad + sample, y1: cy, y2: cy, stroke: it.color, "stroke-width": (it.width || 1.8) * Math.sqrt(fs), "stroke-dasharray": it.dash, "stroke-opacity": it.opacity }, r);
      const t = label(r, x + pad + sample + 8 * fs, cy + 4.5 * fs, it.text, { "font-size": 13 * fs });
      const hit = el("rect", { x, y: cy - rowH / 2, height: rowH, fill: "transparent" }, r);
      if (it.key && o.onToggle) r.addEventListener("click", () => { const on = o.onToggle(it.key); r.style.opacity = on ? 1 : 0.35; });
      return { t, hit };
    });
    const layout = () => {
      const w = pad * 2 + sample + 8 * fs + Math.max(...rows.map(r => r.t.getComputedTextLength()));
      box.setAttribute("width", w); box.setAttribute("height", pad * 2 + rowH * items.length);
      rows.forEach(r => r.hit.setAttribute("width", w));
      if (o.anchor === "right") g.setAttribute("transform", `translate(${-w} 0)`);
    };
    layout();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(layout);
    return g;
  }
  // the paper's region shading and labels on a temperature-like axis
  function shadeRegions(A, P, Q, Tc, tcLabel, fs) {
    fs = fs || 1;
    el("rect", { x: A.X(Q[0]), y: A.y0, width: A.X(Q[1]) - A.X(Q[0]), height: A.y1 - A.y0, fill: COL.Q }, A.regions);
    el("rect", { x: A.X(P[0]), y: A.y0, width: A.X(P[1]) - A.X(P[0]), height: A.y1 - A.y0, fill: COL.P }, A.regions);
    el("line", { x1: A.X(Tc), x2: A.X(Tc), y1: A.y0, y2: A.y1, stroke: "#000", "stroke-width": 1, "stroke-dasharray": "1.5 3" }, A.regions);
    if (tcLabel !== false) label(A.over, A.X(Tc), A.y0 + 17 * fs, "~T~_c", { "text-anchor": "middle", "font-size": 14 * fs });
  }

  /* ------------------------------------------------------------ hero */
  function hero(D) {
    const svgS = $("hero-slice"), svgO = $("hero-op"), slider = $("hero-t");
    const n = D.T.length, t0 = D.T[0], dt = D.T[1] - D.T[0], Tlo = D.T[0], Thi = D.T[n - 1];
    const fIdx = T => Math.max(0, Math.min(n - 1.000001, (T - t0) / dt));
    const at = (a, f) => { const i = Math.floor(f), w = f - i; return a[i] * (1 - w) + a[Math.min(n - 1, i + 1)] * w; };
    const sliceAt = (S, f) => { const i = Math.floor(f), w = f - i, A = S[i], B = S[Math.min(n - 1, i + 1)]; return A.map((v, j) => v * (1 - w) + B[j] * w); };
    const shown = { poly: true, rff: true, gp: true, mlp: true };

    const S = axes(svgS, {
      x0: 94, x1: 430, y0: 42, y1: 296, xlim: [D.m[0], D.m[D.m.length - 1]], ylim: [-0.08, 0.42], grid: true, fs: 1.45,
      xticks: ticks([-1, -0.5, 0, 0.5, 1], one), yticks: ticks([0, 0.1, 0.2, 0.3, 0.4], one),
      xlabel: "Magnetization ~m~", ylabel: "Free energy ~f~(~T~, ~m~)", ylabelX: 24
    });
    const sPath = {};
    for (const k of MODELS) sPath[k] = el("path", { fill: "none", stroke: COL[k], "stroke-width": 2.6, "stroke-linejoin": "round" }, S.data);
    sPath.truth = el("path", { fill: "none", stroke: "#000", "stroke-width": 2.6, "stroke-linejoin": "round" }, S.data);

    const O = axes(svgO, {
      x0: 94, x1: 548, y0: 42, y1: 296, xlim: [Tlo, Thi], ylim: [0, 0.8], grid: true, fs: 1.45,
      xticks: ticks([1, 1.5, 2, 2.5, 3], one), yticks: ticks([0, 0.2, 0.4, 0.6, 0.8], one),
      xlabel: "Temperature ~T~", ylabel: "|~m~^*(~T~)|", ylabelX: 26, title: "Predicted magnetization"
    });
    shadeRegions(O, D.P, D.Q, D.Tc, true, 1.45);
    label(O.over, O.X((D.P[0] + D.P[1]) / 2), O.y1 - 12, "train ~P~", { "text-anchor": "middle", fill: COL.grey, "font-size": 13 * 1.45 });
    label(O.over, O.X((D.Q[0] + D.Tc) / 2), O.y1 - 12, "extrap ~Q~", { "text-anchor": "middle", fill: COL.red, "font-size": 13 * 1.45 });
    el("path", { d: pathOf(D.T.map((T, i) => [O.X(T), O.Y(D.truth.op[i])])), fill: "none", stroke: "#000", "stroke-width": 2.6 }, O.data);
    const oPath = {}, dot = {};
    for (const k of MODELS) oPath[k] = el("path", { fill: "none", stroke: COL[k], "stroke-width": 2.4, "stroke-linejoin": "round" }, O.data);
    const cursor = el("line", { y1: O.y0, y2: O.y1, stroke: "#000", "stroke-width": 1.3, "stroke-opacity": 0.55 }, O.data);
    dot.truth = el("circle", { r: 6.5, fill: "#000" }, O.data);
    for (const k of MODELS) dot[k] = el("circle", { r: 5.8, fill: COL[k], stroke: "#fff", "stroke-width": 1.4 }, O.data);
    legend(O.over, O.x1 - 10, O.y0 + 10, [
      { text: "Ground truth", color: "#000" },
      ...MODELS.map(k => ({ key: k, text: NAMES[k], color: COL[k] }))
    ], {
      anchor: "right", fs: 1.45,
      onToggle: k => {
        shown[k] = !shown[k];
        for (const node of [sPath[k], oPath[k], dot[k]]) node.style.display = shown[k] ? "" : "none";
        return shown[k];
      }
    });

    const tval = $("hero-tval"), where = $("hero-where");
    function draw(T) {
      const f = fIdx(T);
      S.setTitle(`Free energy at ~T~ = ${T.toFixed(2)}`);
      sPath.truth.setAttribute("d", pathOf(sliceAt(D.truth.slices, f).map((v, j) => [S.X(D.m[j]), S.Y(v)])));
      for (const k of MODELS) {
        sPath[k].setAttribute("d", pathOf(sliceAt(D.models[k].slices, f).map((v, j) => [S.X(D.m[j]), S.Y(v)])));
        const pts = [[O.X(T), O.Y(at(D.models[k].op, f))]];
        for (let i = Math.ceil(f); i < n; i++) pts.push([O.X(D.T[i]), O.Y(D.models[k].op[i])]);
        oPath[k].setAttribute("d", pathOf(pts));
        dot[k].setAttribute("cx", O.X(T)); dot[k].setAttribute("cy", O.Y(at(D.models[k].op, f)));
      }
      dot.truth.setAttribute("cx", O.X(T)); dot.truth.setAttribute("cy", O.Y(at(D.truth.op, f)));
      cursor.setAttribute("x1", O.X(T)); cursor.setAttribute("x2", O.X(T));
      tval.textContent = T.toFixed(2);
      if (T >= D.P[0]) { where.className = "inP"; where.textContent = "training region"; }
      else if (T >= D.Tc) { where.className = ""; where.textContent = "outside the training data, same phase"; }
      else { where.className = "below"; where.innerHTML = "below <i>T</i><sub>c</sub>, the unseen phase"; }
    }

    let raf = 0;
    const stop = () => { if (raf) cancelAnimationFrame(raf); raf = 0; };
    function sweep(from, to, ms) {
      stop();
      if (reduced) { slider.value = to; draw(to); return; }
      const start = performance.now();
      const step = now => {
        const p = Math.min(1, (now - start) / ms), T = from + (to - from) * ease(p);
        slider.value = T; draw(T);
        raf = p < 1 ? requestAnimationFrame(step) : 0;
      };
      raf = requestAnimationFrame(step);
    }
    const setT = T => { T = Math.max(Tlo, Math.min(Thi, T)); slider.value = T; draw(T); };
    slider.addEventListener("input", () => { stop(); draw(parseFloat(slider.value)); });
    let dragging = false;
    svgO.addEventListener("pointerdown", e => {
      if (e.target.closest(".legend-hit")) return;
      stop(); dragging = true; svgO.setPointerCapture(e.pointerId); setT(Tlo + (svgX(svgO, e) - O.x0) / (O.x1 - O.x0) * (Thi - Tlo));
    });
    svgO.addEventListener("pointermove", e => { if (dragging) setT(Tlo + (svgX(svgO, e) - O.x0) / (O.x1 - O.x0) * (Thi - Tlo)); });
    const release = () => { dragging = false; };
    svgO.addEventListener("pointerup", release); svgO.addEventListener("pointercancel", release);
    $("hero-play").addEventListener("click", () => sweep(2.9, 1.0, 7000));
    draw(parseFloat(slider.value));
    let played = false;
    onView($("hero"), vis => { if (vis && !played) { played = true; sweep(2.9, 1.0, 7000); } }, 0.45);
  }

  /* ------------------------------------------------------- ferromagnet */
  function ferro() {
    const P = [2.0, 3.0], Q = [1.0, 2.0], TC = 1.5;
    const L = 100, N = L * L, ISING_TC = 2.0 / Math.log(1 + Math.SQRT2);
    const spins = new Int8Array(N);
    for (let i = 0; i < N; i++) spins[i] = Math.random() < 0.5 ? 1 : -1;
    const canvas = $("lattice"), ctx = canvas.getContext("2d");
    const img = ctx.createImageData(L, L), px = img.data;
    const slider = $("temp"), tval = $("tval"), mval = $("mval");
    let T = parseFloat(slider.value), cooling = null;

    const stack = new Int32Array(N);
    function sweep(sites) {                       // Wolff cluster flips at the Ising temperature whose T_c matches the paper's
      const padd = 1 - Math.exp(-2 / (T * ISING_TC / TC));
      let flipped = 0;
      while (flipped < sites) {
        const seed = (Math.random() * N) | 0, s0 = spins[seed];
        let top = 0; stack[top++] = seed; spins[seed] = -s0; flipped++;
        while (top) {
          const i = stack[--top], x = i % L, y = (i / L) | 0;
          for (const j of [((y + L - 1) % L) * L + x, ((y + 1) % L) * L + x, y * L + (x + L - 1) % L, y * L + (x + 1) % L])
            if (spins[j] === s0 && Math.random() < padd) { spins[j] = -s0; stack[top++] = j; flipped++; }
        }
      }
    }
    function drawSpins() {                        // relative to the majority, so a global flip of the cluster is invisible
      let m = 0;
      for (let i = 0; i < N; i++) m += spins[i];
      const up = m >= 0 ? 1 : -1;
      for (let i = 0; i < N; i++) { const c = spins[i] === up ? 20 : 218; px[4 * i] = px[4 * i + 1] = px[4 * i + 2] = c; px[4 * i + 3] = 255; }
      ctx.putImageData(img, 0, 0);
      return m / N;
    }
    const f = (t, m) => 0.5 * (1 - TC / t) * m * m + Math.pow(TC / t, 3) * Math.pow(m, 4) / 12 + 0.01;
    const mstar = t => (t < TC ? Math.sqrt(3 * (TC / t - 1) / Math.pow(TC / t, 3)) : 0);

    const F = axes($("landscape"), {
      x0: 66, x1: 308, y0: 34, y1: 206, xlim: [-1.25, 1.25], ylim: [-0.06, 0.45], grid: true, fs: 1.3,
      xticks: ticks([-1, 0, 1], one), yticks: ticks([0, 0.2, 0.4], one),
      xlabel: "Magnetization ~m~", ylabel: "Free energy ~f~", ylabelX: 16, title: "Free energy"
    });
    const curve = el("path", { fill: "none", stroke: "#000", "stroke-width": 1.6 }, F.data);
    const ball = el("circle", { r: 5.5, fill: COL.poly, stroke: "#fff", "stroke-width": 1 }, F.data);
    const ms = Array.from({ length: 201 }, (_, i) => -1.25 + 2.5 * i / 200);
    function drawLandscape() {
      curve.setAttribute("d", pathOf(ms.map(m => [F.X(m), F.Y(f(T, m))])));
      const m = mstar(T);
      ball.setAttribute("cx", F.X(m)); ball.setAttribute("cy", F.Y(f(T, m)) - 5.5);
    }
    const M = axes($("opcurve"), {
      x0: 66, x1: 308, y0: 34, y1: 206, xlim: [1, 3], ylim: [0, 0.8], grid: true, fs: 1.3,
      xticks: ticks([1, 2, 3], one), yticks: ticks([0, 0.4, 0.8], one),
      xlabel: "Temperature ~T~", ylabel: "|~m~|", ylabelX: 18, title: "Magnetization"
    });
    shadeRegions(M, P, Q, TC, true, 1.3);
    const trail = el("path", { fill: "none", stroke: COL.poly, "stroke-width": 2 }, M.data);
    const minDot = el("circle", { r: 5, fill: COL.poly, stroke: "#fff", "stroke-width": 1 }, M.data);
    const visited = new Set();
    function drawTrace() {
      visited.add(Math.round(T * 200));
      const ts = [...visited].sort((a, b) => a - b).map(v => v / 200);
      trail.setAttribute("d", pathOf(ts.map(t => [M.X(t), M.Y(mstar(t))])));
      minDot.setAttribute("cx", M.X(T)); minDot.setAttribute("cy", M.Y(mstar(T)));
    }

    let frames = 0, running = false, raf = 0;
    function frame(now) {
      frames++;
      if (cooling) {
        const p = Math.min(1, (now - cooling.t0) / cooling.ms);
        T = 3.0 - 2.0 * p; slider.value = T.toFixed(3);
        if (p >= 1) cooling = null;
      }
      if (frames % 4 === 0) sweep(reduced ? N / 40 : N / 10);
      const m = drawSpins();
      drawLandscape(); drawTrace();
      tval.textContent = T.toFixed(2); mval.textContent = Math.abs(m).toFixed(2);
      if (running) raf = requestAnimationFrame(frame);
    }
    slider.addEventListener("input", () => { cooling = null; T = parseFloat(slider.value); });
    $("cool").addEventListener("click", () => { visited.clear(); cooling = { t0: performance.now(), ms: reduced ? 1 : 24000 }; });
    sweep(20 * N); drawSpins(); drawLandscape(); drawTrace();
    onView($("ferro"), vis => {                     // only simulate while the demo is on screen
      if (vis && !running) { running = true; raf = requestAnimationFrame(frame); }
      else if (!vis && running) { running = false; cancelAnimationFrame(raf); }
    });
  }

  /* ---------------------------------------------------------- explorer */
  // errors are Table 1 of the paper, in the order polynomial, RFF, GP, MLP
  const SYSTEMS = [
    { id: "heisenberg", tab: "Heisenberg", kind: "Analytic", color: "#2c7fb8", gh: 879,
      desc: "Mean-field Landau free energy <i>f</i>(<i>T</i>, <i>m</i>) of a ferromagnet. Above <i>T</i><sub>c</sub> the minimum sits at <i>m</i> = 0. Below <i>T</i><sub>c</sub> the surface develops two symmetric minima at nonzero magnetization. Derived quantity: <span class=nw>|<i>m</i>*(<i>T</i>)|</span>, the magnitude of the minimizing magnetization.",
      nmse: [4.8e-2, 2.8e-2, 3.3e-2, 2.0e-1], rel: [7.8, 6.5, 5.5, 28.8], tc: [4.7, 1.6, 1.3, 15.7], note: "" },
    { id: "flory", tab: "Flory&ndash;Huggins", kind: "Analytic", color: "#7570b3", gh: 879,
      desc: "Mixing free energy of a symmetric binary mixture. Above <i>T</i><sub>c</sub> the entropy term dominates and the free energy has a single well. Below <i>T</i><sub>c</sub> the mixture separates and a double well emerges. Derived quantity: <span class=nw>|<i>m</i>*(<i>T</i>)|</span>, the composition of the coexisting phases.",
      nmse: [1.4e-3, 7.5e-4, 9.0e-8, 3.2e-1], rel: [2.4, 1.7, 0.0, 36.5], tc: [3.7, 2.6, 0.4, 34.2], note: "" },
    { id: "polaron", tab: "SSH polaron", kind: "Simulated", color: "#1b9e77", gh: 905,
      desc: "Dispersion <i>E</i>(<i>K</i>) of a single polaron in the Su&ndash;Schrieffer&ndash;Heeger model, computed by variational exact diagonalization, with the electron&ndash;phonon coupling &lambda; as the tuning parameter. At weak coupling the minimum is at <i>K</i> = 0. Past a critical coupling it moves continuously to finite momentum. Derived quantity: the ground-state momentum <span class=nw><i>K</i>*(&lambda;)</span>.",
      nmse: [3.3e-3, 3.7e-3, 1.6e-3, 3.0e-1], rel: [3.5, 3.1, 2.3, 39.5], tc: [0.7, 0.4, 0.9, 14.9], note: "" },
    { id: "rb", tab: "Rayleigh&ndash;B&eacute;nard", kind: "Simulated", color: "#c2185b", gh: 883,
      desc: "Mean temperature profile of a two-dimensional fluid layer heated from below, from a numerical simulation sweep in the Rayleigh number. Below the critical Rayleigh number the fluid conducts and the profile is linear in height. Above it, convection flattens the profile in the interior. Models are trained on the convecting side. Derived quantity: the convective amplitude &Phi;, the RMS departure from the conducting profile.",
      nmse: [3.2e-2, 9.2e-2, 5.2e-2, 1.8e-2], rel: [11.2, 16.1, 13.5, 9.8], tc: [5.0, 2.9, 2.1, 10.8],
      note: "The MLP has the lowest NMSE on the profile itself. Below the transition the profile is affine in height, and an MLP extrapolates affinely past its outermost kink. It still misplaces the transition by more than any of the fixed-feature models." },
    { id: "arpes", tab: "ARPES", kind: "Experiment", color: "#d95f02", gh: 786,
      desc: 'Spectral intensity <i>I</i>(<i>T</i>, <i>E</i>) of overdoped Pb-doped Bi-2212, measured by angle-resolved photoemission [<a href="#ref-he">He et al. 2021</a>, <a href="#ref-chen">Chen et al. 2025</a>]. The antinodal gap closes well above the resistive <i>T</i><sub>c</sub>, so we split <i>P</i> and <i>Q</i> at the gap-closing temperature <i>T</i><sub>gap</sub>. Derived quantity: the spectral peak energy <span class=nw>&minus;<i>E</i>*(<i>T</i>)</span>, a signature of gap closing.',
      nmse: [3.8e-2, 3.4e-2, 8.3e-3, 1.1e-1], rel: [11.9, 12.0, 5.4, 23.1], tc: null,
      note: "The gap closing does not define a sharp critical point, so we report no critical-point error. Polynomial, RFF, and GP follow the peak near <i>T</i><sub>gap</sub> but underestimate its shift far below it. The MLP shifts the peak in the opposite direction." }
  ];
  function explorer() {
    const tabs = document.querySelector("#explorer .tabs"), desc = $("sys-desc"), grid = $("sys-grid"), note = $("sys-note"), bars = $("sys-bars");
    // two boxed panels of horizontal bars, one row per method
    function drawBars(s) {
      bars.textContent = "";
      const panel = (y0, y1, vals, xmax, xt, title) => {
        const A = axes(bars, { x0: 90, x1: 240, y0, y1, xlim: [0, xmax], ylim: [0, 1], xticks: ticks(xt), grid: true, open: true, fs: 0.95 });
        label(A.top, 90, y0 - 11, title, { "font-size": 14 });
        if (!vals) label(A.over, (A.x0 + A.x1) / 2, (A.y0 + A.y1) / 2 + 5, "not defined here", { "text-anchor": "middle", fill: "#666", "font-style": "italic", "font-size": 12.5 });
        MODELS.forEach((k, i) => {
          const y = A.y0 + (i + 0.5) * (A.y1 - A.y0) / MODELS.length;
          label(bars, 82, y + 4.5, NAMES[k], { "text-anchor": "end", "font-size": 13 });
          if (!vals) return;
          el("rect", { x: A.X(0), y: y - 5, width: Math.max(1.2, A.X(vals[i]) - A.X(0)), height: 10, fill: COL[k] }, A.data);
          label(A.over, A.X(vals[i]) + 5, y + 4, vals[i].toFixed(1), { "font-size": 12, fill: "#444" });
        });
      };
      panel(36, 130, s.rel, 50, [0, 25, 50], "Relative error on ~Q~ (%)");
      panel(202, 296, s.tc, 40, [0, 20, 40], "Critical-point error (%)");
    }
    const buttons = SYSTEMS.map((s, i) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "tab"; b.setAttribute("role", "tab"); b.innerHTML = s.tab;
      b.addEventListener("click", () => select(i));
      b.addEventListener("keydown", e => {
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          const j = (i + (e.key === "ArrowRight" ? 1 : SYSTEMS.length - 1)) % SYSTEMS.length;
          select(j); buttons[j].focus(); e.preventDefault();
        }
      });
      tabs.appendChild(b);
      return b;
    });
    function select(i) {
      const s = SYSTEMS[i];
      buttons.forEach((b, j) => { b.setAttribute("aria-selected", String(i === j)); b.tabIndex = i === j ? 0 : -1; });
      desc.innerHTML = `<b>${s.kind}.</b> ${s.desc}`;
      grid.src = `figs/targets/grid_${s.id}.webp`; grid.height = s.gh;
      drawBars(s);
      note.innerHTML = s.note; note.style.display = s.note ? "" : "none";
    }
    select(0);
    const warm = () => SYSTEMS.forEach(s => { new Image().src = `figs/targets/grid_${s.id}.webp`; });
    if ("requestIdleCallback" in window) requestIdleCallback(warm); else setTimeout(warm, 1500);
  }

  /* ------------------------------------------- the paper's bound figures, one system at a time */
  // Figs. 5 and 6 are redrawn from data read back from the paper's vector figures (paper_figs.js).
  const BCOL = { emp: "#1f77b4", gevp: "#2ca02c", volume: "#e377c2", remez: "#8c564b" };
  function decadeTicks(lo, hi, maxN) {
    const a = Math.ceil(Math.log10(lo) - 1e-9), b = Math.floor(Math.log10(hi) + 1e-9), step = Math.max(1, Math.ceil((b - a + 1) / maxN)), out = [];
    for (let e = b; e >= a; e -= step) out.push({ v: Math.pow(10, e), l: e === 0 ? "1" : `10^{${e < 0 ? "−" + -e : e}}` });
    return out;
  }
  function marker(kind, x, y, color, parent) {
    if (kind === "o") return el("circle", { cx: x, cy: y, r: 3.1, fill: color }, parent);
    if (kind === "s") return el("rect", { x: x - 2.9, y: y - 2.9, width: 5.8, height: 5.8, fill: color }, parent);
    if (kind === "^") return el("path", { d: `M${x} ${y - 3.8}L${x + 3.5} ${y + 2.6}L${x - 3.5} ${y + 2.6}Z`, fill: color }, parent);
    return el("path", { d: `M${x} ${y - 3.8}L${x + 3.1} ${y}L${x} ${y + 3.8}L${x - 3.1} ${y}Z`, fill: color }, parent);
  }
  function tabbedFigure(fig, draw) {
    const bar = fig.querySelector(".tabs");
    const btns = SYSTEMS.map((s, i) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "tab"; b.setAttribute("role", "tab"); b.innerHTML = s.tab;
      b.addEventListener("click", () => sel(i));
      b.addEventListener("keydown", e => {
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          const j = (i + (e.key === "ArrowRight" ? 1 : SYSTEMS.length - 1)) % SYSTEMS.length;
          sel(j); btns[j].focus(); e.preventDefault();
        }
      });
      bar.appendChild(b);
      return b;
    });
    function sel(i) {
      btns.forEach((b, j) => { b.setAttribute("aria-selected", String(i === j)); b.tabIndex = i === j ? 0 : -1; });
      draw(SYSTEMS[i].id);
    }
    sel(0);
  }
  function paperFigs() {
    const D = window.PAPER_FIGS;
    if (!D || !$("bvn") || !$("dist")) return;
    const panel = (svg, e, m, xlabel, xticks) => {
      svg.textContent = "";
      const fs = svg.getBoundingClientRect().width > 380 ? 1 : 1.16;   // the panels stack and widen on phones
      return axes(svg, {
        x0: 80, x1: 388, y0: 20 + 16 * fs, y1: 262, xlim: e.xlim, ylim: e.ylim, xlog: true, ylog: true, grid: true, fs,
        xticks, yticks: decadeTicks(e.ylim[0], e.ylim[1], 5), xlabel, ylabel: "Transfer coefficient", ylabelX: 20,
        title: m === "poly" ? "Polynomial" : "RFF"
      });
    };
    tabbedFigure($("bvn"), id => {
      for (const m of ["poly", "rff"]) {
        const e = D.bvn[id][m], A = panel($("bvn-" + m), e, m, "Training set size ~n~", [200, 1000, 2000].map(v => ({ v, l: String(v) })));
        for (const [k, mk] of [["volume", "^"], ["remez", "d"], ["gevp", "s"], ["emp", "o"]]) {
          const pts = e.series[k];
          if (!pts) continue;
          el("path", { d: pathOf(pts.map(p => [A.X(p[0]), A.Y(p[1])])), fill: "none", stroke: BCOL[k], "stroke-width": 1.5 }, A.data);
          pts.forEach(p => marker(mk, A.X(p[0]), A.Y(p[1]), BCOL[k], A.data));
        }
      }
    });
    tabbedFigure($("dist"), id => {
      for (const m of ["poly", "rff"]) {
        const e = D.dist[id][m], ds = e.points.emp.map(p => p[0]), lo = Math.min(...ds), hi = Math.max(...ds);
        const short = v => String(+v.toPrecision(2));
        const A = panel($("dist-" + m), e, m, "Distance ~D~", [lo, hi].map(v => ({ v, l: short(v) })));
        [["emp", "o"], ["gevp", "s"]].forEach(([k, mk], row) => {
          const pts = e.points[k], X = pts.map(p => Math.log(p[0])), Y = pts.map(p => Math.log(p[1]));
          const mx = X.reduce((a, b) => a + b) / X.length, my = Y.reduce((a, b) => a + b) / Y.length;
          const slope = X.reduce((s, x, i) => s + (x - mx) * (Y[i] - my), 0) / X.reduce((s, x) => s + (x - mx) * (x - mx), 0), icpt = my - slope * mx;
          const line = Array.from({ length: 40 }, (_, i) => { const x = Math.exp(Math.log(lo) + (Math.log(hi) - Math.log(lo)) * i / 39); return [A.X(x), A.Y(Math.exp(icpt + slope * Math.log(x)))]; });
          el("path", { d: pathOf(line), fill: "none", stroke: BCOL[k], "stroke-width": 1.4, "stroke-opacity": 0.85 }, A.data);
          pts.forEach(p => marker(mk, A.X(p[0]), A.Y(p[1]), BCOL[k], A.data));
          const g = el("g", {}, A.over), tx = A.x0 + 10, ty = A.y0 + 22 + row * 26;
          const box = el("rect", { x: tx - 5, y: ty - 15, height: 21, rx: 3, fill: "#fff", stroke: BCOL[k] }, g);
          const t = label(g, tx, ty, `~β~ = ${slope.toFixed(2)}`, { fill: BCOL[k], "font-size": 13 });
          box.setAttribute("width", t.getComputedTextLength() + 10);
        });
      }
    });
  }

  /* ------------------------------------------- the bound: feature covariances on the two sides */
  // One dimension. Q sits around the transition at 0 and the training window P, of the same width,
  // sits a distance D away. Each panel is a model with two features, so both covariances are
  // ellipses: a straight line (features 1 and T) and two random Fourier features. P's ellipse,
  // enlarged by the square root of the top generalized eigenvalue, just covers Q's.
  const QA = -0.5, QB = 0.5, WIDTH = 1, DMIN = 0.5, DMAX = 4, DEGS = [1, 2, 3, 4, 5, 6];
  const PBLUE = "#3f6fb5";
  const sinc = x => (Math.abs(x) < 1e-9 ? 1 : Math.sin(x) / x);
  const meanCos = (al, be, a, b) => Math.cos(be + al * (a + b) / 2) * sinc(al * (b - a) / 2);   // average of cos(al T + be) over [a, b]
  // second moments E[phi phi^T] over the window [a, b] for each two-feature model
  const L = 3;                                    // T is drawn in units of 3 so both ellipses fit the same frame
  const RFF2 = { w: [-0.533, 0.304], b: [5.82, 5.32] };   // one draw from a Gaussian spectral measure, length scale 2
  const SECOND = {
    line: (a, b) => { const c = (a + b) / 2, v = (b - a) * (b - a) / 12; return [[1, c / L], [c / L, (c * c + v) / (L * L)]]; },
    rff: (a, b) => {
      const { w, b: ph } = RFF2, M = [[0, 0], [0, 0]];
      for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++) M[i][j] = 0.5 * (meanCos(w[i] - w[j], ph[i] - ph[j], a, b) + meanCos(w[i] + w[j], ph[i] + ph[j], a, b));
      return M;
    },
    mean: { line: (a, b) => [1, (a + b) / 2 / L], rff: (a, b) => RFF2.w.map((w, i) => meanCos(w, RFF2.b[i], a, b)) }
  };

  // a 2x2 symmetric matrix as an ellipse {M^(1/2) u : |u| = 1}: semi-axes and the angle of the first
  function ellipse2(M) {
    const a = M[0][0], b = M[0][1], c = M[1][1], m = (a + c) / 2, r = Math.hypot((a - c) / 2, b);
    return { big: Math.sqrt(m + r), small: Math.sqrt(Math.max(0, m - r)), th: 0.5 * Math.atan2(2 * b, a - c) };
  }
  function ellipsePath(E, s, map, n) {
    const pts = [], ct = Math.cos(E.th), st = Math.sin(E.th);
    for (let i = 0; i <= n; i++) {
      const a = 2 * Math.PI * i / n, u = s * E.big * Math.cos(a), v = s * E.small * Math.sin(a);
      pts.push(map(u * ct - v * st, u * st + v * ct));
    }
    return pathOf(pts) + "Z";
  }
  // top generalized eigenvalue of (A, B) and the point where B's enlarged ellipse touches A's
  function touch2(A, B) {
    const dB = B[0][0] * B[1][1] - B[0][1] * B[0][1];
    const tr = (A[0][0] * B[1][1] + A[1][1] * B[0][0] - 2 * A[0][1] * B[0][1]) / dB, dt = (A[0][0] * A[1][1] - A[0][1] * A[0][1]) / dB;
    const lam = tr / 2 + Math.sqrt(Math.max(0, tr * tr / 4 - dt));
    const r0 = [A[0][0] - lam * B[0][0], A[0][1] - lam * B[0][1]], r1 = [A[0][1] - lam * B[0][1], A[1][1] - lam * B[1][1]];
    let v = Math.hypot(...r0) > Math.hypot(...r1) ? [-r0[1], r0[0]] : [-r1[1], r1[0]];
    const nB = Math.sqrt(v[0] * (B[0][0] * v[0] + B[0][1] * v[1]) + v[1] * (B[0][1] * v[0] + B[1][1] * v[1]));
    v = v.map(x => x / nB);
    const s = Math.sqrt(lam);
    return { lam, at: [s * (B[0][0] * v[0] + B[0][1] * v[1]), s * (B[0][1] * v[0] + B[1][1] * v[1])] };
  }

  // the symmetric inverse square root of a 2x2 positive definite matrix: the map that makes its ellipse a circle
  function invSqrt2(M) {
    const E = ellipse2(M), c = Math.cos(E.th), s = Math.sin(E.th), a = 1 / E.big, b = 1 / E.small;
    return [[a * c * c + b * s * s, (a - b) * c * s], [(a - b) * c * s, a * s * s + b * c * c]];
  }

  // one panel: the covariance ellipses of a two-feature model on P and Q, drawn either in the original
  // features (view 0) or after stretching the plane until P's ellipse is a unit circle (view 1)
  function covPanel(svg, model, title, xl, yl) {
    const F = svg.getBoundingClientRect().width > 380 ? 1 : 1.16;   // the panels stack and widen on phones
    const R0 = 1.3, fx0 = 62, fx1 = 372, fy0 = 36, fy1 = 346, half = (fx1 - fx0) / 2, cx = (fx0 + fx1) / 2, cy = (fy0 + fy1) / 2;
    // the rescaled view is framed for P at distance 2.4 or more, so the extrapolation ellipse grows into it as P moves away
    const lamRef = touch2(SECOND[model](QA, QB), SECOND[model](2.4, 2.4 + WIDTH)).lam;
    el("rect", { x: fx0, y: fy0, width: fx1 - fx0, height: fy1 - fy0, fill: "#fff" }, svg);
    const cg = el("g", { "clip-path": clip(svg, fx0, fy0, fx1 - fx0, fy1 - fy0) }, svg);
    el("path", { d: `M${fx0} ${cy} H${fx1} M${cx} ${fy0} V${fy1}`, stroke: "#000", "stroke-opacity": 0.15 }, cg);
    const qEll = el("path", { fill: COL.Q, stroke: COL.grey, "stroke-width": 1.4 }, cg);
    const pEll = el("path", { fill: COL.P, "fill-opacity": 0.92, stroke: PBLUE, "stroke-width": 1.4 }, cg);
    const pBig = el("path", { fill: "none", stroke: PBLUE, "stroke-width": 1.3, "stroke-dasharray": "6 4" }, cg);
    const hits = [0, 1].map(() => el("circle", { r: 4.6, fill: COL.bound, stroke: "#fff", "stroke-width": 1.2 }, cg));
    el("rect", { x: fx0, y: fy0, width: fx1 - fx0, height: fy1 - fy0, fill: "none", stroke: "#000" }, svg);
    label(svg, cx, fy0 - 12, title, { "text-anchor": "middle", "font-size": 16 * F });
    const axl = el("g", {}, svg);
    label(axl, cx, fy1 + 24 * F, xl, { "text-anchor": "middle", "font-size": 14 * F });
    label(axl, 40, cy, yl, { "text-anchor": "middle", "font-size": 14 * F, transform: `rotate(-90 40 ${cy})` });
    const pTag = label(svg, 0, 0, "~P~", { "text-anchor": "middle", "font-size": 15 * F, fill: PBLUE });
    const qTag = label(svg, 0, 0, "~Q~", { "text-anchor": "middle", "font-size": 15 * F, fill: COL.grey });
    const bigBg = el("rect", { fill: "#fff", "fill-opacity": 0.85 }, svg);
    const bigTag = label(svg, 0, 0, "√~λ~_{max} × ~P~", { "font-size": 14 * F, fill: PBLUE });
    const inside = (x, y) => [Math.max(fx0 + 10, Math.min(fx1 - 10, x)), Math.max(fy0 + 18, Math.min(fy1 - 8, y))];
    // a region's label sits just past the end of its ellipse, on the side where its features lie
    function tag(t, E, mean, map) {
      const ct = Math.cos(E.th), st = Math.sin(E.th), sg = ct * mean[0] + st * mean[1] < 0 ? -1 : 1;
      const p = map(sg * E.big * ct, sg * E.big * st), dx = p[0] - cx, dy = p[1] - cy, n = Math.hypot(dx, dy) || 1;
      const q = inside(p[0] + dx / n * 14 * F, p[1] + dy / n * 14 * F + 5 * F);
      t.setAttribute("x", q[0]); t.setAttribute("y", q[1]);
    }
    return function update(dist, view) {
      const B = SECOND[model](dist, dist + WIDTH), A = SECOND[model](QA, QB), T = touch2(A, B), EP = ellipse2(B), EQ = ellipse2(A);
      const W = invSqrt2(B), s = view;
      const M = [[1 - s + s * W[0][0], s * W[0][1]], [s * W[1][0], 1 - s + s * W[1][1]]];
      const R = Math.exp((1 - s) * Math.log(R0) + s * Math.log(1.2 * Math.sqrt(Math.max(T.lam, lamRef)))), k = half / R;
      const map = (u, v) => [cx + (M[0][0] * u + M[0][1] * v) * k, cy - (M[1][0] * u + M[1][1] * v) * k];
      qEll.setAttribute("d", ellipsePath(EQ, 1, map, 240));
      pEll.setAttribute("d", ellipsePath(EP, 1, map, 240));
      pBig.setAttribute("d", ellipsePath(EP, Math.sqrt(T.lam), map, 4000));
      [1, -1].forEach((sg, i) => { const p = map(sg * T.at[0], sg * T.at[1]); hits[i].setAttribute("cx", p[0]); hits[i].setAttribute("cy", p[1]); });
      tag(pTag, EP, SECOND.mean[model](dist, dist + WIDTH), map);
      tag(qTag, EQ, SECOND.mean[model](QA, QB), map);
      axl.setAttribute("opacity", Math.max(0, 1 - 2 * s));
      // the dashed curve's label: beside the band in the original view, at the top of the circle when rescaled
      const w = bigTag.getComputedTextLength();
      let bx = null, byy = fy0 + 26;
      if (s < 0.02) {
        const inv = 1 / (T.lam * (B[0][0] * B[1][1] - B[0][1] * B[0][1]));
        const ia = B[1][1] * inv, ib = -B[0][1] * inv, ic = B[0][0] * inv, y = R0 - 0.2, disc = ib * ib * y * y - ia * (ic * y * y - 1);
        if (disc > 0) {
          const xl0 = cx + (-ib * y - Math.sqrt(disc)) / ia * k, xr0 = cx + (-ib * y + Math.sqrt(disc)) / ia * k;
          bx = xl0 - w - 6 > fx0 + 4 ? xl0 - w - 6 : xr0 + 6;
        } else bx = fx0 + 8;
        bx = Math.max(fx0 + 6, Math.min(fx1 - w - 6, bx));
      } else if (s > 0.98) {
        const rho = Math.sqrt(T.lam) * k;
        bx = cx - w / 2;
        byy = cy - rho - 8 > fy0 + 22 ? cy - rho - 8 : cy - rho + 22;
      }
      const show = bx !== null;
      bigTag.style.display = bigBg.style.display = show ? "" : "none";
      if (show) {
        bigTag.setAttribute("x", bx); bigTag.setAttribute("y", byy);
        bigBg.setAttribute("x", bx - 3); bigBg.setAttribute("y", byy - 18); bigBg.setAttribute("width", w + 6); bigBg.setAttribute("height", 24);
      }
      return T.lam;
    };
  }

  function boundFig() {
    const strip = $("toy-strip"), slider = $("toy-D"), viewSeg = $("toy-view");
    if (!strip || !$("toy-line") || !$("toy-rff")) return;
    let dist = parseFloat(slider.value), view = 0;

    // strip: where the two regions sit on the temperature axis (a narrower box on phones keeps the text readable)
    const SW = strip.getBoundingClientRect().width < 560 ? 470 : 700;
    strip.setAttribute("viewBox", `0 0 ${SW} 78`);
    const SX0 = 24, SX1 = SW - 16, T0 = -0.9, T1 = 5.4, SX = t => SX0 + (t - T0) / (T1 - T0) * (SX1 - SX0);
    const by = 20, sy0 = 28, sy1 = 54;
    el("rect", { x: SX(QA), y: sy0, width: SX(QB) - SX(QA), height: sy1 - sy0, fill: COL.Q }, strip);
    el("line", { x1: SX(0), x2: SX(0), y1: by - 6, y2: sy1, stroke: "#000", "stroke-dasharray": "1.5 3" }, strip);
    label(strip, SX(-0.25), sy0 + 19, "~Q~", { "text-anchor": "middle", "font-size": 15 });
    const pGroup = el("g", { class: "pband" }, strip);
    const pRect = el("rect", { y: sy0, height: sy1 - sy0, fill: COL.P, stroke: COL.Pedge, "stroke-dasharray": "3 3" }, pGroup);
    const pLab = label(pGroup, 0, sy0 + 19, "~P~", { "text-anchor": "middle", "font-size": 15 });
    el("line", { x1: SX0, x2: SX1, y1: sy1, y2: sy1, stroke: "#000" }, strip);
    el("path", { d: `M${SX1 - 8} ${sy1 - 4} L${SX1} ${sy1} L${SX1 - 8} ${sy1 + 4}`, fill: "none", stroke: "#000" }, strip);
    label(strip, SX1, sy1 + 18, "~T~", { "text-anchor": "end", "font-size": 15 });
    label(strip, SX(0), sy1 + 18, "~T~_c", { "text-anchor": "middle", "font-size": 15 });
    const bracket = el("path", { fill: "none", stroke: "#000" }, strip);
    const bLab = label(strip, 0, by - 5, "~D~", { "text-anchor": "middle", "font-size": 15 });

    const panels = [
      covPanel($("toy-line"), "line", "Straight line", "Feature 1:  1", "Feature 2:  ~T~ − ~T~_c"),
      covPanel($("toy-rff"), "rff", "RFF, two features", "Feature 1:  cos(~ω~_1~T~ + ~b~_1)", "Feature 2:  cos(~ω~_2~T~ + ~b~_2)")
    ];
    const outs = [$("toy-line-l"), $("toy-rff-l")];

    function update() {
      pRect.setAttribute("x", SX(dist)); pRect.setAttribute("width", SX(dist + WIDTH) - SX(dist));
      pLab.setAttribute("x", SX(dist + WIDTH / 2));
      bracket.setAttribute("d", `M${SX(0)} ${by - 4} V${by + 4} M${SX(0)} ${by} H${SX(dist)} M${SX(dist)} ${by - 4} V${by + 4}`);
      bLab.setAttribute("x", (SX(0) + SX(dist)) / 2);
      panels.forEach((up, i) => { outs[i].textContent = sci(up(dist, view)); });
    }
    const markView = () => viewSeg.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String((+b.dataset.v === 1) === (view > 0.5))));

    // animations are short lists of steps: a pause, a change of view, or a sweep of the distance
    let raf = 0;
    function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; }
    function play(steps) {
      stop();
      if (reduced) {
        for (const st of steps) { if (st.view !== undefined) view = st.view; if (st.to !== undefined) dist = st.to; }
        slider.value = dist; markView(); update(); return;
      }
      let i = 0, t0 = null, start = null;
      const tick = now => {
        const st = steps[i];
        if (t0 === null) { t0 = now; start = { view, dist: st.from !== undefined ? st.from : dist }; }
        const p = st.ms ? Math.min(1, (now - t0) / st.ms) : 1, e = ease(p);
        if (st.view !== undefined) view = start.view + (st.view - start.view) * e;
        if (st.to !== undefined) dist = start.dist + (st.to - start.dist) * e;
        if (st.view !== undefined || st.to !== undefined) { slider.value = dist; update(); }
        if (st.view !== undefined) markView();
        if (p >= 1) { i++; t0 = null; }
        raf = i < steps.length ? requestAnimationFrame(tick) : 0;
      };
      raf = requestAnimationFrame(tick);
    }
    // the first look: the original features, then the plane is stretched until P is round, then P moves away
    const intro = () => play([{ view: 0, from: 0.6, to: 0.6, ms: 0 }, { ms: 900 }, { view: 1, ms: 1800 }, { ms: 500 }, { from: 0.6, to: 2.4, ms: 3800 }]);

    for (const [v, text] of [[0, "Original"], [1, "Rescaled"]]) {
      const b = document.createElement("button");
      b.type = "button"; b.textContent = text; b.dataset.v = v;
      b.addEventListener("click", () => play([{ view: v, ms: 1000 }]));
      viewSeg.appendChild(b);
    }
    slider.addEventListener("input", () => { stop(); dist = parseFloat(slider.value); update(); });
    let grab = null;
    const tAt = e => T0 + (svgX(strip, e) - SX0) / (SX1 - SX0) * (T1 - T0);
    pGroup.addEventListener("pointerdown", e => { stop(); grab = tAt(e) - dist; pGroup.setPointerCapture(e.pointerId); e.preventDefault(); });
    pGroup.addEventListener("pointermove", e => {
      if (grab === null) return;
      dist = Math.max(DMIN, Math.min(DMAX, tAt(e) - grab)); slider.value = dist; update();
    });
    const release = () => { grab = null; };
    pGroup.addEventListener("pointerup", release); pGroup.addEventListener("pointercancel", release);

    $("toy-replay").addEventListener("click", intro);
    markView(); update();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(update);
    let introDone = false;
    onView($("toy"), vis => { if (vis && !introDone) { introDone = true; intro(); } }, 0.5);
  }

  /* ------------------------------------------- the scaling law: polynomials and random Fourier features */
  // The bound against distance in the setting of the toy figure, for a polynomial and for random
  // Fourier features with the same number of features. Random features are a median over seeded
  // draws from a Gaussian spectral measure with length scale 2, the first k of seven for k features.
  function scaleFig() {
    const G = window.Gevp, seg = $("scale-k"), svgs = { poly: $("scale-poly"), rff: $("scale-rff") };
    if (!G || !svgs.poly || !svgs.rff) return;
    const KS = [2, 3, 4, 5, 6, 7], ELL = 2, NDRAW = 32, color = { poly: COL.poly, rff: COL.rff };
    let k = 5;
    const Ds = Array.from({ length: 36 }, (_, i) => DMIN * Math.pow(DMAX / DMIN, i / 35));
    let seed = 7;
    const rand = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    const gauss = () => Math.sqrt(-2 * Math.log(rand())) * Math.cos(2 * Math.PI * rand());
    const draws = Array.from({ length: NDRAW }, () => ({ W: Array.from({ length: 7 }, () => gauss() / ELL), B: Array.from({ length: 7 }, () => 2 * Math.PI * rand()) }));
    const table = { poly: {}, rff: {} };
    for (const kk of KS) table.poly[kk] = Ds.map(D => G.bound(kk - 1, D, D + WIDTH, QA, QB).gamma);
    const rffRow = kk => Ds.map(D => {
      const v = draws.map(dr => G.rffBound(dr.W, dr.B, kk, D, D + WIDTH, QA, QB)).sort((a, b) => a - b);
      return Math.sqrt(v[NDRAW / 2 - 1] * v[NDRAW / 2]);
    });

    const P = {};
    for (const key of ["poly", "rff"]) {
      const svg = svgs[key], fs = svg.getBoundingClientRect().width > 380 ? 1 : 1.16;   // the panels stack and widen on phones
      const A = axes(svg, {
        x0: 82, x1: 388, y0: 20 + 16 * fs, y1: 270, xlim: [DMIN, DMAX], ylim: [1, 1e16], xlog: true, ylog: true, grid: true, fs,
        xticks: ticks([0.5, 1, 2, 4]), yticks: [0, 4, 8, 12, 16].map(e => ({ v: Math.pow(10, e), l: e === 0 ? "1" : `10^{${e}}` })),
        xlabel: "Distance ~D~ from ~P~ to ~T~_c", ylabel: "GEVP bound ~λ~_{max}", ylabelX: 20,
        title: key === "poly" ? "Polynomial" : "RFF"
      });
      const faint = {};
      for (const kk of KS) faint[kk] = el("path", { fill: "none", stroke: color[key], "stroke-opacity": 0.3, "stroke-width": 1.4 }, A.data);
      const exp = el("path", { fill: "none", stroke: "#555", "stroke-width": 1.6, "stroke-dasharray": "7 4" }, A.data);
      const main = el("path", { fill: "none", stroke: color[key], "stroke-width": 2.8 }, A.data);
      P[key] = { A, faint, exp, main, leg: el("g", {}, A.over), fs };
    }
    const curve = (A, ys) => pathOf(Ds.map((D, i) => [A.X(D), A.Y(ys[i])]));
    function draw() {
      for (const key of ["poly", "rff"]) {
        const p = P[key], rows = table[key], r = rows[k];
        for (const kk of KS) {
          p.faint[kk].style.display = kk === k || !rows[kk] ? "none" : "";
          if (rows[kk]) p.faint[kk].setAttribute("d", curve(p.A, rows[kk]));
        }
        p.main.setAttribute("d", r ? curve(p.A, r) : "");
        const pts = [];
        if (r) {
          const s0 = Math.log(r[1] / r[0]) / Math.log(Ds[1] / Ds[0]);
          for (const D of Ds) {
            const v = r[0] * Math.exp(s0 * (D - DMIN) / DMIN);
            pts.push([p.A.X(D), p.A.Y(Math.min(v, 1e18))]);
            if (v > 1e18) break;
          }
        }
        p.exp.setAttribute("d", pts.length ? pathOf(pts) : "");
        p.leg.textContent = "";
        legend(p.leg, p.A.x0 + 8, p.A.y0 + 8, [
          { text: key === "poly" ? `Degree ${k - 1}` : `${k} features`, color: color[key], width: 2.4 },
          { text: key === "poly" ? "Other degrees" : "Other counts", color: color[key], width: 1.2, opacity: 0.4 },
          { text: "Exponential, same start", color: "#555", width: 1.4, dash: "6 4" }
        ], { fs: p.fs });
      }
      seg.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.k === k)));
    }
    for (const kk of KS) {
      const b = document.createElement("button");
      b.type = "button"; b.textContent = kk; b.dataset.k = kk;
      b.addEventListener("click", () => { k = kk; if (!table.rff[k]) table.rff[k] = rffRow(k); draw(); });
      seg.appendChild(b);
    }
    table.rff[k] = rffRow(k);
    draw();
    // the other random-feature medians take a moment, so they are filled in one count at a time once the figure is near
    let started = false;
    onView($("scale"), vis => {
      if (!vis || started) return;
      started = true;
      const order = [k, ...KS.filter(x => x !== k)];
      const next = () => {
        const kk = order.shift();
        if (kk === undefined) return;
        if (!table.rff[kk]) table.rff[kk] = rffRow(kk);
        draw(); setTimeout(next, 0);
      };
      next();
    }, 0);
  }

  /* ------------------------------------------------- lightbox and BibTeX */
  function misc() {
    const box = $("lightbox"), big = box.querySelector("img");
    const open = img => { big.src = img.currentSrc || img.src; big.alt = img.alt; box.classList.add("open"); };
    document.querySelectorAll("img.zoomable, img.sys-grid").forEach(img => img.addEventListener("click", () => open(img)));
    box.addEventListener("click", () => box.classList.remove("open"));
    document.addEventListener("keydown", e => { if (e.key === "Escape") box.classList.remove("open"); });
    const copy = $("copy-bib");
    copy.addEventListener("click", () => {
      const done = () => { copy.textContent = "Copied"; setTimeout(() => { copy.textContent = "Copy"; }, 1600); };
      if (navigator.clipboard) navigator.clipboard.writeText($("bibtex").textContent).then(done, () => {});
    });
  }

  /* ----------------------------------------------- outline: mark the section in view */
  function outline() {
    const links = [...document.querySelectorAll(".toc a")];
    const targets = links.map(a => document.querySelector(a.getAttribute("href")));
    const update = () => {
      const line = window.innerHeight * 0.3;
      let current = 0;
      targets.forEach((t, i) => { if (t && t.getBoundingClientRect().top <= line) current = i; });
      if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) current = links.length - 1;
      links.forEach((a, i) => a.classList.toggle("active", i === current));
    };
    window.addEventListener("scroll", update, { passive: true });   // seven position reads per scroll event, cheap enough
    update();
  }

  function start() {
    for (const fn of [outline, ferro, explorer, boundFig, paperFigs, scaleFig, misc]) {
      try { fn(); } catch (err) { console.error(err); }       // one broken figure should not take the others down
    }
    try { if (window.HEISENBERG_MODELS) hero(window.HEISENBERG_MODELS); } catch (err) { console.error(err); }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
