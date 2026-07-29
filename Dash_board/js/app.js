/* ============================================================
   app.js — DATA(data/data.js) → 대시보드 렌더링
   ============================================================ */
"use strict";

const C = {
  talentCore: "#ff4f00", talentPart: "#ffb08a",
  teal: "#00968a", indigo: "#3d4da8", olive: "#8a6d00", plum: "#b04a86",
  other: "#c5c0b1", good: "#00968a", warn: "#8a6d00", bad: "#c62828",
};

/* ---------- 카드 빌더 (다운로드 아이콘 포함) ---------- */
const dlIcon = `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v8m0 0l-3-3m3 3l3-3"/><path d="M2.5 11.5v1.5a1 1 0 001 1h9a1 1 0 001-1v-1.5"/></svg>`;

function card(gridEl, opts) {
  const c = document.createElement("div");
  c.className = "card" + (opts.span2 ? " span2" : "");
  c.innerHTML = `
    <div class="card-head">
      <div class="titles">
        <h3>${opts.title}</h3>
        ${opts.sub ? `<div class="sub">${opts.sub}</div>` : ""}
      </div>
      <div class="dl-group">
        <button class="dl-btn" data-fmt="svg" aria-label="${opts.title} SVG 다운로드">${dlIcon}SVG</button>
        <button class="dl-btn" data-fmt="png" aria-label="${opts.title} PNG 다운로드">${dlIcon}PNG</button>
      </div>
    </div>
    ${opts.legend ? `<div class="legend">${opts.legend.map(l =>
      `<span class="li"><span class="sw" style="background:${l.color}"></span>${l.label}</span>`).join("")}</div>` : ""}
    <div class="chart"></div>
    ${opts.note ? `<div class="foot-note">${opts.note}</div>` : ""}`;
  gridEl.appendChild(c);
  const svg = opts.render(c.querySelector(".chart"));
  const base = opts.file || opts.title.replace(/[\\/:*?"<>|\s]+/g, "_");
  c.querySelector('[data-fmt="svg"]').addEventListener("click", () => downloadSVG(svg, base));
  c.querySelector('[data-fmt="png"]').addEventListener("click", () => downloadPNG(svg, base));
  return c;
}

function htmlCard(gridEl, opts) {
  const c = document.createElement("div");
  c.className = "card" + (opts.span2 ? " span2" : "");
  c.innerHTML = `
    <div class="card-head"><div class="titles">
      <h3>${opts.title}</h3>${opts.sub ? `<div class="sub">${opts.sub}</div>` : ""}
    </div></div>${opts.body}`;
  gridEl.appendChild(c);
  return c;
}

/* ============================================================ */
document.addEventListener("DOMContentLoaded", () => {
  const T = DATA.totals, TAL = DATA.talent.summary;

  /* ---------- 히어로: 인재양성 구성 밴드 ---------- */
  document.getElementById("hero-band-chart").innerHTML = "";
  const restCount = T.projects - TAL.total_talent_projects;
  const restBudget = T.b2026 - TAL.all.b2026;
  const bandCard = card(document.getElementById("hero-band-chart"), {
    title: `2026 AI 예산 ${(T.b2026 / 1e6).toFixed(1)}조원 안에서 인재양성의 위치`,
    sub: "인재양성 96개 사업(주력 + 요소 포함)과 그 외 AI 재정사업의 규모 비교",
    file: "인재양성_구성밴드",
    span2: true,
    legend: [
      { label: "주력 인재양성 78건 · 7.11조", color: C.talentCore },
      { label: "요소 포함 18건 · 0.76조", color: C.talentPart },
      { label: "그 외 AI 재정사업 437건 · 19.68조", color: C.other },
    ],
    render: (elc) => segBand(elc, [
      { key: "주력 인재양성", count: TAL.core.count, value: TAL.core.b2026, color: C.talentCore, desc: "교육/인재 도메인 또는 사업명상 인재양성" },
      { key: "인재양성 요소 포함", count: TAL.partial.count, value: TAL.partial.b2026, color: C.talentPart, desc: "사업 내 인재양성 활동 포함" },
      { key: "그 외 AI 재정사업", count: restCount, value: restBudget, color: C.other, dark: true, desc: "인재양성 성격이 없는 AI 사업" },
    ], { title: "인재양성 구성" }),
    note: "세그먼트에 마우스를 올리면 상세 수치 표시. 인재양성 확정 기준은 '데이터 신뢰성' 섹션 참조.",
  });
  bandCard.classList.add("band-card");

  /* ---------- KPI ---------- */
  const kpis = [
    { label: "인재양성 사업", v: String(TAL.total_talent_projects), unit: "개", sub: `주력 ${TAL.core.count} + 요소 포함 ${TAL.partial.count}`, accent: true },
    { label: "인재양성 2026 예산", v: (TAL.all.b2026 / 1e6).toFixed(2), unit: "조원", sub: `전체 AI 예산의 ${(TAL.all.b2026 / T.b2026 * 100).toFixed(1)}%`, accent: true },
    { label: "인재양성 수행 부처", v: String(DATA.talent.by_dept.length), unit: "개", sub: "최대 과학기술정보통신부 · 교육부 · 고용노동부 순" },
    { label: "전체 AI 재정사업", v: "533", unit: "개", sub: `41개 부처 · 2026년 ${(T.b2026 / 1e6).toFixed(2)}조원 (검증·보정 완료)` },
  ];
  document.getElementById("kpis").innerHTML = kpis.map(k => `
    <div class="kpi${k.accent ? " k-accent" : ""}">
      <div class="k-label">${k.label}</div>
      <div class="k-value">${k.v}<span class="unit">${k.unit}</span></div>
      <div class="k-sub">${k.sub}</div>
    </div>`).join("");

  /* ---------- 용어 정의: 주력 / 요소 포함 ---------- */
  document.getElementById("defs").innerHTML = `
    <div class="def-card">
      <div class="d-title"><span class="sw" style="background:${C.talentCore}"></span>주력 인재양성 (core)
        <span class="d-stat">${TAL.core.count}개 · ${(TAL.core.b2026 / 1e6).toFixed(2)}조원</span></div>
      <div class="d-desc">인재양성이 사업의 주된 성격인 사업. AI·SW중심대학, 내일배움카드, 두뇌한국21 등.</div>
      <div class="d-crit">판정 기준: '교육/인재' 도메인(v1.1 개정 분류) 보유 또는 사업명에 인재·양성·교육·훈련 등 키워드 포함</div>
    </div>
    <div class="def-card">
      <div class="d-title"><span class="sw" style="background:${C.talentPart}"></span>요소 포함 (partial)
        <span class="d-stat">${TAL.partial.count}개 · ${(TAL.partial.b2026 / 1e6).toFixed(2)}조원</span></div>
      <div class="d-desc">주된 목적은 다른 분야이나 사업 내역에 인재양성 활동(교육훈련·인턴십·장학·역량교육 등)을 포함하는 사업. 표시 예산은 사업 전체 기준.</div>
      <div class="d-crit">판정 기준: PDF 원문 사업내용 판정. 사업별 근거는 인재양성 섹션 목록과 표의 칩 호버에 표시</div>
    </div>`;

  /* ---------- 인재양성 ---------- */
  const gTal = document.getElementById("grid-talent");

  card(gTal, {
    title: "부처별 인재양성 예산 (2026)",
    sub: "주력(core)과 요소 포함(partial) 구분 · 상위 10개 부처",
    file: "부처별_인재양성_2026",
    legend: [{ label: "주력 인재양성", color: C.talentCore }, { label: "요소 포함", color: C.talentPart }],
    render: (elc) => stackedH(elc,
      DATA.talent.by_dept.slice(0, 10).map(d => ({
        label: d.dept,
        parts: [
          { key: "주력", value: d.core, color: C.talentCore },
          { key: "요소 포함", value: d.partial, color: C.talentPart },
        ],
      })), { title: "부처별 인재양성" }),
  });

  card(gTal, {
    title: "인재양성 예산 추이 2024 → 2026",
    sub: "2024 결산 · 2025 본예산 · 2026 확정 (보정값)",
    file: "인재양성_연도별_추이",
    legend: [{ label: "주력 인재양성", color: C.talentCore }, { label: "요소 포함", color: C.talentPart }],
    render: (elc) => stackedV(elc, ["2024", "2025", "2026"].map(y => ({
      label: y + "년",
      parts: [
        { key: "주력", value: DATA.talent.yearly.core[y], color: C.talentCore },
        { key: "요소 포함", value: DATA.talent.yearly.partial[y], color: C.talentPart },
      ],
    })), { title: "인재양성 연도별" }),
  });

  card(gTal, {
    title: "인재양성 상위 15개 사업 (2026)",
    sub: "막대 색 = 구분 (오렌지: 주력 / 연한 오렌지: 요소 포함)",
    file: "인재양성_상위15",
    span2: true,
    legend: [{ label: "주력 인재양성", color: C.talentCore }, { label: "요소 포함", color: C.talentPart }],
    render: (elc) => hBar(elc, DATA.talent.top.map(t => ({
      label: `${t.name}`, sub: t.dept, value: t.b26,
      color: t.cat === "core" ? C.talentCore : C.talentPart,
      note: DATA.talent.notes[String(t.id)] || "",
    })), {
      labelW: 300, labelMax: 26, title: "인재양성 상위",
      tipFmt: r => `${Math.round(r.value).toLocaleString()} 백만원${r.note ? `<br><span class="t-muted">${r.note}</span>` : ""}`,
    }),
    note: "'교육/인재' 도메인 라벨 기준(66건 6.82조)에 검증 결과를 반영해 42건 추가·12건 제외, 최종 96건 7.87조원으로 조사됨. 막대에 마우스를 올리면 판정 근거 표시.",
  });

  htmlCard(gTal, {
    title: "요소 포함 18개 사업: 포함된 인재양성 요소",
    sub: "주목적은 다른 분야이나 PDF 원문상 인재양성 활동을 포함하는 사업 (근거는 원문 기반 판정)",
    span2: true,
    body: `<div class="dup-list">${DATA.talent.partial_list.map(t => `
      <div class="dup-item">
        <div class="d-head">${t.dept} · ${t.name}
          <span style="color:var(--muted);font-weight:500">· 2026년 ${fmtKR(t.b26)}원</span></div>
        <div class="d-body">${t.note || "판정 근거 미기재 (talent_projects.csv 참조)"}</div>
      </div>`).join("")}</div>`,
  });

  htmlCard(gTal, {
    title: "부처 간 중복·유사 의심 그룹",
    sub: `인재양성 사업이 2건 이상 걸린 유사도 그룹 ${DATA.talent.dups.length}개 · 분산 편성 검토 대상`,
    span2: true,
    body: `<div class="dup-list">${DATA.talent.dups.map((g, i) => `
      <div class="dup-item">
        <div class="d-head">그룹 ${i + 1} <span style="color:var(--muted);font-weight:500">· 전체 ${g.n}개 사업 중 인재양성 ${g.names.length}건</span></div>
        <div class="d-body">${g.names.join(" · ")}</div>
      </div>`).join("")}</div>`,
  });

  /* ---------- 부처 · 도메인 ---------- */
  const gDept = document.getElementById("grid-dept");

  card(gDept, {
    title: "부처별 2026 AI 예산 상위 12",
    sub: "보정값 기준 · 괄호 안은 사업 수",
    file: "부처별_2026예산",
    render: (elc) => hBar(elc, DATA.by_dept.slice(0, 12).map(d => ({
      label: d.department, value: d.b2026, sub: d.count + "건", color: C.teal,
    })), { title: "부처별 예산" }),
  });

  card(gDept, {
    title: "AI 도메인별 예산 상위 14",
    sub: "사업당 도메인 복수 부여로 합계는 총예산을 초과함",
    file: "도메인별_2026예산",
    render: (elc) => hBar(elc, [
      ...DATA.by_domain.slice(0, 14).map(d => ({
        label: d.domain, value: d.b2026, sub: d.count + "건",
        color: d.domain === "교육/인재" ? C.talentCore : C.indigo,
      })),
    ], { title: "도메인별 예산" }),
    note: "도메인은 v1.1 재분류(195건) 반영. '교육/인재'(오렌지) 78건은 인재양성 주력(core)과 일치하며, 요소 포함 18건은 별도(위 인재양성 섹션).",
  });

  card(gDept, {
    title: "사업 유형별 구성",
    sub: "R&D · 정보화 · 일반 (2026 예산 기준)",
    file: "유형별_구성",
    render: (elc) => donut(elc, [
      { key: "R&D", value: DATA.type.sum["R&D"], color: C.indigo },
      { key: "정보화", value: DATA.type.sum["정보화"], color: C.teal },
      { key: "일반", value: DATA.type.sum["일반"], color: C.other },
    ], { unit: " 백만원", center: (T.b2026 / 1e6).toFixed(1) + "조", centerSub: "2026 확정(보정)", title: "유형별" }),
    note: `사업 수: R&D ${DATA.type.count["R&D"]} · 정보화 ${DATA.type.count["정보화"]} · 일반 ${DATA.type.count["일반"]}`,
  });

  card(gDept, {
    title: "2025 → 2026 증감 상위",
    sub: "증액 상위 5 + 감액 상위 5 (본예산 대비, 보정값)",
    file: "증감_상위",
    legend: [{ label: "증액", color: C.teal }, { label: "감액", color: C.plum }],
    render: (elc) => divergingH(elc, [
      ...DATA.top_inc.slice(0, 5).map(x => ({ label: x.name, value: x.delta })),
      ...DATA.top_dec.slice(0, 5).map(x => ({ label: x.name, value: x.delta })),
    ], { title: "증감 상위" }),
  });

  /* ---------- 데이터 신뢰성 (검증·보정) ---------- */
  const gVer = document.getElementById("grid-verify");

  card(gVer, {
    title: `참고: ${(T.b2026 / 1e6).toFixed(1)}조원의 AI 관련성 구성 (전수 판정)`,
    sub: "에이전트 팀이 533개 사업 전부를 PDF 원문 기준으로 판정 (예산은 검증 보정값)",
    file: "AI관련성_구성밴드",
    span2: true,
    render: (elc) => segBand(elc, [
      { key: "AI 핵심(core)", count: DATA.ai_relevance.count.core, value: DATA.ai_relevance.sum.core, color: C.indigo, desc: "AI가 사업의 본질" },
      { key: "AI 부분(partial)", count: DATA.ai_relevance.count.partial, value: DATA.ai_relevance.sum.partial, color: C.teal, desc: "AI 요소를 일부 포함" },
      { key: "사실상 비AI(none)", count: DATA.ai_relevance.count.none, value: DATA.ai_relevance.sum.none, color: C.other, dark: true, desc: "융자·일반 인프라·일반 행정 등" },
    ], { title: "AI 관련성 구성" }),
    note: "판정 근거: 각 사업의 PDF 원문(사업목적·내용). 상세는 Reports\\분류체계_정합성_검증보고서 참조.",
  });

  card(gVer, {
    title: "예산 수치 검증 판정 (533건)",
    sub: "PDF 원문 총괄표 ↔ JSON 7개 필드 전수 대조. 발견 오류는 v1.1에서 전량 보정 완료",
    file: "검증_예산판정",
    render: (elc) => donut(elc, [
      { key: "일치 (match)", value: DATA.verify.budget.match, color: C.good, icon: "✓" },
      { key: "불일치 (mismatch)", value: DATA.verify.budget.mismatch, color: C.bad, icon: "✕" },
    ], { unit: "건", center: "9.2%", centerSub: "오류율", title: "예산 판정" }),
  });

  card(gVer, {
    title: "발견·보정한 예산 오류 49건: 유형별 원인",
    sub: "전원 PDF 재대조로 원인 규명 후 확정값으로 교체됨 (v1.1)",
    file: "검증_오류유형",
    render: (elc) => hBar(elc, Object.entries(DATA.verify.error_types).map(([k, v]) => ({
      label: k, value: v, color: C.bad,
    })), { fmt: v => v + "건", labelW: 190, labelMax: 17, tipFmt: r => r.value + "건", title: "오류 유형" }),
    note: "6열 시프트: 추경란 없는 총괄표를 7열로 읽어 값이 밀린 유형. 음수 예산 6건 전원 이 유형으로 조사됨.",
  });

  card(gVer, {
    title: "AI 도메인 분류 판정 (533건)",
    sub: "ai_domains 라벨의 PDF 내용 부합 여부. 부적절·누락 195건은 v1.1에서 재분류 완료",
    file: "검증_분류판정",
    render: (elc) => hBar(elc, [
      { label: "✓ 적절 (appropriate)", value: DATA.verify.classification.appropriate, color: C.good },
      { label: "△ 일부 부적절·누락", value: DATA.verify.classification.partial, color: C.warn },
      { label: "✕ 핵심 오류 (wrong)", value: DATA.verify.classification.wrong, color: C.bad },
    ], { fmt: v => v + "건", labelW: 200, labelMax: 18, tipFmt: r => r.value + "건", title: "분류 판정" }),
    note: "36.6%가 부적절·누락으로 조사됨. 도메인 기반 집계는 오차 전제 필요. 사업명 불일치 " + DATA.verify.name_mismatch + "건 별도.",
  });

  htmlCard(gVer, {
    title: "검증 신뢰도: 1·2차 판정 일치율",
    sub: "문제 판정 112건 + 정상 표본은 별도 에이전트가 독립 재검",
    body: `<div class="mini-tiles">${[
      ["예산 판정", DATA.verify.agreement.budget_verdict],
      ["분류 판정", DATA.verify.agreement.classification_verdict],
      ["AI 관련성", DATA.verify.agreement.ai_relevance],
      ["인재양성 여부", DATA.verify.agreement.talent_related],
    ].map(([k, a]) => {
      const pct = (a.agree / (a.agree + a.disagree) * 100).toFixed(1);
      return `<div class="mini"><div class="m-v">${pct}%</div><div class="m-l">${k} (${a.agree}/${a.agree + a.disagree})</div></div>`;
    }).join("")}</div>
    <div class="foot-note" style="margin-top:8px">의미 판단(분류·관련성)은 불일치 시 원문 전체를 본 2차 판정을 최종 채택.</div>`,
  });

  /* ---------- 데이터 테이블 ---------- */
  buildTable();

  /* ---------- CSV 파일 카드 ---------- */
  const files = [
    ["projects_raw.csv", "전체 533개 사업 원자료", "식별·계층·예산 7필드·v1.1 보정값·개정 도메인·검증 판정 포함 (48개 열)"],
    ["sub_projects_raw.csv", "내역사업 1,658행", "모사업 id 연결, 2024–2026 예산 · 불일치 165개 사업은 v1.2 재추출본(source 열)"],
    ["talent_projects.csv", "인재양성 확정 96건", "주력/요소 구분, 보정 예산, 판정 근거"],
    ["verification_issues.csv", "검증 이슈 234행", "예산 불일치 49건 + 분류 부적절 195건 + 사업명 불일치"],
    ["by_department.csv", "부처별 집계 41행", "전체·인재양성(주력/요소) 2026 예산"],
    ["by_domain.csv", "AI 도메인별 집계 28행", "사업 수·2026 예산 (보정값)"],
  ];
  document.getElementById("files").innerHTML = files.map(([f, n, d]) => `
    <a class="file-card" href="data/${f}" download>
      <span class="f-name">${dlIcon} ${n}</span>
      <span class="f-desc">${f} · ${d}</span>
    </a>`).join("");

  /* ---------- 스크롤 스파이 ---------- */
  const links = [...document.querySelectorAll(".nav .tabs a")];
  const secs = links.map(a => document.querySelector(a.getAttribute("href")));
  const spy = new IntersectionObserver((ents) => {
    ents.forEach(e => {
      if (e.isIntersecting) {
        links.forEach(a => a.classList.toggle("active", a.getAttribute("href") === "#" + e.target.id));
      }
    });
  }, { rootMargin: "-30% 0px -60% 0px" });
  secs.forEach(s => s && spy.observe(s));
});

/* ============================================================
   데이터 테이블
   ============================================================ */
const TCOLS = [
  { key: "id", label: "id", num: true },
  { key: "dept", label: "부처" },
  { key: "name", label: "사업명" },
  { key: "b24", label: "2024 결산", num: true },
  { key: "b25", label: "2025 본예산", num: true },
  { key: "b26c", label: "2026 확정*", num: true },
  { key: "ai", label: "AI 관련성" },
  { key: "tal", label: "인재양성" },
  { key: "bv", label: "예산 검증" },
  { key: "dom", label: "AI 도메인" },
];
const tState = { mode: "all", dept: "", verify: "", q: "", sortKey: "b26c", sortDir: -1 };

function buildTable() {
  const deptSel = document.getElementById("f-dept");
  [...new Set(DATA.projects.map(p => p.dept))].sort((a, b) => a.localeCompare(b, "ko"))
    .forEach(d => { const o = document.createElement("option"); o.value = d; o.textContent = d; deptSel.appendChild(o); });

  document.getElementById("f-search").addEventListener("input", e => { tState.q = e.target.value.trim(); renderTable(); });
  deptSel.addEventListener("change", e => { tState.dept = e.target.value; renderTable(); });
  document.getElementById("f-verify").addEventListener("change", e => { tState.verify = e.target.value; renderTable(); });
  document.querySelectorAll("#f-mode button").forEach(b => b.addEventListener("click", () => {
    tState.mode = b.dataset.mode;
    document.querySelectorAll("#f-mode button").forEach(x => x.classList.toggle("on", x === b));
    renderTable();
  }));

  const thead = document.querySelector("#dtable thead tr");
  thead.innerHTML = TCOLS.map(c => `<th tabindex="0" data-key="${c.key}">${c.label} <span class="arrow"></span></th>`).join("");
  thead.querySelectorAll("th").forEach(th => {
    const act = () => {
      const k = th.dataset.key;
      if (tState.sortKey === k) tState.sortDir *= -1;
      else { tState.sortKey = k; tState.sortDir = TCOLS.find(c => c.key === k).num ? -1 : 1; }
      renderTable();
    };
    th.addEventListener("click", act);
    th.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); act(); } });
  });
  renderTable();
}

