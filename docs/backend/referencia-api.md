# Referência da API

URL base: `http://localhost:8000/api/v1`

Todas as respostas usam `application/json`. Endpoints autenticados exigem o header `Authorization: Bearer <access_token>`.

## Formato de Resposta de Erro

Todos os erros seguem um envelope consistente:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Descrição legível por humanos.",
    "details": {
      "nome_do_campo": ["Mensagem de erro."]
    }
  }
}
```

Códigos de erro comuns:

| Código | Status HTTP | Descrição |
|--------|------------|-----------|
| `validation_error` | 400 | Entrada inválida |
| `not_authenticated` | 401 | Token ausente ou expirado |
| `permission_denied` | 403 | Autenticado mas sem autorização |
| `not_found` | 404 | Recurso não encontrado |
| `conflict` | 409 | Recurso já existe |
| `rate_limit_exceeded` | 429 | Muitas requisições |
| `quota_exceeded` | 422 | Cota do usuário atingida |
| `service_unavailable` | 503 | Dependência (DB/Redis) indisponível |

---

## Autenticação

### POST /auth/register/

Cria uma nova conta de usuário. Retorna tokens JWT.

**Rate limit:** 10 requisições/min por IP

**Corpo da requisição:**

```json
{
  "email": "usuario@exemplo.com",
  "password": "senha123",
  "first_name": "Alice",
  "last_name": "Silva"
}
```

| Campo | Tipo | Obrigatório | Restrições |
|-------|------|-------------|------------|
| `email` | string | Sim | E-mail válido, único (case-insensitive) |
| `password` | string | Sim | 6–128 caracteres |
| `first_name` | string | Não | Máx. 50 caracteres |
| `last_name` | string | Não | Máx. 50 caracteres |

**Resposta 201:**

```json
{
  "user": {
    "id": 1,
    "email": "usuario@exemplo.com",
    "first_name": "Alice",
    "last_name": "Silva",
    "full_name": "Alice Silva",
    "bio": "",
    "avatar_url": null,
    "links_count": 0,
    "date_joined": "2025-01-01T00:00:00Z",
    "created_at": "2025-01-01T00:00:00Z"
  },
  "tokens": {
    "access": "<jwt-access-token>",
    "refresh": "<jwt-refresh-token>"
  }
}
```

---

### POST /auth/login/

Autentica e recebe tokens JWT.

**Rate limit:** 10 requisições/min por IP

**Corpo da requisição:**

```json
{
  "email": "usuario@exemplo.com",
  "password": "senha123"
}
```

**Resposta 200:**

```json
{
  "access": "<jwt-access-token>",
  "refresh": "<jwt-refresh-token>",
  "user": {
    "id": 1,
    "email": "usuario@exemplo.com",
    "first_name": "Alice",
    "last_name": "Silva",
    "full_name": "Alice Silva"
  }
}
```

> **Nota:** O objeto `user` no login contém apenas os campos básicos de identidade (`id`, `email`, `first_name`, `last_name`, `full_name`). Para o perfil completo (bio, avatar, links_count, etc.), use `GET /users/me/`.
> O campo `full_name` no login é gerado por `get_full_name()` do Django (retorna `""` se ambos os nomes estiverem em branco), enquanto em `GET /users/me/` ele vem da property do model (retorna o `email` como fallback quando ambos os nomes estão em branco).

**Resposta 401:** Credenciais inválidas.

---

### POST /auth/logout/

Coloca o refresh token na blacklist, invalidando a sessão. O access token expira naturalmente (15 minutos).

**Autenticação:** Obrigatória

**Corpo da requisição:**

```json
{
  "refresh": "<jwt-refresh-token>"
}
```

**Resposta 200:**

```json
{
  "detail": "Successfully logged out."
}
```

---

### POST /auth/token/refresh/

Troca um refresh token por um novo access token.

**Corpo da requisição:**

```json
{
  "refresh": "<jwt-refresh-token>"
}
```

**Resposta 200:**

```json
{
  "access": "<novo-jwt-access-token>",
  "refresh": "<novo-jwt-refresh-token>"
}
```

> **Nota:** Os refresh tokens rodam a cada uso. O token antigo é adicionado à blacklist.

---

## Perfil do Usuário

### GET /users/me/

Retorna o perfil do usuário autenticado.

**Autenticação:** Obrigatória

**Resposta 200:**

```json
{
  "id": 1,
  "email": "usuario@exemplo.com",
  "first_name": "Alice",
  "last_name": "Silva",
  "full_name": "Alice Silva",
  "bio": "Desenvolvedora de software",
  "avatar_url": "https://exemplo.com/avatar.jpg",
  "links_count": 5,
  "date_joined": "2025-01-01T00:00:00Z",
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

### PATCH /users/me/update/

Atualiza campos do perfil. Todos os campos são opcionais.

**Autenticação:** Obrigatória

**Corpo da requisição:**

```json
{
  "first_name": "Alice",
  "last_name": "Silva",
  "bio": "Bio atualizada",
  "avatar_url": "https://exemplo.com/novo-avatar.jpg"
}
```

| Campo | Tipo | Restrições |
|-------|------|------------|
| `first_name` | string | Máx. 50 caracteres |
| `last_name` | string | Máx. 50 caracteres |
| `bio` | string | Máx. 500 caracteres |
| `avatar_url` | string (URL) | Deve ser uma URL válida |

**Resposta 200:** Perfil atualizado (mesmo esquema do GET /users/me/).

---

### POST /users/me/change-password/

Altera a senha do usuário autenticado. Todos os refresh tokens existentes são adicionados à blacklist.

**Autenticação:** Obrigatória

**Corpo da requisição:**

```json
{
  "old_password": "senhaatual",
  "new_password": "novasenha123",
  "confirm_password": "novasenha123"
}
```

| Campo | Tipo | Restrições |
|-------|------|------------|
| `old_password` | string | Deve corresponder à senha atual |
| `new_password` | string | 6–128 caracteres |
| `confirm_password` | string | Deve ser igual a `new_password` |

**Resposta 200:**

```json
{
  "detail": "Password updated successfully."
}
```

---

## Links

### GET /links/

Lista todas as URLs curtas do usuário autenticado. Paginado.

**Autenticação:** Obrigatória

**Parâmetros de query:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `is_active` | booleano | `true` | Filtrar por status ativo (`true` ou `false`); quando ausente, retorna apenas links ativos |
| `page` | inteiro | 1 | Número da página |
| `page_size` | inteiro | 20 | Resultados por página (máx. 100) |

**Resposta 200:**

```json
{
  "pagination": {
    "count": 42,
    "next": "http://localhost:8000/api/v1/links/?page=2",
    "previous": null,
    "total_pages": 3,
    "current_page": 1
  },
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "original_url": "https://exemplo.com/caminho/muito/longo",
      "slug": "abc12345",
      "title": "exemplo.com",
      "short_url": "http://localhost:8000/s/abc12345",
      "owner_email": "usuario@exemplo.com",
      "is_active": true,
      "is_expired": false,
      "click_count": 17,
      "created_at": "2025-01-01T00:00:00Z",
      "expires_at": null
    }
  ],
  "stats": {
    "total_clicks": 124,
    "active_count": 5
  }
}
```

---

### POST /links/

Cria uma nova URL curta.

**Autenticação:** Obrigatória
**Rate limit:** 20 requisições/min por usuário
**Cota:** Máx. 30 links ativos por usuário

**Corpo da requisição:**

```json
{
  "original_url": "https://exemplo.com/caminho/muito/longo",
  "slug": "meu-link",
  "title": "Meu Link",
  "expires_at": "2026-01-01T00:00:00Z"
}
```

| Campo | Tipo | Obrigatório | Restrições |
|-------|------|-------------|------------|
| `original_url` | string | Sim | URL HTTP/HTTPS válida, máx. 2048 chars, segura contra SSRF |
| `slug` | string | Não | 2–50 chars, alfanumérico/hífen/underscore, não reservado |
| `title` | string | Não | Máx. 200 caracteres |
| `expires_at` | datetime (ISO 8601) | Não | Deve ser no futuro |

**Resposta 201:** Objeto da URL curta (mesmo esquema dos itens da listagem).

**Resposta 400:** Slug personalizado já está em uso (retornado como `ValidationError` no campo `slug`).

**Resposta 422:** Cota de links ativos excedida (máx. 30).

**Resposta 400:** URL falhou na validação SSRF ou formato do slug inválido.

---

### GET /links/{id}/

Retorna os detalhes de uma única URL curta.

**Autenticação:** Obrigatória (deve ser o dono)

**Parâmetro de caminho:** `id` — UUID da URL curta.

**Resposta 200:** Objeto da URL curta (mesmo esquema da listagem).

**Resposta 404:** Não encontrado.

**Resposta 403:** Não é o dono.

---

### DELETE /links/{id}/

Soft-delete de uma URL curta. O slug fica imediatamente indisponível para redirects. O registro é mantido no banco de dados com `is_active=false`.

**Autenticação:** Obrigatória (deve ser o dono)

**Resposta 204:** Sem conteúdo.

**Resposta 404:** Não encontrado.

---

### GET /links/{id}/analytics/

Retorna analytics agregados de uma URL curta.

**Autenticação:** Obrigatória (deve ser o dono)
**Rate limit:** 60 requisições/min por usuário
**Cache:** Resultados ficam em cache no Redis por 30 segundos.

**Parâmetros de query:**

| Parâmetro | Tipo | Padrão | Restrições |
|-----------|------|--------|------------|
| `days` | inteiro | 30 | 1–365 |

**Resposta 200:**

```json
{
  "total_clicks": 142,
  "clicks_in_period": 38,
  "period_days": 30,
  "daily_clicks": [
    { "date": "2025-01-01", "count": 5 },
    { "date": "2025-01-02", "count": 3 }
  ],
  "by_device": [
    { "device_type": "desktop", "count": 25 },
    { "device_type": "mobile", "count": 13 }
  ],
  "top_referrers": [
    { "referrer": "https://twitter.com", "count": 12 },
    { "referrer": "https://google.com", "count": 8 }
  ]
}
```

---

## Redirects

### GET /s/{slug}/

Redireciona para a URL original. Esta é uma view Django pura (sem DRF), otimizada para velocidade.

**Autenticação:** Não necessária
**Rate limit:** 100 requisições/min por IP (configurável via `REDIRECT_RATE_LIMIT` em `base.py`; o fallback interno da view é 200 se a setting estiver ausente)

**Parâmetro de caminho:** `slug` — O slug da URL curta.

**Resposta 302:** Header `Location` aponta para a URL original. Sem corpo.

**Resposta 404:** Slug não encontrado, link inativo ou expirado.

**Resposta 429:** Rate limit excedido.

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: text/html
```

> O clique é registrado de forma assíncrona via tarefa Celery — o redirect é retornado imediatamente, sem aguardar o armazenamento do clique.

---

## Health Check

### GET /api/v1/health/

Retorna o status de saúde dos serviços do backend.

**Autenticação:** Não necessária

**Resposta 200 (saudável):**

```json
{
  "status": "ok",
  "checks": {
    "db": { "status": "ok", "latency_ms": 2 },
    "redis": { "status": "ok", "latency_ms": 1 }
  }
}
```

**Resposta 503 (degradado):**

```json
{
  "status": "degraded",
  "checks": {
    "db": { "status": "ok", "latency_ms": 2 },
    "redis": { "status": "error", "latency_ms": null }
  }
}
```

> Usado pelo Docker HEALTHCHECK e load balancers. Intencionalmente aberto a acesso anônimo; restrinja por IP no nível do nginx em produção.

---

## Paginação

Todos os endpoints de listagem retornam respostas paginadas com o seguinte envelope:

```json
{
  "pagination": {
    "count": 100,
    "next": "http://localhost:8000/api/v1/links/?page=2",
    "previous": null,
    "total_pages": 5,
    "current_page": 1
  },
  "results": [...]
}
```

Tamanho padrão de página: **20**. Configurável via `?page_size=N` (máx.: 100).

---

## Ciclo de Vida dos Tokens

```
POST /auth/login/
    └── retorna: access (15 min) + refresh (7 dias)

Cada requisição autenticada:
    └── Authorization: Bearer <access>

Quando o access expira:
    └── POST /auth/token/refresh/ { "refresh": "..." }
        └── retorna: novo access + novo refresh (refresh antigo na blacklist)

POST /auth/logout/ { "refresh": "..." }
    └── refresh na blacklist imediatamente; access expira naturalmente
```
