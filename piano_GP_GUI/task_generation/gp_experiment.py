import GPy
import GPyOpt
import random
import numpy as np
from tqdm import tqdm

from matplotlib import pyplot as plt
from matplotlib.patches import Patch

import enum
from collections import namedtuple

# imports from other files
from generator import generate_task
from generator import TaskParameters
from note_range_per_hand import NoteRangePerHand

# list of possible performer types
performers = ["bad_pitch", "balanced", "bad_timing"]


class PracticeMode(enum.Enum):
    """
        class to define all possible practice modes
    """
    IMP_PITCH = 0
    IMP_TIMING = 1
    SLOWER = 2


# interval of possible bpm_values
BPM_BOUNDS = [50, 200]

Error = namedtuple("Error", "pitch timing")


class GaussianProcess:
    def __init__(self, bpm_norm_fac=100):
        self.data_X = None
        self.data_X_old_shape = None

        self.data_Y = None

        self.bpm_norm_fac = bpm_norm_fac

        self.domain = [
            {'name': 'practice_mode', 'type': 'categorical', 'domain': (0, 1, 2)},
            {'name': 'bpm', 'type': 'continuous', 'domain':
                (self._norm_bpm(BPM_BOUNDS[0]), self._norm_bpm(BPM_BOUNDS[1]))},
            {'name': 'error_pitch', 'type': 'continuous', 'domain': (0, 1)},
            {'name': 'error_timing', 'type': 'continuous', 'domain': (0, 1)}
        ]

        self.space = GPyOpt.core.task.space.Design_space(self.domain)

    def _norm_bpm(self, v):
        return v / self.bpm_norm_fac

    def _params2domain(self, error, task_parameters, practice_mode):
        domain_x = [
            practice_mode.value,
            self._norm_bpm(task_parameters.bpm),
            error.pitch,
            error.timing
        ]

        return np.array([domain_x])

    def _domain2space(self, domain_x):
        # Converts the domain variables into the GPs input space
        # does one-hot encoding
        space_rep = self.space.unzip_inputs(domain_x)
        return space_rep

    def _get_bayes_opt(self):
        return self.bayes_opt

    def update_model(self):
        """
            If the Gaussian Process' training data has changed, "trains" the GP on the complete data set.
        """
        # only calculate new model if data changed
        if self.data_X is None or self.data_X.shape == self.data_X_old_shape:
            return

        self.data_X_old_shape = self.data_X.shape

        kernel = GPy.kern.RBF(input_dim=self.space.model_dimensionality,
                              variance=0.01,
                              lengthscale=1)

        # kernel = GPy.kern.Matern52(input_dim=self.space.model_dimensionality,
        #                       variance=0.01,
        #                       lengthscale=1)

        self.bayes_opt = GPyOpt.methods.BayesianOptimization(
            f=None, domain=self.domain, X=self.data_X, Y=self.data_Y,
            maximize=True, normalize_Y=False,
            kernel=kernel,
        )

        self.bayes_opt.model.max_iters = 0
        self.bayes_opt._update_model()

        # self.bayes_opt.model.model.kern.variance.constrain_bounded(0.2,1,
        #                                                            warning=False)
        # self.bayes_opt.model.model.kern.lengthscale.constrain_bounded(1, 2,
        #                                                            warning=False)

        self.bayes_opt.model.max_iters = 1000
        self.bayes_opt._update_model()

    def get_estimate(self, error, task_parameters, practice_mode):
        """
            Estimates the utility value for a given practice mode
        @param error: namedtuple("Error", "pitch timing")
        @param task_parameters: task_parameters of the music piece
        @param practice_mode: the practice mode for which the utility value should be estimated
        @return: gaussian process' estimate of the utility value
        """
        if not hasattr(self, "bayes_opt"):
            # if there is no model yet, e.g. in the first iteration
            # print("(GP) DATA_X IS NONE, RETURNING RANDOM NUMBER")
            return random.random()

        bayes_opt = self._get_bayes_opt()

        x = self._params2domain(error, task_parameters, practice_mode)
        x = self._domain2space(x)

        mean, var = bayes_opt.model.predict(x)

        return mean[0]

    def get_best_practice_mode(self, error, task_parameters, epsilon=0.05):
        """
            computes the gaussian process' estimate of the best practice mode
            for exploration: currently utilizes epsilon-greedy exploration
        @param error: namedtuple("Error", "pitch timing")
        @param task_parameters: task_parameters of the music piece
        @param (optional) epsilon: the probability of making a random decision. set to 0 for no exploration.
        @return: chosen for given input parameters PracticeMode
        """
        all_practice_modes = list(PracticeMode)
        # epsilon-greedy
        if random.random() > epsilon:
            max_i = np.argmax([self.get_estimate(error, task_parameters, pm)
                               for pm in all_practice_modes])
            return all_practice_modes[max_i]
        else:
            return np.random.choice(all_practice_modes)

    def add_data_point(self, error, task_parameters, practice_mode, utility_measurement):
        """
            Adds a new datapoint to the dataset of the gaussian process.
            Does not update the Gaussian Process for the new training data (see: update_model)
        @param error: namedtuple("Error", "pitch timing")
        @param task_parameters: task_parameters of the music piece
        @param practice_mode: practice mode in which the performer practiced
        @param utility_measurement: observed utility value for the given parameters
        """
        new_x = self._params2domain(error, task_parameters, practice_mode)
        new_y = [utility_measurement]

        if self.data_X is None:
            self.data_X = new_x
            self.data_Y = [new_y]
        else:
            self.data_X = np.vstack((self.data_X, new_x[0]))
            self.data_Y = np.vstack((self.data_Y, new_y[0]))


