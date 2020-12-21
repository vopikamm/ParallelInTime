import subprocess
import os
from os import listdir
from os.path import isfile, join

import shutil
import time

import conversion_fine_coarse as conv
import initialize as init

#what this program does by now:
#(1) creates directories for coarse and the fine solvers
#(2) adjusts the blockMesh file in the coarse solver's folder to be coarse
#(2) runs coarse solver
#(3) copies output of coarse solver as input for fine solvers (with adjustment due to finer grid)
#     THIS CONVERSION IS NOT PRODUCING A CORRECT FILE FOR phi!!!
#(4) runs fine solvers one after the other

#this program needs to be executed in a folder that also contains a folder openFoam 
#containing the folders 0, system and constant (original ones from OLAT) needed for openFoam runs

#pending work:
#- CORRECT INPUT FILE FOR phi CONSTRUCTED FROM OUTPUT OF THE COARSE SOLVER
#- are files in 0 an appropriate input for the coarser grid?
#- cleanup from earlier runs: by now the cleaning(delete everything except for this program and the folder 'openFoam') needs to be done manually
#- read parameters from options file: by now they are set at the beginning of the main
#- check for convergence: how to compare output of one timeslice with input of following timeslice?
#- execute in parallel: how can the subprocesses for the fine solvers be executed in parallel?n

def run_openfoam(folder):
    p1 = subprocess.Popen(['blockMesh','-case',folder], stdout=subprocess.PIPE)
    p1.wait()

    p2 = subprocess.Popen(['pisoFoam','-case',folder], stdout=subprocess.PIPE)
    for line in p2.stdout:
       if line[0:4] == "Time":
           print(folder + ":          " + line)
    p2.wait()

    return p2

def run_coarse_solver(name_folders, t_start, t_end, dt_coarse):

    #adjust documents in 'name_folders + "_coarse"' for the coarse solver
    print("setting time parameters for coarse solver")
    folder = name_folders + "_coarse"
    dt_coarse = 0.02
    modify_param_controlDict(folder, "startTime", t_start)
    modify_param_controlDict(folder, "endTime", t_end)
    modify_param_controlDict(folder, "deltaT", dt_coarse)
    print("startTime: " + str(t_start) + ", endTime: " + str(t_end) + ", deltaT: " + str(dt_coarse))
    #produce folder for every 1250-th timestep
    #TODO: calculate this value
    modify_param_controlDict(folder, "writeInterval", 1250)
    #run coarse solver
    print("-----\n-----\nrunning the coarse solver\n-----\n-----")
    p = run_openfoam(name_folders + "_coarse")
    
    for line in p.stdout:
        if line[0:4] == "Time":
            print(folder + ":          " + line)

    p.wait()

def set_timeparams_for_time_slice(time_slice,dt_fine,time_slice_start,time_slice_end,name_folders):
    print("setting time parameters for time slice " + str(time_slice))
    folder = name_folders + str(time_slice)
    modify_param_controlDict(folder, "startTime", time_slice_start)
    modify_param_controlDict(folder, "endTime", time_slice_end)
    modify_param_controlDict(folder, "deltaT", dt_fine)
    print("startTime: " + str(time_slice_start) + ", endTime: " + str(time_slice_end) + ", deltaT: " + str(dt_fine))
    #produce folder for every 250-th timestep
    #TODO: calculate this value
    modify_param_controlDict(folder, "writeInterval", 250)

def modify_param_controlDict(folder, param, value):
    f = open(folder + "/system/controlDict", 'r')
    inlines = f.readlines()
    f = open(folder + "/system/controlDict", 'w')
    outlines = []
    for line in inlines:
        #print('read line:' + line)
        if (line[0:len(param)] == param):
            end = line.find(']')
            if end == -1:
                fill = '                '[len(param):16]
                line = param + fill + str(value) + ';\n'
            else:
                line = line[0:(end+1)] + ' ' + str(value) + ';\n'
            #print(line)
        outlines.append(line)
    f.writelines(outlines)
    f.close()

