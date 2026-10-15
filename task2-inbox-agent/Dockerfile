FROM node:22-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY task2-inbox-agent/package*.json ./
RUN npm install

COPY task2-inbox-agent/ ./
COPY datasets/ /datasets/
RUN npm run build

EXPOSE 8002

CMD ["node", "dist/index.js"]
