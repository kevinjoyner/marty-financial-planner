# Stage 1: Base
FROM python:3.11-slim AS base

RUN apt-get update && apt-get install -y git curl gnupg gosu

# Install Node.js
RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
RUN apt-get update && apt-get install -y nodejs

# Create user
RUN groupadd appuser && useradd -g appuser -m appuser

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# Deps
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy App
COPY . .
# We initially own it, but volume mount might change it
RUN chown -R appuser:appuser /app

# IMPORTANT: We STAY as ROOT here. 
# start.sh will handle the user switch.
CMD ["./start.sh"]

# Stage 2: Builder
FROM base AS builder
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# Stage 3: Production
FROM python:3.11-slim AS production

RUN apt-get update && apt-get install -y gosu && rm -rf /var/lib/apt/lists/*

RUN groupadd appuser && useradd -g appuser -m appuser

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV PYTHONPATH=/app

WORKDIR /app

COPY --from=base /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .
COPY --from=builder --chown=appuser:appuser /app/frontend/dist /app/frontend/dist

COPY --chown=appuser:appuser start.sh .
COPY --chown=appuser:appuser heal_db.py .
RUN chmod +x start.sh

# Ensure data directory exists
RUN mkdir -p /app/data

EXPOSE 8000

# Run as ROOT so we can fix volume permissions
USER root
CMD ["./start.sh"]
