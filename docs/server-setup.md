# Server Setup Guide: MT5 Terminal

This guide outlines the steps to set up the MetaTrader 5 terminal and its API on a Linux server using Docker and Nginx.

## Prerequisites

- A Linux server (Ubuntu 22.04+ recommended).
- Docker and Docker Compose installed.
- A domain name with A records pointing to your server's IP.

## 1. Clone the Repository

```bash
git clone https://github.com/nodalytics/metatrader-terminal.git
cd metatrader-terminal
```

## 2. Environment Configuration

Create a `.env` file in the root directory and configure the necessary variables (MT5 credentials, API keys, etc.).

## 3. Deployment with Docker Compose

Build and start the services using Docker Compose:

```bash
docker compose up -d --build
```

This will start the MT5 terminal (VNC) and the FastAPI server.

## 4. Nginx Configuration

1.  **Copy snippets**:
    ```bash
    sudo cp nginx/snippets/proxy_params.conf /etc/nginx/snippets/
    ```
2.  **Copy site config**:
    ```bash
    sudo cp nginx/sites-available/mt5 /etc/nginx/sites-available/
    ```
3.  **Edit site config**:
    Update the `server_name` in `/etc/nginx/sites-available/mt5` with your actual subdomains.
4.  **Enable the site**:
    ```bash
    sudo ln -s /etc/nginx/sites-available/mt5 /etc/nginx/sites-enabled/
    ```
5.  **Test and Reload**:
    ```bash
    sudo nginx -t
    sudo systemctl reload nginx
    ```

## 5. SSL with Certbot (Optional but Recommended)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d vnc.yourdomain.com -d api.yourdomain.com
```

## 6. Accessing the Services

- **MT5 VNC**: `https://vnc.yourdomain.com`
- **MT5 API**: `https://api.yourdomain.com`
