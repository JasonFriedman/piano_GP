import mido

import noteHandler as nh

from custom_logging import get_logger_for_this_file
from _setup_data import midi_controller_name
from collections import namedtuple, defaultdict


NoteInfo = namedtuple("NoteInfo", ["pitch", "velocity", "note_on_time", "note_off_time"])
empty_noteinfo = lambda: NoteInfo(-1,-1,-1,-1)

logger = get_logger_for_this_file("midiInput")

def adapt_noteinfo(source, pitch=None, note_on_time=None, note_off_time=None,
                   velocity=None):
    d = source._asdict()
    for var, name in [(pitch, "pitch"), (note_on_time, "note_on_time"), 
                       (note_off_time, "note_off_time"), (velocity, "velocity")]:
        if var is not None:
            d[name] = var
    
    return NoteInfo(**d)
                     
  
class MidiInputThread():
    """
    Class for handling input from a connected MIDI device, e.g. a keyboard.
    (Not actually a subclass of threading.Thead, or a thread at all)
    """

    ###TODO: remove
    testPort = ""

    def __init__(self, input_port=None):

        """
        Initializes necessary variables and note lists/arrays.

        @param tempSize: Number of possible MIDI notes (usually 128).
        """
        #threading.Thread.__init__(self)

        self.inport = None
        # initialize note array and list
        self.noteInfoList = []
        self.noteInfoTemp = defaultdict(empty_noteinfo)
        self.midi_log_func = logger.debug

        # only handle input if true
        self.handleInput = False

        self.noteCounter = 1
        
        self.has_valid_port_set = False
        
        try:
            available_names = mido.get_input_names() 
        except:
            # import traceback
            # traceback.print_exc()
            print("WARNING: Error ocurred during 'mido.get_input_names()'")
            
            available_names = []
        
        try:
            input_port = input_port or [p for p in available_names 
                                        if midi_controller_name in p][0]
            
            self.setPort(input_port)
        
        except IndexError:
            # print("WARN: MidiInputThread opened without specifying an input port")
            pass
            


    def setPort(self, portName):
        """
        Updates the MIDI input port by closing the old one (if it exists)
        and opening the new one.

        @param portName: New MIDI port.
        @return: None
        """
        
        if portName in [None, "None"]:
            return
        # print(repr(portName))
        
        ###TODO: remove
        global testPort

        # close old MIDI input port (if it exists)
        try:
            #print("Trying to close port", testPort)
            self.inport.close()
            #print("Port closed")
        except:
            pass

        # open new MIDI input port and install callback
        # (callback is necessary to avoid blocking after port changes)
        try:
            self.inport = mido.open_input(portName, callback=self.handleMidiInput)
            self.has_valid_port_set = True
            succ_msg = f"Succesfully set midi input port to {portName}"
            print(succ_msg)
            logger.info(succ_msg)
        except:
            import traceback
            traceback.print_exc()

        ###TODO FOR TESTING
        testPort = portName
        


    # handle MIDI input message (callback function of input port)
    def handleMidiInput(self, msg):
        """
        Handle MIDI input message.
        This function was installed as a callback of the input port to avoid polling
        and starvation.

        @param msg: Input MIDI message.
        @return: None
        """
        global testPort

        #print("current input port:", testPort)
        self.midi_log_func(f"handle_input={self.handleInput} | {repr(msg)}")

        if self.handleInput:
            if not msg.is_meta:
                if (msg.type == 'note_on') or (msg.type == 'note_off'):

                    # handle note
                    noteInfo = nh.handleNote(msg.type, msg.note, msg.velocity, self.noteInfoTemp, self.noteInfoList)

                    if noteInfo == -1: 
                        # there was an error
                        # change the log level of the midi messages from debug to warning
                        self.midi_log_func = logger.warning

                    if type(noteInfo) == NoteInfo:
                        # print("ACTUAL:", self.noteCounter, "\t", noteInfo)
                        logger.debug(f"ACTUAL: {self.noteCounter}\t {noteInfo}")
                        self.noteCounter += 1


    ###TODO: needed?
    def resetArrays(self):
        """
        Resets the target note arrays.

        @return: None
        """
        self.noteInfoList = []
        self.noteInfoTemp.clear()

    def inputOn(self):
        """
        Activates the input handler.

        @return: None
        """
        if not self.has_valid_port_set:
            raise Exception("""
You tried to start the MidiInputThread without specifying the input port.
Either use the setPort function or enter the name of your default midi 
input device in the _setup_data.py file.""")

        self.handleInput = True

    def inputOff(self):
        """
        Deactivates the input handler.

        @return: None
        """
        self.handleInput = False


if __name__ == "__main__":
    # # port = 'Q25 MIDI 1'
    # port = 'VMPK Output:out 130:0'
    # testMode = True

    # # print available MIDI input ports
    # print(mido.get_input_names())
    
    # input_port = [p for p in mido.get_input_names() if "Q25" in p][0]
    
    mit = MidiInputThread()
    # mit.setPort(input_port)
    mit.inputOn()
    
    import time 
    time.sleep(5)
    mit.inputOff()
