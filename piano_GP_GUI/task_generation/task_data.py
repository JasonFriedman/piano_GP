import dataclasses as dc
from dataclasses import dataclass, asdict, astuple

from task_generation.midi_note_event_container import MidiNoteEventContainer
from task_generation.practice_modes import PracticeMode
from task_generation.task_parameters import TaskParameters


@dataclass(frozen=False)  # Maor: it was changed to False so the bpm could be changed.
class TaskData:
    parameters: TaskParameters
    time_signature: tuple
    number_of_bars: int
    notes_right: list
    notes_left: list
    bpm: float
    midi: MidiNoteEventContainer = dc.field(default_factory=MidiNoteEventContainer)
    practice_mode: PracticeMode = "None"

    def __post_init__(self):
        assert type(self.midi) != dict

    def asdict(self):
        _d = asdict(self)
        _d["midi"] = self.midi  # the midi container gets turned into a dict!?
        _d["parameters"] = self.parameters
        return _d

    def astuple(self):
        return astuple(self)

    def beats_per_measure(self):
        return self.time_signature[0]

    def note2hand(self, note):
        if note in self.midi.right:
            return "right"
        if note in self.midi.left:
            return "left"
        raise ValueError("note in neither lists?")

    def all_notes(self):
        assert hasattr(self.midi, "together"), "MidiContainer didn't have any events yet?"
        return self.midi.together

    def __repr__(self):
        h = str(id(self))[-5:]
        return f"<TaskData obj {h}>"

    def __hash__(self):
        d = self.asdict()
        d["notes_right"] = tuple(d["notes_right"])
        d["notes_left"] = tuple(d["notes_left"])

        # the midi data is kind of not related to the task itself, thus
        # shouldn't result in a different hash if different.
        del d["midi"]
        del d["parameters"]
        return hash(tuple(d.items()))
