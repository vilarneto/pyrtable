.. _Caching records:
.. index::
   single: Caching; Caching records

Caching records
===============

Pyrtable does not provide any caching mechanism by default. In other words, iterating over a query will always send requests to the server to fetch fresh data.

This, however, can be extremely slow when referring to linked records, i.e., those contained in :class:`SingleRecordLinkField` and :class:`MultipleRecordLinkField` fields. In these cases, the default strategy is to make a new server request *for each linked record*. If you are working on a table with several linked records this will obviously become a waste of resources, especially if some records are linked many times!

To overcome this, Pyrtable offers a caching strategy for linked records. Instead of loading them one by one, you can first fetch all records from the linked table(s), then work normally over the “linking” table. The following example illustrates this strategy::

    # This table contains the records that will be referred to
    # in another table
    class EmployeeRecord(BaseRecord):
        class Meta:
            # Meta data

        name = StringField('Name')

    # This table has a field that links to the first one
    class ProjectRecord(BaseRecord):
        class Meta:
            # Meta data

        team = MultipleRecordLinkField('Team Members',
                                       linked_class='EmployeeRecord')

    if __name__ == '__main__':
        from pyrtable.context import set_default_context, SimpleCachingContext

        # Set up the caching mechanism
        caching_context = SimpleCachingContext()
        set_default_context(caching_context)

        # Fetch and cache all records from the Employee table
        caching_context.pre_cache(EmployeeRecord)

        # From now on references to ``.team`` field
        # will not require server requests
        for project in ProjectRecord.objects.all():
            print(project.name,
                  ', '.join(employee.name for employee in project.team))

When caching will happen?
-------------------------

Besides calling ``caching_context.pre_cache(RecordClass)``, this mechanism will also cache *any* record that is fetched from the server. So, after using ``set_default_context(SimpleCachingContext())`` any linked records will be fetched only once.

.. note::

    If you read the source code you will notice that calling ``caching_context.pre_cache(EmployeeRecord)`` is the same as simply fetching all table records (as they will be cached). In other words, this call is equivalent to ``list(EmployeeRecord.objects.all())``.

Controlling which tables are cached
-----------------------------------

Caching all tables may be too much depending on your scenario. This default behaviour can be tuned using constructor arguments for the :class:`SimpleCachingContext` class:

.. class:: class SimpleCachingContext(allow_classes=None, exclude_classes=None)

``allow_classes``, if specified, is a list of record classes that will always be cached. Any classes not listed will not be cached.

``exclude_classes``, on the other hand, is a list of record classes that will never be cached. Any classes not listed will be cached.

.. index::
   single: pre_cache()
   single: Caching; pre_cache()

The CachingContext.pre_cache() method
-------------------------------------

This method can actually receive several arguments. Each argument specifies what is to be cached:

 - If the argument is a subclass of :class:`BaseRecord`, then all records will be fetched (by calling ``.objects.all()``) and cached.

 - If the argument is a query (e.g., ``MyTableRecord.objects.filter(…)``), then the records will be fetched and cached.

 - If the argument is a single record object (with a non-null ``.id``), then this record will be stored in the cache without being fetched from the server.
