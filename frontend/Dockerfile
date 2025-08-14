# Stage 1: Build React App
FROM node:20-alpine AS builder

WORKDIR /app

# Copy source files
COPY package*.json ./
RUN npm install

COPY . . 
RUN npm run build


# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy custom nginx config to support SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from previous stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
