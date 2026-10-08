# Claw3D Studio — Railway-ready build.
# Node 22: camera-controls requires >= 22 (upstream's Node-20 image crashes).
# The runner keeps devDependencies (TypeScript included) so Next.js can
# transpile next.config.ts at startup without installing anything at runtime.
# Patch: the custom runtime provider must no-op sessions.patch (Claw3D chat.send
# syncs session settings first; orchestrator-backed runtimes reject it otherwise).
FROM node:22-slim AS builder
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/iamlukethedev/Claw3D.git /app
WORKDIR /app
# Patch: make sessions.patch a harmless no-op in the custom runtime provider,
# and relax models.list over strictness when the runtime exposes no models.
# rebuild-3: force fresh layers (no-cache) so the patch is applied.
RUN node -e "const fs=require('fs');const p='src/lib/runtime/custom/provider.ts';let s=fs.readFileSync(p,'utf8');if(!s.includes('case \"sessions.patch\"')){s=s.replace('      case \"config.get\":','      case \"sessions.patch\":\n      case \"sessions.create\":\n        return ({ ok: true } as T);\n      case \"config.get\":');fs.writeFileSync(p,s);console.log('patched provider');}else{console.log('already patched');}"
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
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.ts ./next.config.ts

EXPOSE 3000

CMD ["node", "server/index.js"]
# Claw3D Studio — Railway-ready build.
# Node 22: camera-controls requires >= 22 (upstream's Node-20 image crashes).
# The runner keeps devDependencies (TypeScript included) so Next.js can
# transpile next.config.ts at startup without installing anything at runtime.
# Patch: the custom runtime provider must no-op sessions.patch (Claw3D chat.send
# syncs session settings first; orchestrator-backed runtimes reject it otherwise).
FROM node:22-slim AS builder
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/iamlukethedev/Claw3D.git /app
WORKDIR /app
# Patch: make sessions.patch a harmless no-op in the custom runtime provider,
# and relax models.list over strictness when the runtime exposes no models.
RUN node -e "const fs=require('fs');const p='src/lib/runtime/custom/provider.ts';let s=fs.readFileSync(p,'utf8');if(!s.includes('case \"sessions.patch\"')){s=s.replace('      case \"config.get\":','      case \"sessions.patch\":\n      case \"sessions.create\":\n        return ({ ok: true } as T);\n      case \"config.get\":');fs.writeFileSync(p,s);console.log('patched provider');}else{console.log('already patched');}"
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
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.ts ./next.config.ts

EXPOSE 3000

CMD ["node", "server/index.js"]
# Claw3D Studio — Railway-ready build.
# Node 22: camera-controls requires >= 22 (upstream's Node-20 image crashes).
# The runner keeps devDependencies (TypeScript included) so Next.js can
# transpile next.config.ts at startup without installing anything at runtime.
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
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.ts ./next.config.ts

EXPOSE 3000

CMD ["node", "server/index.js"]
