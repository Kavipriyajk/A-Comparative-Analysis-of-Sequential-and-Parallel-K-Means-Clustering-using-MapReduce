# -*- coding: utf-8 -*-
"""PDC project1

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MWC8k9rWh5Gi-kUlW1esNkgMkP0p-vzS

**K-means clustering sequential**
"""

import numpy as np #used gfor generating random data
import matplotlib.pyplot as plt # used for data visualization
from sklearn.cluster import KMeans # for K -means algorithm implementation
import time

#It initializes the random seed and starts the timer for measuring the execution time
start_time = time.time()

# Generate some random data
X = np.random.rand(1000, 2)

# Define the number of clusters
num_clusters = 50

# Initialize the KMeans object with the number of clusters
kmeans = KMeans(n_clusters=num_clusters)

# Fit the model to the data
kmeans.fit(X)

# Get the centroids and labels
centroids = kmeans.cluster_centers_
labels = kmeans.labels_

end_time = time.time()

# Print the centroids and labels
print("Centroids:")
print(centroids)
print("Labels:")
print(labels)

# fig, ax = plt.subplots()
# ax.scatter(centroids[:, 0], centroids[:, 1], marker='o', s=150, c='black')
# for i, label in enumerate(labels):
#     ax.annotate(label, (centroids[label] + 0.01))
# # Scatter plot the centroids
# plt.scatter(centroids[:, 0], centroids[:, 1], s=100, c='red', label='Centroids')

# Scatter plot the data points with their corresponding labels
plt.scatter(X[:, 0], X[:, 1], c=labels, cmap='viridis', label='Data Points')

plt.title('K-Means Clustering')
plt.xlabel('Feature 1')
plt.ylabel('Feature 2')
plt.legend()
plt.show()

duration = end_time - start_time

print("Execution time:", duration, "seconds")

pip install mpi4py

"""**K-means clustering parallel**"""

from mpi4py import MPI
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import time

start_time = time.time()

# Initialize MPI
comm = MPI.COMM_WORLD #this creates a communicator object
rank = comm.Get_rank() # each process is assigned a unique ran
size = comm.Get_size() #total number of processes is obtained by usng comm.GetSize()

# Generate some random data
#The random data is generated on the root process (rank 0) and is stored in the variable X
X = None
if rank == 0:
    X = np.random.rand(1000, 2)

