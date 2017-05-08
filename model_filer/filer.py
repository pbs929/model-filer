"""
the model_filer should get initialized with a directory where it is looking for things
and with a backend method - are things going to S3?  what is the connection point, etc.?
should have methods for listing the available files and whether they are remote, local, or synced.
method to list mapping of filenames to remote addresses
method to sync all files or one by name

We don't ever delete from the remote; each file there will potentially
correspond to a file registered somewhere in version control.
The best thing would be to sync at the moment that the registry file
is _checked in_.

file can be 'local' or 'synced'
should have local/remote addresses, timestamp
"""
from .remotes import DriveConnection
from .registry import Registry
import dill
import os
from datetime import datetime

FILE_EXTENSION = '.pkl'


class Filer():
    """
    local_path - path to a folder in the local file system where files will be
        stored
    """

    def __init__(self, local_path, remote_connection_path, remote_type='drive'):
        # Validate local path
        if not os.path.isdir(local_path):
            raise FileNotFoundError("Local path '{}' is not a valid directory".format(local_path))
        self.local_path = local_path

        # Set up remote connection
        if remote_type == 'drive':
            self.remote = DriveConnection(remote_connection_path)
            registry_filename = '.drive_registry'
        elif remote_type == 's3':
            self.remote = S3Connection(remote_connection_path)
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

    def load(self, name, pull=True):
        """
        Load a pickled object from the registry.

        Parameters
        ----------
        name: string
            The name of the stored object.
        pull : boolean (default True)
            If True, the file will be pulled from the remote if it does not
            exist locally. Otherwise and error will be thrwon if it does not
            exist locally.
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
        Useful for cleaning up before git checking
        """
        for entry in self.registry.get_all_entries():
            if entry.status == 'local':
                self.remove(entry.name)
