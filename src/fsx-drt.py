# MIT License
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
import os
import sys
import shlex
import logging
import argparse
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def setup_logging():
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

def get_completion_report_path(filesystemId, completionReportPath):
    """Get S3 path for completion report based on DRA configuration"""
    logger.info("Calling get_completion_report_path...")
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
                s3_path = assoc['DataRepositoryPath']
                s3_path = s3_path.rstrip('/')
                full_path = f"{s3_path}{completionReportPath}"
                logger.info(f"Completion report path: {full_path}")
                return full_path
                
        raise ValueError("No AVAILABLE Data Repository Associations found")
        
    except Exception as e:
        logger.error(f"Error in get_completion_report_path: {str(e)}")
        raise

def export(event, context):
    """Export function for data repository task"""
    try:
        # Validate environment variables
        required_vars = ['filesystemid', 'type', 'completionreportpath', 'paths']
        env_vars = validate_env_vars(required_vars)
        
        filesystemId = env_vars['filesystemid']
        type = env_vars['type']
        completionReportPath = env_vars['completionreportpath']
        paths = shlex.split(env_vars['paths'])

        logger.info(f"FileSystemId: {filesystemId}")
        logger.info(f"Type: {type}")
        logger.info(f"Completion Report Path: {completionReportPath}")
        logger.info(f"Paths: {paths}")

        # Create export task
        fsx = boto3.client('fsx')
        report_path = get_completion_report_path(filesystemId, completionReportPath)
        response = fsx.create_data_repository_task(
            Type='EXPORT_TO_REPOSITORY',
            FileSystemId=filesystemId,
            Paths=paths,
            Report={
                'Enabled': True,
                'Path': report_path,
                'Format': 'REPORT_CSV_20191124',
                'Scope': 'FAILED_FILES_ONLY'
            }
        )
        logger.info(f"Created export task: {response}")
        return response

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise

def import_data(event, context):
    """Import function for data repository task"""
    try:
        # Validate environment variables
        required_vars = ['filesystemid', 'type', 'completionreportpath', 'paths']
        env_vars = validate_env_vars(required_vars)
        
        filesystemId = env_vars['filesystemid']
        type = env_vars['type']
        completionReportPath = env_vars['completionreportpath']
        paths = shlex.split(env_vars['paths'])

        logger.info(f"FileSystemId: {filesystemId}")
        logger.info(f"Type: {type}")
        logger.info(f"Completion Report Path: {completionReportPath}")
        logger.info(f"Paths: {paths}")

        # Create import task
        fsx = boto3.client('fsx')
        report_path = get_completion_report_path(filesystemId, completionReportPath)
        response = fsx.create_data_repository_task(
            Type='IMPORT_METADATA_FROM_REPOSITORY',
            FileSystemId=filesystemId,
            Paths=paths,
            Report={
                'Enabled': True,
                'Path': report_path,
                'Format': 'REPORT_CSV_20191124',
                'Scope': 'FAILED_FILES_ONLY'
            }
        )
        logger.info(f"Created import task: {response}")
        return response

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise

def cli_handler():
    """Handle CLI execution"""
    parser = argparse.ArgumentParser(description='FSx Lustre Data Repository Task Manager')
    parser.add_argument('action', choices=['import', 'export'], help='Action to perform')
    parser.add_argument('--filesystem-id', required=True, help='FSx filesystem ID')
    parser.add_argument('--paths', required=True, help='Comma-separated list of paths')
    parser.add_argument('--completion-report-path', required=True, help='Path for completion report')
    args = parser.parse_args()

    # Set environment variables for the functions
    os.environ['filesystemid'] = args.filesystem_id
    os.environ['type'] = args.action.upper()
    os.environ['completionreportpath'] = args.completion_report_path
    os.environ['paths'] = args.paths

    # Execute requested action
    if args.action == 'export':
        return export({}, None)
    else:
        return import_data({}, None)

if __name__ == "__main__":
    setup_logging()
    
    # Verify AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        logger.info(f"AWS Identity: {identity['Arn']}")
    except Exception as e:
        logger.error(f"AWS credentials error: {str(e)}")
        sys.exit(1)

    # Run CLI handler
    result = cli_handler()
    print(result)

