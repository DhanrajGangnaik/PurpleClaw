#!/usr/bin/env bash
# Run with: ./test_api.sh

set -u

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
RESPONSE_FILE="${TMPDIR:-/tmp}/purpleclaw_response.json"

PAYLOAD='{
  "id": "plan-1",
  "name": "Test Plan",
  "description": "Basic validation test",
  "environment": "endpoint",
  "scope": {
    "allowed_targets": ["lab-node-1"],
    "blocked_targets": [],
    "max_execution_time": 300
  },
  "techniques": [
    {
      "id": "T1059",
      "name": "Command and Scripting Interpreter",
      "description": "Technique example"
    }
  ],
  "execution_steps": [
    {
      "step_id": "step-1",
      "description": "Safe stubbed validation step",
      "executor": "custom",
      "command_reference": "ref-safe-001",
      "safe": true
    }
  ],
  "expected_telemetry": [
    {
      "source": "sysmon",
      "event_type": "process_create",
      "description": "Expected process creation event"
    }
  ],
  "expected_detections": [
    {
      "detection_name": "Suspicious Process Execution",
      "data_source": "sysmon",
      "severity": "medium",
      "description": "Example detection expectation"
    }
  ],
  "rollback_steps": [
    {
      "step_id": "rb-1",
      "action": "No-op cleanup"
    }
  ],
  "risk_level": "low",
  "requires_approval": false
}'

pretty_print() {
  if command -v jq >/dev/null 2>&1; then
    jq .
  else
    cat
  fi
}

request() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local response
  local status
  local content

  if [ -n "$body" ]; then
    response="$(curl -sS -w '\n%{http_code}' -X "$method" \
      "$BASE_URL$path" \
      -H 'Content-Type: application/json' \
      -d "$body")"
  else
    response="$(curl -sS -w '\n%{http_code}' -X "$method" \
      "$BASE_URL$path")"
  fi

  status="$(printf '%s' "$response" | tail -n 1)"
  content="$(printf '%s' "$response" | sed '$d')"

  printf '%s\n' "$content" | pretty_print
  printf 'HTTP %s\n' "$status"
  printf '%s\n' "$content" > "$RESPONSE_FILE"

  if [ "$status" != "200" ]; then
    printf 'ERROR: expected HTTP 200\n' >&2
    return 1
  fi
}

assert_json_value() {
  local filter="$1"
  local expected="$2"
  local actual

  if ! command -v jq >/dev/null 2>&1; then
    return 0
  fi

  actual="$(jq -r "$filter" "$RESPONSE_FILE")"
  if [ "$actual" != "$expected" ]; then
    printf 'ERROR: expected %s to be %s, got %s\n' "$filter" "$expected" "$actual" >&2
    return 1
  fi
}

assert_json_exists() {
  local filter="$1"
  local actual

  if ! command -v jq >/dev/null 2>&1; then
    return 0
  fi

  actual="$(jq -r "$filter" "$RESPONSE_FILE")"
  if [ -z "$actual" ] || [ "$actual" = "null" ]; then
    printf 'ERROR: expected %s to exist\n' "$filter" >&2
    return 1
  fi
}

main() {
  local failed=0

  printf '=== VALIDATE PLAN ===\n'
  request POST /validate-plan "$PAYLOAD" && assert_json_value '.valid' 'true' || failed=1

  printf '\n=== EXECUTE PLAN ===\n'
  request POST /execute-stub "$PAYLOAD" && assert_json_exists '.execution_id' || failed=1

  printf '\n=== GET PLANS ===\n'
  request GET /plans || failed=1

  printf '\n=== GET EXECUTIONS ===\n'
  request GET /executions || failed=1

  return "$failed"
}

main "$@"
