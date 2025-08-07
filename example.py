# example.py

import logging as log
from terminaltables3 import AsciiTable, DoubleTable

from termaconfig import TermaConfig, ConfigValidationError

log.basicConfig(
    level = log.INFO,
    format = '%(asctime)s:%(name)s:%(levelname)s: %(message)s',
    datefmt = '%H:%M:%S'
)

if __name__ == '__main__':
    config_path = 'example-config.toml'
    spec_path = 'example-spec.toml'

    try:
        config = TermaConfig(
            config_path,
            spec_path,
            # tabletype can be any valid terminaltables3 class instance.
            # Try passing another! Another valid option is AsciiTable
            # SingleTable is used by default if none was provided.
            tabletype = DoubleTable,
            logging = False
        )
    except ConfigValidationError:
        print()
        print("Errors are present in configuration. Exiting...")
        exit()

    print()
    print("Here's the value of 'option1' in 'basic':", config['basic']['option1'])
