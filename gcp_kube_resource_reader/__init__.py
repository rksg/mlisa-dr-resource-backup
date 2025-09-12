"""
GCP and Kubernetes Resource Reader

A Python package for discovering and managing Google Cloud Platform (GCP) resources
and Kubernetes resources using gcloud CLI and kubectl commands.

This package provides tools for:
- GCP resource discovery (VPC, subnets, clusters, functions, etc.)
- Kubernetes resource extraction and management
- Multi-environment and disaster recovery configuration support
- Terraform variable generation
- Google Cloud Storage (GCS) integration for centralized configuration management

Main modules:
- gcp_resource_reader: GCP resource discovery and configuration
- kube_resource_reader: Kubernetes resource extraction and management
- gcs_utils: GCS utilities for reading config files and writing output files
"""

__version__ = "1.1.0"
__author__ = "RSA MLISA Team"
__email__ = "mlisa-team@rsa.com"

from .gcp_resource_reader import GCPResourceReader
from .kube_resource_reader import KubeResourceReader
from .gcs_utils import GCSReader, GCSWriter

__all__ = [
    "GCPResourceReader",
    "KubeResourceReader",
    "GCSReader",
    "GCSWriter",
]

