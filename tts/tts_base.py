"""
Abstract base class for TTS engines.

All TTS implementations must inherit from ``TTSBase`` and implement
the ``synthesize`` method.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class TTSBase(ABC):
    """Interface every TTS engine must satisfy."""

    @abstractmethod
    async def synthesize(self, text: str, output_path: Path) -> float:
        """Synthesize *text* into an audio file at *output_path*.

        Parameters
        ----------
        text : str
            The text to speak.
        output_path : Path
            Destination file (e.g. ``temp/scene_01.mp3``).

        Returns
        -------
        float
            Duration of the generated audio in seconds.
        """
        ...
