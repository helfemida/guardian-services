# Infra Stack (Docker Compose)

Local infrastructure for violence-detection development.

## What Is Included

- PostgreSQL 15 (metadata and durable app data)
- Redis 7 (debounce/cache/transient state)
- MinIO (object storage for media chunks)
- Kafka in KRaft mode (event bus, no ZooKeeper)
- Kafka UI (topic and message inspection)
- MediaMTX (RTSP ingest + HLS/WebRTC playback)

## Repository Structure

- `docker-compose.yml` - all infrastructure services
- `.env.example` - environment variables template
- `mediamtx.yml` - MediaMTX stream and WebRTC settings
- `contracts/raw-media-events.schema.json` - example payload for `raw-media-events`
- `contracts/violence-alerts.schema.json` - example payload for `violence-alerts`
- `scripts/create-topics.sh` - safe idempotent Kafka topics bootstrap script

## Prerequisites

- Docker Desktop with Docker Compose plugin
- Git Bash or WSL (for running `scripts/create-topics.sh`)

## Quick Start

1. Create local env file:

```bash
cp .env.example .env
```

2. Fill required secrets in `.env`:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`
- `KAFKA_KRAFT_CLUSTER_ID`
- `KAFKA_EXTERNAL_IP` (host IP or DNS name that clients use to reach Kafka)

3. Start infrastructure:

```bash
docker compose up -d
```

4. Check status:

```bash
docker compose ps
docker compose logs -f kafka
```

5. Create/update Kafka topics safely:

```bash
bash scripts/create-topics.sh
```

## Service Endpoints and Ports

| Service | Host Port | Notes |
|---|---:|---|
| PostgreSQL | `5432` | `POSTGRES_PORT` |
| Redis | `6379` | `REDIS_PORT` |
| MinIO API | `9000` | S3-compatible API |
| MinIO Console | `9001` | Web UI |
| Kafka internal listener | `9092` | Container-to-container (`kafka:9092`) |
| Kafka host listener | `29092` | Host tools and IDE clients |
| Kafka UI | `8080` | Web UI |
| MediaMTX RTSP | `8554` | RTSP ingest/play |
| MediaMTX RTMP | `1935` | RTMP ingest/play |
| MediaMTX HLS | `8888` | Browser HLS playback |
| MediaMTX WebRTC HTTP | `8889` | WHEP endpoint |
| MediaMTX WebRTC ICE UDP | `8189/udp` | Required for WebRTC connectivity |
| MediaMTX SRT | `8890/udp` | SRT ingest/play |

## Persistent Volumes

- `pgdata` - PostgreSQL data
- `redis_data` - Redis data (AOF)
- `minio_data` - MinIO objects
- `kafka_data` - Kafka logs and metadata
- `mediamtx_data` - MediaMTX recordings

## Kafka Configuration Notes

Kafka runs in KRaft mode, so ZooKeeper is not required.

Important listeners in `docker-compose.yml`:

- Internal: `kafka:9092` (for containers)
- Host access: `${KAFKA_EXTERNAL_IP}:29092` (for IDEs, local/remote clients)

`KAFKA_EXTERNAL_IP` must be reachable from your Kafka client machine.
Examples:

- same machine as Docker: `127.0.0.1`
- LAN client: server LAN IP (for example `192.168.1.50`)
- Tailscale client: server Tailscale IP (for example `100.x.y.z`)

### IntelliJ Kafka Plugin Connection

Use:

- Bootstrap servers: `<KAFKA_EXTERNAL_IP>:29092`
- Auth: `None`
- SSL: disabled

Do not use `9092` from host IDE.

## Kafka Topics Script (Safe + Idempotent)

Script: `scripts/create-topics.sh`

It manages:

- `raw-media-events` - `10` partitions, retention `24h` (`86400000` ms)
- `violence-alerts` - `5` partitions, retention `7d` (`604800000` ms)

Rerun behavior:

- creates missing topics
- updates `retention.ms` and `cleanup.policy=delete`
- increases partitions if lower than target
- never decreases partitions
- never deletes topics

Optional overrides:

```bash
BOOTSTRAP_SERVER=localhost:9092 REPLICATION_FACTOR=1 bash scripts/create-topics.sh
```

## MediaMTX Setup

Config file: `mediamtx.yml` (mounted read-only into container)

Current paths:

- `camera1`
- `camera2`
- `camera3`

### Playback URLs

HLS:

- `http://<server-ip>:8888/camera1/index.m3u8`
- `http://<server-ip>:8888/camera2/index.m3u8`
- `http://<server-ip>:8888/camera3/index.m3u8`

WebRTC/WHEP (lower latency):

- `http://<server-ip>:8889/camera1/whep`
- `http://<server-ip>:8889/camera2/whep`
- `http://<server-ip>:8889/camera3/whep`

### WebRTC Notes

- Keep both `8889/tcp` and `8189/udp` open.
- In Tailscale or multi-network setups, add reachable addresses in:

```yaml
webrtcAdditionalHosts:
  - <tailscale-or-public-ip>
  - 127.0.0.1
```

`webrtcAdditionalHosts` does not support wildcard `*`.

### Codec Compatibility

For browser playback, prefer camera stream codec `H264`.

`H265` can show black/frozen video in browsers even when stream is online.

## MinIO Usage in Events

When referencing media object in Kafka message, include:

- `bucket`
- `object_key`

Example:

```json
{
  "bucket": "violence-media",
  "object_key": "facility/camera/2026-04-12/chunk.mp4"
}
```

Backend can construct URL or use SDK with endpoint + bucket + key.

## Contracts

Files in `contracts/` currently contain sample payloads used for testing and manual produce in Kafka UI.

- `raw-media-events.schema.json`
- `violence-alerts.schema.json`

Note: despite filename suffix `.schema.json`, these are examples, not strict JSON Schema definitions yet.

## Common Commands

Start all services:

```bash
docker compose up -d
```

Restart one service:

```bash
docker compose up -d mediamtx
```

Pull image for one service:

```bash
docker compose pull kafka
```

Show logs:

```bash
docker compose logs -f mediamtx
docker compose logs -f kafka
```

Stop all services:

```bash
docker compose down
```

Stop and remove volumes (destructive):

```bash
docker compose down -v
```

## Troubleshooting

### Docker Hub token error 520

Symptoms: image pull fails with `auth.docker.io/token ... 520`

Actions:

1. `docker logout && docker login`
2. retry `docker compose pull`
3. check Docker status page
4. restart Docker Desktop if needed

### Kafka image not found

This stack uses `bitnamilegacy/kafka:4.0.0-debian-12-r10` because `bitnami/kafka:latest` is not available.

### WebRTC session timeout (`deadline exceeded while waiting connection`)

Usually caused by ICE connectivity:

- ensure `8189/udp` is published
- ensure correct `webrtcAdditionalHosts`
- verify firewall/NAT rules

### Browser video shows frame only or frozen

Likely codec issue (`H265`).
Switch camera stream to `H264` and test again.

## Security Notes

- Replace all default passwords before sharing environment.
- Do not commit real credentials to git.
- Keep `.env` local; commit only `.env.example`.

## Handoff Checklist

Before handing to another engineer:

1. `docker compose ps` shows all required services up
2. Kafka UI opens on `http://localhost:8080`
3. MinIO console opens on `http://localhost:9001`
4. `bash scripts/create-topics.sh` runs without errors
5. Topics `raw-media-events` and `violence-alerts` exist
6. MediaMTX path playback works (HLS or WHEP)


