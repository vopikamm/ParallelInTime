# ParallelInTime

openFoam.zip:
      - This zip contains the default openFoam parameters, such as the grid or initial conditions. 
        It is necessary to extract this in order to run the code.
        
options.py:
      - In this scripts global parameters of the experiment are defined. Most concerning the parallelisation or the used viscosity.
     
parareal_coarsegrid.py:
      - This is the main script executing the parallelised OpenFoam runs with the in options.py defined parameters. 
        The starting folder openFoam contained in openFoam.zip is necessary. Folders containing the results will be built automatically.
        
convergence.py:
      - This script contains the functions and variables necessary for both parareal_coarsegrid.py and plotting.py. The functions are able to 
        read the written openFoam results into Numpy arrays to e.g. apply the norm on velocity or anomaly fields.
        
plotting.py:
      - The figures presented in the result section of the report can be generated here after running parareal_coarsegrid.py with the desired
        parameters.
