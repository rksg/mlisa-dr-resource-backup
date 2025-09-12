# GCP Kubernetes Resource Reader

A comprehensive Python package for discovering and managing Google Cloud Platform (GCP) resources and Kubernetes resources using gcloud CLI and kubectl commands. This tool provides automated disaster recovery (DR) resource backup and configuration management across multiple environments.

## 🚀 Features

### GCP Resource Discovery
- **Compute Networks and Subnetworks**: Discover VPC networks and subnets with IP range management
- **NAT Routers**: Find and configure NAT gateways for outbound internet access
- **DataProc Clusters**: Extract cluster configurations for big data processing
- **Cloud Functions**: Discover serverless function configurations
- **Cloud Run Services**: Extract container service configurations
- **GKE Container Clusters**: Discover Kubernetes cluster settings
- **Firewall Rules**: Extract security rules and network policies
- **Compute Addresses**: Find static IP addresses and load balancer configurations
- **Redis Instances**: Discover cache configurations
- **Cloud SQL PostgreSQL**: Extract database instance configurations
- **VPC Access Connectors**: Find serverless VPC connectors

### Kubernetes Resource Management
- **Resource Extraction**: Fetch Kubernetes manifests from GKE clusters
- **YAML Processing**: Clean and format YAML output with minimal differences from Helm
- **Placeholder Support**: Apply placeholder values for templating
- **Search and Replace**: Apply configuration-based transformations
- **Multi-Environment Support**: Handle different environments and clusters
- **Druid & Kafka Support**: Specialized extraction for Druid and Kafka resources

### Multi-Site Support
- **Primary and DR Configurations**: Generate both primary and disaster recovery configurations
- **IP Range Management**: Automatic IP range assignment for multi-site deployments
- **Environment-Specific Settings**: Support for staging, production, and regional deployments

### Google Cloud Storage Integration
- **Centralized Configuration**: Read configuration files from GCS buckets
- **Automated Backup**: Save generated files to GCS for centralized management
- **Corporate Environment Support**: Uses gcloud CLI to bypass SSL certificate issues

## 📋 Prerequisites

- **Python 3.8+**
- **Google Cloud SDK (gcloud CLI)** - Required for all operations
- **kubectl** - For Kubernetes operations
- **Valid GCP credentials** and cluster access
- **Google Cloud Storage bucket** (for GCS integration)

## 🛠️ Installation

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd gcp-kube-resource-reader

# Install dependencies
pip install -r requirements.txt

# Run the service
python3 run_service.py stg r1-rai
```

### Docker Installation (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build individual services
docker-compose build build-env
docker-compose build mlisa-dr-resource-backup
```

## 🚀 Usage

### Service Runner (Main Interface)

The `run_service.py` script provides a unified interface for all operations:

```bash
# Basic usage - runs both GCP discovery and Kubernetes extraction
python3 run_service.py <environment> <cluster>

# Examples
python3 run_service.py stg r1-rai
python3 run_service.py prod-us rai
python3 run_service.py prod-eu r1-rai

# With GCS integration (default)
python3 run_service.py stg r1-rai --gcs-bucket my-terraform-bucket

# Skip GCS (use local files only)
python3 run_service.py stg r1-rai --skip-gcs
```

### Supported Environments
- `stg` - Staging environment
- `prod-us` - Production US
- `prod-eu` - Production EU
- `prod-asia` - Production Asia

### Supported Clusters
- `rai` - Primary cluster
- `r1-rai` - Disaster recovery cluster

### Command Line Options

```bash
python3 run_service.py [OPTIONS] <environment> <cluster>

Options:
  --gcs-bucket TEXT    GCS bucket name for reading config and saving output files
                       [default: mlisa-dr-resource-backup]
  --skip-gcs          Skip GCS for reading config and saving output files
                       [default: False]
  -h, --help          Show this help message and exit
```

## 📁 Project Structure

