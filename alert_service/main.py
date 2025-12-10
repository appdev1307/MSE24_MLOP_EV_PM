from confluent_kafka import Consumer
import json
import os
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Prometheus metrics
ANOMALY_COUNT = Counter('anomaly_events_total', 'Total anomaly events')
FAULT_COUNT = Counter('fault_events_total', 'Total fault events')
RUL_GAUGE = Gauge('rul_estimated', 'Latest RUL estimate', ['host'])
FAILURE_PROB_HIST = Histogram('failure_probability', 'Failure probability histogram')

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
PRED_TOPIC = os.environ.get("PRED_TOPIC", "predictions")
GROUP = os.environ.get("ALERT_GROUP", "alert-service-group")
PROM_PORT = int(os.environ.get("PROM_PORT", "9101"))

conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP,
    'group.id': GROUP,
    'auto.offset.reset': 'earliest'
}

def start_consumer():
    c = Consumer(conf)
    c.subscribe([PRED_TOPIC])
    print("Alert Service subscribed to topic:", PRED_TOPIC)

    try:
        while True:
            msg = c.poll(timeout=1.0)
            if not msg:
                continue
            if msg.error():
                print("Kafka error:", msg.error())
                continue

            try:
                data = json.loads(msg.value().decode("utf-8"))
            except:
                continue

            pred = data.get('prediction', {})
            host = data.get('host', 'unknown')

            anomaly = pred.get('IF_Anomaly')
            is_fault = pred.get('is_fault')
            rul = pred.get('RUL_estimated')
            failure_prob = pred.get('failure_prob')

            if anomaly:
                ANOMALY_COUNT.inc()
            if is_fault:
                FAULT_COUNT.inc()
            if rul is not None:
                RUL_GAUGE.labels(host=host).set(float(rul))
            if failure_prob is not None:
                FAILURE_PROB_HIST.observe(float(failure_prob))

    except KeyboardInterrupt:
        pass
    finally:
        c.close()

if __name__ == "__main__":
    start_http_server(PROM_PORT)
    print(f"Prometheus metrics at :{PROM_PORT}/")
    start_consumer()
