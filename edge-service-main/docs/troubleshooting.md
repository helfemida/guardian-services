# Troubleshooting

## RTSP does not connect
- Check `RTSP_URL`.
- Verify the edge host can reach the camera IP and RTSP port `554`.
- Try `RTSP_TRANSPORT=tcp` first; if the camera/network expects UDP, switch to `udp`.
- Use `RTSP_OPEN_TIMEOUT_MS` and `RTSP_READ_TIMEOUT_MS` to fail faster while debugging.
- Verify source is reachable from edge host.
- Confirm codec is supported by OpenCV build.

## MinIO upload fails
- Validate `MINIO_ENDPOINT` and credentials.
- Confirm bucket exists and access policy allows write.

## Kafka publish fails
- Validate `KAFKA_BOOTSTRAP_SERVERS`.
- Check topic exists: `raw-media-events`.
- Confirm network ACL/firewall allows broker connection.
- If bootstrap IP is reachable but `aiokafka` still logs `getaddrinfo failed`, the broker may be advertising an internal hostname like `kafka`.
- In that case either fix broker `advertised.listeners` or set `KAFKA_HOST_ALIASES`, for example `KAFKA_HOST_ALIASES=kafka=100.100.224.121`.

## Person detector fails to start
- Confirm `PERSON_MODEL_PATH` points to a local Ultralytics `.pt` file.
- Verify `ultralytics` is installed.
- Confirm `YOLO_CONFIG_DIR` is writable by the service account.

## Outbox backlog grows
- Review service logs for repeated upload/publish errors.
- Fix dependency outage, then verify backlog drains.
