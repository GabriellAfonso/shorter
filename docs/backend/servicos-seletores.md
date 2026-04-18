# Services e Selectors

A aplicação impõe uma separação estrita entre **escrita** (services) e **leitura** (selectors). As views nunca consultam o banco de dados diretamente.

---

## Resumo do Padrão

| Camada | Responsabilidade | Acesso direto ao DB |
|--------|-----------------|-------------------|
| **View** | Parsing HTTP, validação com serializer, resposta HTTP | Não |
| **Service** | Operações de escrita, regras de negócio, invalidação de cache | Sim (escrita) |
| **Selector** | Operações de leitura, agregações, cache | Sim (leitura) |
| **Task** | Execução assíncrona de chamadas a services | Via service |

---

## Services de Usuário

**Módulo:** `apps/accounts/services/user_service.py`

### `create_user(*, email, password, first_name="", last_name="")`

Cria e retorna uma nova instância de `User`.

```python
from apps.accounts.services.user_service import create_user

user = create_user(
    email="alice@exemplo.com",
    password="senha123",
    first_name="Alice",     # opcional
    last_name="Silva",      # opcional
)
```

**Comportamento:**
- Normaliza o e-mail (lowercase).
- Chama `User.objects.create_user()`, que realiza o hash da senha.
- Registra a criação no log.

---

### `update_user(*, user, first_name=None, last_name=None, bio=None, avatar_url=None)`

Atualiza parcialmente uma instância de `User`. Apenas os campos fornecidos (não-None) são atualizados.

```python
from apps.accounts.services.user_service import update_user

update_user(user=user, bio="Nova bio", avatar_url="https://exemplo.com/img.jpg")
```

**Comportamento:**
- Atualiza apenas os campos fornecidos usando `update_fields` para eficiência.
- Registra a atualização no log.

---

### `change_password(*, user, old_password, new_password)`

Altera a senha do usuário e invalida todas as sessões existentes.

```python
from apps.accounts.services.user_service import change_password

change_password(user=user, old_password="atual", new_password="nova123")
```

**Comportamento:**
- Valida `old_password` contra o hash armazenado; lança `ValidationError` se incorreta.
- Define a nova senha.
- Coloca na blacklist todos os `OutstandingToken` do usuário (força reautenticação em todos os dispositivos).
- Registra a ação no log.

---

## Selectors de Usuário

**Módulo:** `apps/accounts/selectors/user_selector.py`

### `get_user_by_id(user_id) → User`

Retorna o `User` com o ID fornecido, ou lança `NotFound`.

### `get_user_by_email(email) → User`

Retorna o `User` com o e-mail fornecido (case-insensitive), ou lança `NotFound`.

### `user_exists(email) → bool`

Retorna `True` se existir um usuário com o e-mail fornecido.

---

## Services de Links

**Módulo:** `apps/links/services/link_service.py`

### `create_short_url(*, original_url, owner, custom_slug=None, title="", expires_at=None) → ShortURL`

Cria uma nova URL encurtada.

```python
from apps.links.services.link_service import create_short_url

link = create_short_url(
    original_url="https://exemplo.com/caminho/muito/longo",
    owner=request.user,
    custom_slug="meu-link",   # opcional
    title="Meu Link",         # opcional
    expires_at=None,          # datetime opcional
)
```

**Comportamento (em ordem):**
1. Conta os links com `is_active=True` do usuário. Lança `QuotaExceeded` se ≥ 30.
2. Valida `original_url` via `validate_target_url()` (SSRF, esquema, comprimento).
3. Se `custom_slug` fornecido:
   - Valida o formato via `validate_custom_slug()`.
   - Verifica unicidade; lança `ValidationError` no campo `slug` se já existir.
4. Se sem slug: gera um slug aleatório em base-62 (`generate_slug()`). Tenta até 5 vezes em caso de colisão.
5. Infere `title` a partir do domínio se não fornecido.
6. Cria e retorna a instância de `ShortURL`.
7. Registra a criação no log.

**Lança:**
- `QuotaExceeded` (422) — limite de links ativos atingido
- `ValidationError` (400) — slug personalizado já em uso, URL inválida ou slug com formato inválido

---

### `delete_short_url(*, link)`

Soft-delete de um `ShortURL`.

```python
from apps.links.services.link_service import delete_short_url

delete_short_url(link=link)
```

**Comportamento:**
1. Limpa o cache de redirect no Redis para o slug.
2. Invalida o cache de analytics para o ID do link.
3. Define `link.is_active = False` e salva no banco.
4. Registra a deleção no log.

---

### `get_redirect_url(slug) → tuple[str, str] | None`

Retorna `(url_destino, link_id)` para um slug, ou `None` se não encontrado.

**Comportamento:**
1. Verifica o cache Redis (chave de aplicação: `redirect:{slug}`; chave real: `urlshortener:redirect:{slug}`). Retorna valor em cache se existir.
2. Em caso de cache miss: consulta o `ShortURL` via `get_link_by_slug()`.
3. Calcula o TTL (24h ou vida restante do link, o que for menor).
4. Armazena URL + ID no Redis.
5. Retorna `(original_url, link.id)`.

---

### `record_click(*, link_id, ip_address, user_agent, referrer)`

Cria um registro de `LinkClick` e incrementa `ShortURL.click_count`. Chamado pela tarefa Celery — não chamado diretamente pelas views.

