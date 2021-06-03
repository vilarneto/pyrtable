.. _Field classes:

Field classes
=============

Field classes are used to declare properties that map onto Airtable fields (columns). You instantiate field classes when :ref:`defining your record classes <Record classes>`, providing the corresponding Airtable field name as the first argument – see the example below::

   class PersonRecord(BaseRecord):
       name = StringField('Name', read_only=True)
       birth_date = DateField('Birth date')
       number_of_children = IntegerField('Children')

Airtable always allows empty values to any cell. In general, these are represented as ``None`` in Python, with exceptions noted below (for instance, :class:`StringField` will always map empty cells onto empty strings).

You don't need to map all Airtable fields; it's OK to declare only some of the fields in Python.

Neither ``id`` nor ``created_timestamp`` can be used as field names as they are reserved for two special fields described below.

.. index::
   single: id

The ``id`` field
----------------

All record classes have an automatically generated ``.id`` field. It will hold either the Airtable record identifier (a string) or, for deleted and created-but-not-saved records, the ``None`` value.

.. index::
   single: created_timestamp

The ``created_timestamp`` field
-------------------------------

All record classes have an automatically generated ``.created_timestamp`` field. It will hold the record creation timestamp as informed by Airtable, or ``None`` if it was not yet saved.

Field arguments
---------------

Some arguments are used in all field types. These are documented below.

.. index::
   single: field_name
   single: Field arguments; field_name

``field_name``
^^^^^^^^^^^^^^

A string. The name of the field as defined in Airtable.

Beware of field names — not all characters are supported by Pyrtable, even if they are accepted in Airtable. Currently only letters (including diacritics), numbers, spaces, dots, hyphens, underlines are accepted.

.. index::
   single: read_only
   single: Field arguments; read_only

``read_only``
^^^^^^^^^^^^^

A boolean (optional, defaults to ``False``). If ``True``, changes to that field are forbidden in Python. You can use this to guarantee that Pyrtable will never update the corresponding Airtable field. Read-only fields are still writeable when creating records.

Field types
-----------

.. _AttachmentField:
.. index::
   single: AttachmentField
   single: Field types; AttachmentField

``AttachmentField``
^^^^^^^^^^^^^^^^^^^

.. class:: class AttachmentField(field_name, read_only=True, **options)

.. note::

    Currently only reading operations are implemented, so using ``read_only=True`` is mandatory.

Holds a collection of uploaded files. Each uploaded file is represented by an instance of the :class:`Attachment` class that contains the following properties:

 - ``id`` (:py:class:`str`): Airtable unique identifier of this attachment;

 - ``url`` (:py:class:`str`): URL that can be used to download the file;

 - ``filename`` (:py:class:`str`): Name of the uploaded file;

 - ``size`` (:py:class:`int`): Size of the file, in bytes;

 - ``type`` (:py:class:`str`): Mimetype of the file;

 - ``width`` (:py:class:`int`, optional): If the file is an image, its width in pixels;

 - ``height`` (:py:class:`int`, optional): If the file is an image, its height in pixels;

 - ``thumbnails``: If the file is an image, this is an object with three properties: ``small``, ``large`` and ``full``. Each one of these properties point to an object that in turn has three properties: ``url``, ``width`` and ``height``. One can use these properties to access thumbnails for the uploaded image.

The :class:`Attachment` class also has two methods to download the corresponding file:

 - ``download()``: downloads the file and returns the in-memory representation as a :py:class:`bytes` instance;

 - ``download_to(path)``: downloads the file and and stores it as a local file whose path is given by the ``path`` argument.

This property follows :py:class:`collections.abc.Sized` and :py:class:`collections.abc.Iterable` semantics, so the following operations are allowed::

    class PersonRecord(BaseRecord):
        profile_pictures = AttachmentField('Images', read_only=True)

    # ...

    # Counting the number of attached images
    print(len(person.profile_pictures))

    # Iterating over attached images
    for picture in person.profile_pictures:
        if picture.width is not None and picture.height is not None:
            print('There is a %dx%d image' % (image.width, image.height))

.. _BooleanField:
.. index::
   single: BooleanField
   single: Field types; BooleanField

``BooleanField``
^^^^^^^^^^^^^^^^

.. class:: class BooleanField(field_name, **options)

Holds a :py:class:`bool` value. This field never holds ``None``, as empty values are mapped to ``False``.

.. _DateField:
.. index::
   single: DateField
   single: Field types; DateField

``DateField``
^^^^^^^^^^^^^

.. class:: class DateField(field_name, **options)

Holds a :py:class:`datetime.date` value.

.. _DateTimeField:
.. index::
   single: DateTimeField
   single: Field types; DateTimeField

``DateTimeField``
^^^^^^^^^^^^^^^^^

.. class:: class DateTimeField(field_name, **options)

Holds a :py:class:`datetime.datetime` value. If `the pytz package <https://pypi.org/project/pytz/>`_ is installed, values will be timezone aware.

.. _FloatField:
.. index::
   single: FloatField
   single: Field types; FloatField

``FloatField``
^^^^^^^^^^^^^^

.. class:: class FloatField(field_name, **options)

Holds a :py:class:`float` value.

.. _IntegerField:
.. index::
   single: IntegerField
   single: Field types; IntegerField

``IntegerField``
^^^^^^^^^^^^^^^^

.. class:: class IntegerField(field_name, **options)

Holds an :py:class:`int` value.

