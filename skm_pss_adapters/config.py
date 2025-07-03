'''
Class to hold config for PSS and the exports.
'''

import yaml
import re

#-------------------------------------
#  Settings class
#-------------------------------------

class Config:
    """
    A class to hold config for PSS and the exports.
    """

    def __init__(self, filename=None, **kwargs):
        """
        Initializes the settings with yaml file and/or provided keyword arguments.

        Parameters
        ----------
        filename (str, optional):
            The path to the YAML file to load settings from.

        **kwargs:
            Arbitrary keyword arguments to set as attributes.
            (Overrides attributes in YAML file if provided.)
        """
        settings = self.load_settings(filename=filename, **kwargs)
        for key, value in settings.items():
            # print(key, value)
            setattr(self, key, value)

    def load_settings(self, filename=None, **kwargs):
        """
        Load settings from a YAML file and/or keyword arguments.
        Parameters
        ----------
        filename (str, optional):
            The path to the YAML file to load settings from.
            If not provided, defaults to None.
        **kwargs:
            Arbitrary keyword arguments to set as attributes.
            These will override attributes loaded from the YAML file if provided.
        """

        if filename:
            with open(filename, 'r', encoding="utf-8") as file:
                settings = yaml.safe_load(file) if filename else None
        else:
            settings = {}

        for key, value in kwargs.items():
            settings[key] = value

        return settings

pss_export_config = Config(filename="skm_pss_adapters/pss_export_config.yaml")
pss_schema_config = Config(filename="skm_pss_adapters/pss_schema_config.yaml")
