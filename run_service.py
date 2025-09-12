#!/usr/bin/env python3
"""
GCP Kubernetes Resource Reader Service Runner

This program provides a unified interface to run both GCP resource discovery
and Kubernetes resource extraction services with environment and cluster arguments.

Supported Environments:
    - stg (staging)
    - prod-us (production US)
    - prod-eu (production EU)
    - prod-asia (production Asia)

Supported Clusters:
    - rai
    - r1-rai

Author: RSA MLISA Team
Version: 1.1.0
"""

import argparse
import sys
import os
from typing import List
from gcp_kube_resource_reader.gcp_resource_reader import GCPResourceReader
from gcp_kube_resource_reader.kube_resource_reader import KubeResourceReader
from gcp_kube_resource_reader.gcs_utils import GCSReader, GCSWriter


class ServiceRunner:
    """
    Service runner for GCP and Kubernetes resource readers.
    
    This class provides methods to execute both GCP resource discovery
    and Kubernetes resource extraction services with proper error handling
    and output management.
    """
    
    def run_services(self, environment: str, cluster: str) -> List[str]:
        """
        Run both GCP discovery and Kubernetes extraction services.
        
        Args:
            environment: Environment name (stg, prod-us, prod-eu, prod-asia)
            cluster: Cluster type (rai, r1-rai)
            
        Returns:
            List of generated file paths 
        """
        print(f"🚀 Starting DR Resource Backup for {environment}/{cluster}")
        print("=" * 60)
        
        # Run GCP resource discovery
        generated_files = GCPResourceReader().run_gcp_discovery(environment, cluster)
        print("\n" + "=" * 60)
        
        kube_resource_reader = KubeResourceReader()
        # Run Kubernetes resource extraction for both druid and kafka
        generated_files.append(kube_resource_reader.run_kube_extraction(environment, cluster, 'druid'))

        print("\n" + "=" * 60)
        # Run kafka extraction
        generated_files.append(kube_resource_reader.run_kube_extraction(environment, cluster, 'kafka'))
        
        return generated_files

def read_config_from_gcs_utils(gcs_config_bucket_name: str) -> bool:
    """
    Read configuration files from Google Cloud Storage to local filesystem.
    
    This function uses the GCSReader utility to copy configuration files from a GCS bucket
    to the local filesystem. It specifically copies the static-configs directory structure
    which includes config.json and resource definition files.
    
    Args:
        gcs_config_bucket_name (str): Name of the GCS bucket containing configuration files
        
    Returns:
        bool: True if configuration files are successfully copied to local filesystem
        
    Raises:
        ValueError: If GCS Reader fails to copy files or bucket is not accessible
    """
    if not GCSReader(gcs_config_bucket_name)._copy_from_gcs("static-configs/*", "./static-configs/"):
        raise ValueError("GCS Reader not initialized. Set use_gcs=True to enable GCS functionality.") 
    return True

def save_to_gcs_utils(gcs_output_bucket_name: str, file_path: str) -> bool:
    """
    Save generated files to Google Cloud Storage.
    
    This function uses the GCSWriter utility to upload generated Kubernetes resource files
    to a GCS bucket. The file path is preserved in the bucket structure.
    
    Args:
        gcs_output_bucket_name (str): Name of the GCS bucket for storing output files
        file_path (str): Local path to the file to upload to GCS
        
    Returns:
        bool: True if file is successfully uploaded to GCS
        
    Raises:
        ValueError: If GCS Writer fails to upload file or bucket is not accessible
    """
    if not GCSWriter(gcs_output_bucket_name)._copy_to_gcs(file_path, f"{file_path}"):
        raise ValueError("GCS Writer not initialized. Set use_gcs=True to enable GCS functionality.")
    return True

def create_local_dirs():
    """Create local directories for output files."""
    os.makedirs('./kube-resources', exist_ok=True)
    os.makedirs('./static-configs', exist_ok=True)
    os.makedirs('./tf-vars', exist_ok=True)

def main():
    """Main entry point for the service runner."""
    parser = argparse.ArgumentParser(
        description="GCP Kubernetes Resource Reader Service Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  
  # Run with GCS integration
  python3 run_service.py stg r1-rai --gcs-bucket my-bucket
        """
    )
    
    parser.add_argument(
        'environment',
        choices=['stg', 'prod-us', 'prod-eu', 'prod-asia'],
        help='Environment name'
    )
    
    parser.add_argument(
        'cluster',
        choices=['rai', 'r1-rai'],
        help='Cluster type'
    )
    
    parser.add_argument(
        '--gcs-bucket',
        help='GCS bucket name for reading config and saving output files',
        default='mlisa-dr-resource-backup'
    )
    
    parser.add_argument(
        '--skip-gcs',
        help='Skip GCS for reading config and saving output files',
        default=False
    )
    
    args = parser.parse_args()
    
    create_local_dirs()
    if args.skip_gcs == False and not read_config_from_gcs_utils(args.gcs_bucket):
        print("Error: Failed to read config from GCS")
        sys.exit(1)
    
    # Initialize service runner
    runner = ServiceRunner()
    
    # Run the requested service(s)
    generated_files = runner.run_services(args.environment, args.cluster)
    
    # Exit with appropriate code
    if generated_files and len(generated_files) == 4:
        print("\n✅ Service execution completed successfully")
        if args.skip_gcs == False:
            for output_filename in generated_files:
                if not save_to_gcs_utils(args.gcs_bucket, output_filename.replace('./','')):
                    print("Error: Failed to save resources to GCS")
                    sys.exit(1)
            print("\n✅ Resources saved to GCS successfully" , generated_files)
    else:
        print("\n❌ Service execution failed. Files generated: ", generated_files)
        sys.exit(1)

if __name__ == "__main__":
    main()
