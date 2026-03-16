#!/bin/bash

# 1. Initialize Authentication (Must happen BEFORE Nginx starts)
if [ -f /root/vnc-auth.sh ]; then
    chmod +x /root/vnc-auth.sh
    /root/vnc-auth.sh
else
    echo "==> WARNING: /root/vnc-auth.sh not found. skipping auth initialization."
fi

# 2. Start supervisord using exec to ensure it is PID 1
echo "==> Starting services via supervisor..."
exec /usr/bin/supervisord -c /etc/supervisord.conf
