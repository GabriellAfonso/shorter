# Segurança

Este documento descreve as medidas de segurança implementadas no backend.

---

## Autenticação

**Mecanismo:** JWT (JSON Web Tokens) via `djangorestframework-simplejwt`.

| Token | Tempo de vida | Observações |
|-------|--------------|-------------|
| Access token | 15 minutos | Curta duração; enviado no header `Authorization: Bearer` |
| Refresh token | 7 dias | Longa duração; usado apenas para obter novos access tokens |

**Rotação de tokens:** Cada chamada a `/auth/token/refresh/` emite um novo refresh token e coloca o antigo na blacklist.

**Logout:** Colocar o refresh token na blacklist via `/auth/logout/` invalida a sessão. O access token expira naturalmente em até 15 minutos.

**Troca de senha:** Chamar `/users/me/change-password/` coloca **todos** os tokens existentes do usuário na blacklist, forçando reautenticação em todos os dispositivos.

**Permissão padrão:** `IsAuthenticated` — todos os endpoints exigem um access token válido, salvo exceções explícitas.

---

## Proteção contra SSRF

Todas as URLs fornecidas pelo usuário são validadas por `validate_target_url()` antes de serem armazenadas ou encurtadas.

**Esquemas bloqueados:** qualquer coisa que não seja `http` ou `https`.

**Hostnames bloqueados (correspondência exata):**
- `localhost`
- `127.0.0.1`
- `::1`
- `0.0.0.0`
- `169.254.169.254` (endpoint de metadados AWS/GCP)
- `metadata.google.internal`

**Faixas de IP bloqueadas (quando o hostname é um IP literal):**

| Faixa | Descrição |
|-------|-----------|
| `10.0.0.0/8` | RFC1918 privada |
| `172.16.0.0/12` | RFC1918 privada |
| `192.168.0.0/16` | RFC1918 privada |
| `127.0.0.0/8` | Loopback |
| `169.254.0.0/16` | Link-local (APIPA) |
| `100.64.0.0/10` | Espaço de endereço compartilhado (RFC6598) |
| `fc00::/7` | IPv6 local único |
| `fe80::/10` | IPv6 link-local |
| `::1/128` | IPv6 loopback |

**Observação:** Ataques de DNS rebinding (onde um hostname resolve para um IP privado no momento da requisição) são uma limitação conhecida da validação apenas por hostname. Para ambientes de produção com requisitos mais rígidos, considere realizar a resolução DNS no momento da validação e verificar o IP resolvido.

---

## Rate Limiting

Múltiplas camadas independentes de rate limiting protegem diferentes partes do sistema.

### Throttling DRF (endpoints da API)

| Escopo | Classe | Limite | Aplicado a |
|--------|-------|--------|-----------|
| Padrão (anônimo) | `AnonRateThrottle` | 60/min por IP | Todas as requisições não autenticadas |
| Padrão (autenticado) | `UserRateThrottle` | 300/min por usuário | Todas as requisições autenticadas |
| `auth` | `AuthRateThrottle` | 10/min por IP | Register + Login |
| `link_create` | `LinkCreateThrottle` | 20/min por usuário | POST /links/ |
| `link_analytics` | `LinkAnalyticsThrottle` | 60/min por usuário | GET /links/{id}/analytics/ |

Em desenvolvimento, os limites são relaxados para 1000/min (anônimo) e 5000/min (autenticado).

### Janela Deslizante Redis (endpoint de redirect)

A view de redirect (`/s/<slug>/`) usa um pipeline Redis customizado para rate limiting de alta performance sem overhead do DRF:

- **Limite:** 100 requisições/min por IP (configurável via setting `REDIRECT_RATE_LIMIT`)
- **Algoritmo:** INCR + EXPIRE em uma chave por IP; a chave expira após 60 segundos
- **Resposta ao exceder:** HTTP 429 com header `Retry-After: 60`

---

## Validação de Entrada

