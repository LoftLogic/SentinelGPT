from enum import Enum

class Clearence(Enum):
    LOW = 1,
    MODERATE = 2,
    HIGH = 3,
    
    def description(self) -> str:
        descriptions = {
            self.LOW: "",
            self.MODERATE: "",
            self.HIGH: "",
        }
        return descriptions.get(self, "Unknown Description")