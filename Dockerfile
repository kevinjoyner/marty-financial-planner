# Stage 1: Base
FROM python:3.11-slim AS base
RUN apt-get update && apt-get install -y git curl gnupg

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
RUN chown -R appuser:appuser /app

USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 2: Builder
FROM base AS builder
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# Stage 3: Production
FROM python:3.11-slim AS production

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

# Copy scripts and ensure executable
COPY --chown=appuser:appuser start.sh .
COPY --chown=appuser:appuser heal_db.py .
RUN chmod +x start.sh

# Create data dir with correct permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

USER appuser
EXPOSE 8000
CMD ["./start.sh"]
