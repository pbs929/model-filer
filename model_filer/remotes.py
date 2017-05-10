"""
A remote is an object capable writing and reading from a remote location.
Each should have an identical API.
"""
import os
import shutil
from uuid import uuid4

import boto3

class DriveRemote():
    def __init__(self, remote_specifier):
        # Here, the specifier is just a path to a directory
        self.path = remote_specifier
        if not os.path.isdir(self.path):
            raise FileNotFoundError("Local path '{}' is not a valid directory".format(self.path))

    def upload(self, name, local_file):
        unique_name = name + '_' + str(uuid4()) + '.pkl'
        remote_address = os.path.join(self.path, unique_name)
        shutil.copyfile(local_file, remote_address)
        return remote_address

    def download(self, local_file, remote_address):
        shutil.copyfile(remote_address, local_file)

    def delete(self, remote_address):
        os.remove(remote_address)


class S3Remote():
    def __init__(self, remote_specifier=None):
        # Here, the specifier is a path to an AWS creds file
        if remote_specifier is None:
            remote_specifier = '~/.aws/credentials'
        os.environ["AWS_SHARED_CREDENTIALS_FILE"] = remote_specifier
        self.s3_client = boto3.client('s3')

    def upload(self, name, local_file):
        unique_name = name + '_' + str(uuid4()) + '.pkl'
        self.s3_client.upload_file(local_file, 'ds-model-files', unique_name)
        return unique_name

    def download(self, local_file, remote_address):
        self.s3_client.download_file('ds-model-files', remote_address, local_file)

    def delete(self, remote_address):
        self.s3_client.delete_object(Bucket='ds-model-files', Key=remote_address)
