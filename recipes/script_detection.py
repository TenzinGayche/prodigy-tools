import boto3
import prodigy
import os
import logging

# s3 cofig
os.environ["AWS_SHARED_CREDENTIALS_FILE"] = "/home/ta4tsering/.aws/credentials"
s3 = boto3.resource("s3")
s3_client = boto3.client("s3")
BUCKET_NAME = "archive.tbrc.org"

# log config 
logging.basicConfig(
    filename="/usr/local/prodigy/logs/script_detection.log",
    format="%(levelname)s: %(message)s",
    level=logging.INFO,
    )

# Prodigy has a logger named "prodigy" according to 
# https://support.prodi.gy/t/how-to-write-log-data-to-file/1427/10
prodigy_logger = logging.getLogger('prodigy')
prodigy_logger.setLevel(logging.INFO)

@prodigy.recipe("script-detection-recipe")
def script_detection_recipe(dataset, s3_prefix):
    logging.info(f"dataset:{dataset}, s3_prefix:{s3_prefix}")
    obj_list = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=s3_prefix)
    if not obj_list:
        logging.error("no object in s3 prefix")
        raise "no object in s3 prefix"
    obj_keys = []
    for obj in obj_list['Contents']:
        obj_key = obj['Key']
        # TODO: filter non-image files
        obj_keys.append(obj_key)
    return {
        "dataset": dataset,
        "stream": stream_from_s3(obj_keys),
        "view_id": "blocks",
        "config": {
            "blocks": [
                {"view_id": "choice", "text": None}
                ]
            } 
        }

def stream_from_s3(obj_keys):
    options = [
        {"id": 2, "text": "Uchen"},
        {"id": 1, "text": "Ume"},
        {"id": 0, "text": "etc"}
    ]
    for obj_key in obj_keys:
        image_url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": BUCKET_NAME, "Key": obj_key},
            ExpiresIn=31536000
        )
        yield {"image": image_url, "options": options}