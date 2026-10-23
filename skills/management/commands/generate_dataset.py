from django.core.management.base import BaseCommand
from skills.services.domain_mapping import DOMAIN_MAPPING
import pandas as pd
import numpy as np
import random

class Command(BaseCommand):
    help = 'Generate dummy dataset for skills module'

    def handle(self, *args, **options):
        self.stdout.write('🎯 Generating dummy dataset...')
        
        data = []
        for i in range(1, 101):
            primary_domain = random.choice(list(DOMAIN_MAPPING.keys()))
            marks = {}
            for domain, subjects in DOMAIN_MAPPING.items():
                if domain == primary_domain:
                    mean, std = 85, 8
                else:
                    mean, std = 50, 12
                for subj in subjects:
                    marks[subj] = int(np.random.normal(mean, std))
                    marks[subj] = max(0, min(100, marks[subj]))
            
            record = {'student_id': i, 'primary_domain': primary_domain, **marks}
            data.append(record)
        
        df = pd.DataFrame(data)
        df.to_csv('dataset/skills_dataset.csv', index=False)
        self.stdout.write(self.style.SUCCESS('✅ Dataset generated successfully!'))