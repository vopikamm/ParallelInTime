import pyvista as vtki
import numpy as np
import subprocess
import options as opt
import glob
import os
import shutil
import math as m
from matplotlib import pyplot as plt



#Keydict of time to VTK file. Necessary, since folder names and timesteps still missmatch
time_to_vtk = {'0': 0, '5': 250, '10': 500, '15': 750, '20': 1000, '25': 1250, '30': 750,
                '35': 1000, '40': 1250, '45': 1500, '50': 1750, '55': 1500, '60': 1750,
                '65': 2000, '70': 2250, '75': 2500, '80': 2000, '85': 2250, '90': 2500,
                 '95': 2750, '100': 3000}

def loading_vtk(time_step = 60):
    """
    Loads the results for the given time step at all iterations into a list of VTK objects.
    """
    #the time slice where to find the given time_step
    time_slice  = m.ceil(time_step*opt.num_time_slices/opt.t_end)
    data        = []
    dir         = os.getcwd()
    iter_exists = True
    iteration   = 1

    #change directory
    os.chdir(dir + '/reference')

    #delete VTK folder if it already exists
    if os.path.exists('VTK'):
        shutil.rmtree('VTK')

    #create vtk files for all timesteps in timeslice
    vtk_build = subprocess.run(['foamToVTK'], stdout=subprocess.DEVNULL)

    #load vtk files as pyvista objects
    os.chdir('VTK')
    vtk_dir = os.getcwd()
    for files in os.listdir(vtk_dir):
        if files.endswith("3000.vtk"):
            reference = vtki.UnstructuredGrid(vtk_dir+'/'+files)
    os.chdir(dir)

    #stops when last iteration is reached
    while iter_exists:
        folder    = opt.name_folders + str(time_slice) + '_' + str(iteration)

        #change directory
        os.chdir(dir + '/' + folder)

        #delete VTK folder if it already exists
        if os.path.exists('VTK'):
            shutil.rmtree('VTK')

        #create vtk files for all timesteps in timeslice
        vtk_build = subprocess.run(['foamToVTK'], stdout=subprocess.DEVNULL)

        #load vtk files as pyvista objects
        os.chdir('VTK')
        vtk_dir = os.getcwd()
        for files in os.listdir(vtk_dir):
            if files.endswith(str(time_to_vtk[str(time_step)]) + ".vtk"):
                data.append(vtki.UnstructuredGrid(vtk_dir+'/'+files))
        os.chdir(dir)

        #Proceed to the next iteration if it exists
        if os.path.exists(opt.name_folders + '1_' + str(iteration+1)):
            iteration +=1
        else:
            iter_exists = False

    return(data, reference)

def convergence(results,reference):
    convergence     = []
    convergence_ref = []
    for i in range(1,len(results)):
        #compute difference of velocity outputs
        diff_U   = results[i].cell_arrays['U']-results[i-1].cell_arrays['U']
        diff_ref = results[i].cell_arrays['U']-reference.cell_arrays['U']



        points = results[i].points
        array  = results[i].point_arrays['U'] - reference.point_arrays['U']
        X      = points[:,0]

        for j in range(0,len(X)-1):
            if X[j] <= 5:
                array[j,:] = 0

        results[i].add_field_array(diff_U, 'diff_U')
        results[i].add_field_array(diff_ref, 'diff_ref')





        #chose maximum-norm for now
        convergence.append(np.amax(abs(diff_U)))
        convergence_ref.append(np.amax(abs(array[:,0])))
    return(results, convergence, convergence_ref)

if __name__ == "__main__":



    #Loading results from all iteration at time_step to vtk object.
    results, reference = loading_vtk(time_step = 60)

    #computing differences between the iterations at same, given timestep

    results_diff, convergence, convergence_ref = convergence(results,reference)

    #counting how many convergence graphs were created, will give an error when plotting if j > len(opt.nu)
    j = len(glob.glob("conv*.png"))

    #plotting convergence:
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.plot(range(2,len(convergence)+2),convergence, color = 'midnightblue', label='against previous iteration')
    ax2.plot(range(2,len(convergence_ref)+2),convergence_ref, color = 'darkred', label='against reference solution')
    plt.xlabel('# of iterations')
    ax1.set_ylabel(r'$| |_{max}$ aginst previous iteration',color='midnightblue')
    ax2.set_ylabel(r'$| |_{max}$ aginst reference solution',color='darkred')
    ax1.tick_params(axis='y', labelcolor='midnightblue')
    ax2.tick_params(axis='y', labelcolor='darkred')
    ax2.set_ylim([0, max(convergence_ref)])
    #plt.title('Re= %1.1f' %(0.1/opt.nu[j]))
    #plt.savefig('convergence_nu_%1.4f.png'%opt.nu[j])
    plt.show()


    #plotting differences:
    i=1
    for iteration in results_diff[1:]:
        plotter = vtki.Plotter()

        # Add initial mesh
        plotter.add_mesh(iteration, scalars='diff_ref')
        plotter.view_xy()
        plotter.show()
        #plotter.show(screenshot="flow_nu_{:1.4f}_{}.png".format(opt.nu[j], i))
        i+=1
