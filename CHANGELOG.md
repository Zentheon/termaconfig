
# Changelog
All notable changes to this project will be documented in this file.

and this project adheres to [Semantic Versioning](http://semver.org/).
See [conventional commits](https://www.conventionalcommits.org/) for commit guidelines.

- - -
## 1.0.1 - 2025-08-10

#### Bug Fixes
- 82473b8088dba473e0d2646f552ea9563de84ea8 - metaconf will now always contain possible keys - Zentheon

#### Documentation
- 56d722863627ef1997921d2703a042f349ee4607 - **(readme)** fix old name references and grammar - Zentheon
- 615cd1a2a45b0eb3707dfd5310293fda6c719c41 - add changelog template - Zentheon

#### Miscellaneous Chores
- 1b3b9d2709bceb12b22741d045b8a6fa5186ff1d - cleanup a few imports - Zentheon

#### Style
- 7dff023ef7b9f1f5be1de0a8c5010da497e5b84f - manage versioning with cocogitto - Zentheon

- e8e192aa0845fed1615daab3781142964f893df1 - add basic package metadata to __init__.py - Zentheon

- 4e7e179d1061345fe196e75ded27f208cfb2bdb9 - use Ruff for formatting and linting - Zentheon


- - -
## [1.0.0] - 2025-08-07

Initial release ✨

Main featues:

- Added functionality of ConfigObj spec files for data-driven text tables using any `terminaltables3` class.
- Specially formatted error dicts for use with `printree` or other tools.
- Simple AIO `TermaConfig` class or various component clasess for customizability.
- `metaconf` dict created by `ConfigParser` that contains a bunch of info about everything config-related.
- Formatting options from a specification are added to `metaconf` as provided. Validation-relevant keys will always be present as `None` if not provided.
- A few output tests.

- - -
