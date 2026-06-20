#!/bin/bash
# start.sh
# Starts the API, Worker, and Web frontend

# Kill any existing processes on ports 8000, 8001
echo "Cleaning up existing processes on ports 8000 and 8001..."
kill -9 $(lsof -t -i:8000) 2>/dev/null || true
kill -9 $(lsof -t -i:8001) 2>/dev/null || true

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Start the API on port 8000
echo "Starting API on port 8000..."
cd apps/api
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
API_PID=$!
cd ../..

# Start the Worker on port 8001
echo "Starting Worker on port 8001..."
cd apps/worker
uvicorn main:app --host 127.0.0.1 --port 8001 --reload &
WORKER_PID=$!
cd ../..

echo "Backend services are running."
echo "API PID: $API_PID"
echo "Worker PID: $WORKER_PID"

# Wait for them to spin up
sleep 2

# You can now run the web frontend in another terminal, or uncomment the line below
# npm run dev:web

wait
