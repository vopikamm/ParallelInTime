import subprocess
import os
import shutil
import sys
import numpy as np
import select
import math as m
import pyvista as vtki

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
    for time_slice in range(opt.num_time_slices + 1):
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

def create_coarse_folder(name_folders,counter):
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
        #coarse_write_interval = ((opt.t_end - opt.t_start)/opt.dt_coarse) / opt.num_time_slices
        fine_write_interval = ((opt.t_end - opt.t_start)/opt.dt_fine) / opt.num_time_slices
        num_intermediate_steps = opt.min_num_intermediate_times_per_timestep
        # while (coarse_write_interval % num_intermediate_steps) != 0:
        while (fine_write_interval % num_intermediate_steps) != 0:
            num_intermediate_steps = num_intermediate_steps + 1
        #write_interval = coarse_write_interval / num_intermediate_steps
        write_interval = fine_write_interval / num_intermediate_steps
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

def modify_nu(value):
    '''
    Changing viscosity in transportProperties. Re = 0.1/nu
    '''
    #open controlDict file and read lines
    f = open("openFoam/constant/transportProperties", 'r')
    inlines = f.readlines()
    #open controlDict file for writing
    f = open("openFoam/constant/transportProperties", 'w')
    outlines = []
    #go through input line by line
    for line in inlines:
        #compare if the current line contains the parameter to modify
        if (line[0:2] == "nu"):
            #modify current line to contain the new value
            fill = '                '[len("nu"):16]
            line = "nu" + fill + "[0 2 -1 0 0 0 0] " + str(value) + ';\n'
        outlines.append(line)
    f.writelines(outlines)
    f.close()


def run_coarse_solver_for_single_time_slice(dir_fine_last, dir_coarse_last, counter, time_slice, time_slice_start, time_slice_end):
    """
    runs the coarse solver for one time slice and the given iteration (counter)
    """
    #copy folder for starting time from fine folder for last iteration to coarse for current iteration
    fromDirectory_fine = dir_fine_last
    fromDirectory_coarse = dir_coarse_last
    # because end time of one time slice = start time of other time slice: run coarse model in temporary folder
    toDirectory_temp = opt.name_folders + "_temp_"
    shutil.copytree(fromDirectory_fine + "/" + str(time_slice_start), toDirectory_temp + "/" + str(time_slice_start))
    # need to copy system and constant folder once
    if time_slice == 1:
        shutil.copytree(fromDirectory_coarse + "/system", toDirectory_temp + "/system")
        shutil.copytree(fromDirectory_coarse + "/constant", toDirectory_temp + "/constant")

    print("setting time parameters for coarse solver")
    modify_param_controlDict(toDirectory_temp, "startTime", time_slice_start)
    modify_param_controlDict(toDirectory_temp, "endTime", time_slice_end)

    #run coarse solver
    print("----\nrunning the coarse solver for time slice " + str(time_slice) + "\n----")
    p = run_openfoam(opt.name_folders + '_temp_')

    for line in p.stdout:
       if line[0:4] == "Time":
           print("computation completed for " + line)

    # copy coarse results for end time from temporary to coarse folder for this iteration
    fromDirectory = toDirectory_temp
    toDirectory = opt.name_folders + "_coarse_" + str(counter)
    shutil.copytree(fromDirectory + "/" + str(time_slice_end), toDirectory + "/" + str(time_slice_end))

    # remove folder with result for end time from temporary folder
    shutil.rmtree(fromDirectory + "/" + str(time_slice_end))

def parareal_adjustment(dir_coarse_last, dir_coarse_this, dir_fine_last, toDirectory, time_slice_end):
    """
    open the files from the given directories and use merge_files function to calculate new value for fine solver
    """
    files_coarse_last = [f for f in os.listdir(dir_coarse_last) if os.path.isfile(os.path.join(dir_coarse_last, f))]
    for file in files_coarse_last:
        f_coarse_last = open(dir_coarse_last + '/' + file, 'r')
        f_coarse_this = open(dir_coarse_this + '/' + file, 'r')
        f_fine_last   = open(dir_fine_last   + '/' + file, 'r')

        adjustment = 0
        outlines = []
        outlines, adjustment = merge_files(file,f_coarse_this,f_fine_last, f_coarse_last,0)
        if end_current_time_slice != opt.t_end:
            #write output
            f_out = open(toDirectory + '/' + file, 'w')
            f_out.writelines(outlines)
            f_out.close()


