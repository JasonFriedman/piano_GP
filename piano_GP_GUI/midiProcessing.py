from midiutil.MidiFile import MIDIFile
from music21 import converter

import copy
import os
import mido
import settings

import pianoplayer_interface
from task_generation.note_range_per_hand import NoteRangePerHand  # ,get_pitchlist

# some code taken from https://github.com/Michael-F-Ellis/tbon

# constants for MIDI moved to settings.py (to allow customization by machine)


# time signature (ex. 4/4 = (4, 4))
# TODO: USE AS INPUT?
timeSig = (4, 4)

def write_midi(out_file, mf):
    """
    Writes the MIDIUtil object to a MIDI file.
    The object is copied before to prevent modification due to its mutability.

    @param out_file: Output MIDI file path.
    @param mf: MIDIUtil object.
    @return: None
    """
    with open(out_file, 'wb') as outf:
        copy.deepcopy(mf).writeFile(outf)


def set_time_signature(numerator, denominator, m_track, mf):
    """
    Sets the time signature of the MIDIUtil object.

    @param numerator: Numerator of the time signature.
    @param denominator: Demonimator of the time signature.
    @param m_track: Track of the MIDIUtil object.
    @param mf: MIDIUtil object.
    @return: None
    """
    # map denominator to power of 2 for MIDI
    midiDenom = {2: 1, 4: 2, 8: 3, 16: 4}[denominator]
    # make the midi metronome match beat duration
    # (requires recognizing compound meters)
    if denominator == 16 and (numerator % 3 == 0):
        metro_clocks = 18
    elif denominator == 16:
        metro_clocks = 6
    elif denominator == 8 and (numerator % 3 == 0):
        metro_clocks = 36
    elif denominator == 8:
        metro_clocks = 12
    elif denominator == 4:
        metro_clocks = 24
    elif denominator == 2:
        metro_clocks = 48
    else:
        metro_clocks = 24

    mf.addTimeSignature(track=m_track,
                        time=settings.TIME_AT_START,
                        numerator=numerator,
                        denominator=midiDenom,
                        clocks_per_tick=metro_clocks)


def set_tracks(mf, bpm):
    """
    Sets the track names and adds the tempo.

    @param mf: MIDIUtil object.
    @param bpm: Tempo (beats per minute).
    @return: None
    """
    mf.addTrackName(settings.L_TRACK, settings.TIME_AT_START, "Left Hand")
    mf.addTrackName(settings.LD_TRACK, settings.TIME_AT_START, "Left Hand Dexmo")
    mf.addTrackName(settings.R_TRACK, settings.TIME_AT_START, "Right Hand")
    mf.addTrackName(settings.RD_TRACK, settings.TIME_AT_START, "Right Hand Dexmo")
    mf.addTrackName(settings.M_TRACK, settings.TIME_AT_START, "Metronome")

    mf.addTempo(settings.R_TRACK, settings.TIME_AT_START, bpm)  # in file format 1, track doesn't matter


def generate_metronome_and_fingers_for_midi(left, right, outFiles, midi_file, custom_bpm=0):
    """
    Adds a metronome and guidance tracks/staffs to a given MIDI file.
    Both are created/computed individually for each file.

    @param left: True if the left hand is active.
    @param right: True if the right hand is active.
    @param outFiles: List of output MIDI files (needs metronome and guidance).
    @param midi_file: Input MIDI file.
    @param custom_bpm: Custom tempo (beats per minute) if desired.
    @return: saved task data and task settings
    """
    sf, measures, bpm = generate_fingers_and_write_xml(midi_file, outFiles[3], right, left)
    print("bpm extracted from midi: ", bpm)
    # sf.show('text')
    if custom_bpm > 0:
        bpm = custom_bpm

    mf = MIDIFile(numTracks=settings.TRACKS)

    set_tracks(mf, bpm)

    add_metronome(measures + settings.INTRO_BARS, 4, outFiles[1], False, mf)
    count, left_count = extract_number_of_notes(sf)
    c_to_g = False
    if ((len(sf.parts) <= 1) and count < 10) or (
            (len(sf.parts) >= 2) and (count < 10 or left_count < 10)):
        c_to_g = True
    add_fingernumbers(outFiles[2], sf, True, right, left, mf, c_to_g)  # c_to_g false?


