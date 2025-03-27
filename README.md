# Guidance for FSx for Lustre Data Repository Task Scheduler

# FSx Lustre Data Repository Task Manager

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [IAM Permissions](#iam-permissions)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

## Overview

This tool facilitates the management of data repository tasks for FSx for Lustre file systems, enabling automated import and export operations between FSx and S3.

### Key Features
* Export data from FSx Lustre to S3
* Import metadata from S3 to FSx Lustre
* Generate detailed completion reports
* Supports both CLI and AWS Lambda deployment
* Comprehensive error handling and logging

## Prerequisites

* Python 3.x
* AWS credentials configured
* Required IAM permissions for FSx operations
* `boto3` library installed
* FSx for Lustre file system with configured Data Repository Association (DRA)

## Installation

1. Clone the repository
```bash
git clone https://github.com/[your-username]/fsx-lustre-drt-manager.git
cd fsx-lustre-drt-manager
```

2. Install dependencies
```bash
pip install boto3
```

## Usage

### Command Line Interface

#### Export Operation
```bash
python3 fsx_drt_manager.py export \
    --filesystem-id fs-xxxxxxxxxxxxxxxxx \
    --paths "/path1,/path2" \
    --completion-report-path "/fsx-drt-completion-reports"
```

#### Import Operation
```bash
python3 fsx_drt_manager.py import \
    --filesystem-id fs-xxxxxxxxxxxxxxxxx \
    --paths "/path1,/path2" \
    --completion-report-path "/fsx-drt-completion-reports"
```

### AWS Lambda Deployment

1. Package the script
```bash
zip -r function.zip fsx_drt_manager.py
```

2. Lambda Configuration
   * Runtime: Python 3.x
   * Handler:
     * Export: `fsx_drt_manager.export`
     * Import: `fsx_drt_manager.import_data`

3. Environment Variables Setup
```plaintext
filesystemid=fs-xxxxxxxxxxxxxxxxx
type=EXPORT
completionreportpath=/fsx-drt-completion-reports
paths=/path1,/path2
```

## IAM Permissions

Required IAM policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "fsx:CreateDataRepositoryTask",
                "fsx:DescribeDataRepositoryAssociations",
                "fsx:DescribeFileSystems"
            ],
            "Resource": "*"
        }
    ]
}
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `filesystemid` | FSx Lustre filesystem ID | `fs-0106408057ce30716` |
| `type` | Operation type | `EXPORT` or `IMPORT` |
| `completionreportpath` | Report location | `/fsx-drt-completion-reports` |
| `paths` | Paths to process | `/path1,/path2` |

## Completion Reports

Reports are generated in CSV format (`REPORT_CSV_20191124`) containing:
* Failed operations only
* Detailed status information
* Operation timestamps
* Error messages (if applicable)

## Error Handling

The script handles multiple error scenarios:

* Missing environment variables
* AWS credential issues
* FSx API errors
* DRA configuration issues
* Task execution failures

## Contributing

1. Fork the repository
2. Create feature branch
```bash
git checkout -b feature/NewFeature
```
3. Commit changes
```bash
git commit -m 'Add NewFeature'
```
4. Push to branch
```bash
git push origin feature/NewFeature
```
5. Open Pull Request

## License

MIT License

```plaintext
Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Version History

### 1.0.0 (2025-03-27)
* Initial release
* Import/Export functionality
* CLI support
* Lambda deployment support
* Comprehensive error handling
* Detailed completion reports

## Support

* Open an issue for bug reports
* Feature requests welcome
* Pull requests encouraged

## Authors

**Romi Asad, romiasad@amazon.com, GitHub: [@yourusername]**
**Tom McDonald, tjm@amazon.com, GitHub: tjmaws**

## Acknowledgments

* AWS FSx for Lustre team
* Open source community
* Original Project contributors
**Darryl Osborne, darrylo@amazon.com,**
**Shrinath Kurdekar, kurdekar@amazon.com, GitHub: Shrinath Kurdekar**

---

*Last updated: March 27, 2025*