def workaround():
    print("++++++++")
    print("workaround")
    print("++++++++")

    shutil.copy("blub/phi25", "openFoam_timeslice2/25/phi")
    #os.rename("openFoam_timeslice2/25/phi25","openFoam_timeslice2/25/phi")

    shutil.copy("blub/U25", "openFoam_timeslice2/25/U")
    #os.rename("openFoam_timeslice2/25/U25","openFoam_timeslice2/25/phi")

    shutil.copy("blub/phi50", "openFoam_timeslice3/50/phi")
    #os.rename("openFoam_timeslice2/50/phi50","openFoam_timeslice3/50/phi")

    shutil.copy("blub/U50", "openFoam_timeslice3/50/U")
    #os.rename("openFoam_timeslice2/50/U50","openFoam_timeslice3/50/phi")

    shutil.copy("blub/phi75", "openFoam_timeslice4/75/phi")
    #os.rename("openFoam_timeslice2/75/phi25","openFoam_timeslice4/25/phi")

    shutil.copy("blub/U75", "openFoam_timeslice4/75/U")
    #os.rename("openFoam_timeslice2/75/U75","openFoam_timeslice4/75/phi")

def set_initial_start_values_for_time_slice(time_slice, name_folders, time_slice_start):
    if time_slice == 1:
        print("no need to adjust start values for time slice 1")
        return

    print("setting start values for time slice " + str(time_slice))
    #delete folder 0
    folder0 = name_folders + str(time_slice) + '/' + str(int(time_slice_start))
    if os.path.exists(folder0) and os.path.isdir(folder0):
        shutil.rmtree(folder0)
    #take output of coarse solver and copy to fine solver
    fromDirectory = name_folders + '_coarse/' + str(int(time_slice_start)) 
    toDirectory = name_folders + str(time_slice) + '/' + str(int(time_slice_start))
    print("copy from\n" + fromDirectory + "\nto\n" + toDirectory)
    shutil.copytree(fromDirectory, toDirectory)
    #adjust files such that grid size matches
    dir = name_folders + str(time_slice) + '/' + str(int(time_slice_start))

    files = [f for f in listdir(dir) if isfile(join(dir, f))]

    for file in files:
        print("open file " + name_folders + str(time_slice) + '/' + str(int(time_slice_start)) + '/' + file)
        f = open(name_folders + str(time_slice) + '/' + str(int(time_slice_start)) + '/' + file, 'r')
        inlines = f.readlines()
        f = open(name_folders + str(time_slice) + '/' + str(int(time_slice_start)) + '/' + file, 'w')
        outlines = []                                       
        if file == "phi":
            outlines = conv.construct_fine_version_of_phi(inlines,outlines)
        else:
            outlines = conv.construct_fine_version_of_other_files(inlines,outlines)
        f.writelines(outlines)
        f.close()

def check_convergence(num_time_slices):
    pass

if __name__ == "__main__":
    #clean up trash from earlier runs
    init.cleanup()

    num_time_slices = 4
    t_start = 0
    t_end = 100
    dt_fine = 0.02

    name_folders = "openFoam_timeslice"

    #clean up from earlier runs
    init.cleanup()

    #compute dt for coarse solver
    dt_coarse = ((t_end - t_start) * 1.0)/num_time_slices

    print("t_start: " + str(t_start)  + ", t_end: " + str(t_end) + ", dt_fine: " + str(dt_fine) + ",dt_coarse: " + str(dt_coarse))

    #create folders for time slices and for the coarse solver
    init.create_folders(num_time_slices,name_folders)

    #replace blockMeshDict for coarse solver such that it works on a coarser grid
    init.replace_blockMeshDict(name_folders)

    #run coarse solver
    run_coarse_solver(name_folders, t_start, t_end, dt_coarse)

    #set start values for time slices depending on the output of the coarse solver
    for time_slice in range(1,num_time_slices + 1):
        time_slice_start = int(t_start + dt_coarse * (time_slice - 1))
        time_slice_end = int(time_slice_start + dt_coarse)
        set_timeparams_for_time_slice(time_slice,dt_fine,time_slice_start,time_slice_end,name_folders)

        set_initial_start_values_for_time_slice(time_slice, name_folders, time_slice_start)

    workaround()

    #run fine solvers in parallel until convergence --> of course not in parallel by now
    notconverged = True
    while(notconverged):
        #start parallel runs
        processes = []
        for time_slice in range(1,num_time_slices + 1):
            #run openFoam for this time slice
            print("-----\n-----\nrunning the solver for time slice " + str(time_slice) + "\n-----\n-----")
            p = run_openfoam(name_folders + str(time_slice))

        print("all fine solvers have finished")
        
        #check convergence
        notconverged = False
        #check_convergence(num_time_slices)

        #correct start values for time slices
        #for time_slice in range(1,num_time_slices):
            #set_start_values_for_time_slice(time_slice)