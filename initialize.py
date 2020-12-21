import os
import shutil

def cleanup():
    if os.path.exists("openFoam_timeslice_coarse") and os.path.isdir("openFoam_timeslice_coarse"):
        shutil.rmtree("openFoam_timeslice_coarse")
    if os.path.exists("openFoam_timeslice1") and os.path.isdir("openFoam_timeslice1"):
        shutil.rmtree("openFoam_timeslice1")
    if os.path.exists("openFoam_timeslice2") and os.path.isdir("openFoam_timeslice2"):
        shutil.rmtree("openFoam_timeslice2")
    if os.path.exists("openFoam_timeslice3") and os.path.isdir("openFoam_timeslice3"):
        shutil.rmtree("openFoam_timeslice3")
    if os.path.exists("openFoam_timeslice4") and os.path.isdir("openFoam_timeslice4"):
        shutil.rmtree("openFoam_timeslice4")

def create_folders(num_time_slices, name_folders):
    #create folder for coarse solver
    fromDirectory = "openFoam"
    toDirectory = name_folders + "_coarse"
    shutil.copytree(fromDirectory, toDirectory)
    #create folders for time slices
    for time_slice in range(1,num_time_slices + 1):
        # copy subdirectory example
        toDirectory = name_folders + str(time_slice)
        shutil.copytree(fromDirectory, toDirectory)
        print("created dir " + toDirectory)

def replace_blockMeshDict(name_folders):
    #replace system/blockMeshDict by system/blockMeshDict_coarse
    oldFilename = name_folders + '_coarse/system/blockMeshDict_coarse'
    newFilename = name_folders + '_coarse/system/blockMeshDict'
    if os.path.exists(newFilename) and os.path.isdir(newFilename):
        shutil.rmtree(newFilename)
    print('rename ' + oldFilename + ' into ' + newFilename)
    os.rename(oldFilename,newFilename)