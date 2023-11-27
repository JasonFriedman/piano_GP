import os
import time
import shutil
import ntpath
import pathlib
import subprocess

import pickle
import numpy as np
import pandas as pd

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

from collections import namedtuple

# local files
import config
import fileIO
import dexmoOutput
import midiProcessing
import thread_handler


from task_generation.scheduler import Scheduler
from task_generation.task_parameters import TaskParameters
from task_generation.gaussian_process import GaussianProcess
from task_generation.gaussian_process import PracticeMode
import data_acquisition

#IF 0 THAN EXPERT MODE, IF 1 GP MODE
GUI_STATE =0
# directory constants
DATA_DIR = './output/data/'

OUTPUT_DIR = './output/'
TEMP_DIR = './output/temp/'

EXPERT_DIR = "pics_run_not_data.h5"
OUTPUT_FILES_STRS = [TEMP_DIR + 'output.mid', TEMP_DIR + 'output-m.mid', TEMP_DIR + 'output-md.mid',
                     TEMP_DIR + 'output.xml']
OUTPUT_LY_STR = TEMP_DIR + 'output.ly'
OUTPUT_PNG_STR = TEMP_DIR + 'output.png'

LILYPOND_PYTHON_EXE_WIN = "c:/Program Files (x86)/LilyPond/usr/bin/python.exe"
XMl_2_LY_WIN_FOLDER = "c:/Program Files (x86)/LilyPond/usr/bin/musicxml2ly"
MIDI_TO_LY_WIN = "c:/Program Files (x86)/LilyPond/usr/bin/midi2ly"

guidance_modes = ["None", "At every note", "Individual"]
guidance_mode = "At every note"

first_start = True

errors = []
change_task = []

root = tk.Tk()
root.title("AI instructed Piano Learning")
root.geometry("1500x1000")

# Tk variables
show_error_details = tk.BooleanVar()
metronome = tk.BooleanVar()
use_visual_attention = tk.BooleanVar()
node_params = tk.StringVar()

# Tk view elements
dexmo_port_btn = None
show_error_details_checkbox = None
canvas = None

# constants for practice loop
ERROR_THRESHOLD = 0  # if measured error in PlayCompleteSong state is below threshold -> finish practice loop
NUM_PRACTICE_ITERATIONS = 2  # number of practice iterations after PracticeModeState is automatically left

TaskNote = namedtuple("TaskNote", "start pitch duration")


