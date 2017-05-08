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

    # this should work fine...
    fl = Filer(local_dir, remote_dir)

    # bad remote option should raise
    with raises(ValueError):
        Filer(local_dir, remote_dir, remote_type='foo')

    # bad local or remote dir should raise on object creation
    with raises(FileNotFoundError):
        Filer('badlocaldir', remote_dir)
    with raises(FileNotFoundError):
        Filer(local_dir, 'badremotedir')

    # Test object dump #######################################################
    # (starting from blank local and remote)

    fl = Filer(local_dir, remote_dir)

    # Add an object to registry
    dummy_object = "hello!"
    fl.dump(dummy_object, 'dummy1')
    # dummy1 should now be in local but not remote (local state)
    fl.dump(dummy_object, 'dummy2', push=True)
    # dummy2 should be in local and remote (synced state)

    # (make a new filer and it should read the existing registry)
    fl = Filer(local_dir, remote_dir)

    # Test overwriting...
    # Overwriting file in local state...
    with raises(ValueError):
        fl.dump(dummy_object, 'dummy1')  # cannot write without overwrite flag
    fl.dump(dummy_object, 'dummy1', overwrite=True)
    # should have replaced the local file (check for new timestamp)
    fl.dump(dummy_object, 'dummy1', overwrite=True, push=True)
    # should have overwritten and pushed
    # Now overwriting file in synced state...
    with raises(ValueError):
        fl.dump(dummy_object, 'dummy1', overwrite=True)  # cannot overwrite something that is synced

    # Test push/pull #########################################################
    # bad object names should raise
    with raises(ValueError):
        fl.push('badobjectname')
    with raises(ValueError):
        fl.pull('badobjectname')

    # set up a local file...
    fl.remove('dummy1', remove_remote=True)
    fl.dump(dummy_object, 'dummy1', overwrite=True)
    # should be local at this point
    # test push/pull in the local scenario...
    with raises(ValueError):
        fl.pull('dummy1')
    fl.push('dummy1')
    # should now have status "synced"
    # testing push/pull in the synced scenario...
    with raises(ValueError):
        fl.push('dummy1')  # can't push when already synced
    fl.pull('dummy1')  # won't do anything
    # now remove local and pull to replace...
    os.remove(os.path.join(local_dir, 'dummy1.pkl'))
    fl.pull('dummy1')
    # recovered
    assert os.path.isfile(os.path.join(local_dir, 'dummy1.pkl'))

    # test case of missing locals after git clone...
    # reset the file to local status...
    fl.remove('dummy1', remove_remote=True)
    fl.dump(dummy_object, 'dummy1', overwrite=True)
    # should be local at this point
    os.remove(os.path.join(local_dir, 'dummy1.pkl'))
    with raises(FileNotFoundError):
        fl.push('dummy1')  # may want to catch this error and provide friendlier error message

    # test push_all/pull_all
    # set up two local files...
    fl.dump(dummy_object, 'dummy1', overwrite=True)
    fl.remove('dummy2', remove_remote=True)
    fl.dump(dummy_object, 'dummy2', overwrite=True)
    # both local now
    fl.push_all()
    # both should by synced now
    os.remove(os.path.join(local_dir, 'dummy1.pkl'))
    os.remove(os.path.join(local_dir, 'dummy2.pkl'))
    fl.pull_all()
    # both recovered
    assert os.path.isfile(os.path.join(local_dir, 'dummy1.pkl'))
    assert os.path.isfile(os.path.join(local_dir, 'dummy2.pkl'))

    # Test object load ################################################

    # set up synced state
    fl.remove('dummy1', remove_remote=True)
    fl.dump(dummy_object, 'dummy1', push=True)
    # should be synced now
    assert fl.load('dummy1') == dummy_object
    os.remove(os.path.join(local_dir, 'dummy1.pkl'))
    assert fl.load('dummy1') == dummy_object
    assert os.path.isfile(os.path.join(local_dir, 'dummy1.pkl'))

    # Test removal ####################################################
    # set up synced state
    fl.remove('dummy1', remove_remote=True)
    fl.dump(dummy_object, 'dummy1', push=True)
    # now remove...
    fl.remove('dummy1')
    # *should* leave an orphaned file in the remote
    # add back in synced state...
    fl.dump(dummy_object, 'dummy1', push=True)
    fl.remove('dummy1', remove_remote=True)
    # should have removed from remote

    # set up one local, one remote
    fl.dump(dummy_object, 'dummy1', overwrite=True, push=False)
    fl.remove('dummy2', remove_remote=True)
    fl.dump(dummy_object, 'dummy2', push=True)
    fl.remove_locals()
    # should have removed local but not remote
    fl.show_files()
    # At the end of this there should still be an orphaned dummy1 that is not in the registry.

except:
    # tear down
    shutil.rmtree(local_dir)
    shutil.rmtree(remote_dir)
    raise

# TEAR DOWN
shutil.rmtree(local_dir)
shutil.rmtree(remote_dir)
