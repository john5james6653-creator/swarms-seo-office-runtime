# Claw3D Studio — Railway-ready build.
# Upstream's published image runs Node 20, but camera-controls requires Node >= 22,
# which makes next.config.ts fail to transpile at runtime. This image pins Node 22
# and clones the upstream source at build time.
FROM node:22-slim AS deps
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/iamlukethedev/Claw3D.git /app
WORKDIR /app
RUN npm ci --ignore-scripts --omit=dev

FROM node:22-slim AS builder
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/iamlukethedev/Claw3D.git /app
WORKDIR /app
RUN npm ci --ignore-scripts
ENV NEXT_TELEMETRY_DISABLED=1
# Build-time gateway URL (overridden at runtime by CLAW3D_GATEWAY_URL).
ENV NEXT_PUBLIC_GATEWAY_URL=ws://127.0.0.1:18789
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/server ./server
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.ts ./next.config.ts

EXPOSE 3000

CMD ["node", "server/index.js"]
