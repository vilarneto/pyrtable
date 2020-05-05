.. _Record classes:

Defining record classes
=======================

To use Pyrtable you will first need to subclass the :class:`BaseRecord` class, once for each table you need to access. Objects of these subclasses represent records on the corresponding Airtable table, while the subclasses themselves are used to interact with the server (mostly to fetch records).

Each one of these subclasses follow the structure below::

    class MyTableRecord(BaseRecord):
        class Meta:
            base_id = '<BASE ID>'
            table_id = '<TABLE ID>'

        # @TODO You need to provide credentials (the API Key) somehow

        # Fields definitions are created by instantiating *Field classes, such as:
        #name = StringField('Name')
        #birth_date = DateField('Birth date')
        #office = SingleRecordLinkField('Office', linked_class='OfficeRecord')

Details about the missing bits are provided below.

Values for ``base_id`` and ``table_id``
---------------------------------------

``base_id``
^^^^^^^^^^^

Open the desired base in Airtable, go to “Help > API documentation” (top-right corner) and search for a paragraph containing “The ID of this base is `base_id`”.

``table_id``
^^^^^^^^^^^^

The ``table_id`` is the name of the table itself. You can double-click the table name in the top tables to ease copying to the clipboard. Avoid using extraneous characters in the name, as these may render Pyrtable inoperative (accented characters, spaces, dots, hyphens, underlines are all OK).

Fields definitions
------------------

Refer to :ref:`this page <Field classes>` for details about using field classes to define the properties that link to Airtable fields.

Authentication methods
----------------------

To actually interact with the Airtable server, Pyrtable needs to know the *API Key*. Airtable has a `support page <https://support.airtable.com/hc/en-us/articles/219046777-How-do-I-get-my-API-key->`_ explaining how to obtain this key.

Providing the API Key to the record class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The basic way to provide the API Key to Pyrtable is to implement a class method that returns the key::

    class MyTableRecord(BaseRecord):
        @classmethod
        def get_api_key(cls):
            return '<API KEY>'

        # other class stuff here

.. warning::

    Putting the raw API Key in the source code itself is a bad security practice, as anyone with access to your code will have **full R/W access to all your Airtable bases**. API Keys are as sensitive as passwords; they should be securely stored in separate, read-protected files or using OS keychain services. See the :class:`APIKeyFromSecretsFileMixin` below.

.. _APIKeyFromSecretsFileMixin:

Reading the API Key from a file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

    This method requires `the PyYAML package <https://pypi.org/project/PyYAML/>`_ installed.

Using this approach is surprisingly easy. You only need to add the ``APIKeyFromSecretsFileMixin`` mixin when defining the class::

    class MyTableRecord(APIKeyFromSecretsFileMixin, BaseRecord):
        class Meta:
            base_id = '<BASE ID>'
            table_id = '<TABLE ID>'

        # Fields definitions go here

Pyrtable will then search for a file named ``airtable_secrets.yaml`` in one of the following directories:

 - ``./config`` subdirectory (under the current directory), or
 - ``/etc/airtable``

This file is a `YAML file <https://en.wikipedia.org/wiki/YAML>`_ with one of more key-value pairs, where each key is a base ID and the corresponding value is the API Key used to access that base. At the end, the file will contain one or more lines as follows::

    appFGHIJ67890fghij: keyABCDE12345abcde

Don't Repeat Yourself!
----------------------

In general, a Python project will interact with several tables across a single Airtable base. That means that the ``base_id`` value will be the same for all :class:`BaseRecord` subclasses.

To avoid unnecessary code repetition, you can create a base superclass for all record classes of the same base. This superclass will only contain the definition of ``base_id`` and the selected authentication method. See the example::

    class MyBaseRecord(APIKeyFromSecretsFileMixin, BaseRecord):
        class Meta:
            base_id = '<BASE ID>'


    class MyTableRecord(MyBaseRecord):
        class Meta:
            table_id = '<TABLE ID>'

        # Fields definitions go here


    class MyOtherTableRecord(MyBaseRecord):
        class Meta:
            table_id = '<OTHER TABLE ID>'

        # Fields definitions go here

Notice that ``table_id`` is specific to the actual record classes, while the ``base_id`` is common for all of them.