.. _MultipleRecordLinkField:
.. index::
   single: MultipleRecordLinkField
   single: Field types; MultipleRecordLinkField

``MultipleRecordLinkField``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. class:: class MultipleRecordLinkField(field_name, linked_class, **options)

Holds zero or more record references, possibly from another Airtable table. ``linked_class`` is either the record class (i.e., a :class:`BaseRecord` subclass) or a string containing full Python module path to that class (e.g., ``'mypackage.mymodule.MyTableRecord'``).

This property follows :py:class:`collections.abc.Iterable` and :py:class:`collections.abc.MutableSet` semantics, so the following operations are allowed::

    class EmployeeRecord(BaseRecord):
        projects = MultipleRecordLinkField('Projects', linked_class=ProjectRecord)

    # ...

    # Counting the number of linked records
    print(len(employee.projects))

    # Checking if a value is/isn't selected
    if revolutionary_project in employee.projects:
        print('Congratulations, you have worked in our best project!')
    if flopped_project not in employee.projects:
        print('You are not to be blamed. This time.')

    # Iterating over selected values
    for project in employee.projects:
        print('Our employee %s is working on the project %s' %
              (employee.name, project.name))

To change the value of this property there are some ways::

    employee.projects.add(project)
    employee.projects.discard(project)
    employee.projects.set(iterable_projects)

Notice that the last method accepts an iterable, such as lists, tuples, and sets. There are also some shortcuts::

    employee.projects += project
    employee.projects -= project

Pyrtable also creates a companion property with ``'_ids'`` suffix that holds a collection record IDs. So, in the example above the record IDs can be printed as follows::

    print('Linked record IDs: %s' % ', '.join(employee.record_ids))

.. _MultipleSelectionField:
.. index::
   single: MultipleSelectionField
   single: Field types; MultipleSelectionField

``MultipleSelectionField``
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. class:: class MultipleSelectionField(field_name, choices=None, **options)

Holds zero or more values from a predefined set (Airtable calls it a “Multiple select” field) that is mapped onto a Python enum (a subclass of :py:class:`enum.Enum`). The enum class is given as a second argument named ``choices`` — check :py:class:`SingleSelectionField` for a detailed description and examples.

If ``choices`` is not given or is ``None``, the field maps values into strings.

.. warning::

    Due to limitations of the Airtable API, do not use commas in any of the options for multiple select fields. This may confuse Pyrtable in some operations and may cause data loss!

This property follows :py:class:`collections.abc.Iterable` and :py:class:`collections.abc.MutableSet` semantics, so the following operations are allowed::

    # Counting the number of values selected
    print(len(record.multiple_selection_field))

    # Checking if a value is/isn't selected
    if value in record.multiple_selection_field:
        print('The value %r is currently selected.' % value)
    if value not in record.multiple_selection_field:
        print('The value %r currently not selected.' % value)

    # Iterating over selected values
    for value in record.multiple_selection_field:
        print('Selected value: %r' % value)

To change the value of this property there are some ways::

    record.multiple_selection_field.add(value)
    record.multiple_selection_field.discard(value)
    record.multiple_selection_field.set(iterable)

Notice that the last method accepts an iterable, such as lists, tuples, and sets. There are also some shortcuts::

    record.multiple_selection_field += value
    record.multiple_selection_field -= value

.. _SingleRecordLinkField:
.. index::
   single: SingleRecordField
   single: Field types; SingleRecordField

``SingleRecordLinkField``
^^^^^^^^^^^^^^^^^^^^^^^^^

.. class:: class SingleRecordLinkField(field_name, linked_class, **options)

Holds a reference to another record, possibly from another Airtable table. ``linked_class`` is either the record class (i.e., a :class:`BaseRecord` subclass) or a string containing full Python module path to that class (e.g., ``'mypackage.mymodule.MyTableRecord'``).

Pyrtable also creates a companion property with ``'_ids'`` suffix that holds a reference to the record ID. So, for example::

   class EmployeeRecord(BaseRecord):
       office = SingleRecordLinkField('Office',
                                      linked_class='OfficeRecord')

then all objects of ``EmployeeRecord`` class will also have a ``obj.office_id`` that holds the ID of the office record. Accessing this property does not hit the Airtable field.

Accessing the property at runtime is an expensive operation for the first time, as it requires fetching the record from the Airtable server. Once the record is fetched it is cached in memory, so subsequent access are fast. There are techniques to cache foreign records in advance (@TODO document).

.. _SingleSelectionField:
.. index::
   single: SingleSelectionField
   single: Field types; SingleSelectionField

``SingleSelectionField``
^^^^^^^^^^^^^^^^^^^^^^^^

.. class:: class SingleSelectionField(field_name, choices, **options)

Holds a single value from a predefined set (Airtable calls it a “Single select” field) that is mapped onto a Python enum (a subclass of :py:class:`enum.Enum`). The enum class is given as a second argument named ``choices`` — see below::

   class Role(enum.Enum):
       DEVELOPER = 'Developer'
       MANAGER = 'Manager'
       CEO = 'C.E.O.'

   class EmployeeRecord(BaseRecord):
       role = SingleSelectionField('Role', choices=Role)

.. _StringField:
.. index::
   single: StringField
   single: Field types; StringField

``StringField``
^^^^^^^^^^^^^^^

.. class:: class StringField(field_name, **options)

Holds a :py:class:`str` value. Unlike other field types, this field never holds ``None``; nonexistent values are always translated into empty strings.
