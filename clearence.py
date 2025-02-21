from enum import Enum

"""
To be implemented
"""

class Clearence(Enum):
    LOW = 0,
    MODERATE = 1,
    HIGH = 2,
    # To add (?): Share, Read
    
    def description(self) -> str:
        descriptions = {
            self.LOW: "",
            self.MODERATE: "",
            self.HIGH: "",
        }
        return descriptions.get(self, "Unknown Description")