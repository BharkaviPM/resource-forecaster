from django.db import models

# Create your models here.
class ResourceMetric(models.Model):
    timestamp = models.DateTimeField(unique=True)
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    storage_usage = models.FloatField()

    def __str__(self):
        return f"{self.timestamp}: CPU {self.cpu_usage}%"
