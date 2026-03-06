# GitHub Actions Deployment Pipeline

This guide explains how to set up a GitHub Actions workflow to automatically deploy updates to your server.

## 1. Server Preparation

Ensure your server is accessible via SSH and that the deployment user has the necessary permissions to run Docker commands.

### SSH Key Setup
1.  Generate an SSH key pair on your local machine (if you don't have one).
2.  Add the public key to `~/.ssh/authorized_keys` on the server.
3.  Store the private key as a GitHub Secret.

## 2. GitHub Secrets

Go to your repository's **Settings > Secrets and variables > Actions** and add the following secrets:

- `SSH_HOST`: Your server's public IP address or hostname.
- `SSH_USER`: The username to SSH into (e.g., `ubuntu`).
- `SSH_KEY`: The content of your private SSH key.
- `DEPLOY_PATH`: The absolute path where the project should be deployed on the server.
- `GHCR_PAT`: A GitHub Personal Access Token with `read:packages` scope to pull images from GHCR.

## 3. Workflow Configuration

The deployment workflow is defined in `.github/workflows/deploy.yml`. It is triggered automatically when the **"Docker Build & Test"** workflow completes successfully on the `main` branch.

### Deployment Process:
1.  **SCP File Transfer**: Copies `MT5/docker-compose.yml` and `MT5/.env.example` to the server.
2.  **SSH Execution**:
    - Ensures a `.env` file exists (creates it from `.env.example` if missing).
    - Logs into the GitHub Container Registry (`ghcr.io`).
    - Pulls the latest Docker images.
    - Restarts the containers using `docker compose up -d`.

> [!NOTE]
> The workflow assumes that the Docker images are already built and pushed to GHCR by the prerequisite "Docker Build & Test" workflow.

> [!IMPORTANT]
> If this is a first-time setup, you may need to manually configure the `.env` file on the server after the first deployment to include sensitive production credentials.
