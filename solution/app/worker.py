from app.models import DataStore, GameSale
import time

STATES = {
    'UPLOADING': 0,
    'READY': 1,
    'PAUSED': 2,
    'TERMINATED': 3
}

class Task:
    def __init__(self, user, file_id):
        self.__state = STATES['READY']
        self.user = user
        self.file_id = file_id
        self.processed_rows = 0
        self.progress = 0

    def csv_to_db(self):
        f = DataStore.objects.get(id=self.file_id, owner=self.user)

        self.set_state('UPLOADING')
        
        for line in f.csv.readlines()[5+self.processed_rows:-1]:
            try:
                if self.get_state():
                    raise Exception('Exception was Interrupted!')

                cleaned_line = line.strip().decode().split(',')
                print(cleaned_line[0],' --- ', line)
                if len(cleaned_line) == 11:
                    GameSale(
                        metadata     = f,
                        rank         = cleaned_line[0],
                        name         = cleaned_line[1],
                        platform     = cleaned_line[2],
                        year         = cleaned_line[3],
                        genre        = cleaned_line[4],
                        publisher    = cleaned_line[5],
                        na_sales     = cleaned_line[6],
                        eu_sales     = cleaned_line[7],
                        jp_sales     = cleaned_line[8],
                        other_sales  = cleaned_line[9],
                        global_sales = cleaned_line[10]
                    ).save()

                self.processed_rows += 1
                self.progress = self.processed_rows / (len(f.csv.readlines())- 6) * 100
            except Exception:
                break
            time.sleep(1)

        self.set_state('READY')


    def resume(self):
        self.set_state('UPLOADING')
        self.csv_to_db()
    
    def stop(self):
        self.set_state('TERMINATED')
        self.processed_rows = 0

        GameSale.objects.filter(metadata__id=self.file_id).delete()
    
    def get_progress(self):
        return self.progress
    
    def get_state(self):
        return self.__state
    
    def set_state(self, state):
        self.__state = STATES.get(state, 0)