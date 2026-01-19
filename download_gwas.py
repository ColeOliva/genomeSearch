"""
Download GWAS Catalog data from EBI.
This provides gene-trait associations from genome-wide association studies.
"""

import os
import shutil
import urllib.request
import zipfile

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# GWAS Catalog - gene-trait associations (from FTP server)
# Full version with ontology annotations
GWAS_URL = "https://ftp.ebi.ac.uk/pub/databases/gwas/releases/latest/gwas-catalog-associations_ontology-annotated-full.zip"
GWAS_ZIP = os.path.join(DATA_DIR, 'gwas_catalog.zip')
GWAS_FILE = os.path.join(DATA_DIR, 'gwas_catalog.tsv')


def download_file(url, dest_path, desc="file"):
    """Download a file with progress indication."""
    print(f"Downloading {desc}...")
    print(f"  URL: {url}")
    print(f"  Destination: {dest_path}")
    
    try:
        # Create a request with headers to avoid blocks
        request = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        with urllib.request.urlopen(request, timeout=300) as response:
            total_size = response.headers.get('Content-Length')
            if total_size:
                total_size = int(total_size)
                print(f"  Size: {total_size / (1024*1024):.1f} MB")
            
            # Download to temp file first
            temp_path = dest_path + '.tmp'
            downloaded = 0
            block_size = 1024 * 1024  # 1MB blocks
            
            with open(temp_path, 'wb') as f:
                while True:
                    block = response.read(block_size)
                    if not block:
                        break
                    f.write(block)
                    downloaded += len(block)
                    if total_size:
                        pct = (downloaded / total_size) * 100
                        print(f"\r  Progress: {downloaded/(1024*1024):.1f} MB ({pct:.1f}%)", end='', flush=True)
                    else:
                        print(f"\r  Downloaded: {downloaded/(1024*1024):.1f} MB", end='', flush=True)
            
            print()  # newline after progress
            
            # Move temp file to final destination
            shutil.move(temp_path, dest_path)
            print(f"  Done: {dest_path}")
            return True
            
    except Exception as e:
        print(f"  ERROR: {e}")
        if os.path.exists(dest_path + '.tmp'):
            os.remove(dest_path + '.tmp')
        return False


def main():
    """Download GWAS Catalog data."""
    print("=" * 60)
    print("GWAS Catalog Downloader")
    print("=" * 60)
    print()
    print("This downloads gene-trait association data from the")
    print("NHGRI-EBI GWAS Catalog (https://www.ebi.ac.uk/gwas/)")
    print()
    
    # Create data directory
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Check if file already exists
    if os.path.exists(GWAS_FILE):
        size_mb = os.path.getsize(GWAS_FILE) / (1024 * 1024)
        print(f"GWAS catalog already exists: {GWAS_FILE}")
        print(f"  Size: {size_mb:.1f} MB")
        response = input("Re-download? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping download.")
            return
    
    # Download GWAS Catalog ZIP
    success = download_file(GWAS_URL, GWAS_ZIP, "GWAS Catalog")
    
    if success:
        # Extract the ZIP file
        print()
        print("Extracting ZIP file...")
        extracted_ok = False
        try:
            with zipfile.ZipFile(GWAS_ZIP, 'r') as zf:
                # Find the TSV file inside
                tsv_files = [f for f in zf.namelist() if f.endswith('.tsv')]
                if tsv_files:
                    # Extract the first TSV file
                    tsv_name = tsv_files[0]
                    print(f"  Extracting: {tsv_name}")
                    
                    # Extract to data directory
                    zf.extract(tsv_name, DATA_DIR)
                    
                    # Rename to our expected filename
                    extracted_path = os.path.join(DATA_DIR, tsv_name)
                    if os.path.exists(GWAS_FILE):
                        os.remove(GWAS_FILE)
                    shutil.move(extracted_path, GWAS_FILE)
                    
                    size_mb = os.path.getsize(GWAS_FILE) / (1024 * 1024)
                    print(f"  Extracted: {GWAS_FILE} ({size_mb:.1f} MB)")
                    extracted_ok = True
                else:
                    print("  ERROR: No TSV file found in ZIP")
                    return
                    
        except Exception as e:
            print(f"  ERROR extracting: {e}")
            return
        
        # Clean up ZIP file (outside the with block so file is closed)
        if extracted_ok and os.path.exists(GWAS_ZIP):
            try:
                os.remove(GWAS_ZIP)
                print("  Cleaned up ZIP file")
            except Exception as e:
                print(f"  Warning: Could not delete ZIP file: {e}")
        
        print()
        print("=" * 60)
        print("Download complete!")
        print()
        print("Next step: Run 'python import_gwas.py' to import into database.")
        print("=" * 60)
    else:
        print()
        print("Download failed. Please try again or download manually from:")
        print("  https://www.ebi.ac.uk/gwas/docs/file-downloads")


if __name__ == '__main__':
    main()
