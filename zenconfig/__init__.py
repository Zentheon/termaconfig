# zenconfig/__init__.py

import io
import logging as log

from configobj import ConfigObj
from configobj.validate import Validator

from zenconfig.exceptions import ConfigValidationError, TableTypeError
from zenconfig.utils import preprocess_config

# Access the main classes from package root
from zenconfig.parser import ConfigParser
from zenconfig.configtables import ConfigTables
from zenconfig.errortree import ErrorTree
ErrorTree = ErrorTree
ConfigTables = ConfigTables

ConfigValidationError = ConfigValidationError
TableTypeError = TableTypeError

class ZenConfig(ConfigObj):
    def __init__(self, config_file, spec_file, **kwargs):
        config_file, spec_file = self.validate_files(config_file, spec_file)

        config_lines = preprocess_config(config_file)
        spec_lines = preprocess_config(spec_file)
        super().__init__(config_lines, configspec=spec_lines)
        # This is how we access the config options after letting ConfigObj initialize
        config = self.__dict__['parent']

        # Create the error tree, print it and exit
        result = config.validate(Validator(), preserve_errors=True)

        parser = ConfigParser(config, config.configspec, result)
        self.meta_conf = parser.metaconf

        self.errortree = ErrorTree(config, config.configspec, result)
        tree_str = self.errortree.get_tree
        if tree_str:
            if kwargs.get('logging', False):
                for line in tree_str.splitlines():
                    log.log(log.INFO + 3, line)
            else:
                print(tree_str)

            raise ConfigValidationError(f"The configuration at {config_file} failed validation")

        tabletype = kwargs.get('tabletype', None)
        config_tables = ConfigTables(self.meta_conf, config, tabletype=tabletype)
        if config_tables.all_tables:
            if kwargs.get('logging', False):
                log.log(log.INFO + 3, '')
                for line in config_tables.all_tables.splitlines():
                    log.log(log.INFO + 3, line)
            else:
                print()
                print(config_tables.all_tables)

    def validate_files(self, config_file, spec_file):
        if isinstance(config_file, str):
            try: config_file = open(config_file, 'r')
            except FileNotFoundError:
                raise FileNotFoundError(f"Config file not found: {config_file}")
            except PermissionError:
                raise PermissionError(f"Failed opening config file: {spec_file}")
        if isinstance(spec_file, str):
            try: spec_file = open(spec_file, 'r')
            except FileNotFoundError:
                raise FileNotFoundError(f"Specification file not found: {spec_file}")
            except PermissionError:
                raise PermissionError(f"Failed opening specification file: {spec_file}")

        if not isinstance(config_file, io.TextIOBase):
            raise TypeError(f"Input config is neither a filepath nor filedata object: {config_file}")
        if not isinstance(spec_file, io.TextIOBase):
            raise TypeError(f"Input specification is neither a filepath nor filedata object: {spec_file}")

        return config_file, spec_file
