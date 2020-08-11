import os.path as osp
config = dict(
    energy=9.3,
    pixel_size=0.5e-3,
    centerx=620,
    centery=580,
    distance=0.2,
    source_name=["FXE_DET_LPD1M-1/DET/detector"],
    mask_rng=[0, 3500],
    int_rng=[0.2, 5],
    int_mthds = ['BBox', 'numpy', 'cython', 'splitpixel', 'csr', 'lut'],
    int_pts=512,
    quad_positions=[[11.4, 299],
                    [-11.5, 8],
                    [254.5, -16],
                    [278.5, 275]],
    geom_file="",
    run_folder='/Users/ebadkamil/fxe-data',
    port=45454,
    hostname="127.0.0.1",
    TIME_OUT=1.0)