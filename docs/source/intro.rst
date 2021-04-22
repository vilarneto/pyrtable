Introduction
============

Installation
------------

.. code-block:: console

  $ pip install pyrtable

If you want to add support for timezone-aware timestamps (highly recommended):

.. code-block:: console

  $ pip install 'pyrtable[pytz]'

Quick Start
-----------

.. note::

    Notice that this tutorial will not work out-of-the-box, as you would need a corresponding Airtable table having columns with same names and value types as described below. However, you can adapt the examples below with your own existing bases or create one to experiment with Pyrtable.

To use Pyrtable you will first need to subclass the :class:`BaseRecord` class. Objects of your subclass represent records on the corresponding Airtable table, while the subclass itself is used to interact with the table itself (mostly to fetch records). See the examples below::

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
            base_id = 'appABCDE12345'  # @TODO change this value
            table_id = 'Employees'     # @TODO change this value

        @classmethod
        def get_api_key(cls, base_id):
            return 'keyABCDE12345'     # @TODO change this value

        name = StringField('Name')
        birth_date = DateField('Birth date')
        office = SingleRecordLinkField('Office', linked_class='OfficeRecord')
        projects = MultipleRecordLinkField(
                'Allocated in projects', linked_class='ProjectRecord')
        role = SingleSelectionField('Role', choices=Role)

Further information about the structure of :class:`BaseRecord` subclasses (and how to fill these “``@TODO``” values) can be seen in :ref:`how to define record classes <Record classes>`. The reference for the field classes are available :ref:`here <Field classes>`.

At this point, retrieving records from Airtable is quite easy::

    for employee in EmployeeRecord.objects.all():
        print('Employee %s is working on %d projects' %
              (employee.name, len(employee.projects)))
        if employee.role == Role.DEVELOPER:
            print('S/he may understand the difference between loops and conditionals!')

Creating, updating and deleting records are also easy::

    # Creating a record
    new_employee = EmployeeRecord(
            name='John Doe',
            birth_date=datetime.date(1980, 5, 10),
            role=Role.DEVELOPER)
    new_employee.save()

    # Updating a record
    new_employee.role = Role.MANAGER
    new_employee.save()

    # Deleting a record
    new_employee.delete()
