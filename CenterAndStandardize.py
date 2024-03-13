"""
Apply N4 bias correction and standardize MRI ranges.

Nathan Beaumont, 2023
"""
from pathlib import Path
import SimpleITK as sitk

def main():
    """Main."""
    input_path = Path(r"C:\Met Recurrence\DatasetMRIsFixed\MRIandContoursCoregistered")
    output_path = Path(r"C:\Met Recurrence\DatasetMRIsFixed\normalized_MRIs_N4usingOtsu")
    for brain_mri_path in input_path.glob("*/*contrastMRI.nrrd"):
        patient_name = brain_mri_path.parent.name
        if not (output_path / patient_name).exists():
            (output_path / patient_name).mkdir(parents=True)
        if (output_path / patient_name / brain_mri_path.name).exists():
            continue

        # Do N4 bias field correction
        inputImage = sitk.ReadImage(str(brain_mri_path), sitk.sitkFloat32)

        otsu_mask = sitk.OtsuThreshold(inputImage, 0, 1, 200)
        corrector = sitk.N4BiasFieldCorrectionImageFilter()
        corrected_image = corrector.Execute(inputImage, otsu_mask)

        timepoint = brain_mri_path.name.split("_")[0]
        brain_label_filename = timepoint + "_Brain_label.nrrd"
        brain_mask = sitk.ReadImage(str(brain_mri_path.parent / brain_label_filename), sitk.sitkUInt8)
        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(corrected_image, brain_mask)

        image_normalized = (corrected_image - stats.GetMean(1)) / stats.GetSigma(1)

        output_filepath = output_path / patient_name / brain_mri_path.name
        sitk.WriteImage(image_normalized, str(output_filepath))

if __name__ == '__main__':
    main()
