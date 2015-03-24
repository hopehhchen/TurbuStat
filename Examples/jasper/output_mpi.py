# Licensed under an MIT open source license - see LICENSE


import numpy as np
import sys
import os
import copy
from datetime import datetime
from astropy.io.fits import getdata
from itertools import repeat

from spectral_cube import SpectralCube, LazyMask
from astropy.wcs import WCS

from turbustat.statistics import stats_wrapper
from turbustat.data_reduction import Mask_and_Moments

np.random.seed(248954785)


def timestep_wrapper(fiducial_timestep, testing_timestep, statistics,
                     add_noise, rms_noise):

    # Derive the property arrays assuming uniform noise (for sims)
    fiducial_dataset = load_and_reduce(fiducial_timestep, add_noise=add_noise,
                                       rms_noise=rms_noise)
    testing_dataset = load_and_reduce(testing_timestep, add_noise=add_noise,
                                      rms_noise=rms_noise)

    if add_noise:
        vca_break = 1.5
        vcs_break = -0.5
    else:
        vca_break = None
        vcs_break = -0.8

    distances = stats_wrapper(fiducial_dataset, testing_dataset,
                              statistics=statistics, multicore=True,
                              vca_break=vca_break, vcs_break=vcs_break)
    return distances


def single_input(a):
    return timestep_wrapper(*a)


def run_all(fiducial, simulation_runs, statistics, savename,
            pool=None, verbose=True,
            multi_timesteps=False, add_noise=False, rms_noise=0.001):
    '''
    Given a fiducial set and a series of sets to compare to, loop
    through and compare all sets and their time steps. Return an array of
    the distances.

    Parameters
    ----------
    verbose : bool, optional
        Prints out the time when completing a set.
    multi_timesteps : bool, optional
        If multiple timesteps are given for each simulation run, parallelize
        over the timesteps. If only one is given, parallelize over the
        simulation runs.
    '''

    if verbose:
        # print "Simulation runs to be analyzed: %s" % (simulation_runs)
        print "Started at "+str(datetime.now())

    if multi_timesteps:
        # Distances will be stored in an array of dimensions
        # # statistics x # sim runs x # timesteps
        distances_storage = np.zeros((len(statistics),
                                      len(simulation_runs),
                                      len(fiducial)))

        print distances_storage.shape

        for i, key in enumerate(simulation_runs.keys()):
            timesteps = simulation_runs[key]

            if verbose:
                print "On Simulation %s/%s" % (i+1, len(simulation_runs))
                print str(datetime.now())
            if pool is not None:

                distances = pool.map(single_input, zip(fiducial,
                                                       timesteps,
                                                       repeat(statistics),
                                                       repeat(add_noise),
                                                       repeat(rms_noise)))

                # If there aren't the maximum number of timesteps, pad the
                # output to match the max.
                if len(distances) < len(fiducial):
                    diff = len(fiducial) - len(distances)
                    for d in range(diff):
                        distances.append(dict.fromkeys(statistics, np.NaN))

                distances_storage[:, i, :] = \
                    sort_distances(statistics, distances).T

            else:
                for ii, timestep in enumerate(timesteps):
                    fiducial_dataset = load_and_reduce(fiducial[ii],
                                                       add_noise=add_noise,
                                                       rms_noise=rms_noise)
                    testing_dataset = load_and_reduce(timestep,
                                                      add_noise=add_noise,
                                                      rms_noise=rms_noise)
                    if i == 0:
                        distances, fiducial_models = \
                            stats_wrapper(fiducial_dataset, testing_dataset,
                                          statistics=statistics)
                        all_fiducial_models = fiducial_models
                    else:
                        distances = \
                            stats_wrapper(fiducial_dataset, testing_dataset,
                                          fiducial_models=all_fiducial_models,
                                          statistics=statistics)
                    distances = [distances]
                    distances_storage[:, i, ii:ii+1] = \
                        sort_distances(statistics, distances).T

    else:
        distances_storage = np.zeros((len(statistics),
                                      len(simulation_runs)))

        if pool is not None:
            # print zip(repeat(fiducial), simulation_runs.values(),
            #           repeat(statistics))
            # print blah
            distances = pool.map(single_input, zip(repeat(fiducial),
                                                   simulation_runs.values(),
                                                   repeat(statistics),
                                                   repeat(add_noise),
                                                   repeat(rms_noise)))

            distances_storage = sort_distances(statistics, distances).T

        else:
            # Load the fiducial in
            fiducial_dataset = load_and_reduce(fiducial, add_noise=add_noise,
                                               rms_noise=rms_noise)

            for i, key in enumerate(simulation_runs.keys()):
                testing_dataset = \
                    load_and_reduce(simulation_runs[key][comp_face],
                                    add_noise=add_noise,
                                    rms_noise=rms_noise)
                if i == 0:
                    distances, fiducial_models = \
                        stats_wrapper(fiducial_dataset, testing_dataset,
                                      statistics=statistics)
                    all_fiducial_models = fiducial_models
                else:
                    distances = \
                        stats_wrapper(fiducial_dataset, testing_dataset,
                                      fiducial_models=all_fiducial_models,
                                      statistics=statistics)
                distances = [distances]
                distances_storage[:, i:i+1] = \
                    sort_distances(statistics, distances).T

    return distances_storage


