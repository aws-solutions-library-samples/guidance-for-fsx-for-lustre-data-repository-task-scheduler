#!/usr/bin/env python3

# Copyright (c) 2025 Amazon.com
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
FSx Lustre Data Repository Task Manager
A tool for managing FSx Lustre data repository tasks (import/export operations)
"""

import boto3
import textwrap
import botocore
import json
import os
import sys
import shlex
import logging
import argparse
from datetime import datetime

__author__ = "romiasad@ and tjm@"
__copyright__ = "Copyright 2025, Amazon.com"
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Tom McDonald"
__email__ = "tjm@amazon.com"
__status__ = "Production"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def validate_env_vars(required_vars):
    """Validate required environment variables exist"""
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
    return {var: os.environ[var] for var in required_vars}

def get_s3_path_from_dra(filesystemId):
    """Get the S3 path from Data Repository Association"""
    try:
        fsx = boto3.client('fsx')
        response = fsx.describe_data_repository_associations(
            Filters=[{
                'Name': 'file-system-id',
                'Values': [filesystemId]
            }]
        )
        
        if not response['Associations']:
            raise ValueError("No Data Repository Associations found")
            
        for assoc in response['Associations']:
            if assoc['Lifecycle'] == 'AVAILABLE':
                return assoc['DataRepositoryPath']
                
        raise ValueError("No AVAILABLE Data Repository Associations found")
        
    except Exception as e:
        logger.error(f"Error getting S3 path from DRA: {str(e)}")
        raise

def export(event, context):
    """Export function for data repository task"""
    try:
        fsx = boto3.client('fsx')
        
        required_params = ['file_system_id', 'paths', 'completion_report_path']
        missing_params = [p for p in required_params if p not in event]
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

        file_system_id = event['file_system_id']
        fsx_paths = event['paths']
        completion_report_path = event['completion_report_path']
        
        # Always use FAILED_FILES_ONLY as it's the only supported value
        report_scope = 'FAILED_FILES_ONLY'
        logger.info(f"Note: Only FAILED_FILES_ONLY is supported for report scope")
        
        # Get S3 path for the report
        dra_details = get_dra_details(file_system_id)
        s3_base_path = dra_details['s3_path'].rstrip('/')
        
        task_params = {
            'FileSystemId': file_system_id,
            'Type': 'EXPORT_TO_REPOSITORY',
            'Paths': fsx_paths,
            'Report': {
                'Enabled': True,
                'Path': f"{s3_base_path}{completion_report_path}",
                'Format': 'REPORT_CSV_20191124',
                'Scope': report_scope
            }
        }
        
        logger.info("API call parameters:")
        logger.info(json.dumps(task_params, indent=2))
        logger.info("CLI equivalent:")
        cli_command = (
            f"aws fsx create-data-repository-task"
            f" --file-system-id {file_system_id}"
            f" --type EXPORT_TO_REPOSITORY"
            f" --paths {','.join(fsx_paths)}"
            f" --report Enabled=true,Path={s3_base_path}{completion_report_path},"
            f"Format=REPORT_CSV_20191124,Scope={report_scope}"
        )
        logger.info(cli_command)
        
        try:
            response = fsx.create_data_repository_task(**task_params)
            logger.info(f"Created repository task: {response}")
            return response
        except botocore.exceptions.ClientError as e:
            logger.error(f"Botocore error occurred: {str(e)}")
            if 'ResponseMetadata' in e.response:
                logger.error(f"Error response metadata: {e.response['ResponseMetadata']}")
            raise
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        logger.debug(f"Full error details: {str(e)}", exc_info=True)
        raise


def get_dra_details(filesystemId):
    """Get Data Repository Association details"""
    try:
        fsx = boto3.client('fsx')
        response = fsx.describe_data_repository_associations(
            Filters=[{
                'Name': 'file-system-id',
                'Values': [filesystemId]
            }]
        )
        
        if not response['Associations']:
            raise ValueError("No Data Repository Associations found")
            
        for assoc in response['Associations']:
            if assoc['Lifecycle'] == 'AVAILABLE':
                return {
                    's3_path': assoc['DataRepositoryPath'],
                    'fsx_path': assoc['FileSystemPath']
                }
                
        raise ValueError("No AVAILABLE Data Repository Associations found")
        
    except Exception as e:
        logger.error(f"Error getting DRA details: {str(e)}")
        raise

def import_data(event, context):
    try:
        fsx = boto3.client('fsx')
        
        required_params = ['file_system_id', 'paths', 'completion_report_path']
        missing_params = [p for p in required_params if p not in event]
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

        file_system_id = event['file_system_id']
        s3_path = event['paths'][0]
        completion_report_path = event['completion_report_path']
        
        # Always use FAILED_FILES_ONLY as it's the only supported value
        report_scope = 'FAILED_FILES_ONLY'
        logger.info(f"Note: Only FAILED_FILES_ONLY is supported for report scope")
        
        task_params = {
            'FileSystemId': file_system_id,
            'Type': 'IMPORT_METADATA_FROM_REPOSITORY',
            'Paths': [s3_path],
            'Report': {
                'Enabled': True,
                'Path': f"s3://snowytrail/fsxl-drt-testing{completion_report_path}",
                'Format': 'REPORT_CSV_20191124',
                'Scope': report_scope
            }
        }
        
        logger.info("API call parameters:")
        logger.info(json.dumps(task_params, indent=2))
        logger.info("CLI equivalent:")
        cli_command = (
            f"aws fsx create-data-repository-task"
            f" --file-system-id {file_system_id}"
            f" --type IMPORT_METADATA_FROM_REPOSITORY"
            f" --paths {s3_path}"
            f" --report Enabled=true,Path=s3://snowytrail/fsxl-drt-testing{completion_report_path},"
            f"Format=REPORT_CSV_20191124,Scope={report_scope}"
        )
        logger.info(cli_command)
        
        try:
            response = fsx.create_data_repository_task(**task_params)
            logger.info(f"Created repository task: {response}")
            return response
        except botocore.exceptions.ClientError as e:
            logger.error(f"Botocore error occurred: {str(e)}")
            if 'ResponseMetadata' in e.response:
                logger.error(f"Error response metadata: {e.response['ResponseMetadata']}")
            raise
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        logger.debug(f"Full error details: {str(e)}", exc_info=True)
        raise

def cli_handler():
    """Handle CLI execution"""
    parser = argparse.ArgumentParser(
        description='FSx Lustre Data Repository Task Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
            Notes:
              - For report-scope, only FAILED_FILES_ONLY is supported by the FSx API
              - Paths for import should be in S3 format (e.g., s3://bucket/prefix/)
              
            Examples:
              Import from S3:
                %(prog)s import --filesystem-id fs-0123456789 \\
                    --paths s3://bucket/prefix/ \\
                    --completion-report-path "/report-path" \\
                    --report-scope FAILED_FILES_ONLY
                    
              Export to S3:
                %(prog)s export --filesystem-id fs-0123456789 \\
                    --paths "/fsx-path" \\
                    --completion-report-path "/report-path" \\
                    --report-scope FAILED_FILES_ONLY
        ''')
    )
    
    parser.add_argument('action', 
                       choices=['import', 'export'], 
                       help='Action to perform')
    parser.add_argument('--filesystem-id', 
                       required=True, 
                       help='FSx filesystem ID')
    parser.add_argument('--paths', 
                       required=True, 
                       help='For import: S3 path (e.g., s3://bucket/prefix/)\n'
                            'For export: FSx path (e.g., /fsx-path)')
    parser.add_argument('--completion-report-path', 
                       required=True, 
                       help='Path for completion report (e.g., "/fsx-drt-completion-reports")')
    parser.add_argument('--report-scope', 
                       default='FAILED_FILES_ONLY',
                       help='Report scope (Note: only FAILED_FILES_ONLY is supported, other values will be ignored)')
    args = parser.parse_args()

    try:
        # Check if user tried to use ALL_FILES and warn them
        if args.report_scope != 'FAILED_FILES_ONLY':
            logger.warning(f"Report scope '{args.report_scope}' is not supported. Using FAILED_FILES_ONLY instead.")
        
        # Validate filesystem ID
        if not args.filesystem_id.startswith('fs-'):
            raise ValueError("Invalid filesystem ID format. Must start with 'fs-'")

        # For import, verify S3 path format
        if args.action == 'import' and not args.paths.startswith('s3://'):
            # Get DRA details to convert FSx path to S3 path
            dra_details = get_dra_details(args.filesystem_id)
            s3_base_path = dra_details['s3_path'].rstrip('/') + '/'
            paths = [s3_base_path]
        else:
            paths = [args.paths]

        # Create event dictionary for the functions
        event = {
            'file_system_id': args.filesystem_id,
            'paths': paths,
            'completion_report_path': args.completion_report_path,
            'report_scope': 'FAILED_FILES_ONLY'  # Always use FAILED_FILES_ONLY
        }

        logger.info(f"Action: {args.action}")
        logger.info(f"FileSystem ID: {event['file_system_id']}")
        logger.info(f"Paths: {event['paths']}")
        logger.info(f"Completion Report Path: {event['completion_report_path']}")
        logger.info(f"Report Scope: {event['report_scope']} (only supported value)")

        # Execute requested action
        if args.action == 'export':
            return export(event, None)
        else:
            return import_data(event, None)

    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in cli_handler: {str(e)}")
        sys.exit(1)


    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in cli_handler: {str(e)}")
        sys.exit(1)



if __name__ == "__main__":
    setup_logging()
    
    try:
        # Verify AWS credentials
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        logger.info(f"AWS Identity: {identity['Arn']}")
        
        # Run CLI handler
        result = cli_handler()
        print(result)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)



def list_s3_contents(s3_path):
    """List contents of S3 path"""
    try:
        # Parse bucket and prefix from s3 path
        s3_path = s3_path.replace('s3://', '')
        bucket = s3_path.split('/')[0]
        prefix = '/'.join(s3_path.split('/')[1:])
        
        s3 = boto3.client('s3')
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        return [obj['Key'] for obj in response.get('Contents', [])]
    except Exception as e:
        logger.error(f"Error listing S3 contents: {str(e)}")
        raise
