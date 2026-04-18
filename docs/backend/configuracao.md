# Configuração

Os settings estão divididos em três arquivos em `backend/config/settings/`:

| Arquivo | Usado quando |
|---------|-------------|
| `base.py` | Sempre — base compartilhada |
| `development.py` | `DJANGO_SETTINGS_MODULE=config.settings.development` |
| `production.py` | `DJANGO_SETTINGS_MODULE=config.settings.production` |

As variáveis de ambiente são lidas diretamente via `os.environ.get()` (com valores padrão embutidos). Para desenvolvimento local, crie um arquivo `.env` e exporte as variáveis no shell antes de rodar o Django — ou use uma ferramenta como `direnv`.

Copie `.env.example` para `.env` e preencha os valores:

```bash
cp backend/.env.example backend/.env
```

---

## Variáveis de Ambiente

### Django (Core)

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `SECRET_KEY` | Sim | — | Chave secreta do Django (string aleatória longa) |
| `DEBUG` | Não | `False` | Ativar modo debug |
| `ALLOWED_HOSTS` | Sim (prod) | `localhost` | Lista de hostnames permitidos separados por vírgula |
| `DJANGO_SETTINGS_MODULE` | Não | `config.settings.development` | Módulo de settings a usar |

### Banco de Dados

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `DATABASE_URL` | Sim | `sqlite:///db.sqlite3` | URL de conexão do banco (formato dj-database-url) |

**Exemplos de formato:**
```
DATABASE_URL=postgres://usuario:senha@localhost:5432/shorter
DATABASE_URL=sqlite:///db.sqlite3
```

### Redis / Cache / Celery

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `REDIS_URL` | Sim | `redis://localhost:6379/0` | URL de conexão do Redis |

O Redis é usado tanto como **backend de cache** quanto como **broker do Celery**.

### CORS

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `CORS_ALLOWED_ORIGINS` | Sim (prod) | — | Lista de origens de frontend permitidas, separadas por vírgula |

**Exemplo:**
```
CORS_ALLOWED_ORIGINS=https://shorter.exemplo.com,https://www.shorter.exemplo.com
```

### Configurações da Aplicação

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `SHORT_URL_BASE_DOMAIN` | Não | `http://localhost:8000` | URL base prefixada ao slug ao construir a URL curta |
| `SHORT_URL_LENGTH` | Não | `8` | Comprimento dos slugs gerados automaticamente (caracteres base-62) |
| `MAX_LINKS_PER_USER` | Não | `30` | Máximo de links ativos por usuário |

> **Constantes hardcoded em `base.py`** (não configuráveis via env var — altere diretamente no código se necessário):
> - `REDIRECT_CACHE_TTL = 86400` — TTL do cache de redirect em segundos (24 horas)
> - `REDIRECT_RATE_LIMIT = 100` — requisições de redirect permitidas por minuto por IP
> - `MAX_TARGET_URL_LENGTH = 2048` — comprimento máximo das URLs de destino

### Configurações apenas de Produção

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `SECURE_SSL_REDIRECT` | — | `False` em prod | Explicitamente desabilitado — o nginx já faz o redirect HTTP→HTTPS; deixar `True` causaria double-redirect |

---

## Referência de Settings

### Tempo de Vida dos Tokens JWT

Configurado em `base.py` sob `SIMPLE_JWT`:

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}
```

### Limites de Throttle

Configurado em `base.py` sob `REST_FRAMEWORK`:

```python
DEFAULT_THROTTLE_RATES = {
    "anon": "60/minute",
    "user": "300/minute",
    "auth": "10/minute",          # registro + login
    "link_create": "20/minute",   # POST /links/
    "link_analytics": "60/minute", # GET /links/{id}/analytics/
    "redirect": "200/minute",     # /s/<slug>/ (fallback do Redis sliding window)
}
```

Em desenvolvimento, o dict `DEFAULT_THROTTLE_RATES` é **substituído inteiramente** por uma versão com apenas `anon` (1000/minute), `user` (5000/minute) e `auth` (10/minute). As chaves `link_create` e `link_analytics` não existem no dict de dev — os throttles escopados (`LinkCreateThrottle`, `LinkAnalyticsThrottle`) ficam sem configuração de limite em desenvolvimento, o que na prática desativa essas restrições localmente.

### Paginação

```python
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardResultsPagination",
    "PAGE_SIZE": 20,
}
```

### Celery

```python
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = None  # tarefas são fire-and-forget; resultado não é necessário
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "America/Sao_Paulo"
CELERY_TASK_ROUTES = {
    "apps.links.tasks.*": {"queue": "clicks"},
}
```

A tarefa periódica `deactivate_expired_links` é registrada via migration `0002` e gerenciada pelo `django-celery-beat`.

### Cache

```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
        },
        "KEY_PREFIX": "urlshortener",
        "TIMEOUT": 300,  # TTL padrão de 5 minutos
    }
}
```

### Internacionalização

```python
LANGUAGE_CODE = "pt-br"  # Idioma padrão
LANGUAGES = [
    ("en", "English"),
    ("pt-br", "Português (Brasil)"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
```

O idioma é selecionado por requisição via header `Accept-Language` (tratado pelo `LocaleMiddleware`).

---

## Logging

Todos os ambientes registram no console (`stdout`). Níveis de log:

| Logger | Nível |
|--------|-------|
| `django` | `INFO` |
| `django.request` | `DEBUG` (dev) / `WARNING` (prod) |
| `apps` | `DEBUG` |
| `celery` | `INFO` |

Em produção, considere encaminhar os logs para um agregador centralizado (ex.: Papertrail, Datadog ou CloudWatch).
