FROM bitnami/spark:3.2.0
USER root
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /opt/bitnami/spark/jars && \
    chown -R 1001:1001 /opt/bitnami/spark/jars && \
    chmod -R 775 /opt/bitnami/spark/jars
RUN curl -o /opt/bitnami/spark/jars/spark-sql-kafka-0-10_2.12-3.2.0.jar \
    https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.2.0/spark-sql-kafka-0-10_2.12-3.2.0.jar && \
    curl -o /opt/bitnami/spark/jars/kafka-clients-2.8.0.jar \
    https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/2.8.0/kafka-clients-2.8.0.jar && \
    curl -o /opt/bitnami/spark/jars/spark-cassandra-connector_2.12-3.0.1.jar \
    https://repo1.maven.org/maven2/com/datastax/spark/spark-cassandra-connector_2.12/3.0.1/spark-cassandra-connector_2.12-3.0.1.jar && \
    curl -o /opt/bitnami/spark/jars/cassandra-driver-core-3.10.2.jar \
    https://repo1.maven.org/maven2/com/datastax/cassandra/cassandra-driver-core/3.10.2/cassandra-driver-core-3.10.2.jar && \
    curl -o /opt/bitnami/spark/jars/mongo-spark-connector_2.12-10.1.1.jar \
    https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/10.1.1/mongo-spark-connector_2.12-10.1.1.jar
RUN pip install --no-cache-dir py4j pymongo cassandra-driver kafka-python
COPY . /app/
USER 1001
CMD ["python", "streaming_job.py"]