def generateMidi(task, outFiles):
    """
    Generates a MIDI file with custom notes considering various options.

    @param noteValues: Possible durations of the notes (e.g. 1, 1/2 etc.).
    @param notesPerBar: Amounts of notes that a bar can contain.
    @param noOfBars: Total number of bars (plus initial empty bar for metronome).
    @param pitches: A NoteRangePerHand object, declaring the allowed pitches for each hand.
    @param bpm: Tempo (beats per minute).
    @param left: True for generating notes for the left hand.
    @param right: True for generating notes for the right hand.
    @param outFiles: Output MIDI files.
    @return: None
    """
    ## from init here: tracknumber, tempo etc

    right = len(task.notes_right) > 0
    left  = len(task.notes_left)  > 0

    mf = MIDIFile(numTracks=settings.TRACKS)

    set_tracks(mf, task.bpm)
    
    if right:
        mf.addProgramChange(settings.R_TRACK, settings.CHANNEL_PIANO, settings.TIME_AT_START, settings.INSTRUM_PIANO)
    if left:
        mf.addProgramChange(settings.L_TRACK, settings.CHANNEL_PIANO, settings.TIME_AT_START, settings.INSTRUM_PIANO)


    numerator, denominator = task.time_signature
    set_time_signature(numerator, denominator, settings.R_TRACK, mf)
    
    count_notes_left = 0
    count_notes_right = 0
    lastPitch = [None, None]

    for handTrack, notes in [(settings.L_TRACK, task.notes_left),
                             (settings.R_TRACK, task.notes_right)]:
        for  (start, pitch, duration) in notes:
            # choose right/left hand, split at C4 (MIDI: pitch 60)
            if left and ((not right) or (pitch < 60)):
                handTrack = settings.L_TRACK
                count_notes_left += 1
                lastPitch[0] = (handTrack, pitch)
            else:
                handTrack = settings.R_TRACK
                count_notes_right += 1
                lastPitch[1] = (handTrack, pitch)
    
            # print("original note pitches: " + str(pitch))
            mf.addNote(track=handTrack,
                       channel=settings.CHANNEL_PIANO,
                       pitch=pitch,
                       time=start,
                       duration=duration,
                       volume=settings.VOLUME)
            # notes are added to mf

    mf_without_trailing_notes = copy.deepcopy(mf)

    # add 3 extra notes per hand for proper fingering numbers
    for t in range(3):
        tempTime = ((task.number_of_bars - 1) * numerator) + t + 1
        # count_notes += 1
        for hSide in range(2):
            if lastPitch[hSide]:
                mf.addNote(track=lastPitch[hSide][0],
                           channel=settings.CHANNEL_PIANO,
                           pitch=lastPitch[hSide][1],
                           time=tempTime,
                           duration=1,
                           volume=settings.VOLUME)

    # write 1st MIDI file (piano only)
    write_midi(outFiles[0], mf)

    ### METRONOME ###
    add_metronome(task.number_of_bars - 1, numerator, outFiles[1], True, mf_without_trailing_notes)

    ### FINGERNUMBERS ###
    print("generated notes right: " + str(count_notes_right) + " generated notes left: " + str(count_notes_left))
    if (((left and not right) and count_notes_left > 7) or
            ((right and not left) and count_notes_right > 7) or
            (left and right and count_notes_left > 7 and count_notes_right > 7)):
        ## i didn't write this code but I assume it wants to make sure that 
        ## if a hand is playing it has at least 8 notes.
        
        sf, measures, bpm = generate_fingers_and_write_xml(outFiles[0], outFiles[3], right, left)
        write_midi(outFiles[0], mf_without_trailing_notes)
        add_fingernumbers(outFiles[2], sf, False, right, left, mf_without_trailing_notes, False)
    
    else:
        def c_to_g_map(note_range):
            ## the add_fingernumbers function wants to know if the pitches 
            ## allow for a c_to_g mapping, for dexmo purposes.

            # FIXME: debug this
            if note_range in [
                                NoteRangePerHand.ONE_NOTE,
                              NoteRangePerHand.TWO_NOTES,
                              NoteRangePerHand.THREE_NOTES,
                             NoteRangePerHand.FOUR_NOTES,
                              NoteRangePerHand.C_TO_G]:
                return True
            elif note_range in [
                                NoteRangePerHand.ONE_OCTAVE,
                                NoteRangePerHand.C_DUR,
                                NoteRangePerHand.BLUES,
                                NoteRangePerHand.ONE_OCTAVE_BLACK]:
                return False

            else:
                raise ValueError(f"Please specify whether {repr(note_range)} allows for c_to_g dexmo mapping.")
        

        c_to_g_l = c_to_g_map(task.parameters.note_range_left)
        c_to_g_r = c_to_g_map(task.parameters.note_range_right)
        c_to_g = (c_to_g_l and c_to_g_r)
        sf = converter.parse(outFiles[0])
        add_fingernumbers(outFiles[2], sf, False, right, left, mf, c_to_g=c_to_g)
        only_write_xml(outFiles[0], outFiles[3], right, left)

    ### parse the exact times back from the midi file
    ## extremly unintuitive, but the most straight forward way i fear.
    temp_mido_file = mido.MidiFile(outFiles[0])
    mid_left = _midi_messages_to_note_events(temp_mido_file.tracks[2], temp_mido_file)
    mid_right = _midi_messages_to_note_events(temp_mido_file.tracks[1], temp_mido_file)

    task.midi.register_midi_events(mid_left, mid_right)

 

               
