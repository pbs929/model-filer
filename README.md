use dill at first, maybe add others later...

outline:

Training a model:
Instead of saving a pickle, save a file object (wrapper)
pickle.dump  dill.dump  -> filer.dump
Writes to a .pkl file with provided name
optionally pushes to remote.
-> option: local or remote
-> option: overwrite exiting file

if local, adds to the registry of model objects, but with a flag indicating that it doesn't exist remotely.
if remote, adds to the registry and pushes off, noting that it now exists remotely.

registry should exist in a file .file_registry

the model_filer should get initialized with a directory where it is looking for things
and with a backend method - are things going to S3?  what is the connection point, etc.?
should have methods for listing the available files and whether they are remote, local, or synced.
method to list mapping of filenames to remote addresses
method to sync all files or one by name

Loading a model:
Load it by name - check the registry if it exists, first.
Then if it exists but has not been "synced" (downloaded), download it
load it like any other pickle file
Option: only use local files (do not download; raise error or warning instead)

CLI
- push a given file to remote (assume registry file in same directory)
