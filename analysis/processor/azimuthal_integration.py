"""
Calibration analysis and visualization for AGIPD Detector

Author: Ebad Kamil <ebad.kamil@xfel.eu>
All rights reserved.
"""
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import numpy as np
from scipy import constants

from pyFAI.azimuthalIntegrator import AzimuthalIntegrator


class PyFaiAzimuthalIntegrator(object):

    def __init__(self):
        self._distance = None
        self._wavelength = None
        self._poni1 = None
        self._poni2 = None
        self._intg_method = None
        self._intg_rng = None
        self._intg_pts = None
        self._pixel_size = None
        self._threshold_mask = None
        self._user_mask = None

        self._momentum = None
        self._intensities = None

        self._ai_integrator = None

    def __get__(self, instance, cls):
        if instance is None:
            return self

        return self._momentum, self._intensities

    def __set__(self, instance, data):
        # data is of shape (pulses, px, py)
        integrator = self._update_integrator()
        itgt1d = partial(integrator.integrate1d,
                         method=self._intg_method,
                         radial_range=self._intg_rng,
                         correctSolidAngle=True,
                         polarization_factor=1,
                         unit="q_A^-1")

        integ_points = self._intg_pts
        def _integrate(i):
            mask = np.zeros_like(data[i], dtype=np.uint8)
            # Apply mask for nan
            mask[np.isnan(data[i])] = 1
            # Apply threshold mask if provided
            if self._threshold_mask is not None:
                low, high = self._threshold_mask
                mask[(data[i] < low) | (data[i] > high)] = 1
            # Apply user provided mask
            if self._user_mask is not None:
                image_shape = data[i].shape
                mask_shape = self._user_mask[i].shape
                if image_shape == mask_shape:
                    np.logical_or(mask, self._user_mask[i], out=mask)
                else:
                    print(f"User provided mask {mask_shape} and "
                          f"image {image_shape} have different shapes")

            ret = itgt1d(data[i], integ_points, mask=mask)
            return ret.radial, ret.intensity

        with ThreadPoolExecutor(max_workers=5) as executor:
            rets = executor.map(_integrate,
                                range(data.shape[0]))

        momentums, intensities = zip(*rets)
        self._momentum = momentums[0]
        self._intensities = intensities

    def __delete__(self, instance):
        self._ai_integrator = None
        self._momentum = None
        self._intensities = None

    def _update_integrator(self):
        if self._ai_integrator is None:
            self._ai_integrator = AzimuthalIntegrator(
                dist=self._distance,
                pixel1=self._pixel_size,
                pixel2=self._pixel_size,
                poni1=self._poni1,
                poni2=self._poni2,
                rot1=0,
                rot2=0,
                rot3=0,
                wavelength=self._wavelength)
        else:
            if self._ai_integrator.dist != self._distance \
                    or self._ai_integrator.wavelength != self._wavelength \
                    or self._ai_integrator.poni1 != self._poni1 \
                    or self._ai_integrator.poni2 != self._poni2:
                self._ai_integrator.set_param(
                    (self._distance,
                     self._poni1,
                     self._poni2,
                     0,
                     0,
                     0,
                     self._wavelength))
        return self._ai_integrator

    @property
    def distance(self):
        return self._distance

    @distance.setter
    def distance(self, val):
        if val < 0:
            raise ValueError("Distance cannot be negative")
        self._distance = val

    @property
    def wavelength(self):
        return self._wavelength

    @wavelength.setter
    def wavelength(self, val):
        self._wavelength = val

    @property
    def poni1(self):
        return self._poni1

    @poni1.setter
    def poni1(self, val):
        self._poni1 = val

    @property
    def poni2(self):
        return self._poni2

    @poni2.setter
    def poni2(self, val):
        self._poni2 = val

    @property
    def intg_method(self):
        return self._intg_method

    @intg_method.setter
    def intg_method(self, val):
        _available_methods = ["numpy", "cython", "BBox", "lut",
                              "csr", "nosplit_csr", "full_csr", "lut_ocl"]
        if val not in _available_methods:
            raise ValueError("Support available methods {}")
        self._intg_method = val

    @property
    def intg_rng(self):
        return self._intg_rng

    @intg_rng.setter
    def intg_rng(self, val):
        start, stop = val
        if start >= stop:
            raise ValueError("Improper range")
        self._intg_rng = val

    @property
    def intg_pts(self):
        return self._intg_pts

    @intg_pts.setter
    def intg_pts(self, val):
        self._intg_pts = val

    @property
    def pixel_size(self):
        return self._pixel_size

    @pixel_size.setter
    def pixel_size(self, val):
        self._pixel_size = val

    @property
    def user_mask(self):
        return self._user_mask

    @user_mask.setter
    def user_mask(self, val):
        if val is not None and (not isinstance(val, np.ndarray) or val.dtype != np.uint8): #noqa
            raise ValueError("User mask must be ndarray of dtype np.uint8")
        self._user_mask = val

    @property
    def threshold_mask(self):
        return self._threshold_mask

    @threshold_mask.setter
    def threshold_mask(self, val):
        if val is not None and not isinstance(val, tuple):
            raise ValueError("Threshold mask must be a tuple (low, high)")
        self._threshold_mask = val


