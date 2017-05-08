from model_filer import Filer

from pytest import raises
import shutil
import os
import sys

# SET UP
# make temporary directories here.
here = os.path.dirname(os.path.realpath(__file__))
local_dir = os.path.join(here, 'local')
os.makedirs(local_dir)
remote_dir = os.path.join(here, 'remote')
os.makedirs(remote_dir)

try:
    # Test custructor... #####################################################

    # bad remote option should raise
    with raises(ValueError):
        Filer(local_dir, remote_dir, remote_type='foo')

    # bad local or remote dir should raise on object creation
    with raises(FileNotFoundError):
        Filer('badlocaldir', remote_dir)
    with raises(FileNotFoundError):
        Filer(local_dir, 'badremotedir')

    # create real object now for test...
    fl = Filer(local_dir, remote_dir)

    # Test object dump #######################################################
    # (starting from blank local and remote)

    # Add an object to registry
    dummy_object = "hello!"
    fl.dump(dummy_object, 'dummy_object')
    # should now be in local but not remote.
    fl.dump(dummy_object, 'dummy_obj_2', push=True)
    # should be in local and remote

    # Test overwriting... starting with 1 file local and other remote
    with raises(ValueError):
        fl.dump(dummy_object, 'dummy_object')
    fl.dump(dummy_object, 'dummy_object', overwrite=True)
    # should reset the timestamp
    fl.dump(dummy_object, 'dummy_obj_2', overwrite=True)
    # should reset the timestamp and change the file to "local" since push wasn't called
    fl.dump(dummy_object, 'dummy_obj_2', overwrite=True, push=True)
    # should reset the timestamp, change to 'remote', and create a different pushed version of the file.

    # # make a new filer and it should read the existing registry
    fl = Filer(local_dir, remote_dir)


    # Test push/pull #########################################################
    with raises(ValueError):
        fl.push('badobjectname')
    with raises(ValueError):
        fl.pull('badobjectname')

    fl.dump(dummy_object, 'dummy_object', overwrite=True)
    # should be local at this point...
    fl.push('dummy_object')
    # should have status "remote"
    with raises(ValueError):
        fl.push('dummy_object')
    fl.pull('dummy_object') # won't do anything
    os.remove(os.path.join(local_dir, 'dummy_object.flr'))
    fl.pull('dummy_object')
    assert os.path.isfile(os.path.join(local_dir, 'dummy_object.flr'))

    fl.dump(dummy_object, 'dummy_object', overwrite=True)
    # should reset so the file is local at this point...
    with raises(ValueError):
        fl.pull('dummy_object')
    # example of missing locals after git clone...
    os.remove(os.path.join(local_dir, 'dummy_object.flr'))
    with raises(FileNotFoundError):
        fl.push('dummy_object')  # may want to catch this error and provide friendlier error message

    fl.dump(dummy_object, 'dummy_object', overwrite=True)
    fl.dump(dummy_object, 'dummy_obj_2', overwrite=True)
    # both local now
    fl.push_all()
    # both remote now
    os.remove(os.path.join(local_dir, 'dummy_object.flr'))
    os.remove(os.path.join(local_dir, 'dummy_obj_2.flr'))
    fl.pull_all()
    assert os.path.isfile(os.path.join(local_dir, 'dummy_object.flr'))
    assert os.path.isfile(os.path.join(local_dir, 'dummy_obj_2.flr'))

    # Test object load #######################################################

    fl.dump(dummy_object, 'dummy_object', overwrite=True, push=True)
    # should be synced now
    assert fl.load('dummy_object') == dummy_object
    os.remove(os.path.join(local_dir, 'dummy_object.flr'))
    assert fl.load('dummy_object') == dummy_object
    assert os.path.isfile(os.path.join(local_dir, 'dummy_object.flr'))

    fl.show_files()

except:
    # tear down
    shutil.rmtree(local_dir)
    shutil.rmtree(remote_dir)
    raise

# TEAR DOWN
shutil.rmtree(local_dir)
shutil.rmtree(remote_dir)
