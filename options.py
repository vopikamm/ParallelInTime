#number of time slices
#due to the workaround this value is only flexible in the sense that
#the start times for all time slices need to be integer values
num_time_slices = 10 #this value is only a minimal value
#the real number of intermediate times might be higher to have working transitions between time slices
min_num_intermediate_times_per_timestep = 3
#start time
t_start = 0
#end time
t_end = 100
#coarse delta t
dt_coarse = 0.04
#fine delta t
dt_fine = 0.02
#beginning of the name of folders created for the coarse solver and the time slices
name_folders = "openFoam_timeslice"
#time at which to check for convergence
compared_time = 60
#tolerance needed for the check of convergence
tolerance = 0.0001
#viscosity; Re = 0.1/nu
#nu = [x / 1e6 for x in range(40, 62,2)]
#nu = [0.1, 0.004, 0.002, 0.001, 0.0004, 0.0002, 0.000125, 0.0001, 8e-5, 7e-5]
#nu = [x / 1e4 for x in range(4,11)]
nu = [0.0001, 0.0002, 0.0003, 0.0004, 0.0005, 0.0006, 0.0007, 0.0008, 0.0009, 0.001]
