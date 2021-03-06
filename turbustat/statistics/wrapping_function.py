
'''
Wrapper to run all of the statistics between two data sets.
For large-scale comparisons, this is the function that should be called.
'''

from turbustat.statistics import Wavelet_Distance, \
    MVC_distance, \
    PSpec_Distance, \
    BiSpectrum_Distance, \
    GenusDistance, \
    DeltaVariance_Distance, \
    VCA_Distance, \
    VCS_Distance, \
    Tsallis_Distance, \
    StatMomentsDistance, \
    PCA_Distance, \
    SCF_Distance, \
    Cramer_Distance, \
    DendroDistance, \
    PDF_Distance


def stats_wrapper(dataset1, dataset2, fiducial_models=None,
                  statistics=None, multicore=False, vca_break=None,
                  vcs_break=None, cleanup=True):
    '''
    Function to run all of the statistics on two datasets.
    Each statistic is run with set inputs. This function needs to be altered
    to change the inputs.

    Parameters
    ----------
    dataset1 : dict
        Contains the cube and all of its property arrays.
    dataset2 : dict
        See dataset1
    fiducial_models : dict, optional
        Models for dataset1. Avoids recomputing when comparing
        many sets to dataset1.
    statistics : list, optional
        List of all of the statistics to use. If None, all are run.
    multicore : bool, optional
        If the wrapper is being used in parallel, this disables
        returning model values for dataset1.
    cleanup : bool, optional
        Delete distance classes after running.
    '''

    if statistics is None:  # Run them all
        statistics = ["Wavelet", "MVC", "PSpec", "Bispectrum", "DeltaVariance",
                      "Genus", "VCS", "VCA", "VCS_Density", "VCS_Velocity",
                      "VCS_Break",
                      "Tsallis", "PCA", "SCF", "Cramer", "Skewness",
                      "Kurtosis", "SCF", "PCA", "Dendrogram_Hist",
                      "Dendrogram_Num", "PDF_Hellinger", "PDF_KS"]

    distances = {}

    # Calculate the fiducial case and return it for later use
    if fiducial_models is None:

        fiducial_models = {}

        if any("Wavelet" in s for s in statistics):
            wavelet_distance = \
                Wavelet_Distance(dataset1["integrated_intensity"],
                                 dataset2["integrated_intensity"]).distance_metric()
            distances["Wavelet"] = wavelet_distance.distance
            if not multicore:
                fiducial_models["Wavelet"] = wavelet_distance.wt1

            if cleanup:
                del wavelet_distance

        if any("MVC" in s for s in statistics):
            mvc_distance = MVC_distance(dataset1, dataset2).distance_metric()
            distances["MVC"] = mvc_distance.distance
            if not multicore:
                fiducial_models["MVC"] = mvc_distance.mvc1

            if cleanup:
                del mvc_distance

        if any("PSpec" in s for s in statistics):
            pspec_distance = \
              PSpec_Distance(dataset1["integrated_intensity"],
                             dataset2["integrated_intensity"],
                             weights1=dataset1["integrated_intensity_error"][0]**2.,
                             weights2=dataset2["integrated_intensity_error"][0]**2.).distance_metric()
            distances["PSpec"] = pspec_distance.distance
            if not multicore:
                fiducial_models["PSpec"] = pspec_distance.pspec1

            if cleanup:
                del pspec_distance

        if any("Bispectrum" in s for s in statistics):
            bispec_distance = \
                BiSpectrum_Distance(dataset1["integrated_intensity"],
                                    dataset2["integrated_intensity"]).distance_metric()
            distances["Bispectrum"] = bispec_distance.distance
            if not multicore:
                fiducial_models["Bispectrum"] = bispec_distance.bispec1

            if cleanup:
                del bispec_distance

        if any("DeltaVariance" in s for s in statistics):
            delvar_distance = \
              DeltaVariance_Distance(dataset1["integrated_intensity"],
                                     dataset2["integrated_intensity"],
                                     weights1=dataset1["integrated_intensity_error"][0],
                                     weights2=dataset2["integrated_intensity_error"][0]).distance_metric()
            distances["DeltaVariance"] = delvar_distance.distance
            if not multicore:
                fiducial_models["DeltaVariance"] = delvar_distance.delvar1

            if cleanup:
                del delvar_distance

        if any("Genus" in s for s in statistics):
            genus_distance = \
                GenusDistance(dataset1["integrated_intensity"][0],
                              dataset2["integrated_intensity"][0]).distance_metric()
            distances["Genus"] = genus_distance.distance
            if not multicore:
                fiducial_models["Genus"] = genus_distance.genus1

            if cleanup:
                del genus_distance

        if any("VCS" in s for s in statistics):
            vcs_distance = VCS_Distance(dataset1["cube"],
                                        dataset2["cube"],
                                        breaks=vcs_break).distance_metric()
            distances["VCS"] = vcs_distance.distance
            distances["VCS_Density"] = vcs_distance.density_distance
            distances["VCS_Velocity"] = vcs_distance.velocity_distance
            distances["VCS_Break"] = vcs_distance.break_distance
            if not multicore:
                fiducial_models["VCS"] = vcs_distance.vcs1


            if cleanup:
                del vcs_distance

        if any("VCA" in s for s in statistics):
            vca_distance = VCA_Distance(dataset1["cube"],
                                        dataset2["cube"],
                                        breaks=vca_break).distance_metric()
            distances["VCA"] = vca_distance.distance
            if not multicore:
                fiducial_models["VCA"] = vca_distance.vca1

            if cleanup:
                del vca_distance

        if any("Tsallis" in s for s in statistics):
            tsallis_distance = \
                Tsallis_Distance(dataset1["integrated_intensity"][0],
                                 dataset2["integrated_intensity"][0]).distance_metric()
            distances["Tsallis"] = tsallis_distance.distance
            if not multicore:
                fiducial_models["Tsallis"] = tsallis_distance.tsallis1

            if cleanup:
                del tsallis_distance

        if any("Skewness" in s for s in statistics) or\
           any("Kurtosis" in s for s in statistics):
            moment_distance = \
                StatMomentsDistance(dataset1["integrated_intensity"][0],
                                    dataset2["integrated_intensity"][0], 5).distance_metric()
            distances["Skewness"] = moment_distance.skewness_distance
            distances["Kurtosis"] = moment_distance.kurtosis_distance
            if not multicore:
                fiducial_models["stat_moments"] = moment_distance.moments1

            if cleanup:
                del moment_distance

        if any("PCA" in s for s in statistics):
            pca_distance = \
                PCA_Distance(dataset1["cube"][0],
                             dataset2["cube"][0]).distance_metric()
            distances["PCA"] = pca_distance.distance
            if not multicore:
                fiducial_models["PCA"] = pca_distance.pca1

            if cleanup:
                del pca_distance

        if any("SCF" in s for s in statistics):
            scf_distance = \
                SCF_Distance(dataset1["cube"][0],
                             dataset2["cube"][0]).distance_metric()
            distances["SCF"] = scf_distance.distance
            if not multicore:
                fiducial_models["SCF"] = scf_distance.scf1

            if cleanup:
                del scf_distance

        if any("Cramer" in s for s in statistics):
            cramer_distance = \
                Cramer_Distance(dataset1["cube"][0],
                                dataset2["cube"][0]).distance_metric()
            distances["Cramer"] = cramer_distance.distance

            if cleanup:
                del cramer_distance

        if any("Dendrogram_Hist" in s for s in statistics) or \
           any("Dendrogram_Num" in s for s in statistics):
            dendro_distance = DendroDistance(dataset1["cube"][0],
                                             dataset2["cube"][0])
            dendro_distance.distance_metric()

            distances["Dendrogram_Hist"] = dendro_distance.histogram_distance
            distances["Dendrogram_Num"] = dendro_distance.num_distance
            if not multicore:
                fiducial_models["Dendrogram"] = dendro_distance.dendro1

            if cleanup:
                del dendro_distance

        if any("PDF_Hellinger" in s for s in statistics) or \
           any("PDF_KS" in s for s in statistics) or \
           any("PDF_AD" in s for s in statistics):
            pdf_distance = \
                PDF_Distance(dataset1["integrated_intensity"][0],
                             dataset2["integrated_intensity"][0],
                             min_val1=0.05,
                             min_val2=0.05,
                             weights1=dataset1["integrated_intensity_error"][0] ** -2.,
                             weights2=dataset2["integrated_intensity_error"][0] ** -2.)

            pdf_distance.distance_metric()

            distances["PDF_Hellinger"] = pdf_distance.hellinger_distance
            distances["PDF_KS"] = pdf_distance.ks_distance
            distances["PDF_AD"] = pdf_distance.ad_distance
            if not multicore:
                    fiducial_models["PDF"] = pdf_distance.PDF1

            if cleanup:
                del pdf_distance

        if multicore:
            return distances
        else:
            return distances, fiducial_models

    else:

        if any("Wavelet" in s for s in statistics):
            wavelet_distance = \
                Wavelet_Distance(dataset1["integrated_intensity"],
                                 dataset2["integrated_intensity"],
                                 fiducial_model=fiducial_models["Wavelet"]).distance_metric()
            distances["Wavelet"] = wavelet_distance.distance

            if cleanup:
                del wavelet_distance

        if any("MVC" in s for s in statistics):
            mvc_distance = \
                MVC_distance(dataset1,
                             dataset2,
                             fiducial_model=fiducial_models["MVC"]).distance_metric()
            distances["MVC"] = mvc_distance.distance

            if cleanup:
                del mvc_distance

        if any("PSpec" in s for s in statistics):
            pspec_distance = \
              PSpec_Distance(dataset1["integrated_intensity"],
                           dataset2["integrated_intensity"],
                           weight1=dataset1["integrated_intensity_error"][0]**2.,
                           weight2=dataset2["integrated_intensity_error"][0]**2.,
                           fiducial_model=fiducial_models["PSpec"]).distance_metric()
            distances["PSpec"] = pspec_distance.distance

            if cleanup:
                del pspec_distance

        if any("Bispectrum" in s for s in statistics):
            bispec_distance = \
                BiSpectrum_Distance(dataset1["integrated_intensity"],
                                    dataset2["integrated_intensity"],
                                    fiducial_model=fiducial_models["Bispectrum"]).distance_metric()
            distances["Bispectrum"] = bispec_distance.distance

            if cleanup:
                del bispec_distance

        if any("DeltaVariance" in s for s in statistics):
            delvar_distance = \
                DeltaVariance_Distance(dataset1["integrated_intensity"],
                                     dataset2["integrated_intensity"],
                                     weights1=dataset1["integrated_intensity_error"][0],
                                     weights2=dataset2["integrated_intensity_error"][0],
                                     fiducial_model=fiducial_models["DeltaVariance"]).distance_metric()
            distances["DeltaVariance"] = delvar_distance.distance

            if cleanup:
                del delvar_distance

        if any("Genus" in s for s in statistics):
            genus_distance = \
                GenusDistance(dataset1["integrated_intensity"][0],
                              dataset2["integrated_intensity"][0],
                              fiducial_model=fiducial_models["Genus"]).distance_metric()
            distances["Genus"] = genus_distance.distance

            if cleanup:
                del genus_distance

        if any("VCS" in s for s in statistics):
            vcs_distance = \
                VCS_Distance(dataset1["cube"],
                             dataset2["cube"],
                             fiducial_model=fiducial_models["VCS"],
                             breaks=vcs_break).distance_metric()
            distances["VCS_Density"] = vcs_distance.density_distance
            distances["VCS_Velocity"] = vcs_distance.velocity_distance
            distances["VCS_Break"] = vcs_distance.break_distance
            distances["VCS"] = vcs_distance.distance

            if cleanup:
                del vcs_distance

        if any("VCA" in s for s in statistics):
            vca_distance = \
                VCA_Distance(dataset1["cube"],
                             dataset2["cube"],
                             fiducial_model=fiducial_models["VCA"],
                             breaks=vca_break).distance_metric()
            distances["VCA"] = vca_distance.distance

            if cleanup:
                del vca_distance

        if any("Tsallis" in s for s in statistics):
            tsallis_distance= \
                Tsallis_Distance(dataset1["integrated_intensity"][0],
                                 dataset2["integrated_intensity"][0],
                                 fiducial_model=fiducial_models["Tsallis"]).distance_metric()
            distances["Tsallis"] = tsallis_distance.distance

            if cleanup:
                del tsallis_distance

        if any("Skewness" in s for s in statistics) or any("Kurtosis" in s for s in statistics):
            moment_distance = \
                StatMomentsDistance(dataset1["integrated_intensity"][0],
                                    dataset2["integrated_intensity"][0],
                                    5,
                                    fiducial_model=fiducial_models["stat_moments"]).distance_metric()
            distances["Skewness"] = moment_distance.skewness_distance
            distances["Kurtosis"] = moment_distance.kurtosis_distance

            if cleanup:
                del moment_distance

        if any("PCA" in s for s in statistics):
            pca_distance = \
                PCA_Distance(dataset1["cube"][0],
                             dataset2["cube"][0],
                             fiducial_model=fiducial_models["PCA"]).distance_metric()
            distances["PCA"] = pca_distance.distance

            if cleanup:
                del pca_distance

        if any("SCF" in s for s in statistics):
            scf_distance = \
                SCF_Distance(dataset1["cube"][0],
                             dataset2["cube"][0],
                             fiducial_model=fiducial_models["SCF"]).distance_metric()
            distances["SCF"] = scf_distance.distance

            if cleanup:
                del scf_distance

        if any("Cramer" in s for s in statistics):
            cramer_distance = \
                Cramer_Distance(dataset1["cube"][0],
                                dataset2["cube"][0]).distance_metric()
            distances["Cramer"] = cramer_distance.distance

            if cleanup:
                del cramer_distance

        if any("Dendrogram_Hist" in s for s in statistics) or \
           any("Dendrogram_Num" in s for s in statistics):
            dendro_distance = DendroDistance(dataset1["cube"][0],
                                             dataset2["cube"][0],
                                             fiducial_model=fiducial_models["Dendrogram"])
            dendro_distance.distance_metric()

            distances["Dendrogram_Hist"] = dendro_distance.histogram_distance
            distances["Dendrogram_Num"] = dendro_distance.num_distance

            if cleanup:
                del dendro_distance

        if any("PDF_Hellinger" in s for s in statistics) or \
           any("PDF_KS" in s for s in statistics) or \
           any("PDF_AD" in s for s in statistics):
            pdf_distance = \
                PDF_Distance(dataset1["integrated_intensity"][0],
                             dataset2["integrated_intensity"][0],
                             min_val1=0.05,
                             min_val2=0.05,
                             weights1=dataset1["integrated_intensity_error"][0] ** -2.,
                             weights2=dataset2["integrated_intensity_error"][0] ** -2.)

            pdf_distance.distance_metric()

            distances["PDF_Hellinger"] = pdf_distance.hellinger_distance
            distances["PDF_KS"] = pdf_distance.ks_distance
            distances["PDF_AD"] = pdf_distance.ad_distance

            if cleanup:
                del pdf_distance

        return distances
