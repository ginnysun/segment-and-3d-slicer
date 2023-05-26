# Segment and 3D Slicer

These scripts allow you to automatically segment multiple CT images at once and then apply 3D Slicer to analyze 
segments of interest.

This code was written to specifically measure the fat, lean muscle, and fatty muscle content of the autochthon and 
iliopsoas muscles. Additionally, the sacrum and C7 vertebrae are included in the analysis to easily distinguish between
CT Chest and CT Abdomen & Pelvis images.

Code written by Ginny Sun and Julius Heemelaar.

* TotalSegmentator Documentation: https://github.com/wasserth/TotalSegmentator
* 3DSlicer Documentation: https://github.com/Slicer/Slicer

## Code Description
The scripts included in this repository are described in detail below:

### ```setUpAndConfigDicom.py```: 
1. Asks user to input the ```mainDirectory``` (where study directories are located) and the ```outputDirectory``` 
(where data generated by 3D Slicer can be saved)
2. Renames directories pulled by RPDR:
   1. Study directories are named ```{patient_id}_{study_date}```
   2. Series directories are named ```{modality}_{study_date}_{series_description}```
   3. All spaces from directory names are removed
3. Allows users to select which series to further segment and analyze, which is saved to ```seriesList```
4. Allows user to delete files that were not selected, if conserving space is a consideration
5. Creates a file called ```config.py``` that stores the user-specified ```mainDirectory```, ```outputDirectory```, and 
```seriesList```, which following scripts use to know which series to segment and analyze

### ```totalSegmentatorLoop.py```:
1. Loops through the series directories saved in ```config.py``` and generates segmentation files, saved as 
```{series_name}_seg.nii``` in the study directory
   1. Each seg.nii file contains data that specifies the 104 segments generated through ```totalSegmentator```

### ```slicerSegmentAnalysisWithMultipleSeries.py```
1. Loops through the series directories saved in ```config.py``` and loads them into 3D Slicer
2. For each series, 3D Slicer is tasked with creating new segments (```segmentsFromHounsfieldUnits```) created by 
thresholding segments of interest, listed under ```sourceSegments```
   1. Additional segments that are analyzed without thresholding are listed under ```additionalSegments```
3. Slicer runs segment statistics on ```sourceSegments```, ```additionalSegments```, and new segments created by 
```segmentsFromHounsfieldUnits``` and saves the output as ```.csv``` files in ```outputDirectory```

### ```mergeTables.py```
1. Loops through ```outputDirectory``` and creates a master CSV that combines all .csv files located into directory
2. Saves master CSV in local directory, NOT in ```outputDirectory```, as ```combinedData.csv```

## Installation
Save ```setUpAndConfigDicom.py```, ```slicerSegmentAnalysisWithMultipleSeries.py```, and ```totalSegmentatorLoop.py``` 
in the **same** directory

Install 3D Slicer: https://slicer.readthedocs.io/en/latest/user_guide/getting_started.html

Install dependencies:
* ```inquirer```: https://pypi.org/project/inquirer/
* ```pytorch```: https://pytorch.org/get-started/locally/
* ```totalsegmentator```: https://pypi.org/project/TotalSegmentator/

If you plan on using a Conda virtual environment, consider following these steps:
1. Install Anaconda: https://docs.anaconda.com/free/anaconda/install/index.html
2. Consider deactivating base environment, otherwise it will default to activating the base environment on startup and
may cause future confusion:
```commandline
conda config --set auto_activate_base False
```
3. Create virtual environment:
```commandline
conda create --name venv
source activate venv
```
4. Install dependencies by using the command ```conda install``` instead of ```pip install```:
   1. e.g., ```conda install -c conda-forge inquirer```
5. When finished, close your virtual environment:
```commandline
conda deactivate venv
```

## Run Code
### Run ```setUpAndConfigDicom.py```:
```commandline 
python3 setUpAndConfigDicom.py
```
Upon running, you will encounter the following prompts for user input and may enter the following:
1. Please enter path to directory where patient data is stored: ```full/path/to/mainDirectory```
2. Please entire path to directory to store 3DSlicer output: ```full/path/to/outputDirectory```
3. Which series(es) do you want to analyze from patient ```MRN```:
   1. Use the right arrow to select the series you would like to be analyzed
   2. Use the left arrow to unselect a series
   3. Use the up and down arrow to navigate between series
   4. Press ```Enter``` when you are done selecting series within the study
4. Remove unselected directories?: ```y```/```n```

### Run ```totalSegmentatorLoop.py```:
```commandline 
python3 totalSegmentatorLoop.py
```
NOTE: if segmenting a series results in an error, the series will be skipped. A log of skipped series will be 
outputted to the console upon completion.

### Run ```slicerSegmentAnalysisWithMultipleSeries.py```:

For MacOS:
 ```
 /Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script "/full/path/to/slicerSegmentAnalysisWithMultipleSeries.py" 
 ```

For Windows:
```commandline
Slicer.exe --python-script "/full/path/to/slicerSegmentAnalysisWithMultipleSeries.py" --no-splash --no-main-window
```

### Run ```mergeTables.py```
```commandline 
python3 mergeTables.py
```

## Customization
You may customize which segments to analyze within ```slicerSegmentAnalysisWithMultipleSeries.py``` by specifying 
```sourceSegments```, ```segmentsFromHounsfieldUnits```, and ```additionalSegments```:

   1. Specify source segments as list items ```[source_name, source_id]``` in ```sourceSegments```
   2. Specify threshold values and names used to create new segments as list items ```[segment_name, threshold_min, threshold_max]``` in ```segmentsFromHounsfieldUnits```
      1. New segments will be named ```{source_name}_{segment_name}```
   3. Additional segments that you would like to be analyzed without creating new segments through thresholding can be specified in the list ```additionalSegments```

## Troubleshooting
### Unable to run Slicer on Linux
If getting an error involving XCB, you may need to reinstall additional packages. Try running the following:
```commandline
sudo apt-get install libpulse-dev libnss3 libglu1-mesa
sudo apt-get install --reinstall libxcb-xinerama0
```
Additional information on Slicer installation on Linux: 
https://slicer.readthedocs.io/en/latest/user_guide/getting_started.html

### Program not running due to ```FileNotFoundError```
* Make sure ```config.py``` contains the correct path(s), patient MRNs, and DICOM series names
  * Use full path names for ```mainDirectory``` and ```outputDirectory```
* If ```slicerSegmentAnalysisWithMultipleSeries.py``` is not running, check if the correct DICOM series and segmentation
file is being loaded into slicer under the function ```loadFilesIntoSlicer```
### Helpful hints:
* If not running 3D Slicer on a virtual environment, it may be helpful to view Slicer user interface as it runs. To do
this, run the following command:
```commandline
Slicer --python-script "/full/path/to/slicerSegmentAnalysisWithMultipleSeries.py" 
```
* You MUST run ```setUpAndConfigDicom.py``` BEFORE running ```totalSegmentatorLoop.py``` and 
```slicerSegmentAnalysisWithMultipleSeries.py```
* Every time you run ```setUpAndConfigDicom.py```, ```config.py```
will be overwritten
