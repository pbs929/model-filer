# ds_model_filer

A tool for managing large files for data science projects.

## Overview

In data science, we are used to the following workflow:
1. train a model
1. `pickle.dump()` it to disk
1. later, `pickle.load()` the model to use it (e.g. in production)

The problem is that step 3 is often performed by a different person and on a different machine from steps 1 and 2.
And while we can use git to version and share code, doing the same with model files is awkward for a couple of reasons:

* _Model size_ - Model files are often too large to check into Github.
Furthermore, since most production applications need only one model, downloading all available models when a repo is cloned is unnecesary.
It would be better to only retrieve the needed model files, at the time they are needed.
* _Immutability_ - Pickled models are finished products, and we typically want to use them and track their performance without altering them.
Attempting to version control them in git will lead to either an accumulation of large files in the repo, or worse, an accumulation of large diffs in the git history.

This package allows us to use the familiar train-dump-load workflow, but to check only a registry of large files into the repo, while storing the files themselves elsewhere.

### Basic usage

Here is an example of how we would create and "pickle" a model with remote storage on s3:
```python
>>> model = ...  # train a model
>>> local_dir = ...  # path to local directory for model storage
>>> remote_address = ...  # string specifying remote address of an s3 bucket

>>> from model_filer import Filer
>>> filer = Filer(local_dir, remote_address, remote_type='s3')
>>> filer.dump(model, 'my_model', push=True)  # create a pickle and push it to s3
```
Now, if we look in the `local_dir`, we will see a file `my_model.pkl` containing the pickled model.
We will also find a file `.s3_registry` that maps the name of the 'my_model' to an address in the s3 bucket can be retrieved.
We can easily check the contents of the registry file by running:
```python
>>> filer.show_files()
my_model (synced)
```
This shows us we currently have one model and it is in a "synced" state.
The "synced" label means that our model has already been pushed to the remote.
To keep track of our model file, we now simply check the `.s3_registry` (and NOT the pickle file) into git as part of our project.

Later, when we are ready to use or deploy our model, we can clone the repo and run
```python
>>> from model_filer import Filer
>>> filer = Filer(local_dir, remote_address, remote_type='s3')
>>> model = filer.load('my_model')
```
The filer will first check if the model exists already in the local directory, and if it does not, will download it from s3 before de-serializing.

### Local files

In the preceding example, we pickled our model and immediately pushed it to the s3 remote.
However, often when building a model we want to test drive the pickle file before committing to it in perpetuity.
In this case, we can do a local dump
```python
>>> filer.dump(model, 'my_model', push=False)
>>> filer.show_files()
my_model (local)
```
The "local" label shows that the pickle file exists in the local model directory but has not yet been synced to the remote.
Once we have tested our pickle file sufficiently, we can perform the push step:
```python
>>> filer.push('my_model')
>>> filer.show_files()
my_model (synced)
```
Alternatively, we can use the method `push_all()` to sync all local files in the registry.

Because local files cannot be retrieved by another user who has cloned the repo, a best practice is to eliminate all local files before checking the `.s3_registry` into git.
This can be done either by pushing them all to the remote, or by removing them via the `remove` and `remove_locals` methods (see below).

### Removing files

Files can be removed from the registry as follows:
```python
>>> filer.dump(model, 'my_model', push=False)
>>> filer.show_files()
my_model (local)

>>> filer.remove('my_model')
>>> filer.show_files()
[no files exist]
```
The `remove` method can also be used on files that are in a synced state.
However, by default the file is NOT removed from the remote, since references to the file may still exist in the registry somewhere in version control.
To force the removal of the remote file, the flag `remove_remote=True` must be passed.
Use this with caution!

A special convenience method `remove_locals` exists and is useful for cleaning all the local files from the registry before checking into git.

### Overwriting files

In some situations during local development, we may want to replace an existing model in the registry.
In these cases, we can call `filer.dump()` with the option `overwrite=True`.
This _cannot_ be done with files in a synced state.
To force an overwrite in this case, you must explicitly call `filer.remove(remove_remote=True)` followed by `filer.dump()`.
