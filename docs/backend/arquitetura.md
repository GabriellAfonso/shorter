# Arquitetura

## Visão Geral

O backend segue uma arquitetura em camadas de **views finas + services/selectors**. A lógica de negócio vive em funções de serviço; as consultas ao banco de dados ficam em funções seletoras; as views apenas validam a entrada e orquestram as chamadas.

```
Request → View → Serializer (validação)
                    ↓
               Service (escrita) / Selector (leitura)
                    ↓
              Model / Cache / Tarefa Celery
```

## Estrutura de Diretórios

```
backend/
├── apps/
│   ├── accounts/   # Autenticação e gerenciamento de usuários
│   └── links/      # Encurtamento de URLs e analytics
├── config/         # Settings do Django, URLs raiz, Celery
├── core/           # Utilitários compartilhados (paginação, exceções, permissões)
├── locale/         # Arquivos de tradução (.po / .mo)
├── conftest.py
└── manage.py
```

Cada app segue a mesma convenção interna: `api/` (views + serializers + urls), `models/`, `services/`, `selectors/`, `tests/`.

## Roteamento de URLs

Roteador raiz: `config/urls.py`

| Caminho | Módulo | Observações |
|---------|--------|-------------|
| `/api/v1/health/` | `core.views.HealthCheckView` | Sem autenticação |
| `/api/v1/auth/` | `apps.accounts.api.auth_urls` | Register, login, logout, refresh |
| `/api/v1/users/` | `apps.accounts.api.users_urls` | Gerenciamento de perfil |
| `/api/v1/links/` | `apps.links.api.urls` | CRUD de links + analytics |
| `/s/<slug>/` | `apps.links.redirect_views` | Redirect (última rota, sem auth) |
| `/api/schema/` | drf-spectacular | Schema OpenAPI |
| `/api/schema/swagger-ui/` | drf-spectacular | Swagger UI |
| `/api/schema/redoc/` | drf-spectacular | ReDoc |
| `/robots.txt` | template Django | Bloqueia `/s/`, `/api/`, `/core/` |

## Camadas

### Views
- Finas — validam a entrada com serializers, chamam services/selectors, retornam `Response`.
- Sem lógica de negócio.
- Sem acesso direto ao banco de dados.

### Services (`services/`)
- Todas as operações de escrita (criar, atualizar, deletar).
- Aplicam regras de negócio (cota, unicidade, SSRF).
- Gerenciam invalidação de cache.
- Disparam tarefas Celery para trabalho assíncrono.

### Selectors (`selectors/`)
- Todas as operações de leitura (consultas, agregações).
- Cache Redis onde apropriado.
- Retornam instâncias de model ou dicts simples.

### Models
- Finos — apenas definição de campos, índices e propriedades simples.
- Sem lógica de negócio em métodos do model.

## Estratégia de Cache

| Dado | Chave da aplicação | Chave real no Redis | TTL | Invalidado em |
|------|-------------------|---------------------|-----|--------------|
| URL de destino + ID do link | `redirect:{slug}` | `urlshortener:redirect:{slug}` | 24h (menos se o link expirar antes) | Soft-delete, expiração do link |
| Agregação de analytics | `analytics:{link_id}:{days}` | `urlshortener:analytics:{link_id}:{days}` | 30 s | Soft-delete do link |

O `KEY_PREFIX = "urlshortener"` é adicionado automaticamente pelo Django cache framework. As chaves de aplicação são definidas sem o prefixo no código (`redirect:{slug}`, `analytics:{link_id}:{days}`). Todas as chaves são armazenadas no Redis com compressão zlib.

Cache miss cai automaticamente no banco de dados.

## Processamento Assíncrono (Celery)

```
Requisição de redirect
    ↓
RedirectView (síncrono, rápido)
    ↓ HTTP 302 retornado imediatamente
    ↓ (sem bloqueio)
tarefa log_click disparada → worker Celery → record_click() → LinkClick criado
```

**Tarefas:**

| Tarefa | Fila | Gatilho |
|--------|------|---------|
| `log_click` | `clicks` | Cada redirect (assíncrono) |
| `deactivate_expired_links` | default | Periódico (django-celery-beat) |

## Fluxo de Requisição: Redirect

```
GET /s/abc123/
    │
    ▼
RedirectView
    ├── Verificação de rate limit no Redis (configurável via REDIRECT_RATE_LIMIT, padrão: 100/min por IP)
    │       └── 429 Too Many Requests se excedido (+ header Retry-After)
    │
    ├── get_redirect_url("abc123")
    │       ├── Cache Redis hit → retorna (url, link_id)
    │       └── Cache miss → consulta no DB → popula cache → retorna (url, link_id)
    │
    ├── 404 se slug não encontrado ou link expirado
    │
    ├── Dispara log_click.delay(link_id, ip, ua, referrer)  ← assíncrono, sem bloqueio
    │
    └── HTTP 302 Location: <original_url>
```

## Fluxo de Requisição: Criar URL Curta

```
POST /api/v1/links/
    │
    ▼
LinkListCreateView
    ├── Autenticação JWT
    ├── LinkCreateThrottle (20/min por usuário)
    ├── CreateShortURLSerializer.is_valid()
    │       ├── validate_target_url() — verificação SSRF
    │       └── validate_custom_slug() — se slug fornecido
    │
    └── create_short_url(original_url, owner, custom_slug, title, expires_at)
            ├── Verificação de cota (máx. 30 links ativos)
            ├── Geração de slug (aleatório ou personalizado)
            └── ShortURL.objects.create(...)
```

## Internacionalização

- `LocaleMiddleware` do Django lê o header `Accept-Language`.
- Todas as strings de erro voltadas ao usuário usam `gettext_lazy` (`_()`).
- Idiomas suportados: Inglês (`en`), Português do Brasil (`pt-BR`).
- Arquivos de tradução: `backend/locale/pt_BR/LC_MESSAGES/django.po` (compilado para `.mo`).