```
gcp-kube-resource-reader/
├── gcp_kube_resource_reader/          # Main package
│   ├── __init__.py                   # Package initialization
│   ├── gcp_resource_reader.py        # GCP resource discovery
│   ├── kube_resource_reader.py       # Kubernetes resource extraction
│   └── gcs_utils.py                  # GCS utilities
├── docker/                           # Docker configuration
│   ├── Dockerfile.build             # Build environment
│   └── Dockerfile.service           # Runtime environment
├── static-configs/                   # Configuration files
│   ├── config.json                  # Environment configuration
│   ├── druid-resources.yaml         # Druid resource definitions
│   ├── kafka-resources.yaml         # Kafka resource definitions
│   ├── druid-resources-placeholders.yaml
│   └── kafka-resources-placeholders.yaml
├── tf-vars/                         # Generated Terraform variable files
│   ├── stg/
│   ├── prod-us/
│   ├── prod-eu/
│   └── prod-asia/
├── kube-resources/                  # Generated Kubernetes resource files
│   ├── stg/
│   ├── prod-us/
│   ├── prod-eu/
│   └── prod-asia/
├── run_service.py                   # Main service runner
├── docker-compose.yaml              # Docker Compose configuration
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🔧 Configuration

### Environment Configuration

The tool uses `static-configs/config.json` for environment-specific settings:

```json
{
  "stg": {
    "project_id": "your-staging-project",
    "region": "us-central1",
    "dr_region": "us-east1",
    "rai": {
      "vpc": "your-vpc-name",
      "ip_ranges": {
        "primary": {
          "subnet_ip_cidr_range": "10.0.0.0/24",
          "secondary_ip_range_pod": "10.0.0.0/24",
          "secondary_ip_range_svc": "10.0.0.0/24",
          "vpc_connector_ip_cidr_range": "10.0.0.0/24",
          "gke_master_ip_cidr_range": "10.0.0.0/24"
        },
        "dr": {
          "subnet_ip_cidr_range": "10.0.0.0/24",
          "secondary_ip_range_pod": "10.0.0.0/24",
          "secondary_ip_range_svc": "10.0.0.0/24",
          "vpc_connector_ip_cidr_range": "10.0.0.0/24",
          "gke_master_ip_cidr_range": "10.0.0.0/24"
        }
      }
    }
  }
}
```

### GCS Bucket Structure

When using GCS integration, the tool expects this structure:

```
gs://your-bucket/
├── static-configs/
│   ├── config.json
│   ├── druid-resources.yaml
│   ├── kafka-resources.yaml
│   ├── druid-resources-placeholders.yaml
│   └── kafka-resources-placeholders.yaml
├── tf-vars/
│   ├── stg/
│   │   ├── r1-rai.tfvars.json
│   │   └── r1-rai-dr.tfvars.json
│   └── prod-us/
│       ├── rai.tfvars.json
│       └── rai-dr.tfvars.json
└── kube-resources/
    ├── stg/
    │   ├── r1-rai-druid-resources.yaml
    │   └── r1-rai-kafka-resources.yaml
    └── prod-us/
        ├── rai-druid-resources.yaml
        └── rai-kafka-resources.yaml
```

## 📊 Output Files

### GCP Resources (Terraform Variables)
- **Primary**: `./tf-vars/{environment}/{cluster}.tfvars.json`
- **DR**: `./tf-vars/{environment}/{cluster}-dr.tfvars.json`

### Kubernetes Resources (YAML Manifests)
- **Druid**: `./kube-resources/{environment}/{cluster}-druid-resources.yaml`
- **Kafka**: `./kube-resources/{environment}/{cluster}-kafka-resources.yaml`

## 🐳 Docker Usage

### Build and Run

```bash
# Build the images
docker-compose build

# Run the service
docker-compose run --rm mlisa-dr-resource-backup stg r1-rai

