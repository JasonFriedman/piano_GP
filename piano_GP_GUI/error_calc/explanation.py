from collections import namedtuple
from collections import defaultdict
from error_calc.explanation_helpers import NoteExpected, NoteExtra, NoteMissing

Error = namedtuple("Error", ["pitch", "note_hold_time", "timing",
                             "n_missing_notes", "t_missing_notes",
                             "n_extra_notes", "t_extra_notes",
                             "number_of_notes"
                             ])

def get_anchor_map(target_notes):
    anchor_map = defaultdict(lambda: (-1, 0))

    for i in range(len(target_notes)):
        note_i = target_notes[i]

        for j in reversed(range(0, i)):
            # print("j", j)
            note_j = target_notes[j]
            ANCH_THR = 0.1  # seconds ## not sure if needed / has to be greater 0
            time_after_anchor = note_i.note_on_time - note_j.note_on_time
            # print("j", j, time_after_anchor)
            if time_after_anchor > ANCH_THR:
                anchor_map[i] = (j, time_after_anchor)
                break

    # print("ANCHOR MAP", anchor_map)
    return anchor_map


def note_info_list_add_debug(note_info_list, mapping, anchor_map):
    NoteInfoDebug = namedtuple("NoteInfoDebug", ["pitch", "velocity",
                                                 "note_on_time", "note_off_time",
                                                 "time_after_anchor",
                                                 "note_hold_time"])

    debug_list = list()
    # for t_i, a_i in enumerate(mapping):
    for i in range(len(note_info_list)):
        note_i = note_info_list[i]
        n = note_i
        note_hold_time = n.note_off_time - n.note_on_time

        if i not in mapping:
            ## can't calculate anchor for extra notes!
            debug_list.append(
                NoteInfoDebug(n.pitch, n.velocity, n.note_on_time, n.note_off_time,
                              -999, note_hold_time))
            continue

        t_i = mapping.index(i)

        anchor, anchor_td = anchor_map[t_i]
        if anchor == -1:
            time_after_anchor = 0
        elif mapping[anchor] == -1:
            time_after_anchor = anchor_td
        else:
            anchor_note = note_info_list[mapping[anchor]]
            time_after_anchor = n.note_on_time - anchor_note.note_on_time

        # print("TAA", i, anchor, mapping[anchor], time_after_anchor)

        debug_list.append(
            NoteInfoDebug(n.pitch, n.velocity, n.note_on_time, n.note_off_time,
                          time_after_anchor, note_hold_time))
    print("debug_list", debug_list)
    return debug_list


