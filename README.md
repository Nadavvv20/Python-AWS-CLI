# ☁️ AWS Platform CLI (awsctl)

**Platform Engineering Self-Service Tool**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![AWS SDK](https://img.shields.io/badge/AWS-Boto3-orange.svg)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
[![Status](https://img.shields.io/badge/Status-Educational-green.svg)]()

## 📖 Overview
**awsctl** is a Python-based Command Line Interface (CLI) designed to enable developers to provision AWS resources (EC2, S3, Route53) independently.

This tool acts as a **Platform Engineering Guardrail**, ensuring that all resources are created within safe, pre-defined standards. It enforces strict constraints (such as instance types and capacity limits) and abstracts complex AWS API calls into simple, intuitive commands.

Tech Stack: Built with **Python** and the **AWS Boto3 SDK**. It features a robust CLI structure via **Click**, with advanced terminal styling and visual guardrails powered by the **Rich** and **Pyfiglet** libraries.

---

## 📂 Project Structure
The project follows a modular and professional package structure:

```text
Python-AWS-CLI/
├── src/
│   ├── __init__.py
│   ├── cli.py                  # Main CLI logic (Click groups & commands)
│   ├── platform_manager.py     # Cross-resource logic (List All / Cleanup All)
│   ├── ec2/
│   │   ├── __init__.py
│   │   └── manager.py          # EC2 Logic (Constraints, AMI lookup, Lifecycle)
│   ├── s3/
│   │   ├── __init__.py
│   │   └── manager.py          # S3 Logic (Security checks, Uploads, List)
│   ├── route53/
│   │   ├── __init__.py
│   │   └── manager.py          # Route53 Logic (Zones, Records filtering)
│   └── utils/
│       ├── __init__.py
│       └── helpers.py          # Identity helpers (STS/IAM) and Rich-based console output
├── tests/                      # Unit & Integration tests
│       ├── test_ec2.py
│       ├── test_route53_flow.py
│       └── test_s3_flow.py
├── .gitignore
├── README.md                   # Documentation
├── install.sh                  # Installation script with welcome banner
├── post_install.py             # Welcome message after installation
├── setup.py                    # Package installation config
└── main.py                     # Entry point script
```
## ⚙️ Prerequisites
Before installation, ensure you have:
* **Python 3.9+** installed. 
* **AWS CLI** installed and configured. 
    ```bash
    aws configure
    ```
* **Note:** Your IAM user must have permissions to manage EC2, S3, and Route53. 

---

## 🚀 Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/Nadavvv20/Python-AWS-CLI.git
    cd Python-AWS-CLI
    ```

2. **Set up a Virtual Environment:**
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # Mac/Linux:
    source .venv/bin/activate
    ```

3. **Install the tool:**
    ```bash
    bash install.sh
    ```
    > This installs all dependencies in editable mode and displays a welcome banner upon completion.

    *Alternatively, you can install directly with pip (without the welcome banner):*
    ```bash
    pip install -e .
    ```

---

## 🏷️ Tagging & Security Guardrails
The tool enforces organizational standards automatically: 
* **Consistent Tagging:** Every resource includes `CreatedBy=Nadav-Platform-CLI` and `Owner=<Current_User>`. 
* **EC2 Constraints:** 
    * Restricted to `t3.micro` or `t3.small`. 
    * **Hard Cap:** Maximum of 2 running instances created by the CLI allowed simultaneously. 
* **S3 Security:** Public buckets require explicit user confirmation (**Are you sure?**).
* **S3 Encryption:** Every bucket created via the CLI, is configured with default encryption (SSE-S3).
* **Scoped Access:** The tool only operates on resources it created (verified by tags). 

---

## 🛠️ Command Reference Summary

### EC2 Commands (`awsctl ec2`)
| Command | Options | Description |
| :--- | :--- | :--- |
| `create` | `--name`, `--key`, `--ami`, `--type` | Creates a tagged instance & SG. Auto-creates Key Pair if missing. |
| `start` | `instance_id` | Starts a stopped instance. |
| `stop` | `instance_id` | Stops a running instance. |
| `list` | - | Lists all CLI-created instances and their status. |
| `cleanup` | - | Terminates all instances managed by the CLI. |

### S3 Commands (`awsctl s3`)
| Command | Options | Description |
| :--- | :--- | :--- |
| `create` | `--name`, `--public/--private` | Creates a bucket (Public requires confirmation). |
| `upload` | `--bucket`, `--file`, `--key` | Uploads a file to a CLI-managed bucket. |
| `list` | - | Lists all CLI-created buckets. |
| `cleanup` | - | Deletes all buckets managed by the CLI. |

### DNS Commands (`awsctl dns`)
| Command | Arguments/Options | Description |
| :--- | :--- | :--- |
| `create-zone` | `domain_name` | Creates a new Route53 Hosted Zone. |
| `record` | `zone_id`, `action`, `--name`, `--type`, `--value` | Manages DNS records (UPSERT/DELETE). |
| `list` | - | Lists all CLI-created zones and their records. |
| `cleanup` | - | Deletes all Hosted Zones managed by the CLI. |

### Global Commands
| Command | Options | Description |
| :--- | :--- | :--- |
| `awsctl list-all` | - | Lists ALL platform resources in a unified table. |
| `awsctl cleanup-all` | - | Deletes ALL platform resources with a single command (Requires confirmation). |

---

## 📖 Detailed Usage Examples

### Compute (EC2)
Create a server with automatic AMI lookup and Key Pair handling:
```bash
awsctl ec2 create --name dev-app --key my-key --ami ubuntu --type t3.micro
```
*If `my-key` doesn't exist, it will be created and saved as `my-key.pem` in your current folder.*
*A Security Group `Nadav-CLI-SG` will be created automatically with Port 22 open.*

Start or Stop an instance:
```bash
awsctl ec2 stop i-0123456789abcdef0
awsctl ec2 start i-0123456789abcdef0
```
### Storage (S3)
Upload a file to a secure bucket: 
```bash
awsctl s3 upload --bucket my-cli-bucket --file data.json --key backups/data.json
```
### DNS (Route53) 
Add an A record to your zone: 
```bash
awsctl dns record Z0123456789 UPSERT --name api.example.com --type A --value 1.2.3.4
```
### 🧹 Cleanup

To avoid AWS costs, remove all resources created during your session:

```bash
awsctl cleanup-all
```
Or individually:
```bash
awsctl ec2 cleanup
awsctl s3 cleanup
awsctl dns cleanup
```

---

## 🔔 Jenkins Pipeline & Monitoring

To ensure cost optimization and visibility, the project includes a **Jenkins Pipeline** that runs daily to monitor active resources.

### 🤖 Automation Workflow
1. **Schedule:** Runs automatically every day at **17:00**.
2. **Check:** The `instance_status_check.py` script queries AWS for any **running** EC2 instances created by this CLI.
3. **Notify:** Sends a **Telegram notification** with the count of active servers.

### 📂 Pipeline Files
* **`Jenkinsfile`**: Defines the pipeline, manages credentials (AWS & Telegram), and sets up the environment.
* **`instance_status_check.py`**: Python script that performs the logic:
    *   Connects to AWS via Boto3.
    *   Filters instances by tag `CreatedBy=Nadav-Platform-CLI`.
    *   Sends a formatted report to your Telegram chat.

### 💬 Example Notification
> 🤖 **Jenkins Report:**
> Date: 2023-10-27 17:00:01
> Pipeline finished successfully!
> Currently, there are **2 active servers** made by the platform in AWS.
> *Don't forget to shut them down to save costs, by running 'awsctl ec2 cleanup'.*
---
Developed by Nadav Kamar | DevOps Engineer
