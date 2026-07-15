FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm config set strict-ssl false \
    && npm install -g npm@11.7.0 --no-audit --no-fund --registry=https://registry.npmjs.org \
    && npm ci --ignore-scripts --no-audit --no-fund --registry=https://registry.npmjs.org

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build
RUN cp -r .next/static .next/standalone/.next/static

EXPOSE 3000

CMD ["node", ".next/standalone/server.js"]
