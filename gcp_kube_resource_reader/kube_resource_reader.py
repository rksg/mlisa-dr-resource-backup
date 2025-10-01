#!/usr/bin/env python3
"""
Kubernetes Resource Reader

This script converts the kube_res.sh shell script to Python.
It fetches Kubernetes resources from a GKE cluster and generates
a clean YAML output.
Supports both Druid and Kafka resources with GCS integration.

Key Features:
- Fetches Kubernetes resources from GKE clusters using kubectl
- Supports placeholder replacement and search/replace operations
- Integrates with Google Cloud Storage for configuration management
- Supports multiple environments (stg, prod-us, prod-eu, prod-asia)
- Supports multiple cluster types (rai, r1-rai)
- Supports multiple resource types (druid, kafka, monitoring)

Usage: 
    python3 kube_resource_reader.py <environment> <cluster> <resource_type> [--gcs-bucket BUCKET]
    
Examples: 
    python3 kube_resource_reader.py stg rai druid
    python3 kube_resource_reader.py stg rai monitoring
    python3 kube_resource_reader.py stg rai kafka
    python3 kube_resource_reader.py stg rai kafka --use-gcs false
    python3 kube_resource_reader.py prod-us r1-rai druid --gcs-bucket mlisa-dr-resource-backup

Dependencies:
- kubectl: Kubernetes command-line tool
- gcloud: Google Cloud SDK
- Valid GCP credentials and cluster access
- Configuration files in GCS or local filesystem

Author: RSA MLISA Team
Version: 1.1.0
"""

import json
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Optional

class IndentDumper(yaml.Dumper):
    """Custom YAML dumper for better list indentation control."""
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)

def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

# Add the representer to the IndentDumper class
yaml.add_representer(str, str_presenter, Dumper=IndentDumper)

