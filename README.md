# Test Snowpipe Streaming with a Kafka Event Generator

A free, local setup for learning the Snowflake Kafka Connector. No production cluster, no upstream team and no live feed are needed. Confluent Datagen produces fake `orders` events into a local Kafka topic, and the Snowflake Kafka Connector streams them into a Snowflake table with Snowpipe Streaming.

```
Datagen (source connector) ──► Kafka topic "orders" ──► Snowflake connector (sink) ──► Snowpipe Streaming ──► ORDERS table
└──────────── both run inside Kafka Connect, in Docker on your machine ────────────┘
```

## What's inside

| Path | Purpose |
|---|---|
| `docker/docker-compose.yml` | Single-node Kafka (KRaft, no ZooKeeper) and Kafka Connect |
| `docker/Dockerfile.connect` | Connect image with the Datagen and Snowflake plugins installed |
| `connect/datagen-orders.json` | Datagen connector config (the `orders` template) |
| `connect/snowflake-sink.template.json` | Snowflake sink config template (no secrets) |
| `snowflake/setup.sql` | Database, schema, role, user and grants |
| `scripts/` | Helpers to build the sink config and check rows in Snowflake |

## Prerequisites

- Docker Desktop (or Docker Engine with Compose v2)
- A Snowflake account where you can create a database, role and user
- Python 3.9+ with `snowflake-connector-python` and `cryptography` (only for the helper scripts)
- `openssl`

## 1. Create a key pair (Snowpipe Streaming requires key-pair auth)

```bash
mkdir -p keys
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -nocrypt -out keys/rsa_key.p8
openssl rsa -in keys/rsa_key.p8 -pubout -out keys/rsa_key.pub
```

`keys/` is git-ignored. Never commit a private key.

## 2. Prepare Snowflake

Open `snowflake/setup.sql`, paste the body of `keys/rsa_key.pub` (without the `BEGIN`/`END` lines) into `RSA_PUBLIC_KEY`, and run it as `ACCOUNTADMIN`.

## 3. Start Kafka and Kafka Connect

```bash
cd docker
docker compose up -d --build
```

Check that both are up:

```bash
docker exec kafka kafka-broker-api-versions --bootstrap-server kafka:9092   # Kafka is listening
curl http://localhost:8083/                                                 # Connect is up (takes about a minute)
```

## 4. Start the event generator

`curl` talks to Kafka Connect (port 8083), and Connect writes to Kafka.

```bash
curl -X POST -H "Content-Type: application/json" \
  --data @connect/datagen-orders.json http://localhost:8083/connectors
```

Verify that Kafka is producing events:

```bash
docker exec kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic orders --from-beginning --max-messages 5
docker exec kafka kafka-get-offsets --bootstrap-server kafka:9092 --topic orders   # run twice, the count rises
```

## 5. Start the Snowflake sink

The connector takes the private key inline in its config, so generate the config from the template. The generated file contains your key and is git-ignored.

```bash
export SNOWFLAKE_ACCOUNT=<orgname-accountname>
python scripts/generate_snowflake_config.py

curl -X POST -H "Content-Type: application/json" \
  --data @connect/snowflake-sink.generated.json http://localhost:8083/connectors
curl http://localhost:8083/connectors/snowflake-sink-orders/status
```

The connector creates the `ORDERS` table and its pipe on its own. Then check Snowflake:

```sql
SELECT COUNT(*) FROM KAFKA_DEMO.STREAMING.ORDERS;
SELECT ORDERID, ITEMID, ADDRESS:city::string AS city FROM KAFKA_DEMO.STREAMING.ORDERS LIMIT 10;
```

Or run `python scripts/check_orders.py` (grant the optional warehouse and select privileges in `setup.sql` first).

## Notes

- Version 4.x of the Snowflake connector ships only `SnowflakeStreamingSinkConnector`. The `SnowflakeSinkConnector` class from older tutorials does not exist, and the config differs.
- The scripts read `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_KEY_PATH` (default `keys/rsa_key.p8`), `SNOWFLAKE_USER` and `SNOWFLAKE_ROLE`.
- Connect keeps your connector configs in its own Kafka topic, so a restart does not require re-posting them. This includes the private key. Treat the local containers as sensitive.

## Clean up

```bash
curl -X DELETE http://localhost:8083/connectors/datagen-orders
curl -X DELETE http://localhost:8083/connectors/snowflake-sink-orders
cd docker && docker compose down
```

Drop `KAFKA_DEMO`, the role and the user in Snowflake when you are done.

## Third-party components

This repository contains only its own configuration and scripts. It does not redistribute the software below. The images and plugins are downloaded when you build, and each has its own license:

- Confluent Platform images (`cp-kafka`, `cp-kafka-connect`). Check Confluent's licensing, since some components use the Confluent Community License.
- Confluent Datagen connector (`confluentinc/kafka-connect-datagen`)
- Snowflake Kafka Connector (`snowflakeinc/snowflake-kafka-connector`)

Review them for your own use.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
