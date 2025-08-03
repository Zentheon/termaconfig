# example.py

import logging as log
from pathlib import Path
from terminaltables3 import AsciiTable, SingleTable, DoubleTable

from configobj import ConfigObj, ConfigObjError
from configobj.validate import Validator

from zenconfig import ConfigTables, ErrorTree

class ConfigLoader:
    """Uses ConfigObj and ZenConfig to handle everything configuration-related"""

    def __init__(self, config_path, spec_path):
        self.config_path = Path(config_path)
        self.spec_path = Path(spec_path)
        log.debug(f"Config path: {self.config_path} with spec file: {self.spec_path}")

        self.config = {}
        self.spec = {}
        self.load_config()

        # Try passing another tabletype! AsciiTable and DoubleTable are also valid.
        # Defaults to SingleTable if tabletype wasn't provided.
        # For even greater customization, try extending the terminaltables AsciiTable class.
        config_tables = ConfigTables(self.config, self.spec, tabletype=DoubleTable)
        print()
        print(config_tables.all_tables)

    def load_config(self):
        # Load and validate config file
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found at: {self.config_path}")

            spec_data = open(self.spec_path, 'r')

            with open(self.config_path, 'r') as config_data:
                config = ConfigObj(config_data, configspec=spec_data)

            spec = config.configspec
            vtor = Validator()
            result = config.validate(vtor, preserve_errors=True)

            errortree = ErrorTree(config, spec, result)
            errortree.flatten_errors = True

            if errortree.get_tree:
                print(errortree.get_tree)

            self.config = config
            self.spec = spec
            log.debug(f"Config loader returned results: {result}")
            log.debug(self.config)

        except ConfigObjError:
            raise # Add your own handling logic

    def __getitem__(self, key):
            # Allows dictionary access using regular subscript
            # You can also trigger any kind of logic you want whenever your config is accessed
            if not key in self.config:
                raise KeyError(f"Key '{key}' not found in config")
            log.debug(f"Accessed config item via getitem: {key}")
            return self.config[key]

if __name__ == '__main__':
    config_path = 'example-config.toml'
    spec_path = 'example-spec.toml'

    config = ConfigLoader(config_path, spec_path)

    print("Here's the value of 'option1' in 'section1':", config['section1']['option1'])
