# Backend Core - Harassment Detection Platform

This repository contains the backend service for a harassment/violence detection platform.
It provides authentication/authorization, incident management APIs, Kafka ingestion, Redis caching, and real-time WebSocket updates for frontend clients.

## Table of Contents

- [Project Purpose](#project-purpose)
- [Core Features](#core-features)
- [Architecture and Data Flow](#architecture-and-data-flow)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Authentication and Authorization](#authentication-and-authorization)
- [REST API](#rest-api)
- [WebSocket API](#websocket-api)
- [Kafka Integration](#kafka-integration)
- [Caching](#caching)
- [Database Model](#database-model)
- [Frontend Integration Notes](#frontend-integration-notes)
- [Known Limitations and Caveats](#known-limitations-and-caveats)
- [Troubleshooting](#troubleshooting)

## Project Purpose

The backend receives violence detection alerts from Kafka and turns them into persisted incidents.
Authorized users can:

- log in with JWT auth
- list incidents
- resolve incidents as confirmed/false positive
- (admin only) add guard accounts

The backend also publishes incident changes to WebSocket subscribers so the frontend can update in real time.

## Core Features

- JWT-based authentication and role-based authorization (`ADMIN`, `GUARD`)
- Incident listing and resolution API
- Guard management API for admins
- Kafka consumer for incoming detection events
- Dead-letter publishing for failed Kafka records
- Real-time WebSocket topic for incident updates
- Redis-based caching for incident list endpoint
- Audit logging to `logs` table for key actions/failures
- OpenAPI/Swagger UI support

## Architecture and Data Flow

1. Detection pipeline publishes `HarassmentAlertEvent` to Kafka topic `violence-alerts`.
2. `HarassmentAlertConsumerService` consumes the message.
3. `AlertPersistenceServiceImpl`:
   - validates camera existence
   - creates `Incident` row
   - evicts incident cache
   - publishes `IncidentResponse` to `/topic/incidents` over WebSocket
4. Frontend:
   - loads initial data from `GET /api/v1/incidents`
   - subscribes to `/topic/incidents` for live changes
5. When a user resolves an incident:
   - `PATCH /api/v1/incidents/{id}/resolve`
   - DB update + cache eviction + WebSocket update

## Tech Stack

- Java 21
- Spring Boot 4.0.5
- Spring Security
- Spring Data JPA (PostgreSQL)
- Spring Kafka
- Spring WebSocket (STOMP broker)
- Spring Cache + Redis
- JJWT (token generation/validation)
- Lombok
- Springdoc OpenAPI

## Project Structure

Main package: `com.project.backend_core`

- `config/` - Security, Kafka, Redis cache, WebSocket, CORS, seed data
- `controller/` - REST endpoints
- `dto/` - Request/response contracts
- `entity/` - JPA entities and enums
- `facade/` - Security context helper (`AuthFacade`)
- `kafka/` - Kafka consumer + incoming event model
- `mapper/` - Entity to DTO mapping (`IncidentMapper`)
- `repository/` - Spring Data repositories
- `security/` - JWT service and auth filter
- `service/` - Business services

## Getting Started

### Prerequisites

- JDK 21
- PostgreSQL
- Kafka broker
- Redis

### Default server

- HTTP: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/swagger-ui/index.html`
- WebSocket handshake: `ws://localhost:8000/ws`

## Configuration

Configuration file: `src/main/resources/application.yaml`

### Important environment variables

- `KAFKA_SERVER_URL` - Kafka bootstrap server
- `KAFKA_TOPIC` - topic name used for topic bean creation (`spring.kafka.topic.harassment`)
- `DATASOURCE_URL` - PostgreSQL JDBC URL (default: `jdbc:postgresql://localhost:5432/harassment`)
- `DATASOURCE_PASSWORD` - DB password (default: `admin1234`)
- `MINIO_URL` - base MinIO URL used in incident response
- `SPRING_REDIS_HOST` (default: `localhost`)
- `SPRING_REDIS_PORT` (default: `6379`)
- `SPRING_REDIS_PASSWORD` (default: `admin1234`)
- `SPRING_REDIS_USERNAME` (optional)
- `SPRING_REDIS_SSL_ENABLED` (default: `false`)
- `SPRING_REDIS_SSL_BUNDLE` (optional)
- `FRONTEND_URL` - allowed CORS origin (default fallback set in yaml)

### CORS whitelist

CORS is configured from:

```yaml
application:
  cors:
    allowed-origins:
      - ${FRONTEND_URL:http://localhost:5173,http://100.100.224.121:5173}
```

This list is reused for:

- REST CORS (`SecurityConfig`)
- WebSocket handshake allowed origins (`WebSocketConfig`)

For multiple frontend origins, prefer explicit YAML list entries.

## Authentication and Authorization

### Login flow

1. Frontend calls `POST /api/v1/auth/login`.
2. Backend validates credentials.
3. Backend returns `AuthResponse` with access/refresh tokens and role/email.
4. Frontend sends `Authorization: Bearer <accessToken>` for protected endpoints.

### Roles

- `ADMIN`: can call `POST /api/v1/auth/add-guard`, and all incident endpoints.
- `GUARD`: can call incident endpoints.

### Public routes

- `POST /api/v1/auth/login`
- Swagger docs endpoints
- `/ws` WebSocket handshake endpoints

### Seeded default admin

At startup (`DataSeeder`), if missing:

- email: `admin@system.com`
- password: `Admin@123`

## REST API

Base path: `/api/v1`

### Auth endpoints

#### `POST /api/v1/auth/login`

Request (`AuthRequest`):

```json
{
  "email": "admin@system.com",
  "password": "Admin@123"
}
```

Response (`AuthResponse`):

```json
{
  "accessToken": "jwt",
  "refreshToken": "jwt",
  "role": "ADMIN",
  "email": "admin@system.com"
}
```

#### `POST /api/v1/auth/add-guard` (ADMIN only)

Request (`AddGuardRequest`):

```json
{
  "firstname": "John",
  "lastname": "Doe",
  "email": "guard@example.com",
  "password": "Guard@123"
}
```

Response: same shape as `AuthResponse`.

### Incident endpoints

#### `GET /api/v1/incidents`

Auth: `ADMIN` or `GUARD`

Response: `List<IncidentResponse>`

`IncidentResponse` fields:

- `id` (UUID)
- `timestamp` (OffsetDateTime)
- `minioBucket` (string)
- `minioObjectKey` (string)
- `minioUrl` (string)
- `confidenceScore` (number)
- `status` (`PENDING`, `CONFIRMED`, `FALSE_POSITIVE`)
- `reviewedAt` (OffsetDateTime or null)
- `sourceAlertId` (UUID or null)
- `createdAt` (OffsetDateTime)
- `reviewedBy` (`ReviewedByResponse` or null)
- `camera` (`CameraResponse` or null)

`ReviewedByResponse`:

- `id` (Long)
- `firstname`
- `lastname`
- `email`
- `role`

`CameraResponse`:

- `id` (UUID)
- `name`
- `rtspUrl`
- `isActive`
- `facility` (`FacilityResponse`)

`FacilityResponse`:

- `id` (UUID)
- `name`
- `address`
- `createdAt` (LocalDateTime)

#### `PATCH /api/v1/incidents/{id}/resolve`

Auth: `ADMIN` or `GUARD`

Path param:

- `id` - incident UUID

Request (`IncidentResolveRequest`):

```json
{
  "confirmation": true
}
```

Behavior:

- `true` -> status becomes `CONFIRMED`
- `false` -> status becomes `FALSE_POSITIVE`

Response:

- `200 OK` with empty body

### Misc endpoint

#### `GET /`

Returns:

```text
Connection Successful
```

Note: this route is not in `permitAll`, so it still requires auth under current rules.

## WebSocket API

Protocol: STOMP over WebSocket

- Handshake endpoint: `/ws`
- Broker prefixes: `/topic`, `/queue`
- Application destination prefix: `/app`

Incident stream topic:

- Subscribe: `/topic/incidents`

Payload sent to subscribers:

- `IncidentResponse` JSON

When messages are published:

- after new incident creation from Kafka
- after incident resolution updates

Important:

- This is real-time pub/sub only.
- Historical incidents are **not replayed** through WebSocket.
- Frontend should first call `GET /api/v1/incidents`, then subscribe.

## Kafka Integration

Consumer:

- Listener: `HarassmentAlertConsumerService`
- Topic: `violence-alerts` (hardcoded in `@KafkaListener`)
- Group: `harassment`

Incoming event DTO (`HarassmentAlertEvent`):

- `alert_id` (UUID)
- `camera_id` (UUID)
- `bucket` (string)
- `object_key` (string)
- `violence_score` (double)
- `threshold` (double)
- `inferred_at` (OffsetDateTime)

Error handling:

- Retries configured with `DefaultErrorHandler` + fixed backoff
- Failed records are routed to `<topic>.DLT` partition `0`

## Caching

Redis cache configured in `CacheConfig`:

- key serializer: `StringRedisSerializer`
- value serializer: `GenericJacksonJsonRedisSerializer`
- TTL: 12 seconds

Service usage:

- `GET /api/v1/incidents` is cached (`alert:camera::all`)
- cache is evicted on:
  - new incident save
  - incident resolve

## Audit Logs (`logs` table)

The backend persists audit/operational events into `logs`:

- `id` (`bigserial`)
- `created_at` (`timestamptz`)
- `actor_user_id` (nullable FK to `users`)
- `action` (`text`)
- `payload` (`jsonb`, nullable)

Current events written by code:

- `incident_confirmed` - incident resolved as confirmed
- `incident_false_positive` - incident resolved as false positive
- `kafka_consumer_error` - Kafka consumer failed to process a record

Payload examples:

- Incident actions: `incidentId`, `status`, `cameraId`, `sourceAlertId`
- Kafka errors: `topic`, `partition`, `offset`, `timestamp`, `error`

## Database Model

Primary entities:

- `users`
- `facilities`
- `cameras`
- `incidents`
- `logs`

Important relationships:

- `Camera` many-to-one `Facility`
- `Incident` many-to-one `Camera`
- `Incident.reviewedBy` many-to-one `User` (nullable)

## Frontend Integration Notes

Recommended frontend flow:

1. Login -> store `accessToken`.
2. Fetch initial incidents via `GET /api/v1/incidents`.
3. Open STOMP connection to `/ws`.
4. Subscribe to `/topic/incidents`.
5. Upsert incoming incidents by `id`.
6. Resolve actions call `PATCH /api/v1/incidents/{id}/resolve`.

Authorization header for protected REST:

```http
Authorization: Bearer <accessToken>
```

WebSocket auth:

- Current setup allows handshake by origin whitelist.
- No custom STOMP token interceptor is implemented yet.

## Known Limitations and Caveats

- `refreshToken` is returned, but no refresh endpoint exists.
- Kafka listener topic is hardcoded (`violence-alerts`) while another topic name is also configured via yaml; keep this aligned.
- Duplicate handling in consumer currently acknowledges duplicate but does not `return`, so save path still executes.
- `IncidentResolveRequest.confirmation` is nullable `Boolean`; null may cause runtime issues in ternary logic.
- REST validation annotations are minimal; error format may be default Spring behavior.

## Troubleshooting

### Application fails on startup with missing placeholders

Check required env vars:

- `KAFKA_SERVER_URL`
- `KAFKA_TOPIC`
- `MINIO_URL`
- DB/Redis settings as needed

### Port already in use

Backend default port is `8000`. Stop conflicting process or change `server.port`.

### WebSocket connects but no old incidents appear

Expected behavior. WebSocket sends live updates only.
Use `GET /api/v1/incidents` for initial history.

### Kafka DLT errors

Ensure `<topic>.DLT` exists and producer can write to it.

### Camera not found while consuming alerts

`camera_id` from Kafka must exist in `cameras.id` (UUID).
Insert facility + camera seed data before sending test events.

