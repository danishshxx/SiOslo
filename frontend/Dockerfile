# Gunakan Node.js versi ringan
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy file dependencies DAN folder patches (INI KUNCI FIX-NYA)
COPY package.json pnpm-lock.yaml* ./
COPY patches ./patches

# Install dependencies
RUN pnpm install

# Copy semua source code
COPY . .

# Build frontend (React/Vite) & server (Express)
RUN pnpm run build

# Buka port 3000
EXPOSE 3000

# Jalankan server production
CMD ["pnpm", "run", "start"]