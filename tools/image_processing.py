import gzip
import io
import logging
import math

from PIL import Image
from raw_pillow_opener import register_raw_opener

from tools.utils import (create_output_s3_prefix, get_s3_bits, is_archived,
                         update_catalog, upload_to_s3)

log_file = 'processing.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
formatter = logging.Formatter("%(asctime)s, %(levelname)s: %(message)s")
file_handler = logging.FileHandler(filename=log_file)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# register_raw_opener()

class ImageProcessing():
    def __init__(self, image_options={}, config={}):
        self.max_height = image_options['max_height'] if 'max_height' in image_options else 700
        self.max_width = image_options['max_width'] if 'max_width' in image_options else 2000
        self.png_for_1 = image_options['png_for_1'] if 'png_for_1' in image_options else True
        self.quality = image_options['quality'] if 'quality' in image_options else 75
        self.greyscale = image_options['greyscale'] if 'greyscale' in image_options else False
        self.progressive = image_options['progressive'] if 'progressive' in image_options else True
        self.degree = self.get_degree()
        self.origfilename = None
        self.new_filename = None
        self.output_s3_prefix = ""
        self.config = config
        
        
    def get_degree(self):
        angle = math.atan2(self.max_height, self.max_width)
        degree = math.degrees(angle)
        return int(degree)
        
        
    def upload_image(self, image, s3_bucket):
        s3_key = f"{self.output_s3_prefix}/{self.new_filename}"
        image_bytes = io.BytesIO()
        if self.new_filename.split(".")[-1] == "png":
            extention = "png"
        else:
            extention = "jpeg"
        image.save(image_bytes, extention)
        image_bytes.seek(0)
        image_data = image_bytes.read()
        upload_to_s3(image_data, s3_key, s3_bucket)
        return s3_key
        

    def get_new_filename(self, binary):
        if binary:
            self.new_filename = self.origfilename + "_" + str(self.max_width) + "x" + str(self.max_height) +".png"
        else:
            self.new_filename = self.origfilename + "_" + str(self.max_width) + "x" + str(self.max_height) + ".jpg"


    def resize_the_image(self, image):
        try:
            width, height = image.size
            aspect_ratio = width / height

            if aspect_ratio > 1:
                # Image is wider than the maximum dimensions
                new_width = self.max_width
                new_height = int(self.max_width / aspect_ratio)
            else:
                # Image is taller than the maximum dimensions
                new_height = self.max_height
                new_width = int(self.max_height * aspect_ratio)
            resized_img = image.resize((new_width, new_height))
            return resized_img
        except Exception as e:
            logger.exception(
                f"Image corrupted can't resize, error {e}: original filename: {self.origfilename}"
            )
            return


    def compress_and_encode_image(self, resized_image):
        # do cofigurable compression with input quality if given else 75 and do progressive encoding
        compressed_image_bytes = io.BytesIO()
        resized_image.save(compressed_image_bytes, format='JPEG', quality=self.quality, progressive=self.progressive)
        compressed_image = Image.open(compressed_image_bytes, formats=['JPEG'])
        # create new image to not include the metadata of compressed image
        new_image = Image.new(mode=compressed_image.mode, size=resized_image.size)
        new_image.putdata(list(compressed_image.getdata()))
        return compressed_image
    
    
    def process_non_binary_file(self, image):
        #resize the image
        resized_image = self.resize_the_image(image)
        if resized_image:
            if self.greyscale:
                resized_image = resized_image.convert("L")
            new_image = self.compress_and_encode_image(resized_image)
            return new_image
        return      

        
    def processs_image(self, filebits):
        # resize, compress and encode the image and return a processed image
        if filebits:
            if self.origfilename.split(".")[-1] == "CR2":
                register_raw_opener()
                try:
                    image = Image.open(filebits)
                except:
                    print("cannot open "+self.origfilename)
                    return
            elif self.origfilename.split(".")[-1] == "gz":
                decompressed_data = gzip.decompress(filebits.getvalue())
                image_bytes = io.BytesIO(decompressed_data)
                image = Image.open(image_bytes)
            else:
                image = Image.open(filebits)
        else:
            return
            
        if image.mode == '1' and self.png_for_1:
            self.get_new_filename(True)
            s3_key = f"{self.output_s3_prefix}/{self.new_filename}"
            if is_archived(s3_key, self.config):
                return
            image =  self.resize_the_image(image)
        else:
            self.get_new_filename(False)
            s3_key = f"{self.output_s3_prefix}/{self.new_filename}"
            if is_archived(s3_key, self.config):
                return
            image = self.process_non_binary_file(image)
        return image
    

    def processed_and_upload_image_to_s3(self, s3_image_key):
        self.output_s3_prefix = create_output_s3_prefix(s3_prefix=s3_image_key)
        self.origfilename = s3_image_key.split("/")[-1]
        print("process %s" % s3_image_key)
        if not self.png_for_1:
            # no need to get the s3 bits if no processing is necessary
            self.get_new_filename(False)
            s3_key = f"{self.output_s3_prefix}/{self.new_filename}"
            if is_archived(s3_key, self.config):
                return
        filebits, error = get_s3_bits(s3_image_key, self.config['source_s3_bucket'])
        if filebits == None:
            if error.response["Error"]["Code"] == "404":
                logger.exception(f"The object does not exist: s3__key: {s3_image_key}")
            else:
                logger.exception(f"The object didn't download due to error {error}: s3__key: {s3_image_key}")
                return
        processed_image = self.processs_image(filebits)
        if processed_image:
            s3_key = self.upload_image(processed_image, self.config['target_s3_bucket'])
            update_catalog(s3_key, self.config['csv_path'])