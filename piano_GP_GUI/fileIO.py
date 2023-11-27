import xml.etree.ElementTree as ET
from xml.dom import minidom
import json

def create_xml(path, midiPrefix, options, targetNotes):
    """
    Creates a new XML tree containing the necessary nodes.

    @param path: Directory of the XML file.
    @param midiPrefix: Prefix of the XML file (i.e. timestamp).
    @param options: Current task's options set by the user.
    @param targetNotes: List of notes that the user is supposed to play.
    @return: None
    """

    root = ET.Element("MIDI", midiNo=midiPrefix)

    targets = ET.SubElement(root, "target_notes")

    targetNotesJson = json.dumps([ni._asdict() for ni in targetNotes])
    ET.SubElement(targets, "notes", name="Note List").text = targetNotesJson
    ET.SubElement(targets, "options", name="Option List").text = str(options)

    ET.SubElement(root, "trials")

    tree = ET.ElementTree(root)
    tree.write(path + midiPrefix + ".xml")


def create_trial_entry(path, midiPrefix, timestamp, guidanceMode, actualNotes, error):
    """
    Creates a new trial entry in an existing XML file.
    The trial number will be the file's current max trial number plus one.

    @param path: Directory of the XML file.
    @param midiPrefix: Prefix of the XML file (i.e. timestamp).
    @param timestamp: Timestamp of the trial.
    @param guidanceMode: Guidance Mode (Dexmo) used for the task.
    @param actualNotes: List of notes that the user actually played in the trial.
    @param error: Computed error value.
    @return: None
    """

    # parse XML file
    file = path + midiPrefix + ".xml"
    try:
        tree = ET.parse(file)
    except:
        print("Cannot open", file)
        return None

    root = tree.getroot()
    trials = root.find("trials")

    trialNo = len(list(trials)) + 1

    trial = ET.SubElement(trials, "trial", trial_no=str(trialNo), timestamp=str(timestamp))

    actualNotesJson = json.dumps([ni._asdict() for ni in actualNotes])
    ET.SubElement(trial, "notes", name="Played Notes").text = actualNotesJson
    ET.SubElement(trial, "guidance", name="Guidance Mode").text = str(guidanceMode)
    ET.SubElement(trial, "error", name="Error value").text = str(error)

    tree.write(file)


###TODO: remove?
def prettifyXML(filepath):
    """
    Returns a pretty-printed XML string for the Element.

    @param elem: Element of the XML tree.
    @return: Pretty-printed XML string for the Element.
    """
    from pathlib import Path
    filepath = Path(filepath)

    rough_string = filepath.read_text()
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


###TODO: remove?
def printXML(filepath, pretty):
    """
    Prints a given XML file, either directly or prettified (formatted).
    IMPORTANT: this prints out quotations marks as &quot etc.
            but they are written correctly to file.

    @param filepath: Path of the XML file.
    @param pretty: True for having the output prettified.
    @return: None
    """

    if pretty:
        print(prettifyXML(filepath))
    else:
        tree = ET.parse(filepath)
        root = tree.getroot()
        print(ET.tostring(root))


if __name__ == "__main__":

    outpath = "./output/"
    midiPrefix = "midi001"   # without .mid
    outfile = outpath + midiPrefix + ".xml"
    options = [1, True, "bla"]

    from midiInput import NoteInfo

    targetNotes = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]
    targetNotes = [NoteInfo(*t) for t in targetNotes]
    actualNotes = [[11, 22, 33, 44], [55, 66, 77, 88], [99, 0, 0, 0]]
    actualNotes = [NoteInfo(*t) for t in actualNotes]

    create_xml(outpath, midiPrefix, options, targetNotes)
    printXML(outfile, True)
    print("\n\n")
    create_trial_entry(outpath, midiPrefix, "01-11-1999", "guidance1", actualNotes, "123")
    create_trial_entry(outpath, midiPrefix, "22-02-2222", "guidance2", actualNotes, "42.666")
    printXML(outfile, True)
