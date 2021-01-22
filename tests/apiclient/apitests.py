import enum
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

# noinspection PyProtectedMember
from pyrtable._baseandtable import _BaseAndTableProtocol
from pyrtable.fields import IntegerField, StringField, SingleSelectionField, \
    BooleanField
from pyrtable.record import BaseRecord


# noinspection PyMethodMayBeStatic
class MockupHTTPRequestHandler(BaseHTTPRequestHandler):
    @property
    def mockup_dir(self):
        return os.path.join('.', 'server_mockup_data')

    def _get_request_file_path(self) -> str:
        from .utils import build_request_file_name
        file_name = build_request_file_name(method=self.command, url=self.path)
        return os.path.join(self.mockup_dir, file_name)

    def _load_request_data(self) -> Dict[str, Any]:
        import simplejson

        request_file_path = self._get_request_file_path()

        if not os.path.isfile(request_file_path):
            raise RuntimeError(f'No stored data for {self.command} on URL path {self.path}'
                               f' (missing file: {request_file_path})')

        with open(request_file_path, 'rt', encoding='utf-8') as fd:
            request_data = simplejson.load(fd)

        return request_data

    def _do_any_request(self):
        request_data = self._load_request_data()

        self.send_response(request_data['response']['status_code'])
        for key, value in request_data['response']['headers']:
            self.send_header(key, value)
        self.end_headers()

        self.wfile.write(request_data['response']['content'].encode('utf-8'))

    # noinspection PyPep8Naming
    def do_GET(self):
        self._do_any_request()


class MockupHTTPServer(ThreadingHTTPServer):
    def __init__(self):
        super(MockupHTTPServer, self).__init__(('localhost', 0), MockupHTTPRequestHandler)


class CitySize(enum.Enum):
    VERY_SMALL = 'Pequeno I'
    SMALL = 'Pequeno II'
    MEDIUM = 'Médio'
    LARGE = 'Grande'
    METROPOLIS = 'Metrópole'


class RegionRecord(BaseRecord):
    class Meta:
        api_key = 'MockupAPIKey'
        base_id = 'appW6zowdGl1nrt4v'
        table_id = 'Regiões'

    name = StringField('Nome')


class StateRecord(BaseRecord):
    class Meta:
        api_key = 'MockupAPIKey'
        base_id = 'appW6zowdGl1nrt4v'
        table_id = 'Unidades Federativas'

    code = StringField('Código')
    name = StringField('Nome')


class CityRecord(BaseRecord):
    class Meta:
        api_key = 'MockupAPIKey'
        base_id = 'appW6zowdGl1nrt4v'
        table_id = 'Municípios'

    name = StringField('Nome')
    population = IntegerField('População 2010')
    size = SingleSelectionField('Porte', choices=CitySize)
    is_capital = BooleanField('Capital?')


class APITests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._server = MockupHTTPServer()
        self._server_thread = threading.Thread(target=self._server.serve_forever)
        self._server_thread.start()
        print(f'Mockup server running on localhost:{self._server.server_port}', file=sys.stderr)

        server_root_url = f'http://localhost:{self._server.server_port}/v0'
        _BaseAndTableProtocol._API_ROOT_URL = server_root_url

    def tearDown(self):
        self._server.shutdown()
        self._server.server_close()

    async def test_fetch_single(self):
        city = await CityRecord.objects.get(record_id='recLyBCK45O1od8Li')
        self.assertEqual(city.name, 'Manaus')
        self.assertEqual(city.population, 1802014)
        self.assertEqual(city.size, CitySize.METROPOLIS)
        self.assertTrue(city.is_capital)

        city = await CityRecord.objects.get(record_id='rec1bjgfb5qTHfEeX')
        self.assertEqual(city.name, 'São Paulo')
        self.assertEqual(city.population, 11253503)
        self.assertEqual(city.size, CitySize.METROPOLIS)
        self.assertTrue(city.is_capital)

        region = await RegionRecord.objects.get(record_id='recf3tnhMRerrI2s9')
        self.assertEqual(region.name, 'Norte')

    async def test_fetch_single_fail(self):
        with self.assertRaises(KeyError):
            await CityRecord.objects.get(record_id='rec00000000000000')

        with self.assertRaises(KeyError):
            await RegionRecord.objects.get(record_id='rec00000000000000')

        # Wait -- this should raise a MODEL_ID_NOT_FOUND from the server!
        # But it actually returns data from a valid record of the “Municípios” table.
        # Apparently this is this a server-side error.
        # with self.assertRaises(KeyError):
        #     await RegionRecord.objects.get(record_id='recLyBCK45O1od8Li')

        # Should never happen (even the method typing signatures forbid it),
        # but let's expect a ValueError (and not even hit the server) with a None value
        with self.assertRaises(ValueError):
            await CityRecord.objects.get(record_id=None)

    async def test_fetch_many(self):
        regions = [f async for f in RegionRecord.objects.all()]
        self.assertEqual(len(regions), 5)
        self.assertEqual({region.name for region in regions},
                         {'Centro-Oeste', 'Norte', 'Nordeste', 'Sul', 'Sudeste'})

        states = [f async for f in StateRecord.objects.all()]
        self.assertEqual(len(states), 27)

    async def test_filters(self):
        cities = [f async for f in CityRecord.objects.filter(is_capital=True)]
        self.assertEqual(len(cities), 27)
        self.assertTrue(all(city.is_capital for city in cities))

        cities = [f async for f in CityRecord.objects.filter(name='Bom Jesus')]
        self.assertEqual(len(cities), 5)
        self.assertTrue(all(city.name == 'Bom Jesus' for city in cities))
