FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install

COPY index.html ./
COPY vite.config.js ./
COPY src ./src

# VITE_API_BASE_URL is baked in at build time, not runtime.
# Override with --build-arg if the API is reachable at a different host:port.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
