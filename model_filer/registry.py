import csv
import os

# CSV parameters
DELIMITER = '\t'
QUOTECHAR = '|'


class Registry():
    """
    This class is in charge of writing/reading from the registry file.

    No overwriting/changing is allowed. If something needs to be altered, the
    client code should delete an entry and make a new one by calling
    appropriate methods here.

    Parameters
    ----------
    registry_file : string
        Path to the registry file.
    """
    def __init__(self, registry_file):
        if not os.path.exists(registry_file):
            open(registry_file, 'w')
        self.registry_file = registry_file

    def get_all_entries(self):
        with open(self.registry_file, 'r') as f:
            reader = csv.reader(f, delimiter=DELIMITER, quotechar=QUOTECHAR)
            return [RegistryEntry(*row) for row in reader]

    def find_by_name(self, name):
        entries = self.get_all_entries()
        for entry in entries:
            if entry.name == name:
                return entry

    def add_entry(self, name, status, address, timestamp):
        if self.find_by_name(name):
            raise ValueError("Cannot add '{}' to registry; it is already there.")
        entry = RegistryEntry(name=name, status=status,
                              address=address, timestamp=timestamp)
        with open(self.registry_file, 'a') as f:
            writer = csv.writer(f, delimiter=DELIMITER, quotechar=QUOTECHAR)
            writer.writerow(entry.to_list())

    def remove_entry(self, name):
        removed_entry = self.find_by_name(name)
        if not removed_entry:
            raise ValueError("Cannot remove '{}' from registry; it is not there.")
        entries = self.get_all_entries()
        with open(self.registry_file, 'w') as f:
            writer = csv.writer(f, delimiter=DELIMITER, quotechar=QUOTECHAR)
            for entry in entries:
                if entry.name != name:
                    writer.writerow(entry.to_list())
        return removed_entry


class RegistryEntry():
    def __init__(self, name, status, address, timestamp):
        self.name = name
        self.status = status
        self.address = address
        self.timestamp = timestamp
        self._validate()

    def _validate(self):
        assert self.status in ('local', 'synced')

    def to_list(self):
        return [self.name, self.status, self.address, self.timestamp]