def generate_random_piece(task_parameters):
    """
        Generates an array, that resembles a random music piece generated by the given task parameters
    @param task_parameters: task_parameters of the music piece
    @return: tuple: (right-hand, left-hand) - array of the notes (start, pitch, duration)
    """

    task = generate_task(task_parameters=TaskParameters(
        bpm=task_parameters.bpm,
        # fixed:
        noOfBars=task_parameters.noOfBars, maxNotesPerBar=task_parameters.maxNotesPerBar,
        noteValues=task_parameters.noteValues,
        note_range_left=NoteRangePerHand.C_DUR, note_range_right=NoteRangePerHand.C_DUR,
        right=True, left=True, alternating=False
    ))

    # TODO: What is duration? 1/4 note = 1? 1/8 note = 0.5?

    return task.notes_right, task.notes_left


def simulate_pitch_err(task_parameters, performer="balanced", generated_piece=None):
    """
        Simulates a pitch error, a performer could produce for a certain music piece
    @param task_parameters: task_parameters of the music piece
    @param performer: balanced, bad_timing or bad_pitch
    @param (optional) generated_piece: if not given, randomly generates a new piece by given task_parameters
    @return: tuple: pitch error - (right, left)
    """
    # if no "music piece" is given, randomly generate a new one from given task_parameters
    if generated_piece is None:
        generated_piece = generate_random_piece(task_parameters)

    pitch_error = []
    for hand in generated_piece:
        total_number_notes = len(hand)
        durations = np.asarray([note.duration for note in hand])

        if performer == "bad_pitch":
            failure_rate = 0.4
        else:
            failure_rate = 0.15

        # randomly chooses for each note whether it was successfully played in pitch with given failure rate
        failed_notes = np.random.choice(2, total_number_notes, p=[1 - failure_rate, failure_rate])

        # pitch error: percentage of failed notes in relation to the total number of notes
        # weighted by the duration of each note
        pitch_error.append(np.sum(failed_notes * durations) / np.sum(durations))

    # right hand, left hand
    return pitch_error[0], pitch_error[1]


