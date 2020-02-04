from google.cloud import datastore
from google.cloud import bigquery
import datetime
import main

datastore_client = datastore.Client(main.PROJECT_NAME)


def get_pets():
    query = datastore_client.query(kind='Pet')
    query.order = ['-likes']
    pets = list(query.fetch())
    return pets


def add_like(pet_id):
    key = datastore_client.key("Pet", pet_id)
    pet = datastore_client.get(key)

    if("likes" in pet):
        pet['likes'] += 1
    else:
        pet['likes'] = 1

    print("{} has been liked {} times.".format(pet['petname'], pet['likes']))
    datastore_client.put(pet)
    return pet


def search_pets(search_term):
    bigquery_client = bigquery.Client()

    query_params = [bigquery.ScalarQueryParameter('search_term',
                                                  'STRING',
                                                  search_term.lower())]
    job_config = bigquery.QueryJobConfig()
    job_config.query_parameters = query_params

    query_job = bigquery_client.query("""SELECT DISTINCT pet_id  FROM `pets_dataset.pet_labels` WHERE REGEXP_CONTAINS(LOWER(label), @search_term) LIMIT 20 """,
    location='US',
    job_config=job_config)

    results = query_job.result()
    keys = []
    for row in results:
        key = datastore_client.key("Pet", row.pet_id)
        keys.append(key)

    pets = datastore_client.get_multi(keys)
    return pets


def save_pet(data, image_name):
    kind = 'Pet'
    id = image_name
    key = datastore_client.key(kind, id)
    pet = datastore.Entity(key=key)

    pet['added'] = datetime.datetime.now()
    pet['image'] = 'https://storage.googleapis.com/{}/{}.jpg'.format(main.BUCKET_NAME, image_name) 
    pet['likes'] = 0
    for prop, val in data.items():
        pet[prop] = val
    datastore_client.put(pet)