function renderTable() {
  let rows = DATA.projects;
  if (tState.mode === "talent") rows = rows.filter(p => p.tal);
  if (tState.mode === "core") rows = rows.filter(p => p.tal === "core");
  if (tState.dept) rows = rows.filter(p => p.dept === tState.dept);
  if (tState.verify === "mismatch") rows = rows.filter(p => p.bv === "mismatch");
  if (tState.verify === "nonai") rows = rows.filter(p => p.ai === "none");
  if (tState.q) {
    const q = tState.q.toLowerCase();
    rows = rows.filter(p => (p.name + " " + p.dept + " " + p.dom.join(" ")).toLowerCase().includes(q));
  }
  const k = tState.sortKey, dir = tState.sortDir;
  const col = TCOLS.find(c => c.key === k);
  rows = [...rows].sort((a, b) => {
    let va = a[k], vb = b[k];
    if (k === "dom") { va = va.join(";"); vb = vb.join(";"); }
    if (col.num) return ((va ?? -Infinity) - (vb ?? -Infinity)) * dir;
    return String(va ?? "").localeCompare(String(vb ?? ""), "ko") * dir;
  });

  document.querySelectorAll("#dtable thead th .arrow").forEach(s => s.textContent = "");
  const th = document.querySelector(`#dtable thead th[data-key="${k}"] .arrow`);
  if (th) th.textContent = dir === 1 ? "▲" : "▼";

  const aiChip = { core: '<span class="chip ok">core</span>', partial: '<span class="chip warnc">partial</span>', none: '<span class="chip mutedc">none</span>' };
  const talChip = (p) => {
    if (!p.tal) return "";
    const note = (DATA.talent.notes[String(p.id)] || "").replace(/"/g, "'");
    const cls = p.tal === "core" ? "core" : "partial";
    const label = p.tal === "core" ? "주력" : "요소";
    return `<span class="chip ${cls}"${note ? ` title="${note}"` : ""}>${label}</span>`;
  };
  const bvChip = { match: '<span class="chip ok">✓ 일치</span>', mismatch: '<span class="chip badc">✕ 불일치</span>', uncertain: '<span class="chip mutedc">미확정</span>' };

  document.querySelector("#dtable tbody").innerHTML = rows.map(p => `<tr>
    <td class="num">${p.id}</td>
    <td>${p.dept}</td>
    <td>${p.name}${p.corr ? ' <span class="corr-mark" title="파싱 오류 보정값 적용">*</span>' : ""}</td>
    <td class="num">${p.b24 == null ? "-" : Math.round(p.b24).toLocaleString()}</td>
    <td class="num">${p.b25 == null ? "-" : Math.round(p.b25).toLocaleString()}</td>
    <td class="num">${p.b26c == null ? "-" : Math.round(p.b26c).toLocaleString()}</td>
    <td>${aiChip[p.ai] || "-"}</td>
    <td>${talChip(p)}</td>
    <td>${bvChip[p.bv] || "-"}</td>
    <td style="max-width:200px">${p.dom.join(", ")}</td>
  </tr>`).join("");
  document.getElementById("t-count").textContent =
    `${rows.length}건 표시 · 2026 합계 ${fmtKR(rows.reduce((s, p) => s + (p.b26c || 0), 0))}원`;
}
