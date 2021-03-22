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
import conversion_fine_coarse as conv
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
        if os.path.exists(item) and os.path.isdir(item) and item.startswith(name_folders):
            shutil.rmtree(item)

#creates folders containing the data for the different solvers
#params:
#num_time_slices = number of time slices
#name_folders = beginning of the name of the constructed folders
def create_folders(num_time_slices, name_folders,counter):
    #create folder for coarse solver
    fromDirectory = 'openFoam'
    if counter is 1:
        toDirectory = name_folders + "_coarse"
        shutil.copytree(fromDirectory, toDirectory)


    #create folder for every time slices
    for time_slice in range(1,num_time_slices + 1):
        toDirectory = name_folders + str(time_slice) + '_' + str(counter)
        shutil.copytree(fromDirectory, toDirectory)
        print("created dir " + toDirectory)

#replaces the blockMesh file in the folder of the coarse solver by a blockMesh file that defines a coarser grid
#the file is already included by is named 'blockMeshDict_coarse'
#params:
#name_folders = beginning of the name of the constructed folders
def replace_blockMeshDict(name_folders, counter):
    #replace system/blockMeshDict by system/blockMeshDict_coarse
    oldFilename = name_folders + '_coarse' + '/system/blockMeshDict_coarse'
    newFilename = name_folders + '_coarse' + '/system/blockMeshDict'
    if os.path.exists(newFilename) and os.path.isdir(newFilename):
        #delete old file if it exists
        shutil.rmtree(newFilename)
    print('rename ' + oldFilename + ' into ' + newFilename)
    os.rename(oldFilename,newFilename)