def merge_files(file,f1,f2,f3,adjustment):
    """
    calculate parareal adjusted new fine value from f1 (coarse this iteration), f2 (fine last iteration), f3 (coarse last iteration)
    """
    inlines1 = f1.readlines()
    inlines2 = f2.readlines()
    inlines3 = f3.readlines()

    #construct output
    outlines = []
    outlines,adjustment = compute_new_value_from_3_files(inlines1, inlines2, inlines3, outlines, adjustment)

    #close input files
    f1.close()
    f2.close()
    f3.close()

    return outlines,adjustment

def compute_new_value_from_3_files(inlines1, inlines2, inlines3, outlines, adjustment):
    """
    scan through inlines of the coarse last, coarse this and fine last files and process values for lines with values
    """
    #check that input files have same length
    if len(inlines1) != len(inlines2) or len(inlines2) != len(inlines3):
        print("len1 " + str(len(inlines1)))
        print("len2 " + str(len(inlines2)))
        print("len3 " + str(len(inlines3)))
        exit("ERROR: not able to merge files")
    processing_values = False

    #U_j+1^k+1 = G(t_j , t_j+1 , U_j^k+1) + F(t_j , t_j+1 , U_j^k) - G(t_j , t_j+1 , U_j^k)
    result = 0.0
    #process line after line from the input file
    for position in range(0,len(inlines1)):
        line1 = inlines1[position]
        line2 = inlines2[position]
        line3 = inlines3[position]
        #take care of lines that only contain one integer number - this is the number of following values
        if (len(line1) == 2 and ")" in line1):
            processing_values = False
            outlines.append(line1)
        #take care of block of values
        elif processing_values:
            result,adjustment = process_values(line1,line2,line3,adjustment)
            outlines.append(result + "\n")
        #take care of the beginning of a block of values
        elif (len(line1) == 2 and "(" in line1):
            processing_values = True
            outlines.append(line1)
        #for other lines (e.g. text) simply copy to output
        else:
            outlines.append(line1)
    return outlines,adjustment

def process_values(line1,line2,line3,adjustment):
    """
    process values using process_block_of_values function, take care of format in the files
    """
    result = ""
    if "(" in line1:
        new_value,value_fine_last_iteration = process_block_of_values(line1,line2,line3,0,1,None)
        adjustment = adjustment + ((new_value - value_fine_last_iteration)**2)
        result = "(" + str(new_value)

        new_value,value_fine_last_iteration = process_block_of_values(line1,line2,line3,1,None,None)
        adjustment = adjustment + ((new_value - value_fine_last_iteration)**2)
        result = result + " " + str(new_value)

        new_value,value_fine_last_iteration = process_block_of_values(line1,line2,line3,2,None,-2)
        adjustment = adjustment + ((new_value - value_fine_last_iteration)**2)
        result = result + " " + str(new_value) + ")\n"
    else:
        new_value,value_fine_last_iteration = process_block_of_values(line1,line2,line3,0,None,None)
        adjustment = adjustment + ((new_value - value_fine_last_iteration)**2)
        result = str(new_value) + "\n"
    return result,adjustment

def process_block_of_values(line1,line2,line3,part,offset_start,offset_end):
    #G(t_j , t_j+1 , U_j^k+1)
    value_coarse_this_iteration = float(((line1.split(" "))[part])[offset_start:offset_end])
    #F(t_j , t_j+1 , U_j^k)
    value_fine_last_iteration = float(((line2.split(" "))[part])[offset_start:offset_end])
    #G(t_j , t_j+1 , U_j^k)
    value_coarse_last_iteration = float(((line3.split(" "))[part])[offset_start:offset_end])

    #U_j+1^k+1 = G(t_j , t_j+1 , U_j^k+1) + F(t_j , t_j+1 , U_j^k) - G(t_j , t_j+1 , U_j^k)
    new_value = value_coarse_this_iteration + value_fine_last_iteration - value_coarse_last_iteration

    return new_value,value_fine_last_iteration

