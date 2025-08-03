# zenconfig/configtables.py

from zenconfig.utils import (
    flatten_errors,
    get_nested_value,
    get_values_from_string,
    squash_bool_dict_tree,
    strip_metakeys
)

class ErrorTree:
    """Takes config, spec and pre-processed error results to make easily readable error trees."""
    def __init__(self, config, spec, result):
        self.config = config
        self.spec = spec
        self.result = result
        self.flatten_errors = False
        self.strip_metakeys = True
        self.indent = 1

        self.subsection_header = "⤷ "

    @property
    def get_tree(self):
        """
        Generates a tree-like string representation of error messages from the supplied results.

        Returns:
            str or None: A formatted string containing the error tree, or None if there are no errors to report.
        """
        if self.strip_metakeys:
            self.result = strip_metakeys(self.result)
            self.result = squash_bool_dict_tree(self.result)
        if self.flatten_errors:
            self.result = flatten_errors(self.config, self.result)

        error_list = self.process_results(self.config, self.spec, self.result)

        tree_str = self.format_error_table(error_list)
        return tree_str

    def format_error_table(self, error_list):
        """Makes some nice pretty-printed messages of a pre-formatted error list"""
        tree_str = ''
        indent = -1
        for idx, error_entry in enumerate(error_list):
            path = error_entry['path']
            message = error_entry['error']
            type_info = self._create_type_info(error_entry)

            for line in path:
                if line == path[-1]:
                    # Final line. Include message from ConfigObjError and associated spec.
                    tree_str += '\n' + ' ' * indent + f"{self.subsection_header}{line}: {message}"
                    tree_str += '\n' + ' ' * (indent + 2) + f"{self.subsection_header}{type_info}"
                    indent = -1
                elif indent == -1:
                    # First line. No fancy formatting, and indent gets set to 0,
                    # which makes the next line have no leading whitespace.
                    # Also skip adding newline on the first iteration.
                    if idx == 1: tree_str += '\n' + line
                    else: tree_str += line
                    indent += 1
                else:
                    tree_str += '\n' + ' ' * indent + f"{self.subsection_header}{line}"
                    indent += 2
        if tree_str != '':
            return tree_str
        else: return None

    def _create_type_info(self, error_entry) -> str:
        """Creates a string that describes the type and constraints of an error entry."""

        val_type = error_entry['type']
        min_val = error_entry['min']
        max_val = error_entry['max']
        default = error_entry['default']

        type_info = f"Expected {val_type}"
        if min_val and max_val:
            type_info += f" (min={min_val}, max={max_val})"
        elif min_val:
            type_info += f" (min={min_val})"
        elif max_val:
            type_info += f" (max={max_val})"

        if default:
            type_info += f": Default: {default}"

        return type_info

    def process_results(self, config, spec, result):
        """
        Gathers and formats problematic config params with the assotiated specification entries
        and creates a formatted list of dicts for further processing into readable info.
        """
        error_list = []
        if result is True:
            return None
        for entry in result:
            section_list, key, error = entry

            if '@' in key:
                continue
            if key is not None:
                section_list.append(key)
            else:
                section_list.append('[missing section]')
            spec_value = get_nested_value(spec, section_list)
            if error == False:
                error = 'Missing value or section.'

            val_type = spec_value.split('(')[0]
            spec_params = get_values_from_string(spec_value)
            default = ""

            # Handle both possible types of minmax entries (valueless and key=value pairs)
            min_val, max_val = None, None
            for k, v in spec_params.items():
                if v is None:
                    if min_val is None:
                        min_val = k
                    else:
                        max_val = k
                        break
            if 'min' in spec_params:
                min_val = spec_params['min']
            if 'max' in spec_params:
                max_val = spec_params['max']

            if 'default' in spec_params:
                default = spec_params['default']
            error_list.append({
                'path': section_list,
                'error': str(error),
                'spec': spec_value,
                'type': val_type,
                'default': default,
                'min': min_val,
                'max': max_val
            })
        return error_list