**Comportamento:**
1. Busca o `ShortURL` pelo ID.
2. Analisa o `user_agent` em browser, SO e device_type via biblioteca `user-agents`.
3. Aplica SHA-256 no `ip_address`.
4. Cria `LinkClick` com todos os campos processados.
5. Incrementa `click_count` atomicamente usando `F("click_count") + 1`.

---

## Selectors de Links

**Módulo:** `apps/links/selectors/link_selector.py`

### `get_link_by_slug(slug) → ShortURL`

Retorna um `ShortURL` ativo e não expirado para o slug fornecido.

**Lança:** `NotFound` (404) se o slug não existir, estiver inativo ou expirado.

---

### `get_link_by_id(link_id, owner=None) → ShortURL`

Retorna um `ShortURL` pelo UUID. Opcionalmente restringe a um owner específico.

**Lança:** `NotFound` (404) se não encontrado.

---

### `get_user_links(user, is_active=None) → QuerySet`

Retorna um `QuerySet` dos links do usuário. Passe `is_active=True` ou `is_active=False` para filtrar.

---

### `get_link_analytics(link, days=30) → dict`

Agrega analytics brutos do banco de dados (sem cache).

**Retorna:**

```python
{
    "total_clicks": 142,
    "clicks_in_period": 38,
    "period_days": 30,
    "daily_clicks": [
        {"date": "2025-01-01", "count": 5},
        ...
    ],
    "by_device": [
        {"device_type": "desktop", "count": 25},
        ...
    ],
    "top_referrers": [
        {"referrer": "https://twitter.com", "count": 12},
        ...
    ]
}
```

---

### `get_cached_link_analytics(link, days=30) → dict`

Wrapper com cache Redis em torno de `get_link_analytics()`.

**Chave de cache:** `analytics:{link_id}:{days}` (chave real no Redis: `urlshortener:analytics:{link_id}:{days}`)
**TTL:** 30 segundos

Retorna resultado em cache se existir; consulta o banco em caso de miss e popula o cache.

---

### `invalidate_analytics_cache(link_id)`

Remove o cache de analytics de um link. Deleta chaves de cache para `days` em `(7, 30, 90, 365)`.

Chamado automaticamente por `delete_short_url()`.

---

### `get_user_link_stats(user) → dict`

Retorna estatísticas agregadas para o dashboard do usuário.

```python
{
    "total_clicks": 124,
    "active_count": 5
}
```

- `total_clicks` — soma de `click_count` em todos os links do usuário.
- `active_count` — número de links ativos e não expirados.

---

### `slug_exists(slug) → bool`

Retorna `True` se existir algum `ShortURL` com o slug fornecido (ativo ou não).

---

## Tarefas Celery

**Módulo:** `apps/links/tasks.py`

### `log_click(link_id, ip_address, user_agent, referrer)`

Tarefa assíncrona disparada pela `RedirectView` após retornar o HTTP 302.

```python
from apps.links.tasks import log_click

# Disparada de forma assíncrona — não bloqueia o chamador
log_click.delay(str(link_id), ip_address, user_agent, referrer)
```

**Configuração:**
- Fila: `clicks`
- Máx. tentativas: 3
- Delay entre tentativas: 5 segundos
- Tenta novamente automaticamente em qualquer exceção.

---

### `deactivate_expired_links()`

Tarefa periódica que desativa links cujo `expires_at` já passou.

**Agendamento:** Configurado via django-celery-beat (registrado na migration `0002`).

**Comportamento:**
1. Consulta todos os links ativos com `expires_at < now()`.
2. Limpa o cache de redirect no Redis para cada slug.
3. Define `is_active=False` em lote.
4. Retorna a contagem de links desativados.

---

## Validadores

**Módulo:** `apps/links/validators.py`

### `validate_target_url(url)`

Valida que uma URL é segura para encurtar (proteção contra SSRF).

**Verificações (em ordem):**
1. Comprimento ≤ 2048 caracteres.
2. URL parseável com esquema e hostname não vazios.
3. Esquema deve ser `http` ou `https`.
4. Hostname não deve estar na lista de bloqueio: `localhost`, `127.0.0.1`, `::1`, `0.0.0.0`, `169.254.169.254`, `metadata.google.internal`.
5. Se o hostname for um IP literal: não deve estar em nenhuma faixa privada/reservada:
   - `10.0.0.0/8` (RFC1918 privada)
   - `172.16.0.0/12` (RFC1918 privada)
   - `192.168.0.0/16` (RFC1918 privada)
   - `127.0.0.0/8` (loopback)
   - `169.254.0.0/16` (link-local)
   - `100.64.0.0/10` (espaço de endereço compartilhado)
   - `fc00::/7` (IPv6 local único)
   - `fe80::/10` (IPv6 link-local)

**Lança:** `ValidationError` (400) com mensagem descritiva.

---

### `validate_custom_slug(slug) → str`

Valida um slug personalizado fornecido pelo usuário.

**Verificações:**
1. Comprimento: 2–50 caracteres.
2. Padrão: apenas caracteres alfanuméricos, hífens (`-`) e underscores (`_`).
3. Não deve estar entre as palavras reservadas: `admin`, `api`, `static`, `media`, `login`, `logout`, `register`, `dashboard`, `links`, `health`, `metrics`, `favicon`, `robots`, `sitemap`.

**Retorna:** O slug sem modificações.

**Lança:** `ValidationError` (400).