def build_VTKs(iteration, time_step=opt.compared_time):
    time_slice  = m.ceil(time_step*opt.num_time_slices/opt.t_end)
    dir         = os.getcwd()
    folder      = opt.name_folders + str(time_slice) + '_' + str(iteration)
    os.chdir(dir + '/' + folder)

    #delete VTK folder if it already exists
    if os.path.exists('VTK'):
        shutil.rmtree('VTK')

    #create vtk files for all timesteps in the given timeslice
    vtk_build = subprocess.run(['foamToVTK'], stdout=subprocess.DEVNULL)
    os.chdir(dir)

def converged(iteration, time_step=opt.compared_time, variable='U', method='L2'):
    '''
    Check if the results for the given variable at given time_step differ less then the chosen tolerance.
    The norm used for this can be set to 'L2' or 'Maximum'.
    '''
    convergence = False
    #Keydict of time to VTK file. Necessary, since folder names and timesteps still missmatch
    time_to_vtk = {'0': 0, '5': 250, '10': 500, '15': 750, '20': 1000, '25': 1250, '30': 750,
                    '35': 1000, '40': 1250, '45': 1500, '50': 1750, '55': 1500, '60': 1750,
                    '65': 2000, '70': 2250, '75': 2500, '80': 2000, '85': 2250, '90': 2500,
                     '95': 2750, '100': 3000}
    #setting folder and path variables:
    time_slice    = m.ceil(time_step*opt.num_time_slices/opt.t_end)
    dir           = os.getcwd()
    previous_path = dir + '/' + opt.name_folders + str(time_slice) + '_' + str(iteration-1) + '/VTK'
    current_path  = dir + '/' + opt.name_folders + str(time_slice) + '_' + str(iteration) + '/VTK'

    #load vtk files from previous iteration as pyvista objects
    os.chdir(previous_path)

    for files in os.listdir(previous_path):
        if files.endswith(str(time_to_vtk[str(time_step)]) + ".vtk"):
            previous_data = vtki.UnstructuredGrid(previous_path+'/'+files)

    #load vtk files from current iteration as pyvista objects
    os.chdir(current_path)

    for files in os.listdir(current_path):
        if files.endswith(str(time_to_vtk[str(time_step)]) + ".vtk"):
            current_data = vtki.UnstructuredGrid(current_path+'/'+files)

    diff = current_data.cell_arrays[variable] - previous_data.cell_arrays[variable]

    #calculation of norms according to 'method'
    if method is 'L2':
        diff_norm = np.linalg.norm(diff)
    if method is 'Maximum':
        diff_norm = np.amax(abs(diff))

    #check convergence:
    if diff_norm <= opt.tolerance:
        convergence = True
    os.chdir(dir)
    return(convergence,diff_norm)

def reference_run():
    """
    Run the solver on fine grid once to check for convergence to true solution.
    """
    #create folder for coarse solver
    fromDirectory = 'openFoam'
    toDirectory = 'reference'

    if os.path.exists(toDirectory):
        print('Reference solution already calculated')
        return

    shutil.copytree(fromDirectory, toDirectory)

    #adjust parameters in the coarse solver folder
    modify_param_controlDict(toDirectory, "startTime", opt.t_start)
    modify_param_controlDict(toDirectory, "endTime", opt.t_end)
    modify_param_controlDict(toDirectory, "deltaT", opt.dt_fine)

    fine_write_interval = ((opt.t_end - opt.t_start)/opt.dt_fine) / opt.num_time_slices
    num_intermediate_steps = opt.min_num_intermediate_times_per_timestep
    # while (coarse_write_interval % num_intermediate_steps) != 0:
    while (fine_write_interval % num_intermediate_steps) != 0:
        num_intermediate_steps = num_intermediate_steps + 1
    #write_interval = coarse_write_interval / num_intermediate_steps
    write_interval = fine_write_interval / num_intermediate_steps
    modify_param_controlDict(toDirectory, "writeInterval", write_interval)

    #run fine solver
    print("running the fine solver once for convergence")
    p = run_openfoam(toDirectory)

    for line in p.stdout:
       if line[0:4] == "Time":
           print("computation completed for " + line)

