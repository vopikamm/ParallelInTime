import pandas as pd
from matplotlib import pyplot as plt
import matplotlib as mpl
import pyvista as vtki

import convergence as conv



font = {'size'   : 28}
mpl.rc('font', **font)

"""
Plotting the resulting velocity fields and their differences to the reference run.
"""

time_to_vtk = conv.time_to_vtk
#Loading results from all iteration at time_step to vtk object.
results, reference = conv.loading_vtk(time_step = 60)

conv.plot_fields(results[-1], label = 'U in m/s')

#computing differences between the iterations at same, given timestep
results_diff, convergence, convergence_ref = conv.convergence(results,reference)
conv.plot_fields(results_diff[-1], field = 'diff_ref', label = 'Difference to reference in m/s')

#plotting convergence for a single nu value:
# fig, ax1 = plt.subplots()
# ax2 = ax1.twinx()
# ax1.plot(range(2,len(convergence)+2),convergence, color = 'midnightblue', label='against previous iteration')
# ax2.plot(range(2,len(convergence_ref)+2),convergence_ref, color = 'darkred', label='against reference solution')
# plt.xlabel('# of iterations')
# ax1.set_ylabel(r'$| |_{max}$ aginst previous iteration',color='midnightblue')
# ax2.set_ylabel(r'$| |_{max}$ aginst reference solution',color='darkred')
# ax1.tick_params(axis='y', labelcolor='midnightblue')
# ax2.tick_params(axis='y', labelcolor='darkred')
# ax2.set_ylim([0, max(convergence_ref)])
# plt.show()


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


"""
Plotting of the convergence plots for different nu plots:
"""

conv = pd.read_pickle('convergence_mu').sort_values(by=['Nu'])
conv_ref = pd.read_pickle('convergence_mu_ref').sort_values(by=['Nu'])

cmap = plt.get_cmap('viridis_r', len(conv.index))

figu, axe = plt.subplots(figsize=(20,10))

conv.T.plot(ax= axe, colormap = cmap, legend=False)

norm = mpl.colors.Normalize(vmin=min(conv.index), vmax=max(conv.index))
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = axe.figure.colorbar(sm, ticks=list(conv.index), label = r'Nu in $\frac{m^2}{s}$')
plt.xlabel('Number of Iterations')
plt.ylabel(r'$||U_{current}-U_{previous}||_{2}$ in $\frac{m}{s}$')
plt.grid(color='lightgrey', axis='y')
#plt.savefig('convergence.png', bbox_inches = 'tight')
plt.show()

figu, axe = plt.subplots(figsize=(20,10))

conv_ref.T.plot(ax= axe, colormap = cmap, legend=False)

cbar = axe.figure.colorbar(sm, ticks=list(conv_ref.index), label = r'Nu in $\frac{m^2}{s}$')
plt.xlabel('Number of Iterations')
plt.ylabel(r'$||U_{parallel}-U_{reference}||_{2}$ in $\frac{m}{s}$')
plt.grid(color='lightgrey', axis='y')
#plt.savefig('convergence_ref.png', bbox_inches = 'tight')
plt.show()
