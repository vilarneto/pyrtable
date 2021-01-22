import os
from typing import List, Dict, Any


def strip_url_path(url: str) -> str:
    import urllib.parse

    parsed_url = urllib.parse.urlparse(url)

    url_query_params = urllib.parse.parse_qsl(parsed_url.query, keep_blank_values=True)
    url_query_params.sort()
    url_query_params = [pair for pair in url_query_params
                        if pair[0] != 'pageSize']
    url_query_params.sort()

    # noinspection PyProtectedMember
    parsed_url = parsed_url._replace(scheme='', netloc='', query=urllib.parse.urlencode(url_query_params))

    return parsed_url.geturl()


def build_request_hash(method: str, url: str) -> str:
    import hashlib

    url = strip_url_path(url)
    hasher = hashlib.sha1()

    hasher.update(method.encode('utf-8'))
    hasher.update(b':')
    hasher.update(url.encode('utf-8'))
    return hasher.hexdigest()


def build_request_file_name(method: str, url: str) -> str:
    request_hash = build_request_hash(method, url)
    file_path = f'{method.lower()}-{request_hash}.json'
    return file_path


def build_index_file_path(data_dir: str) -> str:
    return os.path.join(data_dir, 'index.yaml')


IndexData = List[Dict[str, Any]]


def load_index_data(data_dir: str) -> IndexData:
    import yaml

    index_file_path = build_index_file_path(data_dir)

    if os.path.isfile(index_file_path):
        with open(index_file_path, 'rt', encoding='utf-8') as fd:
            all_index_data = yaml.safe_load(fd) or []
    else:
        all_index_data = []

    return all_index_data


__all__ = ['IndexData', 'strip_url_path', 'build_request_hash', 'build_request_file_name', 'build_index_file_path',
           'load_index_data']
