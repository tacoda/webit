import boto3
import click

session = boto3.Session()
s3 = session.resource('s3')

@click.command('list-buckets')
def list_buckets():
    "List all S3 buckets"
    for bucket in s3.buckets.all():
        print(bucket)

if __name__ == '__main__':
    list_buckets()
