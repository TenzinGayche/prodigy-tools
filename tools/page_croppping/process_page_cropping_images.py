from pathlib import Path
from tools.image_processing import ImageProcessing
from tools.config import s3_client1, page_cropping_bucket, PAGE_CROPPPING_BUCKET


_config = {
    "source_s3_client": s3_client1,
    "source_s3_bucket": page_cropping_bucket,
    "source_bucket_name": PAGE_CROPPPING_BUCKET,
    "target_s3_client": s3_client1,
    "target_s3_bucket": page_cropping_bucket,
    "target_bucket_name": PAGE_CROPPPING_BUCKET,
    "csv_name": "page_cropping"
}

input_s3_prefixs = (Path(f"./data/page_cropping/sample_images_batch1.txt").read_text(encoding='utf-8')).splitlines()


if __name__ == "__main__":
    processor = ImageProcessing(config=_config)
    for input_s3_prefix in input_s3_prefixs:
        processor.processed_and_upload_image_to_s3(input_s3_prefix)