# Stage 1: Base (Python + Node.js for Dev)
FROM python:3.11-slim AS base

RUN apt-get update && apt-get install -y git curl gnupg

# Install Node.js 20.x
RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
RUN apt-get update && apt-get install -y nodejs

# Create non-root user
RUN groupadd appuser && useradd -g appuser -m appuser

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# Python Deps
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy App
COPY . .
RUN chown -R appuser:appuser /app

USER appuser

# Default Command (Overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 2: Build Frontend (For Production)
FROM base AS builder
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# Stage 3: Production Image
FROM python:3.11-slim AS production

RUN groupadd appuser && useradd -g appuser -m appuser

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV PYTHONPATH=/app

WORKDIR /app

# Install Python Deps
COPY --from=base /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Code
COPY --chown=appuser:appuser . .

# Copy Built Frontend Assets from Builder Stage
# Note: We copy to a specific 'static' folder or overwrite the source frontend
COPY --from=builder --chown=appuser:appuser /app/frontend/dist /app/frontend/dist

COPY --chown=appuser:appuser start.sh .
RUN chmod +x start.sh

RUN mkdir /data && chown appuser:appuser /data

USER appuser

EXPOSE 8000

CMD ["./start.sh"]
