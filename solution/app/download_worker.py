from app.models import DataStore, GameSale
import time
import csv
from django.conf import settings
import os
from django.contrib.admin.utils import label_for_field


STATES = {
    'DOWNLOADING': 0,
    'READY': 1,
    'PAUSED': 2,
    'TERMINATED': 3
}


class DownloadTask:
    def __init__(self, user, file_id, from_year):
        self.__state = STATES['READY']
        self.user = user
        self.file_id = file_id
        self.from_year = from_year
        self.processed_rows = 0
        self.progress = 0

    def db_to_csv(self):
        self.set_state('DOWNLOADING')
        if (self.file_id != None and self.from_year != None):
            f = DataStore.objects.get(id=self.file_id)
            queryset = GameSale.objects.filter(metadata=f, metadata__owner=self.user, year__gt=self.from_year)

        elif (self.file_id != None and self.from_year == None):
            f = DataStore.objects.get(id=self.file_id, owner=self.user)
            queryset = GameSale.objects.filter(metadata=f)
        
        elif (self.file_id == None and self.from_year != None):
            queryset = GameSale.objects.filter(year__gt=self.from_year, metadata__owner=self.user)
        
        else:
            DataStore.objects.get(owner=self.user)
            queryset = GameSale.objects.all()

        if len(queryset) == 0:
            return
        
        opts = queryset.model._meta
        model = queryset.model
        field_names = [field.name for field in opts.fields if field.name != "metadata" and field.name != "id"]
        
        if self.processed_rows == 0:
            with open(f'{settings.BASE_DIR}{settings.MEDIA_URL}{self.user.username}_export_game_sale.csv', 'w', newline='') as csv_file:
                # the csv writer
                writer = csv.writer(csv_file)
            
                # Write a first row with header information
                writer.writerow(field_names)

        
        with open(f'{settings.BASE_DIR}{settings.MEDIA_URL}{self.user.username}_export_game_sale.csv', 'a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            for obj in queryset[self.processed_rows:]:
                try:
                    if self.get_state():
                        raise Exception('Throw an interrupt!')
                    
                    # Write data rows
                    writer.writerow([getattr(obj, field) for field in field_names])
                    print(obj.rank,' --- ' , obj)
                    self.processed_rows += 1
                    self.progress = round(self.processed_rows / len(queryset) * 100, 2)
                
                except Exception as e:
                    # print(e)
                    csv_file.close()
                    return
                time.sleep(1)

            self.set_state('READY')

    def pause(self):
        if self.get_state() == STATES['DOWNLOADING']:
            self.set_state('PAUSED')

    def resume(self):
        if self.get_state() == STATES['PAUSED']:
            self.set_state('DOWNLOADING')
            self.db_to_csv()
    
    def stop(self):
        if self.get_state() != STATES['READY']:
            self.set_state('TERMINATED')
            self.processed_rows = 0

        try:
            os.remove(f'{settings.BASE_DIR}{settings.MEDIA_URL}{self.user.username}_export_game_sale.csv')
        except FileNotFoundError as e:
            print(e)
        
    
    def get_progress(self):
        return self.progress
    
    def get_state(self):
        return self.__state
    
    def set_state(self, state):
        self.__state = STATES.get(state, 0)