# Scatter the data to all the processors
local_X = np.zeros((X.shape[0] // size, X.shape[1]))
comm.Scatter(X, local_X, root=0) #data is scattered and Each processor receives a portion of the data in local_X.

# Define the number of clusters
num_clusters = 50

# Initialize the KMeans object with the number of clusters
kmeans = KMeans(n_clusters=num_clusters)

# Fit the model to the local data
kmeans.fit(local_X)

# Get the local centroids and labels
local_centroids = kmeans.cluster_centers_
local_labels = kmeans.labels_

# Gather the local centroids and labels to the root process
centroids = None
labels = None
if rank == 0:
    centroids = np.zeros((num_clusters, X.shape[1]))
    labels = np.zeros(X.shape[0], dtype=np.int)
centroids_counts = np.zeros(num_clusters, dtype=np.int)
comm.Reduce(local_centroids, centroids, op=MPI.SUM, root=0)
comm.Reduce(local_labels, labels, op=MPI.SUM, root=0)
comm.Reduce(np.array([len(local_X)]*num_clusters), centroids_counts, op=MPI.SUM, root=0)

# Normalize the centroids
if rank == 0:
    for i in range(num_clusters):
        if centroids_counts[i] > 0:
            centroids[i] /= centroids_counts[i]

# Broadcast the centroids to all the processors
comm.Bcast(centroids, root=0)

# Assign the data points to the nearest centroids
distances = np.linalg.norm(local_X[:, np.newaxis, :] - centroids, axis=2)
local_assignments = np.argmin(distances, axis=1)

# Gather the local assignments to the root process
assignments = None
if rank == 0:
    assignments = np.zeros(X.shape[0], dtype=np.int)
counts = np.zeros(num_clusters, dtype=np.int)
comm.Reduce(local_assignments, assignments, op=MPI.SUM, root=0)
comm.Reduce(np.array([len(local_X)]*num_clusters), counts, op=MPI.SUM, root=0)

end_time = time.time()

# Print the final assignments and centroids
if rank == 0:
    print("Final Assignments:")
    print(assignments)
    print("Final Centroids:")
    print(centroids)

# Scatter plot the centroids
plt.scatter(centroids[:, 0], centroids[:, 1], s=100, c='red', label='Centroids')

# Scatter plot the data points with their corresponding labels
plt.scatter(X[:, 0], X[:, 1], c=labels, cmap='viridis', label='Data Points')

plt.title('K-Means Clustering')
plt.xlabel('Feature 1')
plt.ylabel('Feature 2')
plt.legend()
plt.show()

duration = end_time - start_time

print("Execution time:", duration, "seconds")

"""**Parallel implementation of K means clustering using Map Reduce**"""

pip install pyspark

from pyspark import SparkContext, SparkConf
import numpy as np

import random
import matplotlib.pyplot as plt
from functools import reduce
import time

# Define a function to generate random points
def generate_random_points(num_points, max_coord):
    return [(random.uniform(0, max_coord), random.uniform(0, max_coord)) for _ in range(num_points)]

# Define a function to calculate the distance between two points
def distance(point1, point2):
    return ((point1[0]-point2[0])**2 + (point1[1]-point2[1])**2)**0.5

# Define the mapper function for MapReduce
def mapper(point, centroids):
    distances = [distance(point, centroid) for centroid in centroids]
    min_distance_index = distances.index(min(distances))
    return min_distance_index, (point, 1)

# Define the reducer function for MapReduce
def reducer(key, values):
    points, count = zip(*values)
    centroid = tuple(map(lambda x: sum(x) / len(x), zip(*points)))
    return centroid, sum(count)

# Define the K-means algorithm function
def k_means(points, k, num_iterations):
    # Initialize the centroids randomly
    centroids = random.sample(points, k)

    # Run the iterations of K-means algorithm
    for i in range(num_iterations):
        # MapReduce phase 1: Map
        mapped = [mapper(point, centroids) for point in points]

        # MapReduce phase 1: Shuffle and Sort (not necessary in this implementation)

        # MapReduce phase 2: Reduce
        reduced = {}
        for key, value in mapped:
            if key in reduced:
                reduced[key].append(value)
            else:
                reduced[key] = [value]

        # Update the centroids based on the reduced values
        centroids = [reducer(key, values)[0] for key, values in reduced.items()]

    # Return the final centroids and their assigned points
    assigned_points = {}
    for point in points:
        distances = [distance(point, centroid) for centroid in centroids]
        min_distance_index = distances.index(min(distances))
        if min_distance_index in assigned_points:
            assigned_points[min_distance_index].append(point)
        else:
            assigned_points[min_distance_index] = [point]

    return centroids, assigned_points

start_time = time.time()

# Generate some random points
points = generate_random_points(1000, 10)

# Run the K-means algorithm with 50 centroids and 10 iterations
centroids, assigned_points = k_means(points, 50, 10)

end_time = time.time()

print(centroids)
print(assigned_points)

# Plot the points and centroids on a graph
plt.figure(figsize=(8, 6))
colors = ['r', 'g', 'b', 'c', 'm']
for i, centroid in enumerate(centroids):
    color = colors[i % len(colors)]
    plt.scatter(centroid[0], centroid[1], s=100, c=color, marker='x')
    plt.scatter(*zip(*assigned_points[i]), s=50, c=color)
plt.title('K-means Clustering')
plt.xlabel('X')
plt.ylabel('Y')
plt.show()

duration = end_time - start_time

print("Execution time:", duration, "seconds")