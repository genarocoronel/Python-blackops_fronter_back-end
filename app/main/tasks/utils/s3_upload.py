import boto3


def upload_test_voice_recording():
    s3 = boto3.client('s3')

    source_filename = '2020-03-06T094441_call_8185026458_+18582660725_85c7b417-3c90-4091-9de5-a7b65d4d43d0.mp3'

    with open('/Users/KeithHomco/Downloads/%s' % source_filename, 'rb') as data:
        dest_filename = '2020-03-08T094445~call~8185026458~+18582660725~85c7b417-3c90-4091-9de5-a7b65d4d43d0.mp3'
        s3.upload_fileobj(data, 'dss-call-recordings', '2020/03/08/%s' % dest_filename, ExtraArgs={
            "Metadata": {
                "caller_id_name": "TRAVELERS CO",
                "caller_id_number": "8185026458",
                "from": "8185026458",
                "dialed_number": "+18582660725",
                "to": "+18582660725",
                "recording_id": "831476fd-cb97-4c6c-ae27-03aed9c2f702",
                "resource_group_id": "3854c498-b7d3-4045-b79f-86d90d52b40d",
                "timestamp": "1583516681083",
                "timezone": "US/Pacific",
                "type": "call",
            }})


if __name__ == '__main__':
    upload_test_voice_recording()
