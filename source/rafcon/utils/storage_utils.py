"""
.. module:: storage_utils
   :platform: Unix, Windows
   :synopsis: Utility methods for storing and loading files from disk (supports several formats)

.. moduleauthor:: Sebastian Brunner


"""

import json

import yaml

from rafcon.utils.json_utils import JSONObjectDecoder, JSONObjectEncoder


def write_dict_to_yaml(dictionary, path, **kwargs):
    """
    Writes a dictionary to a yaml file
    :param dictionary:  the dictionary to be written
    :param path: the absolute path of the target yaml file
    :param kwargs: optional additional parameters for dumper
    """
    f = open(path, 'w')
    yaml.dump(dictionary, f, indent=4, **kwargs)
    f.close()


def load_dict_from_yaml(path):
    """
    Loads a dictionary from a yaml file
    :param path: the absolute path of the target yaml file
    :return:
    """
    f = file(path, 'r')
    dictionary = yaml.load(f)
    f.close()
    return dictionary


def write_dict_to_json(dictionary, path, **kwargs):
    """
    Write a dictionary to a json file.
    :param path: The relative path to save the dictionary to
    :param dictionary: The dictionary to get saved
    :param kwargs: optional additional parameters for dumper
    """
    f = open(path, 'w')
    # We cannot write directly to the file, as otherwise the 'encode' method wouldn't be called
    result_string = json.dumps(dictionary, cls=JSONObjectEncoder, indent=4, check_circular=False, sort_keys=True,
                                                                                                            **kwargs)
    f.write(result_string)
    f.close()


def load_dict_from_json(path):
    """Loads a dictionary from a json file.

    :param path: The relative path of the json file.
    :return: The dictionary specified in the json file
    """
    f = file(path, 'r')
    result = json.load(f, cls=JSONObjectDecoder)
    f.close()
    return result
