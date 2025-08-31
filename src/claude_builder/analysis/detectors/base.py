"""Base class for project analysis detectors."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class BaseDetector(ABC):
    """Abstract base class for project analysis detectors."""

    # Confidence thresholds for categorization
    HIGH_CONFIDENCE_THRESHOLD = 12
    MEDIUM_CONFIDENCE_THRESHOLD = 8
    LOW_CONFIDENCE_THRESHOLD = 1

    def __init__(self, project_path: Optional[Path] = None):
        """Initialize the detector.

        Args:
            project_path: Path to the project directory
        """
        self.project_path = project_path

    @abstractmethod
    def detect(self, project_path: Optional[Path] = None) -> Dict[str, List[str]]:
        """Detect relevant tools/frameworks and return categorized results.

        Args:
            project_path: Optional project path, uses instance path if not provided

        Returns:
            Dictionary with categories as keys and lists of detected tools as values
        """
        raise NotImplementedError

    @abstractmethod
    def detect_with_confidence(
        self, project_path: Optional[Path] = None
    ) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
        """Detect tools with confidence levels.

        Args:
            project_path: Optional project path, uses instance path if not provided

        Returns:
            Tuple of (categorized_results, confidence_bucket_map)
            - categorized_results: Same as detect()
            - confidence_bucket_map: Maps tool -> confidence bucket (high/medium/low)
        """
        raise NotImplementedError
