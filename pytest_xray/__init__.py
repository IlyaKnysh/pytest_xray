__version__ = "0.3.1"


class Execution:
    def __init__(self):
        self._execution_id = ''

    @property
    def execution_id(self):
        return self._execution_id

    @execution_id.setter
    def execution_id(self, value):
        self._execution_id = value


execution = Execution()
