from datetime import datetime

from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    return {'year': datetime.now(timezone.utc).year, }
