import cv2

def draw_stats(frame, stats_lines):
    """
    Draws a stats overlay on the frame.
    """
    # Draw background for stats
    cv2.rectangle(frame, (5, 5), (280, 15 + len(stats_lines)*30), (0, 0, 0), -1)
    
    for i, line in enumerate(stats_lines):
        color = (0, 255, 0)
        # Color coding logic
        if "Detection" in line and "ms" in line:
            try:
                 val = int(line.split(":")[1].replace("ms","").strip())
                 if val > 100: color = (0, 165, 255)
            except: pass
            
        if "OCR" in line and "ms" in line:
            try:
                 val = int(line.split(":")[1].replace("ms","").strip())
                 if val > 1000: color = (0, 0, 255)
            except: pass
        
        cv2.putText(frame, line, (15, 30 + i*30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

def draw_track(frame, box, track_id, info_text=None, color=(255, 0, 0)):
    x1, y1, x2, y2 = box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    
    label = f"ID {track_id}"
    
    # Primary Label
    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Info Block (e.g., Parsed Wagon Data)
    if info_text:
        # Split multiline info
        lines = info_text.split('\n')
        # specific y offset
        y_off = y1 - 35
        for l in reversed(lines):
            cv2.putText(frame, l, (x1, y_off), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            y_off -= 20
