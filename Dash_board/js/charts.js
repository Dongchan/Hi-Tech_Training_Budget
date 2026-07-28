/* ============================================================
   charts.js — 외부 라이브러리 없는 인라인 SVG 차트
   (file:// 오프라인 동작, PNG/SVG 내보내기 지원)
   ============================================================ */
"use strict";

const NS = "http://www.w3.org/2000/svg";
const INK = "#201515", BODY = "#36342e", MUTED = "#939084",
      LINE = "#c5c0b1", SURFACE = "#eceae3", BG = "#fffefb";
const FONT = 'Inter, "Segoe UI", "Malgun Gothic", sans-serif';

/* ---------- 유틸 ---------- */
function el(name, attrs, parent) {
  const n = document.createElementNS(NS, name);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(n);
  return n;
}
function txt(parent, x, y, s, opts = {}) {
  const t = el("text", {
    x, y,
    fill: opts.fill || BODY,
    "font-size": opts.size || 12,
    "font-family": FONT,
    "font-weight": opts.weight || 400,
    "text-anchor": opts.anchor || "start",
    "dominant-baseline": opts.baseline || "middle",
  }, parent);
  t.textContent = s;
  return t;
}
// 백만원 단위 → 한국식 표기
function fmtKR(v) {
  if (v == null) return "-";
  const sign = v < 0 ? "-" : "";
  const a = Math.abs(v);
  if (a >= 1e6) return sign + (a / 1e6).toFixed(2) + "조";
  if (a >= 100) return sign + Math.round(a / 100).toLocaleString() + "억";
  return sign + Math.round(a).toLocaleString() + "백만";
}
function fmtComma(v) { return v == null ? "-" : Math.round(v).toLocaleString(); }
function ellip(s, n) { return s.length > n ? s.slice(0, n - 1) + "…" : s; }

/* ---------- 툴팁 ---------- */
const tip = () => document.getElementById("tooltip");
function bindTip(node, html) {
  node.addEventListener("mousemove", (e) => {
    const t = tip();
    t.innerHTML = html;
    t.style.opacity = 1;
    const pad = 14;
    let x = e.clientX + pad, y = e.clientY + pad;
    const r = t.getBoundingClientRect();
    if (x + r.width > window.innerWidth - 8) x = e.clientX - r.width - pad;
    if (y + r.height > window.innerHeight - 8) y = e.clientY - r.height - pad;
    t.style.left = x + "px"; t.style.top = y + "px";
  });
  node.addEventListener("mouseleave", () => { tip().style.opacity = 0; });
}

/* ---------- SVG 프레임 ---------- */
function frame(container, w, h, title) {
  container.innerHTML = "";
  const svg = el("svg", {
    viewBox: `0 0 ${w} ${h}`, width: "100%",
    role: "img", "aria-label": title || "chart",
    "data-w": w, "data-h": h,
  });
  container.appendChild(svg);
  return svg;
}

/* ---------- 가로 막대 ----------
   rows: [{label, value, color, sub}] */
function hBar(container, rows, opts = {}) {
  const rowH = opts.rowH || 30, labelW = opts.labelW || 170, valW = 74;
  const w = 640, padT = 6, padB = 6;
  const h = padT + rows.length * rowH + padB;
  const svg = frame(container, w, h, opts.title);
  const max = opts.max || Math.max(...rows.map(r => Math.abs(r.value)), 1);
  const plotW = w - labelW - valW - 16;

  // 눈금선 (은은하게)
  for (let i = 1; i <= 3; i++) {
    const gx = labelW + (plotW * i) / 3;
    el("line", { x1: gx, y1: padT, x2: gx, y2: h - padB, stroke: SURFACE, "stroke-width": 1 }, svg);
  }
  rows.forEach((r, i) => {
    const y = padT + i * rowH;
    const bh = rowH - 9;
    const bw = Math.max((Math.abs(r.value) / max) * plotW, r.value === 0 ? 0 : 2);
    txt(svg, labelW - 8, y + rowH / 2, ellip(r.label, opts.labelMax || 14),
        { anchor: "end", size: 12.5, fill: INK, weight: 500 });
    const bar = el("rect", {
      x: labelW, y: y + 4, width: bw, height: bh,
      rx: 4, fill: r.color || "#00968a",
    }, svg);
    txt(svg, labelW + bw + 7, y + rowH / 2, opts.fmt ? opts.fmt(r.value) : fmtKR(r.value),
        { size: 12, fill: BODY, weight: 600 });
    if (r.sub) txt(svg, w - 4, y + rowH / 2, r.sub, { anchor: "end", size: 11, fill: MUTED });
    bindTip(bar, `<div class="t-title">${r.label}</div>${opts.tipFmt ? opts.tipFmt(r) : fmtComma(r.value) + " 백만원"}`);
  });
  return svg;
}

/* ---------- 누적 가로 막대 ----------
   rows: [{label, parts: [{key, value, color}]}] */
