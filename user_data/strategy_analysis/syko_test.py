import pandas as pd



print(pd.date_range(start='1/1/2000', end='1/02/2000', freq='H'))


date_ranges = pd.date_range(start='1/1/2000', end='1/02/2000', freq='H')
range_of_hour_minute = []

for i in range(1, date_ranges.size):
    print(date_ranges.hour[i])

print(datetime(10))