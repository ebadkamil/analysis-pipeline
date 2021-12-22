"""
Analysis and visualization software

Author: Ebad Kamil <ebad.kamil@xfel.eu>
All rights reserved.
"""

import redis


GLOBAL_REDIS_CLIENT = None

def get_redis_client():
    global GLOBAL_REDIS_CLIENT

    if GLOBAL_REDIS_CLIENT is None:
        GLOBAL_REDIS_CLIENT = redis.Redis(decode_responses=True)

    return GLOBAL_REDIS_CLIENT


class DashMeta:
    AZIMUTHAL_META = "meta:azimuthal_meta"
    EDGE_META = "meta:edge_meta"
