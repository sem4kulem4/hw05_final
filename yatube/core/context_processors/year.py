from datetime import datetime


def year(request):
    current_datetime = datetime.now()
    return {
        'year': current_datetime.year
    }
