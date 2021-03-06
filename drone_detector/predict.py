# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/08_predict.ipynb (unless otherwise specified).

__all__ = ['AllDataParser', 'predict_bboxes', 'predict_instance_masks', 'predict_segmentation']

# Cell
from .imports import *

from .utils import *
from .tiling import *
from .coco import *

from fastcore.foundation import *
from fastcore.script import *

from fastai.vision.all import *
from fastai.learner import load_learner, Learner
from icevision.all import *

from shutil import rmtree

# Cell

class AllDataParser(parsers.Parser, parsers.FilepathMixin, parsers.LabelsMixin, parsers.BBoxesMixin):
    "Read all image files from data_dir, used with IceVision models"
    def __init__(self, data_dir):
        self.image_filepaths = get_image_files(data_dir)

    def __iter__(self) -> Any:
        yield from self.image_filepaths

    def imageid(self, o) -> Hashable:
        return o.stem

    def filepath(self, o) -> Union[str, Path]:
        return o

    def image_width_height(self, o) -> Tuple[int, int]:
        return get_image_size(self.filepath(o))

    def labels(self, o) -> List[int]:
        return []

    def bboxes(self, o) -> List[BBox]:
        return []

# Cell

@call_parse
def predict_bboxes(path_to_model:Param("Path to pretrained model file",type=str)=None,
                   path_to_image:Param("Path to image to annotate", type=str)=None,
                   outfile:Param('Path and filename for output raster', type=str)=None,
                   processing_dir:Param("Directory to save the intermediate tiles. Deleted after use", type=str)='temp',
                   tile_size:Param("Tile size to use. Default 400x400px tiles", type=int)=400,
                   tile_overlap:Param("Tile overlap to use. Default 100px", type=int)=100,
                   num_classes:Param("Number of classes to predict. Default 2", type=int)=2
    ):
    "Detect bounding boxes from a new image using a pretrained model"
    if os.path.exists(processing_dir):
        print('Processing folder exists')
        return
    os.makedirs(processing_dir)
    print(f'Reading and tiling {path_to_image} to {tile_size}x{tile_size} tiles with overlap of {tile_overlap}px')
    tiler = Tiler(outpath=processing_dir, gridsize_x=int(tile_size), gridsize_y=int(tile_size),
                  overlap=(int(tile_overlap), int(tile_overlap)))
    tiler.tile_raster(path_to_image)

    # Check whether is possible to use gpu
    device = 'cpu' if not torch.cuda.is_available() else f'cuda:{torch.cuda.current_device()}'

    # Loading pretrained model
    print('Loading model')
    class_map = ClassMap(list(range(1, num_classes+1)))
    state_dict = torch.load(path_to_model, map_location=device)
    model = faster_rcnn.model(num_classes=len(class_map))
    model.load_state_dict(state_dict)
    if device != 'cpu': model.to(torch.device('cuda'))
    infer_tfms = tfms.A.Adapter([tfms.A.Normalize()])

    print('Starting predictions')
    infer_parser = AllDataParser(data_dir=f'{processing_dir}/raster_tiles')
    infer_set = infer_parser.parse(data_splitter=SingleSplitSplitter(), autofix=False)[0]
    infer_ds = Dataset(infer_set, infer_tfms)
    infer_dl = faster_rcnn.infer_dl(infer_ds, batch_size=16, shuffle=False)
    samples, preds = faster_rcnn.predict_dl(model=model, infer_dl=infer_dl)

    preds_coco = bbox_preds_to_coco_anns(samples, preds)

    # TODO fix categories to not be hardcoded
    preds_coco['categories'] = [
        {'supercategory':'deadwood', 'id':1, 'name': 'Standing'},
        {'supercategory':'deadwood', 'id':2, 'name': 'Fallen'},
    ]

    # Process preds to shapefiles
    coco_proc = COCOProcessor(data_path=processing_dir,
                              outpath=processing_dir,
                              coco_info=None, coco_licenses=None,
                              coco_categories=preds_coco['categories'])


    coco_proc.coco_to_shp(preds_coco)

    # Collate shapefiles
    untile_vector(path_to_targets=f'{processing_dir}/predicted_vectors', outpath=outfile)

    print('Removing intermediate files')
    rmtree(processing_dir)
    return


# Cell

