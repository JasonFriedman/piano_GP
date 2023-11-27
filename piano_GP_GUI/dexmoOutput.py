import pathlib

import mido
from mido import Message
from mido import MidiFile
import time
import logging
import settings

import noteHandler as nh

global midi_interface, midi_interface_sound, CHAN, actualNote, metronome
# midi_interface = 'DEXMO_R:DEXMO_R MIDI 1 24:0'
# midi_interface_sound = 'Synth input port (Qsynth1:0)'

# abstract in python of the MIDI_HAPTIC_DEFINITION
# define channel of the device here
CHAN = 10
# choosing action on the index here
MHP_ACT_IND = 48
# various action modes
NOTE_E = 4
NOTE_F = 5
NOTE_A = 9  # note_off outwards impulse

metronome = True


def set_dexmo(port):
    """
    Sets the MIDI port for Dexmo globally.

    @param port: MIDI port for Dexmo.
    @return: None
    """
    global midi_interface
    midi_interface = port


def set_sound_outport(port):
    """
    Sets the MIDI port for sound output globally.

    @param port: MIDI port for sound output.
    @return: None
    """
    global midi_interface_sound
    midi_interface_sound = port


def toggle_metronome():
    """
    Toggles the global metronome boolean (True if metronome is active).

    @return: None
    """
    global metronome
    metronome = not metronome


def get_midi_interfaces():
    """
    Gets all currently existing MIDI ports (input and output).

    @return: Currently existing MIDI ports (input and output).
    """
    return mido.get_output_names(), mido.get_input_names()


# stop forces on all fingers on dexmo motors
def stop_all_forces(outport):
    """
    Sends messages to Dexmo for stopping all forces on all fingers' motors.

    @param outport: Dexmo MIDI output port.
    @return: None
    """

    logging.info(" SEND NOTE_OFF EVENTS TO ALL FINGERS TO STOP ALL FORCES AT END OFF TASK:")
    x = range(10, 12)
    fingerlist = [28, 40, 52, 64, 76]
    for n in x:
        for finger in fingerlist:
            msg = Message('note_off', channel=n, note=finger, velocity=100)
            outport.send(msg)
            logging.info(msg)


def impulse_outwards(msg, outport):
    """
    Sends an outwards impulse message to Dexmo after a note is finished.

    @param msg: MIDI message.
    @param outport: Dexmo MIDI output port.
    @return: None
    """
    impulsemsg = Message('note_off', channel=msg.channel, note=msg.note + 4, velocity=20)
    outport.send(impulsemsg)
    logging.info(impulsemsg)


def dexmo_action(msg, outport):
    """
    Sends a finger guidance message to Dexmo.

    @param msg: MIDI message.
    @param outport: Dexmo MIDI output port.
    @return:
    """

    logging.info(msg)
    if (msg.type == 'note_on'):
        outport.send(msg)
    elif (msg.type == 'note_off'):
        outport.send(msg)
        impulse_outwards(msg, outport)


def play_demo(midiFile, guidanceMode):
    """
    Demonstrates a taks by playing back its MIDI file (notes and metronome)
    and giving the according haptic feedback with Dexmo (depending on guidance mode).

    @param midiFile: MIDI file of the task.
    @param guidanceMode: Current guidance Mode (Dexmo).
    @return: None
    """
    if guidanceMode != "None":
        timestr = time.strftime("%Y%m%d-%H%M%S")
        log = "/tmp/DexmoPiano/" + timestr + ".log"
        logging.basicConfig(filename=log, level=logging.DEBUG, format='%(asctime)s %(message)s',
                            datefmt='%d/%m/%Y %H:%M:%S')

        logging.info("")
        logging.info("DEMO from " + timestr)

    if midi_interface != "None":
        dexmoPort = mido.open_output(midi_interface)
    with mido.open_output(midi_interface_sound) as soundPort:
        for msg in MidiFile(midiFile).play():
            # sound from piano and metronome track,channel 9 is metronome, piano is 0
            if metronome:
                if msg.channel == 0 or msg.channel == 9:
                    soundPort.send(msg)
            elif msg.channel == 0:  # only piano sound
                soundPort.send(msg)

            # haptic feedback on dexmo for right (channel 10) and left hand (channel 11)
            if msg.channel != 0 and msg.channel != 9:
                if guidanceMode != "None":
                    if msg.type == 'note_on':
                        dexmo_action(msg=msg, outport=dexmoPort)
                    elif msg.type == 'note_off':
                        dexmo_action(msg=msg, outport=dexmoPort)

    if (midi_interface != "None"):  # stop all forces on dexmo
        stop_all_forces(dexmoPort)
        dexmoPort.close()


# only haptic feedback guidance
def practice_task(midiFile, noteInfoTemp, noteInfoList, guidanceMode, showVerticalGuidance=None):
    """
    Starts the practice task by playing only the metronome (if chosen)
    and giving the according haptic feedback with Dexmo (depending on guidance mode).

    @param midiFile: MIDI file of the task.
    @param noteInfoTemp: Temporary list containing each possible note's current state.
    @param noteInfoList: List of all notes played by the user.
    @param guidanceMode: Current guidance Mode (Dexmo).
    @return: None
    """
    if guidanceMode != "None":
        timestr = time.strftime("%Y%m%d-%H%M%S")
        log = "/tmp/DexmoPiano/" + timestr + ".log"
        pathlib.Path(log).parent.mkdir()
        logging.basicConfig(filename=log, level=logging.DEBUG, format='%(asctime)s %(message)s',
                            datefmt='%d/%m/%Y %H:%M:%S')

        logging.info("")
        logging.info("TASK from " + timestr)

    if midi_interface != "None":
        dexmoPort = mido.open_output(midi_interface)
    with mido.open_output(midi_interface_sound) as soundPort:
        noteCounter = 1

        # set start time
        nh.initTime()

        for msg in MidiFile(midiFile):
            if not msg.is_meta:
                # do not play all notes at once
                time.sleep(msg.time)
                # for Nord 4: since Metronome and piano are both on channel 0, then metronome is defined by pitch < 48.
                if settings.CHANNEL_METRO == 0:
                    if (msg.type == 'note_on') or (msg.type == 'note_off'):
                        if msg.note < 48 and metronome:
                            soundPort.send(msg)  # sound only from metronome track
                # Code not for Nord: metronome is on channel 9
                else:
                    if msg.channel == 9 and metronome:
                        soundPort.send(msg)  # sound only from metronome track

                if msg.channel == 0:  # haptic feeback for notes in Piano track

                    ##____________________HANDLE note_____________________________##
                    if (msg.type == 'note_on') or (msg.type == 'note_off'):
                        # handle note
                        noteInfo = nh.handleNote(msg.type, msg.note, msg.velocity, noteInfoTemp,
                                                 noteInfoList)

                        if type(noteInfo) == list:
                            print("TARGET:", noteCounter, "\t", noteInfo)
                            noteCounter += 1
                # haptic feedback on dexmo for right (channel 10) and left hand (channel 11)
                if msg.channel != 0 and msg.channel != 9:
                    if guidanceMode != "None":
                        if msg.type == 'note_on':
                            dexmo_action(msg=msg, outport=dexmoPort)
                        elif msg.type == 'note_off':
                            dexmo_action(msg=msg, outport=dexmoPort)

    if (midi_interface != "None"):
        stop_all_forces(dexmoPort)
        dexmoPort.close()


if __name__ == '__main__':
    # start_music()
    play_demo()
    # practice_task()