def sort_distances(statistics, distances):
    if len(statistics) > 1:
        distance_array = np.empty((len(distances), len(statistics)))
    elif len(statistics) == 1:
        distance_array = np.empty((len(distances), 1))

    for j, dist in enumerate(distances):
        distance_array[j, :] = [dist[stat] for stat in statistics]

    return distance_array


def files_sorter(folder, fiducial_labels=np.arange(0, 5, 1),
                 design_labels=np.arange(0, 32, 1), timesteps='last',
                 faces=[0, 1, 2], suffix="fits", append_prefix=False):
    '''
    If the entire simulation suite is in one directory, this function
    will spit out appropriate groupings.

    Parameters
    ----------
    folder : str
        Folder where data is.
    fiducial_labels : list or numpy.ndarray, optional
        List of the fiducial numbers.
    design_labels : list or numpy.ndarray, optional
        List of the design numbers.
    timesteps : 'last' or list or numpy.ndarray, optional
        List of timesteps to analyze. If 'last', the last timestep
        found for each simulation is used.
    faces : list
        Faces of the simulations to use.
    suffix : str, optional
        File suffix.
    '''

    # Get the files and remove any sub-directories.
    files = [f for f in os.listdir(folder) if not os.path.isdir(f) and
             f[-len(suffix):] == suffix]

    # Set up the dictionaries.
    fiducials = dict.fromkeys(faces)
    designs = dict.fromkeys(faces)
    timestep_labels = dict.fromkeys(faces)
    for face in faces:
        fiducials[face] = dict((lab, []) for lab in fiducial_labels)
        designs[face] = dict((lab, []) for lab in design_labels)
        timestep_labels[face] = dict((lab, []) for lab in design_labels)

    # Sort the files
    for f in files:
        if "Fiducial" in f:
            for lab in fiducial_labels:
                if not "Fiducial"+str(lab)+"_" in f:
                    continue
                for face in faces:
                    if "_0"+str(face)+"_" in f:
                        if append_prefix:
                            fiducials[face][lab].append(folder+f)
                        else:
                            fiducials[face][lab].append(f)

        elif "Design" in f:
            for lab in design_labels:
                if not "Design"+str(lab)+"_" in f:
                    continue
                for face in faces:
                    if "_0"+str(face)+"_" in f:
                        if append_prefix:
                            designs[face][lab].append(folder+f)
                        else:
                            designs[face][lab].append(f)

        else:
            print "Could not find a category for " + f

    # Sort and keep only the specified timesteps
    _timestep_sort(fiducials, timesteps)
    _timestep_sort(designs, timesteps, labels=timestep_labels)

    return fiducials, designs, timestep_labels


