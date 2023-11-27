# run midi player and keyboard input as separate threads
# kill by Ctrl-C

import traceback
import time
from collections import defaultdict
from threading import Thread
import config
import dexmoOutput
import fileIO
from error_calc import functions
from error_calc.explanation import Error
from midiInput import MidiInputThread, empty_noteinfo
from midiOutput import MidiOutputThread
import noteHandler as nh

MAX_NOTE = 128
global portname


def resetArrays():
    """
    Resets global lists/arrays (target and temporary notes).

    @return: None
    """
    global targetTemp, targetTimes

    print("\nRESET!!!\n")

    # arrays for target and actual note times
    targetTimes = []

    # initialize list of tuples for note on/off times
    # index = note: [t_on, t_off, velocity]
    ###TODO: documentation (temporary etc.)
    targetTemp = defaultdict(empty_noteinfo)


def init_midi_keyboard_thread():
    """
    Initializes MIDI keyboard input thread.

    @return: None
    """
    global inputThread

    # create inputThread instance (port is set to None in constructor)
    inputThread = MidiInputThread()


def initOutputThread(root):
    global outputThread

    outputThread = MidiOutputThread(MAX_NOTE, root)


def set_inport(portName):
    """
    Sets MIDI input port (selected in GUI).

    @param portName: Name of the MIDI port.
    @return: None
    """
    global inputThread, portname
    portname = portName

    # check if inputThread was defined
    if 'inputThread' in globals():
        inputThread.setPort(portName)
        return (True)
    else:
        print("ERROR: inputThread was not defined yet")


# set MIDI input port from GUI (installing callback for input messages)
def set_outport(portName):
    global outputThread, portname
    portname = portName

    # check if inputThread was defined
    if 'outputThread' in globals():
        outputThread.setPort(portName)
        return True
    else:
        print("ERROR: outputThread was not defined yet")


def start_midi_playback(midiFileLocation, guidance, task_data, use_visual_attention=True):
    """
    Starts the MIDI playback thread and activates the MIDI input handler.
    After the player thread terminates, the input handler is deactivated again.
    The user's played notes and the error are received and displayed afterwards.

    @param midiFileLocation: Path to the MIDI file.
    @param guidance: Current Dexmo guidance mode.
    @return: Target notes, actual notes and the error.
    """
    global targetTemp, targetTimes, inputThread, outputThread

    ###TODO: change?
    resetArrays()
    inputThread.resetArrays()

    # MIDI PLAYER THREAD
    # initialize MIDI file player thread
    playerThread = Thread(target=dexmoOutput.practice_task,  # target=outputThread.playMidi (PL)
                          args=(midiFileLocation, targetTemp, targetTimes, guidance))
    playerThread.start()

    # KEYBOARD MIDI INPUT THREAD (has been started before)
    # activate input handling
    inputThread.inputOn()

    # ... MIDI playing ...

    # wait for MIDI player thread to terminate
    playerThread.join()

    # deactivate input handling
    inputThread.inputOff()

    # get array with actual notes
    actualTimes = inputThread.noteInfoList

    if len(actualTimes) == 0:  # i.e. they did not play
        print("No notes were played!!!")

    output_note_list, errorVec, errorVecLeft, errorVecRight = \
        functions.computeErrorEvo(task_data, actualTimes,
                                  inject_explanation=True,
                                  plot=True)
    print("task data", task_data.__dict__)
    print("\n\n--- ERRORS ---")
    print("\nNOTE_ERRORS:")

    note_errorString = []
    for n in output_note_list:
        print(n.err_string())
        note_errorString.append(n.err_string(use_colors=False))
    print("\nSUMMED ERROR: ", errorVec)
    print("ERROR LEFT: ", errorVecLeft)
    print("ERROR RIGHT:", errorVecRight)

    # sum(errorVec[:7]): since errorVec[7] is the number of notes it is excluded from the sum
    return targetTimes, actualTimes, sum(
        errorVec[:7]), errorVecLeft, errorVecRight, task_data, note_errorString


# Only record the user without playing the expected midi file.
# If duration is set to 0, wait for the stop button to be pressed
def startRecordThread(midiFileLocation, guidance, duration, root):
    global targetTemp, inputThread, outputThread

    ###TODO: change?
    resetArrays()
    inputThread.resetArrays()

    print("starting input on.")
    inputThread.inputOn()

    if duration > 0:
        root.update()
        root.after(duration * 1000, recordingFinished)


def recordingFinished():
    global targetTimes, actualTimes

    # deactivate input handling
    print("starting input off.")
    inputThread.inputOff()

    # get array with actual notes
    actualTimes = inputThread.noteInfoList

    print("\n\n--- NOTES ---")
    print("\nTarget notes:", targetTimes)
    print("\nActual notes:", actualTimes)

    global errorDiff

    timeSums, errorDiff = functions.computeErrorOld(targetTimes, actualTimes)
    print("\n\n--- ERRORS ---")
    print("\nTARGET TIME:", timeSums[0])
    print("\nACTUAl TIME:", timeSums[1])
    print("\nDIFFERENCE: ", errorDiff)

    options = [1, True, "bla"]
    fileIO.create_xml(config.outputDir,
                      config.currentMidi + config.str_date + config.participant_id + "_" + config.freetext,
                      options,
                      targetTimes)

    # create entry containing actual notes in XML
    fileIO.create_trial_entry(config.outputDir,
                              config.currentMidi + config.str_date + config.participant_id + "_" + config.freetext,
                              config.timestr, config.guidanceMode,
                              actualTimes, errorDiff)

    print("Created XML")
