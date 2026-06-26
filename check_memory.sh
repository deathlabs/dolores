#!/usr/bin/env bash

BASE_URL="http://localhost:8000"
LIMIT="100"

echo "[ Procedural Memory] "
curl -s "${BASE_URL}/api/v1/memories/search/?namespace_prefix=procedural&limit=${LIMIT}" | jq '.[] | .value.instruction'
echo ""

echo "[ Semantic Memory ]"
curl -s "${BASE_URL}/api/v1/memories/search/?namespace_prefix=semantic&limit=${LIMIT}" | jq '.[] | "\(.namespace[1]): \(.value.fact)"'
echo ""

echo "[ Session Memory ]"
curl -s "${BASE_URL}/api/v1/checkpoints/" | jq 'sort_by(.thread_id, .checkpoint_id) | .[] | "\(.thread_id) [\(.checkpoint_id)]"'
echo ""