def _timestep_sort(d, timesteps, labels=None):
    '''
    Helper function for segmenting by timesteps.
    '''
    for lab in d.keys():
        for face in d[lab].keys():
            # Check for empty lists.
            if d[lab][face] == []:
                continue
            d[lab][face].sort()
            if timesteps == 'last':  # Grab the last one
                if labels is not None:
                    labels[lab][face].append(d[lab][face][-1][-16:-14])
                d[lab][face] = d[lab][face][-1]
            elif timesteps == 'max':  # Keep all available
                # Reverse the order so the comparisons are between the highest
                # time steps.
                d[lab][face] = d[lab][face][::-1]
            elif isinstance(timesteps, int):  # Slice out a certain section
                d[lab][face] = d[lab][face][:timesteps]
                if labels is None:
                    continue
                for val in d[lab][face]:
                    labels[lab][face].append(val[-16:-14])
            else:  # Make a copy and loop through the steps
                good_files = copy.copy(d[lab][face])
                for f in d[lab][face]:
                    match = ["_00"+str(step)+"_" in f for step in timesteps]
                    if not any(match):
                        good_files.remove(f)
                    if labels is not None:
                        labels[lab][face].append(f[-16:-14])
                d[lab][face] = good_files


def load_and_reduce(filename, add_noise=False, rms_noise=0.001,
                    nsig=3):
    '''
    Load the cube in and derive the property arrays.
    '''

    if add_noise:
        if rms_noise is None:
            raise TypeError("Must specify value of rms noise.")

        cube, hdr = getdata(filename, header=True)

        from scipy.stats import norm
        cube += norm.rvs(0.0, rms_noise, cube.shape)

        sc = SpectralCube(data=cube, wcs=WCS(hdr))

        mask = LazyMask(np.isfinite, sc)
        sc = sc.with_mask(mask)

    else:
        sc = filename

    reduc = Mask_and_Moments(sc, scale=rms_noise)
    reduc.make_mask(mask=reduc.cube > nsig * reduc.scale)
    reduc.make_moments()
    reduc.make_moment_errors()

    return reduc.to_dict()

