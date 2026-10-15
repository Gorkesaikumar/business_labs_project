FROM node:22-slim

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
COPY datasets/ /datasets/
RUN npm run build

EXPOSE 3000

CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "3000"]
