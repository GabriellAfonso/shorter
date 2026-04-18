# Análise de Portfolio — Shorter (URL Shortener)

Data da análise: 2026-04-07

---

## O que já está bem feito

O projeto já tem uma base sólida que poucos portfolios têm:

- Arquitetura limpa (services/selectors/views)
- SSRF protection, rate limiting com Redis, JWT com blacklist
- Async real com Celery + filas separadas
- Multi-stage Docker builds + compose de produção
- Documentação detalhada em português e README de qualidade
- Paginação, cache de redirects, slugs criptograficamente seguros

Isso já coloca o projeto acima da média. O problema é o que **falta** — e é exatamente isso que um revisor técnico vai procurar.

---

## Melhorias prioritárias

### 🔴 1. CI/CD com GitHub Actions

Atualmente não existe nenhum pipeline. Isso é a primeira coisa que um engenheiro olha no GitHub. Um workflow que roda `pytest`, `ruff`, `eslint` e build do Docker a cada push mostra maturidade de processo.

O mínimo que faz diferença:

```
.github/workflows/
├── ci.yml       # lint + test no PR
└── docker.yml   # build das imagens no merge pro main
```

Um badge de `tests passing` no README é sinal verde imediato.

---

### 🔴 2. Testes no frontend (Vitest + React Testing Library)

Zero testes de frontend é a maior fraqueza técnica do projeto. Não precisa ser 80% de coverage — testar os formulários de login/registro, o fluxo de criação de link e a renderização dos charts já mostra que você sabe testar React. Sem isso, parece que o frontend foi ignorado.

---

### 🔴 3. Linting e formatação no backend (ruff + mypy)

O frontend tem ESLint + Prettier + TypeScript strict. O backend não tem nenhum linter ou formatador configurado. Essa assimetria é perceptível. Adicionar `ruff` (rápido, substitui flake8+isort+black) e `mypy` com configuração básica fecha essa lacuna.

---

### 🟡 4. Completar os testes documentados em TESTS_NEEDED.md

O que falta já está mapeado — isso é um bom sinal. Completar esses 11 casos (redirect rate limiting, HealthCheck com falhas de serviço, edge cases de auth) fecha o ciclo e deixa a cobertura real em >80% nos caminhos críticos.

Casos pendentes documentados:
- Validação de settings de produção (vars obrigatórias ausentes)
- Edge cases de parsing do `CORS_ALLOWED_ORIGINS`
- Redirect view happy path + rate limiting
- `HealthCheckView` com falha de DB e/ou Redis
- Edge cases de `get_link_by_slug` (inativo, expirado, inexistente)
- Casos de erro de auth (email duplicado, senha errada)

---

### 🟡 5. Sentry para error tracking

Uma linha no `settings.py` e no `docker-compose`. Mostra que você pensa em produção além do happy path. Recrutador de empresa que usa Sentry já reconhece o setup imediatamente.

---

### 🟡 6. Headers de rate limit na API

Faltam `X-RateLimit-Limit`, `X-RateLimit-Remaining` e `Retry-After` nas respostas de throttling. É um detalhe de design de API que mostra que você conhece os padrões REST. Simples de adicionar via DRF custom throttle class.

---

### 🟢 7. QR Code por link

Feature pequena, visualmente impressionante na demo. Uma biblioteca como `qrcode` no backend ou `qrcode.react` no frontend gera o QR do link encurtado. Recrutadores não técnicos adoram ver isso na apresentação.

---

### 🟢 8. Busca e filtro no dashboard

A listagem atual não tem busca. Filtrar por slug, URL original ou data de criação é uma feature básica de UX que qualquer usuário esperaria. Mostra que você pensa na experiência real de uso.

---

## O que não vale a pena focar agora

Geo-location em analytics, dark mode, webhooks, API pública — são features bacanas mas não mudam a percepção de qualidade técnica do projeto. Foque primeiro nas lacunas de engenharia (CI, testes, tooling) antes de adicionar features novas.

---

## Tabela de prioridades

| Prioridade | Item | Por que importa ao recrutador |
|---|---|---|
| 🔴 Alta | GitHub Actions CI/CD | Visível no repositório, sinal imediato de profissionalismo |
| 🔴 Alta | Testes no frontend | Maior fraqueza técnica atual |
| 🔴 Alta | ruff + mypy no backend | Fecha assimetria com o frontend |
| 🟡 Média | Completar TESTS_NEEDED.md | Fecha o que já foi reconhecido como faltante |
| 🟡 Média | Sentry | Mostra mentalidade de produção |
| 🟡 Média | Rate limit headers | Detalhe de design de API |
| 🟢 Baixa | QR Code por link | Impacto visual na demo |
| 🟢 Baixa | Busca/filtro no dashboard | UX básica que falta |

---

## Scorecard atual

| Aspecto | Nota | Observação |
|---|---|---|
| Arquitetura | 8.5/10 | Padrões limpos, falta observabilidade |
| Segurança | 8/10 | SSRF e rate limiting sólidos, falta audit logging |
| Testes | 6/10 | Backend razoável, frontend zerado |
| Documentação | 9/10 | Excelente README e docs em PT |
| Frontend | 7.5/10 | Responsivo e tipado, sem testes |
| DevOps | 7/10 | Docker bem feito, sem CI/CD |
| Qualidade de código | 7.5/10 | Type hints e tratamento de erro ok, faltam linters |
| Performance | 8/10 | Cache e async funcionando, sem métricas |
| **Geral** | **7.5/10** | Base sólida, gaps de engenharia corrigíveis |
