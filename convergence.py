import pyvista as vtki
import numpy as np
import subprocess
import options as opt
import glob
import os
import shutil
import math as m
from matplotlib import pyplot as plt
import scipy.misc as misc



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
    """
    Function computes the L2 norm of the difference between velocity fields.
    One result referring to previous iterations, one to the reference run.
    """
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

def plot_fields(array , field = 'U', savefig = None, label='U'):
    """
    Plotting function for the produced velocity fields.
    """
    if type(savefig) == str:
        plotter = vtki.Plotter(off_screen = True)
        # Add initial mesh
        plotter.add_mesh(array, show_scalar_bar=False, scalars=field)
        plotter.add_scalar_bar(title = label, title_font_size=28, label_font_size=28, color='black', position_x =0.22)
        plotter.view_xy()
        plotter.screenshot(savefig, transparent_background=True)
    else:
        plotter = vtki.Plotter()
        # Add initial mesh
        plotter.add_mesh(array, show_scalar_bar=False, scalars=field)
        plotter.add_scalar_bar(title = label, title_font_size=28, label_font_size=28, color='black', position_x =0.22)
        plotter.view_xy()
        plotter.show()
