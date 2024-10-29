from google.cloud import storage

def upload_to_gcs(bucket_name, source_file_path, destination_blob_name):

    public_urls = []

    # Initialize the storage client
    storage_client = storage.Client()

    # Get the bucket
    bucket = storage_client.bucket(bucket_name)

    # Create a blob object and upload the file
    try:
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path)
        #print(f"File {source_file_path} uploaded to gs://{bucket_name}/{destination_blob_name}")
        public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
        public_urls.append(public_url)
        return public_urls
    except Exception as e:
        print(f"An error occurred: {e}")


# Usage example
bucket_name = "bucket-quickstart_maxs-first-project-408116"
source_file_path = "/Users/maxmodlin/maxdev/theah-mvp/templates/generation.json"
destination_blob_name = "client_uploads/generation.json"

p = upload_to_gcs(bucket_name, source_file_path, destination_blob_name)
print(p)


export GOOGLE_APPLICATION_CREDENTIALS="/Users/maxmodlin/maxdev/theah-mvp/maxs-first-project-408116-ea16fdbe2f7a.json"