class BaseState:
    """
    Parent class for all GUI states. Defines variables and functions that find usage in multiple states.
    """

    def __init__(self, scheduler: Scheduler, statemachine):
        self.scheduler = scheduler
        self.statemachine = statemachine


    def _do_on_enter(self):
        pass

    def _do_on_exit(self):
        pass

    def on_enter(self):
        self.clear_frame()
        self._do_on_enter()

    def on_exit(self):
        self._do_on_exit()

    @staticmethod
    def clear_frame():
        """
        Destroys all widgets from the frame.
        """
        for widget in root.winfo_children():
            widget.destroy()

    @staticmethod
    def show_primary_next_state_btn(text: str, state):
        """
        Displays a button in the upper left corner of the window that can be clicked to switch the current state.
        @param text: Text that is displayed on the button
        @param state: BaseState class object. The state that is entered when clicking the button
        """
        tk.Button(
            root, text=text, command=lambda: statemachine.to_next_state(state)
        ).place(x=10, y=10, height=50, width=150)

    @staticmethod
    def show_secondary_next_state_btn(text, state):
        """
        Displays a button in the upper left corner of the window (below primary_next_state_btn) that can be clicked
        to switch the current state.
        @param text: Text that is displayed on the button
        @param state: BaseState class object. The state that is entered when clicking the button
        """
        tk.Button(
            root, text=text, command=lambda: statemachine.to_next_state(state)
        ).place(x=10, y=80, height=50, width=150)

    @staticmethod
    def show_function_btn(text: str, function):
        """
        Adds a Button to the GUI, which can be used to trigger a function.
        @param text: Text that is displayed on the button
        @param function: Function that should be called when pressing the button
        """
        tk.Button(
            root, text=text, command=function
        ).place(x=10, y=10, height=50, width=150)


    @staticmethod
    def init_training_interface():
        """
        Create several GUI buttons that are used as training interface.
        """
        global participant_id_text, free_text
        global show_vertical_guidance

        node_params.set("")
        tk.Label(root, textvariable=node_params, font=("Courier", 12)).place(x=10, y=40)

        # checkbox to toggle metronome playback
        metronome.set(dexmoOutput.metronome)
        check_metronome = tk.Checkbutton(root, text='play metronome', variable=metronome,
                                         command=dexmoOutput.toggle_metronome)
        check_metronome.place(x=10, y=200)

        # dropdown menu to change guidance mode
        l = tk.Label(root, text=" Guidance mode:")
        l.place(x=10, y=220, width=150, height=70)

        guidance = tk.StringVar(root)
        guidance.set(guidance_mode)

        guidance_option_menu = tk.OptionMenu(root, guidance, *guidance_modes, command=set_guidance)
        guidance_option_menu.place(x=10, y=270, width=150, height=30)

        # button to return to main menu
        tk.Button(
            root, text='Back to Menu', command=lambda: statemachine.to_next_state(statemachine.main_menu_state)
        ).place(x=10, y=940, height=50, width=150)



    @staticmethod
    def show_note_sheet(png_file: str):
        """
        Loads the note sheet (png) for the current task.

        @param png_file: Image file (png format)
        """
        background = Image.open(png_file)
        background = background.convert("RGBA")

        img = ImageTk.PhotoImage(background)
        panel = tk.Label(root, image=img)
        panel.image = img
        panel.place(x=170, y=0, width=835, height=1181)

    def gen_ly_for_current_task(self):
        """
        Generates a .ly file (LilyPond format) from the current task's file (needed for png generation).
        If the file is in MusicXML format, finger numbers are taken into account. This is not the case
        for MIDI files.
        """
        xml_generated = False
        files = os.listdir(TEMP_DIR)
        for item in files:
            if item.endswith('.xml'):
                xml_generated = True

        # create png from music xml with fingernumbers
        if xml_generated:
            self.delete_no_fingernumbers_warning()
            if os.name == 'nt':
                subprocess.run([LILYPOND_PYTHON_EXE_WIN, XMl_2_LY_WIN_FOLDER,
                                OUTPUT_FILES_STRS[3], '--output=' + OUTPUT_LY_STR],
                               stderr=subprocess.DEVNULL)
            else:
                subprocess.run(['musicxml2ly',
                                OUTPUT_FILES_STRS[3], '--output=' + OUTPUT_LY_STR],
                               stderr=subprocess.DEVNULL)
        # or from midi without finger numbers, if too few notes are generated
        else:
            self.add_no_fingernumbers_warning()
            if os.name == 'nt':
                subprocess.run([LILYPOND_PYTHON_EXE_WIN, MIDI_TO_LY_WIN,
                                OUTPUT_FILES_STRS[0], '--output=' + OUTPUT_LY_STR],
                               stderr=subprocess.DEVNULL)
            else:
                subprocess.run(['midi2ly',
                                OUTPUT_FILES_STRS[0], '--output=' + OUTPUT_LY_STR],
                               stderr=subprocess.DEVNULL)

    @staticmethod
    def add_no_fingernumbers_warning():
        """
        Creates a warning in case that a created or selected MIDI has too few notes to show fingernumbers.
        """
        global too_few_notes_generated_warning
        too_few_notes_generated_warning = tk.Label(root,
                                                   text=" Info: \n Too few notes generated to show\n fingernumbers on music sheet.",
                                                   fg="red")
        too_few_notes_generated_warning.place(x=1030, y=770, width=250, height=100)

    @staticmethod
    def delete_no_fingernumbers_warning():
        """
        Removes the warning created by add_no_fingernumbers_warning().
        """
        global too_few_notes_generated_warning
        too_few_notes_generated_warning = tk.Label(root, text="")
        too_few_notes_generated_warning.place(x=1030, y=770, width=250, height=100)

    def start_playback_and_calc_error(self, task_parameters: TaskParameters) -> pd.DataFrame:
        """
        Function that matches midi input to currently scheduled task and measures errors.
        @param task_parameters: the parameters of the scheduled task
        @return: calculated errors
        """
        targetNotes, actualNotes, errorVal, error_vec_left, error_vec_right, task_data, note_error_str = \
            thread_handler.start_midi_playback(OUTPUT_FILES_STRS[2], guidance_mode,
                                               self.scheduler.current_task_data(),
                                               use_visual_attention=use_visual_attention.get())
        df_error = data_acquisition.save_data(error_vec_left, error_vec_right, task_data,
                                                      task_parameters, note_error_str,
                                                      config.participant_id, config.free_text)

        self.save_midi_and_xml(targetNotes, self.scheduler.current_task_data(), task_parameters)
        timestamp = get_current_timestamp()
        # create entry containing actual notes in XML
        fileIO.create_trial_entry(OUTPUT_DIR, timestamp, timestamp, guidance_mode, actualNotes,
                                  errorVal)


        return df_error

    def save_midi_and_xml(self, target_notes, task_data, task_parameters):
        """
        Saves the MIDI and the XML file to the globally defined output folder.

        @param target_notes: List of notes to be played by the user.
        @param task_data: a class with all task data.
        @param task_parameters: a list of the parameters that generated the task.
        @return: None
        """

        time_str = get_current_timestamp()

        # MIDI
        shutil.copy(OUTPUT_FILES_STRS[0], OUTPUT_DIR + time_str + '.mid')
        shutil.copy(OUTPUT_FILES_STRS[1], OUTPUT_DIR + time_str + '-m.mid')
        shutil.copy(OUTPUT_FILES_STRS[2], OUTPUT_DIR + time_str + '-md.mid')

        # save task_data and task Parameters to pickle file
        data_to_save = [task_data, task_parameters]

        with open(OUTPUT_DIR + time_str + '-data.task', 'wb') as f:
            pickle.dump(data_to_save, f)

        fileIO.create_xml(OUTPUT_DIR, time_str, task_parameters.astuple(), target_notes)


