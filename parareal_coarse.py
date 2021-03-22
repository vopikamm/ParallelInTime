import subprocess
import os
import shutil
import sys
import numpy

import options as opt


def run_openfoam(folder):
    '''
    Runs the blockMesh command and pisofoam from given folder.
    '''
    #execute blockMesh command for the given solver
    p1 = subprocess.Popen(['blockMesh','-case',folder], stdout=subprocess.PIPE)
    p1.wait()
    #execute given solver and print output of time to console
    p2 = subprocess.Popen(['pisoFoam','-case',folder], stdout=subprocess.PIPE)
    for line in p2.stdout:
        if str(line).find("Time") != -1:
            print(folder + ':             ' + str(line))
    p2.wait()
    return(p2)

def run_fine_solvers(counter):
    #start parallel runs
    processes = []
    for time_slice in range(counter,opt.num_time_slices + 1):
        #run openFoam for this time slice
        print("----\nstarting the solver for time slice " + str(time_slice) + "\n----")
        p = run_openfoam(opt.name_folders + str(time_slice) + '_' + str(counter))
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

def cleanup(name_folders):
    """
    Remove all existing folders from previous runs.
    """
    list_of_dir = os.listdir('.')
    for item in list_of_dir:
        #delete folders that start with name_folders
        if os.path.exists(item) and os.path.isdir(item) and item.startswith(name_folders):
            shutil.rmtree(item)

def create_coarse_folder(num_time_slices, name_folders,counter):
    """
    Create and fill the respective folder for the coarse solver.
    """
    #create folder for coarse solver
    fromDirectory = 'openFoam'
    toDirectory = name_folders + "_coarse_" + str(counter)
    shutil.copytree(fromDirectory, toDirectory)

    #adjust parameters in the coarse solver folder
    modify_param_controlDict(toDirectory, "startTime", opt.t_start)
    modify_param_controlDict(toDirectory, "endTime", opt.t_end)
    modify_param_controlDict(toDirectory, "deltaT", opt.dt_coarse)
    #produce folder for every 'write_interval'-th timestep
    write_interval = ((opt.t_end - opt.t_start)/opt.dt_coarse) / opt.num_time_slices
    modify_param_controlDict(toDirectory, "writeInterval", write_interval)


def create_fine_folders(num_time_slices, name_folders,counter):
    """
    Create and fill the respective folders for the fine solvers. Already computed fine solvers needed.
    """
    fromDir = 'openFoam'

    #output of the function, apparently necessary for iterations
    end_times = []
    for time_slice in range(1,num_time_slices + 1):
        #create folder for every time slices
        toDirectory = name_folders + str(time_slice) + '_' + str(counter)
        shutil.copytree(fromDir, toDirectory)

        #setting start and end times
        time_slice_start = int(opt.t_start + diff_time_slices * (time_slice - 1))
        time_slice_end = int(time_slice_start + diff_time_slices)
        end_times.append(time_slice_end)

        print("time slice =       ", time_slice)

        #change time parameters
        modify_param_controlDict(toDirectory, "startTime", time_slice_start)
        modify_param_controlDict(toDirectory, "endTime", time_slice_end)
        modify_param_controlDict(toDirectory, "deltaT", opt.dt_fine)

        #produce folder for every 'write_interval'-th timestep
        coarse_write_interval = ((opt.t_end - opt.t_start)/opt.dt_coarse) / opt.num_time_slices
        num_intermediate_steps = opt.min_num_intermediate_times_per_timestep
        while (coarse_write_interval % num_intermediate_steps) != 0:
            num_intermediate_steps = num_intermediate_steps + 1
        write_interval = coarse_write_interval / num_intermediate_steps
        modify_param_controlDict(toDirectory, "writeInterval", write_interval)

        #fill the time slice folders with the output of the coarse solver
        if time_slice == 1:
            print("no need to adjust start values for time slice 1")

        #delete folder for start time if it exists
        folder_start = opt.name_folders + str(time_slice) + '_' + str(counter) + '/' + str(int(time_slice_start))
        if os.path.exists(folder_start) and os.path.isdir(folder_start):
            shutil.rmtree(folder_start)
        #delete 0 folder if it exists
        folder0 = opt.name_folders + str(time_slice) + '_' + str(counter) + '/0'
        if os.path.exists(folder0) and os.path.isdir(folder0):
            shutil.rmtree(folder0)
        #take output of coarse solver and copy to fine solver
        fromDirectory = opt.name_folders + '_coarse_' + str(counter) + '/' + str(int(time_slice_start))
        toDirectory = opt.name_folders + str(time_slice) + '_' + str(counter) + '/' + str(int(time_slice_start))
        shutil.copytree(fromDirectory, toDirectory)

    return(end_times)



def modify_param_controlDict(folder, param, value):
    '''
    Changing parameters in controlDict.
    '''
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

if __name__ == "__main__":
    #counter for the number of iterations
    counter = 1
    #clean up from earlier runs
    cleanup(opt.name_folders)

    #initialize the coarse solver
    create_coarse_folder(opt.num_time_slices,opt.name_folders, counter)

    diff_time_slices = ((opt.t_end - opt.t_start) * 1.0)/opt.num_time_slices

    print("t_start: " + str(opt.t_start)  + ", t_end: " + str(opt.t_end) + ", dt_fine: " + str(opt.dt_fine) + ", dt_coarse: " + str(opt.dt_coarse))

    #run coarse solver from t_start until t_end to have starting values for the fine solvers
    p = run_openfoam(opt.name_folders + '_coarse_' + str(counter))
    p.wait()

    #initialize the fine folders
    create_fine_folders(opt.num_time_slices,opt.name_folders, counter)

    #Parallelization of the fine solvers
    run_fine_solvers(counter)
