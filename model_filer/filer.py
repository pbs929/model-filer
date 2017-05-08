from .remotes import DriveRemote
from .registry import Registry

import dill
import os
from datetime import datetime

FILE_EXTENSION = '.pkl'


class Filer():
    """
    Main API object for the project.

    Parameters
    ----------
    local_path : string
        Path to a folder in the local file system where `.pkl` files will be
        stored
    remote_connection : string
        String specifying how to connect to the remote (varies by remote type)
    remote_type : 'drive' or 's3'
        String specifying what type of remote connection to use
    """
    def __init__(self, local_path, remote_connection, remote_type='drive'):
        # Validate local path
        if not os.path.isdir(local_path):
            raise FileNotFoundError("Local path '{}' is not a valid directory".format(local_path))
        self.local_path = local_path

        # Set up remote connection
        if remote_type == 'drive':
            self.remote = DriveRemote(remote_connection)
            registry_filename = '.drive_registry'
        elif remote_type == 's3':
            self.remote = S3Connection(remote_connection)
            registry_filename = '.s3_registry'
        else:
            raise ValueError("Unsupported remote type: {}".format(remote_type))

        # Create registry object
        self.registry = Registry(os.path.join(local_path, registry_filename))

    def _get_local_filename(self, name):
        return os.path.join(self.local_path, name + FILE_EXTENSION)

    def show_files(self):
        """
        Read the registry and display names and statuses.
        """
        for entry in self.registry.get_all_entries():
            print("{} ({})".format(entry.name, entry.status))

    def dump(self, obj, name, push=False, overwrite=False):
        """
        Pickle an object and add it to the registry.

        Parameters
        ----------
        obj : object
            The object to be pickled.
        name : string
            The name to be used to refer to the stored object.
        push : boolean (default False)
            If True, push to the remote immediately after registering.
        overwrite: : boolean (default False)
            If True, overwrite any existing file with the same name. Otherwise
            an error will be raised if a file exists with the name.
        """
        local_file = self._get_local_filename(name)
        # Handle overwriting
        registry_entry = self.registry.find_by_name(name)
        if registry_entry:
            if not overwrite:
                raise ValueError("Cannot write to name '{}': file already exists in registry".format(name))
            if registry_entry.status == 'synced':
                raise ValueError("Cannot overwrite file '{}' because it has already been pushed. ".format(name) +
                                 "To force overwrite, first remove existing registry entry and then retry.")
            if os.path.isfile(local_file):
                os.remove(local_file)
            self.registry.remove_entry(name)
        dill.dump(obj, open(local_file, 'wb'))
        timestamp = datetime.now().strftime("%Y-%m-%d::%H:%M:%S")
        self.registry.add_entry(name, 'local', None, timestamp)
        if push:
            self.push(name)
        # (what happens if this gets interrupted?)

    def load(self, name):
        """
        Load a pickled object from the registry.

        Parameters
        ----------
        name : string
            The name of the stored object.
        """
        registry_entry = self.registry.find_by_name(name)
        if not registry_entry:
            raise ValueError("File '{}' not found in registry".format(name))
        local_file = self._get_local_filename(name)
        if not os.path.isfile(local_file):
            if registry_entry.status == 'synced':
                self.pull(name)
            else:
                raise FileNotFoundError("Locally registered file '{}' not found".format(name))
        return dill.load(open(local_file, 'rb'))

    def push(self, name):
        """
        Push a file to the remote.
        """
        registry_entry = self.registry.find_by_name(name)
        if not registry_entry:
            raise ValueError("File '{}' not found in registry".format(name))
        if registry_entry.status == 'synced':
            raise ValueError("Cannot push file '{}'; already exists remotely".format(name))
        local_file = self._get_local_filename(name)
        address = self.remote.upload(name, local_file)
        # Update registry entry
        old_entry = self.registry.remove_entry(name)
        self.registry.add_entry(name, 'synced', address, old_entry.timestamp)

    def pull(self, name):
        """
        Pull a file from the remote.
        """
        registry_entry = self.registry.find_by_name(name)
        if not registry_entry:
            raise ValueError("File '{}' not found in registry".format(name))
        if registry_entry.status == 'local':
            raise ValueError("Cannot pull file {} from remote; file is marked 'local'".format(name))
        local_file = self._get_local_filename(name)
        if not os.path.isfile(local_file):
            self.remote.download(local_file, registry_entry.address)

    def push_all(self):
        """
        Push all local files to the remote.
        """
        for entry in self.registry.get_all_entries():
            if entry.status == 'local':
                self.push(entry.name)

    def pull_all(self):
        """
        Pull all available files from the remote.
        """
        for entry in self.registry.get_all_entries():
            local_file = self._get_local_filename(entry.name)
            if entry.status == 'synced' and not os.path.isfile(local_file):
                self.pull(entry.name)

    def remove(self, name, remove_remote=False):
        """
        Remove local copy and remove from the registry.

        By default, remote will not be removed in case
        it lives on in git history of the registry...
        """
        entry = self.registry.remove_entry(name)
        if remove_remote and (entry.status == 'synced'):
            self.remote.delete(entry.address)

    def remove_locals(self):
        """
        Useful for cleaning up before git checkin
        """
        for entry in self.registry.get_all_entries():
            if entry.status == 'local':
                self.remove(entry.name)
