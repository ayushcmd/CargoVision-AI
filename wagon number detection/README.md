# Train Wagon number Detection and Extraction System [YOLOv8 + EasyOCR]
## Project Description
<p align="left">
    ⚠️ This repository contains the code for the Train Wagon number Detection and Extraction System using EasyOCR and YOLOv8 algorithm by Ultralytics for object classification on custom data. The project provides code for procedural-oriented programming implementations in Python.
</p>
<p align="left">
    ⚠️ Trained Models and Data are not provided in this repo. 
</p>

<p align="center">
    <img src="img/WagonNumber.png" width=950>
</p>

# Wagon Numbering System of Railways
<p align="left">
    According to the railway system, The 11-digit wagon number holds great importance in identifying the wagon individually. 
</p>
<p align="left">
    ⚠️ This numbering system is specific to The Indian Railway system. It might not be the same for other countries.
</p>

* The first of pair digits signifies the type of wagon. [C1, C2]
* The second pair of digits represents the railway owning the wagon. [C3, C4]
* The third pair of digits represent the year of manufacture. e.g. if the third pair is 11 then it means it was manufactured in 2011. [C5, C6]
* The next set of four digits represents individual wagon numbers. [C7, C8, C9, C10]
* The last digit is a check digit to check and verify the other 10 digits just like a parity checking. [C11]

# Workflow
<p align="center">
    <img src="img/flowchart.png" width="500"/>
</p>

## Results
<p align="center">
    <img src="img/R1.png" width="600"/>
</p>
<p align="center">
    <img src="img/R2.png" width="600"/>
</p>
<p align="center">
    <img src="img/R3.png" width="600"/>
</p>
<p align="center">
    <img src="img/R4.png" width="600"/>
</p>
<p align="center">
    <img src="img/R5.png" width="600"/>
</p>
<p align="center">
    <img src="img/R6.png" width="600"/>
</p>


## Requirements
Requirements installation
```
pip install ultralytics
pip install easyocr
pip install opencv-python
pip install Pillow==9.5.0
```
or
```
pip install requirements.txt 
```

For more details check
* ultralytics YOLOv8 [Github repository](https://github.com/ultralytics/ultralytics) and the YOLOv8 python [documentation](https://docs.ultralytics.com/usage/python/#train)
* EasyOCR Github [repository](https://github.com/JaidedAI/EasyOCR)



## Source Code
Download and run the code for video inference 
* Video inference code: [detect.py](src/detect.py).

* Code to Verify The Detected Wagon Number: [verifyno.py](src/verifyno.py)

## How to Install and Run the project
```
git clone https://github.com/tfortamal/Wagon-Number-Detection.git
cd Wagon-Number-Detection/src
python3 detect.py
```

## Credits
### Author: **Tamal Das** August, 2023
