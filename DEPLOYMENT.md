# MindMirror — Docker Deployment Guide

Complete record of how the MindMirror app was deployed to Azure using Docker and Azure Container Registry (ACR).

---

## Stack Overview

| Service | Image |
|---|---|
| Frontend | Custom Next.js build |
| Backend | Custom Python/FastAPI build |
| Database | postgres:16-alpine |
| AI (LLM) | ollama/ollama:latest |

---

## Prerequisites

- Docker Desktop installed and running
- Azure CLI installed
- An Azure subscription with a resource group
- Azure VM already created

---

## Step 1 — Install Azure CLI

```bash
winget install Microsoft.AzureCLI
```

Close and reopen the terminal after install so `az` is recognized in PATH.

---

## Step 2 — Register Azure Container Registry Provider

The Azure subscription needs the Container Registry namespace registered before ACR can be created.

```bash
# Register the provider
az provider register --namespace Microsoft.ContainerRegistry

# Check registration status (wait until it shows "Registered")
az provider show --namespace Microsoft.ContainerRegistry --query registrationState
```

---

## Step 3 — Create Azure Container Registry

```bash
az acr create --resource-group {resource-name} --name mindmirrorregistry --sku Basic
```

> **Security note:** Disable the ACR admin user and use a managed identity instead:
> ```bash
> az acr update --name mindmirrorregistry --admin-enabled false
> az role assignment create --assignee <vm-principal-id> \
>   --role AcrPull --scope <acr-resource-id>
> ```

---

## Step 4 — Build & Push Images to ACR

Only the `backend` and `frontend` images need to be pushed. `ollama` and `postgres` are already on Docker Hub.

### Fix: Frontend Dockerfile must accept build-time arg

`NEXT_PUBLIC_*` variables in Next.js are baked in at **build time**, not runtime. The Dockerfile must declare the `ARG` before the build step.

Add these two lines to `frontend/Dockerfile` in the builder stage:

```dockerfile
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_URL                        # ← added
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL   # ← added
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build
```

### Build images (PowerShell — no line breaks with `\`)

```powershell
# Build backend
docker build -t mindmirror-backend:latest ./backend

# Build frontend with VM IP baked in
docker build --build-arg NEXT_PUBLIC_API_URL=http://IP_or_Domain:8000 -t mindmirror-frontend:latest ./frontend
```

### Tag and push

```bash
az acr login --name mindmirrorregistry

docker tag mindmirror-backend:latest mindmirrorregistry.azurecr.io/mindmirror-backend:latest
docker tag mindmirror-frontend:latest mindmirrorregistry.azurecr.io/mindmirror-frontend:latest

docker push mindmirrorregistry.azurecr.io/mindmirror-backend:latest
docker push mindmirrorregistry.azurecr.io/mindmirror-frontend:latest
```

---

## Step 5 — Open Firewall Ports on Azure VM

Only open the ports the end user needs (frontend and backend API). Never open database or LLM ports to the public internet.

```bash
az vm open-port --resource-group {resource-name} --name {vm-name} --port 3000
az vm open-port --resource-group {resource-name} --name {vm-name} --port 8000 --priority 901
```

> Note: Each rule needs a unique priority. Port 3000 uses default (900), port 8000 uses 901.

> **Do not open ports 5432 (Postgres) or 11434 (Ollama).** These must only be reachable within the Docker network, not from the internet.

---

## Step 6 — Set Up the VM

SSH into the VM, then:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure and ACR
az login
az acr login --name mindmirrorregistry

