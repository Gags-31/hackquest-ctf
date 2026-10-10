"""Kafka producer/consumer stubs for real-time conversation streaming."""

try:
    from kafka import KafkaProducer, KafkaConsumer  # type: ignore

    def produce(topic: str, value: str):
        KafkaProducer(bootstrap_servers="localhost:9092").send(topic, value.encode())

    def consume(topic: str):
        return KafkaConsumer(topic, bootstrap_servers="localhost:9092")

except ImportError:

    def produce(topic: str, value: str):
        print(f"[kafka-stub] -> {topic}: {value}")

    def consume(topic: str):
        print(f"[kafka-stub] consuming {topic}")
        return []