def _midi_messages_to_note_events(messages, mido_file):
    from midiInput import empty_noteinfo
    from collections import defaultdict
    from noteHandler import handleNote
    from mido import tick2second

    def get_tempo(mido_file):
        for msg in mido_file:
            if hasattr(msg, "tempo"):
                return msg.tempo
        raise Exception("No tempo defined??")
    
    notes_temp = defaultdict(empty_noteinfo)
    out = list()
    time = 0.0
    tempo = get_tempo(mido_file)
    for msg in messages:
        time += tick2second(msg.time, mido_file.ticks_per_beat, tempo)
        
        if msg.is_meta:
            continue
        
        if (msg.type == 'note_on') or (msg.type == 'note_off'):
            handleNote(msg.type, msg.note, msg.velocity, notes_temp, out, timeFunc=lambda: time)
        
    return out

def add_metronome(bars, numerator, outFile, writeFile, mf):
    """
    Adds metronome notes to the respective staff in a MIDIUtil object.

    @param bars: Total number of bars.
    @param numerator: Numerator of the time signature.
    @param outFile: Output MIDI files.
    @param writeFile: True for writing the MIDIUtil object to a MIDI file.
    @param mf: MIDIUtil object.
    @return: None
    """

    mf.addProgramChange(settings.M_TRACK, settings.CHANNEL_METRO, settings.TIME_AT_START, settings.INSTRUM_DRUMS)

    for t in range(bars * numerator):

        # decide if downbeat or 'other' note
        if (t % numerator) == 0:
            # first beat in bar
            pitch = settings.PITCH_METRO_HI
        else:
            pitch = settings.PITCH_METRO_LO

        mf.addNote(track=settings.M_TRACK,
                   channel=settings.CHANNEL_METRO,
                   pitch=pitch,
                   time=t,
                   duration=1,
                   volume=settings.VOLUME)
        print("met channel: ",settings.CHANNEL_METRO)

    if writeFile:
        # write 2nd MIDI file (with metronome)
        write_midi(outFile, mf)


