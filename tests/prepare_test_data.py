import os
import sys
from typing import Optional, Any, Dict

import click

from .apiclient.utils import strip_url_path, build_request_file_name, build_index_file_path, load_index_data, IndexData


_ALLOWED_HEADER_KEYS = {'Content-Type'}


def replace_query_param(url: str, query_param_name: str, query_param_value: Optional[str]) -> str:
    import urllib.parse

    parsed_url = urllib.parse.urlparse(url)
    url_query_params = urllib.parse.parse_qsl(parsed_url.query, keep_blank_values=True)

    url_query_params = list(filter(lambda pair: pair[0] != query_param_name, url_query_params))
    if query_param_value is not None:
        url_query_params.append((query_param_name, query_param_value))

    # noinspection PyProtectedMember
    parsed_url = parsed_url._replace(query=urllib.parse.urlencode(url_query_params))
    url = parsed_url.geturl()
    return url


def save_index_data(output_dir: str, all_index_data: IndexData) -> None:
    import yaml

    all_index_data.sort(key=lambda entry: (entry['method'], entry['first_page_url_path'], entry['page_number']))

    index_file_path = build_index_file_path(output_dir)
    with open(index_file_path, 'wt', encoding='utf-8') as fd:
        yaml.safe_dump(all_index_data, fd)


def cleanup_output_dir(output_dir: str):
    all_index_data = load_index_data(output_dir)
    referenced_json_files = set(entry['file_name'] for entry in all_index_data)
    existing_json_files = {file_name for file_name in os.listdir(output_dir)
                           if os.path.isfile(os.path.join(output_dir, file_name))
                           and os.path.splitext(file_name)[1] == '.json'}
    non_referenced_json_files = existing_json_files - referenced_json_files

    if not non_referenced_json_files:
        return

    print(f'Removing {len(non_referenced_json_files)} unreferenced file(s)', file=sys.stderr)

    for non_referenced_json_file in non_referenced_json_files:
        os.unlink(os.path.join(output_dir, non_referenced_json_file))


def remove_index_data(output_dir: str, method: str, first_page_url: str) -> None:
    first_page_url_path = strip_url_path(first_page_url)

    all_index_data = load_index_data(output_dir)
    all_index_data = [entry for entry in all_index_data
                      if not (entry['method'] == method
                              and entry['first_page_url_path'] == first_page_url_path)]
    save_index_data(output_dir, all_index_data)


def add_index_data(index_data: Dict[str, Any], output_dir: str) -> None:
    all_index_data = load_index_data(output_dir)
    all_index_data = [entry for entry in all_index_data
                      if not (entry['method'] == index_data['method']
                              and entry['url_path'] == index_data['url_path'])]

    all_index_data.append(index_data)
    save_index_data(output_dir, all_index_data)


@click.command()
@click.option('--auth-key', '-a',
              help='Airtable authorization key (will be prompted if not given).')
@click.option('--fields', metavar='COLUMN[,COLUMN...]',
              help='List of fields to fetch.')
@click.option('--filter-formula', '-f',
              help='Filter formula.')
@click.option('--method', '-m', default='GET', type=str.upper,
              help='Request method, such as GET, POST, PATCH, DELETE (default=GET).')
@click.option('--output-dir', '-o', default=os.path.join('.', 'server_mockup_data'),
              help='Output directory (default="./server_mockup_data").')
@click.option('--page-size', '-n', type=int,
              help='Max. number of records returned per page.')
