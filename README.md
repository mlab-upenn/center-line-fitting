# center-line-fitting
Takes track images output by SLAM and outputs points along the center-line in a csv file.

![image](https://user-images.githubusercontent.com/8052622/62645450-3e7a4700-b91a-11e9-846e-29a0dad7f218.png)

## Prerequisites
Get track image and info files from [Cartographer](https://github.com/googlecartographer) or some other SLAM tool. The image file should be in pgm format and the info file should be in yaml format. Here is an example track pgm and yaml combination:
##### track.pgm
![image](https://user-images.githubusercontent.com/8052622/62554222-bd01b680-b83e-11e9-8084-12e16ce1e749.png)
##### track.yaml
```
image: track.pgm
resolution: 0.050000
origin: [-5.659398, -4.766974, 0.000000]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
```

## How It Works
This center-line-fitting algorithm uses four steps:
1. Denoise
2. Skeletonize
3. Prune and Order
4. Subsample

### Denoise
In this step, we run the [DBSCAN](https://en.wikipedia.org/wiki/DBSCAN) clustering algorithm on the image twice. The first time, we run it on the positive space and keep only the pixels from the largest cluster. The second time, we run it on the negative space and keep only the pixels from the *two* largest clusters.

##### Denoised Image:
![image](https://user-images.githubusercontent.com/8052622/62556920-e53fe400-b843-11e9-883e-ecd6d408df63.png)

### Skeletonize
Next we run Zhang's Skeletonize algorithm on the image. Here is the output of "Skeletonize" overlayed over the denoised image:

##### Skeletonized Image:
![image](https://user-images.githubusercontent.com/8052622/62557299-bbd38800-b844-11e9-88ed-803fb8859980.png)

### Prune
Next we use a Depth First Search to try to find a large cycle in graph defined by adjacent pixels in the image. We remove all pixels that do not fall along the cycle. Not only does pruning remove extra branches in the skeleton, it gives us an ordering of the pixels that goes around the track. Here is the output of "Pruning" overlayed over the denoised image:

##### Pruned Image:
![image](https://user-images.githubusercontent.com/8052622/62551846-af4a3200-b83a-11e9-87c7-78e9e341d901.png)

### Subsample
Finally, we subsample pixels along the cycle we came up with. Basically, if the x is the subsample period, we keep every xth pixel on the cycle. The result with subsample period 6 looks like this:

##### Subsampled Image:
![image](https://user-images.githubusercontent.com/8052622/62557733-88ddc400-b845-11e9-8948-b11c0663131d.png)

## Usage
Clone the repository and run the center-line-fitting script:
```
git clone https://github.com/mlab-upenn/center-line-fitting.git
cd center-line-fitting
python src/fit_centerline.py
```

## Plots
To control the plots that are displayed, use
```
python center-line-fitting.py --plot_mode <0, 1, or 2>
```
0 shows no plots, 1 (default) shows basic plots, and 2 shows all plots

## I/O
You can specify the input file paths and output directory using the command line:
```
python center-line-fitting.py --pgm_path <path to track image> --yaml_path <path to track info> --out_dir <path to output directory>
```

## Subsampling Period
You can change the subsampling period as follows:
```
python center-line-fitting.py --subsample_period 20
```
This changes how sparesly the points are sampled from the center-line path
##### subsample_period = 20
![image](https://user-images.githubusercontent.com/8052622/62555068-44035e80-b840-11e9-9fe8-1cfba5de01db.png)
##### subsample_period = 6
![image](https://user-images.githubusercontent.com/8052622/62552918-6e531d00-b83c-11e9-8702-9aae2c749327.png)
