import MySQLdb
import re

import dateutil.parser as dparser
from prova_info import extract
from prova_info2 import prova



info = '120,504 (Spain) (31 August 2002)'
infos = info.split('(')

admissions = infos[0]

if len(infos)>1:
	location = infos[1].replace(')','')

if len(infos)>2:
	date = infos[2].replace(')','')


#date
#extract(info)



#file_name = 'programmes_imdb.rdf'
#programmes_graph.serialize(file_name, format="xml")