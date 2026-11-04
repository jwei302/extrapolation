// The GEVP bound for degree-d polynomials in one dimension, as in the paper:
// Gamma = sup_g E_Q[g^2] / E_P[g^2] over polynomials g of degree <= d, with P and Q
// uniform on two intervals. In a basis orthonormal on P the denominator is the identity,
// so the generalized eigenvalues are the eigenvalues of A = E_Q[psi psi^T]; this keeps the
// problem well conditioned even when Gamma reaches 1e15.
(function (root) {
  const gl = {};                                    // Gauss-Legendre rules, cached by size
  function gaussLegendre(n) {
    if (gl[n]) return gl[n];
    const x = new Float64Array(n), w = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      let z = Math.cos(Math.PI * (i + 0.75) / (n + 0.5)), dp = 1;
      for (let it = 0; it < 100; it++) {
        let p1 = 1, p0 = 0;
        for (let j = 1; j <= n; j++) { const pm = p0; p0 = p1; p1 = ((2 * j - 1) * z * p0 - (j - 1) * pm) / j; }
        dp = n * (z * p1 - p0) / (z * z - 1);
        const z0 = z; z -= p1 / dp;
        if (Math.abs(z - z0) < 1e-16) break;
      }
      x[i] = z; w[i] = 2 / ((1 - z * z) * dp * dp);
    }
    return (gl[n] = { x, w });
  }

  // Legendre polynomials orthonormal under the uniform measure on [a, b]
  function psi(t, d, a, b, out) {
    const u = 2 * (t - a) / (b - a) - 1;
    let pm = 1, p = u;
    out[0] = 1;
    if (d >= 1) out[1] = Math.sqrt(3) * u;
    for (let k = 1; k < d; k++) {
      const pn = ((2 * k + 1) * u * p - k * pm) / (k + 1);
      pm = p; p = pn; out[k + 1] = Math.sqrt(2 * k + 3) * pn;
    }
    return out;
  }

  // A = E_Q[psi psi^T] in the basis orthonormal on P = [pa, pb], with Q = [qa, qb]
  function gram(d, pa, pb, qa, qb) {
    const n = d + 1, { x, w } = gaussLegendre(d + 2), v = new Float64Array(n);
    const A = Array.from({ length: n }, () => new Array(n).fill(0));
    for (let i = 0; i < x.length; i++) {
      psi(qa + (qb - qa) * (x[i] + 1) / 2, d, pa, pb, v);
      const wi = w[i] / 2;
      for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) A[r][c] += wi * v[r] * v[c];
    }
    return A;
  }

  // cyclic Jacobi for a small symmetric matrix; all eigenpairs, largest first
  function eigen(A0) {
    const A = A0.map(r => r.slice()), n = A.length, V = A.map((_, i) => A.map((__, j) => (i === j ? 1 : 0)));
    for (let sweep = 0; sweep < 60; sweep++) {
      let off = 0, diag = 0;
      for (let p = 0; p < n; p++) { diag += A[p][p] * A[p][p]; for (let q = p + 1; q < n; q++) off += A[p][q] * A[p][q]; }
      if (off <= 1e-30 * diag) break;
      for (let p = 0; p < n; p++) for (let q = p + 1; q < n; q++) {
        if (A[p][q] === 0) continue;
        const th = (A[q][q] - A[p][p]) / (2 * A[p][q]);
        const t = (th >= 0 ? 1 : -1) / (Math.abs(th) + Math.sqrt(th * th + 1));
        const c = 1 / Math.sqrt(t * t + 1), s = t * c;
        for (let k = 0; k < n; k++) { const a = A[k][p], b = A[k][q]; A[k][p] = c * a - s * b; A[k][q] = s * a + c * b; }
        for (let k = 0; k < n; k++) { const a = A[p][k], b = A[q][k]; A[p][k] = c * a - s * b; A[q][k] = s * a + c * b; }
        for (let k = 0; k < n; k++) { const a = V[k][p], b = V[k][q]; V[k][p] = c * a - s * b; V[k][q] = s * a + c * b; }
      }
    }
    const order = [...Array(n).keys()].sort((i, j) => A[j][j] - A[i][i]);
    return { values: order.map(i => A[i][i]), vectors: order.map(i => V.map(row => row[i])) };
  }

  // the full generalized spectrum, plus a way to evaluate any combination of the basis
  function spectrum(d, pa, pb, qa, qb) {
    const { values, vectors } = eigen(gram(d, pa, pb, qa, qb)), out = new Float64Array(d + 1);
    const evalAt = (y, t) => { psi(t, d, pa, pb, out); let s = 0; for (let k = 0; k <= d; k++) s += y[k] * out[k]; return s; };
    return { values, vectors, evalAt };
  }

  // all d + 1 generalized eigenvalues to full relative accuracy: the large ones from A in a
  // basis orthonormal on P, the small ones as reciprocals of the large eigenvalues of the
  // reversed problem (E_P in a basis orthonormal on Q), which double precision resolves
  function eigenvalues(d, pa, pb, qa, qb) {
    const fwd = eigen(gram(d, pa, pb, qa, qb)).values, rev = eigen(gram(d, qa, qb, pa, pb)).values;
    return fwd.map((v, i) => (v >= 1 ? v : 1 / rev[d - i]));
  }

  // the GEVP bound for random Fourier features cos(w_j t + b_j), j < m. The features are sampled
  // at Gauss-Legendre nodes on P and Q, made orthonormal on P by a Householder QR (which avoids
  // squaring the conditioning of B), and the bound is the top eigenvalue of A in that basis.
  function rffBound(W, B, m, pa, pb, qa, qb) {
    const n = 24, { x, w } = gaussLegendre(n), MP = [], MQ = [];
    for (let i = 0; i < n; i++) {
      const tp = pa + (pb - pa) * (x[i] + 1) / 2, tq = qa + (qb - qa) * (x[i] + 1) / 2, sw = Math.sqrt(w[i] / 2), rp = [], rq = [];
      for (let j = 0; j < m; j++) { rp.push(sw * Math.cos(W[j] * tp + B[j])); rq.push(sw * Math.cos(W[j] * tq + B[j])); }
      MP.push(rp); MQ.push(rq);
    }
    for (let k = 0; k < m; k++) {                   // Householder QR of MP, in place
      let nrm = 0;
      for (let i = k; i < n; i++) nrm += MP[i][k] * MP[i][k];
      nrm = Math.sqrt(nrm);
      const alpha = MP[k][k] > 0 ? -nrm : nrm, v = new Float64Array(n);
      for (let i = k; i < n; i++) v[i] = MP[i][k];
      v[k] -= alpha;
      let vv = 0;
      for (let i = k; i < n; i++) vv += v[i] * v[i];
      if (vv === 0) continue;
      for (let j = k; j < m; j++) {
        let s = 0;
        for (let i = k; i < n; i++) s += v[i] * MP[i][j];
        s = 2 * s / vv;
        for (let i = k; i < n; i++) MP[i][j] -= s * v[i];
      }
    }
    const Y = MQ.map(row => {                       // features on Q in the basis orthonormal on P
      const y = new Array(m).fill(0);
      for (let j = 0; j < m; j++) { let s = row[j]; for (let k = 0; k < j; k++) s -= y[k] * MP[k][j]; y[j] = s / MP[j][j]; }
      return y;
    });
    const C = Array.from({ length: m }, (_, a) => Array.from({ length: m }, (_, b) => Y.reduce((s, r) => s + r[a] * r[b], 0)));
    return eigen(C).values[0];
  }

  // the bound and its worst-case function, oriented to be positive on Q's far edge
  function bound(d, pa, pb, qa, qb) {
    const S = spectrum(d, pa, pb, qa, qb), top = S.vectors[0];
    const sign = S.evalAt(top, qa) < 0 ? -1 : 1;
    return { gamma: S.values[0], g: t => sign * S.evalAt(top, t) };
  }

  root.Gevp = { bound, spectrum, eigenvalues, rffBound, gaussLegendre, psi, eigen };
})(typeof window !== "undefined" ? window : globalThis);