class MenuState(BaseState):
    """
    Menu state where in- and output ports are set
    """

    def _do_on_enter(self):
        tk.Button(
            root, text='Start gp learning', command=self.start_if_ports_are_set
        ).place(x=675, y=560, height=50, width=150)

        tk.Button(
            root, text='Quit', command=lambda: statemachine.to_next_state(statemachine.end_state)
        ).place(x=675, y=500, height=50, width=150)

        self.create_port_drop_down_menus()

    @staticmethod
    def start_if_ports_are_set():
        if dexmoOutput.midi_interface_sound != "None" and thread_handler.portname != "None":
            statemachine.to_next_state(statemachine.select_name_state)

    def create_port_drop_down_menus(self):
        """
        Creates drop-down menus for choosing the ports for MIDI input/output and Dexmo
        in the start window.
        """
        global dexmo_port_btn, first_start

        # CONSTANTS
        x_pos = 660
        x_diff = 10
        y_diff = 40
        text_height = 50
        field_height = 25
        width = 200

        def create_port_btn(portText, findStr, yPos, portList, set_port):
            """
            Creates a port menu and matches the current MIDI ports for a preselection.
            Example: If Dexmo is connected, a port having "Dexmo" in its name will be preselected.
                     If nothing is found, the user needs to selection the desired port manually.

            @param portText: Text of the port menu description.
            @param findStr: Keyword for matching the port (e.g. "Dexmo").
            @param yPos: Vertical position offset for description and menu.
            @param portList: List of currently existing MIDI ports.
            @param set_port: Function for setting the port in the respective file.
            @return: MIDI port name (global).
            """
            # place button label (text)
            port_label = tk.Label(root, text=portText + " port:")
            port_label.place(x=x_pos, y=yPos, height=text_height, width=width)

            # match port
            midi_port = tk.StringVar(root)
            if first_start:
                matching = [s for s in portList if findStr in s.lower()]
                if matching:
                    midi_port.set(matching[0])
                else:
                    midi_port.set("None")

                set_port(midi_port.get())
            else:
                if portText == "Dexmo output":
                    midi_port.set(dexmoOutput.midi_interface)
                elif portText == "Sound output":
                    midi_port.set(dexmoOutput.midi_interface_sound)
                elif portText == "Piano input":
                    midi_port.set(thread_handler.portname)

            option_menu = tk.OptionMenu(root, midi_port, *portList, command=set_port)
            option_menu.place(x=x_pos - x_diff, y=yPos + y_diff, height=field_height, width=width)

            return midi_port

        # choose outport for (Lego)Dexmo etc
        outports, inports = dexmoOutput.get_midi_interfaces()
        outports = list(dict.fromkeys(outports))
        inports = list(dict.fromkeys(inports))

        outports.append("None")
        inports.append("None")

        # create port buttons with automatic port name choice (if possible)
        dexmo_port_btn = create_port_btn("Dexmo output", "dexmo", 680, outports,
                                         dexmoOutput.set_dexmo)

        create_port_btn("Sound output", "qsynth", 760, outports,
                        dexmoOutput.set_sound_outport)
        create_port_btn("Piano input", "vmpk", 840, inports, thread_handler.set_inport)


