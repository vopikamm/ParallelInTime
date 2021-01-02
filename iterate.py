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
import initialize as init
import options as opt
import merge_results as merge

def transfer_files_onto_finer_grid(file,time_slice_ends,time_slice,dir_coarse_this_iteration):
    f1_coarse = open(dir_coarse_this_iteration + '/' + file, 'r')
    inlines1_coarse = f1_coarse.readlines()
    outlines1_fine = []
    if file == "phi":
        outlines1_fine = conv.construct_fine_version_of_phi(inlines1_coarse,outlines1_fine,time_slice_ends[time_slice - 1])
    else:
        outlines1_fine = conv.construct_fine_version_of_other_files(inlines1_coarse,outlines1_fine)
    f1_coarse.close()
    f1_fine = open(dir_coarse_this_iteration + '/' + file + "_fine",'w')
    f1_fine.writelines(outlines1_fine)
    f1_fine.close()

def merge_files(file,f1,f2,f3,time,adjustment):
    print("merging 3 versions of " + file + " at time " + str(time))

    inlines1 = f1.readlines()
    inlines2 = f2.readlines()
    inlines3 = f3.readlines()

    #construct output
    outlines = []
    if file == "phi":
        outlines,adjustment = merge.compute_new_phi_value_from_3_files(inlines1, inlines2, inlines3, outlines, adjustment, time)
    else:
        outlines,adjustment = merge.compute_new_value_from_3_files_not_phi(inlines1, inlines2, inlines3, outlines, adjustment)

    #close input files
    f1.close()
    f2.close()
    f3.close()

    return outlines,adjustment

def set_start_values_for_coarse_solver_for_one_time_slice(prev_time_slice, prev_time_slice_end):
    #delete current folders
    #list all files in the directory
    list_of_dir = os.listdir(opt.name_folders + "_coarse")
    for item in list_of_dir:
        #delete folders having an integer as name
        if os.path.exists(opt.name_folders + "_coarse/" + item) and os.path.isdir(opt.name_folders + "_coarse/" + item) and conv.is_int(item):
            shutil.rmtree(opt.name_folders + "_coarse/" + item)
    #take output of fine solver and copy to coarse solver
    fromDirectory = opt.name_folders + str(prev_time_slice) + '/' + str(int(prev_time_slice_end))
    toDirectory = opt.name_folders + '_coarse/' + str(int(prev_time_slice_end)) 
    shutil.copytree(fromDirectory, toDirectory)
    #adjust files such that grid size matches
    files = [f for f in listdir(toDirectory) if isfile(join(toDirectory, f))]
    for file in files:
        #read lines of current file as input
        f = open(toDirectory + '/' + file, 'r')
        inlines = f.readlines()
        #open file for writing output
        f = open(toDirectory + '/' + file, 'w')
        outlines = []
        #construct file depending on whether it is phi or any of the other files (since they share the same structure)                                       
        if file == "phi":
            outlines = conv.construct_coarse_version_of_phi(inlines,outlines,prev_time_slice_end)
        else:
            outlines = conv.construct_coarse_version_of_other_files(inlines,outlines)
        f.writelines(outlines)
        f.close()

def run_coarse_solver_for_single_time_slice(time_slice, time_slice_start, time_slice_end):
    #adjust documents in 'name_folders + "_coarse"' for the coarse solver
    print("setting time parameters for coarse solver")
    folder = opt.name_folders + "_coarse"
    main_program.modify_param_controlDict(folder, "startTime", time_slice_start)
    main_program.modify_param_controlDict(folder, "endTime", time_slice_end)
    #run coarse solver
    print("----\nrunning the coarse solver for time slice " + str(time_slice) + "\n----")
    p = main_program.run_openfoam(opt.name_folders + "_coarse")

    for line in p.stdout:
       if line[0:4] == "Time":
           print("computation completed for " + line)

    p.wait()

    if time_slice == opt.num_time_slices:
        main_program.copy_output_coarse_solver_last_time_slice_to_temporary_folder()