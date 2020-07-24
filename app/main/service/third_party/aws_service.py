import boto3
from botocore.exceptions import ClientError

from flask import current_app as app
from app.main.core.errors import BadRequestError, ServiceProviderError, ConfigurationError
from app.main.core.io import open_file
from app.main.model.docproc import DocprocChannel


def upload_to_docproc(src_filepath, desired_obj_name, desired_metadata=None):
    """ Uploads object to Docproc (Client docs dossier) S3 Bucket 
    
    :param src_filepath: the source path of the file
    :param desired_obj_name: the destination object name. If none given, the src_filename is used.
    :param desired_metadata: (optional) a dictionary representing metadata.
    """
    final_metadata = None
    if not app.s3_bucket_docproc:
        raise ConfigurationError('The app is missing DocProc bucket configuration. Please rectify and try again.')
    
    if not does_bucket_exist(app.s3_bucket_docproc):
        raise ServiceProviderError(f'That bucket {app.s3_bucket_docproc} does not exist at Service Provider.')

    if not src_filepath:
        raise BadRequestError('File path cannot be empty. Please correct this and try again.')
        
    if desired_metadata and isinstance(desired_metadata, dict):
        final_metadata['Metadata'] = desired_metadata
    
    s3 = boto3.client('s3')
    with open_file(src_filepath, 'rb') as data:
        s3.upload_fileobj(data, app.s3_bucket_docproc, desired_obj_name, ExtraArgs=final_metadata)

    return True


def download_from_docproc(src_channel, obj_name, dest_filepath):
    """ Gets the requested Object from Docproc (Client docs dossier) S3 Bucket """
    ## tmp: set default bucket
    bucket = app.s3_bucket_docproc
    if src_channel == DocprocChannel.MAIL.value:
        if not app.s3_bucket_docproc:
            raise ConfigurationError('The app is missing DocProc bucket configuration. Please rectify and try again.')
        bucket = app.s3_bucket_docproc

    if src_channel == DocprocChannel.FAX.value:
        if not app.s3_bucket_fax:
            raise ConfigurationError('The app is missing Fax bucket configuration. Please rectify and try again.')
        bucket = app.s3_bucket_fax
    
    if src_channel == DocprocChannel.EMAIL.value:
        if not app.s3_bucket_email:
            raise ConfigurationError('The app is missing Email bucket configuration. Please rectify and try again.')
        bucket = app.s3_bucket_email

    if not does_bucket_exist(bucket):
        raise ServiceProviderError('That bucket {bucket} does not exist at Service Provider.')

    if not obj_name:
        raise BadRequestError('Object name cannot be empty. Please correct this and try again.')

    if not dest_filepath:
        raise BadRequestError('Destination file path cannot be empty. Please correct this and try again.')
    
    s3 = boto3.client('s3')
    with open_file(dest_filepath, 'wb') as data:
        s3.download_fileobj(bucket, obj_name, data)

    return True


def copy_object(src_obj_name, src_bucket, dest_obj_name, dest_bucket):
    """ Copies an Object to another Bucket """
    s3 = boto3.resource('s3')
    fax_src = {
        'Bucket': src_bucket,
        'Key': src_obj_name
    }

    bucket = s3.Bucket(dest_bucket)
    try:
        bucket.copy(fax_src, dest_obj_name)

    except ClientError as e:
        raise ServiceProviderError('Could not copy Fax object to Docproc bucket, {}'.format(str(e)))

    return True


def does_bucket_exist(bucket):
    """ Checks whether a given bucket does in fact exist """
    s3 = boto3.client('s3')

    try:
        res = s3.list_buckets()
        avail_buckets = dict((i['Name'], i['CreationDate']) for i in res['Buckets'])

    except ClientError as e:
        raise ServiceProviderError('Could not list buckets, {}'.format(str(e)))

    return bucket in avail_buckets
  

