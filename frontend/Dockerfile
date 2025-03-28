# Stage 1: Build the React app
FROM node:16-alpine as build
WORKDIR /app
COPY package.json tsconfig.json /app/
# Install react-scripts explicitly before continuing
RUN npm install react-scripts -g
COPY public /app/public
COPY src /app/src
RUN npm install
# Install @types/node to fix TypeScript error with process.env
RUN npm install --save-dev @types/node
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:1.21-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
