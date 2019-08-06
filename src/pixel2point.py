import numpy as np

def pixels2points(image, negate):
    points = []
    for y in range(len(image)):
        for x in range(len(image[y])):
            if negate ^ (image[y][x] > 0):
                points.append([x, y])
    return np.array(points)

def points2pixels(points, width, height, depth, negate):
    image = []
    for _ in range(height):
        row = []
        for _ in range(width):
            if negate:
                row.append(depth)
            else:
                row.append(0)
        image.append(row)
    
    for point in points:
        if negate:
            image[point[1]][point[0]] = 0
        else:
            image[point[1]][point[0]] = depth
    
    return np.array(image)