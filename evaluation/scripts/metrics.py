import numpy as np

def calculate_cer(reference: str, hypothesis: str) -> float:
    """
    Compute Character Error Rate (CER) via Levenshtein distance:
    CER = (Substitutions + Deletions + Insertions) / len(reference)
    """
    ref = ''.join(filter(str.isalnum, reference))
    hyp = ''.join(filter(str.isalnum, hypothesis))
    
    if len(ref) == 0:
        return 0.0 if len(hyp) == 0 else 1.0

    r_len, h_len = len(ref), len(hyp)
    dp = [[0] * (h_len + 1) for _ in range(r_len + 1)]

    for i in range(r_len + 1):
        dp[i][0] = i
    for j in range(h_len + 1):
        dp[0][j] = j

    for i in range(1, r_len + 1):
        for j in range(1, h_len + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost # substitution
            )

    distance = dp[r_len][h_len]
    return float(distance) / float(r_len)


def calculate_iou(box1, box2):
    """
    box: [x1, y1, x2, y2]
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def compute_detection_metrics(gt_boxes, pred_boxes, iou_thresh=0.5):
    """
    Compute TP, FP, FN, Precision, Recall, F1 for bounding box detection at iou_thresh.
    """
    matched_gt = set()
    tp = 0
    fp = 0

    for pb in pred_boxes:
        best_iou = 0.0
        best_gt_idx = -1
        for idx, gb in enumerate(gt_boxes):
            if idx in matched_gt:
                continue
            iou = calculate_iou(pb, gb)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = idx

        if best_iou >= iou_thresh:
            tp += 1
            matched_gt.add(best_gt_idx)
        else:
            fp += 1

    fn = len(gt_boxes) - len(matched_gt)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1': round(f1, 4)
    }
