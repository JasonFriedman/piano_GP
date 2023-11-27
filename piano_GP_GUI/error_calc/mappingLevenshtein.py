"""
Calculates the error in regards to pitch and timing using an approach inspired
by the levenshtein distance.
"""

from collections import defaultdict, namedtuple
from pprint import pprint



def viz_d(d):
    import numpy as np
    xs, ys = zip(*d.keys())
    v = np.zeros((max(xs)+2, max(ys)+2))
    
    for (x, y), val in d.items():
        v[x+1, y+1] = val
    
    print(v)


def damerau_levenshtein_distance(s1, s2, with_transposition=True, verbose=True):
    d = {}
    way = defaultdict(list)
    mapping = defaultdict(list)
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    for i in range(-1,lenstr1):
        d[(i,-1)] = i+1
    for j in range(-1,lenstr2):
        d[(-1,j)] = j+1

    for i in range(lenstr1):
        for j in range(lenstr2):
            if s1[i] == s2[j]:
                cost = 0
                cost_way = ["-"]
            else:
                cost = 1
                cost_way = ["sub"]
                
                
            options = zip ([   
                           d[(i-1,j)] + 1, # deletion
                           d[(i,j-1)] + 1, # insertion
                           d[(i-1,j-1)] + cost, # substitution
                    ],#, ["del", "ins", "sub"], 
                [
                    way[(i-1,j)] + ["del"], # deletion
                    way[(i,j-1)] + ["ins"], # insertion
                    way[(i-1,j-1)] + cost_way ,
                    ],
                [
                    mapping[(i-1,j)] + [()], # deletion
                    mapping[(i,j-1)] + [(i,j)], # insertion
                    mapping[(i-1,j-1)] + [(i,j)] ,
                    ])
            best_option = sorted(options)[0]
            d[(i,j)] = best_option[0]
            way[(i,j)] = best_option[1]
            mapping[(i,j)] = best_option[2]
            if not with_transposition:
                continue
            
            if i and j and s1[i]==s2[j-1] and s1[i-1] == s2[j]:
                if d[i-2,j-2] + cost <= d[(i,j)]:
                    d[(i,j)] = d[i-2,j-2] + cost # transposition
                    way[(i,j)] = way[(i-2,j-2)] + ["trans1", "trans2"]

    
    
    distance = d[lenstr1-1,lenstr2-1]
    way_description = way[lenstr1-1,lenstr2-1]
    
    mapping = mapping[lenstr1-1,lenstr2-1]
    mapping = [t for t in mapping if len(t) > 0]
    mapping = {a:t for t, a in mapping}
    
    
    if verbose:
        # viz_d(d)
        print(distance)
        print(way_description)
        # print(mapping)
        
    return mapping



def get_mapping(task_data, actualNoteInfoList):
    targetNoteInfoList = task_data.all_notes()
    target = sorted(targetNoteInfoList, key=lambda n:n.note_on_time)
    actual = sorted(actualNoteInfoList, key=lambda n:n.note_on_time)
    
    
    target_pitches = [-999] + [n.pitch for n in target]
    actual_pitches = [-999] + [n.pitch for n in actual]
    
    print("TP", target_pitches)
    print("AP", actual_pitches)
    
    mapping = damerau_levenshtein_distance(target_pitches, actual_pitches)
    
    ## clean up mapping from the -999 stuff
    del mapping[0]
    mapping = {k-1:v-1 for k, v in mapping.items()}
    print("MAP", mapping)
    
    rmap = dict() #defaultdict(list)
    for target_i in range(len(targetNoteInfoList)):
        rmap[target_i] = [actual_i for actual_i, ti in mapping.items() if 
                               ti == target_i]

    print("RMAP", rmap)   
        
    for l in rmap.values():
        l.append(-1)
    mapping = [rmap[i][0] for i in range(len(targetNoteInfoList))]
    
    return mapping
    
    
    
    
    

# if __name__ == "__main__":
#     from midiInput import NoteInfo
#     from testErrorCalc import simple_scale, drop_notes, repeat_notes, wrong_pitch, add_pause
    
#     target_notes = simple_scale()
#     actual_notes = target_notes.copy()
    
#     drop_notes(actual_notes)
#     # repeat_notes(actual_notes)
#     # wrong_pitch(actual_notes)
#     # add_pause(actual_notes)
    
#     actual_notes = sorted(actual_notes, key=lambda n: n.note_on_time)
    
#     print("TARGET_NOTES:")
#     print(target_notes)
#     print("ACTUAL_NOTES:")
#     print(actual_notes)
    
#     # print(computeError(target_notes, actual_notes))
#     output_note_list, error = computeError(target_notes, actual_notes)
    
#     # print(note_list_to_lyrics(output_note_list))
#     # note_list_to_plot(output_note_list)
#     # insert_lyrics_into_ly(output_note_list)