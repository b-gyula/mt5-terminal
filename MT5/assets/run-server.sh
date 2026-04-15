#!/bin/sh

# Run the auto-login script
# wine python $HOME/auto_login.py

# Wait for 2 seconds
# sleep 2

if [ ! -f "$MT5_PATH" ]; then
   echo MetaTrader 5 not found.
	exit 1
fi

# Start the server after the auto-login script completes
echo "Starting FastAPI Server..."
cd $HOME
# export PYTHONPATH=$PYTHONPATH:$HOME/api
wine uv run -m app


# CMD ["wine", "python server.py"]
# --host ${SERVER_HOST} -p ${SERVER_PORT}