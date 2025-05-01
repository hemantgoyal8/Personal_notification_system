# README Files for Microservices Architecture

---

## 1. `api-service/README.md`

```md
# API Service

## Overview

The API Service exposes REST endpoints for managing application data. It is built with FastAPI and MongoDB.

### Responsibilities
- Handle incoming HTTP requests
- Perform CRUD operations on MongoDB
- Publish messages to RabbitMQ for background processing

## Prerequisites

- Docker
- Docker Compose

## Installation & Setup (Docker)

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Ensure Docker and Docker Compose are installed**

3. **Start the services**
   ```bash
   docker-compose up --build
   ```

4. **Environment Variables**
   Update the `api-service/.env` file if needed:
   ```ini
   MONGODB_URI=mongodb://mongodb:27017/mydb
   RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
   ```

5. **Access the API**
   Visit: [http://localhost:8000/docs](http://localhost:8000/docs)

## Endpoints

| Method | Path            | Description                   |
|--------|-----------------|-------------------------------|
| GET    | /items/         | List all items                |
| POST   | /items/         | Create a new item             |
| GET    | /items/{id}     | Retrieve item details         |
| PUT    | /items/{id}     | Update an existing item       |
| DELETE | /items/{id}     | Delete an item                |

## Message Queue

- **Exchange**: `exchange.items`
- **Routing Key**: `item.created`, `item.updated`, `item.deleted`

When an item is created or updated, a message is published for asynchronous processing.
```

---

## 2. `worker-service/README.md`

```md
# Worker Service

## Overview

The Worker Service consumes messages from RabbitMQ to perform background tasks (e.g., sending notifications, data enrichment). It's implemented with FastAPI (for health-check endpoints) and Pika.

### Responsibilities
- Consume messages from RabbitMQ
- Execute long-running or non-blocking tasks
- Write results back to MongoDB or publish to other queues

## Architecture Diagram

```text
RabbitMQ --> Worker Service --> MongoDB
```

## Prerequisites

- Docker
- Docker Compose

## Installation & Setup (Docker)

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Ensure Docker and Docker Compose are installed**

3. **Start the services**
   ```bash
   docker-compose up --build
   ```

4. **Environment Variables**
   Update the `worker-service/.env` file if needed:
   ```ini
   MONGODB_URI=mongodb://mongodb:27017/mydb
   RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
   ```

5. **Worker runs automatically in the container**

## Health Check

The service exposes a health endpoint:

- GET `/health` → Returns 200 OK if connected to MongoDB and RabbitMQ.

## Consumed Queues

- `exchange.items` with routing keys `item.created`, `item.updated`, `item.deleted`

## Logging & Monitoring

- Logs are output to console in JSON format.
- Integrate with your preferred logging/monitoring solution.
```

---

## 3. `graphql-gateway/README.md`

```md
# GraphQL Gateway

## Overview

The GraphQL Gateway aggregates data from multiple microservices and presents a unified GraphQL API. Built with Strawberry GraphQL and communicates with the API and Worker services.

### Responsibilities
- Fetch data from REST and direct MongoDB calls
- Resolve mutations by forwarding to the API Service
- Subscribe to RabbitMQ for real-time updates

## Architecture Diagram

```text
Client --- GraphQL Gateway --- API Service
                       |             \
                       |              --> MongoDB
                       \
                        --> RabbitMQ --> Worker Service
```

## Prerequisites

- Docker
- Docker Compose

## Installation & Setup (Docker)

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Ensure Docker and Docker Compose are installed**

3. **Start the services**
   ```bash
   docker-compose up --build
   ```

4. **Environment Variables**
   Update the `graphql-gateway/.env` file if needed:
   ```ini
   API_URL=http://api-service:8000
   RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
   ```

5. **Access the GraphQL Playground**
   Visit: [http://localhost:8080/graphql](http://localhost:8080/graphql)

## Schema

- **Queries**
  - `items`: List items
  - `item(id: ID!)`: Get item by ID

- **Mutations**
  - `createItem(input: CreateItemInput!)`: Create a new item
  - `updateItem(id: ID!, input: UpdateItemInput!)`: Update an item

- **Subscriptions**
  - `onItemCreated`: Subscribe to new items
  - `onItemUpdated`: Subscribe to updates

## Real-time Updates

The gateway listens to RabbitMQ exchanges and pushes events over WebSockets to subscribed clients.
```

---

### Overall Architecture

1. **Client**: Web or mobile application consuming GraphQL API.
2. **GraphQL Gateway**: Single entrypoint, federates data and real-time events.
3. **API Service**: RESTful endpoints for CRUD, backed by MongoDB.
4. **Worker Service**: Background processing via RabbitMQ.
5. **MongoDB**: Primary data store.
6. **RabbitMQ**: Message broker for async tasks and subscriptions.

All services are containerized (Docker), orchestrated via Docker Compose or Kubernetes. Communication is secured using TLS and JWT for authentication.

