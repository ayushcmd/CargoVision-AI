from ultralytics import YOLO
import cv2
import easyocr

# function to varify detected wagon number is 11 digit
def detectionVerification(s):
      if s.isdigit():
        if len(s) == 11:
            return True
      else:
        return False

# function to check the extracted wagon number
def verifyWN(s):
      # converting it to list
      wnList = []
      for n in s:
            wnList.append(int(n))
      
      # getting the check digit
      check_digit = wnList.pop()

      # calculationg S1
      s1 = 0
      for i in range(1, len(wnList), 2):
            s1 = s1 + wnList[i]

      s2 = 0
      for i in range(0, len(wnList), 2):
            s2 = s2 + wnList[i]

      s4 = 3*s1+s2

      # Calculate expected check digit (handles check digit 0 correctly)
      expected_check = (10 - (s4 % 10)) % 10
      return expected_check == check_digit

def performOCR(img):
    # perform OCR on the frame
    ocrResults = reader.readtext(img)
    return ocrResults


# function to draw fancy layout
def drawLayout(frame, string, wagonNo, greenORred):
    # Draw the filled (solid) rectangle on the image
    start_point = (25, 345)
    end_point = (200, 400)
    
    if greenORred:
        color = (0, 255, 0) # green
        cv2.rectangle(frame, start_point, end_point, color, -1)
        # put result text on image
        cv2.putText(frame, string, (30, 380), font, 1,  (0,0,0), 2, cv2.LINE_AA)
        ocrStatus = "Detecting Wagon Number"
        cv2.putText(frame, ocrStatus, (210, 380), font, .8, color, 1, cv2.LINE_AA)
        detectedText = "Wagon Number: "+wagonNo
        wagonNo = "-"
        # Draw the filled (solid) rectangle on the image for wagon number display
        start_point = (25, 410)
        end_point = (490, 470)
        cv2.rectangle(frame, start_point, end_point, (255,255,255), -1)
        cv2.putText(frame, detectedText, (40, 449), font, .9 ,(0,0,0), 1, cv2.LINE_AA)
    else:
        color = (0, 0, 255) # red
        # put result text on image
        start_point = (25, 345)
        end_point = (220, 400)
        cv2.rectangle(frame, start_point, end_point, color, -1)
        cv2.putText(frame, string, (30, 380), font, .9, (0, 0, 0) , 2, cv2.LINE_AA)
        ocrStatus = "Not Detecting Wagon Number"
        cv2.putText(frame, ocrStatus, (230, 380), font, .8, color , 1, cv2.LINE_AA)
    
    return frame


# function to draw fancy detection box
def drawBbox(img, pt1, pt2, color=(255,255,127), thickness=3, r=10, d=10):
    x1,y1 = pt1
    x2,y2 = pt2
    # Top left
    cv2.line(img, (x1 + r, y1), (x1 + r + d, y1), color, thickness)
    cv2.line(img, (x1, y1 + r), (x1, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
    # Top right
    cv2.line(img, (x2 - r, y1), (x2 - r - d, y1), color, thickness)
    cv2.line(img, (x2, y1 + r), (x2, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
    # Bottom left
    cv2.line(img, (x1 + r, y2), (x1 + r + d, y2), color, thickness)
    cv2.line(img, (x1, y2 - r), (x1, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)
    # Bottom right
    cv2.line(img, (x2 - r, y2), (x2 - r - d, y2), color, thickness)
    cv2.line(img, (x2, y2 - r), (x2, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)
    return img


# function to extract single line wagon number
def getSingleLineWagonNo(ocrResults, wagonNo):
    global savedWagonNumber
    freezCount = 0
    for result in ocrResults:
        # render results on image
        text = result[1]
        if detectionVerification(text) and verifyWN(text):
            wagonNo = text
            if freezCount <= 1:
                  freezCount += 1
                  savedWagonNumber = wagonNo
    return savedWagonNumber

# function to extract multi line wagon number
def getMultiLineWagonNo(ocrResults, wagonNo):
    text = ""
    freezCount = 0
    global savedWagonNumber
    for result in ocrResults:
        # render results on image
        text = result[1]
        if len(text) == 5 or len(text) == 6:
            wagonNo = wagonNo + text

    if detectionVerification(wagonNo):
        if verifyWN(wagonNo):
            if freezCount <= 1:
                freezCount += 1
                savedWagonNumber = wagonNo
    return savedWagonNumber




# load the model
wadonNumberDetectionModel = YOLO("wnd/models/wagonNumberDetectionV2.pt")

# initilize the reader
reader = easyocr.Reader(['en'], gpu=False)


wagonNo = "-"
savedWagonNumber = ""
confidence = 0
countDetect = 0
singleLineDetection = 0
multiLineDetection = 0
font = cv2.FONT_HERSHEY_DUPLEX



def DetectWagonNumber(frame):
    """
    This function takes an image frame and returns the wagon number.
    Parameters:
        parameter1 (numpy.ndarray): An Image.

    Returns:
        String: If detected, 11 digit neumirical wagon number is returned else empty string is returned.
    """
    # Resize the image
    global wagonNo, countDetect, singleLineDetection, multiLineDetection
    new_height = 480
    new_width = int(frame.shape[1] * (new_height / frame.shape[0]))
    resized_frame = cv2.resize(frame, (new_width, new_height))

    

    # perform wagon no detection on the frame
    wagonNoDetectionResults = wadonNumberDetectionModel.predict(source=resized_frame, show=False, save=False, save_txt=False)
    # segemnt or crop the frame
    for result in wagonNoDetectionResults:
        # fetching detection results
        bboxes = []
        bboxes = result.boxes.xyxy
        clsid = []
        clsName = ""

        # check if there is any detction or not
        if result.boxes.cls.numel() == 0:
            print("no detection")
            wagonNo = ""
        if result.boxes.cls.numel() > 0:
            clsid = result.boxes.cls.tolist()
            clsName = wagonNoDetectionResults[0].names[clsid[0]]
            #check detected class
            for id in clsid:
                if id == 0:
                    countDetect +=1
                    singleLineDetection += 1
                else:
                        countDetect +=1
                        multiLineDetection += 1

        for bbox in bboxes:
            # print("Bounding box of detection: ", bbox)
                x1 = int(bbox[0])
                y1 = int(bbox[1])
                x2 = int(bbox[2])
                y2 = int(bbox[3])
            
                point1 = (x1, y1)
                point2 = (x2, y2)

                # crop and display the frame
                croppedFrame = resized_frame[point1[1]:point2[1],point1[0]:point2[0]]

                # draw detection box
                resized_frame = drawBbox(resized_frame, point1, point2, (0,255,0), 3)
                # print("Detected class", clsName)

                print(f"Total Detection: {countDetect}")
                print(f"Single Line wagon number: {singleLineDetection}")
                print(f"Multi Line wagon number: {multiLineDetection}")
                
                # perform OCR on the frame
                ocrResults = performOCR(croppedFrame)
                # print("OCR results: ", ocrResults)

                  # if clsName == "":

                wagonNo = ""
                if clsName == "Wagon_number_single_line":
                    wagonNo = getSingleLineWagonNo(ocrResults, wagonNo)
                else:
                    wagonNo = getMultiLineWagonNo(ocrResults, wagonNo)

    
        # draw layout with results on image
        resized_frame = drawLayout(resized_frame, "[ Wagon ]", wagonNo, greenORred = True)
    else:
        # draw red layout on the frame
        resized_frame = drawLayout(resized_frame, "[ Wagon ]", wagonNo, greenORred=False)

    return wagonNo , resized_frame