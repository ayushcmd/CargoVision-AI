from roboflow import Roboflow
from ultralytics import YOLO
import os
import shutil
import yaml
from glob import glob

def remap_and_copy(source_path, dest_path_images, dest_path_labels, target_class_id):
    """
    Copies images and maps all labels to a single target_class_id (0).
    """
    os.makedirs(dest_path_images, exist_ok=True)
    os.makedirs(dest_path_labels, exist_ok=True)

    source_images = glob(os.path.join(source_path, 'images', '*'))
    
    for img_path in source_images:
        basename = os.path.basename(img_path)
        name_root, ext = os.path.splitext(basename)
        
        src_label_file = os.path.join(source_path, 'labels', f"{name_root}.txt")
        if not os.path.exists(src_label_file):
            continue

        with open(src_label_file, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 5:
                # Force class to target_class_id (usually 0 for single-class model)
                new_line = f"{target_class_id} " + " ".join(parts[1:])
                new_lines.append(new_line)
        
        if new_lines:
            # Copy Image
            shutil.copy(img_path, os.path.join(dest_path_images, basename))
            # Write Label
            with open(os.path.join(dest_path_labels, f"{name_root}.txt"), 'w') as f:
                f.write('\n'.join(new_lines))

def main():
    api_key = "u0leKBS1HrAOJli1hvLI"
    
    # 3 Specialized Number Datasets
    # We map ALL of them to Class 0: "Number"
    dataset_config = [
        ("sedykh-marat-dxrw3", "wagon-numbers-detection", 1),
        ("student-ih3dc", "wagon-detection-qc7bh", 1),
        ("wagoncounting", "wagon-numbers-jafet", 1),
    ]

    rf = Roboflow(api_key=api_key)
    
    MERGED_DIR = "railway_numbers_only"
    if os.path.exists(MERGED_DIR): shutil.rmtree(MERGED_DIR)
    
    print("-" * 60)
    print("STEP 1: Downloading & Merging Number Datasets")
    print("-" * 60)

    for workspace, project_id, version in dataset_config:
        try:
            print(f"Processing {workspace}/{project_id} v{version}")
            project = rf.workspace(workspace).project(project_id)
            dataset = project.version(version).download("yolov8")
            
            location = dataset.location
            for split in ['train', 'valid', 'test']:
                src_split = os.path.join(location, split)
                if not os.path.exists(src_split): continue
                
                dest_img = os.path.join(MERGED_DIR, split, 'images')
                dest_lbl = os.path.join(MERGED_DIR, split, 'labels')
                
                # Map everything to Class 0
                remap_and_copy(src_split, dest_img, dest_lbl, 0)
                
        except Exception as e:
            print(f"Skipping {project_id}: {e}")

    # Create data.yaml
    yaml_content = {
        'train': os.path.abspath(os.path.join(MERGED_DIR, 'train', 'images')),
        'val': os.path.abspath(os.path.join(MERGED_DIR, 'valid', 'images')),
        'test': os.path.abspath(os.path.join(MERGED_DIR, 'test', 'images')),
        'nc': 1,
        'names': ['Wagon Number']
    }
    
    yaml_path = os.path.join(MERGED_DIR, 'data.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_content, f)

    print("-" * 60)
    print("STEP 2: Training Model B (Numbers Only)")
    print("-" * 60)

    model = YOLO('yolov8n.pt') 
    
    results = model.train(
        data=yaml_path,
        epochs=50,
        imgsz=640,
        batch=16,
        project='railway_hackathon_numbers',
        name='number_detector_v1',
        freeze=10,
        lr0=0.001,
        patience=10
    )
    print("Training Complete! Weights at: runs/railway_hackathon_numbers/number_detector_v1/weights/best.pt")

if __name__ == '__main__':
    main()