# Create project folder
mkdir mindmirror && cd mindmirror
mkdir -p backend/database
```

Copy files to the VM:
- `docker-compose.yml`
- `.env`
- `backend/database/schema.sql`

Use `nano` to paste content directly:
```bash
nano docker-compose.yml
nano .env
nano backend/database/schema.sql
```

---

## Step 7 — Configure .env on VM

> **Security rules for this file:**
> - Never commit this file to version control — add `.env` to `.gitignore`
> - Replace every placeholder value before starting the app
> - Generate `JWT_SECRET` with the command below — never leave the placeholder

```env
POSTGRES_USER=mindmirror_user
POSTGRES_PASSWORD=your_strong_db_password_here
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
WHISPER_MODEL=base
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/mindmirror
NEXT_PUBLIC_API_URL=http://IP_or_Domain:8000
JWT_SECRET=your_generated_secret_here
HF_HOME=/app/.cache/huggingface
AI_PROVIDER=ollama
FRONTEND_ORIGIN=http://IP_or_Domain:3000
```

Generate a strong JWT secret and replace `your_generated_secret_here` with the output:
```bash
openssl rand -hex 32
```

Generate a strong Postgres password and replace `your_strong_db_password_here` with the output:
```bash
openssl rand -hex 16
```

> **Note:** `GROQ_API_KEY` has been removed. If you switch to the Groq AI provider in the future, add a real API key at that point — never use a placeholder string as a key value.

---

## Step 8 — Run the App

```bash
cd ~/mindmirror
docker compose pull
docker compose down
docker compose up -d

# Check all services are healthy
docker compose ps

# Watch logs
docker compose logs -f
```

---

## Bugs Fixed Along the Way

### 1. `az` not recognized after install
**Cause:** Terminal session didn't reload PATH after Azure CLI install.
**Fix:** Close and reopen the terminal.

---

### 2. `MissingSubscriptionRegistration` error
**Cause:** Azure subscription hadn't enabled the Container Registry provider.
**Fix:**
```bash
az provider register --namespace Microsoft.ContainerRegistry
az provider show --namespace Microsoft.ContainerRegistry --query registrationState
# Wait until output shows "Registered"
```

---

### 3. Port conflict when opening VM ports
**Cause:** Both `az vm open-port` commands used the same default priority (900).
**Fix:** Add `--priority 901` to the second command.

---

### 4. CORS error — `Access-Control-Allow-Origin` missing
**Cause 1:** `NEXT_PUBLIC_API_URL` was still pointing to `localhost:8000` — Next.js bakes this in at build time so runtime env vars have no effect.
**Fix:** Pass the VM IP as a build arg:
```powershell
docker build --build-arg NEXT_PUBLIC_API_URL=http://IP_or_Domain:8000 -t mindmirror-frontend:latest ./frontend
```

**Cause 2:** Backend `FRONTEND_ORIGIN` was hardcoded to `http://localhost:3000` in `docker-compose.yml`, overriding the `.env` file.
**Fix:** Update `docker-compose.yml` directly:
```yaml
- FRONTEND_ORIGIN=http://IP_or_Domain:3000
```
Then:
```bash
docker compose down
docker compose up -d
```

Verify the backend picked up the correct value:
```bash
docker exec mindmirror_backend env | grep FRONTEND
# Should show: FRONTEND_ORIGIN=http://IP_or_Domain:3000
```

---

### 5. `./backend:/app` volume mount overwriting container code
**Cause:** Dev-mode volume mount was left in docker-compose.yml, mounting local source over the container's built code.
**Fix:** Remove that volume in production, keep only the cache volume:
```yaml
volumes:
  - hf_cache:/app/.cache/huggingface  # keep
# - ./backend:/app                    # remove in production
```

---

### 6. PowerShell doesn't support `\` line continuation
**Cause:** Bash-style multi-line commands don't work in PowerShell.
**Fix:** Write commands on a single line in PowerShell:
```powershell
docker build --build-arg NEXT_PUBLIC_API_URL=http://IP_or_Domain:8000 -t mindmirror-frontend:latest ./frontend
```

---

## Access the App

| Service | URL |
|---|---|
| Frontend | http://IP_or_Domain:3000 |
| Backend API | http://IP_or_Domain:8000 |
| API Docs | http://IP_or_Domain:8000/docs |

---

## Quick Reference — Useful Commands

```bash
# Restart all containers and reload env
docker compose down && docker compose up -d

# Check container status
docker compose ps

# View logs for a specific service
docker logs mindmirror_backend --tail 50
docker logs mindmirror_frontend --tail 50

# Check what env vars a container is using
docker exec mindmirror_backend env

# Pull latest images and restart
docker compose pull && docker compose up -d --force-recreate

# Get VM public IP
az vm show --resource-group {resource-name} --name {vm-name} --show-details --query publicIps -o tsv
```