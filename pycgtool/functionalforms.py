import abc
import enum
import math

import numpy as np


def get_functional_forms():
    enum_dict = {}
    for subclass in FunctionalForm.__subclasses__():
        name = subclass.__name__
        enum_dict[name] = subclass
        # enum_dict[name] = name

    return enum.Enum('FunctionalForms', enum_dict)


class FunctionalForm(metaclass=abc.ABCMeta):
    """
    Parent class of any functional form used in Boltzmann Inversion to convert variance to a force constant.
    """
    def __init__(self, mean_func=np.nanmean, variance_func=np.nanvar):
        """
        Inject functions for calculating the mean and variance into the
        Boltzmann Inversion equations.

        :param mean_func: Function to calculate the mean - default is np.nanmean
        :param variance_func: Function to calculate the variance - default is np.nanvar
        """
        self._mean_func = mean_func
        self._variance_func = variance_func

    def eqm(self, values, temp):
        """
        Calculate equilibrium value.
        May be overridden by functional forms.

        :param values: Measured internal coordinate values from which to calculate equilibrium value
        :param temp: Temperature of simulation
        :return: Calculated equilibrium value
        """
        return self._mean_func(values)

    @abc.abstractmethod
    def fconst(self, values, temp):
        """
        Calculate force constant.
        Abstract static method to be defined by all functional forms.

        :param values: Measured internal coordinate values from which to calculate force constant
        :param temp: Temperature of simulation
        :return: Calculated force constant
        """
        raise NotImplementedError

    @abc.abstractproperty
    def gromacs_type_ids(self):
        """
        Return tuple of GROMACS potential type ids when used as length, angle, dihedral.
        
        :return tuple[int]: Tuple of GROMACS potential type ids
        """
        raise NotImplementedError

    @classmethod
    def gromacs_type_id_by_natoms(cls, natoms):
        """
        Return the GROMACS potential type id for this functional form when used with natoms.
        
        :param int natoms: 
        :return int: GROMACS potential type id 
        """
        tipe = cls.gromacs_type_ids[natoms - 2]
        if tipe is None:
            raise TypeError("The functional form {0} does not have a defined GROMACS potential type when used with {1} atoms.".format(cls.__name__, natoms))
        return tipe


class Harmonic(FunctionalForm):
    gromacs_type_ids = (1, 1, 1)  # Consider whether to use improper (type 2) instead, it is actually harmonic

    def fconst(self, values, temp):
        rt = 8.314 * temp / 1000.
        var = self._variance_func(values)
        return rt / var


class CosHarmonic(FunctionalForm):
    gromacs_type_ids = (None, 2, None)

    def fconst(self, values, temp):
        rt = 8.314 * temp / 1000.
        mean = self.eqm(values, temp)
        var = self._variance_func(values)
        return rt / (math.sin(mean)**2 * var)


class MartiniDefaultLength(FunctionalForm):
    gromacs_type_ids = (1, None, None)

    def fconst(self, values, temp):
        return 1250.


class MartiniDefaultAngle(FunctionalForm):
    gromacs_type_ids = (None, 2, None)

    def fconst(self, values, temp):
        return 25.


class MartiniDefaultDihedral(FunctionalForm):
    gromacs_type_ids = (None, None, 1)

    def fconst(self, values, temp):
        return 50.
