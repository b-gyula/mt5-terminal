#!/bin/bash

# Start supervisord in the background
/usr/bin/supervisord -c /etc/supervisord.conf &

# Give supervisor a moment to start services (X11, etc.)
sleep 5

# Run MT5 (foreground to keep container alive if you prefer, or we can tail logs)
/root/run-mt5.sh
