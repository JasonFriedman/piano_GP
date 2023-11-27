import dataclasses as dc
from dataclasses import dataclass, astuple

from task_generation.note_range_per_hand import NoteRangePerHand


@dataclass
class TaskParameters:
    """
    @param bpm: Tempo (beats per minute).
    @param maxNotesPerBar: Maximum number of notes that a bar can contain.
    @param numberOfBars: Total number of bars.
    @param noteValuesList: Possible durations of the notes (e.g. 1, 1/2 etc.).
    @param pitchesList: Possible MIDI pitch numbers (0-127).
    @param alternating: if true play left/right alternating instead of simultaneously
    @param twoHandsTup: Tuple of booleans, True if left/right hand is active.
    """
    timeSignature: tuple = (4, 4)
    noteValues: list = dc.field(default_factory=lambda: [1 / 2, 1 / 4])
    maxNotesPerBar: int = 3
    noOfBars: int = 7
    note_range_right: NoteRangePerHand = NoteRangePerHand.TWO_NOTES
    # FIXME: debug
    note_range_left: NoteRangePerHand = NoteRangePerHand.ONE_NOTE
    left: bool = False
    right: bool = True
    alternating: bool = True
    bpm: float = None

    def astuple(self):
        return astuple(self)
