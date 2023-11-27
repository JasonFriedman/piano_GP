#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy
import random
import functools
from deap import base, creator, tools, algorithms



# IND_SIZE=3

def get_eval_function(target_notes, actual_notes):
    # TODO find good value for time_error_window or different workaround.
    # high values are needed for finding the correct missing notes if notes are similar

    # TODO there might be cases where a mapping is very good, e.g.
    # [0, 1, 3, 4, 5, 6, 2] where 2 should be a -1, otherwise correct
    # all notes would have good fitness, except the last one which has a very
    # high timing error. maybe it still should be kept in hopes of a good mutation
    # maybe i'm thinking too much about 'perfect' data and it's not as relevant in real data
    def eval_function(mapping, time_error_window=2.5, verbose=False):
        actual_notes_unused = set(range(len(actual_notes)))

        error_timing = 0
        timing_already_added = set()
        error_note_hold_time = 0
        error_pitch = 0
        total_time_note_on = 0

        for target_i in range(len(target_notes)):
            target_note = target_notes[target_i]
            total_time_note_on += target_note.note_off_time - target_note.note_on_time

            if mapping[target_i] != -1:
                # print(mapping)
                actual_note = actual_notes[mapping[target_i]]
                actual_notes_unused.remove(mapping[target_i])
            else:
                continue

            ## pitch error

            if target_note.pitch != actual_note.pitch:
                error_pitch += 1 * (target_note.note_off_time - target_note.note_on_time)

            ## timing error

            ## check which notes preceed the current note / are played at same time
            t_on = target_note.note_on_time
            relevant_distances = [(idx, t_on - t_x.note_on_time)
                                  for idx, t_x in enumerate(target_notes)]

            relevant_distances = filter(lambda t: t[1] >= 0, relevant_distances)
            # relevant_distances = filter(lambda t: t[1] <= time_error_window, relevant_distances)
            relevant_distances = list(relevant_distances)

            ## This while loop makes sure that we remove all distances greater
            ## than the time_error_window, but we at least have one non-zero distance in it
            ## if such distance exists (e.g. not for first notes)
            while True:
                if len([time_diff for t_i, time_diff in relevant_distances
                        if time_diff > 0]) <= 1:
                    break
                if relevant_distances[0][1] <= time_error_window:
                    break
                relevant_distances.pop(0)

            for t_i, time_diff in relevant_distances:
                # if (target_i, t_i) in timing_already_added:
                #     continue
                # timing_already_added.update([(target_i, t_i), (t_i, target_i)])

                if mapping[t_i] == -1:
                    continue

                actual_time_diff = actual_note.note_on_time - actual_notes[
                    mapping[t_i]].note_on_time
                err = abs(time_diff - actual_time_diff)

                error_timing += err

            ## hold time error
            hold_time = lambda note: note.note_on_time - note.note_off_time

            error_note_hold_time += abs(
                hold_time(target_note) - hold_time(actual_note)
            )

        if verbose:
            print("UNUSED NOTES:", actual_notes_unused)
            print("notes played by the user", [actual_notes[i] for i in actual_notes_unused])
            print ("timing error ", error_timing)
        return (error_timing, error_note_hold_time, error_pitch,
                len(actual_notes_unused), mapping.count(-1))

    return eval_function


def mateSwapEntries(ind1, ind2, indpb):
    ## derived from deap's cxUniformPartialyMatched
    size = min(len(ind1), len(ind2))

    from collections import defaultdict
    p1, p2 = defaultdict(lambda: -1), defaultdict(lambda: -1)

    # Initialize the position of each indices in the individuals
    for i in range(size):
        p1[ind1[i]] = i
        p2[ind2[i]] = i

    for i in range(size):
        if random.random() < indpb:
            # Keep track of the selected values
            temp1 = ind1[i]
            temp2 = ind2[i]
            # Swap the matched value
            ind1[i] = temp2
            if temp2 != -1 and temp2 in ind1 and temp2 in p1.keys():
                ind1[p1[temp2]] = temp1

            ind2[i] = temp1
            if temp1 != -1 and temp1 in ind2 and temp1 in p2.keys():
                ind2[p2[temp1]] = temp2

            # Update the positions
            p1[temp1], p1[temp2] = p1[temp2], p1[temp1]
            p2[temp1], p2[temp2] = p2[temp2], p2[temp1]

    return ind1, ind2


## TODO maybe have a weighed choice when mutating based on the surroundings of
## the mutation, either just index based or with an additional function which
## has timing information. 
## -> it makes little sense to mutate the X in [0, 2, X, 3, ...] to 10 or higher
## we expect the mapping to be somewhat in ascending order

## TODO have some shift mutations

def mutReplace(n_actual_notes, ind, indpb=0.05):
    # print("mutReplace")
    for i in range(len(ind)):
        if random.random() < indpb:
            notes_possible = set(range(n_actual_notes))
            notes_possible = notes_possible.difference(ind)
            notes_possible.add(-1)

            ind[i] = random.choice(list(notes_possible))

    return ind,


