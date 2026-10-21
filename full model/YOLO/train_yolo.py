from roboflow import Roboflow
from ultralytics import YOLO
import os
import shutil
import yaml
from glob import glob

def remap_and_copy(source_path, dest_path_images, dest_path_labels, target_class_id, oversample_factor=1):
    """
    Copies images and creates remapped label files.
    Supports Oversampling: Copies files multiple times with unique names.
    """
    os.makedirs(dest_path_images, exist_ok=True)
    os.makedirs(dest_path_labels, exist_ok=True)

    # We look for images in the source
    source_images = glob(os.path.join(source_path, 'images', '*'))
    
    for img_path in source_images:
        basename = os.path.basename(img_path)
        name_root, ext = os.path.splitext(basename)
        
        # Check for Label existence first
        src_label_file = os.path.join(source_path, 'labels', f"{name_root}.txt")
        if not os.path.exists(src_label_file):
            continue

        # Prepare Label Content
        with open(src_label_file, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 5:
                # Replace original class_id with target_class_id
                new_line = f"{target_class_id} " + " ".join(parts[1:])
                new_lines.append(new_line)
        
        if not new_lines: continue
        
        # --- OVERSAMPLING LOOP ---
        for i in range(oversample_factor):
            # Unique suffix for duplicates
            suffix = f"_copy{i}" if i > 0 else ""
            new_name_root = f"{name_root}{suffix}"
            
            # Copy Image
            dest_img_path = os.path.join(dest_path_images, f"{new_name_root}{ext}")
            shutil.copy(img_path, dest_img_path)
            
            # Write Label
            dest_label_path = os.path.join(dest_path_labels, f"{new_name_root}.txt")
            with open(dest_label_path, 'w') as f:
                f.write('\n'.join(new_lines))

def main():
    api_key = "u0leKBS1HrAOJli1hvLI"
    
    if api_key == "YOUR_API_KEY":
        print("Please replace 'YOUR_API_KEY' within the script.")
        return

    # MAPPING CONFIGURATION
    # (Workspace, Project, Version, Target_Class_ID, Target_Class_Name, Oversample_Factor)
    dataset_config = [
        # GLOBAL CLASS 0: Wagon (Factor=1)
        ("aispry-ob85t", "wagon-detection-zsnyn", 2, 0, "Wagon", 1),
        ("alisha-nyb7f", "wagon-detection-qxlxh", 1, 0, "Wagon", 1),
        ("wagons-thdfd", "cv-alt", 2, 0, "Wagon", 1),
        
        # GLOBAL CLASS 1: Wagon parts (Factor=2)
        ("db-rail", "train-wagon-cv-project", 3, 1, "Wagon parts", 2),
        
        # GLOBAL CLASS 2: Wagon numbers (Factor=25)
        ("sedykh-marat-dxrw3", "wagon-numbers-detection", 1, 2, "Wagon numbers", 25),
        ("student-ih3dc", "wagon-detection-qc7bh", 1, 2, "Wagon numbers", 25),
        ("wagoncounting", "wagon-numbers-jafet", 1, 2, "Wagon numbers", 25),
    ]

    rf = Roboflow(api_key=api_key)
    
    # Create Merged Dataset Structure
    MERGED_DIR = "railway_hackathon_merged_oversampled"
    if os.path.exists(MERGED_DIR): shutil.rmtree(MERGED_DIR) 
    
    for split in ['train', 'valid', 'test']:
        os.makedirs(os.path.join(MERGED_DIR, split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(MERGED_DIR, split, 'labels'), exist_ok=True)

    print("-" * 60)
    print("STEP 1: Downloading & Merging Datasets (With Balancing)")
    print("-" * 60)

    for workspace, project_id, version, target_id, target_name, factor in dataset_config:
        try:
            print(f"Processing {workspace}/{project_id} v{version} -> Class {target_id} (x{factor})")
            project = rf.workspace(workspace).project(project_id)
            dataset = project.version(version).download("yolov8")
            
            location = dataset.location
            
            # Merge Train, Valid, Test splits
            for split in ['train', 'valid', 'test']:
                # Some datasets might use 'train' or 'valid' folders differently
                src_split_path = os.path.join(location, split)
                if not os.path.exists(src_split_path): 
                    continue
                    
                dest_images = os.path.join(MERGED_DIR, split, 'images')
                dest_labels = os.path.join(MERGED_DIR, split, 'labels')
                
                remap_and_copy(src_split_path, dest_images, dest_labels, target_id, factor)
                
        except Exception as e:
            print(f"Skipping {project_id}: {e}")

    # Create Custom data.yaml
    yaml_content = {
        'train': os.path.abspath(os.path.join(MERGED_DIR, 'train', 'images')),
        'val': os.path.abspath(os.path.join(MERGED_DIR, 'valid', 'images')),
        'test': os.path.abspath(os.path.join(MERGED_DIR, 'test', 'images')),
        'nc': 3,
        'names': ['Wagon', 'Wagon parts', 'Wagon numbers']
    }
    
    yaml_path = os.path.join(MERGED_DIR, 'data.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_content, f)

    print("-" * 60)
    print(f"Dataset Merged at: {MERGED_DIR}")
    print("STEP 2: Starting Training on Merged Dataset")
    print("-" * 60)

    # Train
    model = YOLO('yolov8n.pt') 
    
    try:
        results = model.train(
            data=yaml_path,
            epochs=50,
            imgsz=640,
            batch=4,
            project='railway_hackathon_take2',
            name='merged_model_v1',
            freeze=10,
            lr0=0.001,
            patience=10
        )
        print("Training Complete!")
    except Exception as e:
        print(f"Training Failed: {e}")

if __name__ == '__main__':
    main()
