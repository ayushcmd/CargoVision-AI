# Given number in string format
number_str = "21131123499"

def detectionVerification(s):
      if s.isdigit() and len(s) == 11 or len(s) == 6 or len(s) == 5:
        return True
      else:
        return False


def verifyWN(s):
      # converting it to list
      wnList = []
      for n in s:
            wnList.append(int(n))
      
      # getting the check digit
      check_digit = wnList.pop()
      # print("Check Digit: ", check_digit)
      # print("Wagon Numebr: ",wnList)

      # calculationg S1
      s1 = 0
      for i in range(1, len(wnList), 2):
            s1 = s1 + wnList[i]
      # print("S1: ",s1)
      s2 = 0
      for i in range(0, len(wnList), 2):
            s2 = s2 + wnList[i]
      # print("S2: ",s2)

      s4 = 3*s1+s2
      # print("S4: ",s4)

      # Calculate S10 (closest multiple of 10 greater than S4)
      s10 = ((s4 // 10) + 1) * 10
      # print("S10: ",s10)

      if s10-s4 == check_digit:
            return True
      else:
            return False


if detectionVerification(number_str):
     print("Wagon number verificaton: ", verifyWN(number_str))
else:
     print("Detection Verification: ", detectionVerification(number_str))


