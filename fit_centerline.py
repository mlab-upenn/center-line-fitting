import time
import argparse
import sys
import os
import numpy as np
import yaml
from sklearn.cluster import DBSCAN
from skimage.feature import canny
from skimage.morphology import skeletonize
from scipy.interpolate import CubicSpline
from graph_util import FindCycle
from pixel2point import pixels2points, points2pixels
from matplotlib import pyplot as plt
from tkinter import Tk
from tkinter.filedialog import askopenfile, askdirectory

def imageFromFile(pgmf):

    if pgmf is None:
        pgmf = askopenfile(mode='rb', filetypes=[('PGM Files', '*.pgm')], title='Select PGM Track Image File')

    if pgmf is None:
        sys.exit("Invalid PGM File")

    header = []
    while len(header) < 4:
        line = pgmf.readline()
        words = line.split()
        if len(words) > 0 and words[0] != b'#':
            header.extend(words)
    
    if len(header) != 4 or header[0] != b'P5' or not header[1].isdigit() or not header[2].isdigit() or not header[3].isdigit():
        raise ValueError("Error Reading PGM File")
    
    width = int(header[1])
    height = int(header[2])
    depth = int(header[3])

    image = []
    while len(image) < height:
        row = []
        while len(row) < width:
            word = ord(pgmf.read(1))
            row.append(word)
        image.append(row)

    return np.array(image), depth, pgmf.name

def infoFromFile(yamlf):

    if yamlf is None:
        yamlf = askopenfile(mode='r', filetypes=[('YAML Files', '*.yaml *.yml')], title='Select Track Info YAML File')

    if yamlf is None:
        sys.exit("Invalid YAML File")

    data = yaml.safe_load(yamlf)
    resolution = None
    origin = None
    try:
        resolution = data['resolution']
        origin = data['origin']
    except KeyError:
        sys.exit("Error Reading YAML File")

    return resolution, origin

def outputDirFromFile(output_dir):

    if output_dir is None:
        output_dir = askdirectory(title='Select Output Directory')

    if output_dir is None:
        sys.exit("Invalid Output Directory")

    return output_dir

def plot(image, title, plot_mode):
    if plot_mode > 0:
        fig = plt.figure()
        fig.canvas.set_window_title(title)
        plt.imshow(image, interpolation='nearest', cmap='Greys')

def plotExtra(image, title, plot_mode):
    if plot_mode > 1:
        plot(image, title, plot_mode)

def denoise(image, depth):
    db_scan = DBSCAN(eps=1, min_samples=3)

    points = pixels2points(image, False)

    clusters = db_scan.fit(points).labels_
    cluster_sizes = np.bincount(clusters + 1)
    if len(cluster_sizes) < 2:
        raise RuntimeError('No clusters found')
    cluster_sizes = cluster_sizes[1:] # ignore noise at first index
    main_cluster = np.argmax(cluster_sizes)

    points = [x for i, x in enumerate(points) if clusters[i] == main_cluster]

    height, width = image.shape
    image = points2pixels(points, width, height, depth, False)

    negative_points = pixels2points(image, True)

    clusters = db_scan.fit(negative_points).labels_
    cluster_sizes = np.bincount(clusters + 1)
    if len(cluster_sizes) < 3:
        raise RuntimeError('Not enough clusters found')
    cluster_sizes = cluster_sizes[1:] # ignore noise at first index
    main_clusters = np.argsort(cluster_sizes)[-2:]

    negative_points = [x for i, x in enumerate(negative_points) if clusters[i] in main_clusters]

    return points2pixels(negative_points, width, height, depth, True)

def prune(image, plot_mode):
    height, width = image.shape
    g = FindCycle()
    for y, row in enumerate(image):
        for x, pixel in enumerate(row):
            if pixel > 0:
                for j in range(y-1, y+2):
                    for i in range(x-1, x+2):
                        if i >= 0 and i < width and j >= 0 and j < height and image[j][i] > 0:
                            g.addEdge((x, y), (i, j))
    
    g.findCycle()

    if plot_mode < 2:
        return image, g.cycle

    image = np.zeros((height, width))
    for i, (x, y) in enumerate(g.cycle):
        image[y, x] = i / len(g.cycle) * (155) + 100
    return image, g.cycle

def subsample(image, cycle, period):
    subsampled_cycle = []
    for i, point in enumerate(cycle):
        if i % period == 0 and len(cycle) - i >= period / 2:
            subsampled_cycle.append(point)

    height, width = image.shape
    image = points2pixels(subsampled_cycle, width, height, depth, False)
    
    return image, subsampled_cycle

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Fits a center-line to a closed track.')
    parser.add_argument('--pgm_path', help='file path to the pgm track image file', nargs='?', type=argparse.FileType('rb'), default=None)
    parser.add_argument('--yaml_path', help='file path to the yaml track info file', nargs='?', type=argparse.FileType('r'), default=None)
    parser.add_argument('--subsample_period', help='defines the subsampling rate of the center-line pixels for the output points', nargs='?', type=int, default=6)
    parser.add_argument('--plot_mode', help='0: no plots, 1: basic plots, 2: all plots', nargs='?', type=int, default=1)
    parser.add_argument('--out_dir', help='directory path to write output to', nargs='?', type=argparse.FileType('w'), default=None)
    args = parser.parse_args()

    plot_mode = args.plot_mode
    subsample_period = args.subsample_period
    
    # Get track image and info from file
    Tk().withdraw()
    image, depth, name = imageFromFile(args.pgm_path)
    resolution, origin = infoFromFile(args.yaml_path)

    start_time = time.time()

    plot(image, "Original Image", plot_mode)

    # Denoise image
    print("Denoising")
    image = denoise(image, depth)
    denoised = image

    plotExtra(image, "Denoised", plot_mode)

    # Skeletonize Image
    print("Skeletonizing")
    image = skeletonize(np.where(image > 0, 1, 0)) # convert to binary image and skeletonize
    skeleton_overlay = np.where(image == 1, 0, denoised)
    image = image * depth

    plotExtra(image, "Skeletonized", plot_mode)
    plotExtra(skeleton_overlay, "Skeletonized Overlayed on Denoised", plot_mode)

    # Prune Image
    print("Pruning")
    image, track_cycle = prune(image, plot_mode)
    overlayed = np.where(image > 0, 0, denoised)

    plotExtra(image, "Pruned", plot_mode)
    plotExtra(overlayed, "Pruned Overlayed on Denoised", plot_mode)

    # Subsample
    print("Subsampling")
    image, track_cycle = subsample(image, track_cycle, subsample_period)

    plot(image, "Output", plot_mode)

    # Transform to Real-World Coordinates
    print("Transforming to Real-World Coordinates")
    track_cycle = np.array(track_cycle)
    track_cycle = track_cycle * resolution - origin[0:2]

    print("Processing Time:", time.time() - start_time, "seconds")

    # Save to CSV File
    print("Writing Output CSV")
    output_dir = outputDirFromFile(args.out_dir)
    output_path = os.path.join(output_dir, os.path.splitext(name)[0] + '.csv')
    np.savetxt(output_path, track_cycle, delimiter=",")

    print("Finished. Output saved to", output_path)

    # Display Plots
    plt.show()