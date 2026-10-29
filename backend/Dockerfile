# Dockerfile for StockTalk Backend (Express.js + TypeScript + SQLite)
FROM node:20-alpine

WORKDIR /app

# Install dependencies first (better layer caching)
COPY package.json package-lock.json* ./
RUN npm install --omit=dev

# Copy application code
COPY . .

# Build TypeScript
RUN npm run build

# Expose Express on port 8000
EXPOSE 8000

# Bind to 0.0.0.0 so the container is reachable from the host
CMD ["npm", "start"]
