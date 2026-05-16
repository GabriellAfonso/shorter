/**
 * k6 — isolated code benchmark with per-stage breakdown.
 *
 * Backend pinned to 1 vCPU / 1G RAM (docker-compose.bench.yml). Goal: find
 * the saturation knee — the highest RPS where p95 stays under budget.
 *
 * For each path (hit / not_found) we run six sequential constant-arrival-rate
 * scenarios at fixed RPS levels (5, 20, 40, 60, 80, 100). Each level lasts
 * 15s and emits its own Trend + status counters, so the final table shows
 * one row per RPS step.
 *
 * Run:
 *   k6 run benchmark-isolated.js
 *   k6 run -e BASE_URL=http://localhost:8000 -e CACHE_MODE=on benchmark-isolated.js
 *
 * To compare cache ON vs OFF, restart the backend stack with CACHE_REDIS
 * flipped and re-run:
 *   docker compose -f docker-compose.bench.yml down -v
 *   CACHE_REDIS=false docker compose -f docker-compose.bench.yml up -d --build --wait
 *   k6 run -e CACHE_MODE=off benchmark-isolated.js
 */

import http from "k6/http";
import { Trend, Counter } from "k6/metrics";

// ─── Config ──────────────────────────────────────────────────────────────────
const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

const WARM_SLUGS = Array.from({ length: 100 }, (_, i) =>
  `test${String(i).padStart(4, "0")}`
);

const randomWarmSlug = () => WARM_SLUGS[Math.floor(Math.random() * WARM_SLUGS.length)];
const randomMissingSlug = () => `nf${Math.random().toString(36).slice(2, 10)}`;

// ─── RPS steps tested per path ──────────────────────────────────────────────
const RATES = [5, 20, 40, 60, 80, 100];
const STAGE_S = 15;   // duration per RPS level
const GAP_S   = 3;    // cooldown between scenarios

// Buffers between path groups
const WARMUP_S = 15;
const PRE_NF_GAP_S = 10;

// ─── Per-stage metrics ──────────────────────────────────────────────────────
// One Trend + four status counters per (path, rate) combination.
const M = {};
for (const r of RATES) {
  M[`hit_${r}`] = {
    t:    new Trend(`dur_hit_${r}`, true),
    s302: new Counter(`hit_${r}_302`),
    s429: new Counter(`hit_${r}_429`),
    s5xx: new Counter(`hit_${r}_5xx`),
    sOth: new Counter(`hit_${r}_other`),
  };
  M[`nf_${r}`] = {
    t:    new Trend(`dur_nf_${r}`, true),
    s404: new Counter(`nf_${r}_404`),
    s429: new Counter(`nf_${r}_429`),
    s5xx: new Counter(`nf_${r}_5xx`),
    sOth: new Counter(`nf_${r}_other`),
  };
}

// ─── Build scenarios ────────────────────────────────────────────────────────
const scenarios = {
  warmup: {
    executor: "shared-iterations",
    vus: 5,
    iterations: 100,
    maxDuration: `${WARMUP_S}s`,
    exec: "warmupOne",
    tags: { scenario: "warmup" },
  },
};

// Hit path: 6 sequential constant-arrival-rate scenarios.
let cursor = WARMUP_S + GAP_S;
RATES.forEach((rate) => {
  scenarios[`hit_${rate}`] = {
    executor: "constant-arrival-rate",
    rate: rate,
    timeUnit: "1s",
    duration: `${STAGE_S}s`,
    preAllocatedVUs: Math.max(20, rate),
    maxVUs: Math.max(100, rate * 5),
    exec: `hit_${rate}`,
    startTime: `${cursor}s`,
    tags: { scenario: `hit_${rate}` },
  };
  cursor += STAGE_S + GAP_S;
});

cursor += PRE_NF_GAP_S;

// Not-found path: same 6 levels.
RATES.forEach((rate) => {
  scenarios[`nf_${rate}`] = {
    executor: "constant-arrival-rate",
    rate: rate,
    timeUnit: "1s",
    duration: `${STAGE_S}s`,
    preAllocatedVUs: Math.max(20, rate),
    maxVUs: Math.max(100, rate * 5),
    exec: `nf_${rate}`,
    startTime: `${cursor}s`,
    tags: { scenario: `nf_${rate}` },
  };
  cursor += STAGE_S + GAP_S;
});

export const options = {
  scenarios,
  summaryTrendStats: ["avg", "min", "med", "p(50)", "p(95)", "p(99)", "max"],
  noConnectionReuse: false,
};

// ─── Runners ────────────────────────────────────────────────────────────────
export function warmupOne() {
  const idx = ((__VU - 1) * __ITER) % WARM_SLUGS.length;
  http.get(`${BASE_URL}/s/${WARM_SLUGS[idx]}/`, { redirects: 0 });
}

function recordHit(rate, res) {
  const m = M[`hit_${rate}`];
  m.t.add(res.timings.duration);
  const s = res.status;
  if (s === 301 || s === 302) m.s302.add(1);
  else if (s === 429)         m.s429.add(1);
  else if (s >= 500)          m.s5xx.add(1);
  else                        m.sOth.add(1);
}

function recordNf(rate, res) {
  const m = M[`nf_${rate}`];
  m.t.add(res.timings.duration);
  const s = res.status;
  if (s === 404)      m.s404.add(1);
  else if (s === 429) m.s429.add(1);
  else if (s >= 500)  m.s5xx.add(1);
  else                m.sOth.add(1);
}

