#!/bin/bash
# Auto-deploy script: sync code + rebuild frontend + restart services
set -e

echo "=== Syncing backend code to Docker VM ==="
FILES=(
    "src/engines/risk_index.py"
    "src/engines/risk_monitor.py"
    "src/engines/report_generator.py"
    "src/engines/social_content.py"
    "src/engines/context_signals.py"
    "src/engines/orchestrator.py"
    "src/scheduler/daily_job.py"
    "src/data/collector.py"
)
for f in "${FILES[@]}"; do
    orb run -m meks -u root cp "/mnt/mac/Users/yaojun72/Documents/workspace/llm/daliyQ/$f" "/opt/daliyQ/$f" 2>/dev/null
done
echo "  ✓ Backend synced"

echo "=== Building frontend ==="
cd /Users/yaojun72/Documents/workspace/llm/daliyQ/frontend
npx vite build 2>&1 | tail -1
echo "  ✓ Frontend built"

echo "=== Deploying frontend to Docker ==="
cd /Users/yaojun72/Documents/workspace/llm/daliyQ
orb run -m meks -u root docker cp frontend/dist/. macro_risk_frontend:/usr/share/nginx/html/
orb run -m meks -u root docker exec macro_risk_frontend nginx -s reload 2>/dev/null
echo "  ✓ Frontend deployed"

echo "=== Restarting API ==="
orb run -m meks -u root docker restart macro_risk_api 2>/dev/null
echo "  ✓ API restarted"

echo ""
echo "=== Deploy complete ==="