def simulate_timing_err(task_parameters, performer="balanced", generated_piece=None):
    """
        Simulates timing errors, a performer could produce for a certain music piece
    @param task_parameters: task_parameters of the music piece
    @param performer: balanced, bad_timing or bad_pitch
    @param (optional) generated_piece: if not given, randomly generates a new piece by given task_parameters
    @return: tuple: timing error - (right, left)
    """
    if task_parameters.timeSignature != (3, 4) and task_parameters.timeSignature != (4, 4):
        raise NotImplementedError("Timing Error Simulation currently only implemented for time signatures 3/4 and 4/4.")

    # formula to calculate the total number of mseconds of a bar from given time signature and bpm
    mseconds_per_bar = (task_parameters.timeSignature[0] / task_parameters.bpm) * 60 * 1000

    # if no "music piece" is given, randomly generate a new one from given task_parameters
    if generated_piece is None:
        generated_piece = generate_random_piece(task_parameters)

    if performer == "bad_timing":
        ms_mean = 300
        ms_std_deviation = 200
    else:
        ms_mean = 100
        ms_std_deviation = 50

    timing_errors = []
    for hand in generated_piece:
        # grouping the notes in each bar
        grouped_in_bars = []
        index = 0
        # skip the first bar (metronome cue)
        for bar in range(1, task_parameters.noOfBars):
            group = []
            while index < len(hand) \
                    and hand[index].start < (bar + 1) * task_parameters.timeSignature[0]:
                group.append(hand[index])
                index += 1
            grouped_in_bars.append(group)

        # TODO: look at pauses and calulate anticipation time

        # "timing_errors" accumulates all timing errors over the whole music piece
        timing_offsets = []
        # for each bar: loop over the number of notes in the bar
        for notes in grouped_in_bars:
            ms_errors_in_bar = []
            for n in range(len(notes)):
                timing_offset = abs(np.random.normal(ms_mean, ms_std_deviation))
                # if sum of timing deviations is larger than number of mseconds in bar:
                # append the remaining mseconds of the bar
                if (sum(ms_errors_in_bar) + timing_offset) > mseconds_per_bar:
                    ms_errors_in_bar.append(mseconds_per_bar - np.sum(ms_errors_in_bar))
                    break
                ms_errors_in_bar.append(timing_offset)

            timing_offsets.append(ms_errors_in_bar)

        # flattens the array of timing errors ([[1,2,3],[4,5,6]] -> [1,2,3,4,5,6])
        timing_offsets = sum(timing_offsets, [])

        # normed by the length of a bar in mseconds
        timing_errors.append(np.mean(timing_offsets) / mseconds_per_bar)
        # Std. Deviation could also be used as Timing Error criterion

    # right hand, left hand
    return timing_errors[0], timing_errors[1]


def simulate_error_tuple(task_parameters, performer):
    generated_piece = generate_random_piece(task_parameters)

    # currently only one error is passed to the GP which is the average between right and left hand

    pitch_error = simulate_pitch_err(task_parameters, performer=performer, generated_piece=generated_piece)
    pitch_error = (pitch_error[0] + pitch_error[1]) / 2

    timing_error = simulate_timing_err(task_parameters, performer=performer, generated_piece=generated_piece)
    timing_error = (timing_error[0] + timing_error[1]) / 2
    error = Error(pitch=pitch_error, timing=timing_error)

    return error


def perf_after_practice(error_pre, practice_mode):
    if practice_mode == PracticeMode.IMP_PITCH:
        return Error(pitch=error_pre.pitch * 0.5,
                     timing=error_pre.timing + error_pre.timing * (0.1 * random.random()))
    if practice_mode == PracticeMode.IMP_TIMING:
        return Error(pitch=error_pre.pitch + error_pre.pitch * (0.1 * random.random()),
                     timing=error_pre.timing * 0.5)
    if practice_mode == PracticeMode.SLOWER:
        return Error(pitch=error_pre.pitch * 0.75,
                     timing=error_pre.timing * 0.75)


def error_diff_to_utility(error_pre, error_post):
    diff_timing = error_pre.timing - error_post.timing
    diff_pitch = error_pre.pitch - error_post.pitch

    # TODO: improve error weighting
    return (diff_timing + diff_pitch) / 2


def plot_simulation(iterations=10000):
    tp = TaskParameters(bpm=120)

    fig, axs = plt.subplots(2, 3, sharey='row', figsize=(15, 9))
    fig.suptitle(f'Histogram of Simulated Pitch Errors for {iterations} iterations', fontsize=14)
    for i in range(len(performers)):
        pitch_errors = [simulate_pitch_err(tp, performer=performers[i]) for iteration in
                        tqdm(range(iterations), desc=f"Pitch-Error-Sim {performers[i]:>10} | Iterations: ")]

        for j, hand in enumerate(["Right", "Left"]):
            axs[j, i].hist([error[j] for error in pitch_errors], bins=30)
            axs[j, i].set_title(f"Pitch Error ({hand}): {performers[i]}")
            axs[j, i].set_xticks(np.arange(0, 1.1, 0.1))
            axs[j, i].set_xlabel("pitch error")
            axs[j, i].set_ylabel("number of occurences")
    plt.show()

    fig, axs = plt.subplots(2, 3, sharey='row', figsize=(15, 9))
    fig.suptitle(f'Histogram of Simulated Timing Errors for {iterations} iterations', fontsize=14)
    for i in range(len(performers)):
        timing_errors = [simulate_timing_err(tp, performer=performers[i]) for iteration in
                         tqdm(range(iterations), desc=f"Timing-Error-Sim {performers[i]:>9} | Iterations: ")]
        for j, hand in enumerate(["Right", "Left"]):
            axs[j, i].hist([error[j] for error in timing_errors], bins=30)
            axs[j, i].set_title(f"Timing-Errors ({hand}): {performers[i]}")
            axs[j, i].set_xticks(np.arange(0, 1.1, 0.1))
            axs[j, i].set_xlabel("mean timing error")
            axs[j, i].set_ylabel("number of occurences")
    plt.show()


