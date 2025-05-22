FROM node:20-alpine

WORKDIR /app/frontend/

COPY ./frontend/package.json /app/frontend/

COPY ./frontend /app/frontend
RUN npm install



RUN npm install








