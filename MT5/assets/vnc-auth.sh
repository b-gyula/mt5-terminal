#!/bin/bash

# Create .htpasswd for Nginx Basic Auth
if [ -n "$VNC_USER" ] && [ -n "$VNC_PASSWORD" ]; then
    echo "==> Setting up Nginx Basic Auth for user: $VNC_USER"
    if htpasswd -bc /root/.htpasswd "$VNC_USER" "$VNC_PASSWORD" > /dev/null 2>&1; then
        echo "    ✅ .htpasswd created successfully at /root/.htpasswd"
        chmod 644 /root/.htpasswd
    else
        echo "    ❌ ERROR: Failed to create .htpasswd"
        exit 1
    fi
else
    echo "==> WARNING: VNC_USER or VNC_PASSWORD not set. Authentication will likely fail."
fi

# Create VNC password file for Xtigervnc
if [ -n "$VNC_PASSWORD" ]; then
    echo "==> Setting up VNC password..."
    mkdir -p /root/.vnc
    if echo "$VNC_PASSWORD" | vncpasswd -f > /root/.vnc/passwd; then
        echo "    ✅ VNC password file created at /root/.vnc/passwd"
        chmod 600 /root/.vnc/passwd
    else
        echo "    ❌ ERROR: Failed to set VNC password"
        # exit 1 # Not critical for HTTP auth but good to know
    fi
else
    echo "==> WARNING: VNC_PASSWORD not set. Direct VNC will not be secure."
fi
