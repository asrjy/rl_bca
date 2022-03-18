import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# load data
# rtp_hvac_agent = np.load(r'A:\Files\PycharmProjects\RL-EmsPy\Current_Prototype\Output_Saved\rtp_histo_agent.npy')
rtp_hvac_agent = np.load(r'A:\Files\PycharmProjects\RL-EmsPy\Current_Prototype\Output_Saved\20220317_0951_rtp_histo_agent.npy')
rtp_hvac_control = np.load(r'A:\Files\PycharmProjects\RL-EmsPy\Current_Prototype\Output_Saved\rtp_histo_control.npy')

df_all = pd.read_csv(r'A:\Files\PycharmProjects\RL-EmsPy\Current_Prototype\Output_Saved\dfs_results')

# transform data
rtp_all = df_all['rtp'].to_numpy()


# plot data
rtp_bins_full_coverage = [0, 5, 10, 15, 20, 25, 50, 100, 500, 1000, 5000, 10000]
rtp_bins_low = [0, 5, 10, 15, 20, 25, 50, 100, 150]
rtp_bins_high = [100, 500, 1000, 5000, 10000]

n_controlled_zones = 4
rtp_all = np.tile(rtp_all, n_controlled_zones)

hist_range = (0, 50)
hist_range = (0, 100)
hist_range = (0, 10000)
hist_range = (51, 500)
hist_range = (500, 10000)
hist_range = (2000, 10000)
hist_range = (5000, 10000)


hist_range = (0, 50)
hist_range = (0, 100)

n_bins = 100
n_bins = 50
n_bins = 10

plt.figure()
# plt.yscale('log', nonposy='clip')
plt.hist(rtp_all, bins=n_bins, range=hist_range, alpha=0.75, label='All Time', color='k')
plt.hist(rtp_hvac_control, bins=n_bins, range=hist_range, alpha=0.75, label="Control")
plt.hist(rtp_hvac_agent, bins=n_bins, range=hist_range, alpha=0.5, label="Agent")
plt.xlabel('$RTP Bins')
plt.ylabel('RTP HVAC Usage')
plt.legend()


