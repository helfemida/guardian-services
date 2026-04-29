#!/usr/bin/env bash
set -euo pipefail

# Safe and idempotent Kafka topic bootstrap script.
# - Creates topics if missing
# - Updates retention/cleanup configs on rerun
# - Never deletes topics
# - Never decreases partition count

KAFKA_SERVICE="${KAFKA_SERVICE:-kafka}"
BOOTSTRAP_SERVER="${BOOTSTRAP_SERVER:-localhost:9092}"
REPLICATION_FACTOR="${REPLICATION_FACTOR:-1}"

RAW_TOPIC="${RAW_TOPIC:-raw-media-events}"
RAW_PARTITIONS="${RAW_PARTITIONS:-10}"
RAW_RETENTION_MS="${RAW_RETENTION_MS:-86400000}"          # 24h

ALERTS_TOPIC="${ALERTS_TOPIC:-violence-alerts}"
ALERTS_PARTITIONS="${ALERTS_PARTITIONS:-5}"
ALERTS_RETENTION_MS="${ALERTS_RETENTION_MS:-604800000}"   # 7d

ERROR_TOPIC="${ERROR_TOPIC:-raw-media-events-errors}"
ERROR_PARTITIONS="${ERROR_PARTITIONS:-3}"
ERROR_RETENTION_MS="${ERROR_RETENTION_MS:-604800000}"     # 7d

KAFKA_TOPICS_CMD=(docker compose exec -T "${KAFKA_SERVICE}" kafka-topics.sh)
KAFKA_CONFIGS_CMD=(docker compose exec -T "${KAFKA_SERVICE}" kafka-configs.sh)

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $1" >&2
    exit 1
  fi
}

topic_exists() {
  local topic="$1"
  "${KAFKA_TOPICS_CMD[@]}" --bootstrap-server "${BOOTSTRAP_SERVER}" --list | grep -Fxq "${topic}"
}

get_partition_count() {
  local topic="$1"
  "${KAFKA_TOPICS_CMD[@]}" \
    --bootstrap-server "${BOOTSTRAP_SERVER}" \
    --describe \
    --topic "${topic}" \
    | awk -F'PartitionCount:|ReplicationFactor:' 'NF>1 {gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2; exit}'
}

create_topic() {
  local topic="$1"
  local partitions="$2"
  local retention_ms="$3"

  echo "Creating topic '${topic}' (partitions=${partitions}, retention.ms=${retention_ms})"
  "${KAFKA_TOPICS_CMD[@]}" \
    --bootstrap-server "${BOOTSTRAP_SERVER}" \
    --create \
    --if-not-exists \
    --topic "${topic}" \
    --partitions "${partitions}" \
    --replication-factor "${REPLICATION_FACTOR}" \
    --config cleanup.policy=delete \
    --config retention.ms="${retention_ms}"
}

reconcile_topic() {
  local topic="$1"
  local target_partitions="$2"
  local target_retention_ms="$3"

  if topic_exists "${topic}"; then
    local current_partitions
    current_partitions="$(get_partition_count "${topic}")"
    echo "Topic '${topic}' exists (current partitions=${current_partitions})"

    if [[ -n "${current_partitions}" ]] && (( current_partitions < target_partitions )); then
      echo "Increasing partitions for '${topic}' to ${target_partitions}"
      "${KAFKA_TOPICS_CMD[@]}" \
        --bootstrap-server "${BOOTSTRAP_SERVER}" \
        --alter \
        --topic "${topic}" \
        --partitions "${target_partitions}"
    elif [[ -n "${current_partitions}" ]] && (( current_partitions > target_partitions )); then
      echo "WARN: '${topic}' has ${current_partitions} partitions (> target ${target_partitions}); not decreasing."
    fi

    "${KAFKA_CONFIGS_CMD[@]}" \
      --bootstrap-server "${BOOTSTRAP_SERVER}" \
      --alter \
      --entity-type topics \
      --entity-name "${topic}" \
      --add-config "retention.ms=${target_retention_ms},cleanup.policy=delete"
  else
    create_topic "${topic}" "${target_partitions}" "${target_retention_ms}"
  fi
}

main() {
  require_command docker
  require_command awk
  require_command grep

  echo "Bootstrapping Kafka topics with safe idempotent script..."
  echo "Kafka service: ${KAFKA_SERVICE}"
  echo "Bootstrap server (inside Kafka container): ${BOOTSTRAP_SERVER}"

  reconcile_topic "${RAW_TOPIC}" "${RAW_PARTITIONS}" "${RAW_RETENTION_MS}"
  reconcile_topic "${ALERTS_TOPIC}" "${ALERTS_PARTITIONS}" "${ALERTS_RETENTION_MS}"
  reconcile_topic "${ERROR_TOPIC}" "${ERROR_PARTITIONS}" "${ERROR_RETENTION_MS}"

  echo
  echo "Final topic state:"
  "${KAFKA_TOPICS_CMD[@]}" --bootstrap-server "${BOOTSTRAP_SERVER}" \
    --describe --topic "${RAW_TOPIC}" --topic "${ALERTS_TOPIC}" --topic "${ERROR_TOPIC}"
}

main "$@"
