import os
import glob
from collections import Counter

def audit_dataset(dataset_path):
    print(f"Auditing Dataset: {dataset_path}")
    
    class_counts = Counter()
    total_files = 0
    empty_files = 0
    
    label_dirs = [
        os.path.join(dataset_path, 'train', 'labels'),
        os.path.join(dataset_path, 'valid', 'labels'),
        os.path.join(dataset_path, 'test', 'labels')
    ]
    
    for label_dir in label_dirs:
        if not os.path.exists(label_dir):
            continue
            
        files = glob.glob(os.path.join(label_dir, "*.txt"))
        total_files += len(files)
        
        for fpath in files:
            with open(fpath, 'r') as f:
                lines = f.readlines()
                if not lines:
                    empty_files += 1
                for line in lines:
                    try:
                        c_id = int(line.split()[0])
                        class_counts[c_id] += 1
                    except:
                        pass

    print("-" * 30)
    print(f"Total Images: {total_files}")
    print(f"Empty Labels: {empty_files}")
    print("-" * 30)
    print("Class Distribution:")
    print(f"Class 0 (Wagon): {class_counts[0]}")
    print(f"Class 1 (Parts): {class_counts[1]}")
    print(f"Class 2 (Number): {class_counts[2]}")
    print("-" * 30)
    
    if class_counts[2] < 500:
        print("WARNING: Severe Class Imbalance for Wagon Numbers!")
        print("Recommendation: Oversample Class 2 or use a separate model.")

if __name__ == "__main__":
    # Assuming standard path based on previous turns
    # Update this path if the user's merged folder is different
    MERGED_PATH = "railway_hackathon_merged" 
    if os.path.exists(MERGED_PATH):
        audit_dataset(MERGED_PATH)
    else:
        print(f"Folder {MERGED_PATH} not found.")
