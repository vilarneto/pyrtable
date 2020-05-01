import os
import threading


def find_config_file(filename: str) -> str:
    candidate_dirs = ['config', '/etc/airtable']

    for candidate_dir in candidate_dirs:
        if not os.path.isdir(candidate_dir):
            continue
        path = os.path.join(candidate_dir, filename)
        if os.path.isfile(path):
            return path

    raise FileNotFoundError('Cannot find config file %r' % filename)


def _load_config_file(filename: str, loader=None):
    path = find_config_file(filename)
    if not path:
        return None

    if loader is None:
        ext = os.path.splitext(path)[1].lower()
        if ext in ('.yaml', '.yml'):
            # noinspection PyShadowingNames
            def loader(path: str):
                import yaml

                with open(path, 'rt', encoding='utf-8') as fd:
                    return yaml.safe_load(fd)

        elif ext == '.json':
            # noinspection PyShadowingNames
            def loader(path: str):
                import simplejson as json

                with open(path, 'rb') as fd:
                    return json.load(fd, encoding='utf-8')

    if loader is None:
        raise AttributeError('`loader` is None and could not be inferred')

    return loader(path)


_cached_config_files = {}
_cached_config_files_lock = threading.Lock()


def load_config_file(filename: str, loader=None, disable_caching=False):
    global _cached_config_files

    if disable_caching:
        return _load_config_file(filename, loader)

    with _cached_config_files_lock:
        if filename in _cached_config_files:
            return _cached_config_files[filename]

        contents = _load_config_file(filename, loader)
        _cached_config_files[filename] = contents
        return contents


__all__ = ['find_config_file', 'load_config_file']
