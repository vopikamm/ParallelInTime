import subprocess
import os
from os import listdir
from os.path import isfile, join

import shutil
import time
import select
import sys
import numpy

import parareal_openFoam as main_program
import options as opt
import merge_results as merge
import iterate as iterate

#cleans up from earlier runs by deleting the constructed folders
#params:
#name_folders = beginning of the name of the constructed folders
def cleanup(name_folders):
    #list all files in the directory
    list_of_dir = os.listdir('.')
    for item in list_of_dir:
        #delete folders that start with name_folders
        if os.path.exists(item) and os.path.isdir(item) and item.startswith("iteration"):
            shutil.rmtree(item)

#replaces the blockMesh file in the folder of the coarse solver by a blockMesh file that defines a coarser grid
#the file is already included by is named 'blockMeshDict_coarse'
#params:
#name_folders = beginning of the name of the constructed folders
def replace_blockMeshDict(name_folder_coarse):
    #replace system/blockMeshDict by system/blockMeshDict_coarse
    oldFilename = name_folder_coarse + '/system/blockMeshDict_coarse'
    newFilename = name_folder_coarse + '/system/blockMeshDict'
    if os.path.exists(newFilename) and os.path.isdir(newFilename):
        #delete old file if it exists
        shutil.rmtree(newFilename)
    print('rename ' + oldFilename + ' into ' + newFilename)
    os.rename(oldFilename,newFilename)