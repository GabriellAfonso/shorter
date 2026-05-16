# Isolated Code Benchmark

Goal: produce **portable, code-defined performance numbers** for the resume —
not numbers that depend on a particular VPS.

The backend container is pinned to **1 vCPU / 1G RAM** via
`docker-compose.bench.yml`. Postgres and Redis run unlimited so they never
become the bottleneck. Any number you read off is a property of the
backend code at that resource budget.

---

## What gets measured

| Scenario     | URL pattern                | Path exercised                              |
|--------------|----------------------------|---------------------------------------------|
| `warmup`     | `/s/test0000../s/test0099` | Pre-loads the Redis cache with 100 slugs    |
| `hit_<rate>` | random warm slug → 302     | Cache-hit hot path                          |
| `nf_<rate>`  | random unknown slug → 404  | Cache-miss / negative-cache effectiveness   |

Each path is exercised at **6 fixed RPS levels** (5, 20, 40, 60, 80, 100)
using `constant-arrival-rate` for 15 s per level. Every level emits its
own latency Trend and status counters, so the final table has one row per
RPS step — no aggregation hiding the saturation knee.

The number you report is the **highest RPS where p95 stays under your
latency budget** (e.g. 100 ms) with 0 % error.

---

## Run it

> Commands are PowerShell-friendly (Windows host).

### 1. Start the isolated stack

Cache **OFF** (default — every request hits the DB, baseline):
```powershell
docker compose -f docker-compose.bench.yml up -d --build --wait
```

Cache **ON** (Redis-backed):
```powershell
docker compose -f docker-compose.bench.yml down -v
$env:CACHE_REDIS = "true"
docker compose -f docker-compose.bench.yml up -d --build --wait
```

The backend container auto-bootstraps on first start:
1. `migrate --noinput`
2. Creates a bench user (`bench@bench.local`)
3. Seeds slugs `test0000..test0099`
4. Starts gunicorn (2 workers, uvicorn worker class)

The `--wait` flag blocks until every service is healthy.

Confirm what the backend actually loaded:
```powershell
docker compose -f docker-compose.bench.yml exec backend env | findstr CACHE_REDIS
```

### 2. Run k6

```powershell
k6 run -e CACHE_MODE=off benchmark-isolated.js
# or, after restarting the stack with CACHE_REDIS=true:
k6 run -e CACHE_MODE=on benchmark-isolated.js
```

`CACHE_MODE` is **just a label** that appears in the report header — it
does not toggle anything. The real toggle is the backend environment
variable `CACHE_REDIS`, set when the container starts.

Each run takes ~4 minutes (warmup + 6 hit stages + 6 not-found stages).
Results write to `benchmark-isolated-results.txt`.

### 3. Tear down

```powershell
docker compose -f docker-compose.bench.yml down -v
Remove-Item Env:CACHE_REDIS   # clear the host env var
```

---

## How to read the output

```
HIT path (302 — known slug, cache hit after warmup):
║ RPS ║ p50      ║ p95       ║ p99       ║ max       ║ err   ║ total ║
║ 5   ║ 11.5ms   ║ 13.2ms    ║ 15.2ms    ║ 16.6ms    ║ 0.0%  ║ 76    ║
║ 20  ║ 10.2ms   ║ 12.0ms    ║ 15.5ms    ║ 189.0ms   ║ 0.0%  ║ 301   ║
║ 40  ║ 10.2ms   ║ 12.5ms    ║ 16.6ms    ║ 73.4ms    ║ 0.0%  ║ 600   ║
║ 60  ║ 11.0ms   ║ 1679.9ms  ║ 2082.8ms  ║ 2257.4ms  ║ 0.0%  ║ 886   ║  ← knee
║ 80  ║ 4280.5ms ║ 5978.8ms  ║ 6886.6ms  ║ 7607.7ms  ║ 0.0%  ║ 947   ║
║ 100 ║ 7258.2ms ║ 12092.2ms ║ 12647.2ms ║ 13548.2ms ║ 0.0%  ║ 938   ║
```

- **p50 / p95 / p99** = latency percentiles within that 15 s slice at
  that exact RPS.
- **err** = non-success rate (429 + 5xx + unexpected statuses).
- **total** = completed iterations at that level. Drops when the server
  cannot keep up with the requested rate.
- **Knee** = the first row where p95 leaves your latency budget. The
  previous row is your "max sustained RPS" claim.

In the example above the knee is between **40 RPS** (p95 = 12.5 ms) and
**60 RPS** (p95 = 1.7 s). The defensible number is **40 RPS sustained at
p95 < 15 ms**.

---

## Cache ON vs OFF — example comparison

Measured on the same 1 vCPU container, same code, only `CACHE_REDIS`
toggled between runs:

| Path | RPS | Cache ON p50 | Cache OFF p50 | Speedup |
|------|-----|-------------:|--------------:|--------:|
| HIT  | 5   | 11.5 ms      | 23.7 ms       | 2.1×    |
| HIT  | 40  | 10.2 ms      | 22.8 ms       | 2.2×    |
| NF   | 40  | 18.5 ms      | 17.5 ms       | ≈ 1×    |

Two observations worth understanding:

1. The cache delivers a clean ~2.2× speedup on the hit path — that is the
   headline metric.
2. On the not-found path, cache ON is **not** faster than DummyCache,
   because every miss still does a Redis round-trip *and* a DB query.
   Adding a negative cache (TTL the `None` result) would close that gap.

---

## Resume-ready phrasing

Pick the strongest 1–2 of these and replace placeholders with your own
measured numbers:

- "URL shortener: **p50 of ~10 ms** on the redirect hot path with a Redis
  cache (vs ~23 ms without — **~2.2× speedup**), sustained at 40 RPS
  on a 1 vCPU backend with **p95 < 15 ms** and **0 % error**."
- "Click logging dispatched asynchronously via Celery
  (`acks_late=True`, `max_retries=3`) — redirect latency stays decoupled
  from analytics write volume."
- "Benchmark is fully reproducible: `docker-compose.bench.yml` pins the
  backend to 1 vCPU / 1G RAM, seeds 100 deterministic slugs on startup,
  and the k6 script sweeps 5 → 100 RPS in 6 fixed steps so the saturation
  knee is visible directly in the result table."

---

## Why these numbers are defensible

1. **Resources are pinned** — no "it depends on your hardware" excuse.
2. **Postgres and Redis are unlimited** — the backend code is the only
   variable.
3. **Rate limiting is off** (`BENCHMARK_MODE=true`) — caps reflect code,
   not policy.
4. **Cache toggle is built in** — the ON vs OFF comparison directly
   demonstrates the engineering decision.
5. **Constant-arrival-rate, not ramping** — each row is steady-state at
   one specific RPS, so percentiles are not poisoned by mixing load
   levels.
6. **Reproducibility** — anyone can clone the repo, run two commands,
   and reproduce the numbers within ~5 %.
