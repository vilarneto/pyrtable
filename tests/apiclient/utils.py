import os
from typing import List, Dict, Any


def build_hash_value(hasher, value: Any):
    import simplejson

    json = simplejson.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    hasher.update(json.encode('utf-8'))


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


def build_request_hash(method: str, url: str, data: Any) -> str:
    import hashlib

    url = strip_url_path(url)
    hasher = hashlib.sha1()

    hasher.update(method.encode('utf-8'))
    hasher.update(b':')
    hasher.update(url.encode('utf-8'))

    if data is not None:
        hasher.update(b':')
        build_hash_value(hasher, data)

    return hasher.hexdigest()


def build_request_file_name(method: str, url: str, data: Any) -> str:
    request_hash = build_request_hash(method, url, data)
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


__all__ = ['IndexData', 'build_hash_value', 'strip_url_path', 'build_request_hash', 'build_request_file_name',
           'build_index_file_path', 'load_index_data']
