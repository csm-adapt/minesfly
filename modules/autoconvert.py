
# coding: utf-8

# # Summary/Overview
# 
# This script looks for .TXM files, extracts the pixel size information and stores the tomography in an HDF5 file.
# The structure of this file is guaranteed to contain:
# 
# ```
#     /tomograph
#     /tomograph.attrs["pixel size"]
# ```
# 
# It is stored with the same name as the original .TXM file, but with an .hdf5 file extension. If the .hdf5 file
# already exists, no conversion is performed.

# In[1]:

import os, sys
orsProgramData = os.path.join(os.environ['ProgramData'], 'ORS', 'Dragonfly30', 'python')
sys.path.append(orsProgramData)
sys.path.append('C:\Program Files\Dragonfly')
os.system('registerDLLs.bat')
import logging, time
from glob import glob
import re
import numpy as np
import h5py
from OrsPlugins.orsimageloader import OrsImageLoader
from OrsPlugins.orsimagesaver import OrsImageSaver


# In[2]:

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logging.basicConfig(format='[%(asctime)s](%(levelname)s) %(message)', datefmt='%m/%d/%Y %I:%M:%S %p')


def info(fmt, *pos):
    # logging.info(fmt, *pos)
    print('[{}](INFO): '.format(time.asctime(time.gmtime())) + fmt % pos)
    sys.stdout.flush()


def debug(fmt, *pos):
    # logging.debug(fmt, *pos)
    print('[{}](DEBUG): '.format(time.asctime(time.gmtime())) + fmt % pos)
    sys.stdout.flush()


# ## User input

def txm_to_hdf5(searchdir, destination, exclude=tuple(), destdepth=-1):
    """
    Tracks a folder recursively looking for TXM files, converts these to
    HDF5 files, and stores the pixel size, in microns, in the attributes.

    :param searchdir: (string) Parent directory from which the search is conducted
    :param destination: (string) Destination directory where the results are stored.
    :param exclude: (list) regular expressions for files to ignore. Default: []
        Example: `re.compile(r'(warmup|warm-up|warm)', re.I)  # do not include warmup files.`
    :param destdepth: (int) depth of the search directory hierarchy to reproduce in the destination.
        Default: -1 (full reproduction). Example: `destdepth=0` all output will be written to the
        destination folder
    :return: None
    """

    # In[3]:

    # get the directory in which to search for new TXM files
    assert os.path.isdir(searchdir)
    # specify the parent directory where the converted files will live
    if os.path.exists(destination):
        assert os.path.isdir(destination)
    destparent = destination
    # glob pattern to search
    searchstr = "{}/**/*.txm".format(searchdir)

    # ## Overview
    #
    # 1. Use `glob` to search `searchdir` for all .TXM files $\rightarrow$ `txm_files`
    # 2. From `txm_files`, construct corresponding .hdf5 filenames $\rightarrow$ `hdf5_files`
    # 3. Keep from `txm_files` and `hdf5_files` only those filenames where
    #    the filename in `hdf5_files` does *not* exist.
    # 4. For each TXM/HDF5 file pair:
    #
    #    1. read file $\rightarrow$ `channel`
    #    2. extract pixel size $\rightarrow$ `pixelsize`
    #    3. create numpy array from `channel` $\rightarrow$ `data`
    #    3. open HDF5 file for writing $\rightarrow$ `h5`
    #    3. create HDF5 dataset from `data` $\rightarrow$ `h5["tomograph"]`
    #    5. write `pixelsize` to `h5["tomograph"].attr["pixel size"]`
    #    6. close HDF5 file
    #    7. delete new channel

    # In[4]:

    # get all .txm files from the working directory
    txm_files = glob(searchstr, recursive=True)
    for exclusion in exclude:
        txm_files = [txm for txm in txm_files if not re.search(exclusion, txm)]

    # In[5]:

    # generate HDF5 filenames from TXM filenames.
    def is_network_path(path):
        return path.startswith('//')

    def split_path(path):
        if is_network_path(path):
            std_path = path.replace(os.sep, '/')
            return std_path.split('/')
        else:
            return path.split(os.sep)

    def join_path(dir_list):
        return os.sep.join(dir_list)

    # skip the path leading up to the parent search directory
    search_start = len(split_path(searchdir))
    # include in the destination only the first `destdepth` entries
    search_end = search_start + destdepth
    # Convert the destination path to a list of folders. This makes
    # construction of the full path much easier
    split_path_to_destination = split_path(destparent)

    hdf5_files = []
    for txm in txm_files:
        # separate the filename from the path
        srcpath, ifile = os.path.split(txm)
        srcpath = split_path(srcpath)
        # construct HDF5 filename
        ofile = os.path.splitext(ifile)[0] + '.hdf5'
        # construct the list of folders starting with the full destination directory,
        # through the `destdepth` child folders from the search directory, finally excluding
        # the folders up to the parent folder in the search directory
        dstpath = split_path_to_destination + srcpath[search_start:search_end]
        # combine this newly created directory with the output filename
        ofile = join_path(dstpath + [ofile])
        # handle network paths
        if is_network_path(destparent):
            ofile = '//' + ofile.replace(os.sep, '/')
        # append the new filename to the list of hdf5_files
        hdf5_files.append(ofile)

    # In[6]:

    # keep only those txm/hdf5 files for which the hdf5 file does *not* already exist
    exists = [os.path.isfile(h5) for h5 in hdf5_files]
    txm_files = [txm for txm,complete in zip(txm_files, exists) if not complete]
    hdf5_files = [hdf for hdf,complete in zip(hdf5_files, exists) if not complete]

    # In[ ]:

    def create_directory_hierarchy(filename):
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except OSError as exc:  # Guard against race condition
                if exc.errno != OSError.errno.EEXIST:
                    raise
        return dirname

    # In[ ]:

    # process the files
    for txm,hdf in zip(txm_files, hdf5_files):
        try:
            info("Input: {}".format(txm))
            info("Output: {}".format(hdf))
            # read the file using Dragonfly/ORS ImageLoader
            try:
                channel = OrsImageLoader.createDatasetDeterminingGeometryFromFiles([txm])
                debug("TXM read successfully.")
            except:
                debug("TXM file ({}) failed to read. Skipping.".format(txm))
                raise
            # extract the pixel size
            pixelsize = channel.getXSpacing()*1e6  # convert pixel size to microns
            info("Pixel size: %f", pixelsize)
            # get the data as a numpy ndarray
            data = channel.getNDArray()
            debug("Extracted NDArray")
            # make sure the directory where this file will live actually exists
            path = create_directory_hierarchy(hdf)
            debug("%s available for writing", path)
            # open the file for reading
            try:
                ofile = h5py.File(hdf, "w")
                debug("Opened %s for writing.", hdf)
                # create the dataset from the channel data
                dset = ofile.create_dataset("tomograph", data=data)
                debug("Created HDF5 dataset from TXM data.")
                # add attributes
                dset.attrs["pixel size"] = pixelsize
                dset.attrs["pixel units"] = r'$\mu m$'
                debug("Added pixels size and unit attributes.")
                debug("HDF5 written successfully.")
            except:
                # the HDF5 file must be closed before it can be removed.
                try:
                    ofile.close()
                except:
                    pass
                os.remove(hdf)
                debug("HDF5 (%s) removed.", hdf)
                debug("HDF5 (%s) failed to write. Skipping")
                raise
            finally:
                try:
                    ofile.close()
                except:
                    pass
        except:
            continue
        finally:
            # delete the channel object
            try:
                channel.deleteObject()
                debug("Deleted TXM channel object.")
            except (AttributeError, UnboundLocalError):
                pass
