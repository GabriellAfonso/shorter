# Shorter — Encurtador de URLs

Encurtador full-stack com foco em arquitetura em camadas, cache, tarefas assíncronas e segurança.

[![Django](https://img.shields.io/badge/Django-6.x-092E20?logo=django)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.16-red?logo=django)](https://www.django-rest-framework.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-8-DC382D?logo=redis)](https://redis.io)
[![Celery](https://img.shields.io/badge/Celery-5-37814A?logo=celery)](https://docs.celeryq.dev)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)

---

## Funcionalidades

- Slug base-62 de 8 chars via `secrets` (~218 trilhões de combinações)
- Slug custom com palavras reservadas (`admin`, `api`, `login`…)
- TTL opcional por link; Celery Beat desativa expirados
- Analytics: cliques diários, dispositivo, top referrers (cache Redis 30 s)
- JWT — access 15 min + refresh 7 dias com blacklist no logout
- Rate limit Redis no redirect (fixed-window 60s, 100 req/min por IP) + `UserRateThrottle` por ação no DRF
- SSRF: bloqueia IPs privados (RFC1918, loopback, link-local) e IMDS (AWS/GCP)
- IPs armazenados como hash SHA-256 truncado
- Log de cliques assíncrono (Celery) — não bloqueia o 302

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Django 6 + DRF 3.16 |
| Auth | SimpleJWT (rotação + blacklist) |
| Banco | PostgreSQL 16 |
| Cache / Broker | Redis 8 |
| Async | Celery 5 + django-celery-beat |
| Frontend | React 18 + TypeScript + Vite |
| Docs API | drf-spectacular (Swagger / OpenAPI 3) |
| Containers | Docker Compose v2 |

---

## Início rápido

**Pré-requisito:** Docker Desktop ≥ 24

```bash
git clone https://github.com/GabriellAfonso/shorter.git
cd shorter
cp backend/.env.example backend/.env
docker compose up --build
```

| Serviço | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000/api/v1/ |
| Swagger | http://localhost:8000/api/schema/swagger-ui/ |
| Admin | http://localhost:8000/core/ |
| Health | http://localhost:8000/api/v1/health/ |

Credenciais demo: `admin@demo.com / admin1234` · `user@demo.com / demo1234`

---

## API

Prefixo `/api/v1/`. Documentação interativa em `/api/schema/swagger-ui/`.

- `auth/` — register, login, logout, token/refresh
- `users/me/` — perfil, update, change-password
- `links/` — CRUD + `links/{id}/analytics/?days=30`
- `s/{slug}/` — redirect público 302
- `health/` — status DB + Redis

---

## Arquitetura

Feature-based:

```
backend/
├── config/       # settings, urls, celery
├── core/         # exceptions, permissions, utils, health
└── apps/
    ├── accounts/ # User custom + auth + profile
    └── links/    # models, services, selectors, validators, throttles, tasks
```

Fluxo: `Views → Services → Repositories/Selectors → Models`. Views finas, regras de negócio nos services, queries + cache nos selectors.

---

## Decisões de design

- **Cache de redirect** — Redis consultado antes do DB (`redirect:{slug}`). TTL = mín(expiry, 24 h). Redirect < 100 ms quente.
- **Log async** — `log_click.delay()` disparado *após* o 302. Worker persiste `LinkClick` e incrementa `click_count` via `F()`.
- **SSRF** — `validate_target_url` parseia hostname, bloqueia IPs privados e schemes não HTTP(S).
- **JWT blacklist** — refresh invalidado no logout via `simplejwt.token_blacklist`. Axios intercepta 401 e renova access silenciosamente.

---

## License

GNU General Public License v3.0 — veja LICENSE para detalhes.
