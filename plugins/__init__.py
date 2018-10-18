from abc import ABC, abstractmethod


class Handler(ABC):

    def __init__(self, full_path):
        self.logger = logging.getLogger(__name__)
        self.full_path = full_path

    def initialize(self):
        pass

    @abstractmethod
    def add_mappings(self, mappings):
        pass

    @abstractmethod
    def add_meta(self):
        pass
