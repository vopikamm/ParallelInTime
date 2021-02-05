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
import initialize as init
import options as opt
import merge_results as merge

#def transfer_files_onto_finer_grid(file,time_slice_ends,time_slice,dir_coarse_this_iteration):
#    if file != "phi":
#        f1_coarse = open(dir_coarse_this_iteration + '/' + file, 'r')
#        inlines1_coarse = f1_coarse.readlines()
#        outlines1_fine = []
#        outlines1_fine = conv.construct_fine_version_of_other_files(inlines1_coarse,outlines1_fine)
#        f1_coarse.close()
#        f1_fine = open(dir_coarse_this_iteration + '/' + file + "_fine",'w')
#        f1_fine.writelines(outlines1_fine)
#        f1_fine.close()

def merge_files(file,f1,f2,f3,time,adjustment):
    #print("merging 3 versions of " + file + " at time " + str(time))

    inlines1 = f1.readlines()
    inlines2 = f2.readlines()
    inlines3 = f3.readlines()

    #construct output
    outlines = []
    outlines,adjustment = merge.compute_new_value_from_3_files_not_phi(inlines1, inlines2, inlines3, outlines, adjustment)

    #close input files
    f1.close()
    f2.close()
    f3.close()

    return outlines,adjustment

def set_start_values_for_coarse_solver_for_one_time_slice(prev_time_slice, prev_time_slice_end,iteration):
    folder = "iteration" + str(iteration) + "/coarse"
    main_program.modify_param_controlDict(folder, "startTime", prev_time_slice_end)
    #delete current folders
    #list all files in the directory
    list_of_dir = os.listdir(folder)
    for item in list_of_dir:
        #delete folders having an integer as name
        if os.path.exists(folder + "/" + item) and os.path.isdir(folder + "/" + item) and item != "system" and item != "constant":
            shutil.rmtree(folder + "/" + item)
    #use mapFields to have correct grid
    wd = os.getcwd()
    source = '../../iteration' + str(iteration - 1) + '/' +  opt.name_folders + str(prev_time_slice) 
    p1 = subprocess.Popen(['mapFields',source,'-consistent'], cwd=wd + '/iteration' + str(iteration) + '/coarse',stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    p1.wait()

def set_start_values_for_coarse_solver_for_first_time_slice(prev_time_slice, prev_time_slice_end,iteration):
    folder = "iteration" + str(iteration) + "/coarse"
    main_program.modify_param_controlDict(folder, "startTime", prev_time_slice_end)
    #delete current folders
    #list all files in the directory
    list_of_dir = os.listdir(folder)
    for item in list_of_dir:
        #delete folders having an integer as name
        if os.path.exists(folder + "/" + item) and os.path.isdir(folder + "/" + item) and item != "system" and item != "constant" and item != str(prev_time_slice_end):
            shutil.rmtree(folder + "/" + item)

def run_coarse_solver_for_single_time_slice(time_slice, time_slice_start, time_slice_end, iteration):
    #adjust documents in 'name_folders + "_coarse"' for the coarse solver
    #print("setting time parameters for coarse solver")
    folder = "iteration" + str(iteration) + "/coarse"
    main_program.modify_param_controlDict(folder, "startTime", time_slice_start)
    main_program.modify_param_controlDict(folder, "endTime", time_slice_end)
    #run coarse solver
    print("----\nrunning the coarse solver for time slice " + str(time_slice) + "\n----")
    main_program.run_openfoam(folder)
    print("finished running coarse solver for time slice " + str(time_slice))