from django.db import transaction
def f():
    with transaction.atomic():
        pass
