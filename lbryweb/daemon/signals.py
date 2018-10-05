from django.dispatch import Signal

download_started = Signal(providing_args=['account_id', 'uri', 'file_name' 'lbrynet_data'])