function stackedH(container, rows, opts = {}) {
  const rowH = opts.rowH || 32, labelW = opts.labelW || 150;
  const w = 640, padT = 6, padB = 6, valW = 78;
  const h = padT + rows.length * rowH + padB;
  const svg = frame(container, w, h, opts.title);
  const totals = rows.map(r => r.parts.reduce((s, p) => s + (p.value || 0), 0));
  const max = opts.max || Math.max(...totals, 1);
  const plotW = w - labelW - valW - 12;

  rows.forEach((r, i) => {
    const y = padT + i * rowH, bh = rowH - 10;
    txt(svg, labelW - 8, y + rowH / 2, ellip(r.label, 12), { anchor: "end", size: 12.5, fill: INK, weight: 500 });
    let x = labelW;
    r.parts.forEach(p => {
      if (!p.value) return;
      const bw = (p.value / max) * plotW;
      const rect = el("rect", { x, y: y + 5, width: Math.max(bw - 2, 1.5), height: bh, rx: 3, fill: p.color }, svg);
      bindTip(rect, `<div class="t-title">${r.label}</div>${p.key}: ${fmtComma(p.value)} 백만원 (${fmtKR(p.value)}원)`);
      x += bw;
    });
    txt(svg, x + 6, y + rowH / 2, fmtKR(totals[i]), { size: 12, fill: BODY, weight: 600 });
  });
  return svg;
}

/* ---------- 연도별 수직 누적 막대 ----------
   cols: [{label, parts: [{key, value, color}]}] */
function stackedV(container, cols, opts = {}) {
  const w = 640, h = 260, padL = 60, padB = 34, padT = 16;
  const svg = frame(container, w, h, opts.title);
  const totals = cols.map(c => c.parts.reduce((s, p) => s + (p.value || 0), 0));
  const max = Math.max(...totals, 1);
  const plotH = h - padT - padB, plotW = w - padL - 20;
  const colW = Math.min(plotW / cols.length, 150), barW = Math.min(colW * 0.46, 64);

  // y 그리드 + 라벨
  for (let i = 0; i <= 3; i++) {
    const val = (max * i) / 3, gy = h - padB - (plotH * i) / 3;
    el("line", { x1: padL, y1: gy, x2: w - 16, y2: gy, stroke: i === 0 ? LINE : SURFACE, "stroke-width": 1 }, svg);
    txt(svg, padL - 8, gy, fmtKR(val), { anchor: "end", size: 11, fill: MUTED });
  }
  cols.forEach((c, i) => {
    const cx = padL + colW * i + colW / 2;
    let y = h - padB;
    c.parts.forEach(p => {
      if (!p.value) return;
      const bh = (p.value / max) * plotH;
      const rect = el("rect", { x: cx - barW / 2, y: y - bh + 1, width: barW, height: Math.max(bh - 2, 1.5), rx: 4, fill: p.color }, svg);
      bindTip(rect, `<div class="t-title">${c.label} · ${p.key}</div>${fmtComma(p.value)} 백만원 (${fmtKR(p.value)}원)`);
      y -= bh;
    });
    txt(svg, cx, y - 10, fmtKR(totals[i]), { anchor: "middle", size: 12.5, fill: INK, weight: 600 });
    txt(svg, cx, h - padB + 16, c.label, { anchor: "middle", size: 12.5, fill: BODY, weight: 500 });
  });
  return svg;
}

/* ---------- 도넛 ----------
   parts: [{key, value, color, icon}] */
function donut(container, parts, opts = {}) {
  const w = 640, h = 240, cx = 150, cy = h / 2, R = 88, r = 54;
  const svg = frame(container, w, h, opts.title);
  const total = parts.reduce((s, p) => s + p.value, 0);
  let a0 = -Math.PI / 2;
  parts.forEach(p => {
    const frac = p.value / total;
    const a1 = a0 + frac * Math.PI * 2;
    const large = frac > 0.5 ? 1 : 0;
    const p0 = [cx + R * Math.cos(a0), cy + R * Math.sin(a0)];
    const p1 = [cx + R * Math.cos(a1), cy + R * Math.sin(a1)];
    const q1 = [cx + r * Math.cos(a1), cy + r * Math.sin(a1)];
    const q0 = [cx + r * Math.cos(a0), cy + r * Math.sin(a0)];
    const d = `M${p0} A${R},${R} 0 ${large} 1 ${p1} L${q1} A${r},${r} 0 ${large} 0 ${q0} Z`;
    const path = el("path", { d, fill: p.color, stroke: BG, "stroke-width": 2 }, svg);
    bindTip(path, `<div class="t-title">${p.icon || ""} ${p.key}</div>${fmtComma(p.value)}${opts.unit || "건"} · ${(frac * 100).toFixed(1)}%`);
    a0 = a1;
  });
  txt(svg, cx, cy - 8, opts.center || fmtComma(total), { anchor: "middle", size: 26, weight: 600, fill: INK });
  txt(svg, cx, cy + 16, opts.centerSub || "", { anchor: "middle", size: 12, fill: MUTED });
  // 우측 직접 라벨
  const lx = 300;
  parts.forEach((p, i) => {
    const ly = cy - ((parts.length - 1) * 26) / 2 + i * 26;
    el("rect", { x: lx, y: ly - 6, width: 11, height: 11, rx: 3, fill: p.color }, svg);
    txt(svg, lx + 18, ly, `${p.icon || ""} ${p.key}`, { size: 13, fill: INK, weight: 500 });
    txt(svg, lx + 200, ly, `${fmtComma(p.value)}${opts.unit || "건"} (${((p.value / total) * 100).toFixed(1)}%)`,
        { size: 12.5, fill: BODY });
  });
  return svg;
}