@call_parse
def predict_instance_masks(path_to_model:Param("Path to pretrained model file",type=str)=None,
                           path_to_image:Param("Path to image to annotate", type=str)=None,
                           outfile:Param('Path and filename for output raster', type=str)=None,
                           processing_dir:Param("Directory to save the intermediate tiles. Deleted after use", type=str)='temp',
                           tile_size:Param("Tile size to use. Default 400x400px tiles", type=int)=400,
                           tile_overlap:Param("Tile overlap to use. Default 100px", type=int)=100,
                           num_classes:Param("Number of classes to predict. Default 2", type=int)=2
    ):
    "Segment instance masks from a new image using a pretrained model"

    if os.path.exists(processing_dir):
        print('Processing folder exists')
        return
    os.makedirs(processing_dir)
    print(f'Reading and tiling {path_to_image} to {tile_size}x{tile_size} tiles with overlap of {tile_overlap}px')
    tiler = Tiler(outpath=processing_dir, gridsize_x=int(tile_size), gridsize_y=int(tile_size),
                  overlap=(int(tile_overlap), int(tile_overlap)))
    tiler.tile_raster(path_to_image)

    # Check whether is possible to use gpu
    device = 'cpu' if not torch.cuda.is_available() else f'cuda:{torch.cuda.current_device()}'

    # Loading pretrained model
    print('Loading model')
    class_map = ClassMap(list(range(1, num_classes+1)))
    state_dict = torch.load(path_to_model, map_location=device)
    model = mask_rcnn.model(num_classes=len(class_map))
    model.load_state_dict(state_dict)
    if device != 'cpu': model.to(torch.device('cuda'))
    infer_tfms = tfms.A.Adapter([tfms.A.Normalize()])

    print('Starting predictions')
    infer_parser = AllDataParser(data_dir=f'{processing_dir}/raster_tiles')
    infer_set = infer_parser.parse(data_splitter=SingleSplitSplitter(), autofix=False)[0]
    infer_ds = Dataset(infer_set, infer_tfms)
    infer_dl = mask_rcnn.infer_dl(infer_ds, batch_size=16, shuffle=False)
    samples, preds = mask_rcnn.predict_dl(model=model, infer_dl=infer_dl)

    preds_coco = mask_preds_to_coco_anns(samples, preds)

    # TODO fix categories to not be hardcoded
    preds_coco['categories'] = [
        {'supercategory':'deadwood', 'id':1, 'name': 'Standing'},
        {'supercategory':'deadwood', 'id':2, 'name': 'Fallen'},
    ]

    # Process preds to shapefiles
    coco_proc = COCOProcessor(data_path=processing_dir,
                              outpath=processing_dir,
                              coco_info=None, coco_licenses=None,
                              coco_categories=preds_coco['categories'])


    coco_proc.coco_to_shp(preds_coco)

    # Collate shapefiles
    untile_vector(path_to_targets=f'{processing_dir}/predicted_vectors', outpath=outfile)

    print('Removing intermediate files')
    rmtree(processing_dir)
    return


# Cell

@call_parse
def predict_segmentation(path_to_model:Param("Path to pretrained model file",type=str)=None,
                         path_to_image:Param("Path to image to annotate", type=str)=None,
                         outfile:Param('Path and filename for output raster', type=str)=None,
                         processing_dir:Param("Directory to save the intermediate tiles. Deleted after use", type=str)='temp',
                         tile_size:Param("Tile size to use. Default 400x400px tiles", type=int)=400,
                         tile_overlap:Param("Tile overlap to use. Default 100px", type=int)=100
    ):
    """Segment image into land cover classes with a pretrained models
    TODO save also information about label and class"""
    if os.path.exists(processing_dir):
        print('Processing folder exists')
        return
    os.makedirs(processing_dir)
    print(f'Reading and tiling {path_to_image} to {tile_size}x{tile_size} tiles with overlap of {tile_overlap}px')
    tiler = Tiler(outpath=processing_dir, gridsize_x=int(tile_size), gridsize_y=int(tile_size),
                  overlap=(int(tile_overlap), int(tile_overlap)))
    tiler.tile_raster(path_to_image)

    # Check whether is possible to use gpu
    cpu = True if not torch.cuda.is_available() else False

    # Loading pretrained model

    # PyTorch state dict TODO
    if path_to_model.endswith('.pth') or path_to_model.endswith('.pt'):
        print('Using PyTorch state dict not yet supported')
        print('Removing intermediate files')
        rmtree(processing_dir)
        return
    # fastai learn.export()
    elif path_to_model.endswith('.pkl'):
        learn = load_learner(path_to_model, cpu=cpu)
        test_files = get_image_files(f'{processing_dir}/raster_tiles')
        print('Starting prediction')
        os.makedirs(f'{processing_dir}/predicted_rasters')
        for chunk in range(0, len(test_files), 100):
            test_dl = learn.dls.test_dl(test_files[chunk:chunk+100], num_workers=0, bs=1)
            preds = learn.get_preds(dl=test_dl)[0]

            print('Rasterizing predictions')
            for f, p in tqdm(zip(test_files[chunk:chunk+100], preds)):
                ds = gdal.Open(str(f))
                out_raster = gdal.GetDriverByName('gtiff').Create(f'{processing_dir}/predicted_rasters/{f.stem}.{f.suffix}',
                                                                  ds.RasterXSize,
                                                                  ds.RasterYSize,
                                                                  1, gdal.GDT_Int16)
                out_raster.SetProjection(ds.GetProjectionRef())
                out_raster.SetGeoTransform(ds.GetGeoTransform())
                np_pred = p.numpy().argmax(axis=0)
                band = out_raster.GetRasterBand(1).WriteArray(np_pred)
                band = None
                out_raster = None
                ds = None

    print('Merging predictions')
    untile_raster(f'{processing_dir}/predicted_rasters', outfile=outfile)

    print('Removing intermediate files')
    rmtree(processing_dir)
    return