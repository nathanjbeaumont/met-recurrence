"""
Expand contours.

Nathan Beaumont, 2023
"""
from pathlib import Path
import os
import slicer
import vtk


def getSegmentIDs(seg_node):
    """Get segment IDs given a segmentation node."""
    segment_ids = vtk.vtkStringArray()
    seg_node.GetSegmentation().GetSegmentIDs(segment_ids)
    segment_ids = [segment_ids.GetValue(i) for i in range(segment_ids.GetNumberOfValues())]  # convert to python str list
    return segment_ids


def main():
    """Run main function."""
    input_folder = Path(r"C:\Met Recurrence\DatasetMRIsFixed\MRIandContoursCoregistered")
    output_folder = Path(r"C:\Met Recurrence\DatasetMRIsFixed\ContourExpansions")

    for patient_path in input_folder.iterdir():
        if patient_path.is_file():
            continue
        if not os.path.exists(output_folder / patient_path.name):
            os.makedirs(output_folder / patient_path.name)

        for timepoint in ["6month", "3month"]:
            brain_contour_path = patient_path / f"{timepoint}_Brain_label.nrrd"
            brain_labelmap = slicer.util.loadLabelVolume(str(brain_contour_path))

            # transfer brain labelmap to seg
            brain_seg = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
            brain_seg.SetName(brain_labelmap.GetName())
            slicer.vtkSlicerSegmentationsModuleLogic.ImportLabelmapToSegmentationNode(brain_labelmap, brain_seg)
            brain_seg.SetSegmentName(0, 'brain')

            for gtv_path in patient_path.glob(f"{timepoint}*label.nrrd"):
                if "brain" in gtv_path.name.lower():
                    continue
                print('expanding ' + str(gtv_path))
                slicer.app.processEvents()  # have to do this or screen doesn't update until script is done running

                # Load gtv
                gtv_labelmap = slicer.util.loadLabelVolume(str(gtv_path))

                # transfer gtv labelmap to segmentation
                seg_node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
                seg_node.SetName(gtv_labelmap.GetName())
                segment_editor_widget = slicer.modules.segmenteditor.widgetRepresentation().self().editor
                segment_editor_widget.setSourceVolumeNode(gtv_labelmap)  # have to set source volume before importing labelmap
                slicer.vtkSlicerSegmentationsModuleLogic.ImportLabelmapToSegmentationNode(gtv_labelmap, seg_node)

                # copy brain segment into gtv segmentation, have to do this for intersect operation
                brain_segment_id = brain_seg.GetSegmentation().GetNthSegmentID(0)
                seg_node.GetSegmentation().CopySegmentFromSegmentation(brain_seg.GetSegmentation(), brain_segment_id)
                brain_segment_id = seg_node.GetSegmentation().GetNthSegmentID(1)  # brain segment id might have been renamed after copy operation

                # Create contour expansions and save them as labelmaps
                print("Creating contour expansions")
                slicer.app.processEvents()  # have to do this or screen doesn't update until script is done running
                segment_editor_node = segment_editor_widget.mrmlSegmentEditorNode()
                segment_editor_node.SetOverwriteMode(2)  # Allow overlap

                logical_ops = segment_editor_widget.effectByName("Logical operators")
                margin_effect = segment_editor_widget.effectByName("Margin")
                segment_editor_node.SetAndObserveSegmentationNode(seg_node)
                gtv_segment_id = seg_node.GetSegmentation().GetNthSegmentID(0)
                for expansion_mm in [0]:
                    new_segment_id = f"{gtv_segment_id}_{expansion_mm}mm"
                    seg_node.GetSegmentation().AddEmptySegment(new_segment_id)
                    logical_ops.parameterSetNode().SetSelectedSegmentID(new_segment_id)
                    logical_ops.setParameter("Operation", "COPY")
                    logical_ops.setParameter("ModifierSegmentID", gtv_segment_id)
                    logical_ops.self().onApply()
                    margin_effect.setParameter("MarginSizeMm", expansion_mm)
                    margin_effect.self().onApply()
                    logical_ops.setParameter("Operation", "INTERSECT")
                    logical_ops.setParameter("ModifierSegmentID", brain_segment_id)
                    logical_ops.self().onApply()

                    # Create output labelmap volume
                    expansion_labelmap = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
                    expansion_labelmap_name = f"{gtv_labelmap.GetName().split('-label')[0]}_{expansion_mm}mm"
                    expansion_labelmap.SetName(expansion_labelmap_name)

                    single_segment_array = vtk.vtkStringArray()
                    single_segment_array.InsertNextValue(new_segment_id)
                    slicer.vtkSlicerSegmentationsModuleLogic.ExportSegmentsToLabelmapNode(seg_node, single_segment_array, expansion_labelmap, gtv_labelmap)

                    filename = gtv_path.name.split("_label")[0] + f"_{expansion_mm}mm_label.nrrd"

                    slicer.util.saveNode(expansion_labelmap, str(output_folder / patient_path.name / filename))
                    slicer.mrmlScene.RemoveNode(expansion_labelmap)
                slicer.mrmlScene.RemoveNode(seg_node)
                slicer.mrmlScene.RemoveNode(gtv_labelmap)
            slicer.mrmlScene.RemoveNode(brain_seg)
            slicer.mrmlScene.RemoveNode(brain_labelmap)
    print("Done")


if __name__ == "__main__":
    main()
