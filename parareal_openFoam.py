import subprocess
import os

from distutils.dir_util import copy_tree
import shutil
import time

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

def run_openfoam(folder):
	p = subprocess.Popen(['pisoFoam','-case',folder], stdout=subprocess.PIPE)
	for line in p.stdout:
		print(line)
	p.wait()

def set_start_values_for_time_slice(time_slice, name_folders, time_slice_start):
	print("setting start values for time slice " + str(time_slice))
	#delete folder 0
	folder0 = name_folders + str(time_slice) + '/0'
	if os.path.exists(folder0) and os.path.isdir(folder0):
		shutil.rmtree(folder0)
	#take output of coarse solver
	fromDirectory = name_folders + '_coarse/' + str(int(time_slice_start)) 
	toDirectory = name_folders + str(time_slice) + '/' + str(int(time_slice_start))
	print("copy from\n" + fromDirectory + "\nto\n" + toDirectory)
	shutil.copytree(fromDirectory, toDirectory)
			
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

def check_convergence(num_time_slices):
	pass

def create_folders(num_time_slices, name_folders):
	#create folder for coarse solver
	fromDirectory = "openFoam"
	toDirectory = name_folders + "_coarse"
	copy_tree(fromDirectory, toDirectory)
	#create folders for time slices
	for time_slice in range(1,num_time_slices + 1):
		# copy subdirectory example
		toDirectory = name_folders + str(time_slice)
		copy_tree(fromDirectory, toDirectory)
		print("created dir " + toDirectory)

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
	run_openfoam(name_folders + "_coarse")

if __name__ == "__main__":
	#clean up trash from earlier runs --> needs to be done manually now
	#cleanup()

	#TODO: put into options file?
	num_time_slices = 4
	t_start = 0
	t_end = 100
	dt_fine = 0.02

	name_folders = "openFoam_timeslice"

	#compute dt for coarse solver
	dt_coarse = ((t_end - t_start) * 1.0)/num_time_slices

	print("t_start: " + str(t_start)  + ", t_end: " + str(t_end) + ", dt_fine: " + str(dt_fine) + ",dt_coarse: " + str(dt_coarse))

	#create folders for time slices and for the coarse solver
	create_folders(num_time_slices,name_folders)

	#run coarse solver
	run_coarse_solver(name_folders, t_start, t_end, dt_coarse)

	time.sleep(1)

	#set start values for time slices depending on the output of the coarse solver
	for time_slice in range(1,num_time_slices + 1):
		time_slice_start = int(t_start + dt_coarse * (time_slice - 1))
		time_slice_end = int(time_slice_start + dt_coarse)
		set_timeparams_for_time_slice(time_slice,dt_fine,time_slice_start,time_slice_end,name_folders)

		set_start_values_for_time_slice(time_slice, name_folders, time_slice_start)

	#run fine solvers in parallel until convergence --> of course not in parallel by now
	notconverged = True
	while(notconverged):
		#start parallel runs
		for time_slice in range(1,num_time_slices + 1):
			#run openFoam for this time slice
			print("-----\n-----\nrunning the solver for time slice " + str(time_slice) + "\n-----\n-----")
			run_openfoam(name_folders + str(time_slice))
		
		#check convergence
		notconverged = False
		#check_convergence(num_time_slices)

		#correct start values for time slices
		#for time_slice in range(1,num_time_slices):
			#set_start_values_for_time_slice(time_slice)