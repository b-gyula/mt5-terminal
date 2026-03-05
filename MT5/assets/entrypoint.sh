#!/bin/bash

# Start supervisord in the background
/usr/bin/supervisord -c /etc/supervisord.conf &

# Wait for supervisor and its services to be ready
echo "Waiting for services to initialize..."
sleep 10

# Run MT5
echo "Starting MetaTrader 5..."
/root/run-mt5.sh

# Keep container alive and show logs if run-mt5.sh returns
echo "MetaTrader 5 process exited. Tailing supervisor logs..."
tail -f /dev/stdout
