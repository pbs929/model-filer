"""
A remote is an object capable writing and reading from a remote location.
Each should have an identical API.
"""
import os
import shutil
from uuid import uuid4

class DriveRemote():
    def __init__(self, path):
        if not os.path.isdir(path):
            raise FileNotFoundError("Local path '{}' is not a valid directory".format(path))
        self.path = path

    def upload(self, name, local_file):
        unique_name = name + '_' + str(uuid4())
        remote_address = os.path.join(self.path, unique_name)
        shutil.copyfile(local_file, remote_address)
        return remote_address

    def download(self, local_filename, remote_address):
        shutil.copyfile(remote_address, local_filename)

    def delete(self, remote_address):
        os.remove(remote_address)
