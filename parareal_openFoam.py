import subprocess
import os
from os import listdir
from os.path import isfile, join

import shutil
import time
import select
import sys
import numpy

import initialize as init
import options as opt
import merge_results as merge
import iterate as iterate

#what this program does by now:
#(1) creates directories for coarse and the fine solvers
#(2) adjusts the blockMesh file in the coarse solver's folder to be coarse
#(2) runs coarse solver
#(3) copies output of coarse solver as input for fine solvers (with adjustment due to finer grid)
#(4) runs fine solvers in parallel
#(5) recomputes coarse solver on single time slices with output of the fine solvers as input
#(6) calculate new starting values for time slices
#(7) if the adjustment in step (6) is too large: go back to step (4)

#this program needs to be executed in a folder that also contains 
#- a folder openFoam 
#              containing the folders 0, system and constant (original ones from OLAT) needed for openFoam runs

#pending work:
#- check if check of convergence is correct ... might be that I mixed something up there
#        -> might also be interesting to check in theory how low the error can get. It obviously can't become 0 since a coarse file that is involved.
#- Is it ok to look at one time slice less from iteration to iteration? I think this isn't done in the original Parareal but to me it makes sense.
#- visualize results
#

#running open foam
#params:
#folder = folder containing the solver that should be run
def run_openfoam(folder):
    #execute blockMesh command for the given solver
    p1 = subprocess.Popen(['blockMesh','-case',folder], stdout=subprocess.PIPE)
    p1.wait()

    #execute given solver and print output of time to console
    p2 = subprocess.Popen(['pisoFoam','-case',folder], stdout=subprocess.PIPE)
    for line in p2.stdout:
       if line[0:4] == "Time":
           print(folder + ":          " + line)
    p2.wait()

#running the coarse solver
def run_coarse_solver(iteration):
    #adjust documents in 'name_folders + "_coarse"' for the coarse solver
    #print("setting time parameters for coarse solver")
    folder = "iteration" + str(iteration) + "/coarse"
    modify_param_controlDict(folder, "startTime", opt.t_start)
    modify_param_controlDict(folder, "endTime", opt.t_end)
    modify_param_controlDict(folder, "deltaT", opt.dt_coarse)
    #produce folder for every 'write_interval'-th timestep
    write_interval = ((opt.t_end - opt.t_start)/opt.dt_coarse) / opt.num_time_slices
    modify_param_controlDict(folder, "writeInterval", write_interval)
    #run coarse solver
    print("----\nrunning the coarse solver\n----")
    run_openfoam(folder)
    print("finished running the coarse solver")

#setting the time parameters for a time slice
#params:
#time_slice = time slice for which the parameters are set
#time_slice_start = start time of this time slice
#time_slice_end = end time of this time slice
def set_timeparams_for_time_slice(time_slice,time_slice_start,time_slice_end, iteration):
    #print("setting time parameters for time slice " + str(time_slice))
    folder = "iteration" + str(iteration) + "/" + opt.name_folders + str(time_slice)
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

