"""Base classes for SecureOps platform."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class BaseComponent(ABC):
    """Base class for all components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """Process input data."""
        pass


class BaseStage(BaseComponent):
    """Base class for pipeline stages."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.stage_name = self.__class__.__name__
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data."""
        return input_data is not None
    
    def validate_output(self, output_data: Any) -> bool:
        """Validate output data."""
        return output_data is not None
    
    def execute(self, input_data: Any) -> Any:
        """Execute stage with validation."""
        if not self.validate_input(input_data):
            raise ValueError(f"Invalid input for {self.stage_name}")
        
        output = self.process(input_data)
        
        if not self.validate_output(output):
            raise ValueError(f"Invalid output from {self.stage_name}")
        
        return output