@click.argument('table_name')
@click.argument('record_id', required=False, default=None)
def cli(method: str,
        output_dir: str,
        table_name: str,
        record_id: Optional[str],
        auth_key: Optional[str] = None,
        fields: Optional[str] = None,
        filter_formula: Optional[str] = None,
        page_size: Optional[int] = None):
    """
    Send a request to the Airtable server and save the results on disk as a regression test case.
    """
    import asyncio
    import urllib.parse
    import aiohttp
    import simplejson

    table_name = {
        'municipios': 'Municípios',
        'regioes': 'Regiões',
        'uf': 'Unidades Federativas',
    }.get(table_name.lower(), table_name)

    if record_id is not None:
        if fields is not None:
            raise RuntimeError('--fields cannot be used when a record ID is given')
        if filter_formula is not None:
            raise RuntimeError('--filter-formula cannot be used when a record ID is given')

    if auth_key is None:
        from getpass import getpass
        auth_key = getpass('Airtable authorization key: ')

    url = f'https://api.airtable.com/v0/appW6zowdGl1nrt4v/{urllib.parse.quote(table_name)}'
    if record_id is not None:
        url += f'/{urllib.parse.quote(record_id)}'

    parsed_url = urllib.parse.urlparse(url)
    url_query_params = []

    if fields is not None:
        for field in fields.split(','):
            url_query_params.append(('fields[]', field))

    if filter_formula is not None:
        url_query_params.append(('filterByFormula', filter_formula))

    if page_size is not None:
        url_query_params.append(('pageSize', str(page_size)))

    headers = {
        'Authorization': f'Bearer {auth_key}',
    }

    # noinspection PyProtectedMember
    parsed_url = parsed_url._replace(query=urllib.parse.urlencode(url_query_params))
    url = parsed_url.geturl()
    del parsed_url, fields, filter_formula, page_size, url_query_params

    os.makedirs(output_dir, exist_ok=True)

    # noinspection PyShadowingNames
    async def paginate(url: str):
        page_number = 0
        previous_file_name = None
        previous_url = None
        first_page_url_path = strip_url_path(url)
        total_record_count = 0

        file_name = build_request_file_name(method, url)
        remove_index_data(output_dir=output_dir, method=method, first_page_url=url)

        async with aiohttp.ClientSession() as session:
            while url is not None:
                page_number += 1
                print(f'Getting page {page_number}', file=sys.stderr)

                async with session.request(method, url, headers=headers) as response:
                    response_status = response.status
                    response_headers = response.headers
                    response_content = await response.text()
                    response_data = await response.json()

                next_offset = (response_data or {}).get('offset')
                if next_offset is not None:
                    next_url = replace_query_param(url, 'offset', next_offset)
                    next_file_name = build_request_file_name(method, next_url)
                else:
                    next_url = None
                    next_file_name = None

                record_list = (response_data or {}).get('records')
                if record_list is not None:
                    record_count = len(record_list)
                elif record_id is not None and response_status == 200:
                    record_count = 1
                else:
                    record_count = None

                total_record_count += record_count or 0

                request_data = {
                    'page_number': page_number,
                    'method': method,
                    'url': url,
                    'response': {
                        'status_code': response_status,
                        'headers': [(key, value) for key, value in response_headers.items()
                                    if key in _ALLOWED_HEADER_KEYS],
                        'content': response_content,
                    }
                }
                if previous_url is not None:
                    request_data['previous_url'] = previous_url
                if next_url is not None:
                    request_data['next_url'] = next_url
                if previous_file_name is not None:
                    request_data['previous_file_name'] = previous_file_name
                if next_file_name is not None:
                    request_data['next_file_name'] = next_file_name

                file_path = os.path.join(output_dir, file_name)
                print(f'Saving to {file_path}', file=sys.stderr)
                with open(file_path, 'wt', encoding='utf-8') as fd:
                    simplejson.dump(request_data, fd, ensure_ascii=False, separators=(',', ':'))

                index_data = {
                    'method': method,
                    'original_url': url,
                    'record_count': record_count,
                    'url_path': strip_url_path(url),
                    'first_page_url_path': first_page_url_path,
                    'file_name': file_name,
                    'page_number': page_number
                }
                add_index_data(index_data, output_dir=output_dir)

                previous_file_name = file_name
                previous_url = url
                url = next_url
                file_name = next_file_name

        print(f'Total record count: {total_record_count}', file=sys.stderr)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(paginate(url))

    cleanup_output_dir(output_dir)


if __name__ == '__main__':
    cli()
