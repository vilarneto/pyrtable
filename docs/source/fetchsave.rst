Retrieving and saving records
=============================

Once you have :ref:`created your Pyrtable classes <Record classes>`, it's now time to actually communicate with the server.

There are three ways to fetch records: you can get :ref:`all records of a table <BaseRecord.all>`, :ref:`only those that meet a given criteria <BaseRecord.filter>`, or :ref:`a single record from a record ID <BaseRecord.get>`.

You can also update the server by :ref:`updating records <BaseRecord.update>`, :ref:`creating records <BaseRecord.create>` and :ref:`deleting records <BaseRecord.delete>`.

From now on, the record class will be referred as :class:`MyTableRecord`.

.. _BaseRecord.all:

.. index::
   single: all()
   single: Fetching records; Entire table
   single: CRUD operations; Retrieving (fetching) all records

Retrieving all records
----------------------

:class:`MyTableRecord.objects.all()` can be used to traverse all records of the corresponding Airtable table::

    # Assuming that MyTableRecord has a `name` field
    for record in MyTableRecord.objects.all():
        print('Record with ID %s has a name %s.' % (record.id, record.name))

Notice that ``MyTableRecord.objects.all()`` will give an *iterator*, not a list of records itself. This means that calling this method will not hit the server — that will happen every time you iterate over that. In other words::

    # This will not yet fetch records with the server
    all_records_query = MyTableRecord.objects.all()

    # This loop will fetch data from the server
    for record in all_records_query:
        print('Record with ID %s has a name %s.' % (record.id, record.name))

    # This will fetch data all over again
    for record in all_records_query:
        print('Person named %s has %d years old' % (record.name, record.age))

If you want to fetch data only once, you need to make a list out of the iterator right on the beginning::

    # This will hit the server and fetch all records
    all_records = list(MyTableRecord.objects.all())

    # From now on, `all_records` holds all records -
    # iterating over it will not fetch data from the server.

.. _BaseRecord.filter:

.. index::
   single: filter()
   single: Fetching records; Filtering
   single: CRUD operations; Retrieving (fetching) some records

Retrieving some records
-----------------------

If you want to fetch only records that match given criteria, you can use :class:`MyTableRecord.objects.filter()`. It's also an iterator, so fetching will not happen until you actually iterate over elements::

    # Filter by equality
    query = MyTableRecord.objects.filter(first_name='John')
    query = MyTableRecord.objects.filter(age=30)
    query = MyTableRecord.objects.filter(is_admin=True)
    query = MyTableRecord.objects.filter(role=Role.MANAGER)

    # Filter MultipleSelectionField fields
    query = MyTableRecord.objects.filter(role__contains=(Role.DEVELOPER, Role.MANAGER))
    query = MyTableRecord.objects.filter(role__excludes=(Role.DEVELOPER, Role.MANAGER))

    # Filter by inequality:
    # - “not equals”
    query = MyTableRecord.objects.filter(first_name_ne='John')
    # - “greater than”
    query = MyTableRecord.objects.filter(age__gt=30)
    # - “greater than or equals”
    query = MyTableRecord.objects.filter(age__gte=30)
    # - “less than”
    query = MyTableRecord.objects.filter(age__lt=30)
    # - “less than or equals”
    query = MyTableRecord.objects.filter(age__lte=30)
    # - “is empty”
    query = MyTableRecord.objects.filter(age__empty=True)

    # Multiple criteria can be specified - they are ANDed together
    query = MyTableRecord.objects.filter(
            first_name='John', last_name='Doe', age__gt=30)

Filters can be further narrowed before iteration, so the following pattern is perfectly valid::

    def get_admins(managers_only=False):
        query = MyTableRecord.objects.filter(is_admin=True)
        if managers_only:
            query = query.filter(role=Role.MANAGER)

        # Server will be queried here
        return list(query)

Actually :class:`MyTableRecord.objects.all()` also has a ``.filter()`` method, so you can start with “all” (meaning “no filters”) and narrow them down before hitting the server::

    def get_employees(admin_only=False, managers_only=False):
        query = MyTableRecord.objects.all()
        if admin_only:
            query = query.filter(is_admin=True)
        if managers_only:
            query = query.filter(role=Role.MANAGER)

        # Server will be queried here
        return list(query)

Extended syntax and ORing criteria
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The basic usage of :class:`MyTableRecord.objects.filter()` — using property names as named arguments — will not allow one to use alternative criteria, as all of them will be ANDed together. To use that, the :class:`Q` operator can be used to encapsulate independent criteria that can be combined with the ``||`` (double-pipe) operator::

    from pyrtable.filters import Q

    query = MyTableRecord.objects.filter(
            Q(first_name='John') || Q(first_name='Jane'))

The :class:`Q` operator will also accept ``&&`` (double-ampersand) to combine with AND and ``~`` (tilde) to invert (negate) the enclosed criteria::

    from pyrtable.filters import Q

    # These are all the same:
    query = MyTableRecord.objects.filter(
            first_name='John', last_name='Doe', age__ne=30)
    query = MyTableRecord.objects.filter(
            Q(first_name='John') && Q(last_name='Doe') && Q(age__ne=30))
    query = MyTableRecord.objects.filter(
            Q(first_name='John') && Q(last_name='Doe') && ~Q(age=30))

.. _BaseRecord.get:

.. index::
   single: get()
   single: Fetching records; Single record
   single: CRUD operations; Retrieving (fetching) a single record

Retrieving a single record
--------------------------

If you have the Airtable record ID, you can use :class:`MyTableRecord.objects.get(id)` to retrieve the corresponding record. However, referencing a record by its ID is not required for common use cases.

.. _BaseRecord.update:
.. index::
   single: save()
   single: Updating records
   single: CRUD operations; Updating records

Updating records
----------------

Changing record properties is allowed for any field not declared with ``read_only=True``. However, you must tell Pyrtable that you want to persist these changes in the server. To do that you call the record's ``.save()`` method::

    # Create a query to fetch people named “John Doe”
    # (remember, this does not hit the server yet)
    query = MyTableRecord.objects.filter(
        first_name='John', last_name='Doe')

    # Get the first record that matches the filtering criteria
    record = next(iter(query))

    # Change some values
    record.last_name = 'Chloe'
    record.age = 35

    # Send (persist) changes to the server
    record.save()

Pyrtable is clever enough to avoid sending a server request if no changes were made in the record::

    record.age += 10
    record.age -= 10
    # The last operation reverted the former one:
    # at the end the record did not change at all.
    # The next call will *not* send a server request:
    record.save()

.. _BaseRecord.create:

.. index::
   single: save()
   single: Updating records
   single: CRUD operations; Creating records

Creating records
----------------

To create a record, you first populate its field values and then call the ``.save()`` method::

    # Create the object and set the properties one by one
    new_record = MyTableRecord()
    new_record.first_name = 'John'
    new_record.last_name = 'Doe'
    new_record.age = 35

    # You can also set (some) properties when creating the object
    new_record = MyTableRecord(
        first_name='John', last_name='Doe', age=35)

    # Create the record in the server
    new_record.save()

.. _BaseRecord.delete:

.. index::
   single: delete()
   single: Deleting records
   single: CRUD operations; Deleting records

Deleting records
----------------

A record can be deleted from the server by calling its ``.delete()`` method::

    query = MyTableRecord.objects.filter(
        first_name='John', last_name='Doe')
    record = next(iter(query))

    # Delete this record
    record.delete()