def get_explanation(task_data, actual, mapping,
                    inject_explanation=True,
                    openface_data=None,
                    plot=False,
                    ):
    target = task_data.all_notes()
    print("task_data", task_data.__dict__)
    print("target:", target[0].note_off_time - target[0].note_on_time)
    total_time_note_on = 0
    for t in target:
        total_time_note_on += t.note_off_time - t.note_on_time

    anchor_map = get_anchor_map(target)
    target_debug = note_info_list_add_debug(target, list(range(len(target))), anchor_map)
    actual_debug = note_info_list_add_debug(actual, mapping, anchor_map)

    #### EXTRA NOTES ####

    extra_notes_dict = dict(left=list(), right=list())
    extra_notes = [a for idx, a in enumerate(actual_debug) if idx not in mapping]
    for extra_note in extra_notes:
        if len(task_data.notes_left) == 0:
            extra_notes_dict["right"].append(extra_note)
            continue
        if len(task_data.notes_right) == 0:
            extra_notes_dict["left"].append(extra_note)
            continue

        pitch_time_dist = [
            (abs(extra_note.pitch - n.pitch), abs(extra_note.note_on_time - n.note_on_time), "left")
            for n in task_data.midi.left]
        pitch_time_dist.extend([(abs(extra_note.pitch - n.pitch),
                                 abs(extra_note.note_on_time - n.note_on_time), "right")
                                for n in task_data.midi.right]
                               )
        hand = sorted(pitch_time_dist)[0][2]
        extra_notes_dict[hand].append(extra_note)

    errors = []
    output_note_list = list()

    for hand in ("left", "right"):
        num_notes = len(getattr(task_data, f"notes_{hand}"))
        error_timing = 0
        error_note_hold_time = 0
        error_pitch = 0

        notes_missing = 0
        notes_missing_t = 0

        for t_i, a_i in enumerate(mapping):
            ## check whether the target notes belogs to the hand we want to calculate
            ## the error for.
            if task_data.note2hand(target[t_i]) != hand:
                continue

            t = target_debug[t_i]
            if a_i == -1:
                notes_missing += 1
                notes_missing_t += t.note_hold_time
                output_note_list.append(NoteMissing(t.pitch, t.velocity,
                                                    t.note_on_time, t.time_after_anchor,
                                                    t.note_hold_time))

                continue

            a = actual_debug[a_i]

            pitch_diff = t.pitch - a.pitch
            if abs(pitch_diff) > 0:
                # print("WRONG PITCH", t_i, t, a_i, a)
                # fixme: superwierd! at least the name is extremely non-suitable
                # in the current implementation the pitch error is calculated as a sum or durations of the wrongly played notes
                error_pitch += (t.note_off_time - t.note_on_time)

            hold_diff = t.note_hold_time - a.note_hold_time
            if abs(hold_diff) > 0:
                # print("WRONG HOLD TIME", t_i, a_i, t.note_hold_time, a.note_hold_time)
                error_note_hold_time += abs(hold_diff)

            timing_diff = t.time_after_anchor - a.time_after_anchor
            if abs(timing_diff) > 0:
                # print("WRONG TIMING", t_i, a_i, t.time_after_anchor, a.time_after_anchor)
                error_timing += min(abs(timing_diff), 1.0)

            output_note_list.append(
                NoteExpected(a.pitch, a.velocity, a.note_on_time, a.time_after_anchor,
                             a.note_hold_time,
                             t.pitch, t.velocity, t.note_on_time, t.time_after_anchor,
                             t.note_hold_time))

        # if only played with one hand, so to avoid division by zero
        if num_notes == 0:
            number = 1
        else:
            number = num_notes
        # fixme: what is this?
        #b = (task_data.time_signature[0] / task_data.time_signature[1]) / task_data.bpm * 60 * 1000
        print("number of notes missing", notes_missing)
        print("error_timing ", error_timing)
        print ("task data bpm ", task_data.bpm)

        errors.append(Error(pitch=error_pitch / total_time_note_on,
                            note_hold_time=error_note_hold_time / (
                                        task_data.number_of_bars * task_data.time_signature[0]),
                            # how to get on number of bars and signature(?)
                            timing=error_timing / (number - notes_missing), #   number),
                            n_missing_notes=notes_missing / number,
                            t_missing_notes=notes_missing_t / number,
                            n_extra_notes=len(extra_notes_dict[hand]) / number,
                            t_extra_notes=sum(
                                extra.note_hold_time for extra in extra_notes_dict[hand]),
                            number_of_notes=num_notes
                            ))

        for a in extra_notes:
            output_note_list.append(NoteExtra(a.pitch, a.velocity,
                                              a.note_on_time, a.time_after_anchor,
                                              a.note_hold_time))

    def get_note_on(note):
        if hasattr(note, "note_on_time"):
            return note.note_on_time
        if hasattr(note, "note_on_time_target"):
            return note.note_on_time_target
        raise Exception("Note type can't be sorted bc no note on.")

    output_note_list = sorted(output_note_list, key=get_note_on)

    # pprint(output_note_list)

    # import shutil
    # cwidth = shutil.get_terminal_size().columns
    # print("NOTES".center(cwidth, "+"))
    # for n in output_note_list:
    #     print(n.err_string())

    # ONE FOR EACH HAND?

    error_left, error_right = errors

    error_total = Error(*[l + r for l, r in zip(error_left, error_right)])

    # TODO missing missing notes / extra notes

    if inject_explanation:
        insert_lyrics_into_ly(output_note_list, task_data)

    if plot:
        try:
            note_list_to_plot(output_note_list, task_data, openface_data)
        except:
            import traceback
            traceback.print_exc()

    return output_note_list, error_total, error_left, error_right


# lyr_string(self, task_infos, lilypond=False, debug=False):

