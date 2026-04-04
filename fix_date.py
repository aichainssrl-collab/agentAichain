import locale
from datetime import datetime

# In Python we can just format it nicely.
d = datetime.now()
days = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
months = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

formatted = f"{days[d.weekday()]} {d.day} {months[d.month-1]} {d.year}"
print(formatted)
