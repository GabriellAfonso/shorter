/**
 * k6 load test — production redirect endpoints
 *
 * Targets 100 seeded test slugs (test0000–test0099) on
 * https://gabrielafonso.com.br/s/<slug>. Seed them on the VPS first:
 *
 *     python manage.py create_test_slugs
 *
 * Compares cache ON vs cache OFF — flip CACHE_REDIS in backend/.env and
 * restart the backend between runs.
 *
 * Status tracking:
 *   - 302/301: success (redirect)
 *   - 429:     rate-limited (set BENCHMARK_MODE=true to disable)
 *   - 5xx:     server error / saturation
 *
 * Stages (each 20s + 5s cooldown), focused on the saturation zone:
 *   stage_10   →   10 RPS
 *   stage_50   →   50 RPS
 *   stage_100  →  100 RPS
 *   stage_150  →  150 RPS
 *   stage_200  →  200 RPS
 *   stage_300  →  300 RPS
 *   stage_500  →  500 RPS
 *
 * Run: k6 run benchmark.js
 */

import http from "k6/http";
import { check } from "k6";
import { Counter, Trend } from "k6/metrics";

// ─── Target URLs ─────────────────────────────────────────────────────────────
const BASE_URL = "https://gabrielafonso.com.br";

// Seeded test slugs: test0000 .. test0099
const SLUGS = Array.from({ length: 100 }, (_, i) =>
  `test${String(i).padStart(4, "0")}`
);

const randomSlug = () => SLUGS[Math.floor(Math.random() * SLUGS.length)];

// ─── Metrics ─────────────────────────────────────────────────────────────────
const RATES = [10, 50, 100, 150, 200, 300, 500];

const trends = {};
const counters = {};
const status2xx = {};
const status3xx = {};
const status429 = {};
const status5xx = {};
const statusOther = {};

for (const r of RATES) {
  trends[r] = new Trend(`dur_${r}`, true);
  counters[r] = new Counter(`hits_${r}`);
  status2xx[r] = new Counter(`status2xx_${r}`);
  status3xx[r] = new Counter(`status3xx_${r}`);
  status429[r] = new Counter(`status429_${r}`);
  status5xx[r] = new Counter(`status5xx_${r}`);
  statusOther[r] = new Counter(`statusOther_${r}`);
}

// ─── Timing ──────────────────────────────────────────────────────────────────
const STAGE_DURATION = 20;
const COOLDOWN = 5;

function stageStart(index) {
  return index * (STAGE_DURATION + COOLDOWN);
}

// ─── Scenarios ───────────────────────────────────────────────────────────────
const scenarios = {};
RATES.forEach((rate, i) => {
  scenarios[`stage_${rate}`] = {
    executor: "constant-arrival-rate",
    rate: rate,
    timeUnit: "1s",
    duration: `${STAGE_DURATION}s`,
    preAllocatedVUs: Math.max(20, Math.ceil(rate / 4)),
    maxVUs: Math.max(200, rate * 2),
    exec: `run_${rate}`,
    startTime: `${stageStart(i)}s`,
  };
});

export const options = {
  scenarios,
  summaryTrendStats: ["avg", "min", "med", "p(95)", "p(99)", "max"],
  // Don't fail the whole run on non-2xx — we expect 429s and want to see them
  noConnectionReuse: false,
};

// ─── Request runner ──────────────────────────────────────────────────────────
function runAt(rate) {
  const res = http.get(`${BASE_URL}/s/${randomSlug()}`, { redirects: 0 });

  const s = res.status;
  if (s >= 200 && s < 300) status2xx[rate].add(1);
  else if (s >= 300 && s < 400) status3xx[rate].add(1);
  else if (s === 429) status429[rate].add(1);
  else if (s >= 500) status5xx[rate].add(1);
  else statusOther[rate].add(1);

  trends[rate].add(res.timings.duration);
  counters[rate].add(1);

  check(res, { [`stage_${rate} redirect or 429`]: (r) => r.status === 302 || r.status === 301 || r.status === 429 });
}

// Each scenario needs its own exec function name
export function run_10()  { runAt(10); }
export function run_50()  { runAt(50); }
export function run_100() { runAt(100); }
export function run_150() { runAt(150); }
export function run_200() { runAt(200); }
export function run_300() { runAt(300); }
export function run_500() { runAt(500); }

// ─── Summary ─────────────────────────────────────────────────────────────────
export function handleSummary(data) {
  const ms = (v) => (v === undefined ? "N/A" : `${v.toFixed(1)}ms`);
  const cnt = (m) => (data.metrics[m]?.values?.count ?? 0);

  const rows = RATES.map((r) => {
    const t = data.metrics[`dur_${r}`];
    const total = cnt(`hits_${r}`);
    return {
      rate: r,
      actualRps: (total / STAGE_DURATION).toFixed(0),
      avg: t?.values?.avg,
      p95: t?.values?.["p(95)"],
      p99: t?.values?.["p(99)"],
      max: t?.values?.max,
      total,
      s2xx: cnt(`status2xx_${r}`),
      s3xx: cnt(`status3xx_${r}`),
      s429: cnt(`status429_${r}`),
      s5xx: cnt(`status5xx_${r}`),
      sOther: cnt(`statusOther_${r}`),
    };
  });

  const header = "╔═════════╦═════════╦══════════╦══════════╦══════════╦══════════╦═══════╦═══════╦═══════╦═══════╦═══════╗";
  const sep    = "╠═════════╬═════════╬══════════╬══════════╬══════════╬══════════╬═══════╬═══════╬═══════╬═══════╬═══════╣";
  const footer = "╚═════════╩═════════╩══════════╩══════════╩══════════╩══════════╩═══════╩═══════╩═══════╩═══════╩═══════╝";
  const title  = "║ Target  ║ Actual  ║ avg      ║ p95      ║ p99      ║ max      ║ 2xx   ║ 3xx   ║ 429   ║ 5xx   ║ other ║";

  const body = rows
    .map((r) =>
      `║ ${String(r.rate).padEnd(7)} ║ ${String(r.actualRps).padEnd(7)} ║ ${ms(r.avg).padEnd(8)} ║ ${ms(r.p95).padEnd(8)} ║ ${ms(r.p99).padEnd(8)} ║ ${ms(r.max).padEnd(8)} ║ ${String(r.s2xx).padEnd(5)} ║ ${String(r.s3xx).padEnd(5)} ║ ${String(r.s429).padEnd(5)} ║ ${String(r.s5xx).padEnd(5)} ║ ${String(r.sOther).padEnd(5)} ║`
    )
    .join("\n");

  const report = `
${header}
║                       SHORTER — Production Redirect Benchmark                                                      ║
║                       https://gabrielafonso.com.br/s/<slug>                                                        ║
${sep}
${title}
${sep}
${body}
${footer}
`;

  console.log(report);
  return {
    stdout: report,
    "benchmark-results.txt": report,
  };
}
