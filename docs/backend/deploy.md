# Deploy

## Desenvolvimento (Docker Compose)

A forma mais fácil de rodar a stack completa localmente:

```bash
# A partir da raiz do repositório
docker compose up
```

Serviços iniciados:
- `backend` — Django + Gunicorn na porta 8000
- `frontend` — Servidor de desenvolvimento Vite na porta 5173
- `db` — PostgreSQL
- `redis` — Redis
- `celery` — Worker Celery (fila clicks)
- `celery-beat` — Agendador Celery Beat (tarefas periódicas)

### Targets úteis do Makefile

```bash
make up          # Iniciar todos os serviços
make down        # Parar todos os serviços
make logs        # Ver logs de todos os serviços
make shell       # Shell do Django
make test        # Rodar testes do backend
make migrate     # Rodar migrations
make seed        # Popular dados de demonstração
make prod-up     # Iniciar stack de produção
```

---

## Stack de Produção

### Serviços Necessários

| Serviço | Provedor recomendado |
|---------|---------------------|
| Backend Django | Heroku, Fly.io, Railway, AWS ECS |
| PostgreSQL | Supabase, AWS RDS, Neon |
| Redis | Upstash, Redis Cloud, AWS ElastiCache |
| Frontend (React/Vite) | Vercel, Netlify, Cloudflare Pages |
| Arquivos estáticos | WhiteNoise (embutido) ou S3 + CloudFront |

### Variáveis de Ambiente (Produção)

Configure essas variáveis no painel de secrets/environment da sua plataforma de hospedagem:

```env
SECRET_KEY=<string-aleatoria-longa>
DEBUG=False
ALLOWED_HOSTS=api.shorter.exemplo.com
DATABASE_URL=postgres://usuario:senha@host:5432/shorter
REDIS_URL=redis://usuario:senha@host:6379/0
CORS_ALLOWED_ORIGINS=https://shorter.exemplo.com
SHORT_URL_BASE_DOMAIN=https://shorter.exemplo.com
DJANGO_SETTINGS_MODULE=config.settings.production
```

### Executando o Backend

```bash
# Aplicar migrations
python manage.py migrate

# Coletar arquivos estáticos (servidos pelo WhiteNoise)
python manage.py collectstatic --no-input

# Iniciar Gunicorn (WSGI)
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Ou Uvicorn (ASGI, para suporte assíncrono)
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

### Executando o Celery

```bash
# Worker (processa a fila de clicks)
celery -A config.celery worker -Q clicks --loglevel=info

# Agendador Beat (dispara tarefas periódicas)
celery -A config.celery beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## Build Docker para Produção

O Dockerfile do backend usa um build multi-stage:

1. **Stage builder** — instala as wheels Python.
2. **Stage runtime** — imagem slim, copia as wheels pré-compiladas.

```bash
# Construir a imagem de produção
docker build -t shorter-backend ./backend

# Executar
docker run -p 8000:8000 \
  -e SECRET_KEY=... \
  -e DATABASE_URL=... \
  -e REDIS_URL=... \
  shorter-backend
```

O `docker-compose.prod.yml` de produção adiciona um proxy nginx reverso na frente do backend e do frontend.

---

## Configuração do Nginx (Produção)

O serviço nginx (`docker/nginx/nginx.conf`) gerencia:
- Terminação TLS (configure certificados SSL).
- Proxy reverso para o backend (`http://backend:8000`).
- Servir os arquivos estáticos do React SPA.
- Headers de segurança.

### Restrições de endpoints recomendadas

```nginx
# Restringir admin apenas a IPs confiáveis
location /core/ {
    allow <seu-ip>;
    deny all;
    proxy_pass http://backend;
}

# Restringir health check à rede interna
location /api/v1/health/ {
    allow 127.0.0.1;
    allow 10.0.0.0/8;
    deny all;
    proxy_pass http://backend;
}
```

---

## Health Check

O Docker HEALTHCHECK consulta `GET /api/v1/health/` a cada 30 segundos.

O endpoint retorna:
- **200 OK** — banco de dados e Redis acessíveis.
- **503 Service Unavailable** — uma ou ambas as dependências estão fora do ar.

```json
{
  "status": "ok",
  "checks": {
    "db": { "status": "ok", "latency_ms": 2 },
    "redis": { "status": "ok", "latency_ms": 1 }
  }
}
```

---

## Migrations em Produção

Sempre execute as migrations antes de fazer deploy do novo código:

```bash
python manage.py migrate --no-input
```

Para deploys sem downtime, execute as migrations em um passo de pré-deploy, antes que o novo container da aplicação seja iniciado.

---

## Celery Beat — Tarefas Periódicas

A tarefa `deactivate_expired_links` é registrada via migration `0002`. Após rodar as migrations, a tarefa é automaticamente cadastrada na tabela `django_celery_beat_periodictask` e será processada pelo agendador Beat.

Nenhuma configuração manual é necessária após `python manage.py migrate`.

---

## Considerações de Escalabilidade

| Preocupação | Abordagem |
|-------------|-----------|
| Alto throughput de redirects | Cache Redis garante que a maioria dos redirects nunca acesse o DB |
| Latência no registro de cliques | Tarefa Celery assíncrona — redirect retorna antes da escrita do clique |
| Múltiplas instâncias do backend | API sem estado; compartilham o mesmo Redis e PostgreSQL |
| Escalabilidade de sessão | Baseado em JWT — sem estado de sessão no servidor |
| Expiração de links | Tarefa Celery periódica (não em tempo de requisição) — links expirados são desativados em lote |

### Configuração inicial recomendada

| Recurso | Tamanho |
|---------|---------|
| Instâncias do backend | 2 (para redundância) |
| Workers Gunicorn | `(2 × núcleos de CPU) + 1` |
| Workers Celery | 2 (fila clicks) |
| PostgreSQL | 1 primário (+ réplica de leitura se necessário) |
| Redis | 1 instância (Upstash Hobby para pequena escala) |

---

## Rollback

A aplicação usa soft-deletes e analytics append-only — sem operações destrutivas no banco de dados em operação normal. Reverter um deploy é seguro desde que as migrations sejam retrocompatíveis (adicionar colunas com defaults, nunca remover colunas no mesmo deploy).
