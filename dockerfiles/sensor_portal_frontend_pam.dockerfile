FROM node:20-alpine

WORKDIR /app/frontend_pam/

COPY ./frontend_pam/package*.json /app/frontend_pam/
RUN npm install
RUN npm install -g esbuild@0.24.2

COPY ./frontend_pam /app/frontend_pam/