def generate_fingers_and_write_xml(midiFile, mxmlFile, right, left):
    """
    Computes the optimal fingering numbers using PianoPlayer and stores them
    to a MusicXML file.

    @param midiFile: Input MIDI file.
    @param mxmlFile: Output MusicXML file.
    @param right: True for generating notes for the right hand.
    @param left: True for generating notes for the left hand.
    @return: From PianoPlayer: score file, measure number, bpm
    """
    pianoplayer = pianoplayer_interface.PianoplayerInterface(midiFile)
    lbeam = 1
    if left and not right and len(pianoplayer.get_score().parts) <= 1:
        lbeam = 0
    if len(pianoplayer.get_score().parts) <= 1 and right and left:
        raise Exception("both hands selected but only one beam in score!")
    pianoplayer.generate_fingernumbers(left and not right, right and not left, 0, lbeam,
                                       pianoplayer.get_measure_number())
    pianoplayer.write_output(mxmlFile)
    return pianoplayer.get_score(), pianoplayer.get_measure_number(), pianoplayer.get_bpm()

def only_write_xml(midiFile, mxmlFile, right, left):
    """
    Creates an xml file without finger numbers for the case that there are less than 7 notes.

    @param midiFile: Input MIDI file.
    @param mxmlFile: Output MusicXML file.
    @param right: True for generating notes for the right hand.
    @param left: True for generating notes for the left hand.
    @return: From PianoPlayer: score file, measure number, bpm
    """
    pianoplayer = pianoplayer_interface.PianoplayerInterface(midiFile)
    lbeam = 1
    if left and not right and len(pianoplayer.get_score().parts) <= 1:
        lbeam = 0
    if len(pianoplayer.get_score().parts) <= 1 and right and left:
        raise Exception("both hands selected but only one beam in score!")
    pianoplayer.write_output(mxmlFile)
    return pianoplayer.get_score(), pianoplayer.get_measure_number(), pianoplayer.get_bpm()

def extract_number_of_notes(sf):
    """
    Counts the number of notes in a PianoPlayer score file.

    @param sf: PianoPlayer score file.
    @return: Number of notes, number of left hand notes
    """
    count = len(sf.parts[0].notes)
    count_left = 0
    if len(sf.parts) >= 2:
        count_left = len(sf.parts[1].notes)
    return count, count_left


def add_fingernumbers(outFile, sf, with_note, right, left, mf, c_to_g):
    """
    Adds fingering numbers to the respective tracks in a MIDIUtil object
    and writes that to a MIDI file.

    @param outFile: Output MIDI file.
    @param sf: PianoPlayer score file.
    @param with_note: True for writing the notes to the MIDI file.
    @param right: True if the right hand is active.
    @param right: True if the left hand is active.
    @param mf: MIDIUtil object.
    @param c_to_g: True for having C-G guidance.
    @return: None
    """
    if right:
        mf.addProgramChange(settings.RD_TRACK, settings.CHANNEL_RH, settings.TIME_AT_START, settings.INSTRUM_DEXMO)
    if left:
        mf.addProgramChange(settings.LD_TRACK, settings.CHANNEL_LH, settings.TIME_AT_START, settings.INSTRUM_DEXMO)

    for note in sf.parts[0].notesAndRests:
        if right:
            if with_note:
                add_note_to_midi(note, settings.R_TRACK, settings.CHANNEL_PIANO, mf)
            add_dexmo_note_to_midi(note, settings.RD_TRACK, settings.CHANNEL_RH, mf, c_to_g)
        elif len(sf.parts) < 2:
            if with_note:
                add_note_to_midi(note, settings.L_TRACK, settings.CHANNEL_PIANO, mf)
            add_dexmo_note_to_midi(note, settings.LD_TRACK, settings.CHANNEL_LH, mf, c_to_g)
    if left and len(sf.parts) >= 2:
        for note in sf.parts[1].notesAndRests:
            if with_note:
                add_note_to_midi(note, settings.L_TRACK, settings.CHANNEL_PIANO, mf)
            add_dexmo_note_to_midi(note, settings.LD_TRACK, settings.CHANNEL_LH, mf, c_to_g)

    # write 3rd MIDI file (with dexmo notes)
    write_midi(outFile, mf)


