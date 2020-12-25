import subprocess
import os
from os import listdir
from os.path import isfile, join

import shutil
import time
import select
import sys

import conversion_fine_coarse as conv
import initialize as init
import options as opt

#what this program does by now:
#(1) creates directories for coarse and the fine solvers
#(2) adjusts the blockMesh file in the coarse solver's folder to be coarse
#(2) runs coarse solver
#(3) copies output of coarse solver as input for fine solvers (with adjustment due to finer grid)
#     THIS CONVERSION IS NOT PRODUCING A CORRECT FILE FOR phi!!! 
#     THEREFORE A WORKAROUND COPYING EXISTING FILES IS AT THE MOMENT
#(4) runs fine solvers in parallel

#this program needs to be executed in a folder that also contains 
#- a folder openFoam 
#              containing the folders 0, system and constant (original ones from OLAT) needed for openFoam runs
#- a folder workaround
#              containig files phi for the current workaround (as described above)

#pending work:
#- CORRECT INPUT FILE FOR phi CONSTRUCTED FROM OUTPUT OF THE COARSE SOLVER
#- check for convergence: how to compare output of one timeslice with input of following timeslice?
#- by now all fine solvers are only run once -> with the implementation of convergence check if makes sense to run them multiple times

#running open foam
#params:
#folder = folder containing the solver that should be run
def run_openfoam(folder):
    #execute blockMesh command for the given solver
    p1 = subprocess.Popen(['blockMesh','-case',folder], stdout=subprocess.PIPE)
    p1.wait()

    #execute given solver and print output of time to console
    p2 = subprocess.Popen(['pisoFoam','-case',folder], stdout=subprocess.PIPE)
    #for line in p2.stdout:
    #   if line[0:4] == "Time":
    #       print(folder + ":          " + line)
    #p2.wait()

    #returning of p2 might be senseful for parallelization...but not really needed now
    return p2

#running the coarse solver
def run_coarse_solver():
    #adjust documents in 'name_folders + "_coarse"' for the coarse solver
    print("setting time parameters for coarse solver")
    folder = opt.name_folders + "_coarse"
    modify_param_controlDict(folder, "startTime", opt.t_start)
    modify_param_controlDict(folder, "endTime", opt.t_end)
    modify_param_controlDict(folder, "deltaT", opt.dt_coarse)
    #produce folder for every 'write_interval'-th timestep
    write_interval = ((opt.t_end - opt.t_start)/opt.dt_coarse) / opt.num_time_slices
    modify_param_controlDict(folder, "writeInterval", write_interval)
    #run coarse solver
    print("-----\n-----\nrunning the coarse solver\n-----\n-----")
    p = run_openfoam(opt.name_folders + "_coarse")

    for line in p.stdout:
       if line[0:4] == "Time":
           print("computation completed for " + line)

    p.wait()

#setting the time parameters for a time slice
#params:
#time_slice = time slice for which the parameters are set
#time_slice_start = start time of this time slice
#time_slice_end = end time of this time slice
def set_timeparams_for_time_slice(time_slice,time_slice_start,time_slice_end):
    print("setting time parameters for time slice " + str(time_slice))
    folder = opt.name_folders + str(time_slice)
    modify_param_controlDict(folder, "startTime", time_slice_start)
    modify_param_controlDict(folder, "endTime", time_slice_end)
    modify_param_controlDict(folder, "deltaT", opt.dt_fine)
    #produce folder for every 'write_interval'-th timestep
    coarse_write_interval = ((opt.t_end - opt.t_start)/opt.dt_coarse) / opt.num_time_slices
    num_intermediate_steps = opt.min_num_intermediate_times_per_timestep
    while (coarse_write_interval % num_intermediate_steps) != 0:
        num_intermediate_steps = num_intermediate_steps + 1
    write_interval = coarse_write_interval / num_intermediate_steps
    modify_param_controlDict(folder, "writeInterval", write_interval)

#modifying a value in the controlDict file
#params:
#folder = folder containing the solver for which the value should be modified
#param = parameters thats value should be modified
#value = new value of the parameter
def modify_param_controlDict(folder, param, value):
    #open controlDict file and read lines
    f = open(folder + "/system/controlDict", 'r')
    inlines = f.readlines()
    #open controlDict file for writing
    f = open(folder + "/system/controlDict", 'w')
    outlines = []
    #go through input line by line
    for line in inlines:
        #compare if the current line contains the parameter to modify
        if (line[0:len(param)] == param):
            #modify current line to contain the new value
            fill = '                '[len(param):16]
            line = param + fill + str(value) + ';\n'
        outlines.append(line)
    f.writelines(outlines)
    f.close()

#workaround needed for phi files as input for the fine solvers (look at top of this file for further information)
def workaround(start_times):
    print("++++++++")
    print("WORKAROUND")
    print("needed for correct phi files as input for the fine solvers")
    print("++++++++")

    for i in range(0,len(start_times)):
        if not conv.is_int(start_times[i]):
            print("++++++++")
            print("ERROR")
            print("number of time slices not working with current workaround")
            print("++++++++")  
            sys.exit()
        if not start_times[i] == 0:
            shutil.copy("workaround/phi" + str(start_times[i]), "openFoam_timeslice" + str(i+1) + "/" + str(start_times[i]) + "/phi")

