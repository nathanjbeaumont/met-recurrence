import pickle
from pathlib import Path
from radiomics import featureextractor
import numpy as np


def main():
    """Main."""
    binwidth = 0.015  # assume 95% of data will have a range about -2 to 2, divide this into 30 to 130 bins
    timepoint = "3month"
    contour_timepoint = "3month"
    mri_folder_path = Path(r"C:\Met Recurrence\DatasetMRIsFixed\normalized_MRIs_N4usingOtsu")
    contour_folder_path = Path(r"C:\Met Recurrence\DatasetMRIsFixed\ContourExpansions")
    expansion_str = "0perc"
    binwidth_str = str(binwidth).replace('.', 'p')
    output_path = Path(r"C:\Met Recurrence\RadiomicsMRIsFixed") / \
    f"binWidth{binwidth_str}N4viaOtsuNoResample{expansion_str}Expansion{timepoint}"

    settings = {}
    settings['binWidth'] = binwidth
    # settings['resampledPixelSpacing'] = [1, 1, 1]  # some images are 0.98x0.98x1
    # settings['resegmentRange'] = [-1.0]  # assume under -1 voxels are CSF

    extractor = featureextractor.RadiomicsFeatureExtractor(**settings)
    extractor.enableFeatureClassByName('shape', enabled=False)
    # extractor.enableImageTypeByName('Wavelet')

    contour_extractions_list = []
    mri_path_list = []
    contour_path_list = []
    features_kept = []
    labels = []
    for mri_path in sorted(mri_folder_path.rglob(f"{timepoint}_contrastMRI.nrrd")):
        print(f"Processing {mri_path}")
        contour_folder = contour_folder_path / mri_path.parent.name
        expansion_search_str = "_" + expansion_str if expansion_str else ""
        contour_paths = sorted(contour_folder.glob(f"{contour_timepoint}*{expansion_search_str}_label.nrrd"))
        contour_paths = [n for n in contour_paths if "brain" not in n.name.lower()]

        for contour_path in contour_paths:
            extractor_dict = extractor.execute(str(mri_path), str(contour_path))
            start_feature_idx = list(extractor_dict.keys()).index("original_firstorder_10Percentile")
            features_kept = list(extractor_dict.keys())[start_feature_idx:]
            values_kept = [extractor_dict[key] for key in features_kept]
            contour_extractions_list.append(values_kept)
            mri_path_list.append(str(mri_path))
            contour_path_list.append(str(contour_path))
            labels.append("gtv" in contour_path.name.lower())

    if not output_path.exists():
        output_path.mkdir()
    contour_extractions_mat = np.array(contour_extractions_list)
    np.save(output_path / f"{timepoint}_contour_extractions_mat.npy", contour_extractions_mat)

    labels_np = np.asarray(labels)
    np.save(output_path / f"{timepoint}_labels.npy", labels_np)

    with open(output_path / f"{timepoint}_mri_path_list.pkl", 'wb') as f:
        pickle.dump(mri_path_list, f)

    with open(output_path / f"{timepoint}_contour_path_list.pkl", 'wb') as f:
        pickle.dump(contour_path_list, f)

    with open(output_path / f"{timepoint}_feature_names.pkl", 'wb') as f:
        pickle.dump(features_kept, f)


if __name__ == '__main__':
    main()
