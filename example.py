# example.py

import logging as log
from terminaltables3 import AsciiTable, SingleTable, DoubleTable

from zenconfig import ZenConfig, ConfigValidationError

log.basicConfig(
    level = log.INFO,
    format = '%(asctime)s:%(name)s:%(levelname)s: %(message)s',
    datefmt = '%H:%M:%S'
)

if __name__ == '__main__':
    config_path = 'example-config.toml'
    spec_path = 'example-spec.toml'

    try:
        config = ZenConfig(
            config_path,
            spec_path,
            tabletype = DoubleTable,
            logging = True
        )
    except ConfigValidationError:
        print()
        print("Errors are present in configuration. Exiting...")
        exit()

    print()
    print("Here's the value of 'option1' in 'basic':", config['basic']['option1'])