# Different functions used to deliver a utility value to the plot_utility function -------------------------------------

# returns the utility calculated with method: error_diff_to_utility
def _utility_practice_mode(practice_mode, error_pre):
    error_post = perf_after_practice(error_pre, practice_mode)
    utility = error_diff_to_utility(error_pre, error_post)

    return utility


# wrapper function to abstract argument practice mode
def utility_practice_mode(practice_mode):
    return lambda error_pre: _utility_practice_mode(practice_mode, error_pre)


# returns the maximum utility obtainable by pure utility calculation with method: error_diff_to_utility
def utility_max(error_pre):
    return max([error_diff_to_utility(error_pre, perf_after_practice(error_pre, pm)) for pm in list(PracticeMode)])


# returns the utility estimate of a gaussian process for a specific practice mode
def _utility_gp(gaussian_process, task_parameter, practice_mode, error_pre):
    return gaussian_process.get_estimate(error_pre, task_parameter, practice_mode)


# wrapper function to abstract arguments gaussian process and practice mode
def utility_gp(gaussian_process, task_parameter, practice_mode):
    return lambda error_pre: _utility_gp(gaussian_process, task_parameter, practice_mode, error_pre)[0]


# ----------------------------------------------------------------------------------------------------------------------

def plot_utility(utility_function, density=50, title="Utility", data_points=None):
    plot_data = []
    for i, error_pitch in enumerate(np.linspace(0, 1, density)):
        for j, error_timing in enumerate(np.linspace(0, 1, density)):
            error_pre = Error(pitch=error_pitch, timing=error_timing)
            utility = utility_function(error_pre)

            plot_data.append([error_pitch, error_timing, utility])

    plot_data = np.array(plot_data)

    fig = plt.figure(figsize=(10, 7))
    ax = plt.axes(projection="3d")

    ax.scatter3D(plot_data[:, 0], plot_data[:, 1], plot_data[:, 2], s=8)

    if data_points is not None:
        ax.scatter3D(data_points[:, 0], data_points[:, 1], data_points[:, 2], color="red", alpha=0.6)

    ax.set_title(title)
    ax.set_xlabel('error_pitch')
    ax.set_ylabel('error_timing')
    ax.set_zlabel('utility')
    ax.set_zlim(0, 0.5)

    plt.show()


def plot_utility_all(gaussian_process, task_parameter, density):
    plot_data_pitch = []
    plot_data_timing = []
    plot_data_slower = []

    for error_pitch in np.linspace(0, 1, density):
        for error_timing in np.linspace(0, 1, density):
            error_pre = Error(pitch=error_pitch, timing=error_timing)

            utility_pitch = gaussian_process.get_estimate(error_pre, task_parameter, PracticeMode.IMP_PITCH)
            utility_timing = gaussian_process.get_estimate(error_pre, task_parameter, PracticeMode.IMP_TIMING)
            utility_slower = gaussian_process.get_estimate(error_pre, task_parameter, PracticeMode.SLOWER)

            plot_data_pitch.append([error_pitch, error_timing, utility_pitch[0]])
            plot_data_timing.append([error_pitch, error_timing, utility_timing[0]])
            plot_data_slower.append([error_pitch, error_timing, utility_slower[0]])

    plot_data_pitch = np.array(plot_data_pitch)
    plot_data_timing = np.array(plot_data_timing)
    plot_data_slower = np.array(plot_data_slower)

    fig = plt.figure(figsize=(10, 7))
    ax = plt.axes(projection="3d")
    cmap = plt.cm.viridis

    ax.scatter(plot_data_pitch[:, 0], plot_data_pitch[:, 1], plot_data_pitch[:, 2], color=cmap(0.))
    ax.scatter(plot_data_timing[:, 0], plot_data_timing[:, 1], plot_data_timing[:, 2], color=cmap(0.5))
    ax.scatter(plot_data_slower[:, 0], plot_data_slower[:, 1], plot_data_slower[:, 2], color=cmap(1.))

    ax.set_title("Utility: Gaussian Process for all Practice Modes")
    ax.set_xlabel('error_pitch')
    ax.set_ylabel('error_timing')
    ax.set_zlabel('utility')

    custom_lines = [Patch(facecolor=cmap(0.)),
                    Patch(facecolor=cmap(0.5)),
                    Patch(facecolor=cmap(1.))]
    plt.legend(custom_lines, ["IMP_PITCH", "IMP_TIMING", "SLOWER"])

    plt.show()


