#!/bin/bash

echo "================"
echo "Starting service..."
echo "================"

python engine/engine.py &
python app.py > app_log.txt &

echo "================"
echo "Started!"
echo "================"

