from django.db import models

# Create your models here.

class Brick(models.Model):
    name = models.CharField(max_length=100, unique=True, blank=False, null=False)
    shape = models.CharField(max_length=20, unique=True, blank=False, null=False)
    color = models.CharField(max_length=20, unique=True, blank=False, null=False)


class DetectionRequest(models.Model):
    SUBMITTED = 'SUBMITTED'
    RUNNING = 'RUNNING'
    FINISHED = 'FINISHED'
    ERROR = 'ERROR'
    STATUS_CHOICES = [
        (SUBMITTED, 'SUBMITTED'),
        (RUNNING, 'RUNNING'),
        (FINISHED, 'FINISHED'),
        (ERROR, 'ERROR'),
    ]
    timestamp = models.DateTimeField(auto_now_add=True)
    station_id = models.CharField(max_length=50)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=SUBMITTED,
    )
    image = models.ImageField(upload_to='saved_images/%Y/%m/%d')
    search_key = models.CharField(max_length=200, null=True)
    order_list = models.CharField(max_length=1000, null=True)
    result = models.CharField(max_length=1000, null=True)

    str2pretty = lambda self, x: 'None' if x == 'None' or x is None else str('<br />'.join([str(i) for i in eval(x)]))
    __str__ = lambda self: str(self.id) + ' | ' + str(
        self.timestamp) + ' | ' + self.station_id + ' | ' + self.status + ' | ' + str(self.search_key) + ' | ' + str(self.order_list) + ' | ' + self.str2pretty(self.result) + '<br />'
