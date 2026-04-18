# Documentação do Backend — Shorter URL Shortener

Bem-vindo à documentação do backend do **Shorter**, uma plataforma de encurtamento de URLs escalável construída com Django.

## Índice

| Arquivo | Descrição |
|---------|-----------|
| [arquitetura.md](arquitetura.md) | Design do sistema, estrutura de pastas e padrões principais |
| [referencia-api.md](referencia-api.md) | Referência completa da API REST com exemplos de request/response |
| [modelos.md](modelos.md) | Modelos do banco de dados e descrição dos campos |
| [servicos-seletores.md](servicos-seletores.md) | Camadas de lógica de negócio e consultas |
| [seguranca.md](seguranca.md) | Medidas de segurança: SSRF, rate limiting, autenticação, privacidade |
| [configuracao.md](configuracao.md) | Referência de settings e variáveis de ambiente |
| [testes.md](testes.md) | Configuração de testes, fixtures e convenções |
| [deploy.md](deploy.md) | Guia de deploy e notas de produção |

## Início Rápido (Desenvolvimento)

### Pré-requisitos

- Python 3.12+
- PostgreSQL (ou SQLite para desenvolvimento local)
- Redis

### Configuração

```bash
# Instalar dependências
pip install -r requirements.txt -r requirements-dev.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env com seus valores

# Aplicar migrations
python manage.py migrate

# Popular dados de demonstração
python manage.py seed_data

# Iniciar servidor de desenvolvimento
python manage.py runserver
```

### Usuários de Demonstração (após seed)

| E-mail | Senha | Papel |
|--------|-------|-------|
| admin@demo.com | admin1234 | Superusuário |
| user@demo.com | demo1234 | Usuário comum |

### Executar com Docker

```bash
# A partir da raiz do repositório
docker compose up
```

O backend estará disponível em `http://localhost:8000`.

## Stack Tecnológica

| Componente | Tecnologia |
|-----------|-----------|
| Framework | Django 6.0.3 |
| API | Django REST Framework 3.16.1 |
| Autenticação | SimpleJWT (tokens JWT de acesso + refresh) |
| Banco de dados | PostgreSQL (SQLite em desenvolvimento) |
| Cache / Broker | Redis |
| Tarefas assíncronas | Celery + django-celery-beat |
| Documentação da API | drf-spectacular (OpenAPI 3) |
| Arquivos estáticos | WhiteNoise |

## Documentação Interativa da API

Com o servidor em execução:

- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/api/schema/redoc/`
- Schema OpenAPI (JSON): `http://localhost:8000/api/schema/`
