from django.db import transaction
def do_tx():
    with transaction.atomic():
        x = 1+1
        return x
