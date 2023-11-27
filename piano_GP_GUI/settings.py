import socket
# computer specific settings

# TAU lab computer
if socket.gethostname() == 'mikzot005':
    #'DESKTOP-17671'
    ### CONSTANTS ###
    CHANNEL_PIANO = 0
    CHANNEL_METRO = 0  # for Nord 4, metronome has to be on the same channel
    CHANNEL_LH = 11
    CHANNEL_RH = 10

    INSTRUM_PIANO = 0
    INSTRUM_DRUMS = 0 #9
    INSTRUM_DEXMO = 0

    PITCH_METRO_HI = 39
    PITCH_METRO_LO = 42
    VOLUME = 100
    TIME_AT_START = 0  # start at the beginning

    INTRO_BARS = 1  # no. of empty first bars for metronome intro

    R_TRACK = 0  # right hand track
    L_TRACK = 1  # left hand track
    M_TRACK = 2  # metronome track
    RD_TRACK = 3  # right hand dexmo track
    LD_TRACK = 4  # left hand dexmo track
    TRACKS = 5
elif socket.gethostname() == 'pertinax':

    ### CONSTANTS ###
    CHANNEL_PIANO = 0
    CHANNEL_METRO = 0  # for Nord 4, metronome has to be on the same channel
    CHANNEL_LH = 11
    CHANNEL_RH = 10

    INSTRUM_PIANO = 0
    INSTRUM_DRUMS = 0 #9
    INSTRUM_DEXMO = 0

    PITCH_METRO_HI = 22
    PITCH_METRO_LO = 22
    VOLUME = 10
    TIME_AT_START = 0  # start at the beginning

    INTRO_BARS = 1  # no. of empty first bars for metronome intro

    R_TRACK = 0  # right hand track
    L_TRACK = 1  # left hand track
    M_TRACK = 2  # metronome track
    RD_TRACK = 3  # right hand dexmo track
    LD_TRACK = 4  # left hand dexmo track
    TRACKS = 5

else: # any other computer
    ### CONSTANTS ###
    CHANNEL_PIANO = 0
    CHANNEL_METRO = 9
    CHANNEL_LH = 11
    CHANNEL_RH = 10

    INSTRUM_PIANO = 0
    INSTRUM_DRUMS = 9
    INSTRUM_DEXMO = 0

    PITCH_METRO_HI = 76  # high wood block
    PITCH_METRO_LO = 77  # low wood block
    VOLUME = 100
    TIME_AT_START = 0  # start at the beginning

    INTRO_BARS = 1  # no. of empty first bars for metronome intro

    R_TRACK = 0  # right hand track
    L_TRACK = 1  # left hand track
    M_TRACK = 2  # metronome track
    RD_TRACK = 3  # right hand dexmo track
    LD_TRACK = 4  # left hand dexmo track
    TRACKS = 5