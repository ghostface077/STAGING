FROM node:20-alpine AS base

WORKDIR /app

# --- Dépendances ---
FROM base AS deps
COPY package.json package-lock.json ./
RUN npm ci

# --- Build ---
# NEXT_PUBLIC_API_URL doit être disponible ici : Next.js fige les variables
# NEXT_PUBLIC_* dans le bundle JavaScript au moment de `next build`, pas au
# lancement du conteneur. La passer uniquement en `environment:` runtime dans
# docker-compose.yml n'aurait donc aucun effet sur le code déjà construit.
FROM base AS builder
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# --- Exécution ---
FROM base AS runner
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs \
    && apk add --no-cache wget

COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD wget --quiet --spider http://localhost:3000 || exit 1

CMD ["npm", "start"]