def gp_sim(iterations=100, performer="balanced"):
    """
        Trains a gaussian process with simulated data
        @param iterations: amount of data-points created for the GP
        @param performer: balanced, bad_timing, bad_pitch or all (all = randomly chosen each iteration)
    """
    tp = TaskParameters(bpm=120)
    GP = GaussianProcess()

    if performer != "all":
        p = performer

    # create data-points for Gaussian Process
    for i in tqdm(range(iterations), desc="Simulating Data Points: "):
        if performer == "all":
            p = random.choice(performers)

        # update model every 3 iterations
        if i < 200:
            if i % 3 == 0:
                GP.update_model()
        else:
            if i % 20 == 0:
                GP.update_model()

        # bpm = random.randint(BPM_BOUNDS[0], BPM_BOUNDS[1])
        # tp = TaskParameters(bpm=bpm)

        # calculate error_pre depending on the performer
        error_pre = simulate_error_tuple(tp, p)

        # let the gp choose the best practice mode (epsilon-greedy)
        given_practice_mode = GP.get_best_practice_mode(error_pre, tp)

        # calculate error_post depending on chosen practice mode
        error_post = perf_after_practice(error_pre, given_practice_mode)

        # calculate utility from error_pre and error_post
        utility = error_diff_to_utility(error_pre, error_post)

        utility *= np.random.normal(1, 0.05)

        # add data-point to GP
        GP.add_data_point(error_pre, tp, given_practice_mode, utility)

    training_points = {
        0: [],  # pitch
        1: [],  # timing
        2: []  # slower
    }

    for i, point in enumerate(GP.data_X):
        training_points[point[0]].append([point[2], point[3], GP.data_Y[i][0]])

    for i in range(3):
        training_points[i] = np.array(training_points[i])

    # plot utility for the different Practice Modes for altering pitch and timing error
    plot_utility(utility_function=utility_gp(GP, tp, practice_mode=PracticeMode.IMP_PITCH),
                 title="Utility: Gaussian Process for IMP_PITCH", density=30, data_points=training_points[0])
    plot_utility(utility_function=utility_gp(GP, tp, practice_mode=PracticeMode.IMP_TIMING),
                 title="Utility: Gaussian Process for IMP_TIMING", density=30, data_points=training_points[1])
    plot_utility(utility_function=utility_gp(GP, tp, practice_mode=PracticeMode.SLOWER),
                 title="Utility: Gaussian Process for SLOWER", density=30, data_points=training_points[2])

    plot_utility_all(GP, tp, density=50)

    density = 100
    best_mode = np.zeros((density, density))
    for i, error_pitch in enumerate(np.linspace(0, 1, density)):
        for j, error_timing in enumerate(np.linspace(0, 1, density)):
            best_pm = GP.get_best_practice_mode(Error(pitch=error_pitch, timing=error_timing), tp, epsilon=0)
            if best_pm == PracticeMode.IMP_PITCH:
                best_mode[i][j] = 0
            elif best_pm == PracticeMode.IMP_TIMING:
                best_mode[i][j] = 1
            else:
                best_mode[i][j] = 2

    plt.pcolormesh(np.linspace(0, 1, density), np.linspace(0, 1, density), best_mode)
    plt.title("GP's Estimate for best Practice Mode")
    plt.ylabel("error_pitch")
    plt.xlabel("error_timing")

    cmap = plt.cm.viridis
    custom_lines = [Patch(facecolor=cmap(0.)),
                    Patch(facecolor=cmap(0.5)),
                    Patch(facecolor=cmap(1.))]
    plt.legend(custom_lines, ["IMP_PITCH", "IMP_TIMING", "SLOWER"])
    plt.show()


if __name__ == '__main__':
    # plot_simulation()

    # plot_utility(utility_function=utility_practice_mode(PracticeMode.IMP_PITCH), title="IMP_PITCH Utility")
    # plot_utility(utility_function=utility_practice_mode(PracticeMode.IMP_TIMING), title="IMP_TIMING Utility")

    # plot_utility(utility_function=utility_max, title="Max Utility")

    gp_sim(iterations=300, performer="all")
    pass
