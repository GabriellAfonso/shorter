# Modelos de Dados

## User (Usuário)

**App:** `apps.accounts`
**Tabela:** `users`
**Manager customizado:** `EmailUserManager`

A aplicação usa um model de usuário completamente customizado. O campo de e-mail substitui o `username` padrão do Django como identificador principal.

| Campo | Tipo | Observações |
|-------|------|-------------|
| `id` | BigAutoField (PK) | Inteiro 64-bit auto-incremental (via `DEFAULT_AUTO_FIELD`) |
| `email` | EmailField | Único, case-insensitive, usado como `USERNAME_FIELD` |
| `first_name` | CharField (150) | Opcional; a API limita a 50 chars via serializer |
| `last_name` | CharField (150) | Opcional; a API limita a 50 chars via serializer |
| `bio` | TextField | Bio opcional do perfil; sem limite no model — a API limita a 500 chars via serializer |
| `avatar_url` | URLField | URL opcional da foto de perfil |
| `is_active` | BooleanField | Padrão Django; `True` para contas ativas |
| `is_staff` | BooleanField | Padrão Django; dá acesso ao admin |
| `date_joined` | DateTimeField | Definido pelo Django na criação |
| `created_at` | DateTimeField | Auto-definido na criação |
| `updated_at` | DateTimeField | Auto-definido a cada save |

**Propriedades:**

- `full_name` — Retorna a concatenação de `first_name` e `last_name` (com strip); cai para o `email` apenas se o resultado for vazio (i.e., ambos os campos em branco).

**Observações:**
- `USERNAME_FIELD = "email"` — e-mail é usado para autenticação.
- `REQUIRED_FIELDS = []` — sem campos extras obrigatórios para `createsuperuser`.
- O campo `username` está definido como `None` (completamente removido).

---

## ShortURL (URL Curta)

**App:** `apps.links`
**Tabela:** `short_urls`
**Módulo:** `apps/links/models/short_url.py`

A entidade principal que representa uma URL encurtada.

| Campo | Tipo | Observações |
|-------|------|-------------|
| `id` | UUIDField (PK) | UUID4 gerado automaticamente |
| `original_url` | URLField (2048) | A URL completa de destino |
| `slug` | CharField (50) | Identificador único usado na URL curta; indexado |
| `title` | CharField (200) | Título opcional de exibição; padrão é o domínio inferido |
| `owner` | FK → User | `CASCADE` ao deletar; `related_name="short_urls"` |
| `is_active` | BooleanField | `True` por padrão; definido como `False` no soft-delete; indexado |
| `created_at` | DateTimeField | Auto-definido na criação |
| `updated_at` | DateTimeField | Auto-definido a cada save |
| `expires_at` | DateTimeField | Opcional; link fica inativo após este timestamp |
| `click_count` | PositiveIntegerField | Contador desnormalizado; incrementado atomicamente via `F()` a cada clique |

**Propriedades:**

- `is_expired` — `True` se `expires_at` está definido e está no passado.
- `short_url` — String completa da URL curta, ex: `http://localhost:8000/s/abc12345`.

**Índices:**

| Índice | Campos | Finalidade |
|--------|--------|-----------|
| Único | `slug` | Consultas rápidas por slug |
| Composto | `owner`, `-created_at` (desc) | Paginação da lista de links do usuário |
| Simples | `is_active` | Filtragem de links ativos |

**Ordenação:** `-created_at` (mais recente primeiro)

**Soft delete:** Links nunca são deletados definitivamente. Definir `is_active=False` os torna imediatamente indisponíveis para redirects e os exclui da contagem de cota.

---

## LinkClick (Clique no Link)

**App:** `apps.links`
**Tabela:** `link_clicks`
**Módulo:** `apps/links/models/link_click.py`

Um evento de analytics append-only registrado a cada redirect. Nunca é atualizado após a criação.

| Campo | Tipo | Observações |
|-------|------|-------------|
| `id` | BigAutoField (PK) | Inteiro 64-bit auto-incremental (via `DEFAULT_AUTO_FIELD`) |
| `link` | FK → ShortURL | `CASCADE` ao deletar; `related_name="clicks"` |
| `timestamp` | DateTimeField | Auto-definido na criação; indexado |
| `ip_address` | CharField (64) | SHA-256 do IP real truncado em 32 hex chars (preservação de privacidade) |
| `user_agent` | TextField | String User-Agent bruta; truncada em 500 chars pelo service antes do armazenamento |
| `referrer` | URLField (2048) | Header HTTP Referer; em branco se ausente |
| `country` | CharField (100) | Código do país (atualmente em branco — reservado para GeoIP futuro) |
| `browser` | CharField (100) | Extraído do `user_agent` (ex.: `Chrome`) |
| `os` | CharField (100) | Extraído do `user_agent` (ex.: `Windows`) |
| `device_type` | CharField (50) | Um de: `desktop`, `mobile`, `tablet`, `bot` |

**Índices:**

| Índice | Campos | Finalidade |
|--------|--------|-----------|
| Composto | `link`, `timestamp` | Consultas de analytics por intervalo de tempo |
| Composto | `link`, `device_type` | Agregação por tipo de dispositivo |

**Ordenação:** `-timestamp` (mais recente primeiro)

**Privacidade:** O IP real nunca é armazenado. Apenas os primeiros 32 caracteres hexadecimais do SHA-256 são persistidos (hash unidirecional), tornando usuários individuais não identificáveis, enquanto ainda permite estimativas de visitantes únicos.

---

## Relacionamento entre Entidades

```
User ─────────────┐
                  │ 1:N (owner)
                  ▼
              ShortURL ─────────────┐
                                    │ 1:N (link)
                                    ▼
                                LinkClick
```

---

## Migrations

As migrations são gerenciadas pelo Django. Arquivos principais:

| Arquivo | Descrição |
|---------|-----------|
| `apps/accounts/migrations/0001_initial.py` | Cria a tabela `users` |
| `apps/links/migrations/0001_initial.py` | Cria as tabelas `short_urls` e `link_clicks` |
| `apps/links/migrations/0002_periodic_task_deactivate_expired_links.py` | Registra a tarefa periódica do Celery Beat para expiração de links |

Para rodar as migrations:

```bash
python manage.py migrate
```
