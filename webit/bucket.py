# -*- coding: utf-8 -*-

"""Classes for S3 Buckets"""

from functools import reduce
import mimetypes
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from hashlib import md5
import util


class BucketManager:
    """Manages an S3 Bucket"""

    CHUNK_SIZE = 8388608

    def __init__(self, session):
        """Create a BucketManager object"""
        self.session = session
        self.s3 = self.session.resource('s3')
        self.transfer_config = boto3.s3.transfer.TransferConfig(
            multipart_chunksize=self.CHUNK_SIZE,
            multipart_threshold=self.CHUNK_SIZE
        )
        self.manifest = {}

    def get_region_name(self, bucket):
        """Get the region name for this bucket"""
        bucket_location = self.s3.meta.client.get_bucket_location(Bucket=bucket.name)
        return bucket_location['LocationConstraint'] or 'us-east-1'

    def get_bucket_url(self, bucket):
        """Get the website URL for this bucket"""
        return "http://{}.{}".format(bucket.name, util.get_endpoint(self.get_region_name(bucket)).host)

    def all_buckets(self):
        """Get an iterator for all buckets"""
        return self.s3.buckets.all()

    def all_objects(self, bucket_name):
        """Get an iterator for all objects in a bucket"""
        return self.s3.Bucket(bucket_name).objects.all()

    def load_manifest(self, bucket):
        """Load manifest for caching purposes"""
        paginator = self.s3.meta.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket.name):
            for obj in page.get('Contents', []):
                self.manifest[obj['Key']] = obj['ETag']

    def get_bucket(self, bucket_name):
        """Get a bucket by name"""
        return self.s3.Bucket(bucket_name)

    @staticmethod
    def hash_data(data):
        """Generate md5 hash for data"""
        hash = md5()
        hash.update(data)
        return hash

    def generate_etag(self, path):
        """Generate etag for a file"""
        hashes = []
        with open(path, 'rb') as f:
            while True:
                data = f.read(self.CHUNK_SIZE)
                if not data:
                    break
                hashes.append(self.hash_data(data))
        if not hashes:
            return
        elif len(hashes) == 1:
            return '"{}"'.format(hashes[0].hexdigest())
        else:
            hash = self.hash_data(reduce(lambda x, y: x + y, (h.digest() for h in hashes)))
            return '"{}-{}"'.format(hash.hexdigest(), len(hashes))


    def init_bucket(self, bucket_name):
        """Create a new bucket or return an existing one by name"""
        # TODO: Handle botocore.errorfactory.NoSuchBucket
        try:
            if self.session.region_name == 'us-east-1':
                s3_bucket = self.s3.create_bucket(Bucket=bucket_name)
            else:
                s3_bucket = self.s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': self.session.region_name
                    })
        except ClientError as error:
            if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                s3_bucket = self.s3.Bucket(bucket_name)
            else:
                raise error
        return s3_bucket

    @staticmethod
    def set_policy(bucket):
        """Set bucket policy to be readable by everyone"""
        policy = """
            {
                "Version":"2012-10-17",
                "Statement":[{
                    "Sid":"PublicReadGetObject",
                    "Effect":"Allow",
                    "Principal":"*",
                    "Action":"s3:GetObject",
                    "Resource":"arn:aws:s3:::%s/*"
                }]
            }
            """ % bucket.name
        policy = policy.strip()
        pol = bucket.Policy()
        pol.put(Policy=policy)

    @staticmethod
    def configure_website(bucket):
        """Configure S3 website hosting for bucket"""
        bucket.Website().put(WebsiteConfiguration={
            'ErrorDocument': {
                'Key': 'error.html'
            },
            'IndexDocument': {
                'Suffix': 'index.html'
            }
        })

    def upload_file(self, bucket, path, key):
        """Upload path to s3_bucket at key"""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        etag = self.generate_etag(path)
        if self.manifest.get(key, '') == etag:
            print("Skipping {}, etags match".format(key))
            return
        bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': content_type
            },
            Config=self.transfer_config)

    def sync(self, pathname, bucket_name):
        """Sync contents of path to bucket"""
        # TODO: Handle boto3.exceptions.S3UploadFailedError
        # TODO: Delete the file from the bucket if it no longer exists in the local directory
        bucket = self.s3.Bucket(bucket_name)
        self.load_manifest(bucket)
        root = Path(pathname).expanduser().resolve()

        def handle_directory(target):
            for path in target.iterdir():
                if path.is_dir():
                    handle_directory(path)
                if path.is_file():
                    self.upload_file(bucket, str(path), str(path.relative_to(root)))

        handle_directory(root)
