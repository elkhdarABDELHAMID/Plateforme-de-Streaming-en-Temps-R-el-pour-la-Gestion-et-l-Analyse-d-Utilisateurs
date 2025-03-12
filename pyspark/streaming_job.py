# Fichier: ./pyspark/streaming_job.py
import logging
import socket
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pyspark-streaming")

def wait_for_service(service_name, host, port, max_attempts=15, wait_time=5):
    for attempt in range(max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, int(port)))
            sock.close()
            logger.info(f"الخدمة {service_name} متاحة على {host}:{port}!")
            return True
        except socket.error as e:
            logger.warning(f"محاولة {attempt + 1}/{max_attempts}: {service_name} غير متاح بعد... ({str(e)})")
            time.sleep(wait_time)
    logger.error(f"فشل الاتصال بـ {service_name} على {host}:{port} بعد {max_attempts} محاولات")
    return False

def main():
    logger.info("انتظار بدء تشغيل الخدمات الأخرى...")
    services = [
        ("Spark Master", "spark-master", 7077),
        ("Kafka", "kafka", 9092),
        ("MongoDB", "mongodb", 27017),
        ("Cassandra", "cassandra", 9042)
    ]
    for service_name, host, port in services:
        if not wait_for_service(service_name, host, port):
            raise Exception(f"غير قادر على الاتصال بـ {service_name}")

    try:
        spark = SparkSession \
            .builder \
            .appName("RandomUserStreaming") \
            .master("spark://spark-master:7077") \
            .config("spark.cassandra.connection.host", "cassandra") \
            .config("spark.cassandra.connection.port", "9042") \
            .config("spark.mongodb.output.uri", "mongodb://mongodb:27017/randomUserDB.randomUserCollection") \
            .config("spark.driver.host", "pyspark-streaming") \
            .config("spark.submit.deployMode", "client") \
            .config("spark.executor.memory", "1g") \
            .config("spark.driver.memory", "1g") \
            .config("spark.streaming.stopGracefullyOnShutdown", "true") \
            .getOrCreate()
        spark.sparkContext.setLogLevel("INFO")
        logger.info("تم تهيئة SparkSession بنجاح")
    except Exception as e:
        logger.error(f"فشل في تهيئة SparkSession: {str(e)}")
        raise

    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("age", IntegerType(), True),
        StructField("country", StringType(), True)
    ])

    try:
        df = spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka:9092") \
            .option("subscribe", "random_user_data") \
            .option("startingOffsets", "earliest") \
            .option("failOnDataLoss", "false") \
            .option("group.id", "pyspark-consumer-group") \
            .load()
        logger.info("تم الاتصال بـ Kafka بنجاح")
    except Exception as e:
        logger.error(f"فشل في الاتصال بـ Kafka: {str(e)}")
        raise

    parsed_df = df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    try:
        query_console = parsed_df \
            .writeStream \
            .outputMode("append") \
            .format("console") \
            .option("truncate", "false") \
            .option("checkpointLocation", "/checkpoints/checkpoint_console") \
            .start()
        logger.info("بدأت الكتابة إلى الـ Console بنجاح")
    except Exception as e:
        logger.error(f"فشل في الكتابة إلى الـ Console: {str(e)}")
        raise

    try:
        query_mongo = parsed_df \
            .writeStream \
            .outputMode("append") \
            .format("mongodb") \
            .option("uri", "mongodb://mongodb:27017/randomUserDB.randomUserCollection") \
            .option("checkpointLocation", "/checkpoints/checkpoint_mongo") \
            .start()
        logger.info("بدأت الكتابة إلى MongoDB بنجاح")
    except Exception as e:
        logger.error(f"فشل في الكتابة إلى MongoDB: {str(e)}")
        raise

    try:
        query_cassandra = parsed_df \
            .writeStream \
            .outputMode("append") \
            .format("org.apache.spark.sql.cassandra") \
            .option("keyspace", "random_user_keyspace") \
            .option("table", "users") \
            .option("checkpointLocation", "/checkpoints/checkpoint_cassandra") \
            .start()
        logger.info("بدأت الكتابة إلى Cassandra بنجاح")
    except Exception as e:
        logger.error(f"فشل في الكتابة إلى Cassandra: {str(e)}")
        raise

    try:
        spark.streams.awaitAnyTermination()
    except Exception as e:
        logger.error(f"خطأ في عملية البث: {str(e)}")
    finally:
        logger.info("إيقاف SparkSession")
        spark.stop()

if __name__ == "__main__":
    main()