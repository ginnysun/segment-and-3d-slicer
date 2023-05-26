import os
import slicer
import config


def loadFilesIntoSlicer(directory, patient, dicom):
    try:
        dicom_data_dir = os.path.join(directory, patient, dicom)
        master_volume_node = loadDICOMIntoSlicer(dicom_data_dir)
        seg_path = os.path.join(directory, patient, dicom + "_seg.nii")
        segmentation_node = loadSegmentationIntoSlicer(seg_path)
    except Exception as e:
        print(e)
        slicer.mrmlScene.RemoveNode(master_volume_node)
        slicer.mrmlScene.RemoveNode(segmentation_node)
        print("unable to load files into Slicer")
    else:
        print("loaded DICOM \'" + dicom +
              "\' and segmentation file \'" + dicom + "_seg.nii" +
              "\' for patient \'" + patient + "\' into scene")
        return master_volume_node, segmentation_node


# Load DICOM file into scene and return as Volume Node
def loadDICOMIntoSlicer(dicomDataDir):
    from DICOMLib import DICOMUtils
    loaded_node_ids = []  # this list will contain the list of all loaded node IDs
    with DICOMUtils.TemporaryDICOMDatabase() as db:
        DICOMUtils.importDicom(dicomDataDir, db)
        patient_uids = db.patients()
        for patient_uid in patient_uids:
            loaded_node_ids.extend(DICOMUtils.loadPatientByUID(patient_uid))
    masterVolumeNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLScalarVolumeNode')
    return masterVolumeNode


# Load segmentation file into scene and return Segmentation Node
def loadSegmentationIntoSlicer(segPath):
    segmentation_node = slicer.util.loadSegmentation(segPath)
    return segmentation_node


# Create temporary segment editor to get access to effects
def createSegmentEditor(master_volume_node, segmentation_node):
    segment_editor_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
    segment_editor_widget = slicer.qMRMLSegmentEditorWidget()
    segment_editor_widget.setMRMLScene(slicer.mrmlScene)
    segment_editor_widget.setMRMLSegmentEditorNode(segment_editor_node)
    segment_editor_widget.setSegmentationNode(segmentation_node)
    segment_editor_widget.setSourceVolumeNode(master_volume_node)
    print("successfully created Segment Editor node")
    return segment_editor_node, segment_editor_widget


# Create new segmentation node and add to scene
def createNewSegmentationNode():
    new_segmentation_node = slicer.vtkMRMLSegmentationNode()
    # Add statSegmentationNode to scene
    slicer.mrmlScene.AddNode(new_segmentation_node)
    new_segmentation_node.CreateDefaultDisplayNodes()
    return new_segmentation_node


# Run thresholding and return new segments in a separate segmentationNode
def createSegmentsByThresholding(source_segments, segments_from_hfu, additional_segments, master_volume_node, segmentation_node):
    segment_editor_node, segment_editor_widget = createSegmentEditor(master_volume_node, segmentation_node)
    # create an empty segmentation node to place newly created segments,
    # segments placed in the node will be used for data analysis
    new_segmentation_node = createNewSegmentationNode()
    for name, seg in source_segments:
        src_name, src_id = name, segmentation_node.GetSegmentation().GetSegmentIdBySegmentName(seg)
        # add source segment to the new segmentation node
        new_segmentation_node.GetSegmentation().AddSegment(segmentation_node.GetSegmentation().GetSegment(src_id))
        for segmentName, thresholdMin, thresholdMax in segments_from_hfu:
            # Create New Segment
            new_segment = segmentation_node.GetSegmentation().AddEmptySegment(src_name + "_" + segmentName)
            print("created segment \'" + src_name + "_" + segmentName + "\'")
            segment_editor_node.SetSelectedSegmentID(new_segment)
            # Set overwrite mode: 0/1/2 -> overwrite all/visible/none
            segment_editor_node.SetOverwriteMode(2)  # i.e. "allow overlap" in UI
            # Set editable area to be inside segment of interest
            segment_editor_node.SetMaskSegmentID(src_id)
            segment_editor_node.SetMaskMode(segmentation_node.EditAllowedInsideSingleSegment)

            # Thresholding
            segment_editor_widget.setActiveEffectByName("Threshold")
            effect = segment_editor_widget.activeEffect()
            effect.setParameter("MinimumThreshold", str(thresholdMin))
            effect.setParameter("MaximumThreshold", str(thresholdMax))
            effect.self().onApply()
            print("applied thresholding to \'" + src_name + "_" + segmentName + "\'")
            # Add a copy of the newly created segment to new_segmentation_node
            new_segmentation_node.GetSegmentation().AddSegment(segmentation_node.GetSegmentation().GetSegment(new_segment))
    # add any additional segments that would like to be analyzed
    for seg in additional_segments:
        add_seg = segmentation_node.GetSegmentation().GetSegmentIdBySegmentName(seg)
        new_segmentation_node.GetSegmentation().AddSegment(segmentation_node.GetSegmentation().GetSegment(add_seg))
    # close segment editor
    segment_editor_widget = None
    slicer.mrmlScene.RemoveNode(segment_editor_node)
    return new_segmentation_node


