#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""WebIt: Deploy websites with AWS

WebIt automates the process of deploying static websites to AWS.
- Configure AWS S3 buckets
    - Create them
    - Set them up for static website hosting
    - Deploy local files to them
- Configure DNS with AWS Route 53
- Configure a CDN and SSL with AWS CloudFront
"""

import boto3
import click

from bucket import BucketManager

session = boto3.Session()
bucket_manager = BucketManager(session)


@click.group()
def cli():
    """WebIt deploys websites to AWS"""


@cli.command('list-buckets')
def list_buckets():
    """List all S3 buckets"""
    for bucket in bucket_manager.all_buckets():
        print(bucket)


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List objects in an S3 bucket"""
    for obj in bucket_manager.all_objects(bucket):
        print(obj)


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """Create and configure S3 bucket"""
    s3_bucket = bucket_manager.init_bucket(bucket)
    bucket_manager.set_policy(s3_bucket)
    bucket_manager.configure_website(s3_bucket)
    return


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents of PATHNAME to BUCKET"""
    bucket_manager.sync(pathname, bucket)


if __name__ == '__main__':
    cli()
