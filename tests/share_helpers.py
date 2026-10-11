from uuid import uuid4


def consent_payload(day=None):
    return {'day': day, 'consent': True, 'consent_version': 'weekly-live-v1', 'request_id': str(uuid4())}


def consent_args():
    data = consent_payload()
    data.pop('day')
    return data