class SelectNameState(BaseState):
    """
    State where the name of the user can be entered.
    """

    def __init__(self, scheduler: Scheduler, statemachine):
        super().__init__(scheduler, statemachine)

    def _do_on_enter(self):
        tk.Label(root, text="Enter Name").grid(row=0)
        name_entry = tk.Entry(root)
        name_entry.grid(row=0, column=1)
        tk.Button(root, text="Save",
                  command=lambda: self.save_name(name_entry.get())).grid(row=0, column=3)

    def save_name(self, username):
        statemachine.username = username
        self.statemachine.to_next_state(statemachine.select_song_state)
        return


class SelectSongState(BaseState):
    """
    State with file dialog to pick a midi file.
    """

    def __init__(self, scheduler: Scheduler, statemachine):
        super().__init__(scheduler, statemachine)
        self.midi_file = None



    def _do_on_enter(self):
        self.init_training_interface()

        self.midi_file = None

        while self.midi_file is None or len(self.midi_file) == 0:
            self.midi_file = filedialog.askopenfilename(
                filetypes=[("Midi files", ".midi .mid")]
            )
        print (self.midi_file)
        self.check_dexmo_connected(main_window=True)



        self.statemachine.to_next_state(
            PlayCompleteSong(self.scheduler, self.statemachine, self.midi_file,
                             practice_parameters= {"bpm": 85, "error_before_practice": None, "practice_mode": None})

        )


    def check_dexmo_connected(self, main_window):
        """
        Checks if Dexmo is connected and changes the list of feasible guidance modes accordingly.

        @param main_window: True if the current window is the main window.
        @return: None
        """

        global guidance_modes, guidance_mode
        if dexmo_port_btn.get() == "None":
            guidance_modes = ["None"]
            guidance_mode = "None"
            if main_window:
                self.add_dexmo_warning()
        else:
            guidance_modes = ["None", "At every note", "Individual"]

    @staticmethod
    def add_dexmo_warning():
        """
        Creates a warning in case that Dexmo is not connected.
        """
        tk.Label(
            root, text=" Warning: \n No Dexmo connected, \n no guidance possible.", fg="red"
        ).place(x=10, y=300, width=150, height=70)


