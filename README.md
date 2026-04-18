# Linkr — Encurtador de URLs

Encurtador de URLs full-stack construído como projeto de portfólio, com foco em boas práticas de backend: arquitetura em camadas, cache, tarefas assíncronas e segurança.

[![Django](https://img.shields.io/badge/Django-6.x-092E20?logo=django)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.16-red?logo=django)](https://www.django-rest-framework.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-8-DC382D?logo=redis)](https://redis.io)
[![Celery](https://img.shields.io/badge/Celery-5-37814A?logo=celery)](https://docs.celeryq.dev)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)

---

## Funcionalidades

- **Encurtamento** — slug base-62 de 8 chars (218 trilhões de combinações), gerado com `secrets` e livre de colisões
- **Slug personalizado** — com lista de palavras reservadas protegidas (`admin`, `api`, `login`…)
- **Expiração de links** — TTL opcional por link; Celery Beat desativa expirados periodicamente
- **Analytics** — cliques diários, breakdown por dispositivo e top referrers (cache Redis com TTL de 30 s)
- **Autenticação JWT** — access token (15 min) + refresh token (7 dias) com blacklist no logout
- **Rate limiting** — janela deslizante via Redis nos redirecionamentos (100 req/min por IP); throttle por escopo no DRF para criação e analytics
- **Proteção SSRF** — bloqueia IPs privados RFC1918, loopback, link-local e endpoints de metadados (AWS IMDS, GCP)
- **Privacidade** — IPs armazenados como hash SHA-256 truncado; nunca o IP bruto
- **Log assíncrono de cliques** — task Celery disparada após o HTTP 302, sem adicionar latência ao redirecionamento

---

## Arquitetura

```
Navegador
    │
    ▼
Nginx (80/443)  ──────────────────────────────────────────┐
    │  /api/*  /s/*                                        │  /*
    ▼                                                      ▼
Django + Uvicorn/Gunicorn (8000)                  React SPA (nginx)
    │
    ├── PostgreSQL  (dados)
    ├── Redis       (cache de slugs + broker Celery)
    └── Celery Worker  (log de cliques, desativação de expirados)
          └── Celery Beat  (agendador)
```

### Fluxo de redirecionamento (hot path)

```
GET /s/<slug>
  → hit no Redis?  → 302 para a URL original         (< 5 ms com cache quente)
  → cache miss     → busca no banco → 302, re-cacheia no Redis
  → após a resposta: task Celery persiste LinkClick + incrementa click_count via F()
```

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Django 6 + Django REST Framework 3.16 |
| Auth | SimpleJWT — access 15 min, refresh 7 dias, blacklist |
| Banco | PostgreSQL 16 (`uuid-ossp`, `pg_trgm`) |
| Cache / Broker | Redis 8 (AOF, LRU 256 MB) |
| Tarefas assíncronas | Celery 5 + django-celery-beat |
| Frontend | React 18 + TypeScript + Vite |
| Documentação da API | drf-spectacular (OpenAPI 3 / Swagger) |
| Containers | Docker + Docker Compose v2 |
| Proxy reverso | Nginx 1.27 |

---

## Início rápido (Docker)

**Pré-requisito:** Docker Desktop ≥ 24

```bash
git clone https://github.com/seu-usuario/linkr.git
cd linkr

cp backend/.env.example backend/.env

docker compose up --build
```

| Serviço | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000/api/v1/ |
| Admin | http://localhost:8000/core/ |
| Health | http://localhost:8000/api/v1/health/ |

Credenciais de demo (criadas automaticamente):

| Papel | E-mail | Senha |
|---|---|---|
| Admin | admin@demo.com | admin1234 |
| Usuário | user@demo.com | demo1234 |

---

## API

Todos os endpoints usam o prefixo `/api/v1/`. Requisições autenticadas exigem `Authorization: Bearer <access_token>`.

### Auth

| Método | Endpoint | Autenticação | Descrição |
|---|---|---|---|
| `POST` | `/auth/register/` | — | Cadastro, retorna tokens + usuário |
| `POST` | `/auth/login/` | — | Login, retorna tokens |
| `POST` | `/auth/logout/` | ✓ | Invalida refresh token |
| `POST` | `/auth/token/refresh/` | — | Renova access token |

### Links

| Método | Endpoint | Autenticação | Descrição |
|---|---|---|---|
| `GET` | `/links/` | ✓ | Lista links (paginado, 20/página) |
| `POST` | `/links/` | ✓ | Cria link encurtado |
| `GET` | `/links/{id}/` | ✓ | Detalhe do link |
| `DELETE` | `/links/{id}/` | ✓ | Desativa link |
| `GET` | `/links/{id}/analytics/?days=30` | ✓ | Analytics (cliques, dispositivos, referrers) |

**Criar link** `POST /links/`
```json
// Request
{
  "original_url": "https://exemplo.com/caminho/longo",
  "slug": "meu-link",          // opcional
  "title": "Página exemplo",   // opcional
  "expires_at": "2025-12-31T23:59:00"  // opcional, null = sem expiração
}

// Response 201
{
  "id": "uuid",
  "slug": "meu-link",
  "short_url": "http://localhost:8000/s/meu-link",
  "original_url": "https://exemplo.com/caminho/longo",
  "click_count": 0,
  "is_active": true,
  "is_expired": false,
  "expires_at": "2025-12-31T23:59:00Z",
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Analytics** `GET /links/{id}/analytics/?days=30`
```json
{
  "total_clicks": 142,
  "daily_clicks": [{ "date": "2025-01-01", "clicks": 12 }],
  "device_breakdown": [
    { "device_type": "desktop", "count": 89 },
    { "device_type": "mobile",  "count": 45 }
  ],
  "top_referrers": [{ "referrer": "https://twitter.com", "count": 34 }]
}
```

### Redirecionamento e Health

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/s/{slug}/` | 302 para a URL original |
| `GET` | `/api/v1/health/` | Status do banco e do Redis |

---

## Estrutura do backend

```
backend/
├── config/
│   ├── settings/{base,development,production}.py
│   ├── celery.py
│   └── urls.py
├── core/
│   ├── exceptions.py      # envelope de erro padronizado
│   ├── permissions.py     # IsOwner
│   ├── utils.py           # generate_slug, hash_ip, get_client_ip
│   └── views.py           # HealthCheckView
└── apps/
    ├── authentication/    # register / login / logout / token refresh
    ├── users/             # modelo User customizado (email como username)
    └── links/
        ├── models/        # ShortURL, LinkClick
        ├── api/           # serializers + views + URLs (DRF)
        ├── services/      # lógica de negócio (link_service.py)
        ├── selectors/     # queries + cache Redis (link_selector.py)
        ├── validators.py  # validação SSRF-safe + slugs reservados
        ├── throttles.py   # ScopedRateThrottle por ação
        ├── tasks.py       # Celery: log_click, deactivate_expired_links
        ├── redirect_views.py  # view Django (não DRF) + rate limit Redis
        └── tests/         # pytest (~80%+ coverage)
```

### Padrão de arquitetura

- **Services** — toda lógica de negócio (`create_short_url`, `record_click`)
- **Selectors** — todas as leituras do banco + cache (`get_link_by_slug`, `get_cached_link_analytics`)
- **Views** — finas: validam entrada, chamam service, retornam Response

---

## Decisões de design

**Cache de redirecionamento no Redis** — A view de redirect consulta o Redis antes do banco (`redirect:{slug}`). TTL = mínimo entre expiração do link e 24 h. Mantém redirecionamentos abaixo de 100 ms com cache quente.

**Log assíncrono com Celery** — `log_click.delay(...)` é disparado *após* o HTTP 302. O worker persiste `LinkClick` e incrementa `click_count` via `F("click_count") + 1`. O redirect nunca espera por analytics.

**Proteção SSRF** — `validate_target_url` resolve o hostname e bloqueia IPs privados, loopback, link-local, AWS IMDS (`169.254.169.254`) e esquemas não HTTP(S).

**JWT com blacklist** — Refresh tokens são invalidados no logout via `rest_framework_simplejwt.token_blacklist`. O cliente Axios intercepta 401 e renova silenciosamente o access token antes de reenviar as requisições em fila.

**Multi-stage Docker** — Estágio *builder* compila wheels com `libpq-dev`; estágio *runtime* só instala `libpq5`. Reduz o tamanho da imagem final pela metade.

---

## Testes

```bash
# Com Docker (recomendado)
make test

# Localmente (venv ativado)
cd backend && pytest

# Com cobertura detalhada
pytest --cov=. --cov-report=html
```

Isolamento: o fixture `use_locmem_cache` em `conftest.py` substitui o Redis pelo `LocMemCache` do Django em todos os testes — sem necessidade de Redis rodando.

Meta de cobertura: **80%** nos caminhos críticos (configurado em `pytest.ini`).

---

## Variáveis de ambiente

Copie `backend/.env.example` para `backend/.env`. Os padrões funcionam para o Docker local.

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | *(obrigatório)* | Chave secreta do Django |
| `DJANGO_SETTINGS_MODULE` | `config.settings.development` | Módulo de settings |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/urlshortener` | Conexão com o banco |
| `REDIS_URL` | `redis://localhost:6379/0` | Conexão com o Redis |
| `SHORT_URL_BASE_DOMAIN` | `http://localhost:8000` | Prefixo da URL curta gerada |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Origens CORS permitidas |
| `SHORT_URL_LENGTH` | `8` | Comprimento do slug gerado automaticamente |

---

## License

MIT
