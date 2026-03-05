#!/bin/bash

# Create .htpasswd for Nginx Basic Auth
if [ -n "$VNC_USER" ] && [ -n "$VNC_PASSWORD" ]; then
    echo "Setting up Nginx Basic Auth for user: $VNC_USER"
    htpasswd -bc /root/.htpasswd "$VNC_USER" "$VNC_PASSWORD"
else
    echo "Warning: VNC_USER or VNC_PASSWORD not set. Authentication might fail."
fi

# Create VNC password file for Xtigervnc
if [ -n "$VNC_PASSWORD" ]; then
    echo "Setting up VNC password"
    mkdir -p /root/.vnc
    echo "$VNC_PASSWORD" | vncpasswd -f > /root/.vnc/passwd
    chmod 600 /root/.vnc/passwd
else
    echo "Warning: VNC_PASSWORD not set. Direct VNC might not be secure."
fi
