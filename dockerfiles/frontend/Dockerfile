FROM node:24-alpine AS build

WORKDIR /app

COPY simple_tickets_frontend_v2/package*.json ./

RUN npm ci

COPY simple_tickets_frontend_v2/ ./

RUN npm run build


FROM nginx:alpine

COPY dockerfiles/frontend/nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]