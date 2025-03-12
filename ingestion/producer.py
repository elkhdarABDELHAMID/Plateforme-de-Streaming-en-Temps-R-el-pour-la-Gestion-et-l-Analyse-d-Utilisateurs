import json
import time
import logging
import requests
from kafka import KafkaProducer
from retry import retry

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('random-user-producer')

# Configuration du producteur Kafka
def create_kafka_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=lambda x: json.dumps(x).encode('utf-8'),
            acks='all',
            retries=3
        )
        return producer
    except Exception as e:
        logger.error(f"Erreur lors de la création du producteur Kafka: {e}")
        raise

# Fonction pour appeler l'API Random User
@retry(tries=5, delay=10, backoff=2, max_delay=60)
def fetch_random_users(batch_size=10):
    try:
        response = requests.get(f"https://randomuser.me/api/?results={batch_size}")
        response.raise_for_status()  # Raise exception for non-200 status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors de l'appel à l'API Random User: {e}")
        raise

# Fonction principale qui récupère des données et les envoie à Kafka
def run():
    producer = create_kafka_producer()
    topic_name = 'random_user_data'
    batch_size = 10
    interval_seconds = 10
    
    logger.info(f"Démarrage du producteur pour le topic {topic_name}")
    
    try:
        while True:
            try:
                # Récupérer les données
                user_data = fetch_random_users(batch_size)
                logger.info(f"Récupéré {len(user_data['results'])} utilisateurs")
                
                # Enrichir avec timestamp d'ingestion
                user_data['ingestion_timestamp'] = int(time.time())
                
                # Envoyer à Kafka
                future = producer.send(topic_name, value=user_data)
                record_metadata = future.get(timeout=10)
                
                logger.info(f"Message envoyé au topic={record_metadata.topic}, partition={record_metadata.partition}, offset={record_metadata.offset}")
                
                # Attendre avant le prochain lot
                time.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle de production: {e}")
                time.sleep(interval_seconds)  # Attente même en cas d'erreur
    
    except KeyboardInterrupt:
        logger.info("Arrêt du producteur demandé")
    finally:
        producer.close()
        logger.info("Producteur fermé")

if __name__ == "__main__":
    # Attendre que Kafka soit prêt
    time.sleep(30)
    logger.info("Démarrage du script producteur")
    run()