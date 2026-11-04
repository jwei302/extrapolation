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
    if (tcLabel !== false) label(A.over, A.X(Tc), A.y0 + 17 * fs, typeof tcLabel === "string" ? tcLabel : "~T~_c", { "text-anchor": "middle", "font-size": 14 * fs });
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
    const sliceShade = el("rect", { x: S.x0, y: S.y0, width: S.x1 - S.x0, height: S.y1 - S.y0 }, S.regions);
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
      sliceShade.setAttribute("fill", T >= D.P[0] && T <= D.P[1] ? COL.P : COL.Q);
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
      if (T >= D.P[0]) { where.className = "inP"; where.innerHTML = "in <i>P</i>"; }
      else if (T >= D.Tc) { where.className = ""; where.innerHTML = "in <i>Q</i>, above <i>T</i><sub>c</sub>"; }
      else { where.className = "below"; where.innerHTML = "in <i>Q</i>, below <i>T</i><sub>c</sub>"; }
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

  /* ------------------------------------------------- phase transitions, one tab per system */
  // Each tab pairs a small live simulation (left) with the paper's ground truth: the observable at the
  // chosen parameter (middle) and the derived quantity it traces (right). Middle panels are shaded like
  // the region of the right panel the parameter sits in.
  const ISING_TC = 2.0 / Math.log(1 + Math.SQRT2);
  function bracket(xs, x) {                       // index and weight for linear interpolation, clamped at the ends
    const n = xs.length;
    if (x <= xs[0]) return [0, 0];
    if (x >= xs[n - 1]) return [n - 2, 1];
    let lo = 0, hi = n - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (xs[m] <= x) lo = m; else hi = m; }
    return [lo, (x - xs[lo]) / (xs[hi] - xs[lo])];
  }
  const interp = (xs, ys, x) => { const [i, w] = bracket(xs, x); return ys[i] * (1 - w) + ys[i + 1] * w; };
  const rowAt = (xs, rows, x) => { const [i, w] = bracket(xs, x); return rows[i].map((v, j) => v * (1 - w) + rows[i + 1][j] * w); };
  // a black curve with a ball resting on it, as in the Landau panel
  function curveWithBall(F) {
    const curve = el("path", { fill: "none", stroke: "#000", "stroke-width": 1.6 }, F.data);
    const ball = el("circle", { r: 5.5, fill: COL.poly, stroke: "#fff", "stroke-width": 1 }, F.over);   // unclipped, so it shows at an edge
    return (pts, bx, by) => {
      curve.setAttribute("d", pathOf(pts.map(p => [F.X(p[0]), F.Y(p[1])])));
      ball.setAttribute("cx", F.X(bx)); ball.setAttribute("cy", F.Y(by) - 5.5);
    };
  }
  function grayLattice(ctx, L) {                   // draws +1 sites dark and -1 sites light
    const img = ctx.createImageData(L, L), px = img.data;
    return (s, up) => {
      for (let i = 0; i < L * L; i++) { const c = s[i] === up ? 20 : 218; px[4 * i] = px[4 * i + 1] = px[4 * i + 2] = c; px[4 * i + 3] = 255; }
      ctx.putImageData(img, 0, 0);
    };
  }

  // draws a field in [-1, 1] blurred over a couple of sites, from cream (-1) to navy (+1), with a mild
  // S-curve so domains read as flat color and their walls stay soft
  function smoothLattice(ctx, L, sigma) {
    const N = L * L, img = ctx.createImageData(L, L), px = img.data, a = new Float32Array(N), b = new Float32Array(N);
    const r = Math.ceil(3 * sigma), k = Array.from({ length: 2 * r + 1 }, (_, i) => Math.exp(-((i - r) ** 2) / (2 * sigma * sigma)));
    const ks = k.reduce((p, q) => p + q, 0);
    for (let i = 0; i < k.length; i++) k[i] /= ks;
    const LO = [244, 239, 228], HI = [29, 53, 87];
    return field => {
      for (let y = 0; y < L; y++) for (let x = 0; x < L; x++) {           // periodic, like the lattice
        let v = 0;
        for (let j = -r; j <= r; j++) v += k[j + r] * field[y * L + (x + j + L) % L];
        a[y * L + x] = v;
      }
      for (let y = 0; y < L; y++) for (let x = 0; x < L; x++) {
        let v = 0;
        for (let j = -r; j <= r; j++) v += k[j + r] * a[((y + j + L) % L) * L + x];
        b[y * L + x] = v;
      }
      for (let i = 0; i < N; i++) {
        let u = Math.min(1, Math.max(0, (b[i] + 1) / 2));
        u = 0.5 * u + 0.5 * u * u * (3 - 2 * u);
        px[4 * i] = LO[0] + (HI[0] - LO[0]) * u; px[4 * i + 1] = LO[1] + (HI[1] - LO[1]) * u;
        px[4 * i + 2] = LO[2] + (HI[2] - LO[2]) * u; px[4 * i + 3] = 255;
      }
      ctx.putImageData(img, 0, 0);
    };
  }

  function heisenbergDemo(ctx) {
    const TC = 1.5, L = 256, N = L * L, spins = new Int8Array(N), avg = new Float32Array(N), paint = smoothLattice(ctx, L, 2);
    const accept = new Float64Array(9);
    function sweep(T) {                           // one Metropolis sweep at the Ising temperature whose T_c matches the paper's
      const beta = TC / (T * ISING_TC);
      accept[4] = Math.exp(-4 * beta); accept[8] = Math.exp(-8 * beta);   // flipping costs dE = 2 s h, h the four neighbours
      for (let parity = 0; parity < 2; parity++)  // checkerboard: one sublattice, then the other
        for (let y = 0; y < L; y++) {
          const row = y * L, up = ((y + L - 1) % L) * L, dn = ((y + 1) % L) * L;
          for (let x = (y + parity) & 1; x < L; x += 2) {
            const i = row + x, dE = 2 * spins[i] * (spins[up + x] + spins[dn + x] + spins[row + (x + L - 1) % L] + spins[row + (x + 1) % L]);
            if (dE <= 0 || Math.random() < accept[dE]) spins[i] = -spins[i];
          }
        }
    }
    const f = (t, m) => 0.5 * (1 - TC / t) * m * m + Math.pow(TC / t, 3) * Math.pow(m, 4) / 12 + 0.01;
    const mstar = t => (t < TC ? Math.sqrt(3 * (TC / t - 1) / Math.pow(TC / t, 3)) : 0);
    const ms = Array.from({ length: 201 }, (_, i) => -1.25 + 2.5 * i / 200);
    return {
      label: "Temperature <i>T</i>", sym: "<i>T</i>", qty: "|<i>m</i>|", go: "Cool through <i>T</i><sub>c</sub>",
      aria: "A lattice of spins at the chosen temperature", size: L, pixelated: false,
      lo: 1, hi: 3, step: 0.005, from: 3, to: 1, P: [2, 3], Q: [1, 2], tc: TC, fmt: t => t.toFixed(2),
      caption: "The ferromagnetic Heisenberg model describes interacting magnetic spins, represented here by an analytical Landau&ndash;Ginzburg free energy. Above <i>T</i><sub>c</sub>, the system has zero spontaneous magnetization and a single free-energy minimum. Below <i>T</i><sub>c</sub>, magnetic order emerges and the free energy develops two symmetric minima at nonzero magnetization.",
      reset(T) {
        for (let i = 0; i < N; i++) spins[i] = Math.random() < 0.5 ? 1 : -1;
        for (let n = 0; n < 60; n++) sweep(T);
        avg.set(spins);
      },
      frame(T, k) {
        if (!reduced || k % 4 === 0) sweep(T);
        for (let i = 0; i < N; i++) avg[i] = 0.75 * avg[i] + 0.25 * spins[i];   // a short exposure, so single flips don't flicker
        paint(avg);
        return mstar(T).toFixed(2);               // the lattice can hold several domains, so report the Landau minimum
      },
      mid: {
        xlim: [-1.25, 1.25], ylim: [-0.06, 0.45], xticks: ticks([-1, 0, 1], one), yticks: ticks([0, 0.2, 0.4], one),
        xlabel: "Magnetization ~m~", ylabel: "Free energy ~f~", ylabelX: 16, title: "Free energy"
      },
      drawMid(F) {
        const draw = curveWithBall(F);
        return T => draw(ms.map(m => [m, f(T, m)]), mstar(T), f(T, mstar(T)));
      },
      right: {
        xticks: ticks([1, 2, 3], one), ylim: [0, 0.8], yticks: ticks([0, 0.4, 0.8], one),
        xlabel: "Temperature ~T~", ylabel: "|~m~|", ylabelX: 18, title: "Magnetization"
      },
      op: mstar
    };
  }

  function floryDemo(ctx) {
    const TC = 1, L = 100, N = L * L, s = new Int8Array(N), paint = grayLattice(ctx, L), boltz = new Float64Array(33);
    function exchange(T, tries) {                 // Kawasaki moves: swap unlike neighbours, so the composition is conserved
      const beta = TC / (T * ISING_TC);
      for (let d = -12; d <= 20; d += 2) boltz[d + 12] = Math.min(1, Math.exp(-d * beta));
      const nb = i => { const x = i % L, y = (i / L) | 0; return s[y * L + (x + 1) % L] + s[y * L + (x + L - 1) % L] + s[((y + 1) % L) * L + x] + s[((y + L - 1) % L) * L + x]; };
      for (let a = 0; a < tries; a++) {
        const i = (Math.random() * N) | 0, x = i % L, y = (i / L) | 0, r = (Math.random() * 4) | 0;
        const j = r === 0 ? y * L + (x + 1) % L : r === 1 ? y * L + (x + L - 1) % L : r === 2 ? ((y + 1) % L) * L + x : ((y + L - 1) % L) * L + x;
        const si = s[i];
        if (si === s[j]) continue;
        const dE = 2 * si * nb(i) + 2 * s[j] * nb(j) + 4;
        if (dE <= 0 || Math.random() < boltz[dE + 12]) { s[i] = -si; s[j] = si; }
      }
    }
    const f = (t, m) => { const x = 0.5 + m; return t * (x * Math.log(x) + (1 - x) * Math.log(1 - x)) + 2 * TC * x * (1 - x); };
    const ts = Array.from({ length: 801 }, (_, i) => 0.5 + 2 * i / 800);
    const table = ts.map(t => {                   // the minimizer solves t ln((1/2 + m)/(1/2 - m)) = 4 T_c m
      if (t >= TC) return 0;
      let a = 1e-9, b = 0.5 - 1e-12;
      for (let it = 0; it < 50; it++) { const m = (a + b) / 2; if (t * Math.log((0.5 + m) / (0.5 - m)) < 4 * TC * m) a = m; else b = m; }
      return (a + b) / 2;
    });
    const mstar = t => interp(ts, table, t);
    const ms = Array.from({ length: 201 }, (_, i) => -0.499 + 0.998 * i / 200);
    return {
      label: "Temperature <i>T</i>", sym: "<i>T</i>", qty: "|<i>m</i>*|", go: "Cool through <i>T</i><sub>c</sub>",
      aria: "A lattice of two mixed species at the chosen temperature", size: L, pixelated: true,
      lo: 0.5, hi: 2.5, step: 0.005, from: 2.5, to: 0.5, P: [1.5, 2.5], Q: [0.5, 1.5], tc: TC, fmt: t => t.toFixed(2),
      caption: "The analytical Flory&ndash;Huggins model describes whether two substances mix uniformly or separate into distinct phases. At high temperatures, entropy favors a uniform mixture. Below <i>T</i><sub>c</sub>, the mixture separates into phases with different compositions, and the mixing free energy develops a double well.",
      reset(T) {
        for (let i = 0; i < N; i++) s[i] = i < N / 2 ? 1 : -1;
        for (let i = N - 1; i > 0; i--) { const j = (Math.random() * (i + 1)) | 0, t = s[i]; s[i] = s[j]; s[j] = t; }
        exchange(T, 4 * N);
      },
      frame(T) { exchange(T, reduced ? N : 4 * N); paint(s, 1); return mstar(T).toFixed(2); },
      mid: {
        xlim: [-0.5, 0.5], ylim: [-0.22, 0.5], xticks: ticks([-0.4, 0, 0.4], one), yticks: ticks([-0.2, 0, 0.2, 0.4], one),
        xlabel: "Composition ~m~", ylabel: "~f~(~m~) − ~f~(0)", ylabelX: 16, title: "Free energy"
      },
      drawMid(F) {
        const draw = curveWithBall(F);
        return T => { const f0 = f(T, 0), m = mstar(T); draw(ms.map(x => [x, f(T, x) - f0]), m, f(T, m) - f0); };
      },
      right: {
        xticks: ticks([0.5, 1.5, 2.5], one), ylim: [0, 0.5], yticks: ticks([0, 0.2, 0.4], one),
        xlabel: "Temperature ~T~", ylabel: "|~m~^*|", ylabelX: 18, title: "Composition"
      },
      op: mstar
    };
  }

  function polaronDemo(ctx) {
    const D = window.TRANSITIONS.polaron, N = 48, S = 340, psi = new Float64Array(N), Hpsi = new Float64Array(N);
    function relax(c, iters) {                    // imaginary-time steps psi <- psi - tau H psi, with H_{n,n+j} = c_j / 2
      for (let it = 0; it < iters; it++) {
        for (let n = 0; n < N; n++) {
          let v = 0;
          for (let j = 1; j <= 3; j++) { if (n >= j) v += psi[n - j] * c[j]; if (n + j < N) v += psi[n + j] * c[j]; }
          Hpsi[n] = 0.5 * v;
        }
        let norm = 0;
        for (let n = 0; n < N; n++) { psi[n] -= 0.3 * Hpsi[n]; norm += psi[n] * psi[n]; }
        norm = Math.sqrt(norm);
        for (let n = 0; n < N; n++) psi[n] /= norm;
      }
    }
    const kstar = l => interp(D.lam, D.kstar, l);
    return {
      label: "Coupling <i>&lambda;</i>", sym: "<i>&lambda;</i>", qty: "<i>K</i>*", go: "Raise <i>&lambda;</i> through <i>&lambda;</i><sub>c</sub>",
      aria: "The ground-state wavefunction of the electron on a chain at the chosen coupling", size: S, pixelated: false,
      lo: 0.2, hi: 1.0, step: 0.002, from: 0.2, to: 1.0, P: [0.2, 0.6], Q: [0.6, 1.0], tc: 0.6839, fmt: t => t.toFixed(2),
      caption: "The numerically simulated Su&ndash;Schrieffer&ndash;Heeger (SSH) polaron model describes an electron whose hopping between lattice sites is coupled to lattice vibrations. At weak coupling, its energy is minimized at zero momentum. Beyond a critical coupling, the minimum shifts to nonzero momentum, producing a sharp change in the ground state.",
      reset(l) { for (let n = 0; n < N; n++) psi[n] = 1 + 0.6 * (Math.random() - 0.5); relax(rowAt(D.lam, D.hop, l), 200); },
      frame(l) {
        for (let n = 0; n < N; n++) psi[n] += 2e-3 * (Math.random() - 0.5);   // a little noise, so no excited state lingers
        relax(rowAt(D.lam, D.hop, l), 40);
        const pad = 18, dx = (S - 2 * pad) / (N - 1), y0 = S / 2, amp = 1.5 * S;
        ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, S, S);
        ctx.strokeStyle = "#000"; ctx.lineWidth = 1.2;
        ctx.beginPath(); ctx.moveTo(pad - 8, y0); ctx.lineTo(S - pad + 8, y0); ctx.stroke();
        ctx.strokeStyle = COL.poly; ctx.lineWidth = 3;
        ctx.beginPath();
        for (let n = 0; n < N; n++) { ctx.moveTo(pad + n * dx, y0); ctx.lineTo(pad + n * dx, y0 - amp * psi[n]); }
        ctx.stroke();
        ctx.fillStyle = COL.poly; ctx.beginPath();
        for (let n = 0; n < N; n++) { const x = pad + n * dx, y = y0 - amp * psi[n]; ctx.moveTo(x + 3.6, y); ctx.arc(x, y, 3.6, 0, 2 * Math.PI); }
        ctx.fill();
        ctx.fillStyle = "#000"; ctx.beginPath();
        for (let n = 0; n < N; n++) { ctx.moveTo(pad + n * dx + 2.6, y0); ctx.arc(pad + n * dx, y0, 2.6, 0, 2 * Math.PI); }
        ctx.fill();
        return kstar(l).toFixed(2);
      },
      mid: {
        xlim: [0, 0.6 * Math.PI], ylim: [-0.2, 1.0], xticks: ticks([0, 0.5, 1, 1.5], one), yticks: ticks([0, 0.5, 1], one),
        xlabel: "Momentum ~K~", ylabel: "~E~(~K~) − ~E~(0)", ylabelX: 16, title: "Polaron dispersion"
      },
      drawMid(F) {
        const draw = curveWithBall(F);
        return l => {
          const row = rowAt(D.lam, D.E, l), k = kstar(l);
          draw(D.K.map((K, j) => [K, row[j] - row[0]]), k, interp(D.K, row, k) - row[0]);
        };
      },
      right: {
        xticks: ticks([0.2, 0.6, 1.0], one), ylim: [0, 1.0], yticks: ticks([0, 0.5, 1], one),
        xlabel: "Coupling ~λ~", ylabel: "~K~^*", ylabelX: 18, title: "Ground-state momentum", tcLabel: "~λ~_c"
      },
      op: kstar
    };
  }

  function convectionDemo(ctx) {
    // one cell of the paper's Rayleigh-Benard setup: free-slip walls, insulating sides, Pr = 1, in units of the
    // thermal diffusion time. Vorticity-streamfunction on a (M+1)^2 grid, Heun steps, Poisson by sine transforms.
    const D = window.TRANSITIONS.rb, logRa = D.ra.map(Math.log10);
    const M = 24, n = M - 1, W = M + 1, h = 1 / M, NN = W * W, S = 340, R = 120;
    const Smat = new Float64Array(n * n), kap = new Float64Array(n * n), A = new Float64Array(n * n), C = new Float64Array(n * n);
    for (let a = 0; a < n; a++) for (let b = 0; b < n; b++) Smat[a * n + b] = Math.sin(Math.PI * (a + 1) * (b + 1) / M);
    for (let q = 0; q < n; q++) for (let p = 0; p < n; p++)
      kap[q * n + p] = 4 / (h * h) * (Math.sin((p + 1) * Math.PI / (2 * M)) ** 2 + Math.sin((q + 1) * Math.PI / (2 * M)) ** 2);
    function sandwich() {                           // A <- S A S^T
      for (let r = 0; r < n; r++) for (let k = 0; k < n; k++) { let v = 0; for (let m = 0; m < n; m++) v += A[r * n + m] * Smat[k * n + m]; C[r * n + k] = v; }
      for (let q = 0; q < n; q++) for (let k = 0; k < n; k++) { let v = 0; for (let r = 0; r < n; r++) v += Smat[q * n + r] * C[r * n + k]; A[q * n + k] = v; }
    }
    const T = new Float64Array(NN), om = new Float64Array(NN), psi = new Float64Array(NN), u = new Float64Array(NN), w = new Float64Array(NN);
    const T1 = new Float64Array(NN), om1 = new Float64Array(NN), kT = new Float64Array(NN), kO = new Float64Array(NN), k2T = new Float64Array(NN), k2O = new Float64Array(NN);
    function velocity(o) {                          // lap psi = -omega with psi = 0 on the walls, then u = psi_z, w = -psi_x
      for (let j = 1; j < M; j++) for (let i = 1; i < M; i++) A[(j - 1) * n + i - 1] = o[j * W + i];
      sandwich();
      for (let t = 0; t < n * n; t++) A[t] *= 4 / (M * M) / kap[t];
      sandwich();
      for (let j = 1; j < M; j++) for (let i = 1; i < M; i++) psi[j * W + i] = A[(j - 1) * n + i - 1];
      for (let j = 0; j <= M; j++) for (let i = 0; i <= M; i++) {
        const c = j * W + i;                        // psi is odd across every wall
        const pl = i > 0 ? psi[c - 1] : -psi[c + 1], pr = i < M ? psi[c + 1] : -psi[c - 1];
        const pd = j > 0 ? psi[c - W] : -psi[c + W], pu = j < M ? psi[c + W] : -psi[c - W];
        u[c] = (pu - pd) / (2 * h); w[c] = -(pr - pl) / (2 * h);
      }
    }
    function rhs(Tt, o, dT, dO, Ra) {
      velocity(o);
      const ih = 1 / (2 * h), ih2 = 1 / (h * h);
      for (let j = 1; j < M; j++) for (let i = 0; i <= M; i++) {
        const c = j * W + i;
        const Tl = i > 0 ? Tt[c - 1] : Tt[c + 1], Tr = i < M ? Tt[c + 1] : Tt[c - 1], Tx = (Tr - Tl) * ih;
        dT[c] = -(u[c] * Tx + w[c] * (Tt[c + W] - Tt[c - W]) * ih) + (Tr + Tl + Tt[c + W] + Tt[c - W] - 4 * Tt[c]) * ih2;
        if (i === 0 || i === M) { dO[c] = 0; continue; }
        const Ox = (o[c + 1] - o[c - 1]) * ih, Oz = (o[c + W] - o[c - W]) * ih;
        dO[c] = -(u[c] * Ox + w[c] * Oz) + (o[c + 1] + o[c - 1] + o[c + W] + o[c - W] - 4 * o[c]) * ih2 + Ra * Tx;
      }
    }
    let umax = 0;
    function step(Ra) {
      const dt = Math.min(0.24 * h * h, 0.4 * h / Math.max(umax, 1e-9));
      rhs(T, om, kT, kO, Ra);
      for (let c = 0; c < NN; c++) { T1[c] = T[c] + dt * kT[c]; om1[c] = om[c] + dt * kO[c]; }
      rhs(T1, om1, k2T, k2O, Ra);
      umax = 0;
      for (let j = 1; j < M; j++) for (let i = 0; i <= M; i++) {
        const c = j * W + i;
        T[c] += 0.5 * dt * (kT[c] + k2T[c]); om[c] += 0.5 * dt * (kO[c] + k2O[c]);
        umax = Math.max(umax, Math.abs(u[c]), Math.abs(w[c]));
      }
      return dt;
    }
    const kick = a => { for (let j = 1; j < M; j++) for (let i = 1; i < M; i++) om[j * W + i] += a * Math.sin(Math.PI * i * h) * Math.sin(Math.PI * j * h); };
    function phi() {                                // RMS departure of the mean profile from conduction, 1 - z
      let v = 0;
      for (let j = 0; j <= M; j++) {
        let m = 0;
        for (let i = 0; i <= M; i++) m += T[j * W + i] * (i === 0 || i === M ? 0.5 : 1);
        v += (m / M - (1 - j * h)) ** 2;
      }
      return Math.sqrt(v / W);
    }
    // coolwarm, from cold (blue) to hot (red)
    const STOPS = [[59, 76, 192], [98, 130, 234], [141, 176, 254], [185, 208, 249], [221, 220, 220], [245, 196, 172], [244, 152, 122], [221, 95, 75], [180, 4, 38]];
    const LUT = new Uint8Array(256 * 3);
    for (let q = 0; q < 256; q++) {
      const x = q / 255 * 8, a = Math.min(7, Math.floor(x)), f = x - a;
      for (let ch = 0; ch < 3; ch++) LUT[3 * q + ch] = Math.round(STOPS[a][ch] * (1 - f) + STOPS[a + 1][ch] * f);
    }
    const off = document.createElement("canvas"); off.width = off.height = R;
    const octx = off.getContext("2d"), img = octx.createImageData(R, R), px = img.data;
    const NP = 160, tx = new Float64Array(NP), tz = new Float64Array(NP);
    const spawn = p => { tx[p] = 0.02 + 0.96 * Math.random(); tz[p] = 0.02 + 0.96 * Math.random(); };
    const at = (F, x, z) => {                       // bilinear from the grid
      const fx = Math.min(M - 1e-9, x * M), fz = Math.min(M - 1e-9, z * M), i = fx | 0, j = fz | 0, a = fx - i, b = fz - j, c = j * W + i;
      return (F[c] * (1 - a) + F[c + 1] * a) * (1 - b) + (F[c + W] * (1 - a) + F[c + W + 1] * a) * b;
    };
    return {
      label: "Rayleigh number Ra", sym: "Ra", qty: "&Phi;", go: "Lower Ra through Ra<sub>c</sub>",
      aria: "A convection cell heated from below, colored by temperature, at the chosen Rayleigh number", size: S, pixelated: false,
      lo: logRa[0], hi: logRa[logRa.length - 1], step: 0.002, from: logRa[logRa.length - 1], to: logRa[0],
      P: [Math.log10(1500), Math.log10(7500)], Q: [Math.log10(300), Math.log10(1500)], tc: Math.log10(776.2),
      fmt: t => String(Math.round(Math.pow(10, t))),
      caption: "Rayleigh&ndash;B&eacute;nard convection is the onset of circulation in a fluid layer heated from below and cooled from above, modeled here by numerical simulation. At low Rayleigh numbers, heat passes through the stationary fluid by conduction. Above a critical Rayleigh number, buoyancy drives convection, redistributing heat and flattening the temperature profile in the interior.",
      reset(t) {
        for (let j = 0; j <= M; j++) for (let i = 0; i <= M; i++) { T[j * W + i] = 1 - j * h; om[j * W + i] = 0; }
        kick(300); umax = 0;
        for (let k = 0; k < 200; k++) step(Math.pow(10, t));
        for (let p = 0; p < NP; p++) spawn(p);
      },
      frame(t) {
        const Ra = Math.pow(10, t), t0 = performance.now();
        kick(0.4 * (Math.random() - 0.5));          // a little noise, so convection can start above Ra_c
        for (let sim = 0; sim < 0.008 && performance.now() - t0 < 6;) sim += step(Ra);
        for (let p = 0; p < NP; p++) {
          tx[p] = Math.min(0.995, Math.max(0.005, tx[p] + 5e-4 * at(u, tx[p], tz[p])));
          tz[p] = Math.min(0.995, Math.max(0.005, tz[p] + 5e-4 * at(w, tx[p], tz[p])));
          if (Math.random() < 0.003) spawn(p);
        }
        for (let r = 0; r < R; r++) for (let c = 0; c < R; c++) {
          const q = Math.max(0, Math.min(255, Math.round(255 * at(T, (c + 0.5) / R, 1 - (r + 0.5) / R)))), o = 4 * (r * R + c);
          px[o] = LUT[3 * q]; px[o + 1] = LUT[3 * q + 1]; px[o + 2] = LUT[3 * q + 2]; px[o + 3] = 255;
        }
        octx.putImageData(img, 0, 0);
        ctx.imageSmoothingEnabled = true; ctx.drawImage(off, 0, 0, S, S);
        ctx.fillStyle = "rgba(15, 15, 15, 0.8)"; ctx.beginPath();
        for (let p = 0; p < NP; p++) { const x = tx[p] * S, y = (1 - tz[p]) * S; ctx.moveTo(x + 2.4, y); ctx.arc(x, y, 2.4, 0, 2 * Math.PI); }
        ctx.fill();
        return phi().toFixed(2);
      },
      mid: {
        xlim: [0, 1], ylim: [0, 1], xticks: ticks([0, 0.5, 1], one), yticks: ticks([0, 0.5, 1], one),
        xlabel: "Mean temperature", ylabel: "Height ~z~", ylabelX: 16, title: "Temperature profile"
      },
      drawMid(F) {
        el("path", { d: `M${F.X(1)} ${F.Y(0)}L${F.X(0)} ${F.Y(1)}`, fill: "none", stroke: "#000", "stroke-width": 1.2, "stroke-dasharray": "4 3" }, F.data);
        const gaps = el("path", { fill: "none", stroke: COL.poly, "stroke-width": 2 }, F.data);
        const curve = el("path", { fill: "none", stroke: "#000", "stroke-width": 1.6 }, F.data);
        return t => {
          const row = rowAt(logRa, D.T, t);
          curve.setAttribute("d", pathOf(D.z.map((z, j) => [F.X(row[j]), F.Y(z)])));
          let d = "";
          for (let j = 4; j < D.z.length - 1; j += 4) d += `M${F.X(1 - D.z[j]).toFixed(1)} ${F.Y(D.z[j]).toFixed(1)}H${F.X(row[j]).toFixed(1)}`;
          gaps.setAttribute("d", d);
        };
      },
      right: {
        xticks: [{ v: Math.log10(300), l: "300" }, { v: 3, l: "1000" }, { v: Math.log10(3000), l: "3000" }],
        ylim: [0, 0.25], yticks: ticks([0, 0.1, 0.2], one),
        xlabel: "Rayleigh number Ra", ylabel: "Φ", ylabelX: 18, title: "Convective amplitude", tcLabel: "Ra_c"
      },
      op: t => interp(logRa, D.phi, t)
    };
  }

  function arpesDemo(ctx) {
    // a model image, not the data: the BCS spectral function A(k, w) f(w) with self-energy
    // -i G1 + Delta^2 / (w + eps_k + i G0), and a gap Delta(T) that closes at T_gap
    const D = window.TRANSITIONS.arpes, TG = 90, D0 = 14, G1 = 8, G0 = 1, Ehi = 15, Elo = -45, S = 340, R = 120;
    const off = document.createElement("canvas"); off.width = off.height = R;
    const octx = off.getContext("2d"), img = octx.createImageData(R, R), px = img.data, I = new Float64Array(R * R);
    function spectrum(T) {
      const kT = 0.08617 * T, gap = T < TG ? D0 * Math.tanh(1.74 * Math.sqrt(TG / T - 1)) : 0, g2 = gap * gap;
      for (let r = 0; r < R; r++) {
        const E = Ehi - (r + 0.5) / R * (Ehi - Elo), fermi = 1 / (Math.exp(E / kT) + 1);
        for (let c = 0; c < R; c++) {
          const eps = 60 * (2 * (c + 0.5) / R - 1), q = (E + eps) * (E + eps) + G0 * G0;
          const a = E - eps - g2 * (E + eps) / q, b = G1 + g2 * G0 / q;
          I[r * R + c] = b / (Math.PI * (a * a + b * b)) * fermi;
        }
      }
      return I;
    }
    const peak = spectrum(D.T[0]).reduce((m, v) => Math.max(m, v), 0);
    let shown = NaN;
    const peakAt = T => interp(D.T, D.peak, T);
    return {
      label: "Temperature <i>T</i>", sym: "<i>T</i>", qty: "&minus;<i>E</i>*", unit: "meV", go: "Cool through <i>T</i><sub>gap</sub>",
      aria: "A model photoemission image near the Fermi momentum at the chosen temperature", size: S, pixelated: false,
      lo: 65, hi: 150, step: 0.1, from: 150, to: 65, P: [95, 150], Q: [65, 95], tc: TG, fmt: t => t.toFixed(0) + " K",
      caption: "Angle-resolved photoemission spectroscopy (ARPES) probes a material&rsquo;s electronic structure by measuring the energies and momenta of emitted electrons. Here, experimental measurements of a cuprate superconductor by <a href='#ref-he'>He et al. (2021)</a> reveal a gap opening on cooling and a corresponding shift in the spectral peak. In this sample, the gap closes near 90 K, above the superconducting transition near 66 K.",
      reset() { shown = NaN; },
      frame(T) {
        if (!(Math.abs(T - shown) < 0.05)) {
          spectrum(T);
          for (let k = 0; k < R * R; k++) { const g = Math.round(255 * (1 - Math.pow(Math.min(1, I[k] / peak), 0.6))); px[4 * k] = px[4 * k + 1] = px[4 * k + 2] = g; px[4 * k + 3] = 255; }
          octx.putImageData(img, 0, 0);
          shown = T;
        }
        ctx.imageSmoothingEnabled = true; ctx.drawImage(off, 0, 0, S, S);
        const yF = Ehi / (Ehi - Elo) * S;
        ctx.strokeStyle = COL.poly; ctx.lineWidth = 2; ctx.setLineDash([3, 5]);
        ctx.beginPath(); ctx.moveTo(0, yF); ctx.lineTo(S, yF); ctx.stroke(); ctx.setLineDash([]);
        return peakAt(T).toFixed(1);
      },
      mid: {
        xlim: [-25, 0], ylim: [3.4, 6.0], xticks: ticks([-20, -10, 0], v => (v < 0 ? "−" : "") + Math.abs(v)), yticks: ticks([4, 5, 6]),
        xlabel: "Energy ~E~ (meV)", ylabel: "Intensity ~I~", ylabelX: 16, title: "Measured spectrum"
      },
      drawMid(F) {
        const draw = curveWithBall(F);
        return T => { const row = rowAt(D.T, D.I, T), e = -peakAt(T); draw(D.E.map((E, j) => [E, row[j]]), e, interp(D.E, row, e)); };
      },
      right: {
        xticks: ticks([70, 100, 130]), ylim: [0, 12.5], yticks: ticks([0, 5, 10]),
        xlabel: "Temperature ~T~ (K)", ylabel: "−~E~^* (meV)", ylabelX: 18, title: "Peak energy", tcLabel: "~T~_{gap}"
      },
      op: peakAt
    };
  }

  function ferro() {
    const fig = $("ferro"), canvas = $("lattice"), ctx = canvas.getContext("2d"), slider = $("temp"), go = $("cool");
    const svgF = $("landscape"), svgM = $("opcurve"), plabel = $("ferro-param"), readout = $("ferro-readout"), cap = $("ferro-cap");
    const MAKE = { heisenberg: heisenbergDemo, flory: floryDemo, polaron: polaronDemo, rb: convectionDemo, arpes: arpesDemo };
    const made = {}, visited = new Set(), box = { x0: 66, x1: 308, y0: 34, y1: 206, grid: true, fs: 1.3 };
    let d = null, T = 0, cooling = null, frames = 0, running = false, raf = 0, last = null;
    let setMid, shade, M, trail, minDot, tval, qval;

    function select(id) {
      d = made[id] || (made[id] = MAKE[id](ctx));
      cooling = null; visited.clear(); last = null; T = d.from;
      slider.min = d.lo; slider.max = d.hi; slider.step = d.step; slider.value = T;
      plabel.innerHTML = d.label; go.innerHTML = d.go; cap.innerHTML = d.caption;
      readout.innerHTML = `${d.sym} = <b></b>, ${d.qty} = <b></b>${d.unit ? " " + d.unit : ""}`;
      [tval, qval] = readout.querySelectorAll("b");
      canvas.width = canvas.height = d.size;
      canvas.style.imageRendering = d.pixelated ? "pixelated" : "auto";
      canvas.setAttribute("aria-label", d.aria);
      svgF.textContent = ""; svgM.textContent = "";
      const F = axes(svgF, Object.assign({}, box, d.mid));
      shade = el("rect", { x: F.x0, y: F.y0, width: F.x1 - F.x0, height: F.y1 - F.y0 }, F.regions);
      setMid = d.drawMid(F);
      M = axes(svgM, Object.assign({}, box, { xlim: [d.lo, d.hi] }, d.right));
      shadeRegions(M, d.P, d.Q, d.tc, d.right.tcLabel || true, 1.3);
      trail = el("path", { fill: "none", stroke: COL.poly, "stroke-width": 2 }, M.data);
      minDot = el("circle", { r: 5, fill: COL.poly, stroke: "#fff", "stroke-width": 1 }, M.over);
      d.reset(T);
      render();
    }
    function render() {
      qval.textContent = d.frame(T, frames);
      setMid(T);
      shade.setAttribute("fill", T >= d.P[0] && T <= d.P[1] ? COL.P : COL.Q);   // the middle panel takes the color of T's region
      const k = Math.round((T - d.lo) / (d.hi - d.lo) * 400);      // fill in the range passed since the last frame
      for (let v = Math.min(k, last ?? k); v <= Math.max(k, last ?? k); v++) visited.add(v);
      last = k;
      const ts = [...visited].sort((a, b) => a - b).map(v => d.lo + v / 400 * (d.hi - d.lo));
      trail.setAttribute("d", pathOf(ts.map(t => [M.X(t), M.Y(d.op(t))])));
      minDot.setAttribute("cx", M.X(T)); minDot.setAttribute("cy", M.Y(d.op(T)));
      tval.textContent = d.fmt(T);
    }
    function frame(now) {
      frames++;
      if (cooling) {
        const p = Math.min(1, (now - cooling.t0) / cooling.ms);
        T = d.from + (d.to - d.from) * p; slider.value = T;
        if (p >= 1) cooling = null;
      }
      render();
      if (running) raf = requestAnimationFrame(frame);
    }
    slider.addEventListener("input", () => { cooling = null; T = parseFloat(slider.value); });
    go.addEventListener("click", () => { visited.clear(); last = null; cooling = { t0: performance.now(), ms: reduced ? 1 : 24000 }; });
    tabbedFigure(fig, select);
    onView(fig, vis => {                            // only simulate while the demo is on screen
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
      note: "Below the transition, the temperature profile is linear in height and independent of Rayleigh number. The MLP approximates this simple profile well but misplaces the transition." },
    { id: "arpes", tab: "ARPES", kind: "Experiment", color: "#d95f02", gh: 786,
      desc: 'Spectral intensity <i>I</i>(<i>T</i>, <i>E</i>) of overdoped Pb-doped Bi-2212, measured by angle-resolved photoemission [<a href="#ref-he">He et al. 2021</a>, <a href="#ref-chen">Chen et al. 2025</a>]. The antinodal gap closes well above the resistive <i>T</i><sub>c</sub>, so we split <i>P</i> and <i>Q</i> at the gap-closing temperature <i>T</i><sub>gap</sub>. Derived quantity: the spectral peak energy <span class=nw>&minus;<i>E</i>*(<i>T</i>)</span>, a signature of gap closing.',
      nmse: [3.8e-2, 3.4e-2, 8.3e-3, 1.1e-1], rel: [11.9, 12.0, 5.4, 23.1], tc: null,
      note: "The spectral gap closes above the superconducting transition, so no critical-point error is reported. The MLP predicts the peak shift in the wrong direction." }
  ];
  function explorer() {
    const tabs = document.querySelector("#explorer .tabs"), grid = $("sys-grid"), note = $("sys-note"), bars = $("sys-bars");
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
