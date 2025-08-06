# zenconfig/errortree.py

from zenconfig.utils import (
    get_nested_value,
    squash_true_dicts,
    strip_metakeys,
    parse_string_values
)

class ErrorTree:
    """Takes config, spec and pre-processed error results to make easily readable error trees."""
    def __init__(self, config, spec, result, **kwargs):
        self.delimiter = kwargs.get('delimiter', '__')
        self.subsection_header = kwargs.get('subsection_header', '⤷ ')

        self.config = config
        self.spec = spec
        self.result = result
        self.flatten_errors = False
        self.strip_metakeys = True
        self.indent = 1

    @property
    def get_tree(self):
        """
        Generates a tree-like string representation of error messages from the supplied results.

        Returns:
            str or None: A formatted string containing the error tree, or None if there are no errors to report.
        """
        if self.strip_metakeys:
            self.result = strip_metakeys(self.result, self.delimiter)
            self.result = squash_true_dicts(self.result)

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

            # Skip entries that passed validation
            if error_entry['error'] == 'True':
                continue

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
                    if idx != 1: tree_str += '\n' + line
                    else: tree_str = line
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
        Gathers and formats problematic config params with the associated specification entries
        and creates a formatted list of dicts for further processing into readable info.
        """
        error_list = []

        def traverse_results(d, section_path=[]):
            if isinstance(d, dict):
                for key, value in d.items():
                    new_section_path = section_path + [key]
                    if isinstance(value, dict):
                        traverse_results(value, new_section_path)
                    else:
                        if value is True: error = None
                        if value is False: error = 'Missing value or section.'
                        else: error = value

                        spec_value = get_nested_value(spec, new_section_path)
                        spec_type, spec_params = parse_string_values(spec_value)
                        min_val, max_val, default = self.get_spec_params(spec_params)

                        error_list.append({
                            'path': new_section_path,
                            'error': str(error),
                            'spec': spec_value,
                            'type': spec_type,
                            'default': default,
                            'min': min_val,
                            'max': max_val
                        })
            elif isinstance(d, list):
                for idx, item in enumerate(d):
                    new_section_path = section_path + [f"item{idx}"]
                    traverse_results(item, new_section_path)

        traverse_results(result)

        return error_list

    def get_spec_params(self, spec_params):
        """Extracts type and constraints from the specification string."""
        # Handle both possible types of minmax entries (valueless and key=value pairs)
        min_val, max_val = None, None
        if not isinstance(spec_params, dict):
            return min_val, max_val, None
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
        else: default = None

        return min_val, max_val, default
