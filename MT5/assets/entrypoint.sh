#!/bin/sh
# Make sure no X11 lock files exist from previous execution
/root/rmX11lock.sh
# 1. Initialize Authentication (Must happen BEFORE Nginx starts)
if [ -f /root/vnc-auth.sh ]; then
    /root/vnc-auth.sh
else
    echo "==> WARNING: /root/vnc-auth.sh not found. skipping auth initialization."
fi

# 2. Start supervisord using exec to ensure it is PID 1
echo "==> Starting services via supervisor..."
exec /usr/bin/supervisord -c /etc/supervisord.conf