def add_dexmo_note_to_midi(note, track, channel, mf, c_to_g):
    """
    Add a given Dexmo note to a MIDIUtil object.

    @param note: Dexmo note.
    @param track: Track in the MIDIUtil object.
    @param channel: MIDI channel.
    @param mf: MIDIUtil object.
    @param c_to_g: True for having C-G guidance.
    @return: None
    """
    if note.isNote:
        if c_to_g:
            pitch = map_note_to_c_till_g(note)
        else:
            pitch = convert_note_to_dexmo_note(note)
        # print("add dexmo note: " + str(note) + " original pitch: " + str(note.pitch.ps) + " dexmo pitch: " + str(
        #     pitch))
        if pitch is not None:
            mf.addNote(track=track,
                       channel=channel,
                       pitch=pitch,
                       time=note.offset,
                       duration=note.duration.quarterLength,
                       volume=settings.VOLUME)


def add_note_to_midi(note, track, channel, mf):
    """
    Add a given Dexmo note to a MIDIUtil object.

    @param note: Dexmo note.
    @param track: Track in the MIDIUtil object.
    @param channel: MIDI channel.
    @param mf: MIDIUtil object.
    @return: None
    """
    if note.isNote:
        # print("add note: " + str(note) + " pitch: " + str(note.pitch.ps) + " time: " + str(note.offset) +
        # " duration: " + str(note.duration.quarterLength))
        mf.addNote(track=track,
                   channel=channel,
                   pitch=int(note.pitch.ps),
                   time=note.offset,
                   duration=note.duration.quarterLength,
                   volume=settings.VOLUME)


def convert_note_to_dexmo_note(note):
    """
    Converts a given MIDI note to the special Dexmo note format.

    @param note: MIDI note.
    @return: Dexmo note (special format).
    """
    if len(note.articulations) == 0:
        # print("no fingernumber")
        return None
    finger = note.articulations[0].fingerNumber
    # print("finger: " + str(finger))
    if finger == 1:
        # thumb
        return 29
    elif finger == 2:
        # idx
        return 41
    elif finger == 3:
        # mid
        return 53
    elif finger == 4:
        # ring
        return 65
    elif finger == 5:
        # pinky
        return 77
    return None


def map_note_to_c_till_g(note):
    """
    Maps a given MIDI note to match C-G guidance.

    @param note: MIDI note.
    @return: Dexmo note (special format).
    """
    if note.pitch.ps == 55 or note.pitch.ps == 60:
        # thumb
        return 29
    elif note.pitch.ps == 53 or note.pitch.ps == 54 or note.pitch.ps == 61 or note.pitch.ps == 62:
        # idx
        return 41
    elif note.pitch.ps == 51 or note.pitch.ps == 52 or note.pitch.ps == 63 or note.pitch.ps == 64:
        # mid
        return 53
    elif note.pitch.ps == 50 or note.pitch.ps == 49 or note.pitch.ps == 65 or note.pitch.ps == 66:
        # ring
        return 65
    elif note.pitch.ps == 48 or note.pitch.ps == 67 or note.pitch.ps == 68:
        # pinky
        return 77
    return None


if __name__ == "__main__":
    
    noOfBars = 24

    outFiles = ["./output/output.mid", "./output/output-m.mid",
                "./output/output-md.mid", "./output/output.xml"]

    # create folder if it does not exist yet
    outDir = "./output/"
    if not os.path.exists(outDir):
        os.makedirs(outDir)

     generate_metronome_and_fingers_for_midi(True, True, outFiles, 'test_input/TripletsAndQuarters.mid')
