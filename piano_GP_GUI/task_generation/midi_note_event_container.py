import dataclasses as dc
from dataclasses import dataclass


@dataclass
class MidiNoteEventContainer:
    left: list = dc.field(init=False)
    right: list = dc.field(init=False)
    together: list = dc.field(init=False)

    def register_midi_events(self, midi_left, midi_right):
        self.left = midi_left
        self.right = midi_right
        self.together = sorted(self.left + self.right, key=lambda n: n.note_on_time)

    def __repr__(self):
        try:
            return super().__repr__()
        except:
            return "MidiNoteEventContainer"