class PlayCompleteSong(BaseState):
    """
    Main state where the original music piece is played.
    """

    def __init__(self, scheduler: Scheduler, statemachine, midi_file,  practice_parameters=None):
        super().__init__(scheduler, statemachine)
        self.midi_file = midi_file
        self.practice_parameters = practice_parameters


    def _load_with_bpm(self, bpm):
        """
        Procedure  used to  load a piece
        with the bpm selected within the slider
        """
        bpm = int(bpm)
        self.practice_parameters["bpm"]=bpm
        task_data = self.scheduler.queue_new_target_task_from_midi(self.midi_file)

        self.scheduler.current_task_data().bpm = bpm
        print("changed task bpm ", task_data.bpm,  "debug task parameters ", task_data.parameters.bpm)


        midiProcessing.generateMidi(task_data, outFiles=OUTPUT_FILES_STRS)

        self.gen_ly_for_current_task()
        subprocess.run(['lilypond', '--png', '-o', TEMP_DIR, OUTPUT_LY_STR],
                       stderr=subprocess.DEVNULL)

        self.show_note_sheet(OUTPUT_PNG_STR)
        root.update_idletasks()

        self.show_function_btn('Play Piece', self.start_playback)

        tk.Button(
            root, text="Play Demo", command=lambda: dexmoOutput.play_demo(OUTPUT_FILES_STRS[2], guidance_mode)
        ).place(x=10, y=140, height=50, width=150)

        self.show_secondary_next_state_btn('Select new Song', statemachine.select_song_state)


    def _do_on_enter(self):
        self.init_training_interface()
        self.scheduler.clear_queue()

        midiBPM = tk.Scale(root, from_=0, to=250, length=150, orient=tk.HORIZONTAL, command=self._load_with_bpm)
        midiBPM.place(x=10, y=570)
        if (self.practice_parameters["bpm"]!=None):
            midiBPM.set(self.practice_parameters["bpm"])



               
        

    
            
    def get_next_practise_mode(self, error) -> PracticeMode:
        """
        Find the practice mode the Gaussian process recommends.
        @param error: error input
        @return: PracticeMode: the chosen practice mode
        """
        task = self.scheduler.current_task_data()
        return self.statemachine.gaussian_process.get_best_practice_mode(error=error, bpm=task.parameters.bpm)

    def start_timing(self,var):

        return var
    def start_pitch(self,var):

        return var

    def get_next_practise_mode_expert(self) -> PracticeMode:
        """
        get the practice mode as input from user.
        @param error: error input
        @return: PracticeMode: the chosen practice mode
        """
        task = self.scheduler.current_task_data()
        input_exp = None

        input_exp = input("which practice mode? t\p:\n")
        while (input_exp != 't' and input_exp != 'p'):
            input_exp = input("which practice mode? t\p:\n")
        if input_exp == 'p':
            return PracticeMode.IMP_PITCH
        if input_exp == 't':
           return PracticeMode.IMP_TIMING

        #var = tk.IntVar()
        #button_timing = tk.Button(
         #   root, text='timing', command=self.start_timing(var)
        #).place(x=540, y=500, height=50, width=150)
        #button_pitch = tk.Button(
         #   root, text='pitch', command=self.start_pitch(var)
        #).place(x=675, y=500, height=50, width=150)
        #print("waiting...")
        #button = button_pitch or button_timing
        #button.wait_variable(var)
        #print("done waiting.")
        #return PracticeMode



    @staticmethod
    def error_diff_to_utility(error_pre, error_post):
        """
        Calculates the utility given two error measurements.
        @param error_pre: error before practice
        @param error_post: error after practice
        @return: utility value
        """
        diff_timing = (error_pre["timing_left"] + error_pre["timing_right"]) - (
                error_post["timing_left"] + error_post["timing_right"])
        diff_pitch = (error_pre["pitch_left"] + error_pre["pitch_right"]) - (
                error_post["pitch_left"] + error_post["pitch_right"])

        return (diff_timing + diff_pitch) / 2

    def start_playback(self):
        error = self.start_playback_and_calc_error(TaskParameters())
        errors.append(error)
        add_error_plot()

        # if there is an error measurement from before practicing
        # -> calculate the utility and add the measurement to Gaussian process

        if self.practice_parameters["error_before_practice"] is not None:
            #FIXME: hacky - add practice prameters and not task parameters to the gp saving
            self.scheduler.current_task_data().parameters.bpm = self.practice_parameters["bpm"]
            utility = self.error_diff_to_utility(self.practice_parameters["error_before_practice"], error)
            statemachine.save_data_point_and_add_to_gaussian_process(self.midi_file, (
                self.practice_parameters["error_before_practice"], error),
                                                                     self.scheduler.current_task_data().parameters,
                                                                     self.practice_parameters["practice_mode"], utility)
        if GUI_STATE==0:
            # in the expert mode-
            practice_mode = self.get_next_practise_mode_expert()
        else:
            #gp mode
            practice_mode = self.get_next_practise_mode(error)


        tk.Label(root, text=f"Recommended Practice-Mode:\n{practice_mode.name}").pack()

        # TODO: set threshold reasonably with new Errors
        if ERROR_THRESHOLD < error.Summed_right + error.Summed_left:
            self.show_primary_next_state_btn(
                'Start Practice', PracticeModeState(
                    self.scheduler, self.statemachine, self.midi_file, error, self.practice_parameters, practice_mode=practice_mode
                )
            )
            self.show_secondary_next_state_btn('Select new Song', statemachine.select_song_state)
        else:
            # TODO: add visual feedback that error was very low and learning might be finished
            self.show_primary_next_state_btn('Select new Song', statemachine.select_song_state)
            self.show_secondary_next_state_btn(
                'Play Complete Piece\nonce more', PlayCompleteSong(
                    self.scheduler, self.statemachine, self.midi_file, self.practice_parameters
                )
            )