### Validação de URL
Veja [Proteção contra SSRF](#proteção-contra-ssrf) acima. Verificações adicionais:
- Comprimento máximo: 2048 caracteres.
- Deve ser uma URL parseável com esquema e hostname.

### Validação de Slug
Slugs personalizados são validados antes do armazenamento:
- Comprimento: 2–50 caracteres.
- Caracteres permitidos: `[a-zA-Z0-9\-_]` apenas.
- Palavras reservadas são bloqueadas (admin, api, login, dashboard, etc.).

### Validação de Senha
- Comprimento mínimo: 6 caracteres.
- Comprimento máximo: 128 caracteres.
- Os validadores embutidos do Django também são aplicados (configurável nos settings).

---

## Privacidade de Endereço IP

O IP real do cliente **nunca é armazenado** no banco de dados.

**Fluxo:**
1. `get_client_ip(request)` extrai o IP real do header `X-Forwarded-For` ou de `REMOTE_ADDR`.
2. `hash_ip(ip)` aplica SHA-256 e trunca para os primeiros **32 caracteres** hexadecimais (`hexdigest()[:32]`).
3. Apenas o hash truncado é armazenado em `LinkClick.ip_address` (campo `CharField(64)`).

Isso atende aos requisitos de LGPD/GDPR para analytics (dados agregados, não identificáveis), enquanto ainda permite estimativas de visitantes únicos dentro de uma janela de sessão curta (mesmo hash de IP = mesmo visitante estimado).

---

## Permissões em Nível de Objeto

A classe de permissão `IsOwner` (`core/permissions.py`) é aplicada a todos os endpoints que operam sobre um link específico:

- `GET /links/{id}/`
- `DELETE /links/{id}/`
- `GET /links/{id}/analytics/`

**Verificação:** `request.user == obj.owner`

Qualquer usuário com token válido mas que não seja dono do recurso específico recebe HTTP 403.

---

## CORS

O Cross-Origin Resource Sharing é configurado via `django-cors-headers`.

| Ambiente | Origens permitidas |
|----------|-------------------|
| Desenvolvimento | `http://localhost:5173` (servidor Vite) |
| Produção | Configurado via variável de ambiente `CORS_ALLOWED_ORIGINS` |

---

## Headers de Segurança

O middleware de segurança embutido do Django está ativo:
- `SecurityMiddleware` — redirect HTTPS, HSTS, X-Content-Type-Options, X-Frame-Options.
- `XFrameOptionsMiddleware` — `DENY` por padrão.

Em produção, as seguintes configurações são adicionalmente aplicadas:
- `SECURE_SSL_REDIRECT = False` — o nginx já faz o redirect HTTP→HTTPS; manter `True` causaria double-redirect
- `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` — Django detecta HTTPS via header do proxy
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- `SECURE_HSTS_SECONDS` configurado.

---

## Segurança do Admin

O Django admin está montado em `/core/` (caminho não padrão) para reduzir a exposição a scanners automatizados.

**Recomendação para produção (veja também `CLAUDE.md`):**
```nginx
location /core/ {
    allow <seu-ip>;
    deny all;
    proxy_pass http://backend;
}
```

Opcional: `django-axes` para proteção contra força bruta (bloqueia IPs após N tentativas de login com falha).

---

## Cota de Usuário

Cada usuário autenticado está limitado a **30 URLs curtas ativas**. Tentar criar a 31ª retorna HTTP 422 (`quota_exceeded`).

Isso previne abuso do plano gratuito e limita o crescimento do banco de dados por usuário.

---

## Trade-offs Conhecidos

| Trade-off | Motivo |
|-----------|--------|
| `HealthCheckView` aberto a acesso anônimo | Necessário para Docker HEALTHCHECK e load balancers; restrinja por IP no nginx em produção |
| Sem resolução DNS no validador SSRF | Verificação apenas por hostname; DNS rebinding é um risco residual, aceitável para o deploy inicial |
| Cache de analytics cobre apenas 7/30/90/365 dias | A UI expõe apenas esses intervalos fixos; chamadas diretas à API com valores não padrão recebem cache com no máximo 5 min de atraso |
