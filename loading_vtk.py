import pyvista as vtki
import numpy as np
import subprocess
import options as opt
import os
import shutil



def loading_vtk(iteration=1):
    grids = {}  # contains all calculated timesteps as pyvista objects, shape: (num_time_slices,times_in_slice)
    dir   = os.getcwd()
    for i in range(1,opt.num_time_slices+1):
        folder    = opt.name_folders + str(i) + '_' + str(iteration)
        #change directory
        os.chdir(dir + '/' + folder)
        #cd        = subprocess.run(['cd', folder], stdout=subprocess.DEVNULL)
        #remove VTK folder if already existing
        if os.path.exists('VTK'):
            shutil.rmtree('VTK')
        #create vtk files for all timesteps in timeslice
        vtk_build = subprocess.run(['foamToVTK'], stdout=subprocess.DEVNULL)
        #load vtk files as pyvista objects
        os.chdir('VTK')
        vtk_dir = os.getcwd()
        for files in os.listdir(vtk_dir):
            if files.endswith(".vtk"):
                grids[files[22:-4]] = vtki.UnstructuredGrid(vtk_dir+'/'+files) #very dependent on file naming!
        os.chdir(dir)
    return(grids)

grids = loading_vtk()


#plotting example:
#here the spacing is chosen 250 --> where is this actually chosen?
time_identifier = list(range(0,int((opt.t_end-opt.t_start)/opt.dt_fine),250))


plotter = vtki.Plotter()

# Add initial mesh
mesh = grids[str(time_identifier[0])]
plotter.add_mesh(mesh, scalars='phi')
plotter.view_xy()
plotter.show()
