from django.core.management.base import BaseCommand
import pandas as pd, numpy as np
from datetime import datetime, timedelta
from resource_predictor.models import ResourceMetric

class Command(BaseCommand):
    help = 'Generate synthetic resource data'

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=240)

    def handle(self, *args, **options):
        hours = options['hours']
        now = datetime.utcnow()
        timestamps = [now - timedelta(hours=h) for h in range(hours)][::-1]
        cpu = (50 + 20*np.sin(np.linspace(0,6*np.pi,hours)) + np.random.normal(0,5,hours)).clip(0,100)
        mem = (60 + 10*np.sin(np.linspace(0,3*np.pi,hours)) + np.random.normal(0,3,hours)).clip(0,100)
        storage = (100 + np.cumsum(np.random.normal(0.1,0.5,hours))).clip(0)
        ResourceMetric.objects.all().delete()
        objs = [ResourceMetric(timestamp=t, cpu_usage=float(c), memory_usage=float(m), storage_usage=float(s))
                for t,c,m,s in zip(timestamps,cpu,mem,storage)]
        ResourceMetric.objects.bulk_create(objs)
        self.stdout.write(self.style.SUCCESS(f"Created {len(objs)} records"))
