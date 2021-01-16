# Pyrtable: Python framework for interfacing with Airtable

Pyrtable is a Python 3 library to interface with [Airtable](https://airtable.com)'s REST API.

There are other Python projects to deal with Airtable. However, most of them basically offer a thin layer to ease authentication and filtering – at the end, the programmer still has to manually deal with JSON encoding/decoding, pagination, request rate limits, and so on.

Pyrtable is a high-level, ORM-like library that hides all these details. It performs automatic mapping between Airtable records and Python objects, allowing CRUD operations while aiming to be intuitive and fun. Programmers used to [Django](https://www.djangoproject.com) will find many similarities and will (hopefully) be able to interface with Airtable bases in just a couple of minutes.

## What does it look like?

Ok, let's have a taste of how one can define a class that maps onto records of a table:

````python
import enum
from pyrtable.record import BaseRecord
from pyrtable.fields import StringField, DateField, SingleSelectionField, \
        SingleRecordLinkField, MultipleRecordLinkField

class Role(enum.Enum):
    DEVELOPER = 'Developer'
    MANAGER = 'Manager'
    CEO = 'C.E.O.'

class EmployeeRecord(BaseRecord):
    class Meta:
        # Open “Help > API documentation” in Airtable and search for a line
        # starting with “The ID of this base is XXX”.
        base_id = 'appABCDE12345'
        table_id = 'Employees'

    @classmethod
    def get_api_key(cls):
        # The API key can be generated in you Airtable Account page. 
        # DO NOT COMMIT THIS STRING!
        return 'keyABCDE12345'

    name = StringField('Name')
    birth_date = DateField('Birth date')
    office = SingleRecordLinkField('Office', linked_class='OfficeRecord')
    projects = MultipleRecordLinkField(
            'Allocated in projects', linked_class='ProjectRecord')
    role = SingleSelectionField('Role', choices=Role)
````

After that, common operations are pretty simple:

````python
# Iterating over all records
for employee in EmployeeRecord.objects.all():
    print("%s is currently working on %d project(s)" % (
        employee.name, len(employee.projects)))

# Filtering
for employee in EmployeeRecord.objects.filter(
        birth_date__gte=datetime.datetime(2001, 1, 1)):
    print("%s was born in this century!" % employee.name)

# Creating, updating and deleting a record
new_employee = EmployeeRecord(
    name='John Doe',
    birth_date=datetime.date(1980, 5, 10),
    role=Role.DEVELOPER)
new_employee.save()

new_employee.role = Role.MANAGER
new_employee.save()

new_employee.delete()
````

Notice that we don't deal with Airtable column or table names once record classes are defined.

## Beyond the basics

Keep in mind that Airtable is *not* a database system and is not really designed for tasks that need changing tons of data. In fact, only fetch (list) operations are batched – insert/update/delete operations are limited to a single record per request, and Airtable imposes a 5 requests per second limit even for paid accounts. You will need a full minute to update 300 records!
 
That said, Pyrtable will respect that limit. In fact, it will track dirty fields to avoid unnecessary server requests and will render `.save()` calls as no-ops for unchanged objects. That also works with multiple threads, so the following pattern can be used to update and/or create several records:

```python
from concurrent.futures.thread import ThreadPoolExecutor

all_records = list(EmployeeRecord.objects.all())

# Do operations that change some records here
# No need to keep track of which records were changed

with ThreadPoolExecutor(max_workers=10) as executor:
    for record in all_records:
        executor.submit(record.save)
```

Or, if you want a really nice [tqdm](https://tqdm.github.io) progress bar:

```python
from tqdm import tqdm

with ThreadPoolExecutor(max_workers=10) as executor:
    for _ in tqdm(executor.map(lambda record: record.save(), all_records),
                  total=len(all_records), dynamic_ncols=True, unit='',
                  desc='Updating Airtable records'):
        pass
```

Pyrtable also has some extra tools to cache data and read authentication keys from external JSON/YAML files check out the `APIKeyFromSecretsFileMixin` mixin class. Remember to never commit sensitive data to your repository, as Airtable authentication allows **full R/W access to all your bases** with a single API key!

## Compatibility

Pyrtable is compatible with Python 3.7 and 3.8. Previous 3.x versions may or may not work. Python 2.x is not supported at all. 

## Documentation

Technical documentation is available at https://pyrtable.readthedocs.io.

## Questions, bug reports, improvements

Want to try it out, contribute, suggest, offer a hand? Great! The project is available at https://github.com/vilarneto/pyrtable.

## License

Pyrtable is released under [MIT license](https://opensource.org/licenses/MIT).

Copyright (c) 2020,2021 Vilar Fiuza da Camara Neto