#setting the start values for a time slice by construction from the output of the coarse solver
#formal:
#U_j+1^0 = G(t_j , t_j+1 , U_j^0)
#j time steps of coarse integrator
#j: beginning of current time slice, j+1: end of current time slice
#0 --> iteration 0
#params:
#time_slice = number of the current time slice
#time_slice_start = start time of the current time slice (needed to address corresponding output of the coarse solver)
def set_initial_start_values_for_time_slice(time_slice, time_slice_start):
    #for time_slice 1 the input that is taken for the coarse solver can be taken
    #maybe something needs to be changed here if start times > 0 are allowed
    if time_slice == 1:
        print("no need to adjust start values for time slice 1")
        return

    print("setting start values for time slice " + str(time_slice))
    #delete folder for start time if it exists
    folder_start = opt.name_folders + str(time_slice) + '/' + str(int(time_slice_start))
    if os.path.exists(folder_start) and os.path.isdir(folder_start):
        shutil.rmtree(folder_start)
    #delete 0 folder if it exists
    folder0 = opt.name_folders + str(time_slice) + '/0'
    if os.path.exists(folder0) and os.path.isdir(folder0):
        shutil.rmtree(folder0)
    #take output of coarse solver and copy to fine solver
    fromDirectory = opt.name_folders + '_coarse/' + str(int(time_slice_start)) 
    toDirectory = opt.name_folders + str(time_slice) + '/' + str(int(time_slice_start))
    print("copy from\n" + fromDirectory + "\nto\n" + toDirectory)
    shutil.copytree(fromDirectory, toDirectory)
    #adjust files such that grid size matches
    files = [f for f in listdir(toDirectory) if isfile(join(toDirectory, f))]
    for file in files:
        print("open file " + opt.name_folders + str(time_slice) + '/' + str(int(time_slice_start)) + '/' + file)
        #read lines of current file as input
        f = open(opt.name_folders + str(time_slice) + '/' + str(int(time_slice_start)) + '/' + file, 'r')
        inlines = f.readlines()
        #open file for writing output
        f = open(opt.name_folders + str(time_slice) + '/' + str(int(time_slice_start)) + '/' + file, 'w')
        outlines = []
        #construct file depending on whether it is phi or any of the other files (since they share the same structure)                                       
        if file == "phi":
            outlines = conv.construct_fine_version_of_phi(inlines,outlines)
        else:
            outlines = conv.construct_fine_version_of_other_files(inlines,outlines)
        f.writelines(outlines)
        f.close()

#running all fine solvers in parallel
#start values already set before
def run_fine_solvers():
    #start parallel runs
    processes = []
    for time_slice in range(1,opt.num_time_slices + 1):
        #run openFoam for this time slice
        print("-----\n-----\nrunning the solver for time slice " + str(time_slice) + "\n-----\n-----")
        p = run_openfoam(opt.name_folders + str(time_slice))
        processes.append(p)

    #print output of processes running openFoam for the different time slices
    streams = [p.stdout for p in processes]
    while True:
        rstreams, _, _ = select.select(streams, [], [])
        for stream in rstreams:
            line = stream.readline()
            if line[0:4] == "Time":
                print("computation completed for " + line)
        if all(p.poll() is not None for p in processes):
            break
    for stream in streams:
        print(stream.read())

    print("all fine solvers have finished")

#adjust the starting values for all time slices
#therefore we compute the end point of the previous time slice as described in the literature
#formal:
#U_j+1^k+1 = G(t_j , t_j+1 , U_j^k+1) + F(t_j , t_j+1 , U_j^k) - G(t_j , t_j+1 , U_j^k)
#j time steps of coarse integrator
#j: beginning of previous time slice, j+1: end of previous time slice / start of current time slice
#k iterationcounter
#k: last iteration, k+1: current iteration
#G(t_j , t_j+1 , U_j^k+1): result of the coarse solver for start time of current time slice and current iteration
# -> NOT COMPUTED BY NOW
#     -> take output of the fine solver for pre-prev time slice (so from previous iteration)
#     -> transfer this onto the coarse grid
#     -> adjust settings in controlDict of coarse solver and let in run on previous time slice
#F(t_j , t_j+1 , U_j^k): end result of the fine solver for previous time slice and last iteration
# -> 'output' of fine solver for previous time slice
#G(t_j , t_j+1 , U_j^k): result of the coarse solver for start time of current time slice and previous iteration
# -> current input values
def adjust_starting_values():
    for time_slice in range(1,opt.num_time_slices + 1):
        pass

#checks for convergence in the given time slice
#obviously does nothing by now
def check_convergence():
    return True

#
#
#main program
#
#
if __name__ == "__main__":
    #clean up from earlier runs
    init.cleanup(opt.name_folders)

    #compute dt for coarse solver
    dt_coarse = ((opt.t_end - opt.t_start) * 1.0)/opt.num_time_slices

    print("t_start: " + str(opt.t_start)  + ", t_end: " + str(opt.t_end) + ", dt_fine: " + str(opt.dt_fine) + ",dt_coarse: " + str(dt_coarse))

    #create folders for time slices and for the coarse solver
    init.create_folders(opt.num_time_slices,opt.name_folders)

    #replace blockMeshDict for coarse solver such that it works on a coarser grid
    init.replace_blockMeshDict(opt.name_folders)

    #run coarse solver
    run_coarse_solver()

    #start_times needed for workaround
    start_times = []

    #set start values for time slices depending on the output of the coarse solver
    for time_slice in range(1,opt.num_time_slices + 1):
        time_slice_start = int(opt.t_start + dt_coarse * (time_slice - 1))
        start_times.append(time_slice_start)
        time_slice_end = int(time_slice_start + dt_coarse)
        set_timeparams_for_time_slice(time_slice,time_slice_start,time_slice_end)
        set_initial_start_values_for_time_slice(time_slice, time_slice_start)

    workaround(start_times)

    #run fine solvers in parallel until convergence
    notconverged = True
    while(notconverged):
        #run all fine solvers in parallel
        run_fine_solvers()
        
        #adjust the start values according to parareal method
        adjust_starting_values()
        
        #check convergence
        notconverged = not check_convergence()