# syntax=docker/dockerfile:1

# =============================================================================
# BASIC / NAIVE IMAGE (for comparison only)
#
# * one single stage
# * full Node.js image including compilers and build tools
# * dev dependencies, sources and the build step all stay in the final image
# * serves the build with `vite preview` (fine for a demo, not for real prod)
#
# Build:  docker build -t counter-frontend:basic .
# =============================================================================
FROM node:22

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite embeds this value into the static bundle at build time.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

EXPOSE 8080

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "8080"]
