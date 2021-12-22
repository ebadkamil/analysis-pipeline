config = dict(
    energy=9.3,
    pixel_size=0.5e-3,
    centerx=128,
    centery=128,
    distance=0.2,
    mask_rng=[0, 20],
    int_rng=[0.0, 5],
    int_mthds=["BBox", "numpy", "cython", "splitpixel", "csr", "lut"],
    int_pts=512,
    port=54055,
    hostname="127.0.0.1",
    TIME_OUT=1.0,
)


command_docker_options = {
    "--no-deps": False,
    "--always-recreate-deps": False,
    "--scale": "",
    "--abort-on-container-exit": False,
    "SERVICE": "",
    "--remove-orphans": False,
    "--no-recreate": True,
    "--force-recreate": False,
    "--no-build": False,
    "--no-color": False,
    "--rmi": "none",
    "--volumes": True,  # Remove volumes when docker-compose down (don't persist kafka and zk data)
    "--follow": False,
    "--timestamps": False,
    "--tail": "all",
    "--detach": True,
    "--build": False,
    "--no-log-prefix": False,
}