// k6 requires distinct exported exec functions per scenario.
export function hit_5()   { recordHit(5,   http.get(`${BASE_URL}/s/${randomWarmSlug()}/`, { redirects: 0 })); }
export function hit_20()  { recordHit(20,  http.get(`${BASE_URL}/s/${randomWarmSlug()}/`, { redirects: 0 })); }
export function hit_40()  { recordHit(40,  http.get(`${BASE_URL}/s/${randomWarmSlug()}/`, { redirects: 0 })); }
export function hit_60()  { recordHit(60,  http.get(`${BASE_URL}/s/${randomWarmSlug()}/`, { redirects: 0 })); }
export function hit_80()  { recordHit(80,  http.get(`${BASE_URL}/s/${randomWarmSlug()}/`, { redirects: 0 })); }
export function hit_100() { recordHit(100, http.get(`${BASE_URL}/s/${randomWarmSlug()}/`, { redirects: 0 })); }

export function nf_5()    { recordNf(5,    http.get(`${BASE_URL}/s/${randomMissingSlug()}/`, { redirects: 0 })); }
export function nf_20()   { recordNf(20,   http.get(`${BASE_URL}/s/${randomMissingSlug()}/`, { redirects: 0 })); }
export function nf_40()   { recordNf(40,   http.get(`${BASE_URL}/s/${randomMissingSlug()}/`, { redirects: 0 })); }
export function nf_60()   { recordNf(60,   http.get(`${BASE_URL}/s/${randomMissingSlug()}/`, { redirects: 0 })); }
export function nf_80()   { recordNf(80,   http.get(`${BASE_URL}/s/${randomMissingSlug()}/`, { redirects: 0 })); }
export function nf_100()  { recordNf(100,  http.get(`${BASE_URL}/s/${randomMissingSlug()}/`, { redirects: 0 })); }

// ─── Summary ────────────────────────────────────────────────────────────────
export function handleSummary(data) {
  const ms = (v) => (v === undefined ? "  N/A" : `${v.toFixed(1)}ms`);
  const cnt = (m) => data.metrics[m]?.values?.count ?? 0;
  const trend = (m, k) => data.metrics[m]?.values?.[k];

  const pct = (good, total) => (total === 0 ? "  -  " : `${((1 - good / total) * 100).toFixed(1)}%`);

  const cacheMode = __ENV.CACHE_MODE || "unset";

  const hitRows = RATES.map((r) => {
    const ok = cnt(`hit_${r}_302`);
    const bad = cnt(`hit_${r}_429`) + cnt(`hit_${r}_5xx`) + cnt(`hit_${r}_other`);
    const total = ok + bad;
    return {
      rate: r,
      p50: ms(trend(`dur_hit_${r}`, "p(50)")),
      p95: ms(trend(`dur_hit_${r}`, "p(95)")),
      p99: ms(trend(`dur_hit_${r}`, "p(99)")),
      max: ms(trend(`dur_hit_${r}`, "max")),
      err: pct(ok, total),
      total,
    };
  });

  const nfRows = RATES.map((r) => {
    const ok = cnt(`nf_${r}_404`);
    const bad = cnt(`nf_${r}_429`) + cnt(`nf_${r}_5xx`) + cnt(`nf_${r}_other`);
    const total = ok + bad;
    return {
      rate: r,
      p50: ms(trend(`dur_nf_${r}`, "p(50)")),
      p95: ms(trend(`dur_nf_${r}`, "p(95)")),
      p99: ms(trend(`dur_nf_${r}`, "p(99)")),
      max: ms(trend(`dur_nf_${r}`, "max")),
      err: pct(ok, total),
      total,
    };
  });

  const renderTable = (label, rows) => {
    const head = "║ RPS ║ p50      ║ p95       ║ p99       ║ max       ║ err   ║ total ║";
    const sep  = "╠═════╬══════════╬═══════════╬═══════════╬═══════════╬═══════╬═══════╣";
    const top  = "╔═════╦══════════╦═══════════╦═══════════╦═══════════╦═══════╦═══════╗";
    const bot  = "╚═════╩══════════╩═══════════╩═══════════╩═══════════╩═══════╩═══════╝";
    const body = rows.map((r) =>
      `║ ${String(r.rate).padEnd(3)} ║ ${r.p50.padEnd(8)} ║ ${r.p95.padEnd(9)} ║ ${r.p99.padEnd(9)} ║ ${r.max.padEnd(9)} ║ ${r.err.padEnd(5)} ║ ${String(r.total).padEnd(5)} ║`
    ).join("\n");
    return `${label}\n${top}\n${head}\n${sep}\n${body}\n${bot}`;
  };

  const report = `
SHORTER — Isolated Code Benchmark
Target: ${BASE_URL}
Cache mode: ${cacheMode}
Backend: 1 vCPU / 1G RAM (docker-compose.bench.yml)
Each row = ${STAGE_S}s constant-arrival-rate at the given RPS.

${renderTable("HIT path (302 — known slug, cache hit after warmup):", hitRows)}

${renderTable("NOT_FOUND path (404 — random slug, exercises miss/negative-cache):", nfRows)}

How to read
  • p50 is the typical request. p95/p99 expose tail latency.
  • The "knee" is the RPS where p95 starts exceeding your latency budget
    (e.g. 100 ms). Report that RPS as "max sustainable".
  • err = non-success percentage (429 + 5xx + unexpected).
`;

  console.log(report);
  return {
    stdout: report,
    "benchmark-isolated-results.txt": report,
  };
}
