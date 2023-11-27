import time
from custom_logging import get_logger_for_this_file
import config

# number of digits up to which a float is rounded
ROUND_DIGITS = 3

startTime = 0.0

logger = get_logger_for_this_file(__name__)

def initTime():
    """
    Sets start time globally (at task initialization).

    @return: None
    """
    global startTime

    startTime = time.time()

    ###TODO: remove
    print("Start time:", startTime)


def getTime():
    """
    Returns current time in milliseconds.

    @return: Current time [s.ms].
    """
    return round(time.time() - startTime, ROUND_DIGITS)


def handleNote(noteType, pitch, velocity, noteInfoTemp, noteInfoList, timeFunc=getTime):
    """
    Handles a given MIDI note, played by the user.
    Every note is defined by two events: note_on (pressed) and note_off (released).
    The handler stores the times for every individual note. The matching is quite
    easy as both events can only occur alternately per note (at least with regular
    MIDI devices).
    Multiple (different) notes played simultaneously can also be handled.

    @param noteType: Type of the MIDI note (note_on or note_off).
    @param pitch: Pitch of the MIDI note.
    @param velocity: Velocity of the MIDI note.
    @param noteInfoTemp: Temporary list containing each possible note's current state.
    @param noteInfoList: List of all notes played by the user.
    @param timeFunc: Function that returns the (absolute) time of the event.
    @return: -1 for error, 0 for note_on success, noteInfo for note_off success
    """

    from midiInput import adapt_noteinfo

    # the NoteInfo object before any updates
    note_info = noteInfoTemp[pitch]

    # store note_on time
    if noteType == 'note_on' and velocity > 0: # in some keyboards instead of note_off we get note_on with velocity==0.
        # check if note_on was not set already
        if note_info.note_on_time != -1:
            logger.error(f"note_on was set twice! Pitch: {pitch} | {(noteType, pitch, velocity)}")
            return -1
        # if config.show_vertical_guidance:
        #   config.vnotes.update_key_pressed(pitch, time.time() - config.playing_start_time) # update visual notes
        #   noteInfoTemp[pitch] = [getTime(), -1, velocity]
        noteInfoTemp[pitch] = adapt_noteinfo(note_info, pitch=pitch,
                                             note_on_time=timeFunc(),
                                             velocity=velocity)
        return 0

    # store note_off time and return difference
    elif noteType == 'note_off' or (noteType == 'note_on' and velocity == 0):
        # check if note_off was not set already
        if (note_info.note_on_time == -1) or (note_info.note_off_time != -1):
            logger.error(f"note_on was set twice! Pitch: {pitch} | {(noteType, pitch, velocity)}")
            return -1
        try:
            if config.showVerticalGuidance:
                config.vnotes.update_key_released(pitch, time.time() - config.playing_start_time)  # update visual notes
        except AttributeError:
            pass

        final_note_info = adapt_noteinfo(note_info,
                                         note_off_time=timeFunc())
        """ (Safety) Copy from PianoLab, should be done by adapt_note_info
        noteOffTime = getTime()
        noteInfoTemp[pitch][1] = [noteOffTime]
        noteOnTime = noteInfoTemp[pitch][0]
        velocityOn = noteInfoTemp[pitch][2] # velocity when the key was pressed
        velocityOff = velocity
        """
        # reset entry
        """ (Safety)Copy from PianoLab
        noteInfoTemp[pitch] = [-1, -1, -1]
        noteInfo = [pitch, velocityOn, noteOnTime, noteOffTime, velocityOff]
        """
        try:
            noteInfoTemp.pop(pitch)
            # same as
            # del noteInfoTemp[pitch]
        except KeyError:
            print("Error removing from noteInfoTemp")


        noteInfoList.append(final_note_info)

        return final_note_info

    else:
        print("noteType error:", noteType)
        return -1