class PracticeModeState(BaseState):
    """
    Practice mode state where the music piece can be practiced in selected practice mode.
    """

    def __init__(self, scheduler: Scheduler, statemachine, midi_file: str, error_from_complete_piece, practice_parameters,
                 practice_mode: PracticeMode):
        super().__init__(scheduler, statemachine)
        self.midi_file = midi_file
        self.error_from_complete_piece = error_from_complete_piece
        self.practice_mode = practice_mode
        # counts the number of times user has played the piece in this practice loop
        self.num_iterations = 0
        self.practice_parameters = practice_parameters

    def _do_on_enter(self):
        self.init_training_interface()

        task = self.scheduler.current_task_data()
        task_parameters = task.parameters

        # timing: change displayed note sheet, so that all notes are D
        if self.practice_mode == PracticeMode.IMP_TIMING:
            task.notes_right = [TaskNote(start=note.start, pitch=62, duration=note.duration)
                                for note in task.notes_right]

            task.notes_left = [TaskNote(start=note.start, pitch=50, duration=note.duration)
                               for note in task.notes_left]
            tk.Label(root, text=f"Practice Mode Improve Timing").place(x=1050, y=50, height=60, width=300)
        # pitch: display message to focus only on correct pitch
        elif self.practice_mode == PracticeMode.IMP_PITCH:
            tk.Label(root,
                     text=f"Practice Mode Improve Pitch\n Transition from one note to another\n"
                          f"when you feel confident \n that you will get the pitch right.\n"
                          f"Do not actively focus on the Timing"
                     ).place(x=1050, y=50, height=300, width=300)
        # left: remove notes in the right hand from task
        elif self.practice_mode == PracticeMode.LEFT:
            task.notes_right = []
            tk.Label(root, text=f"Practice Mode only Left Hand").place(x=1050, y=50, height=60, width=300)
        # right: remove notes in the left hand from task
        elif self.practice_mode == PracticeMode.RIGHT:
            task.notes_left = []
            tk.Label(root, text=f"Practice Mode only Right Hand").place(x=1050, y=50, height=60, width=300)

        midiProcessing.generateMidi(task, outFiles=OUTPUT_FILES_STRS)

        self.gen_ly_for_current_task()
        subprocess.run(['lilypond', '--png', '-o', TEMP_DIR, OUTPUT_LY_STR],
                       stderr=subprocess.DEVNULL)

        self.show_note_sheet(OUTPUT_PNG_STR)

        root.update_idletasks()

        # currently error measurements are not implemented for pitch training mode
        if self.practice_mode != PracticeMode.IMP_PITCH:
            self.show_function_btn('Play Piece in Practice-Mode', self.start_practice)

        self.show_secondary_next_state_btn(
            'Return to Complete Piece', PlayCompleteSong(
                self.scheduler, self.statemachine, self.midi_file,
                practice_parameters={"error_before_practice": self.error_from_complete_piece,
                                     "practice_mode": self.practice_mode,
                                     "bpm": self.practice_parameters ["bpm"]}
            )
        )

    def start_practice(self):
        self.num_iterations += 1

        practice_error = self.start_playback_and_calc_error(TaskParameters())

        if self.num_iterations >= NUM_PRACTICE_ITERATIONS:
            self.statemachine.to_next_state(
                PlayCompleteSong(
                    self.scheduler, self.statemachine, self.midi_file,
                    practice_parameters={"error_before_practice": self.error_from_complete_piece,
                                         "practice_mode": self.practice_mode,
                                         "bpm": self.practice_parameters["bpm"]
                                         }
                )
            )
        else:
            self.show_function_btn('Resume Learning', self.start_practice)

            self.show_secondary_next_state_btn(
                'Return to Complete Piece', PlayCompleteSong(
                    self.scheduler, self.statemachine, self.midi_file,
                    practice_parameters={"error_before_practice": self.error_from_complete_piece,
                                         "practice_mode": self.practice_mode,
                                         "bpm": self.practice_parameters ["bpm"]
                                         }
                )
            )


class EndState(BaseState):

    def _do_on_enter(self):
        quit()


class Statemachine:
    """
    Class that manages state transitions.
    """

    def __init__(self):
        self.scheduler = Scheduler()
        self.gaussian_process = GaussianProcess()
        self.data_logger = DataLogger()
        self.username = ""
        self.complexity_level = 0
        self.main_menu_state = MenuState(self.scheduler, self)
        self.select_song_state = SelectSongState(self.scheduler, self)
        self.select_name_state = SelectNameState(self.scheduler, self)
        self.end_state = EndState(self.scheduler, self)

        self.current_state = self.main_menu_state

    def to_next_state(self, next_state):
        self.current_state.on_exit()
        self.current_state = next_state
        self.current_state.on_enter()

    """
    needs:
    - error: DataFrame (error.pitch_right, error.pitch_left, error.timing_right, error.timing_left) is (error_pre,error_post)
    - task_parameters: TaskParameters
    - practice_mode: PracticeMode
    - utility_measurement: float
    """

    def save_data_point_and_add_to_gaussian_process(self, midi_name: str, error, task_parameters: TaskParameters,
                                                    practice_mode, utility: float):
        """
        Saves a data point to the database and adds it to the gaussian process.
        @param midi_name: name of the midi file
        @param error: error measurements
        @param task_parameters: parameters of the music piece
        @param practice_mode: practice mode that was practiced in inbetween error measurements
        @param utility: utility value
        """
        print("===============SAVE DATA==================")
        print("------------------NAME--------------------")
        print(self.username)
        print("---------------MIDI-NAME------------------")
        print(midi_name)
        print("-----------------ERROR--------------------")
        print("BEFORE")
        print("-pitch")
        print("left", error[0]["pitch_left"], ", right", error[0]["pitch_right"])
        print("-timing")
        print("left", error[0]["timing_left"], ", right", error[0]["timing_right"])
        print("AFTER")
        print("-pitch")
        print("left", error[1]["pitch_left"], ", right", error[1]["pitch_right"])
        print("-timing")
        print("left", error[1]["timing_left"], ", right", error[1]["timing_right"])
        print("----------------UTILITY-------------------")
        print(utility)
        print("------------TASK PARAMETERS---------------")
        print(task_parameters)
        print("--------------PRACTICEMODE----------------")
        print(practice_mode)
        print("==========================================")

        # save data point
        self.data_logger.add_entry(
            midi_filename=midi_name,
            username=self.username,
            error_before=error[0],
            error_after=error[1],
            practice_mode=practice_mode,
            task_parameters=task_parameters
        )
        if GUI_STATE ==0:
            self.data_logger.save_database_expert()
        else:
            self.data_logger.save_database()

        # Save data point to gaussian process
        self.gaussian_process.add_data_point(error[0], task_parameters.bpm, practice_mode, utility)
        self.gaussian_process.update_model()


