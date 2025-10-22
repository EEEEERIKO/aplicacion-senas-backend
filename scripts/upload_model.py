#!/usr/bin/env python3
import boto3
import sys
import os

def upload(local_path, bucket, key):
    s3 = boto3.client('s3')
    with open(local_path, 'rb') as f:
        s3.upload_fileobj(f, bucket, key)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: upload_model.py <local_path> <bucket> <key>')
        sys.exit(1)
    upload(sys.argv[1], sys.argv[2], sys.argv[3])
