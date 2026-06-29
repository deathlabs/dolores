#!/usr/bin/env bash

BASE_URL="http://localhost:8000"
LIMIT="100"

source "$(dirname "$0")/tools/.env"
source "$(dirname "$0")/inference/.env"

session_memory() {   
    curl -s "${BASE_URL}/api/v1/checkpoints/" | jq -r 'sort_by(.thread_id, .checkpoint_id) | .[] | "\(.thread_id) [\(.checkpoint_id)]"' | tail -n 3
}

procedural_memory() {
    curl -s "${BASE_URL}/api/v1/memories/search/?namespace_prefix=procedural&limit=${LIMIT}" | jq '.[] | .value.instruction'
}

semantic_memory() {
    curl -s "${BASE_URL}/api/v1/memories/search/?namespace_prefix=semantic&limit=${LIMIT}" | jq -r '.[] | "\(.namespace[1]): \(.value.fact)"'
}


tool_calls() {
    docker logs dolores-inference 2>&1 |
        jq -r '
            if .tool_calls then
                .tool_calls[] |
                "pending, \(.name), \(.args | tojson)"
            elif .type == "tool" then
                "\(.status // "unknown"), \(.name), {}"
            else
                empty
            end
        '
}

downloads() {
    docker exec dolores-tools ls -lah /home/dolores/downloads/
}

pull_requests() {
    IFS=',' read -ra REPOS <<< "${REPOSITORIES}"
    for REPO in "${REPOS[@]}"; do
        REPO="$(echo "[ ${REPO} ]" | xargs)"
        curl -s \
            -H "Authorization: Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/${REPO}/pulls?state=open" \
            | jq -r 'sort_by(.number) | .[] | .html_url'
        echo ""
    done
}

case "$1" in
    "session-memory")
        session_memory
        ;;
    "procedural-memory")
        procedural_memory
        ;;
    "semantic-memory")
        semantic_memory
        ;;
    "tool-calls")
        tool_calls
        ;;
    "downloads")
        downloads
        ;;
    "pull-requests")
        pull_requests
        ;;
    *)
        echo "Usage: $0 {session-memory|procedural-memory|semantic-memory|tool-calls|downloads|pull-requests}"
        exit 1
        ;;
esac