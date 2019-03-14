import re

under_list = [
    'Milan U19 — Spezia U19',
    'Chelsea U19 — Montpellier U19',
    'Vasco da Gama U20 — CS Paraibano U20',
    'AC Milan (w) — Juvenrus (w)',
    'Roma (w) — Fiorentina (w)',
    'Serbia U17 (w) — Russia U17 (w)',
    'Emmen (r)-Twente (r)',
    'Shanghai Shenhua (r)-Hebei China Fortune (r)',
    'Kingston City (U20) - Oakleigh Cannons (U20)',
    'Zbrojovka Brno (U21) - Sigma Olomouc (U21)',
    'Arsenal LFC (W) - Bristol Academy (W)',
    'Lobos BUAP (W) - Puebla (W)',
    'Antwerpen (res) - Standard Liège (res)',
    'Shanghai Shenhua (R) - Hebei China Fortun (R)',
    'Silkeborg IF (R) - Vendsyssel FF (Reserves)']

lower_list = [
'Milan — Spezia',
    'Chelsea — Montpellier',
    'Vasco da Gama — CS Paraibano',
    'AC Milan — Juvenrus',
    'Roma — Fiorentina',
    'Serbia — Russia ',
    'Emmen -Twente',
    'Shanghai Shenhua -Hebei China Fortune',
    'Kingston City - Oakleigh Cannons',
    'Zbrojovka Brno - Sigma Olomouc',
    'Arsenal LFC - Bristol Academy',
    'Lobos BUAP - Puebla',
    'Antwerpen - Standard Liège',
    'Shanghai Shenhua - Hebei China Fortun',
    'Silkeborg I - Vendsyssel FF'    
]    
    
# for u in under_list:
for u in lower_list:
    if re.search('(u\d{2}|\(w\)|\(r\)|\(res\)|\(Reserves\))', u.lower()):
        print('del: ' + u)
    else:
        print('add: ' + u)