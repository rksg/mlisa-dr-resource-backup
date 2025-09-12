"""
GCS Utilities for GCP Resource Reader and Kubernetes Resource Reader.

This module provides utility classes for copying files to/from GCS using gcloud CLI commands.
This approach bypasses SSL certificate issues in corporate environments.

Classes:
- GCSReader: Copy configuration files from GCS to local filesystem
- GCSWriter: Copy generated files from local filesystem to GCS
- Default Reader bucket: mlisa-dr-resource-backup
- Default Writer bucket: mlisa-dr-resource-backup

Usage:
    # Copy config files from GCS to local
    reader = GCSReader()
    reader._copy_from_gcs("static-configs/config.json", "local/config.json")
    
    # Copy generated files to GCS
    writer = GCSWriter()
    writer._copy_to_gcs("local/output.tfvars.json", "tf-vars/stg/output.tfvars.json")
"""

import subprocess

class GCSReader:
    """
    GCS Reader class for copying configuration files from Google Cloud Storage.
    
    This class uses gcloud CLI commands to copy files from GCS to local filesystem.
    This approach bypasses SSL certificate issues in corporate environments.
    """
    
    def __init__(self, 
                 bucket_name: str = "mlisa-dr-resource-backup"):
        """
        Initialize GCS Reader.
        
        Args:
            bucket_name: GCS bucket name (default: mlisa-dr-resource-backup)
        """
        self.bucket_name = bucket_name
        print(f"GCS Config Reader initialized for bucket: {self.bucket_name}")
    
    def _copy_from_gcs(self, gcs_path: str, local_path: str) -> bool:
        """
        Copy a file from GCS to local filesystem using gcloud CLI.
        
        Args:
            gcs_path: Path to file in GCS bucket
            local_path: Local path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        gcs_uri = f"gs://{self.bucket_name}/{gcs_path}"
        command = ["gcloud", "storage", "cp", gcs_uri, local_path]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print(f"Successfully copied from GCS: {gcs_uri}")
                return True
            else:
                print(f"Failed to copy from GCS: {gcs_uri}")
                print(f"Error: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("Command timed out")
        except Exception as e:
            print(f"Error: {e}")
        return False


class GCSWriter:
    """
    GCS Writer class for copying generated files to Google Cloud Storage.
    
    This class uses gcloud CLI commands to copy files from local filesystem to GCS.
    This approach bypasses SSL certificate issues in corporate environments.
    """
    
    def __init__(self, 
                 bucket_name: str = "mlisa-dr-resource-backup",
                 ):
        """
        Initialize GCS Writer.
        
        Args:
            bucket_name: GCS bucket name (default: mlisa-dr-resource-backup)
        """
        self.bucket_name = bucket_name
        print(f"GCS Writer initialized for bucket: {self.bucket_name}")
    
    def _copy_to_gcs(self, local_path: str, gcs_path: str) -> bool:
        """
        Copy a file from local filesystem to GCS using gcloud CLI.
        
        Args:
            local_path: Local path to the file
            gcs_path: Path to file in GCS bucket
            
        Returns:
            True if successful, False otherwise
        """
        gcs_uri = f"gs://{self.bucket_name}/{gcs_path}"
        command = ["gcloud", "storage", "cp", local_path, gcs_uri]
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print(f"Successfully copied from GCS: {gcs_uri}")
                return True
            else:
                print(f"Failed to copy from GCS: {gcs_uri}")
                print(f"Error: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("Command timed out")
        except Exception as e:
            print(f"Error: {e}")
        return False