import pandas as pd
from matplotlib import pyplot as plt
import matplotlib as mpl

# conv1 = pd.read_pickle('convergence')
# conv2 = pd.read_pickle('convergence2')
# conv3 = pd.read_pickle('convergence3')
#
# conv_ref1 = pd.read_pickle('convergence_ref')
# conv_ref2 = pd.read_pickle('convergence_ref2')
# conv_ref3 = pd.read_pickle('convergence_ref3')
#
# conv_ref = pd.concat([conv_ref1,conv_ref2,conv_ref3], axis=0).sort_values(by=['Nu'])
# conv = pd.concat([conv1,conv2,conv3], axis=0).sort_values(by=['Nu'])
conv = pd.read_pickle('convergence_final').sort_values(by=['Nu'])
conv_ref = pd.read_pickle('convergence_ref_final').sort_values(by=['Nu'])

cmap = plt.get_cmap('viridis_r', len(conv.index))

figu, axe = plt.subplots(figsize=(20,10))

conv.T.plot(ax= axe, colormap = cmap, legend=False)

norm = mpl.colors.Normalize(vmin=min(conv.index), vmax=max(conv.index))
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = axe.figure.colorbar(sm, ticks=list(conv.index), label = 'Nu')
plt.xlabel('# of Iterations')
plt.ylabel(r'$||U_{current}-U_{previous}||_{2}$');
plt.show()

figu, axe = plt.subplots(figsize=(20,10))

conv_ref.T.plot(ax= axe, colormap = cmap, legend=False)

cbar = axe.figure.colorbar(sm, ticks=list(conv_ref.index), label = 'Nu')
plt.xlabel('# of Iterations')
plt.ylabel(r'$||U_{parallel}-U_{serial}||_{2}$');
plt.show()