class ImageIntegrator:
    """
    Attributes:
    -----------
    momentum: ndarray
        Shape of numpy array: (n_points, )
    intensities: ndarray
        Shape of numpy array: (n_pulses, n_points)"""
    constant = 1e-3 * constants.c * constants.h / constants.e

    _azimuthal_integrator = PyFaiAzimuthalIntegrator()

    def __init__(self):

        self.momentums = None
        self.intensities = None

    def integrate(self, ai_config, image):
        """
        Pararmeters
        -----------
        ai_config: dict
        For eg.:ai_config = dict(energy=9.3,
                                 pixel_size=0.5e-3,
                                 centrex=580,
                                 centrey=620,
                                 distance=0.2,
                                 intg_rng=[0.2, 5],
                                 intg_method='BBox',
                                 intg_pts=512,
                                 threshold_mask=(0,100),
                                 user_mask=user_mask)
                    user_mask: ndarray (Same shape as image to integrate)
        image: ndarray
            Shape: (pulses, px, py)
        """
        # Set properties of _azimuthal_integrator descriptor
        self.__class__._azimuthal_integrator.distance = ai_config['distance']
        self.__class__._azimuthal_integrator.wavelength = \
            ImageIntegrator.constant / ai_config["energy"]
        self.__class__._azimuthal_integrator.poni1 = \
            ai_config["centrey"] * ai_config['pixel_size']
        self.__class__._azimuthal_integrator.poni2 = \
            ai_config["centrex"] * ai_config['pixel_size']
        self.__class__._azimuthal_integrator.intg_method = \
            ai_config['intg_method']
        self.__class__._azimuthal_integrator.intg_rng = \
            ai_config['intg_rng']
        self.__class__._azimuthal_integrator.intg_pts = \
            ai_config['intg_pts']
        self.__class__._azimuthal_integrator.pixel_size = \
            ai_config['pixel_size']
        self.__class__._azimuthal_integrator.threshold_mask = \
            ai_config.get('threshold_mask', None)
        self.__class__._azimuthal_integrator.user_mask = \
            ai_config.get('user_mask', None)

        self._azimuthal_integrator = image
        self.momentums, self.intensities = self._azimuthal_integrator
        return self.momentums, np.array(self.intensities)


if __name__ == "__main__":

    intg = ImageIntegrator()
    config = dict(energy=9.3,
                  pixel_size=0.5e-3,
                  centrex=512,
                  centrey=512,
                  distance=0.2,
                  intg_rng=[0., 5],
                  intg_method='BBox',
                  intg_pts=512,
                  threshold_mask=(0,100),
                  user_mask=None)
    mom, intensities = intg.integrate(
        config, np.random.uniform(-200, 2000, (1, 1024, 1024)))
    print(intensities)
