# termaconfig/errortree.py

from printree import ftree

from termaconfig.utils import (
    get_nested_value,
    squash_true_dicts,
    strip_metakeys,
    parse_string_values,
    split_dot_notated_keys
)

class ErrorTree:
    """Takes config, spec and pre-processed error results to make easily readable error trees."""
    def __init__(self, metaconf, **kwargs):
        self.delimiter = kwargs.get('delimiter', '__')

        self.include_missing = kwargs.get('include_missing', True)
        self.include_valid = kwargs.get('include_valid', False)
        if not isinstance(self.include_missing, bool):
            raise TypeError(f"Expected include_missing to be a boolean, got: {self.include_missing}")
        if not isinstance(self.include_valid, bool):
            raise TypeError(f"Expected include_valid to be a boolean, got: {self.include_valid}")

        self.metaconf = metaconf
        # Set to false if any errors show up
        self.valid = True
        self.build_tree()

    @property
    def get_tree(self) -> str:
        """
        Generates a tree-like string representation of any configuration errors.

        Returns:
            str: A visual representation of self.tree using printree.
        """
        return ftree(self.tree)

    def build_tree(self):
        """Traverses the metaconf and constructs a self.tree dict for use with tree-printing utilities."""
        if not hasattr(self, 'metaconf'):
            raise AttributeError("metaconf attribute is required before calling this method.")

        metaconf = split_dot_notated_keys(self.metaconf, 'children')
        self.tree = {}

        def traverse_dict(metaconf_sec, tree_sec):
            for section, section_data in metaconf_sec.items():
                tree_sec[section] = {}
                if not isinstance(section_data, dict): continue

                if 'data' in section_data:
                    for conf_key, conf_data in section_data['data'].items():

                        # Check missing and error conditions
                        if conf_data['missing'] and self.include_missing:
                            self.valid = False
                            tree_sec[section][conf_key] = "\033[1mMissing\033[0m"
                        elif conf_data.get('error') is None and self.include_valid:
                            tree_sec[section][conf_key] = "Valid"
                        elif not conf_data['error']: continue
                        else:
                            self.valid = False
                            tree_sec[section][conf_key] = {
                                '\033[1merror\033[0m': f"\033[1m{conf_data['error']}\033[0m",
                                '': '\033[1m^^^^^' + '^' * len(conf_data['error']) + '\033[0m',
                                'expected': conf_data.get('type'),
                                'default': conf_data.get('default', None),
                            }
                            # Only add min/max if not None
                            if conf_data['min']:
                                tree_sec[section][conf_key]['min'] = conf_data['min']
                            if conf_data['max']:
                                tree_sec[section][conf_key]['max'] = conf_data['max']

                # Child sections processed after options, which looks cleaner
                if 'children' in section_data:
                    for child_sec in section_data['children']:
                        traverse_dict(section_data['children'], tree_sec[section])

        traverse_dict(metaconf, self.tree)
