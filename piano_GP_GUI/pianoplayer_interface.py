from music21 import converter, stream
from pianoplayer.hand import Hand
from pianoplayer.scorereader import reader, PIG2Stream


class PianoplayerInterface:
    """
    Interface for the PianoPlayer library, used to generate/compute fingering numbers.
    See https://github.com/marcomusy/pianoplayer/blob/master/bin/pianoplayer.
    """

    def __init__(self, filename):
        """
        Initializes necessary variables.

        @param filename: MIDI file to be opened.
        """
        self.sf = converter.parse(filename)
        self.bpm = self.sf.parts[0].metronomeMarkBoundaries()[0][2].getQuarterBPM()
        tmp = self.sf.parts[0].makeMeasures()
        self.measures = len(tmp.elements)

    def generate_fingernumbers(self, left_only, right_only, rbeam, lbeam, n_measures, depth=0, hand_size='M'):
        """
        Automatically generates fingering numbers using the PianoPlayer library.

        @param left_only: True if fingering should be generated for the left hand only.
        @param right_only: True if fingering should be generated for the right hand only.
        @param rbeam: Right hand track number (called 'beam' in PianoPlayer library).
        @param lbeam: Left hand track number (called 'beam' in PianoPlayer library).
        @param n_measures: Number of score measures (bars) to scan.
        @param depth: Depth of combinatorial search, [4-9] (default: autodepth) - optional.
        @param hand_size: Hand size (default: M) - optional.
        @return: None
        """

        if not left_only:
            rh = Hand("right", hand_size)
            rh.verbose = False
            if depth == 0:
                rh.autodepth = True
            else:
                rh.autodepth = False
                rh.depth = depth
            rh.lyrics = False
            rh.handstretch = False

            rh.noteseq = reader(self.sf, beam=rbeam)
            rh.generate(1, n_measures)

        if not right_only:
            lh = Hand("left", hand_size)
            lh.verbose = False
            if depth == 0:
                lh.autodepth = True
            else:
                lh.autodepth = False
                lh.depth = depth
            lh.lyrics = False
            lh.handstretch = False

            lh.noteseq = reader(self.sf, beam=lbeam)
            lh.generate(1, n_measures)

    def get_score(self):
        """
        Returns the PianoPlayer score file.

        @return: PianoPlayer score file.
        """
        return self.sf

    def get_bpm(self):
        """
        Returns the tempo.

        @return: Tempo (beats per minute).
        """
        return self.bpm

    def get_measure_number(self):
        """
        Returns PianoPlayer's measure (bar) number.

        @return: PianoPlayer's measure (bar) number.
        """
        return self.measures

    def write_output(self, outputfile):
        """
        Write the PianoPlayer score file to a MusicXML file.

        @param outputfile: MusicXML file.
        @return: None
        """
        sf_without_trailing_notes = stream.Score()
        for index, part in enumerate(self.sf):
            tmp_part = stream.Part()
            for i,measure in enumerate(part):
                if i == len(self.sf[index]) - 4:
                    break
                tmp_part.append(measure)
            sf_without_trailing_notes.append(tmp_part)
        self.sf = sf_without_trailing_notes
        self.sf.write('xml', fp=outputfile)
