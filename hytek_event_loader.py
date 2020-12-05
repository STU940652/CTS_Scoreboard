import csv
import pickle
import traceback
import copy

# 6 #1 Girls 8 & Under 100 Yard Medley Relay
# 7 #1   ...   (Girls 8 & Under 100 Yard Medley Relay)
# 92 Lane
# 93 Team
# 94
# 95 Relay
# 96 Seed Time
# 97 Heat   1 of 1   Finals
# 98 3
# 99 SCAY-MA
# 101 A
# 102 1:18.60
# 105 Staniar, Molly 8
# 106 Barshinger, Sawyer 8
# 107 Kifer, Helen 8
# 108 Siekman, Gabrielle N 8
#

# 6 #6 Boys 9 & Over 200 Yard Freestyle
# 7 #6   ...   (Boys 9 & Over 200 Yard Freestyle)
# 62 2:45.99
# 63 9-10 DIST
# 64 2:32.49
# 65 11-12 DIST
# 66 2:12.99
# 67 13-14 DIST
# 68 1:59.99
# 69 15&O DIST
# 92 Lane
# 93 Name
# 94 Age
# 95   Team
# 96 Seed Time
# 97 Heat   1 of 1   Finals
# 98 5
# 99 Weaver, Madden
# 100  10
# 101 SCAY-MA
# 102 2:25.28
# 104 DIST

class HytekEventLoader ():
    max_display_string_length = 0
    
    def __init__( self, file_name = None):
        self.event_names = {}
        self.events = {}
        self.events_uncombined = {}
        self.combined = {}
        if file_name:
            self.load( file_name)

    def clear( self):
        self.event_names.clear()
        self.events.clear()
        self.events_uncombined = copy.deepcopy(self.events)
        self.combined.clear()
        self.max_display_string_length = 0
            
    def load( self, file_name):
        self.clear()
        with open(file_name, "rt") as schedule_file:
            self.load_from_file( schedule_file)

    def load_from_bytestream( self, stream):
        self.load_from_file( [x.decode('utf8') for x in stream])
        
    def load_from_file( self, schedule_file):
        self.clear()
        reader = csv.reader( schedule_file)
        for row in reader:           
            # Hack to remove whitespaces
            for i in range(len(row)):
                row[i]=row[i].strip()
            
            event_number_name = row[6]
            if event_number_name.startswith("#"): event_number_name = event_number_name[1:]
            if event_number_name.startswith("Event "): event_number_name = event_number_name[6:]
            event_number, event_name = event_number_name.strip().split(' ',1)
            event_number = int(event_number.strip())
            self.event_names[event_number] = event_name.strip()
            
            lane_header = row.index("Lane",60,107)
            column_offset = 6
            while (column_offset < 9):
                try:
                    int(row[lane_header+column_offset])
                except ValueError:
                    column_offset += 1
                    continue
                break
            
            lane_column = lane_header+column_offset
            heat_number = int(row[lane_column-1].split()[1])            
            lane = int(row[lane_column])
            team = row[row.index("Team",lane_header,107)+column_offset]

            if "Name" in row[lane_header:107]:   
                # Indv
                name = ' '.join(reversed(row[row.index("Name",lane_header,107)+column_offset].split(','))).strip()
                display_string = (team + '    ')[:4] + ' ' + name
            elif "Relay" in row[lane_header:107]:
                # Relay
                display_string = team
            else:
                display_string = ""

            self.max_display_string_length = max(self.max_display_string_length, len(display_string))

            if (event_number, heat_number) not in self.events:
                self.events[(event_number, heat_number)] = {}
                
            self.events[(event_number, heat_number)][lane] = display_string
            
        self.events_uncombined = copy.deepcopy(self.events)
    
    def combine_events(self, combined=None):
        if combined != None:
            self.combined=combined
        self.events = copy.deepcopy(self.events_uncombined)
        
        for combine_source, combine_destination in self.combined.items():
            if (combine_source != combine_destination):
                for lane in self.events[combine_source]:
                    self.events[combine_destination][lane] = self.events[combine_source][lane] + '*'
                del self.events[combine_source]
        
    def get_event_name( self, event_number):
        try:
            return self.event_names[event_number]
        except:
            return ""
            
    def get_display_string( self, event_number, heat_number, lane):
        try:
            return self.events[ (event_number, heat_number) ][lane]
        except:
            pass
        return ""
            
    def get_display_string_uncombined( self, event_number, heat_number, lane):
        try:
            return self.events_uncombined[ (event_number, heat_number) ][lane]
        except:
            pass
        return ""
            
    def to_object( self):
        return pickle.dumps({
            "event_names": self.event_names, 
            "events": self.events,
            "events_uncombined": self.events_uncombined,
            "combined": self.combined,
        }, protocol=0).decode('utf8')
        
    def from_object( self, p):
        #try:
            o = pickle.loads(p.encode('utf8'))
            self.event_names = o['event_names']
            self.events = o['events']
            self.events_uncombined = o['events_uncombined']
            self.combined = o['combined']
        #except:
        #    pass
            
if __name__ == "__main__":
    import sys
    event_info = HytekEventLoader(sys.argv[1])
    
    event_info.combined[(2,1)] = (1,1)
    event_info.combined[(4,1)] = (3,1)
    event_info.combined[(6,1)] = (5,1)
    event_info.combined[(7,1)] = (5,1)
    event_info.combine_events()
    
    event_heat = list(event_info.events.keys())
    event_heat.sort()
    for event, heat in event_heat:
        print ("Event", event, " Heat", heat, end=" ")
        if event in event_info.event_names:
            print (event_info.event_names[event])
        else:
            print ("")

        lanes = list(event_info.events[(event, heat)].keys())
        lanes.sort()
        for lane in lanes:
            print ("\t", lane, "\t", event_info.events[(event, heat)][lane])