def note_list_to_lyrics(note_list, task_infos, lilypond, debug=False):
    lyrics = [r"\override LyricText.self-alignment-X = #1" + "\n"]
    buffer = list()

    markup_params = r"\hspace #2 \fontsize #-2 \box \pad-around #0.5"

    for note in note_list:
        if type(note) == NoteExtra:
            cols = note.lyr_string(task_infos, lilypond=lilypond, debug=debug).split(", ")
            joined_cols = "\n".join([fr"\line {{ {c} }}" for c in cols])
            tmp_lyric = fr"{markup_params} \column {{ {joined_cols} }} \hspace #2 "

            buffer.append(tmp_lyric)
            continue

        buff_lyric = " ".join(buffer)
        buffer.clear()

        if type(note) == NoteExpected:
            cols = note.lyr_string(task_infos, lilypond=lilypond, debug=debug).split("\n")
            joined_cols = "\n".join([fr"\line {{ {c} }}" for c in cols])
            lyric = fr"\markup{{ {buff_lyric} {markup_params} \column {{ {joined_cols} }} }}"

        if type(note) == NoteMissing:
            cols = note.lyr_string(task_infos, lilypond=lilypond, debug=debug).split(", ")
            joined_cols = "\n".join([fr"\line {{ {c} }}" for c in cols])
            lyric = fr"\markup{{ {buff_lyric} {markup_params} \column {{ {joined_cols} }} }}"

        lyrics.append(lyric)

    all_lines = "\n".join(lyrics)

    final_lyrics = fr"\addlyrics {{ {all_lines} }}"

    return final_lyrics


def note_list_to_plot(note_list, task_infos, openface_data=None, debug=False):
    import matplotlib.pyplot as plt
    plt.figure(figsize=(16, 9))
    min_y = min([n.pitch for n in note_list if hasattr(n, "pitch")])
    for idx, note in enumerate(note_list):
        if type(note) == NoteExtra:
            cols = note.lyr_string(task_infos, lilypond=False, debug=debug).split(", ")
            x, y = note.note_on_time, note.pitch - min_y
            plt.scatter(x, y, c="b")
            plt.annotate("\n".join(cols), xy=(x, y), xytext=(x, -2 - (idx % 5)),
                         arrowprops=dict(alpha=0.2), )


        elif type(note) == NoteExpected:
            cols = note.lyr_string(task_infos, lilypond=False, debug=debug).split("\n")
            x, y = note.note_on_time, note.pitch - min_y

            plt.scatter(x, y, c="b")
            plt.annotate("\n".join(cols), xy=(x, y), xytext=(x, -2 - (idx % 5)),
                         arrowprops=dict(alpha=0.2), )

        if type(note) == NoteMissing:
            cols = note.lyr_string(task_infos, lilypond=False, debug=debug).split(", ")
            x, y = note.note_on_time_target, note.pitch_target - min_y
            plt.scatter(x, y, c="b")
            plt.annotate("\n".join(cols), xy=(x, y), xytext=(x, -2 - (idx % 5)),
                         arrowprops=dict(alpha=0.2), )

    if openface_data is not None:
        # openface_data = openface_data.iloc[:-1,:]

        print(openface_data)

        from openface_data_acquisition import train_classifier_on_saved
        clf, target_classes, preprocess = train_classifier_on_saved()

        df = preprocess(openface_data)

        # prediction = clf.predict(df)
        prediction = clf.decision_function(df)

        # target_class = self.class_names[predicted_class]

        line_objects = plt.plot(openface_data.timestamp, prediction)
        plt.legend(line_objects, list(target_classes))

    # plt.legend()
    plt.ylim([-8, None])
    plt.show()


def insert_lyrics_into_ly(note_list, task_infos):
    # import shutil
    from pathlib import Path
    original_ly = Path("output/temp/output.ly")
    modified_ly = Path("output/temp/output_with_errors.ly")

    content = original_ly.read_text().splitlines()
    lyric_str = note_list_to_lyrics(note_list, task_infos, lilypond=True)

    # print(lyric_str)

    for idx, line in enumerate(content):
        if not r"\context Voice" in line:
            continue
        else:
            break
    else:
        print("(insert_lyrics_into_ly) LINE NOT FOUND!!!")
        return

    content.insert(idx + 1, lyric_str)

    modified_ly.write_text("\n".join(content), encoding='utf-8')

    import subprocess
    subprocess.run(['lilypond', '--png', '-o', modified_ly.parent, modified_ly],
                   stderr=subprocess.DEVNULL)