if __name__ == "__main__":
    #Run the fine solver once for reference
    reference_run()
    #change nu
    for n in range(0,len(opt.nu)):
        modify_nu(opt.nu[n])

        #counter for the number of iterations
        counter = 1
        #clean up from earlier runs
        cleanup(opt.name_folders)


        #initialize the coarse solver
        create_coarse_folder(opt.name_folders, counter)

        diff_time_slices = ((opt.t_end - opt.t_start) * 1.0)/opt.num_time_slices

        print("t_start: " + str(opt.t_start)  + ", t_end: " + str(opt.t_end) + ", dt_fine: " + str(opt.dt_fine) + ", dt_coarse: " + str(opt.dt_coarse))


        ################
        # 1st iteration
        ################

        #run coarse solver from t_start until t_end to have starting values for the fine solvers
        p = run_openfoam(opt.name_folders + '_coarse_' + str(counter))
        p.wait()

        #initialize the fine folders
        create_fine_folders(opt.num_time_slices,opt.name_folders, counter)

        #Parallelization of the fine solvers
        run_fine_solvers(counter)

        #creating VTK folder for time_step:
        build_VTKs(counter)

        ###################
        # other iterations
        ###################
        for iteration in range(2,opt.num_time_slices + 1):

            # run the coarse solver for the current iteration
            create_coarse_folder(opt.name_folders, iteration)

            for time_slice in range(1,opt.num_time_slices+1):

                time_slice_start = int(opt.t_start + diff_time_slices * (time_slice - 1))
                time_slice_end = int(time_slice_start + diff_time_slices)

                dir_fine_last_iteration   = opt.name_folders + str(time_slice) + "_" + str(iteration-1)
                dir_coarse_last_iteration = opt.name_folders + "_coarse_" + str(iteration)
                dir_coarse_this_iteration = opt.name_folders + "_coarse_" + str(iteration+1)
                print(time_slice_start)

                run_coarse_solver_for_single_time_slice(dir_fine_last_iteration, dir_coarse_last_iteration, iteration, time_slice, time_slice_start, time_slice_end)

            #remove temporary folder
            shutil.rmtree(opt.name_folders + "_temp_")

            # create fine folders for current iteration
            create_fine_folders(opt.num_time_slices,opt.name_folders, iteration)

            # parareal adjustment to get starting values for fine solver
            for time_slice in range(1,opt.num_time_slices+1):

                time_slice_start = int(opt.t_start + diff_time_slices * (time_slice - 1))
                time_slice_end = int(time_slice_start + diff_time_slices)

                dir_fine_last_iteration   = opt.name_folders + str(time_slice) + "_" + str(iteration-1)
                dir_coarse_last_iteration = opt.name_folders + "_coarse_" + str(iteration)
                dir_coarse_this_iteration = opt.name_folders + "_coarse_" + str(iteration+1)

                toDirectory = opt.name_folders + str(time_slice) + "_" + str(iteration-1)
                parareal_adjustment(dir_coarse_last_iteration, dir_coarse_this_iteration, dir_fine_last_iteration, toDirectory, time_slice_end)

            #Parallelization of the fine solvers
            run_fine_solvers(iteration)

            #creating VTK folder for time_step:
            build_VTKs(iteration)

            break_criterium, diff_norm = converged(iteration)

            if break_criterium:
                print('Difference between last consecutive iterations: ' + str(diff_norm))
                break
            else:
                print('Not yet converged')

        #os.system('ipython convergence.py')
