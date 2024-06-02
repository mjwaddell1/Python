import math
from random import randint
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import numpy as np

# Cluster test
# Mickey Mouse shape
# Check if points cluster according to circles

# assume canvas 1000x1000, 0,0 bottom left
circles = [(260,700,150),(740,700,150),(500,370,250)] # x,y,radius - ears,face
dotcnt = 3000
side = 1000 # square side

def InCircle(x,y,cx,cy,rad):
    #print(math.sqrt((x-cx)**2+(y-cy)**2), rad)
    return math.sqrt((x-cx)**2+(y-cy)**2) <= rad

# print(InCircle(7,6,5,5,3))

dotlist=[]
for d in range(dotcnt):
    while True:
        x = randint(1, side)
        y = randint(1, side)
        res = False
        for c in circles:
            res = res or InCircle(x,y,*c)
        if res: break # in a circle
    dotlist.append((x,y))

# print(dotlist)
plt.figure(figsize=(5,5))
plt.xlim(0, side)
plt.ylim(0, side)
plt.scatter([d[0] for d in dotlist], [d[1] for d in dotlist], marker='.')
plt.show()

colors=[[.75,.5,.5,1],[.5,.75,.5,1],[.5,.5,.75,1]] # RGBA

fig = plt.figure(figsize=(5,5)) # Initialize the plot with the specified dimensions.
ax = fig.add_subplot(1, 1, 1) # Create a plot, adds second chart popup

k_means = KMeans(init = "k-means++", n_clusters = 3, n_init = 12)
arry = np.array(dotlist) # convert to nparray
k_means.fit(arry) # run cluster process
k_means_labels = k_means.labels_
print('Labels', k_means_labels) # [1 3 2 ... 1 1 2]

k_means_cluster_centers = k_means.cluster_centers_

# Loop that plots the data points and centroids. k range 0-2
for k, col in zip(range(len([[4, 4], [-2, -1], [2, -3]])), colors):
    my_members = (k_means_labels == k) # data points in this cluster, return array of boolean
    cluster_center = k_means_cluster_centers[k] # cluster centroid

    # Plots the datapoints with color col. based on true\false array, include true entries
    ax.plot(arry[my_members, 0], arry[my_members, 1], 'w', markerfacecolor=col, marker='.', markeredgecolor='none', markersize=6)

    # Plots the centroids with specified color, but with a darker outline
    ax.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col, markeredgecolor='k', markersize=6)

ax.set_title('KMeans') # Title of the plot
ax.set_xticks(()) # Remove x-axis ticks
ax.set_yticks(()) # Remove y-axis ticks
plt.show() # shows subplot then main plot