if __name__ == "__main__":

    # Call as:
    # python output.py path/to/folder/ 0 0 1 max fiducial0 T T
    #  /lustre/home/ekoch/results/
    # The args correspond to: directory, fiducial number, face,
    # comparison face, time steps to use, output file prefix,
    # use multiple cores?, add_noise?, save_direc

    from MPI import MPIPool

    statistics = ["Wavelet", "MVC", "PSpec", "Bispectrum", "DeltaVariance",
                  "Genus", "VCS", "VCA", "Tsallis", "PCA", "SCF", "Cramer",
                  "Skewness", "Kurtosis", "VCS_Density", "VCS_Velocity",
                  "PDF", "Dendrogram_Hist", "Dendrogram_Num"]

    print "Statistics to run: %s" % (statistics)
    num_statistics = len(statistics)

    # Read in cmd line args

    # Read in all files in the given directory
    PREFIX = str(sys.argv[1])

    try:
        fiducial_num = int(sys.argv[2])
    except ValueError:
        fiducial_num = str(sys.argv[2])
    face = int(sys.argv[3])
    comp_face = int(sys.argv[4])
    try:
        timesteps = int(sys.argv[5])
    except ValueError:
        timesteps = str(sys.argv[5])
    save_name = str(sys.argv[6])
    MULTICORE = str(sys.argv[7])
    if MULTICORE == "T":
        MULTICORE = True
    else:
        MULTICORE = False
    add_noise = str(sys.argv[8])
    if add_noise == "T":
        add_noise = True
    else:
        add_noise = False
    output_direc = str(sys.argv[9])

    # Sigma for COMPLETE NGC1333 data using signal-id (normal dist)
    # Note that the mean is forced to 0
    rms_noise = 0.1277369117707014 / 2.  # in K

    # Set whether we have multiple timesteps for each set
    if timesteps is 'last':
        multi_timesteps = False
    else:
        multi_timesteps = True

    fiducials, designs, timesteps_labels = \
        files_sorter(PREFIX, timesteps=timesteps,
                     append_prefix=True)

    if MULTICORE:
        pool = MPIPool(loadbalance=True)

        if not pool.is_master():
            # Wait for instructions from the master process.
            pool.wait()
            sys.exit(0)
    else:
        pool = None

    if fiducial_num == "fid_comp":  # Run all the comparisons of fiducials

        print "Fiducials to compare %s" % (fiducials[face].keys())
        fiducial_index = []
        fiducial_col = []

        # number of comparisons b/w all fiducials
        num_comp = (len(fiducials[face])**2. - len(fiducials[face]))/2
        # Change dim 2 to match number of time steps
        distances_storage = np.zeros((num_statistics, num_comp, 10))
        posn = 0
        prev = 0
        # no need to loop over the last one
        for fid_num, i in zip(fiducials[face].keys()[:-1],
                              np.arange(len(fiducials[comp_face])-1, 0, -1)):
            posn += i
            comparisons = fiducials[comp_face].copy()

            for key in range(fid_num + 1):
                del comparisons[key]
            partial_distances = \
                run_all(fiducials[face][fid_num], comparisons,
                        statistics, save_name, pool=pool,
                        multi_timesteps=multi_timesteps, verbose=True,
                        add_noise=add_noise, rms_noise=rms_noise)
            distances_storage[:, prev:posn, :] = partial_distances
            prev += i

            fiducial_index.extend(fiducials[comp_face].keys()[fid_num+1:])

            fiducial_col.extend([posn-prev] * len(fiducials[comp_face].keys()[fid_num:]))

        # consistent naming with non-fiducial case
        simulation_runs = fiducial_index
        # face = comp_face
    else:  # Normal case of comparing to single fiducial

        distances_storage = \
            run_all(fiducials[face][fiducial_num],
                    designs[comp_face], statistics, save_name,
                    pool=pool,
                    multi_timesteps=multi_timesteps,
                    add_noise=add_noise, rms_noise=rms_noise)

        simulation_runs = designs[comp_face].keys()
        fiducial_index = [fiducial_num] * len(designs.keys())

    # If using timesteps 'max', some comparisons will remain zero
    # To distinguish a bit better, set the non-comparisons to zero
    distances_storage[np.where(distances_storage == 0)] = np.NaN

    filename = save_name +"_fiducial"+str(fiducial_num)+"_" + str(face) + "_" + str(comp_face) + \
        "_distance_results.h5"

    from pandas import DataFrame, HDFStore, concat, Series

    # Save data for each statistic in a dataframe.
    # Each dataframe is saved in a single hdf5 file

    store = HDFStore(output_direc+filename)

    for i in range(num_statistics):
        # If timesteps is 'max', there will be different number of labels
        # in this case, don't bother specifying column names.
        if 'max' not in timesteps:
            df = DataFrame(distances_storage[i, :, :], index=simulation_runs,
                           columns=timesteps_labels[0][face])
        else:
            df = DataFrame(distances_storage[i, :, :], index=simulation_runs)

        # if not "Fiducial" in df.columns:
        #    df["Fiducial"] = Series(fiducial_index, index=df.index)
        if statistics[i] in store:
            existing_df = store[statistics[i]]
            if len(existing_df.index) == len(df.index):
                store[statistics[i]] = df
            else:  # Append on
                for ind in df.index:
                    if ind in list(existing_df.index):
                        existing_df.ix[ind] = df.ix[ind]
                    else:
                        existing_df = concat([existing_df, df])
                    store[statistics[i]] = existing_df
        else:
            store[statistics[i]] = df

    store.close()

    if MULTICORE:
        pool.close()

    print "Done at " + str(datetime.now())