#setting the start values for a time slice by construction from the output of the coarse solver
#formal:
#U_j+1^0 = G(t_j , t_j+1 , U_j^0)
#j time steps of coarse integrator
#j: beginning of current time slice, j+1: end of current time slice
#0 --> iteration 0
#params:
#time_slice = number of the current time slice
#time_slice_start = start time of the current time slice (needed to address corresponding output of the coarse solver)
def set_initial_start_values_for_time_slice(time_slice, time_slice_start,iteration):
    #print("setting start values for time slice " + str(time_slice))
    #delete folder for start time if it exists
    folder_timeslice = "iteration" + str(iteration) + "/" + opt.name_folders + str(time_slice)
    folder_start = folder_timeslice + '/' + str(int(time_slice_start))
    if os.path.exists(folder_start) and os.path.isdir(folder_start):
        shutil.rmtree(folder_start)
    #create empty folder for start time
    os.mkdir(folder_start)
    #delete 0 folder if it exists
    folder0 = folder_timeslice + '/0'
    if os.path.exists(folder0) and os.path.isdir(folder0):
        shutil.rmtree(folder0)
    #use mapFields to transfer output of the coarse solver onto the finer grid
    wd = os.getcwd()
    source = '../' + '/coarse'
    p1 = subprocess.Popen(['mapFields',source,'-consistent'], cwd=wd + '/' + folder_timeslice, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    p1.wait()

#running all fine solvers in parallel
#start values already set before
#params:
#counter = iteration counter needed since from iteration to iteration there is always one time slice less to compute (reason is described in main)
def run_fine_solvers(iteration):
    #start parallel runs
    processes = []
    for time_slice in range(iteration,opt.num_time_slices + 1):
        #run openFoam for this time slice
        print("----\nstarting the solver for time slice " + str(time_slice) + "\n----")
        folder_timeslice = "iteration" + str(iteration) + "/" + opt.name_folders + str(time_slice)
        run_openfoam(folder_timeslice)

    #print output of processes running openFoam for the different time slices
    

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
# -> output of coarse solver for recomputation of single time slice (compute and then get result from folder for coarse solver)
#F(t_j , t_j+1 , U_j^k): end result of the fine solver for previous time slice and last iteration
# -> 'output' of fine solver for previous time slice (get from folder for time slice)
#G(t_j , t_j+1 , U_j^k): result of the coarse solver for start time of current time slice and previous iteration
# -> current input values (get from folder for time slice)
def adjust_starting_values(time_slice_ends,time_slice_starts,adjustment,iteration):
    fromDirectory = "iteration" + str(iteration - 1) + "/coarse"
    toDirectory = "iteration" + str(iteration) + "/coarse"
    shutil.copytree(fromDirectory, toDirectory)
    for time_slice in range(1,iteration):
        fromDirectory = "iteration" + str(iteration - 1) + '/' + opt.name_folders + str(time_slice)
        toDirectory = "iteration" + str(iteration) + '/' + opt.name_folders + str(time_slice)
        shutil.copytree(fromDirectory, toDirectory)
    for time_slice in range(iteration - 1,opt.num_time_slices):
        #comment lines starting with 'ex:' contain an example that might help to understand the code
        #ex: for time slice 3 (time_slice = 3): 
        #ex:                    value
        #ex:                     we
        #ex:                   compute
        #
        #ex:                  ts
        #ex:   |-----|-----|-----|-...
        #ex: j:0     1     2     3
        #
        #ex:        tse   tse   tse
        #ex:        [0]   [1]   [2]
        #
        #ex:          ts=2   ts=3
        #
        #ex: (tse = time_slice_ends, ts = time_slice)
        #ex: U_3^k+1 = G(t_2 , t_3 , U_2^k+1) + F(t_2 , t_3 , U_2^k) - G(t_2 , t_3 , U_2^k)
        previous_time_slice = time_slice - 1
        end_previous_time_slice = time_slice_starts[time_slice - 1]
        end_current_time_slice = time_slice_ends[time_slice - 1]

        #ex: G(t_2 , t_3 , U_2^k+1)
        #ex: we need to compute this from t_2 (time_slice_ends[1]) to t_3 (time_slice_ends[2]) with the coarse solver and the last start values for the fine solver
        #ex: so we need the coarse solver such that it has the computed values for t_2 (time_slice_ends[1])) from the fine solver as input
        #ex: so we copy the output computed from the fine solver for time slice 2 (end_previous_time_slice) to the coarse solver and coarsen it
        #ex: the start end time of time slice 2 (time_slice_ends[1] = end_previous_time_slice) is the start time of time slice 3
        if (time_slice == 1):
            iterate.set_start_values_for_coarse_solver_for_first_time_slice(previous_time_slice, end_previous_time_slice,iteration)
        else:
            iterate.set_start_values_for_coarse_solver_for_one_time_slice(previous_time_slice, end_previous_time_slice,iteration)
        #ex: we now run the coarse solver only on time slice 3 (time_slice)
        #ex: we need the starttime (time_slice_ends[1] = end_previous_time_slice) and the endtime (time_slice_ends[2] = end_current_time_slice)
        iterate.run_coarse_solver_for_single_time_slice(time_slice, end_previous_time_slice, end_current_time_slice,iteration)


        #G(t_j , t_j+1 , U_j^k+1)
        #ex:just computed values on time_slice 3 with coarse solver
        #not converted onto finer grid by now!
        dir_coarse_this_iteration = "iteration" + str(iteration) + "/coarse" + '/' + str(end_current_time_slice)
        #F(t_j , t_j+1 , U_j^k)
        #obviously defined on finer grid
        dir_fine_last_iteration = "iteration" + str(iteration - 1) + "/" + opt.name_folders + str(time_slice) + '/' + str(end_current_time_slice)
        #G(t_j , t_j+1 , U_j^k)
        #can be found in folder for temporary files
        #so it's already transferred onto the finer grid
        dir_coarse_last_iteration = "iteration" + str(iteration - 1) + "/coarse" + '/' + str(end_current_time_slice)
        #values to compute:
        #same as dir_coarse_last_iteration
        dir_new_fine_start_value = "iteration" + str(iteration) + "/" + opt.name_folders + str(time_slice + 1) + '/' + str(end_current_time_slice)

        #create directory for the fine versions of the files from this iteration on the coarse grid
        dir_coarse_this_iteration_temp = "iteration" + str(iteration) + "/" + opt.name_folders + "_coarse_temp" + str(time_slice)
        #delete temp folder if it exists
        if os.path.exists(dir_coarse_this_iteration_temp) and os.path.isdir(dir_coarse_this_iteration_temp):
            shutil.rmtree(dir_coarse_this_iteration_temp)
        #create temp folder
        os.mkdir(dir_coarse_this_iteration_temp)
        #copy folders constant and system
        shutil.copytree("iteration" + str(iteration - 1) + "/" + opt.name_folders + str(time_slice) + '/constant', dir_coarse_this_iteration_temp + '/constant')
        shutil.copytree("iteration" + str(iteration - 1) + "/" + opt.name_folders + str(time_slice) + '/system', dir_coarse_this_iteration_temp + '/system')
        #adjust start time in controlDict
        modify_param_controlDict(dir_coarse_this_iteration_temp, "startTime", end_current_time_slice)

        #create fine versions
        wd = os.getcwd()
        #print("calling mapFields with source " + '../' + opt.name_folders + "_coarse and target " + dir_coarse_this_iteration_temp)
        p1 = subprocess.Popen(['mapFields','../coarse','-consistent'], cwd=dir_coarse_this_iteration_temp, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        p1.wait()



        #create directory for the fine versions of the files from last iteration on the coarse grid
        dir_coarse_last_iteration_temp = "iteration" + str(iteration) + "/" + opt.name_folders + "_coarse_temp_last_iteration" + str(time_slice)
        #delete temp folder if it exists
        if os.path.exists(dir_coarse_last_iteration_temp) and os.path.isdir(dir_coarse_last_iteration_temp):
            shutil.rmtree(dir_coarse_last_iteration_temp)
        #create temp folder
        os.mkdir(dir_coarse_last_iteration_temp)
        #copy folders constant and system
        shutil.copytree("iteration" + str(iteration - 1) + "/" + opt.name_folders + str(time_slice) + '/constant', dir_coarse_last_iteration_temp + '/constant')
        shutil.copytree("iteration" + str(iteration - 1) + "/" + opt.name_folders + str(time_slice) + '/system', dir_coarse_last_iteration_temp + '/system')
        #adjust start time in controlDict
        modify_param_controlDict(dir_coarse_last_iteration_temp, "startTime", end_current_time_slice)

        #create fine versions
        wd = os.getcwd()
        #print("calling mapFields with source " + '../' + opt.name_folders + "_coarse and target " + dir_coarse_this_iteration_temp)
        p1 = subprocess.Popen(['mapFields','../../iteration' + str(iteration - 1) + '/coarse','-consistent'], cwd=dir_coarse_last_iteration_temp, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        p1.wait()

        if not os.path.exists("iteration" + str(iteration) + "/" + opt.name_folders + str(time_slice + 1)):
            newfolder = "iteration" + str(iteration) + "/" + opt.name_folders + str(time_slice + 1)
            os.mkdir(newfolder)
            shutil.copytree("iteration" + str(iteration - 1) + "/" + opt.name_folders + str(time_slice + 1) + '/constant', newfolder + '/constant')
            shutil.copytree("iteration" + str(iteration - 1) + "/" + opt.name_folders + str(time_slice + 1) + '/system', newfolder + '/system')

        if not os.path.exists(dir_new_fine_start_value):
            os.mkdir(dir_new_fine_start_value)

        files = [f for f in listdir(dir_fine_last_iteration) if isfile(join(dir_fine_last_iteration, f))]
        for file in files:
            if file != "phi":
                #print("file: " + file)

                #read lines of current 3 files as input
                f1 = open(dir_coarse_this_iteration_temp + '/' + str(end_current_time_slice) + '/' + file,'r')
                f2 = open(dir_fine_last_iteration + '/' + file, 'r')
                f3 = open(dir_coarse_last_iteration_temp + '/' + str(end_current_time_slice) + '/' + file, 'r')

                outlines,adjustment = iterate.merge_files(file,f1,f2,f3,end_current_time_slice,adjustment)

                if end_current_time_slice != opt.t_end:
                    #write output
                    f_out = open(dir_new_fine_start_value + '/' + file, 'w')
                    f_out.writelines(outlines)
                    f_out.close()
            #else:
                #TODO: delete files
        #delete temp folder if it exists
        #if os.path.exists(dir_coarse_this_iteration_temp) and os.path.isdir(dir_coarse_this_iteration_temp):
        #    shutil.rmtree(dir_coarse_this_iteration_temp)
    return adjustment

#checks for convergence
def check_convergence(adjustment):
    adjustment = numpy.sqrt(adjustment)
    print("adjustment: " + str(adjustment))
    if adjustment > opt.tolerance:
        return False
    else:
        return True

#
#
#main program
#
#
if __name__ == "__main__":
    #clean up from earlier runs
    init.cleanup(opt.name_folders)

    diff_time_slices = ((opt.t_end - opt.t_start) * 1.0)/opt.num_time_slices

    print("t_start: " + str(opt.t_start)  + ", t_end: " + str(opt.t_end) + ", dt_fine: " + str(opt.dt_fine) + ",dt_coarse: " + str(opt.dt_coarse))

    iteration = 1

    print("++++++++")
    print("ITERATION " + str(iteration))
    print("++++++++")

    #create folders for the coarse solver in iteration 0
    os.mkdir("iteration" + str(iteration))
    fromDirectory = "openFoam"
    toDirectory = "iteration" + str(iteration) + "/coarse"
    shutil.copytree(fromDirectory, toDirectory)

    #replace blockMeshDict for coarse solver such that it works on a coarser grid
    init.replace_blockMeshDict("iteration" + str(iteration) + "/coarse")

    #run coarse solver from t_start until t_end to have starting values for the fine solvers
    run_coarse_solver(iteration)

    #start and end times of time slices needed for iterating
    end_times = []
    start_times = []

    #set start values for time slices depending on the output of the coarse solver
    for time_slice in range(1,opt.num_time_slices + 1):
        #create folder
        toDirectory = "iteration" + str(iteration) + "/" + opt.name_folders + str(time_slice)
        shutil.copytree(fromDirectory, toDirectory)
        #print("created dir " + toDirectory)
        #set time parameters
        time_slice_start = int(opt.t_start + diff_time_slices * (time_slice - 1))
        time_slice_end = int(time_slice_start + diff_time_slices)
        end_times.append(time_slice_end)
        start_times.append(time_slice_start)
        set_timeparams_for_time_slice(time_slice,time_slice_start,time_slice_end,iteration)
        #copy starting values
        set_initial_start_values_for_time_slice(time_slice, time_slice_start,iteration)

    #run fine solvers in parallel until convergence
    notconverged = True
    #adjustment necessary in the current iteration -> needed for check of convergence
    #collects the changes from current starting values of fine solvers to newly computed starting values of fine solvers
    #uses euclidean distance
    adjustment = 0.0
    while(notconverged):
        if iteration != 1:
            print("++++++++")
            print("ITERATION " + str(iteration))
            print("++++++++")

        #from iteration to iteration there is always one time slice that needs no recomputition, so after opt.num_time_slices iterations nothing is changing anymore
        #reason:
        #the starting values for time slice 1 are only set in the beginning
        #the starting values for time slice 2 are set in the beginning and then are adjusted according to the output of time slice 1
        #since the output of time slice 1 is not changing due to the similar input, obviously there are no changes in time slice 2 after it was computed two times
        #and so on...
        if iteration == opt.num_time_slices:
            exit("exiting without reaching the given tolerance of " + str(opt.tolerance) + "\nadjustment is " + str(adjustment) + " in iteration " + str(iteration))
        

        #run all fine solvers in parallel
        run_fine_solvers(iteration)

        #set up folder for next iteration
        fromDirectory = "iteration" + str(iteration)
        toDirectory = "iteration" + str(iteration + 1)
        
        #adjust the start values for the next iteration according to parareal method returning the adjustment made in this iteration
        #as euclidean distance between values computed in this iteration and starting values
        adjustment = adjust_starting_values(end_times,start_times,adjustment,iteration + 1)
        
        #check convergence
        notconverged = not check_convergence(adjustment)

        #increase counter since end of iteration is reached
        iteration = iteration + 1

        #reset adjustment
        adjustment = 0.0