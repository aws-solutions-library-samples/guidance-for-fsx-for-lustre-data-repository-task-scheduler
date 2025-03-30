#!/usr/bin/env python3

import boto3
import botocore
import json
import os
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG
)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def serialize_datetime(obj):
    """Convert datetime objects in a dict to ISO format strings"""
    if isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def validate_env_vars(required_vars):
    """Validate required environment variables exist"""
    logger.debug(f"Validating environment variables: {required_vars}")
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
    return {var: os.environ[var] for var in required_vars}

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

def create_data_repository_task(task_type, file_system_id, paths, completion_report_path):
    """Create a data repository task"""
    try:
        fsx = boto3.client('fsx')
        
        # Get DRA details and validate
        logger.info(f"Getting DRA details for filesystem: {file_system_id}")
        dra_details = get_dra_details(file_system_id)
        logger.info(f"DRA details retrieved: {json.dumps(dra_details)}")
        
        s3_base_path = dra_details['s3_path'].rstrip('/')
        fsx_base_path = dra_details['fsx_path'].rstrip('/')
        
        # Debug logging
        logger.info(f"S3 base path: {s3_base_path}")
        logger.info(f"FSx base path: {fsx_base_path}")
        logger.info(f"Input paths: {paths}")
        logger.info(f"Task type: {task_type}")
        
        # Construct paths based on task type
        if task_type == 'EXPORT_TO_REPOSITORY':
            # For export, use FSx paths
            task_paths = [fsx_base_path]
        else:
            # For import, use the exact path from DRA
            task_paths = [dra_details['s3_path']]  # Use the exact path from DRA
        
        logger.info(f"Final task paths: {task_paths}")
        
        task_params = {
            'FileSystemId': file_system_id,
            'Type': task_type,
            'Paths': task_paths,
            'Report': {
                'Enabled': True,
                'Path': f"{s3_base_path}{completion_report_path}",
                'Format': 'REPORT_CSV_20191124',
                'Scope': 'FAILED_FILES_ONLY'
            }
        }
        
        logger.info(f"Creating data repository task with parameters: {json.dumps(task_params)}")
        
        response = fsx.create_data_repository_task(**task_params)
        logger.info(f"Successfully created repository task: {json.dumps(response, cls=DateTimeEncoder)}")
        return serialize_datetime(response)
        
    except botocore.exceptions.ClientError as e:
        logger.error(f"AWS API error: {str(e)}")
        if 'ResponseMetadata' in e.response:
            logger.error(f"Error response metadata: {json.dumps(e.response['ResponseMetadata'])}")
        raise
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        raise

def handler(event, context):
    """Main handler function"""
    try:
        logger.info(f"Starting handler with event: {json.dumps(event)}")
        
        # Get environment variables
        env_vars = validate_env_vars(['FILE_SYSTEM_ID', 'TASK_TYPE', 'COMPLETION_REPORT_PATH', 'FSX_PATHS'])
        logger.info(f"Environment variables loaded: {json.dumps(env_vars)}")
        
        file_system_id = env_vars['FILE_SYSTEM_ID']
        task_type = env_vars['TASK_TYPE']
        completion_report_path = env_vars['COMPLETION_REPORT_PATH']
        paths = [env_vars['FSX_PATHS']]  # Convert single path to list
        
        return create_data_repository_task(task_type, file_system_id, paths, completion_report_path)
        
    except Exception as e:
        logger.error(f"Unhandled exception in handler: {str(e)}", exc_info=True)
        raise