# Run with custom GCS bucket
docker-compose run --rm -e GCS_BUCKET=my-bucket mlisa-dr-resource-backup stg r1-rai
```

### Environment Variables

```bash
# Set GCS bucket
export GCS_BUCKET=my-terraform-bucket

# Run with environment variable
docker-compose run --rm mlisa-dr-resource-backup stg r1-rai
```

## 🔍 API Reference

### GCPResourceReader Class

```python
from gcp_kube_resource_reader import GCPResourceReader

# Initialize reader
reader = GCPResourceReader(
    project_id="your-project-id",
    network_name="your-vpc-name",
    region="us-central1",
    dr_region="us-east1",
    ip_ranges=ip_ranges_config
)

# Run GCP discovery
files = reader.run_gcp_discovery("stg", "r1-rai")
```

### KubeResourceReader Class

```python
from gcp_kube_resource_reader import KubeResourceReader

# Initialize reader
reader = KubeResourceReader()

# Run Kubernetes extraction
output_file = reader.run_kube_extraction("stg", "r1-rai", "druid")
```

### GCS Utilities

```python
from gcp_kube_resource_reader import GCSReader, GCSWriter

# Read config from GCS
reader = GCSReader("my-bucket")
reader._copy_from_gcs("static-configs/*", "./static-configs/")

# Save files to GCS
writer = GCSWriter("my-bucket")
writer._copy_to_gcs("./tf-vars/stg/output.json", "tf-vars/stg/output.json")
```

## 🧪 Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run linting
flake8 gcp_kube_resource_reader/
black gcp_kube_resource_reader/
mypy gcp_kube_resource_reader/
```

### Testing

```bash
# Test the service runner
python3 run_service.py stg r1-rai --skip-gcs

# Test with GCS integration
python3 run_service.py stg r1-rai --gcs-bucket test-bucket
```

## 🔒 Security Considerations

- **Non-Root Execution**: Container runs as non-root user for enhanced security
- **Minimal Dependencies**: Only necessary runtime components included
- **GCS Integration**: Uses gcloud CLI to bypass SSL certificate issues in corporate environments
- **Credential Management**: Supports service account authentication

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Ensure gcloud is authenticated
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Kubectl Context Issues**
   ```bash
   # Get GKE credentials
   gcloud container clusters get-credentials CLUSTER_NAME --zone ZONE --project PROJECT_ID
   ```

3. **GCS Permission Issues**
   ```bash
   # Check bucket permissions
   gsutil iam get gs://your-bucket-name
   ```

4. **Configuration File Issues**
   ```bash
   # Verify config file exists and is valid JSON
   cat static-configs/config.json | jq .
   ```

### Debug Mode

```bash
# Run with verbose output
python3 -v run_service.py stg r1-rai

# Check generated files
ls -la tf-vars/stg/
ls -la kube-resources/stg/
```

## 📝 Changelog

### Version 1.1.0
- **Unified Service Runner**: Single `run_service.py` interface for all operations
- **GCS Integration**: Full support for reading configuration from and writing output to Google Cloud Storage
- **gcloud CLI Approach**: Uses gcloud CLI instead of Python libraries for better corporate environment compatibility
- **Simplified Dependencies**: Reduced dependency complexity by removing unused Google Cloud libraries
- **Enhanced Documentation**: Comprehensive comments and updated examples
- **Improved Error Handling**: Better error messages and troubleshooting guidance
- **Docker Support**: Multi-stage Docker builds with security best practices

### Version 1.0.0
- Initial release
- GCP resource discovery functionality
- Kubernetes resource management
- Multi-environment support
- Disaster recovery configuration generation
- Terraform variable generation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Support

For support and questions, please contact the RSA MLISA team at mlisa-team@rsa.com.

## 🙏 Acknowledgments

- RSA MLISA Team for development and maintenance
- Google Cloud Platform for infrastructure services
- Kubernetes community for container orchestration tools