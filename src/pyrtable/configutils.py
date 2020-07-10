import os
import threading
from typing import List, Optional


_config_dirs: Optional[List[str]] = None
_config_dirs_lock = threading.Lock()


def get_config_dirs() -> List[str]:
    global _config_dirs

    import os

    with _config_dirs_lock:
        if _config_dirs is None:
            _config_dirs = os.environ.get('PYRTABLE_CONFIG_DIRS')
            if _config_dirs is not None:
                _config_dirs = _config_dirs.split(':')

        if _config_dirs is None:
            home_dir = os.path.expanduser('~')
            _config_dirs = [
                os.path.join(os.getcwd(), 'config'),
                os.path.join(home_dir, '.config', 'airtable'),
                '/etc/airtable']

    general_config_dir = os.environ.get('CONFIG_DIR')
    if general_config_dir is not None:
        _config_dirs.insert(0, general_config_dir)

    return _config_dirs


def find_config_file(filename: str) -> str:
    for candidate_dir in get_config_dirs():
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


__all__ = ['get_config_dirs', 'find_config_file', 'load_config_file']
