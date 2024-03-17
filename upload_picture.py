# -*- coding=utf-8
import configparser
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import requests
import logging
import sys

class PictureUploader:
    def __init__(self, config_path='uploader_config.ini'):
        """
        从配置文件初始化上传器配置
        :param config_path: 配置文件路径
        """
        config = configparser.ConfigParser()
        config.read(config_path)
        
        self.secret_id = config.get('COS', 'SecretId')
        self.secret_key = config.get('COS', 'SecretKey')
        self.region = config.get('COS', 'Region')
        self.token = config.get('COS', 'Token') if config.has_option('COS', 'Token') else None
        self.domain = config.get('COS', 'Domain')
        self.bucket_name = config.get('COS', 'BucketName')
        
        cos_config = CosConfig(Region=self.region, SecretId=self.secret_id, SecretKey=self.secret_key, Token=self.token, Domain=self.domain)
        self.client = CosS3Client(cos_config)

    def upload_picture(self, pic_url):
        """
        上传图片到指定存储桶
        :param pic_url: 图片的URL
        :return: 上传后的文件访问路径
        """
        object_key = "blog/" + pic_url.split("/")[-1]
        stream = requests.get(pic_url)
        self.client.put_object(
            Bucket=self.bucket_name,
            Body=stream.content,
            Key=object_key,
        )
        location = f"https://{self.domain}/{object_key}"
        return location

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    uploader = PictureUploader(config_path='uploader_config.ini')
    pic_url = "https://pic3.zhimg.com/v2-fefa671cb2745731e43b694e6ff8e8be_b.jpg"
    response_location = uploader.upload_picture(pic_url)
    print(f"Uploaded picture location: {response_location}")