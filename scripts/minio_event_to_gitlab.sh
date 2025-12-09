#!/usr/bin/env bash
set -euo pipefail

GITLAB_TRIGGER_URL=${GITLAB_TRIGGER_URL:-"https://gitlab.com/api/v4/projects/<PROJECT_ID>/trigger/pipeline"}
GITLAB_TOKEN=${GITLAB_TOKEN:-"<YOUR_TRIGGER_TOKEN>"}
REF=${REF:-main}

curl -X POST -F token=${GITLAB_TOKEN} -F ref=${REF} ${GITLAB_TRIGGER_URL}
