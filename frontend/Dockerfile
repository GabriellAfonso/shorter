# ── Stage 1: build ────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install --prefer-offline

COPY . .

ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

ARG VITE_BASE_PATH=/shorter/
ENV VITE_BASE_PATH=${VITE_BASE_PATH}

RUN npm run build


# ── Stage 2: exportar dist ─────────────────────────────────────────────────
FROM alpine:3.20

COPY --from=builder /app/dist /dist

# Copia os arquivos buildados para o volume montado pelo compose
CMD ["sh", "-c", "cp -rp /dist/. /output/ && echo 'Frontend assets copied to /output'"]
