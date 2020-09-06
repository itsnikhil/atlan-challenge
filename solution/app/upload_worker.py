from app.models import DataStore, GameSale
import time

# Possible states
STATES = {
    'UPLOADING': 0,
    'READY': 1,
    'PAUSED': 2,
    'TERMINATED': 3
}


class UploadTask:
    """
        State Machine class which is responsible for handling upload task states
    """
    def __init__(self, user, file_id):
        self.__state = STATES['READY']
        self.user = user
        self.file_id = file_id
        self.processed_rows = 0
        self.progress = 0
        self.bytes_read = 0

    def csv_to_db(self):
        """
            Method to convert csv file to database records line by line
        """
        f = DataStore.objects.get(id=self.file_id, owner=self.user)

        self.set_state('UPLOADING')
        
        # Read line
        for line in f.csv.readlines()[5+self.processed_rows:-1]:
            self.bytes_read += len(line)
            self.processed_rows += 1
            
            try:
                # Interupt signal to stop execution
                if self.get_state():
                    raise Exception('Throw an interrupt!')
                
                # Split csv by delimeter
                cleaned_line = line.strip().decode().split(',')
                print(cleaned_line[0],' --- ', line)
                if len(cleaned_line) == 11:
                    try:
                        # Save record
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
                    except Exception:
                        pass
                
                self.progress = round((self.bytes_read / f.csv.size) * 100, 2)
            except Exception as e:
                # print(e)
                return
            
            # time.sleep(1)

        # Signal task completed
        self.set_state('READY')

    def pause(self):
        """
            Transition to pause state from uploading state
        """
        if self.get_state() == STATES['UPLOADING']:
            self.set_state('PAUSED')

    def resume(self):
        """
            Transition to uploading state from paused state
        """
        if self.get_state() == STATES['PAUSED']:
            self.set_state('UPLOADING')
            self.csv_to_db()
    
    def stop(self):
        """
            Rollback and transition to stop state if process is not completed so far.
        """
        if self.get_state() != STATES['READY']:
            self.set_state('TERMINATED')
            self.processed_rows = 0
            self.bytes_read = 0

            # Rollback
            GameSale.objects.filter(metadata__id=self.file_id).delete()
    
    def get_progress(self):
        """
            Progress getter 
        """
        return self.progress
    
    def get_state(self):
        """
            State getter 
        """
        return self.__state
    
    def set_state(self, state):
        """
            State setter 
        """
        self.__state = STATES.get(state, 0)