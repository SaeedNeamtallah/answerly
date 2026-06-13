# Stage 1: Install dependencies
FROM node:20-slim AS deps
WORKDIR /app
COPY frontend-next/package.json frontend-next/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --no-frozen-lockfile

# Stage 2: Build the source code
FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend-next ./
ENV NEXT_PUBLIC_API_BASE_URL=/api
RUN npm install -g pnpm && pnpm build

# Stage 3: Production runner
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV production
ENV PORT 3001
ENV HOSTNAME "0.0.0.0"

RUN groupadd --system --gid 1001 nodejs
RUN useradd --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER nextjs

EXPOSE 3001

CMD ["node_modules/.bin/next", "start", "-H", "0.0.0.0", "-p", "3001"]
