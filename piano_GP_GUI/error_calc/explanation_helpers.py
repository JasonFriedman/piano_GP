#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dataclasses
from dataclasses import dataclass
from collections import OrderedDict

class unicode_notes:
    FULL_NOTE = "𝅝 "
    HALF_NOTE = "𝅗𝅥 "
    QUARTER_NOTE = "𝅘𝅥 "
    EIGHT_NOTE = "𝅘𝅥𝅮 "
    SIXTEEN_NOTE = "𝅘𝅥𝅯 "


def time_to_fraction(td, bpm, beats_per_measure=4):
    return td*bpm/(60 * beats_per_measure)
    

def fraction_to_single_note(fraction_of_measure, for_ly=False):
    rem_map = OrderedDict(
        FULL_NOTE = (1, "𝅝 "),
        HALF_NOTE = (1/2, "𝅗𝅥 "),
        QUARTER_NOTE = (1/4, "𝅘𝅥 "),
        EIGHT_NOTE = (1/8, "𝅘𝅥𝅮 "),
        # SIXTEEN_NOTE = (1/16, "𝅘𝅥𝅯 "),
        )
    
    if for_ly:
        for key, (d, note) in rem_map.items():
            rem_map[key] = (d, r"\fontsize #4 " + note)
    
    fraction_of_measure = abs(fraction_of_measure)
    
    if fraction_of_measure < 1/10:
        return ""
    
    diffs = [(abs(fraction_of_measure - frac), note) for frac, note in rem_map.values() ]
    
    return sorted(diffs)[0][1]
    

def fraction_to_notes(fraction_of_measure, levels=2, for_ly=False):
    rem_map = OrderedDict(
        FULL_NOTE = (1, "𝅝 "),
        HALF_NOTE = (1/2, "𝅗𝅥 "),
        QUARTER_NOTE = (1/4, "𝅘𝅥 "),
        EIGHT_NOTE = (1/8, "𝅘𝅥𝅮 "),
        # SIXTEEN_NOTE = (1/16, "𝅘𝅥𝅯 "),
        )
    
    if for_ly:
        for key, (d, note) in rem_map.items():
            rem_map[key] = (d, r"\fontsize #4 " + note)
    
    
    fraction_of_measure = abs(fraction_of_measure)
    
    if not for_ly:
        join_base = ""
    else:
        join_base = r"\hspace #0.1 "
    
    out_str = []
    for name, (divisor, note) in rem_map.items():
        div, fraction_of_measure = divmod(fraction_of_measure, divisor)
        if len(out_str) > 0 and int(div) == 0:
            return join_base.join(out_str)
        
        out_str += [note] * int(div)
        
        if len(set(out_str)) >= levels:
            return join_base.join(out_str)
    
    return join_base.join(out_str)
        

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    # for easy copy pasting into f-strings
    #{bcolors.WARNING}
    #{bcolors.ENDC}

class bcolors_empty:
    HEADER = ''
    OKBLUE = ''
    OKCYAN = ''
    OKGREEN = ''
    WARNING = ''
    FAIL = ''
    ENDC = ''
    BOLD = ''
    UNDERLINE = ''



@dataclass
class NoteBase:
    def err_string(self, use_colors=True):
        if use_colors:
            bc = bcolors
        else:
            bc = bcolors_empty
        return f"{bc.WARNING}{self.__class__.__name__}{bc.ENDC}({fmt_dict(dataclasses.asdict(self))})"

    def lyr_string(self, task_infos, lilypond=False, debug=False):
        return self.err_string(use_colors=False)

@dataclass
class NotePlayed(NoteBase):
    pitch : int
    velocity: int
    note_on_time : float
    note_on_time_relative : float
    note_hold_time : float
    
@dataclass
class NoteExpected(NotePlayed):
    pitch_target: int
    velocity_target: int
    note_on_time_target: float
    note_on_time_relative_target: float
    note_hold_time_target: float
    
    def err_string(self, use_colors=True):
        if use_colors:
            bc = bcolors
        else:
            bc = bcolors_empty
            
        err_strs = list()
        if self.pitch != self.pitch_target:
            err_strs.append(f"{bc.WARNING}Pitch{bc.ENDC}:\t\t{self.pitch-self.pitch_target:+d} [{self.pitch} - {self.pitch_target}]")
           
        hold_diff = self.note_hold_time - self.note_hold_time_target
        if abs(hold_diff) >= 0.1:
            err_strs.append(f"{bc.WARNING}Hold Time{bc.ENDC}:\t\t{hold_diff:+.2f} [{self.note_hold_time:.2f} - {self.note_hold_time_target:.2f}]")
            
            
        relative_on_diff = self.note_on_time_relative - self.note_on_time_relative_target
        if abs(relative_on_diff) >= 0.1:
            err_strs.append(f"{bc.WARNING}Rel On Time{bc.ENDC}:\t{relative_on_diff:+.2f} [{self.note_on_time_relative:.2f} - {self.note_on_time_relative_target:.2f}]")
            
        whitespace = " "*len("NoteExpected(")
        err_str = f"\n{whitespace}".join(err_strs)
        
        return f"NoteExpected({err_str})"
    
    def lyr_string(self, task_infos, lilypond=False, debug=False):
        if debug:
            err_str = self.err_string(use_colors=False)
            only_core = err_str[err_str.find("(")+1:-1]
            
            return only_core or r"\null"

        err_strs = list()
        if self.pitch != self.pitch_target:
            err_strs.append(f"Pitch:\t\t{self.pitch-self.pitch_target:+d}")
           
        relative_on_diff = self.note_on_time_relative - self.note_on_time_relative_target
        time_viz = fraction_to_single_note(
                    time_to_fraction(relative_on_diff, task_infos.bpm, task_infos.beats_per_measure()),
                    for_ly = lilypond,
                    # levels=1
                    )
        if time_viz:
            if relative_on_diff > 0:
                text = "too late!"
            else: 
                text = "too early!"
            
            if lilypond:
                text = r" \hspace #1.5 "+ text
        
            err_strs.append(time_viz + text) 
           
        
        hold_diff = self.note_hold_time - self.note_hold_time_target
        time_viz = fraction_to_single_note(
                    time_to_fraction(hold_diff, task_infos.bpm, task_infos.beats_per_measure()),
                    for_ly = lilypond,
                    # levels=1
                    )
        # if abs(hold_diff) >= 0.1:
        if time_viz:
            if hold_diff > 0:
                text = "too long!"
            else: 
                text = "too short!"
            
            if lilypond:
                text = r" \hspace #1.5 "+ text
        
            err_strs.append(time_viz + text)
            
        
        if lilypond and len(err_strs) == 0 :
            return r"\null"
        return "\n".join(err_strs) 

@dataclass
class NoteMissing(NoteBase):
    pitch_target: int
    velocity_target: int
    note_on_time_target: float
    note_on_time_relative_target: float
    note_hold_time_target: float
    
    def lyr_string(self, task_infos, lilypond=False, debug=False):
        return "NoteMissing"
    
    
def fmt_dict(d):
    strs = list()
    for k, v in d.items():
        if type(v) != float:
            strs.append(f"{k}={v}")
        else:
            strs.append(f"{k}={v:.2f}")

    return ", ".join(strs)
@dataclass
class NoteExtra(NotePlayed):
    pass

