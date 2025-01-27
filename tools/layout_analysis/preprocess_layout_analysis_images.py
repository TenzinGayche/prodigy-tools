from pathlib import Path

from tools.config import (BDRC_ARCHIVE_BUCKET, LAYOUT_ANALYSIS_BUCKET,
                          bdrc_archive_bucket, bdrc_archive_s3_client,
                          layout_analysis_bucket, layout_analysis_s3_client)
from tools.image_processing import ImageProcessing

_config = {
    "source_s3_client": bdrc_archive_s3_client,
    "source_s3_bucket": bdrc_archive_bucket,
    "source_bucket_name": BDRC_ARCHIVE_BUCKET,
    "target_s3_client": layout_analysis_s3_client,
    "target_s3_bucket": layout_analysis_bucket,
    "target_bucket_name": LAYOUT_ANALYSIS_BUCKET,
    "csv_path": "./data/Q3_layout_analysis_02.csv"
}

input_s3_prefixs = (Path(f"./data/layout_analysis/sample_images.txt").read_text(encoding='utf-8')).splitlines()


if __name__ == "__main__":
    processor = ImageProcessing(config=_config)
    for input_s3_prefix in input_s3_prefixs:
        processor.processed_and_upload_image_to_s3(input_s3_prefix)