class DataLogger:
    """
    Database interface class
    """

    def __init__(self):
        if not os.path.isdir(DATA_DIR):
            os.makedirs(DATA_DIR)
        if GUI_STATE ==0:
            dir = EXPERT_DIR
        else:
            dir = "data.h5"

        if os.path.isfile(DATA_DIR + dir):
            if GUI_STATE ==0:

                self.dataframe = pd.read_hdf(DATA_DIR + EXPERT_DIR)
            else:
                self.dataframe = pd.read_hdf(DATA_DIR + "data.h5")

        else:
            dataframe_columns = {
                'midi_filename': np.ndarray((0,), dtype=str),
                'username': np.ndarray((0,), dtype=str),
                # 'task_parameters': np.ndarray((0,), dtype=object),
                'practice_mode': np.ndarray((0,), dtype=str),
                'bpm': np.ndarray((0,), dtype=float),
                'error_before_left_timing': np.ndarray((0,), dtype=float),
                'error_before_right_timing': np.ndarray((0,), dtype=float),
                'error_before_left_pitch': np.ndarray((0,), dtype=float),
                'error_before_right_pitch': np.ndarray((0,), dtype=float),
                'error_after_left_timing': np.ndarray((0,), dtype=float),
                'error_after_right_timing': np.ndarray((0,), dtype=float),
                'error_after_left_pitch': np.ndarray((0,), dtype=float),
                'error_after_right_pitch': np.ndarray((0,), dtype=float),
            }

            self.dataframe = pd.DataFrame(dataframe_columns)

    def add_entry(self, midi_filename, username, error_before, error_after, practice_mode, task_parameters):
        """
        Adds an entry into the database. Does not save it to the database file. (see method save_database)
        @param midi_filename: name of the midi file
        @param username: name of the user that has recorded the data point
        @param error_before: error measurement before practice
        @param error_after: error measurement after practice
        @param practice_mode: practice mode that was practiced in inbetween error measurements
        @param task_parameters:parameters of the music piece
        """
        entry = {
            'midi_filename': ntpath.basename(midi_filename),
            'username': username,
            'practice_mode': practice_mode.name,
            'bpm': task_parameters.bpm
            # 'task_parameters': task_parameters
        }

        if error_before is None:
            entry_error_before = {
                'error_before_left_timing': None,
                'error_before_right_timing': None,
                'error_before_left_pitch': None,
                'error_before_right_pitch': None,
            }
        else:
            entry_error_before = {
                'error_before_left_timing': error_before['timing_left'],
                'error_before_right_timing': error_before['timing_right'],
                'error_before_left_pitch': error_before['pitch_left'],
                'error_before_right_pitch': error_before['pitch_right']
            }

        entry_error_after = {
            'error_after_left_timing': error_after['timing_left'],
            'error_after_right_timing': error_after['timing_right'],
            'error_after_left_pitch': error_after['pitch_left'],
            'error_after_right_pitch': error_after['pitch_right']
        }

        entry.update(entry_error_before)
        entry.update(entry_error_after)

        self.dataframe = pd.concat([self.dataframe, pd.DataFrame([entry])], ignore_index=True)

    def save_database(self):
        """
        Saves the current database to .h5 file.
        """
        self.dataframe.to_hdf(path_or_buf=DATA_DIR + "data.h5", key='data')

    def save_database_expert(self):
        """
        Saves the current database to .expert h5 file.
        """
        if os.path.isfile(DATA_DIR + EXPERT_DIR):
            self.dataframe.to_hdf(path_or_buf=DATA_DIR + EXPERT_DIR, key='data')

        else:
            self.dataframe.to_hdf(DATA_DIR + EXPERT_DIR, key='data', mode ='w')



