# Testes

## Visão Geral

A suíte de testes usa **pytest** com **pytest-django** e **factory-boy**. Todos os testes rodam sem precisar de um Redis ativo — um cache em memória o substitui automaticamente.

**Versões dos pacotes:**

| Pacote | Versão |
|--------|--------|
| pytest | 9.0.2 |
| pytest-django | 4.12.0 |
| pytest-cov | 7.0.0 |
| factory-boy | 3.3.3 |
| Faker | 40.8.0 |
| freezegun | 1.5.5 |

---

## Executando os Testes

```bash
# A partir do diretório backend
cd backend

# Rodar todos os testes
pytest

# Rodar com relatório de cobertura
pytest --cov=apps --cov-report=html

# Rodar um arquivo específico
pytest apps/links/tests/unit/test_services.py

# Rodar um teste específico
pytest apps/links/tests/unit/test_services.py::TestCreateShortURL::test_creates_with_custom_slug

# Rodar apenas testes unitários (por marker)
pytest -m unit

# Rodar apenas testes de integração
pytest -m integration

# Rodar com saída verbosa
pytest -v
```

---

## Configuração (`pytest.ini`)

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marcar teste como lento
    unit: marcar teste como unitário
    integration: marcar teste como de integração
```

---

## Fixtures (`conftest.py`)

Fixtures raiz disponíveis para todos os testes:

### `use_locmem_cache` (autouse)

Substitui o cache Redis configurado pelo cache em memória do Django em cada teste. Garante que os testes sejam isolados e não precisem de uma instância Redis em execução.

```python
@pytest.fixture(autouse=True)
def use_locmem_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
```

### `api_client`

Uma instância de `APIClient` do Django REST Framework (não autenticado).

```python
def test_algo(api_client):
    response = api_client.get("/api/v1/health/")
    assert response.status_code == 200
```

### `user`

Uma instância de `User` gerada por factory (não autenticado no client).

```python
def test_algo(user):
    assert user.email is not None
```

### `auth_client`

Um `APIClient` pré-configurado com credenciais JWT para `user`.

```python
def test_algo(auth_client):
    response = auth_client.get("/api/v1/users/me/")
    assert response.status_code == 200
```

---

## Factories

### `UserFactory`

**Módulo:** `apps/accounts/tests/factories.py`

```python
from apps.accounts.tests.factories import UserFactory

user = UserFactory()                          # e-mail sequencial, senha padrão "testpass123"
user = UserFactory(email="alice@teste.com")   # e-mail específico
users = UserFactory.create_batch(5)           # 5 usuários
```

### `ShortURLFactory`

**Módulo:** `apps/links/tests/factories.py`

```python
from apps.links.tests.factories import ShortURLFactory, ExpiredShortURLFactory

link = ShortURLFactory()                      # link aleatório para um novo usuário
link = ShortURLFactory(owner=user)            # link para um usuário específico
link = ShortURLFactory(is_active=False)       # link inativo
link = ShortURLFactory(slug="meu-slug")       # slug específico

# Link já expirado (expires_at = 1 hora atrás)
link = ExpiredShortURLFactory(owner=user)
```

### `LinkClickFactory`

**Módulo:** `apps/links/tests/factories.py`

```python
from apps.links.tests.factories import LinkClickFactory

click = LinkClickFactory(link=link)
click = LinkClickFactory(link=link, device_type="mobile")
```

---

## Organização dos Testes

```
apps/
├── accounts/tests/
│   ├── factories.py
│   └── integration/
│       ├── test_auth.py          # POST /auth/register/, login, logout, refresh
│       └── test_users.py         # GET/PATCH /users/me/, change-password
│
└── links/tests/
    ├── factories.py
    ├── unit/
    │   ├── test_models.py        # Propriedades e comportamento de ShortURL/LinkClick
    │   ├── test_selectors.py     # Funções seletoras e comportamento do cache
    │   ├── test_services.py      # Funções de serviço e regras de negócio
    │   ├── test_validators.py    # Validação de URL e slug
    │   └── test_tasks.py         # Comportamento das tarefas Celery
    └── integration/
        └── test_views.py         # Testes completos de endpoints da API (CRUD + analytics + redirect)
```

---

## Exemplos de Testes

### Teste de integração (endpoint da API)

```python
import pytest

@pytest.mark.django_db
class TestCreateLink:
    def test_cria_url_curta(self, auth_client):
        payload = {"original_url": "https://exemplo.com"}
        response = auth_client.post("/api/v1/links/", payload)

        assert response.status_code == 201
        data = response.json()
        assert data["original_url"] == "https://exemplo.com"
        assert data["slug"] != ""

    def test_exige_autenticacao(self, api_client):
        response = api_client.post("/api/v1/links/", {"original_url": "https://exemplo.com"})
        assert response.status_code == 401
```

### Teste unitário (service)

```python
import pytest
from apps.links.services.link_service import create_short_url
from apps.accounts.tests.factories import UserFactory

@pytest.mark.django_db
class TestCreateShortURL:
    def test_cria_com_slug_aleatorio(self):
        user = UserFactory()
        link = create_short_url(original_url="https://exemplo.com", owner=user)

        assert link.pk is not None
        assert len(link.slug) == 8
        assert link.is_active is True

    def test_lanca_erro_quando_cota_excedida(self):
        from core.exceptions import QuotaExceeded
        from apps.links.tests.factories import ShortURLFactory

        user = UserFactory()
        ShortURLFactory.create_batch(30, owner=user)

        with pytest.raises(QuotaExceeded):
            create_short_url("https://exemplo.com", user)
```

### Testes com tempo congelado

Use `freezegun` para testar lógica de expiração:

```python
from freezegun import freeze_time
from datetime import datetime, timedelta, timezone

@pytest.mark.django_db
def test_expiracao_do_link():
    from apps.links.tests.factories import ShortURLFactory

    futuro = datetime.now(timezone.utc) + timedelta(hours=1)
    link = ShortURLFactory(expires_at=futuro)

    assert link.is_expired is False

    with freeze_time(futuro + timedelta(seconds=1)):
        link.refresh_from_db()
        assert link.is_expired is True
```

### Testando tarefas Celery de forma síncrona

```python
@pytest.mark.django_db
def test_tarefa_log_click():
    from apps.links.tasks import log_click
    from apps.links.tests.factories import ShortURLFactory

    link = ShortURLFactory()
    # Chamar diretamente (não via .delay()) para executar de forma síncrona nos testes
    log_click(str(link.id), "1.2.3.4", "Mozilla/5.0", "")

    link.refresh_from_db()
    assert link.click_count == 1
```

---

## Cobertura

Meta: **> 80% de cobertura nos caminhos críticos** (services, selectors, validators, views).

```bash
pytest --cov=apps --cov-report=html --cov-report=term-missing
```

O relatório de cobertura é gerado em `htmlcov/index.html`.