class KubeResourceReader:
    """
    Kubernetes Resource Reader for extracting and processing Kubernetes resources from GKE clusters.
    
    This class provides functionality to:
    - Connect to GKE clusters using gcloud and kubectl
    - Fetch Kubernetes resources and clean their YAML output
    - Apply placeholder replacements and search/replace operations
    - Generate clean YAML files suitable for Terraform or other deployment tools
    - Integrate with Google Cloud Storage for configuration management
    
    Attributes:
        project_id (str): GCP project ID for the cluster
        region (str): GCP region where the cluster is located
        placeholders (dict): Cached placeholder configurations for resource processing
    """
    
    def __init__(self):
        """
        Initialize the Kubernetes Resource Reader.
        
        Sets up the basic attributes needed for resource processing.
        Configuration is loaded dynamically based on environment and cluster parameters.
        """
        self.project_id = None
        self.region = None
        self.placeholders = None
        
    def check_dependencies(self) -> None:
        """
        Check if required dependencies (kubectl and gcloud) are available.
        
        This method verifies that the necessary command-line tools are installed
        and accessible in the system PATH. It's called before attempting to
        connect to GKE clusters or fetch resources.
        
        Raises:
            SystemExit: If any required dependency is not found or not accessible
        """
        dependencies = ['kubectl', 'gcloud']
        
        for dep in dependencies:
            try:
                if dep == 'kubectl':
                    subprocess.run([dep, 'version', '--client'], 
                                 capture_output=True, check=True, text=True)
                else:
                    subprocess.run([dep, '--version'], 
                             capture_output=True, check=True, text=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"Error: {dep} is required but not installed or not in PATH.")
                if dep == 'kubectl':
                    print("Installation: https://kubernetes.io/docs/tasks/tools/")
                elif dep == 'gcloud':
                    print("Installation: https://cloud.google.com/sdk/docs/install")
                sys.exit(1)
    
    def load_config(self, config_path: Path, environment: str) -> tuple[str, str]:
        """
        Load project_id and region from config.json based on environment.
        
        This method reads the configuration file and extracts the project ID and region
        for the specified environment. The configuration file should contain environment-specific
        settings including project IDs and regions.
        
        Args:
            config_path (str): Path to the configuration directory containing config.json
            environment (str): Environment name (e.g., 'stg', 'prod-us', 'prod-eu', 'prod-asia')
            
        Returns:
            tuple[str, str]: A tuple containing (project_id, region)
            
        Raises:
            SystemExit: If the environment is not found or required fields are missing
        """
        config_file = config_path + "/config.json"
        
        try:
            with open(config_file, 'r') as f:   
                config = json.load(f)
            
            if environment not in config:
                print(f"Error: environment '{environment}' not found in config.json")
                sys.exit(1)
            
            env_config = config[environment]
            project_id = env_config.get('project_id')
            region = env_config.get('region')
            
            if not project_id:
                print(f"Error: project_id not found for environment '{environment}' in config.json")
                sys.exit(1)
            
            if not region:
                print(f"Error: region not found for environment '{environment}' in config.json")
                sys.exit(1)
            
            return project_id, region
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error: Failed to parse config.json: {e}")
            sys.exit(1)
    
    def get_kubectl_context(self, project_id: str, cluster: str, region: str) -> tuple[str, str]:
        """Set kubectl context for the specified cluster and return both cluster name and context."""
        try:
            # Get list of clusters
            result = subprocess.run([
                'gcloud', 'container', 'clusters', 'list',
                '--project', project_id,
                '--format', 'value(name)'
            ], capture_output=True, check=True, text=True)
            
            clusters = result.stdout.strip().split('\n')
            
            # Find the appropriate cluster based on cluster type
            kube_cluster = None
            if cluster == "rai":
                kube_cluster = next((c for c in clusters if '-sa-' in c and 'gke' in c), None)
            elif cluster == "r1-rai":
                kube_cluster = next((c for c in clusters if 'alto-' in c and 'gke' in c), None)
            else:
                print(f"Error: cluster '{cluster}' not supported. Use 'rai' or 'r1-rai'")
                sys.exit(1)
            
            if not kube_cluster:
                print(f"Error: No GKE cluster found for cluster type '{cluster}' in project '{project_id}'")
                sys.exit(1)
            
            # Get the current kubectl context
            current_context_result = subprocess.run([
                'kubectl', 'config', 'current-context'
            ], capture_output=True, check=True, text=True)

            print(f"Fetching kubectl context for cluster: {kube_cluster}")
            
            # Set kubectl credentials
            subprocess.run([
                'gcloud', 'container', 'clusters', 'get-credentials',
                kube_cluster, '--project', project_id, '--region', region,
            ], check=True)
            
            # Get the kubectl context for the cluster
            cluster_context_result = subprocess.run([
                'kubectl', 'config', 'current-context'
            ], capture_output=True, check=True, text=True)
            
            cluster_context = cluster_context_result.stdout.strip()
            print(f"Cluster kubectl context: {cluster_context}")

            # Set back the kubectl context to the current context
            current_context = current_context_result.stdout.strip()
            current_context_result = subprocess.run([
                'kubectl', 'config', 'use-context', current_context
            ], check=True, stdout=subprocess.DEVNULL)
            
            return kube_cluster, cluster_context
            
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to set kubectl context: {e}")
            sys.exit(1)
    
    def clean_kubectl_output_json(self, json_content: str) -> json:
        try:
            data = json.loads(json_content)
            if not data:
                return ""
            
            metadata = data.get('metadata', {})
            metadata.pop('resourceVersion', None)
            metadata.pop('uid', None)
            metadata.pop('generation', None)
            metadata.pop('creationTimestamp', None)
            metadata.pop('managedFields', None)

            # Clean annotations
            annotations = metadata.get('annotations', {})
            annotations.pop('kubectl.kubernetes.io/last-applied-configuration', None)
            annotations.pop('deployment.kubernetes.io/revision', None)
            annotations.pop('kubernetes.io/change-cause', None)
            annotations.pop('cloud.google.com/neg', None)
            annotations.pop('cloud.google.com/neg-status', None)
            annotations.pop('volume.kubernetes.io/selected-node', None)
            annotations.pop('pv.kubernetes.io/bind-completed', None)
            
            # Clean labels
            labels = metadata.get('labels', {})
            labels.pop('helm.sh/chart', None)
            
            # Remove owner references
            metadata.pop('ownerReferences', None)
            
            # Clean spec section
            spec = data.get('spec', {})
            if spec:
                # Clean template metadata
                template = spec.get('template', {})
                if template:
                    template_metadata = template.get('metadata', {})
                    if template_metadata:
                        template_labels = template_metadata.get('labels', {})
                        template_labels.pop('pod-template-hash', None)
                        template_labels.pop('pod-template-generation', None)
                        
                        template_annotations = template_metadata.get('annotations', {})
                        template_annotations.pop('kubectl.kubernetes.io/restartedAt', None)
                        template_annotations.pop('kubectl.kubernetes.io/last-applied-configuration', None)
                        template_metadata.pop('creationTimestamp', None)
                    
                    # Clean selector
                    selector = spec.get('selector', {})
                    if selector:
                        match_labels = selector.get('matchLabels', {})
                        match_labels.pop('pod-template-hash', None)
                        match_labels.pop('pod-template-generation', None)
                
                # Clean service-specific fields
                if data.get('kind') == 'Service' and not data.get('metadata').get('name').endswith('-headless'):
                    spec.pop('clusterIP', None)
                    spec.pop('clusterIPs', None)
                    spec.pop('loadBalancerIP', None)

                if data.get('kind') == 'PersistentVolumeClaim':
                    spec.pop('volumeName', None)

            data.pop('status', None)

            # Convert back to YAML with proper formatting
            return data
            
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse JSON content: {e}")
            return ""
    
    def fetch_resource(self, resource_type: str, resource_name: str, cluster_context: str, namespace_name: str) -> Optional[json]:
        """Fetch a specific Kubernetes resource."""
        try:
            if resource_name == "mlisa-monitoring-fluentd" or resource_name == "mlisa-monitoring-fluentd-config":
                namespace_name = "kube-system"
            result = subprocess.run([
                'kubectl', '-n', namespace_name, 'get',
                resource_type, resource_name, '-o', 'json', '--context', cluster_context
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                return self.clean_kubectl_output_json(result.stdout)
            
        except subprocess.CalledProcessError:
            return None
    
    def load_placeholders(self, config_path: Path, resource_type: str) -> dict:
        """Load placeholder configuration from resource-specific placeholders file (cached)."""
        placeholder_file = config_path + f"/{resource_type}-resources-placeholders.yaml"
        
        try:
            with open(placeholder_file, 'r') as f:
                self.placeholders = yaml.safe_load(f) or {}
                print(f"Loaded placeholders: {self.placeholders}")
                return self.placeholders
        except FileNotFoundError:
            print(f"Warning: Placeholder file {placeholder_file} not found, using empty placeholders")
            self.placeholders = {}
            return self.placeholders
        except yaml.YAMLError as e:
            print(f"Warning: Failed to parse placeholder file: {e}")
            self.placeholders = {}
            return self.placeholders
    
    def add_placeholders(self, data: json, resource_type: str, resource_name: str) -> json:
        """Add placeholder values enclosed in double pipe symbols based on configuration."""
        if not self.placeholders or resource_type not in self.placeholders:
            return data
        
        resource_placeholders = self.placeholders[resource_type]
        if not isinstance(resource_placeholders, list):
            return data
        
        # Find the resource configuration
        resource_config = None
        for item in resource_placeholders:
            if isinstance(item, dict) and resource_name in item:
                resource_config = item[resource_name]
                break
        
        if not resource_config or not isinstance(resource_config, list):
            return data
        
        # Apply placeholders
        for placeholder_item in resource_config:
            if not isinstance(placeholder_item, dict):
                continue
            
            # Each item is a dictionary with path as key and placeholder name as value
            for path, placeholder_name in placeholder_item.items():
                # Split the path (e.g., "data|DRUID_INDEXER_LOG_DIR" -> ["data", "DRUID_INDEXER_LOG_DIR"])
                path_parts = path.split('|')
                if len(path_parts) < 2:
                    continue
                
                # Navigate to the target field
                current = data
                for part in path_parts[:-1]:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        current = None
                        break
                
                # Set the placeholder value if we found the target field
                if current is not None and isinstance(current, dict):
                    field_name = path_parts[-1]
                    placeholder_value = f"||{placeholder_name}||"
                    current[field_name] = placeholder_value
        
        return data
    
    def apply_search_replace(self, data: json, resource_type: str) -> json:
        """Apply search and replace operations on YAML content based on configuration."""
        if not self.placeholders or 'Search_and_Replace' not in self.placeholders:
            return data
        
        search_replace_config = self.placeholders['Search_and_Replace']
        if not isinstance(search_replace_config, list):
            return data
        
        result_content = json.dumps(data, indent=2)
        
        # Apply each search and replace operation
        for search_replace_item in search_replace_config:
            if not isinstance(search_replace_item, dict):
                continue
            
            # Each item is a dictionary with search string as key and replacement as value
            for search_string, replacement_string in search_replace_item.items():
                if isinstance(search_string, str) and isinstance(replacement_string, str):
                    # Perform the replacement
                    result_content = result_content.replace(search_string, f"||{replacement_string}||")
        
        return json.loads(result_content)
    
    def run_kube_extraction(self, environment: str, cluster: str, service_type: str) -> str:
        """
        Main execution function for extracting Kubernetes resources.
        
        This method orchestrates the entire process of:
        1. Loading configuration for the specified environment
        2. Setting up kubectl context for the GKE cluster
        3. Reading resource definitions from YAML files
        4. Fetching actual Kubernetes resources from the cluster
        5. Applying placeholder replacements and search/replace operations
        6. Cleaning and formatting the output YAML
        7. Saving the results to output files
        
        Args:
            environment (str): Environment name (e.g., 'stg', 'prod-us', 'prod-eu', 'prod-asia')
            cluster (str): Cluster type ('rai' or 'r1-rai')
            service_type (str): Service type ('druid' or 'kafka' or 'monitoring')
            
        Returns:
            str: Path to the generated output file containing the extracted resources
            
        Raises:
            SystemExit: If configuration files are missing or cluster access fails
        """
        print(f"Parsing {service_type}-resources.yaml and fetching Kubernetes manifests...")
        
        # Check dependencies
        self.check_dependencies()

        # Define file paths
        config_path = "./static-configs"
        input_file = config_path + f"/{service_type}-resources.yaml"
        output_file = "./kube-resources/" + environment + f"/{cluster}-{service_type}-resources.yaml"

        # Load configuration
        self.project_id, self.region = self.load_config(config_path, environment)
        
        # Set kubectl context
        kube_cluster, kube_context = self.get_kubectl_context(self.project_id, cluster, self.region)
        

        
        print(f"Environment: {environment}")
        print(f"Cluster: {cluster}")
        print(f"Service Type: {service_type}")
        print(f"Project ID: {self.project_id}")
        print(f"Region: {self.region}")
        print(f"Kube Cluster: {kube_cluster}")
        print(f"Kubectl Context: {kube_context}")
        print(f"Input file: {input_file}")
        print(f"Output file: {output_file}")
        
        # Parse resources directly from YAML and process them
        resource_count = 0
        successful_resources = 0
        
        try:
            with open(input_file, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                print(f"Warning: {input_file} is empty or invalid")
                return
            self.load_placeholders(config_path, service_type)
            with open(output_file, 'w') as output_f:
                # Iterate through each resource type and its list of resources
                for resource_type, resource_list in data.items():
                    if isinstance(resource_list, list):
                        print(f"Found resource type: {resource_type}")
                        if resource_type == "Namespaces":
                            namespace_name = resource_list[0]
                        for resource_name in resource_list:
                            if isinstance(resource_name, str) and resource_name.strip():
                                resource_name = resource_name.strip()
                                resource_count += 1
                                print(f"Processing {resource_count}: {resource_type}: {resource_name}")
                                
                                json_data = self.fetch_resource(resource_type, resource_name, kube_context, namespace_name)
                                
                                if json_data:
                                    # Add placeholder values if configured
                                    json_data_with_placeholders = self.add_placeholders(json_data, resource_type, resource_name)
                                    
                                    # Apply search and replace operations
                                    json_data_with_replacements = self.apply_search_replace(json_data_with_placeholders, resource_type)
                                    
                                    # Clean up the YAML content to ensure proper formatting
                                    cleaned_yaml = yaml.dump(
                                                    json_data_with_replacements,
                                                    Dumper=IndentDumper,
                                                    default_flow_style=False,
                                                    sort_keys=False,
                                                    allow_unicode=True,
                                                    width=100000,
                                                    indent=2,
                                                    explicit_start=False,
                                                    explicit_end=False
                                                    )
                                    if cleaned_yaml:
                                        output_f.write(cleaned_yaml)
                                        output_f.write("---\n")
                                        successful_resources += 1
                                        print(f"  ✓ Fetched {resource_type}/{resource_name}")
                                else:
                                    print(f"  ! Resource {resource_type}/{resource_name} not found")
                    else:
                        print(f"Warning: {resource_type} is not a list, skipping")
        
        except FileNotFoundError:
            print(f"Error: Input file {input_file} not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error: Failed to parse YAML file {input_file}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: Failed to parse {input_file}: {e}")
            sys.exit(1)
        
        # Clean up the output file to remove trailing separators
        self.cleanup_output_file(output_file)
        
        print()
        print(f"Resources extracted to {output_file}")
        print(f"Total resources processed: {resource_count}")
        print(f"Total resources in output file: {successful_resources}")

        return output_file
    
    def cleanup_output_file(self, output_file: str) -> None:
        """Clean up the output file to remove trailing separators and extra newlines."""
        try:
            with open(output_file, 'r') as f:
                content = f.read()
            
            # Remove trailing --- and extra newlines
            content = content.rstrip('\n-')
            content = content.rstrip('\n')
            
            with open(output_file, 'w') as f:
                f.write(content)
                
        except Exception as e:
            print(f"Warning: Failed to cleanup output file: {e}")