def add_error_plot():
    """
    Adds a plot to the main window that shows the user's errors.

    @return: None
    """

    global show_error_details_checkbox, show_error_details, canvas

    tk.Label(root, text=" Error visualization:").place(x=1200, y=10, width=150, height=20)

    fig = Figure(figsize=(9, 6), facecolor="white")
    axis = fig.add_subplot(111)
    np.linspace(0, 10, 1000)

    x_values = []
    for i in range(len(errors)):
        x_values.append(i + 1)
    timing_error_right = [err[10] for err in errors]
    pitch_error_right = [err[8] for err in errors]
    axis.plot(x_values, pitch_error_right, "-r", label="Pitch Error", marker='o')
    axis.plot(x_values, timing_error_right, "-b", label="Timing Error", marker='o')

    if change_task:
        for i in change_task:
            axis.axvline(x=i + 0.5, color="black")
            axis.text(i + 0.5, 4.05, "new task", rotation=45, fontsize=8)

    # axis.axhline(y=0.2, color="red", linestyle="--")

    axis.set_xticks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    axis.set_yticks([0, 1])
    axis.set_ylim(0, 1)
    axis.set_xlabel("Trials")
    axis.set_ylabel("Error")

    axis.legend(loc='upper right')
    axis.grid()

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas._tkcanvas.place(x=1050, y=30, width=400, height=400)

    show_error_details.set(False)
    show_error_details_checkbox = tk.Checkbutton(root, text='show error show_error_details',
                                                 command=add_error_details,
                                                 variable=show_error_details)
    # show_error_details_checkbox.place(x=1050, y=440)


def add_error_details():
    """
    Adds descriptions and show_error_details concerning the user's error to the error plot.
    Unsure which details should be displayed, in the scope of the current project this method will not be used
    since the checkbox that switches to the details is deactivated.

    @return: None
    """

    global canvas
    fig = Figure(figsize=(9, 6), facecolor="white")
    axis = fig.add_subplot(111)
    x = np.linspace(0, 1, 10)


    x_values = []
    for i in range(len(errors)):
        x_values.append(i + 1)
    timing_error_right = [err[10] for err in errors]
    pitch_error_right = [err[8] for err in errors]
    axis.plot(x_values, pitch_error_right, "-r", label="Pitch Error", marker='o')
    axis.plot(x_values, timing_error_right, "-b", label="Timing Error", marker='o')

    if change_task:
        for i in change_task:
            axis.axvline(x=i + 0.5, color="black")
            axis.text(i + 0.5, 4.05, "new task", rotation=45, fontsize=8)

    axis.set_xticks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    axis.set_yticks([0, 1])
    axis.set_ylim(0, 1)
    axis.set_xlabel("Trials")
    axis.set_ylabel("Error")

    # axis.plot(x, np.sin(x), "-r", label="Tempo")
    # axis.plot(x, np.cos(x), "-g", label="Notes")
    # axis.plot(x, np.tan(x), "--y", label="etc")

    axis.legend(loc='upper right')
    axis.grid()

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas._tkcanvas.place(x=1050, y=30, width=400, height=400)

    global show_error_details_checkbox, show_error_details
    show_error_details = tk.BooleanVar()
    show_error_details.set(True)
    show_error_details_checkbox = tk.Checkbutton(root, text='show error show_error_details',
                                                 command=add_error_plot,
                                                 variable=show_error_details)
    # show_error_details_checkbox.place(x=1050, y=440)


def set_guidance(guidance):
    global guidance_mode
    guidance_mode = guidance


def get_current_timestamp() -> str:
    return time.strftime("%Y_%m_%d-%H_%M_%S")


if __name__ == '__main__':
    # create file output folder if it does not already exist
    pathlib.Path(TEMP_DIR).mkdir(exist_ok=True)

    statemachine = Statemachine()

    thread_handler.init_midi_keyboard_thread()

    statemachine.to_next_state(statemachine.main_menu_state)

    root.mainloop()
