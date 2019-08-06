import numpy as np

def getPixelsFromFile(path):
    image = None
    depth = None
    with open(path, 'rb') as pgmf:
        header = []
        while len(header) < 4:
            line = pgmf.readline()
            words = line.split()
            if len(words) > 0 and words[0] != b'#':
                header.extend(words)

        print("HEADER:", header)
        
        if len(header) != 4 or header[0] != b'P5' or not header[1].isdigit() or not header[2].isdigit() or not header[3].isdigit():
            raise ValueError("Invalid PGM File")
        
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

    return np.array(image), depth

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