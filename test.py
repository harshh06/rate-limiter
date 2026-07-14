from datetime import datetime
start_time = datetime(2026, 7, 13, 10, 30, 0)
end_time = datetime(2026, 7, 14, 13, 45, 30)
time_difference = end_time - start_time
print(time_difference.total_seconds())