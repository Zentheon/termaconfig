# termaconfig/parser.py

import terminaltables3 as tt3

import termaconfig as tc
from termaconfig.exceptions import TableTypeError
import termaconfig.utils as util

class ConfigParser:
    """Creates a combined 'metaconf' dict containing all relevant info about a configuration.

    It's designed and intended for ConfigObj, but will work with any similarly formatted inputs.
    """
    def __init__(self, config, spec, vtd_result, **kwargs):
        self.delimiter = kwargs.get('delimiter', '__')

        self.spec = spec
        self.vtd_result = vtd_result

        self.metaconf = self._traverse_configspec([], config, spec, {})

    def _traverse_configspec(self, keys, config, opperating_dict, metaconf):
        """
        Recursively searches in a provided config specification and an assotiated, validated config.
        A `meta_conf` dict is created containing parsed metakey information, error results, defaults
        and values from the input config.
        """
        # Validate inputs
        if not isinstance(opperating_dict, dict):
            raise TypeError(f"Expected loaded specification dict, not '{opperating_dict}'")
        if not isinstance(config, dict):
            raise TypeError(f"Expected loaded config dict, not '{config}'")

        key_path = '.'.join(keys)
        if key_path and key_path not in metaconf:
            metaconf[key_path] = {}
            metaconf[key_path]['data'] = {}
            metaconf[key_path] = util.fill_required_keys(metaconf[key_path], tc.REQUIRED_SEC_KEYS)
        for key, value in opperating_dict.items():
            value = util.sanitize_str(value)
            current_keys = keys + [key]
            # parent_key is empty if there was nothing before delimiter (section metakey)
            parent_key = key.split(self.delimiter)[0]
            meta_key = key.split(self.delimiter)[-1]
            value_from_config = None
            if parent_key:
                try:
                    value_from_config = util.sanitize_str(util.get_nested_value(config, keys + [parent_key]))
                except KeyError:
                    metaconf[key_path]['data'][parent_key] = {'missing': True}

            if self.delimiter in key:
                # Section configs start with delimiter
                if key.startswith(self.delimiter):
                    metaconf[key_path][meta_key] = value
                # Per-setting values get added to a respective nested dict
                else:
                    # Initialize target setting dict if needed
                    if not parent_key in metaconf[key_path]['data']:
                        metaconf[key_path]['data'][parent_key] = {}

                    metaconf[key_path]['data'][parent_key][meta_key] = value
            elif isinstance(value, dict):
                # Recursively traverse nested sections
                metaconf = self._traverse_configspec(current_keys, config, value, metaconf)
            else:
                data = metaconf[key_path]['data']
                if not key in data:
                    data[key] = {}
                    data[key] = util.fill_required_keys(data[key], tc.REQUIRED_PARAM_KEYS)
                data[key] = self.get_vtd_results(data[key], keys + [parent_key])
                data[key] = self.get_spec_info(data[key], value)
                data[key]['value'] = value_from_config

        return metaconf

    def get_vtd_results(self, data, keys):
        """Retrieves validation results and adds relevant `error` and `missing` entries."""

        try: result = util.get_nested_value(self.vtd_result, keys)
        except KeyError: result = True

        # Value is present and valid
        if result is True:
            data['error'] = None
            data['missing'] = False
        # Value is missing
        elif result is False:
            data['error']  = None
            data['missing'] = True
        # Value is present but invalid
        else:
            data['error'] = str(result)
            data['missing'] = False

        return data

    def get_spec_info(self, data, spec_value):
        """Extracts type and constraints from the specification string."""
        spec_type, spec_params = util.parse_string_values(spec_value)
        # Handle both possible types of minmax entries (valueless and key=value pairs)
        if not isinstance(spec_params, dict):
            data.update({
                'spec': spec_value,
                'type': spec_type
            })
            return data
        for k, v in spec_params.items():
            if v is None:
                if data['min'] is None:
                    data['min'] = k
                else:
                    data['max'] = k
                    break
        if 'min' in spec_params:
            data['min'] = spec_params['min']
        if 'max' in spec_params:
            data['max'] = spec_params['max']

        if 'default' in spec_params:
            default = spec_params['default']
        else: default = None

        data.update({
            'spec': spec_value,
            'type': spec_type,
            'default': default
        })

        return data
