from enum import Enum

"""
To be implemented
"""

class Clearence(Enum):
    LOW = 1,
    MODERATE = 2,
    HIGH = 3,
    # To add (?): Share, Read
    
    def description(self) -> str:
        descriptions = {
            self.LOW: "",
            self.MODERATE: "",
            self.HIGH: "",
        }
        return descriptions.get(self, "Unknown Description")