from google.cloud import storage
import main

storage_client = storage.Client(project = main.PROJECT_NAME)
bucket = storage_client.get_bucket(main.BUCKET_NAME)

def save_pet_picture(image_file, image_name):
	try:
		blob = bucket.blob('{}.jpg'.format(image_name))
		blob.upload_from_string(image_file.read(), content_type=image_file.content_type)
		blob.make_public()
	
		return blob.public_url
	except Exception as err:
		raise err