from django.db import models

# Create your models here.


class DetectionRequest(models.Model):
    SUBMITTED = 'SUBMITTED'
    SHOTTING = 'SHOTTING'
    SEARCHING = 'SEARCHING'
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

    __str__ = lambda self: str(self.id) + '|' + str(
        self.timestamp) + '|' + self.station_id + '|' + self.status + '|' + str(self.order_list) + '|' + str(self.result
                                                                                                            ) + '<br />'