/* ---------- 증감 다이버징 ----------
   rows: [{label, value}] value 백만원 (+증액 / -감액) */
function divergingH(container, rows, opts = {}) {
  const rowH = 28, w = 640, labelW = 190;
  const padT = 6, padB = 6;
  const h = padT + rows.length * rowH + padB;
  const svg = frame(container, w, h, opts.title);
  const max = Math.max(...rows.map(r => Math.abs(r.value)), 1);
  const cx = labelW + (w - labelW - 80) / 2;
  const half = (w - labelW - 80) / 2;
  el("line", { x1: cx, y1: padT, x2: cx, y2: h - padB, stroke: LINE, "stroke-width": 1 }, svg);
  rows.forEach((r, i) => {
    const y = padT + i * rowH, bh = rowH - 9;
    const bw = (Math.abs(r.value) / max) * (half - 8);
    const pos = r.value >= 0;
    txt(svg, labelW - 8, y + rowH / 2, ellip(r.label, 16), { anchor: "end", size: 12, fill: INK, weight: 500 });
    const rect = el("rect", {
      x: pos ? cx : cx - bw, y: y + 4, width: Math.max(bw, 2), height: bh, rx: 4,
      fill: pos ? "#00968a" : "#b04a86",
    }, svg);
    txt(svg, pos ? cx + bw + 6 : cx - bw - 6, y + rowH / 2,
        (pos ? "+" : "−") + fmtKR(Math.abs(r.value)),
        { anchor: pos ? "start" : "end", size: 11.5, fill: BODY, weight: 600 });
    bindTip(rect, `<div class="t-title">${r.label}</div>2025 대비 ${pos ? "+" : ""}${fmtComma(r.value)} 백만원`);
  });
  return svg;
}

/* ---------- 히어로 세그먼트 밴드 ----------
   parts: [{key, value, color, desc}] */
function segBand(container, parts, opts = {}) {
  const w = 1152, h = 132, bandY = 34, bandH = 44;
  const svg = frame(container, w, h, opts.title);
  const total = parts.reduce((s, p) => s + p.value, 0);
  let x = 0;
  parts.forEach(p => {
    const bw = (p.value / total) * w;
    const rect = el("rect", { x: x + 1, y: bandY, width: bw - 2, height: bandH, rx: 5, fill: p.color }, svg);
    bindTip(rect, `<div class="t-title">${p.key}</div>${fmtComma(p.value)} 백만원 (${fmtKR(p.value)}원) · ${(p.value / total * 100).toFixed(1)}%<br><span class="t-muted">${p.desc || ""}</span>`);
    // 상단 키 라벨 + 하단 수치 (좁은 세그먼트는 겹침 방지를 위해 생략 — 툴팁·범례로 확인)
    if (bw >= 130) {
      txt(svg, x + 8, bandY - 14, `${p.key} · ${p.count}건`, { size: 13, fill: BODY, weight: 600 });
      txt(svg, x + 8, bandY + bandH + 20, `${fmtKR(p.value)}원 (${(p.value / total * 100).toFixed(0)}%)`,
          { size: 15, fill: p.dark ? INK : p.color, weight: 600 });
    }
    x += bw;
  });
  return svg;
}

/* ---------- PNG / SVG 다운로드 ---------- */
function svgString(svg) {
  const clone = svg.cloneNode(true);
  const w = +svg.dataset.w, h = +svg.dataset.h;
  clone.setAttribute("xmlns", NS);
  clone.setAttribute("width", w);
  clone.setAttribute("height", h);
  // 배경(크림) 삽입 — 내보내기에서 투명 방지
  const bg = document.createElementNS(NS, "rect");
  bg.setAttribute("x", 0); bg.setAttribute("y", 0);
  bg.setAttribute("width", w); bg.setAttribute("height", h);
  bg.setAttribute("fill", BG);
  clone.insertBefore(bg, clone.firstChild);
  return new XMLSerializer().serializeToString(clone);
}
function saveBlob(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
}
function downloadSVG(svg, name) {
  saveBlob(new Blob([svgString(svg)], { type: "image/svg+xml;charset=utf-8" }), name + ".svg");
}
function downloadPNG(svg, name) {
  const w = +svg.dataset.w, h = +svg.dataset.h, scale = 2;
  const img = new Image();
  const url = URL.createObjectURL(new Blob([svgString(svg)], { type: "image/svg+xml;charset=utf-8" }));
  img.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = w * scale; canvas.height = h * scale;
    const ctx = canvas.getContext("2d");
    ctx.scale(scale, scale);
    ctx.drawImage(img, 0, 0, w, h);
    URL.revokeObjectURL(url);
    canvas.toBlob(b => saveBlob(b, name + ".png"), "image/png");
  };
  img.src = url;
}
