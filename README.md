# Automatic deadwood detection from RGB UAV imagery



`drone_detector`is a python package for automatic deadwood detection or segmentation from RGB UAV imagery. It utilizes [IceVision](https://airctic.com) for object detection and instance segmentation, and [fastai](https://docs.fast.ai) for semantic segmentation. 

## Installation

Use `conda` to create environment from `environment.yml` with

```
conda env create -f environment.yml
```

This will install all otherwise difficult to install dependencies like gdal. At the moment `rtree` conda installation doesn't work properly with python 3.8 or newer, but if you wish to use that then you need to manually install `libspatialindex-dev` to your machine.

After that change directory to `drone_detector` and run `pip install -e .` to get CLI commands to work.

 ### Running with Singularity
 
 Use provided `dronecontainer.def` definition file to build Singularity container. Follow instructions on [https://cloud.sylabs.io/builder](https://cloud.sylabs.io/builder) and build the image with
 
 ```
 singularity build --remote dronecontainer.sif dronecontainer.der
 ```

### Running with Docker

TODO

## Usage

`drone_detector` provides several utilities, like tiling raster and vector files into smaller patches with overlap, and untiling them back to a larger tiles.

CLI commands `predict_bboxes`, `predict_instance_masks` and `predict_segmentation` work similarly, with `--path_to_model`, `--path_to_image`, `--outfile`, `--processing_dir`, `--tile_size` and `--tile_overlap` flags. `predict_bboxes` and `predict_instance_masks` have additional flag `--num_classes`.

`predict_bboxes` and `predict_instance_masks` utilize IceVision for Faster RCNN and Mask RCNN, whereas `predict_segmentation` utilizes fast.ai U-Net 

### Bounding box detection

`predict_bboxes` 
