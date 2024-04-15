
import logging
import datetime
base_datetime = datetime.datetime(1970, 1, 1)

from _cuvis_il import cuvis_il
from typing import List, Union

import cuvis.cuvis_types as internal

from dataclasses import dataclass

def _fn_bits(n):
    flaglist = []
    while n:
        b = n & (~n + 1)
        flaglist.append(b)
        n ^= b
    return flaglist


def _bit_translate(n, translate_dict):
    flags = _fn_bits(n)
    return [key for key, vald in translate_dict.items()
            if vald in flags]

class SDKException(Exception):

    def __init__(self, *args):
        if len(args) == 0:
            self.message = cuvis_il.cuvis_get_last_error_msg()
        else:
            self.message = args
        logging.exception(self.message)
        super().__init__(self.message)
        pass


@dataclass
class SessionData(object):
    name: str
    session_number: int
    sequence_number: int

    def __repr__(self):
        return "'SessionFile: {}; no. {}, seq. {}'".format(self.name,
                                                           self.session_number,
                                                           self.sequence_number)

@dataclass
class GPSData(object):
    longitude: float
    latitude: float
    altitude: float
    time: datetime.datetime

    def __repr__(self):
        return "'GPS: lon./lat.: {} / {}; alt. {}, time {}'".format(
            self.longitude, self.latitude, self.altitude,
            self.time)
    
    @classmethod
    def _from_internal(cls, gps):
        return cls(longitude=gps.longitude,
                   latitude=gps.latitude,
                   altitude=gps.altitude,
                   time= base_datetime + datetime.timedelta(
            milliseconds=gps.time))

@dataclass
class SensorInfo(object):
    averages: int
    temperature: int
    gain: float
    readout_time: datetime.datetime

    @classmethod
    def _from_internal(cls, info):
        return cls(averages=info.averages,
                   temperature=info.temperature,
                   gain=info.gain,
                   readout_time= base_datetime + datetime.timedelta(
            milliseconds=info.readout_time))

    

class Bitset(object):
    _translation_dict = {}
    _inverse_dict = {}

    @classmethod
    def supremum(cls):
        """"Returns a bitset containing all possible members of the current Bitset class"""
        return cls(sum([v for k,v in cls._translation_dict.items()]))
    
    def all(self):
        """"Returns a bitset containing all possible members of the current Bitset class"""
        return type(self).supremum()

    def __init__(self, value):
        self._value = value

    def strings(self) -> List[str]:
        """"Returns a list containing the string values of the current members of the Bitset"""
        return _bit_translate(self._value, type(self)._translation_dict)

    def __repr__(self):
        """"Returns the string representation of the current Bitset"""
        return f'{self.__class__.__name__}({self.strings()})'
    
    def __int__(self):
        """"Returns the internal integer value of the current Bitset """
        return self._value
    
    def __len__(self):
        """"Returns the amount of members of the current Bitset """
        return bin(self._value).count('1')
    
    def __iter__(self):
        """"Returns an iterator over the string values of the current member of the Bitset """
        return _bit_translate(self._value, type(self)._translation_dict).__iter__()
    
    def __contains__(self, member):
        """"Returns True if the input value is part of the set. The value can be a string, an int or a similiar Bitset instance """
        if isinstance(member, str):
            return type(self)._translation_dict[member] & self._value
        elif isinstance(member, int):
            return member & self._value
        elif isinstance(member, type(self)):
            return (member & self._value) == member
        else:
            raise ValueError(f'Cannot call operator with type {type(member)}')
    
    @classmethod
    def from_strings(cls,*values: List[str]):
        """" Creates a Bitset from a list of strings """
        return cls(sum([cls._translation_dict[v] for v in values]))

    
class MeasurementFlags(Bitset):
    _translation_dict = internal.__CuvisMeasurementFlag__
    _inverse_dict =  internal.__MeasurementFlag__
    def __init__(self, value: int):
        super().__init__(value)


class Capabilities(Bitset):
    _translation_dict = internal.__CuvisCapabilities__
    _inverse_dict = internal.__Capabilities__
    def __init__(self, value: int):
        super().__init__(value)
