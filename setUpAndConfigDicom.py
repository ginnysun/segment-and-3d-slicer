# Ginny Sun, Julius Heemelaar
# 5/15/2023
import os
import shutil
import pydicom
import inquirer


def renameDicomFolder(directory):
    for study_folder in os.listdir(directory):
        study_path = os.path.join(directory, study_folder)
        if not os.path.isdir(study_path):
            continue

        patient_id = ''
        for series_folder in os.listdir(study_path):
            series_path = os.path.join(study_path, series_folder)
            if not os.path.isdir(series_path):
                continue

            # Load DICOM metadata
            dcm_files = os.listdir(series_path)
            if len(dcm_files) == 0:
                continue

            dcm_file_path = os.path.join(series_path, dcm_files[0])
            if os.path.isdir(dcm_file_path):
                continue
            dcm = pydicom.dcmread(dcm_file_path)

            # Check if the DICOM series has a valid series description
            if not hasattr(dcm, "SeriesDescription") or not dcm.SeriesDescription:
                continue

            # Get the new folder name based on DICOM header values
            study_date = dcm.StudyDate
            modality = dcm.Modality
            series_description = dcm.SeriesDescription
            new_series_folder = f"{modality}_{study_date}_{series_description}"

            # Rename the series folder
            new_series_path = os.path.join(study_path, new_series_folder)
            shutil.move(series_path, new_series_path)
            print(f"Renamed series folder '{series_folder}' to '{new_series_folder}'")

            if not patient_id:
                patient_id = dcm.PatientID

            # Rename the study folder
            new_study_folder = f"{patient_id}_{study_date}"
            new_study_path = os.path.join(directory, new_study_folder)
            shutil.move(study_path, new_study_path)
            print(f"Renamed study folder '{study_folder}' to '{new_study_folder}'")

    print("Done!")


def dicomReplaceSpaces(directory):
    # Loop through all study folders within the repo folder
    for study_folder_name in os.listdir(directory):
        study_folder_path = os.path.join(directory, study_folder_name)
        if os.path.isdir(study_folder_path):
            # Loop through all serie folders within the study folder
            for serie_folder_name in os.listdir(study_folder_path):
                serie_folder_path = os.path.join(study_folder_path, serie_folder_name)
                if os.path.isdir(serie_folder_path):
                    # Replace spaces and parentheses with underscores in the serie folder name
                    new_serie_folder_name = serie_folder_name.replace(" ", "_").replace("(", "").replace(")", "")
                    if new_serie_folder_name != serie_folder_name:
                        new_serie_folder_path = os.path.join(study_folder_path, new_serie_folder_name)
                        # Rename the serie folder
                        os.rename(serie_folder_path, new_serie_folder_path)
                        print(f"Renamed folder {serie_folder_path} to {new_serie_folder_path}")


def getPatientList(directory):
    return [patient for patient in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, patient))]


# Get list of DICOM Folders corresponding to patient
def getDICOMFolder(directory, patient):
    patient_path = os.path.join(directory, patient)
    return [x for x in os.listdir(patient_path)
            if os.path.isdir(os.path.join(patient_path, x))]


# removes directories listed in directory_list
def removeFolders(directory_list):
    for directory in directory_list:
        shutil.rmtree(directory)


if __name__ == '__main__':
    mainDirectory = input("Please enter path to directory where patient data is stored: ")
    # mainDirectory = "/Users/ginnysun/Desktop/nini/Research/Segmentation/testset"
    outputDirectory = input("Please entire path to directory to store 3DSlicer output: ")
    # outputDirectory = "/Users/ginnysun/Desktop/nini/Research/Segmentation/testset_results"
    if not os.path.isdir(mainDirectory) or not os.path.isdir(outputDirectory):
        raise Exception("Please check if directories were entered correctly")
    renameDicomFolder(mainDirectory)
    dicomReplaceSpaces(mainDirectory)
    patients = getPatientList(mainDirectory)
    seriesList = []
    notSelected = []
    for pt in patients:
        question = [
          inquirer.Checkbox('series',
                            message="Which series(es) do you want to analyze from patient " + pt + " (right arrow to select)",
                            choices=getDICOMFolder(mainDirectory, pt),
                            ),
        ]
        series = inquirer.prompt(question)
        series['patient'] = pt
        seriesList.append(series)
        # get list of series that weren't previously selected
        for dicom in getDICOMFolder(mainDirectory, pt):
            if dicom not in series['series']:
                notSelected.append(os.path.join(mainDirectory, pt, dicom))
    print(seriesList)
    removeNotSelected = input("Remove unselected directories? (y/n): ")
    # continues to prompt unless entered as y or n
    while removeNotSelected != "y" and removeNotSelected != "n":
        removeNotSelected = input("Remove unselected directories? (y/n): ")
    if removeNotSelected == "y":
        removeFolders(notSelected)
    with open("config.py", "w") as file:
        file.write("seriesList = " + str(seriesList) + "\n")
        file.write("mainDirectory = \"" + mainDirectory + "\"\n")
        file.write("outputDirectory = \"" + outputDirectory + "\"\n")