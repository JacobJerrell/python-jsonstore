#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
"""
Provides a Python class that maps values to/from a JSON file
"""
from __future__ import absolute_import
import json
import sys
from collections import OrderedDict
from copy import deepcopy
"""
TODO:
 * make backup file when saving
 * add transaction contexts
"""


class JSONDb(object):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.__flush()

    def __flush(self):
        with open(self.__dict__['__path'], 'wb') as f:
            output = json.dumps(
                self.__dict__['__data'],
                indent=self.__dict__['__indent'],
                )
            f.write(output.encode('utf-8'))

    def __init__(self, path, indent=None):
        with open(path, 'a+b') as f:
            raw_data = f.read().decode('utf-8')
        if not raw_data:
            data = OrderedDict()
        else:
            data = json.loads(raw_data, object_pairs_hook=OrderedDict)

        self.__dict__['__data'] = data
        self.__dict__['__path'] = path
        self.__dict__['__indent'] = indent

    def __getattr__(self, key):
        if key.startswith('_JSONDb__'):
            raise AttributeError
        if key in self.__dict__['__data']:
            return self.__dict__['__data'][key]
        raise KeyError(key)
        return None

    @classmethod
    def __valid_object(cls, obj, parents=None):
        """
        Determine if the object can be encoded into JSON
        """
        # pylint: disable=unicode-builtin,long-builtin
        if isinstance(obj, (dict, list)):
            if parents is None:
                parents = [obj]
            elif any(o is obj for o in parents):
                raise ValueError("Cycle detected in list/dictionary")
            parents.append(obj)

        if obj is None:
            return True
        if isinstance(obj, (bool, int, float, str)):
            return True
        if isinstance(obj, dict):
            return all(
                cls.__valid_object(k, parents) and cls.__valid_object(v, parents)
                for k, v in obj.items()
                )
        elif isinstance(obj, (list, tuple)):
            return all(cls.__valid_object(o, parents) for o in obj)
        elif sys.version_info < (3, ):
            return isinstance(obj, (long, unicode))
        else:
            return False

    def __setattr__(self, key, value):
        if not self.__valid_object(value):
            raise AttributeError
        if key.startswith(' '):
            raise AttributeError
        self.__dict__['__data'][key] = deepcopy(value)

    def __delattr__(self, key):
        del self.__dict__['__data'][key]

    def __get_obj(self, name):
        steps = name.split('.')
        path = []
        obj = self.__dict__['__data']
        if not name:
            return obj
        for step in steps:
            path.append(step)
            try:
                obj = obj[step]
            except AttributeError:
                raise KeyError('.'.join(path))
        return obj

    def __setitem__(self, name, value):
        path, _, key = name.rpartition('.')
        if self.__valid_object(value):
            dictionary = self.__get_obj(path)
            dictionary[key] = deepcopy(value)
        else:
            raise AttributeError

    def __getitem__(self, key):
        obj = self.__get_obj(key)
        if obj is self:
            raise KeyError
        return obj

    def __delitem__(self, name):
        path, _, key = name.rpartition('.')
        obj = self.__get_obj(path)
        del obj[key]
