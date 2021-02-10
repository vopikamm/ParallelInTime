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
#tolerance needed for the check of convergence
tolerance = 300
#viscosity; Re = 0.1/nu
nu = [0.01, 0.1]
