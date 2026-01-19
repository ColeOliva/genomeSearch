#!/usr/bin/env python3
"""
Download ClinVar data files from NCBI FTP.

Downloads:
- variant_summary.txt.gz: Comprehensive variant data with clinical significance
- gene_specific_summary.txt: Gene-level summary of pathogenic variants
"""

import gzip
import os
import shutil
import urllib.request

DATA_DIR = "data"

# ClinVar FTP URLs
CLINVAR_FILES = {
    "variant_summary.txt.gz": "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz",
    "gene_specific_summary.txt": "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/gene_specific_summary.txt",
}


def download_file(url, filename):
    """Download a file with progress reporting."""
    filepath = os.path.join(DATA_DIR, filename)
    
    if os.path.exists(filepath):
        print(f"  {filename} already exists, skipping...")
        return filepath
    
    print(f"  Downloading {filename}...")
    
    # Download with progress
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 / total_size)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\r    {mb_downloaded:.1f}/{mb_total:.1f} MB ({percent:.1f}%)", end="", flush=True)
    
    urllib.request.urlretrieve(url, filepath, reporthook=report_progress)
    print()  # Newline after progress
    
    return filepath


def extract_gzip(gz_path):
    """Extract a gzip file."""
    txt_path = gz_path[:-3]  # Remove .gz
    
    if os.path.exists(txt_path):
        print(f"  {os.path.basename(txt_path)} already extracted, skipping...")
        return txt_path
    
    print(f"  Extracting {os.path.basename(gz_path)}...")
    with gzip.open(gz_path, 'rb') as f_in:
        with open(txt_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    return txt_path


def main():
    """Download all ClinVar files."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print("Downloading ClinVar data files...")
    print("=" * 50)
    
    for filename, url in CLINVAR_FILES.items():
        print(f"\n{filename}:")
        filepath = download_file(url, filename)
        
        # Extract gzip files
        if filepath.endswith('.gz'):
            extract_gzip(filepath)
    
    print("\n" + "=" * 50)
    print("ClinVar download complete!")
    print("\nFiles downloaded to data/:")
    print("  - variant_summary.txt (~2.5 GB uncompressed)")
    print("  - gene_specific_summary.txt (~3.5 MB)")
    print("\nNext step: Run 'python import_clinvar.py' to import the data.")


if __name__ == "__main__":
    main()