def computeResults(output_directory, filename, master_volume_node, thresholded_segments):
    import SegmentStatistics
    seg_stat_logic = SegmentStatistics.SegmentStatisticsLogic()
    seg_stat_logic.getParameterNode().SetParameter("Segmentation", thresholded_segments.GetID())
    seg_stat_logic.getParameterNode().SetParameter("ScalarVolume", master_volume_node.GetID())
    seg_stat_logic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.enabled", "True")
    seg_stat_logic.getParameterNode().SetParameter("ScalarVolumeSegmentStatisticsPlugin.voxel_count.enabled", "True")
    seg_stat_logic.getParameterNode().SetParameter("ScalarVolumeSegmentStatisticsPlugin.volume_mm3.enabled", "True")
    seg_stat_logic.computeStatistics()
    seg_stat_logic.exportToCSVFile(os.path.join(output_directory, filename))
    print("stored results to \'" + os.path.join(output_directory, filename) + "\'")


if __name__ == '__main__':
    # path to main directory
    mainDirectory = config.mainDirectory
    # path to directory to store results
    outputDirectory = config.outputDirectory
    seriesList = config.seriesList
    print(seriesList)
    for item in seriesList:
        skipped = []
        patientID = item['patient']
        print(patientID)
        for dicom in item['series']:
            try:
                masterVolumeNode, segmentationNode = loadFilesIntoSlicer(mainDirectory, patientID, dicom)
            except Exception as e:
                print(f"skipping {dicom} due to {e}")
                skipped.append((patientID, dicom))
                continue
            # Specify source segments as list items [source_name, source_id]
            sourceSegments = [
                ["esml", 'Segment_100'],
                ["esmr", 'Segment_101'],
                ["pml", 'Segment_102'],
                ["pmr", 'Segment_103']]
            # Specify threshold values and names used to create new segments as list items
            # [segment_name, threshold_min, threshold_max]
            segmentsFromHounsfieldUnits = [
                ["fat", -150, -30],
                ["fattymuscle", -29, 29],
                ["leanmuscle", 30, 150]]
            # Specify additional segments to be analyzed
            additionalSegments = ['Segment_92', 'Segment_35']
            thresholdedSegments = createSegmentsByThresholding(sourceSegments, segmentsFromHounsfieldUnits,
                                                               additionalSegments,
                                                               masterVolumeNode, segmentationNode)
            # run statistics and write to csv file
            computeResults(outputDirectory, patientID + dicom + ".csv", masterVolumeNode, thresholdedSegments)
            # Clear the Scene
            # slicer.mrmlScene.Clear(0)
            slicer.mrmlScene.RemoveNode(masterVolumeNode)
            slicer.mrmlScene.RemoveNode(segmentationNode)
            slicer.mrmlScene.RemoveNode(thresholdedSegments)
    print(f"skipped directories: {skipped}")
    print("stored all results to \'" + outputDirectory + "\'")
    exit()