def mutSwitch(ind, indpb=0.05):
    # print("mutSwitch")
    for i in range(len(ind) - 1):
        if random.random() < indpb:
            ind[i], ind[i + 1] = ind[i + 1], ind[i]

    return ind,


def mutLeftShiftOnMissing(ind, indpb=0.1):
    if not -1 in ind:
        return ind,

    if random.random() > indpb:
        return ind,

    index_to_remove = random.choice([i for i, v in enumerate(ind) if v == -1])
    ind.pop(index_to_remove)
    ind.append(-1)

    return ind,


def mutGeneral(n_actual_notes, ind, indpb):
    mutReplace_ = functools.partial(mutReplace, n_actual_notes)
    mut_functs_with_weight = [(1, mutReplace_),
                              (2, mutSwitch),
                              (1, mutLeftShiftOnMissing)]

    weights, pop = zip(*mut_functs_with_weight)
    # print(weights, pop)

    mut_func = random.choices(pop, k=1, weights=weights)[0]
    return mut_func(ind, indpb)


def initial_guess(n_target, n_actual):
    init = list(range(n_actual))
    while len(init) > n_target:
        r = random.randint(0, max(len(init) - 1, 0))
        init.pop(r)

    while len(init) < n_target:
        r = random.randint(0, max(len(init) - 1, 0))
        init.insert(r, -1)

    return init

def my_min(weights, list_of_x):
    times_weights = lambda array: sum(a * b for a, b in zip(array, weights))
    best_ones = sorted([m for m in list_of_x], key=lambda m: times_weights(m), reverse=True)

    best = best_ones[0]

    return times_weights(best), best


def my_max(weights, list_of_x):
    times_weights = lambda array: sum(a * b for a, b in zip(array, weights))
    best_ones = sorted([m for m in list_of_x], key=lambda m: times_weights(m), reverse=False)

    best = best_ones[0]

    return times_weights(best), best


def find_best_mapping(target_notes, actual_notes, interactive=False):
    weights = (-0.5, -1.0, -1.0, -2.0, -2.5)
    if not hasattr(creator, "FitnessMin"):
        creator.create("FitnessMin", base.Fitness, weights=weights)
        creator.create("Individual", list, fitness=creator.FitnessMin)

    POP_SIZE = 100

    # IND_SIZE = len(target_notes)
    toolbox = base.Toolbox()
    # toolbox.register("indices", random.sample, range(len(actual_notes)), len(target_notes))
    # toolbox.register("indices", range, IND_SIZE)
    toolbox.register("indices", initial_guess, len(target_notes), len(actual_notes))
    # from error_calc.mappingLevenshtein import get_mapping as get_mapping_lv
    # lv_mapping = get_mapping_lv(target_notes, actual_notes)

    # toolbox.register("indices", lambda: lv_mapping)
    toolbox.register("individual", tools.initIterate, creator.Individual,
                     toolbox.indices)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # def evalOneMax(individual):
    #     return sum(individual[:3]),

    eval_function = get_eval_function(target_notes, actual_notes)

    toolbox.register("evaluate", eval_function)
    toolbox.register("mate", mateSwapEntries, indpb=0.05)
    toolbox.register("mutate", mutGeneral, len(actual_notes), indpb=0.175)
    # toolbox.register("select", tools.selBest)
    toolbox.register("select", tools.selTournament, tournsize=3)

    pop = toolbox.population(n=POP_SIZE)
    hof = tools.ParetoFront()
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    # stats.register("avg", numpy.mean, axis=0)
    # stats.register("std", numpy.std, axis=0)
    # stats.register("min", numpy.min, axis=0)
    stats.register("min", my_min, weights)
    stats.register("max", my_max, weights)
    # stats.register("max", numpy.max, axis=0)

    pop, log = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.5, ngen=10,
                                   stats=stats, halloffame=hof, verbose=True)

    times_weights = lambda array: sum(a * b for a, b in zip(array, weights))

    best_ones = sorted([m for m in hof], key=lambda m: times_weights(eval_function(m)),
                       reverse=True)

    import pprint
    pprint.pprint([(times_weights(eval_function(b)), b) for b in best_ones])
    # f = 

    # print(best_ones)
    best = best_ones[0]
    print("best", best)
    eval_function(best, verbose=True)

    if interactive:
        while True:
            try:
                suggestion = input("Enter your suggestion: ")
                suggestion = suggestion.replace("[", "").replace("]", "")
                suggestion = list(map(int, suggestion.split(",")))

                print(eval_function(suggestion, verbose=True))
                print("use ctrl-c to exit")
                print()
            except KeyboardInterrupt:
                break
            except:
                import traceback
                traceback.print_exc()

    return best


def get_mapping(task_data, actualNoteInfoList, interactive=False):
    mapping = find_best_mapping(task_data.all_notes(), actualNoteInfoList,
                                interactive=interactive)
    print ("played notes", task_data.all_notes())
    print ("actual notes", actualNoteInfoList)
    return mapping
