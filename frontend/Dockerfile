FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ENV BACKEND_URL=http://backend:8000
ENV NEXT_PUBLIC_API_URL=
RUN npm run build
ENV PORT=3000
CMD ["npm", "start"]
