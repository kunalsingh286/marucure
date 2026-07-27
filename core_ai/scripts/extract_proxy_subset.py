import pandas as pd
import zipfile
import tarfile
import os
import shutil

def main():
    print("Extracting Data_Entry_2017.csv from zip...")
    if not os.path.exists("Data_Entry_2017.csv"):
        with zipfile.ZipFile("Data_Entry_2017.csv.zip", "r") as z:
            z.extract("Data_Entry_2017.csv", ".")
        
    print("Reading metadata with pandas...")
    df = pd.read_csv("Data_Entry_2017.csv")
    
    # Filter strictly for 'No Finding' (150 samples)
    normal_df = df[df['Finding Labels'] == 'No Finding'].head(150)
    normal_images = set(normal_df['Image Index'].tolist())
    
    # Filter strictly for 'Nodule' or 'Fibrosis', without '|' (100 samples)
    silicosis_df = df[df['Finding Labels'].isin(['Nodule', 'Fibrosis'])].head(100)
    silicosis_images = set(silicosis_df['Image Index'].tolist())
    
    target_images = normal_images.union(silicosis_images)
    
    normal_dir = os.path.abspath("core_ai/data/train/normal")
    silicosis_dir = os.path.abspath("core_ai/data/train/silicosis")
    
    print(f"Found {len(normal_images)} normal and {len(silicosis_images)} silicosis images.")
    print(f"Searching and extracting {len(target_images)} target images from tar archive directly (to avoid full 2GB extraction)...")
    
    extracted_count = 0
    with tarfile.open("images_001.tar.gz", "r:gz") as tar:
        for member in tar:
            if not member.isfile():
                continue
            
            filename = os.path.basename(member.name)
            if filename in target_images:
                # determine target dir
                if filename in normal_images:
                    target_path = os.path.join(normal_dir, filename)
                else:
                    target_path = os.path.join(silicosis_dir, filename)
                
                # Extract directly to destination
                f_in = tar.extractfile(member)
                if f_in is not None:
                    with open(target_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    extracted_count += 1
                    
                    if extracted_count % 50 == 0:
                        print(f"Extracted {extracted_count}/{len(target_images)} images...")
                        
            if extracted_count >= len(target_images):
                break
                
    print(f"Successfully extracted {extracted_count} images directly into target directories.")
    
if __name__ == "__main__":
    main()
