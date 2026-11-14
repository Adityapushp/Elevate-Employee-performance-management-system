FROM node:20-alpine
WORKDIR /app
COPY backend/package.json ./backend/package.json
RUN cd backend && npm install --omit=dev
COPY backend/src ./backend/src
COPY database ./database
ENV NODE_ENV=production
EXPOSE 8000
CMD ["sh", "-c", "node backend/src/db/migrate.js && node backend/src/db/seed-demo.js && node backend/src/server.js"]
