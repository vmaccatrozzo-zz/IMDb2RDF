import MySQLdb
import re
from rdflib import URIRef
from rdflib import Literal
from rdflib import BNode
from rdflib import Namespace
from rdflib.graph import Graph
from rdflib import plugin
from rdflib.serializer import Serializer
import dateutil.parser as dparser
import datetime
import csv



dc = Namespace("http://purl.org/dc/elements/1.1/")
dcterms = Namespace("http://purl.org/dc/terms/")
po = Namespace("http://purl.org/ontology/po/")
event =	Namespace("http://purl.org/NET/c4dm/event.owl#")
foaf =	Namespace("http://xmlns.com/foaf/0.1/")
rdf	= Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#')
skos =	Namespace('http://www.w3.org/2004/02/skos/core#')
imdb = Namespace('http://imdb.org/')
dbpedia = Namespace('http://dbpedia.org/ontology/')

db = MySQLdb.connect("127.0.0.1","root","","imdb2",use_unicode=True,charset='utf8')
cursor = db.cursor()


#create dictionaries

info_type=dict()
cursor.execute("SELECT * FROM info_type")
data = cursor.fetchall()
for row in data :
	info_type[row[0]]=row[1]
	
kind_type=dict()
cursor.execute("SELECT * FROM kind_type")
data = cursor.fetchall()
for row in data :
	kind_type[row[0]]=row[1]

link_type=dict()
cursor.execute("SELECT * FROM link_type")
data = cursor.fetchall()
for row in data :
	link_type[row[0]]=row[1]

company_type=dict()
cursor.execute("SELECT * FROM company_type")
data = cursor.fetchall()
for row in data :
	company_type[row[0]]=row[1]

company_name=dict()
cursor.execute("SELECT id, name FROM company_name")
data = cursor.fetchall()
for row in data :
	company_name[row[0]]=row[1]

role_type=dict()
cursor.execute("SELECT * FROM role_type")
data = cursor.fetchall()
for row in data :
	role_type[row[0]]=row[1]
	
comp_cast_type=dict()
cursor.execute("SELECT * FROM comp_cast_type")
data = cursor.fetchall()
for row in data :
	comp_cast_type[row[0]]=row[1]

keywords=dict()
cursor.execute("SELECT * FROM keyword")
data = cursor.fetchall()
for row in data :
	keywords[row[0]]=row[1]

db.close()

not_done = []
programmes_graph = Graph()
for movie_id in range(1,2531954):  
	try:	
		print movie_id
		programmes_graph = Graph()
		program_id = Literal(movie_id)
		program_url='program/%s' %movie_id
		program_uri = URIRef(imdb[program_url])
		db = MySQLdb.connect("127.0.0.1","root","","imdb2",use_unicode=True,charset='utf8')
		cursor = db.cursor()

		cursor.execute("SELECT title, kind_id, production_year, episode_of_id, season_nr, episode_nr, series_years FROM title WHERE id= %s",(movie_id))
		data = cursor.fetchall()
		for row in data :
			programmes_graph.add((program_uri,dc["title"],Literal(row[0])))
			kind_to_use=''
			kind = kind_type[row[1]]
			kind_splitted=kind.split()
			l=len(kind_splitted)
			if l>1:
				for i in range(1,l):
					kind_splitted[i]=kind_splitted[i].capitalize()
				for i in range(0,l):
					kind_to_use = kind_to_use + kind_splitted[i]
			else: 
				kind_to_use = kind.capitalize()
			programmes_graph.add((program_uri,rdf["type"], imdb[kind_to_use]))
			programmes_graph.add((imdb[kind_to_use],rdf["type"],imdb["Kind"]))
			programmes_graph.add((program_uri,po["pid"],program_id))
			programmes_graph.add((program_uri,dc["created"],Literal(row[2])))
			if row[3] != None:
				brand_url='program/%s' %row[3]
				brand_uri = URIRef(imdb[brand_url])
				programmes_graph.add((program_uri,po["episode"],brand_uri))
				programmes_graph.add((program_uri,imdb["seasonNr"],Literal(row[4])))
				programmes_graph.add((program_uri,imdb["episodeNr"],Literal(row[5])))
				#series_years = row[6]

		cursor.execute("SELECT id, info_type_id, info FROM movie_info WHERE movie_id= %s",(movie_id))
		data = cursor.fetchall()
		for row in data :
			location=''
			journal=''
			date=''
			title=''
			other_info=''
			id = row[0]
			type=info_type[row[1]].encode('utf-8')
			info=row[2].encode('utf-8')
			if type=='alternate versions':
				programmes_graph.add((program_uri,imdb["alternateVersions"],Literal(info)))
			if type=='goofs':
				programmes_graph.add((program_uri,imdb["goofs"],Literal(info)))
			if type=='crazy credits':
				programmes_graph.add((program_uri,imdb["crazyCredits"],Literal(info)))
			if type=='quotes':
				programmes_graph.add((program_uri,imdb["quotes"],Literal(info)))
			if type=='trivia':
				programmes_graph.add((program_uri,imdb["trivia"],Literal(info)))
			if type=='production dates':
				programmes_graph.add((program_uri,imdb["productionDates"],Literal(info)))
			if type=='copyright holder':
				copyrightHolder_url='copyrightHolder/%s' %info.decode('utf-8')
				copyrightHolder_uri = URIRef(imdb[copyrightHolder_url])
				programmes_graph.add((program_uri,dc["rightsHolder"],copyrightHolder_uri))
				programmes_graph.add((copyrightHolder_uri,rdf["type"],imdb['CopyrightHolder']))
			if type=='filming dates':
				programmes_graph.add((program_uri,imdb["filmingDates"],Literal(info)))
			if type=='opening weekend':
				programmes_graph.add((program_uri,imdb["openingWeekend"],Literal(info)))
			if type=='budget':
				programmes_graph.add((program_uri,imdb["budget"],Literal(info)))
			if type=='admissions':
				infos = info.split('(')
				bn = BNode ()
				programmes_graph.add((program_uri,imdb["admission"],bn))
				admissions = infos[0]
				programmes_graph.add((bn,imdb["admissions_number"],Literal(admissions)))
				if len(infos)>1:
					location = infos[1].replace(')','')
					location_url='location/%s' %location.decode('utf-8')
					location_url= location_url.replace('/ ' ,'/').replace(' ','_').replace('__','_')
					location_uri = URIRef(imdb[location_url])
					programmes_graph.add((bn,imdb["location"],location_uri))
					programmes_graph.add((location_uri,rdf["type"],imdb['Location']))	
				if len(infos)>2:
					date = infos[2].replace(')','')
					programmes_graph.add((bn,dc["created"],Literal(date)))
			if type=='gross':
				programmes_graph.add((program_uri,imdb["gross"],Literal(info)))
			if type=='rentals':
				programmes_graph.add((program_uri,imdb["rentals"],Literal(info)))
			if type=='weekend gross':
				programmes_graph.add((program_uri,imdb["weekendGross"],Literal(info)))
			if type=='book':
				info_url = 'book/%s' %id
				info_uri = URIRef(imdb[info_url])
				programmes_graph.add((program_uri,imdb["book"],info_uri))	
				programmes_graph.add((info_uri,rdf["type"],imdb['Book']))
				today = datetime.datetime.now().strftime('%d/%m/%Y')
				strings=[]
				if 'In: ' in info:
					author=''
					title=''
					strings = info.split('In: ')
					author_title = strings[0]
					rest = strings[1]
					if '"' in author_title:
						author_title=author_title.split('"')
						author = author_title[0]
						title = author_title[1].replace('"','')
					else:
						title = author_title.replace('"','')
					if '"' in author:
						title = author.split('"')[1]
						author=''
					rest=rest.split('"')
					if len(rest)>2:
						journal=rest[1]
						if len(rest)>3:
							other_info=rest[2]
							other_infos=rest[2].split(',')
							date=''
							other_info=''
							for other in other_infos:		
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info= other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
									other_infos = other_info.split('(')
							location=''
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
			
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')		
				elif 'by:' in info:
					date=''
					location=''
					other_info=''
					strings = info.split('by:')
					author_title = strings[1].split('"')
					journal_location = strings[0]		
					author = author_title[0]
					title = author_title[1]
					journal = ''
					if len(author_title)>2:
						other_infos = author_title[2].split(',')
						date=''
						other_info=''
						for other in other_infos:
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
								other_info = other_info
							except:
								date=date
								if other_info=='':
									other_info = other_info + other
								else:
									other_info = other_info + ', ' + other

				

					if len(journal_location.split('"'))>2:
						journal = journal_location.split('"')[1]
						other_infos = journal_location.split('"')[2].split('(')
						location=''
						other_info=''
						if len(other_infos)>1:
							for other in other_infos:
								if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
									location = other.split('),')[0]
									other_info = other.split('),')[1]
								else:
									location = location
									other_info = other_info
						other_info = other_info.replace(', ','')
				elif 'by' in info:
					date=''
					location=''
					other_info=''
					strings = info.split('by')
					journal_title = strings[0]	
					if len(strings[0].split('\''))>2:
						title = strings[0].split('\'')[1]
						journal = strings[0].split('\'')[0]
					author = strings[1].split('"')[0]
					#print author
					if ", " in author:
						author = author.split(", ")[0]
					if len(strings[1].split('"'))>2:
						for other in strings[1].split('"')[1].split(','):
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
								other_info = other_info
							except:
								date=date
								if other_info=='':
									other_info = other_info + other
								else:
									other_info = other_info + ', ' + other
				else:
					author_title=info.split('"')
					author = author_title[0]
					date=''
					location=''
					other_info=''
					journal=''
					title=''
					if len(author_title)>1:
						title = author_title[1]
						if len(author_title)>2:
							other_info=author_title[2]
							other_infos=author_title[2].split(',')
							for other in other_infos:
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info = other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
							other_infos = other_info.split('(')
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')
		

				authors=[]	
				if ' and ' in author:
					authors = author.split(' and ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')		
							authors[i] = authors[i].replace(':','')
						if authors[i][-1]=='_':
							authors[i] = authors[i][:-1]
						authors[i] = 'person/%s' %authors[i]
				if ' & ' in author:
					authors = author.split(' & ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')	
							authors[i] = authors[i].replace(':','')
						if authors[i][-1]=='_':
							authors[i] = authors[i][:-1]
						authors[i] = 'person/%s' %authors[i]	

				if authors !=[]:
					for i in range(0,len(authors)):
						authors[i] = authors[i].replace('__','_').decode('utf-8')
						#print 'author %s' %authors[i]
						author_uri = URIRef(imdb[authors[i]])
						programmes_graph.add((info_uri,dc["creator"],author_uri))
						programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
			
				if author != '' and author != 'Anonymous' and author != '.' and author != ' ' and author != '. ' :
					#print author
					splitted = author.split(', ')
					if len(splitted)>1:
						author= splitted[1]+' '+ splitted[0]
						author=author.replace('.','')
						author=author.replace(':','')
						author=author.replace(' ','_')
						author=author.replace('__','_')
					else:	
						author=author.replace(':','')	
						author=author.replace(' ','_')	
						author=author.replace('.','')
				
					if author[-1]=='_':
							author = author[:-1]
					if author[0]=='_':
							author = author[1:]
					author_url = 'person/%s' %author.decode('utf-8')
					author_uri = URIRef(imdb[author_url])
					programmes_graph.add((info_uri,dc["creator"],author_uri))
					programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
					#print 'author %s' %author_url

				if date != '' and date != today:
					programmes_graph.add((info_uri,dc["created"],Literal(date)))
					#print 'date %s' %date
				if location != '' and location != 'BK':
					location_url='location/%s' %location.decode('utf-8')
					location_url= location_url.replace('/ ' ,'/').replace(' ','_').replace('__','_')
					location_uri = URIRef(imdb[location_url])
					programmes_graph.add((info_uri,imdb["location"],location_uri))
					programmes_graph.add((location_uri,rdf["type"],imdb['Location']))
					#print location_uri

				if journal != '':
					programmes_graph.add((info_uri,dc["source"],Literal(journal.decode('utf-8'))))
					#print 'journal %s' %journal.decode('utf-8')
				if other_info != '':
					other_info=other_info.replace('. ','') 
					programmes_graph.add((info_uri,dc["description"],Literal(other_info.decode('utf-8'))))
					#print 'other_info %s' %other_info.decode('utf-8')
				if title != '':
					programmes_graph.add((info_uri,dc["title"],Literal(title.decode('utf-8'))))
					#print 'title %s' %title.decode('utf-8')
			if type=='novel':
				info_url = 'novel/%s' %id
				info_uri = URIRef(imdb[info_url])
				programmes_graph.add((program_uri,imdb["novel"],info_uri))	
				programmes_graph.add((info_uri,rdf["type"],imdb['Novel']))
				today = datetime.datetime.now().strftime('%d/%m/%Y')
				strings=[]
				if 'In: ' in info:
					author=''
					title=''
					strings = info.split('In: ')
					author_title = strings[0]
					rest = strings[1]
					if '"' in author_title:
						author_title=author_title.split('"')
						author = author_title[0]
						title = author_title[1].replace('"','')
					else:
						title = author_title.replace('"','')
					if '"' in author:
						title = author.split('"')[1]
						author=''
					rest=rest.split('"')
					if len(rest)>2:
						journal=rest[1]
						if len(rest)>3:
							other_info=rest[2]
							other_infos=rest[2].split(',')
							date=''
							other_info=''
							for other in other_infos:		
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info= other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
									other_infos = other_info.split('(')
							location=''
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
				
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')		
				elif 'by:' in info:
					date=''
					location=''
					other_info=''
					strings = info.split('by:')
					author_title = strings[1].split('"')
					journal_location = strings[0]		
					author = author_title[0]
					title = author_title[1]
					journal = ''
					if len(author_title)>2:
						other_infos = author_title[2].split(',')
						date=''
						other_info=''
						for other in other_infos:
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
								other_info = other_info
							except:
								date=date
								if other_info=='':
									other_info = other_info + other
								else:
									other_info = other_info + ', ' + other

				
	
					if len(journal_location.split('"'))>2:
						journal = journal_location.split('"')[1]
						other_infos = journal_location.split('"')[2].split('(')
						location=''
						other_info=''
						if len(other_infos)>1:
							for other in other_infos:
								if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
									location = other.split('),')[0]
									other_info = other.split('),')[1]
								else:
									location = location
									other_info = other_info
						other_info = other_info.replace(', ','')
				elif 'by' in info:
					date=''
					location=''
					other_info=''
					strings = info.split('by')
					journal_title = strings[0]	
					if len(strings[0].split('\''))>2:
						title = strings[0].split('\'')[1]
						journal = strings[0].split('\'')[0]
					author = strings[1].split('"')[0]
					#print author
					if ", " in author:
						author = author.split(", ")[0]
					if len(strings[1].split('"'))>2:
						for other in strings[1].split('"')[1].split(','):
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
								other_info = other_info
							except:
								date=date
								if other_info=='':
									other_info = other_info + other
								else:
									other_info = other_info + ', ' + other
				else:
					author_title=info.split('"')
					author = author_title[0]
					date=''
					location=''
					other_info=''
					journal=''
					title=''
					if len(author_title)>1:
						title = author_title[1]
						if len(author_title)>2:
							other_info=author_title[2]
							other_infos=author_title[2].split(',')
							for other in other_infos:
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info = other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
							other_infos = other_info.split('(')
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')
			

				authors=[]	
				if ' and ' in author:
					authors = author.split(' and ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')		
							authors[i] = authors[i].replace(':','')		
						if authors[i]!='':
							if authors[i][-1]=='_':
								authors[i] = authors[i][:-1]
							authors[i] = 'person/%s' %authors[i]
				if ' & ' in author:
					authors = author.split(' & ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')	
							authors[i] = authors[i].replace(':','')
						if authors[i][-1]=='_':
							authors[i] = authors[i][:-1]
						authors[i] = 'person/%s' %authors[i]	

				if authors !=[]:
					for i in range(0,len(authors)):
						authors[i] = authors[i].replace('__','_').decode('utf-8')
						#print 'author %s' %authors[i]
						author_uri = URIRef(imdb[authors[i]])
						programmes_graph.add((info_uri,dc["creator"],author_uri))
						programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
			
				if author != '' and author != 'Anonymous' and author != '. ':
					splitted = author.split(', ')
					if len(splitted)>1:
						author= splitted[1]+' '+ splitted[0]
						author=author.replace('.','')
						author=author.replace(':','')
						author=author.replace(' ','_')
						author=author.replace('__','_')
					else:	
						author=author.replace(':','')	
						author=author.replace(' ','_')	
						author=author.replace('.','')		
					if author[-1]=='_':
							author = author[:-1]
					if author[0]=='_':
							author = author[1:]
					author_url = 'person/%s' %author.decode('utf-8')
					author_uri = URIRef(imdb[author_url])
					programmes_graph.add((info_uri,dc["creator"],author_uri))
					programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
					#print 'author %s' %author_url

				if date != '' and date != today:
					programmes_graph.add((info_uri,dc["created"],Literal(date)))
					#print 'date %s' %date
				if location != '' and location != 'BK':
					location_url='location/%s' %location.decode('utf-8')
					location_url= location_url.replace('/ ' ,'/').replace(' ','_').replace('__','_')
					location_uri = URIRef(imdb[location_url])
					programmes_graph.add((info_uri,imdb["location"],location_uri))
					programmes_graph.add((location_uri,rdf["type"],imdb['Location']))
					#print location_uri

				if journal != '':
					programmes_graph.add((info_uri,dc["source"],Literal(journal.decode('utf-8'))))
					#print 'journal %s' %journal.decode('utf-8')
				if other_info != '':
					other_info=other_info.replace('. ','') 
					programmes_graph.add((info_uri,dc["description"],Literal(other_info.decode('utf-8'))))
					#print 'other_info %s' %other_info.decode('utf-8')
				if title != '':
					programmes_graph.add((info_uri,dc["title"],Literal(title.decode('utf-8'))))
					#print 'title %s' %title.decode('utf-8')			
			if type=='adaption':
				adaption_url='adaption/%s' %info.decode('utf-8')
				adaption_uri = URIRef(imdb[adaption_url])
				programmes_graph.add((program_uri,imdb["adaption"],adaption_uri))
				programmes_graph.add((adaption_uri,rdf["type"],imdb['Adaption']))

			if type=='essays':
				info_url = 'essay/%s' %id
				info_uri = URIRef(imdb[info_url])
				programmes_graph.add((program_uri,imdb["essay"],info_uri))	
				programmes_graph.add((info_uri,rdf["type"],imdb['Essay']))
				today = datetime.datetime.now().strftime('%d/%m/%Y')
				strings=[]
				if 'In: ' in info:
					author=''
					title=''
					strings = info.split('In: ')
					author_title = strings[0]
					rest = strings[1]
					if '"' in author_title:
						author_title=author_title.split('"')
						author = author_title[0]
						title = author_title[1].replace('"','')
					else:
						title = author_title.replace('"','')
					if '"' in author:
						title = author.split('"')[1]
						author=''
					rest=rest.split('"')
					if len(rest)>2:
						journal=rest[1]
						if len(rest)>3:
							other_info=rest[2]
							other_infos=rest[2].split(',')
							date=''
							other_info=''
							for other in other_infos:		
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info= other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
									other_infos = other_info.split('(')
							location=''
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
				
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')		
				elif 'by:' in info:
					date=''
					location=''
					other_info=''
					strings = info.split('by:')
					author_title = strings[1].split('"')
					journal_location = strings[0]		
					author = author_title[0]
					title = author_title[1]
					journal = ''
					if len(author_title)>2:
						other_infos = author_title[2].split(',')
						date=''
						other_info=''
						for other in other_infos:
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
								other_info = other_info
							except:
								date=date
								if other_info=='':
									other_info = other_info + other
								else:
									other_info = other_info + ', ' + other

				
	
					if len(journal_location.split('"'))>2:
						journal = journal_location.split('"')[1]
						other_infos = journal_location.split('"')[2].split('(')
						location=''
						other_info=''
						if len(other_infos)>1:
							for other in other_infos:
								if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
									location = other.split('),')[0]
									other_info = other.split('),')[1]
								else:
									location = location
									other_info = other_info
						other_info = other_info.replace(', ','')
				elif 'by' in info:
					date=''
					location=''
					other_info=''
					strings = info.split('by')
					journal_title = strings[0]	
					if len(strings[0].split('\''))>2:
						title = strings[0].split('\'')[1]
						journal = strings[0].split('\'')[0]
					author = strings[1].split('"')[0]
					#print author
					if ", " in author:
						author = author.split(", ")[0]
					if len(strings[1].split('"'))>2:
						for other in strings[1].split('"')[1].split(','):
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
								other_info = other_info
							except:
								date=date
								if other_info=='':
									other_info = other_info + other
								else:
									other_info = other_info + ', ' + other
				else:
					author_title=info.split('"')
					author = author_title[0]
					date=''
					location=''
					other_info=''
					journal=''
					title=''
					if len(author_title)>1:
						title = author_title[1]
						if len(author_title)>3:
							other_info=author_title[2]
							other_infos=author_title[2].split(',')
							for other in other_infos:
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info = other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
							other_infos = other_info.split('(')
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')	
			

				authors=[]	
				if ' and ' in author:
					authors = author.split(' and ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')		
							authors[i] = authors[i].replace(':','')
						if authors[i][-1]=='_':
							authors[i] = authors[i][:-1]
						authors[i] = 'person/%s' %authors[i]
				if ' & ' in author:
					authors = author.split(' & ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')	
							authors[i] = authors[i].replace(':','')
						if authors[i][-1]=='_':
							authors[i] = authors[i][:-1]
						authors[i] = 'person/%s' %authors[i]	

				if authors !=[]:
					for i in range(0,len(authors)):
						authors[i] = authors[i].replace('__','_').decode('utf-8')
						#print 'author %s' %authors[i]
						author_uri = URIRef(imdb[authors[i]])
						programmes_graph.add((info_uri,dc["creator"],author_uri))
						programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
			
				if author != '' and author != 'Anonymous' and author !='. ' and author !='.':
					#print author
					splitted = author.split(', ')
					if len(splitted)>1:
						author= splitted[1]+' '+ splitted[0]
						author=author.replace('.','')
						author=author.replace(':','')
						author=author.replace(' ','_')
						author=author.replace('__','_')
					else:	
						author=author.replace(':','')	
						author=author.replace(' ','_')	
						author=author.replace('.','')
					if author[-1]=='_':
							author = author[:-1]
					if author[0]=='_':
							author = author[1:]
					author_url = 'person/%s' %author.decode('utf-8')
					author_uri = URIRef(imdb[author_url])
					programmes_graph.add((info_uri,dc["creator"],author_uri))
					programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
					#print 'author %s' %author_url

				if date != '' and date != today:
					programmes_graph.add((info_uri,dc["created"],Literal(date)))
					#print 'date %s' %date
				if location != '' and location != 'BK':
					location_url='location/%s' %location.decode('utf-8')
					location_url= location_url.replace('/ ' ,'/').replace(' ','_').replace('__','_')
					location_uri = URIRef(imdb[location_url])
					programmes_graph.add((info_uri,imdb["location"],location_uri))
					programmes_graph.add((location_uri,rdf["type"],imdb['Location']))
					#print location_uri

				if journal != '':
					programmes_graph.add((info_uri,dc["source"],Literal(journal.decode('utf-8'))))
					#print 'journal %s' %journal.decode('utf-8')
				if other_info != '':
					other_info=other_info.replace('. ','') 
					programmes_graph.add((info_uri,dc["description"],Literal(other_info.decode('utf-8'))))
					#print 'other_info %s' %other_info.decode('utf-8')
				if title != '':
					programmes_graph.add((info_uri,dc["title"],Literal(title.decode('utf-8'))))
					#print 'title %s' %title.decode('utf-8')
		
			if type=='printed media reviews':
				info_url = 'printedMediaReviews/%s' %id
				info_uri = URIRef(imdb[info_url])
				programmes_graph.add((program_uri,imdb["printedMediaReviews"],info_uri))	
				programmes_graph.add((info_uri,rdf["type"],imdb['PrintedMediaReviews']))
				today = datetime.datetime.now().strftime('%d/%m/%Y')
				strings=[]
				if 'In: ' in info:
					author=''
					title=''
					strings = info.split('In: ')
					author_title = strings[0]
					rest = strings[1]
					if '"' in author_title:
						author_title=author_title.split('"')
						author = author_title[0]
						title = author_title[1].replace('"','')
					else:
						title = author_title.replace('"','')
					if '"' in author:
						title = author.split('"')[1]
						author=''
					rest=rest.split('"')
					if len(rest)>2:
						journal=rest[1]
						if len(rest)>3:
							other_info=rest[2]
							other_infos=rest[2].split(',')
							date=''
							other_info=''
							for other in other_infos:		
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info= other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
									other_infos = other_info.split('(')
							location=''
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
				
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')		
				elif 'by:' in info:
					date=''
					location=''
					other_info=''
					strings = info.split('by:')
					author_title = strings[1].split('"')
					journal_location = strings[0]		
					author = author_title[0]
					title = author_title[1]
					journal = ''
					if len(author_title)>2:
						other_infos = author_title[2].split(',')
						date=''
						other_info=''
						for other in other_infos:
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
								other_info = other_info
							except:
								date=date
								if other_info=='':
									other_info = other_info + other
								else:
									other_info = other_info + ', ' + other

				
	
					if len(journal_location.split('"'))>2:
						journal = journal_location.split('"')[1]
						other_infos = journal_location.split('"')[2].split('(')
						location=''
						other_info=''
						if len(other_infos)>1:
							for other in other_infos:
								if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
									location = other.split('),')[0]
									other_info = other.split('),')[1]
								else:
									location = location
									other_info = other_info
						other_info = other_info.replace(', ','')
				elif 'by' in info:
					date=''
					location=''
					other_info=''
					strings = info.split('by')
					journal_title = strings[0]	
					if len(strings[0].split('\''))>2:
						title = strings[0].split('\'')[1]
						journal = strings[0].split('\'')[0]
					author = strings[1].split('"')[0]
					#print author
					if ", " in author:
						author = author.split(", ")[0]
					if len(strings[1].split('"'))>2:
						for other in strings[1].split('"')[1].split(','):
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
								other_info = other_info
							except:
								date=date
								if other_info=='':
									other_info = other_info + other
								else:
									other_info = other_info + ', ' + other
				else:
					author_title=info.split('"')
					author = author_title[0]
					date=''
					location=''
					other_info=''
					journal=''
					title=''
					if len(author_title)>1:
						title = author_title[1]
						if len(author_title)>2:
							other_info=author_title[2]
							other_infos=author_title[2].split(',')
							for other in other_infos:
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info = other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
							other_infos = other_info.split('(')
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')
			

				authors=[]	
				if ' and ' in author:
					authors = author.split(' and ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:			
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')		
							authors[i] = authors[i].replace(':','')
						if authors[i][-1]=='_':
							authors[i] = authors[i][:-1]
						authors[i] = 'person/%s' %authors[i]
				if ' & ' in author:
					authors = author.split(' & ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')	
							authors[i] = authors[i].replace(':','')
						if authors[i][-1]=='_':
							authors[i] = authors[i][:-1]
						authors[i] = 'person/%s' %authors[i]	

				if authors !=[]:
					for i in range(0,len(authors)):
						authors[i] = authors[i].replace('__','_').decode('utf-8')
						#print 'author %s' %authors[i]
						author_uri = URIRef(imdb[authors[i]])
						programmes_graph.add((info_uri,dc["creator"],author_uri))
						programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
		
				if author != '' and author != 'Anonymous' and author!='. ':
					splitted = author.split(', ')
					if len(splitted)>1:
						author= splitted[1]+' '+ splitted[0]
						author=author.replace('.','')
						author=author.replace(':','')
						author=author.replace(' ','_')
						author=author.replace('__','_')
					else:	
						author=author.replace(':','')	
						author=author.replace(' ','_')	
						author=author.replace('.','')
					if author[-1]=='_':
							author = author[:-1]
					if author[0]=='_':
							author = author[1:]
					author_url = 'person/%s' %author.decode('utf-8')
					author_uri = URIRef(imdb[author_url])
					programmes_graph.add((info_uri,dc["creator"],author_uri))
					programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
					#print 'author %s' %author_url

				if date != '' and date != today:
					programmes_graph.add((info_uri,dc["created"],Literal(date)))
					#print 'date %s' %date
				if location != '' and location != 'BK':
					location_url='location/%s' %location.decode('utf-8')
					location_url= location_url.replace('/ ' ,'/').replace(' ','_').replace('__','_')
					location_uri = URIRef(imdb[location_url])
					programmes_graph.add((info_uri,imdb["location"],location_uri))
					programmes_graph.add((location_uri,rdf["type"],imdb['Location']))
					#print location_uri

				if journal != '':
					programmes_graph.add((info_uri,dc["source"],Literal(journal.decode('utf-8'))))
					#print 'journal %s' %journal.decode('utf-8')
				if other_info != '':
					other_info=other_info.replace('. ','') 
					programmes_graph.add((info_uri,dc["description"],Literal(other_info.decode('utf-8'))))
					#print 'other_info %s' %other_info.decode('utf-8')
				if title != '':
					programmes_graph.add((info_uri,dc["title"],Literal(title.decode('utf-8'))))
					#print 'title %s' %title.decode('utf-8')
		
			if type=='other literature':
				info_url = 'otherLiterature/%s' %id
				info_uri = URIRef(imdb[info_url])
				programmes_graph.add((program_uri,imdb["otherLiterature"],info_uri))	
				programmes_graph.add((info_uri,rdf["type"],imdb['OtherLiterature']))
				today = datetime.datetime.now().strftime('%d/%m/%Y')
				strings=[]
				if 'In: ' in info:
					author=''
					title=''
					journal=''
					strings = info.split('In: ')
					author_title = strings[0]
					rest = strings[1]
					if '"' in author_title:
						author_title=author_title.split('"')
						author = author_title[0]
						title = author_title[1].replace('"','')
					else:
						title = author_title.replace('"','')
					if '"' in author:
						title = author.split('"')[1]
						author=''
					rest=rest.split('"')
					if len(rest)>2:
						journal=rest[1]
						if len(rest)>3:
							other_info=rest[2]
							other_infos=rest[2].split(',')
							date=''
							other_info=''
							for other in other_infos:		
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info= other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
									other_infos = other_info.split('(')
							location=''
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
				
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')		
				elif 'by:' in info:
					date=''
					location=''
					other_info=''
					journal=''
					strings = info.split('by:')
					author_title = strings[1].split('"')
					journal_location = strings[0]		
					author = author_title[0]
					title = author_title[1]
					journal = ''
					if len(author_title)>2:
						other_infos = author_title[2].split(',')
						date=''
						other_info=''
						for other in other_infos:
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
								other_info = other_info
							except:
								date=date
								if other_info=='':
									other_info = other_info + other
								else:
									other_info = other_info + ', ' + other

				
	
					if len(journal_location.split('"'))>2:
						journal = journal_location.split('"')[1]
						other_infos = journal_location.split('"')[2].split('(')
						location=''
						other_info=''
						if len(other_infos)>1:
							for other in other_infos:
								if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
									location = other.split('),')[0]
									other_info = other.split('),')[1]
								else:
									location = location
									other_info = other_info
						other_info = other_info.replace(', ','')
				elif 'by' in info:
					date=''
					location=''
					other_info=''
					journal=''
					title=''
					strings = info.split('by')
					journal_title = strings[0]
					if len(strings[0].split('\''))>2:	
						title = strings[0].split('\'')[1]
						journal = strings[0].split('\'')[0]
					author = strings[1].split('"')[0]
					#print author
					if ", " in author:
						author = author.split(", ")[0]
					if len(strings[1].split('"'))>2:
						for other in strings[1].split('"')[1].split(','):
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
								other_info = other_info
							except:
								date=date
								if other_info=='':
									other_info = other_info + other
								else:
									other_info = other_info + ', ' + other
				else:
					author_title=info.split('"')
					author = author_title[0]
					date=''
					location=''
					other_info=''
					journal=''
					title=''
					if len(author_title)>1:
						title = author_title[1]
						if len(author_title)>2:
							other_info=author_title[2]
							other_infos=author_title[2].split(',')
							for other in other_infos:
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info = other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
							other_infos = other_info.split('(')
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')
			

				authors=[]	
				if ' and ' in author:
					authors = author.split(' and ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')		
							authors[i] = authors[i].replace(':','')
						if authors[i][-1]=='_':
							authors[i] = authors[i][:-1]
						authors[i] = 'person/%s' %authors[i]
				if ' & ' in author:
					authors = author.split(' & ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')	
							authors[i] = authors[i].replace(':','')
						if authors[i]!='':
							if authors[i][-1]=='_':
								authors[i] = authors[i][:-1]
							authors[i] = 'person/%s' %authors[i]	

				if authors !=[]:
					for i in range(0,len(authors)):
						authors[i] = authors[i].replace('__','_').decode('utf-8')
						#print 'author %s' %authors[i]
						author_uri = URIRef(imdb[authors[i]])
						programmes_graph.add((info_uri,dc["creator"],author_uri))
						programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
		
				if author != '' and author != 'Anonymous' and author !='. ':
					splitted = author.split(', ')
					if len(splitted)>1:
						author= splitted[1]+' '+ splitted[0]
						author=author.replace('.','')
						author=author.replace(':','')
						author=author.replace(' ','_')
						author=author.replace('__','_')
					else:	
						author=author.replace(':','')	
						author=author.replace(' ','_')	
						author=author.replace('.','')
					if author[-1]=='_':
							author = author[:-1]
					if author[0]=='_':
							author = author[1:]
					author_url = 'person/%s' %author.decode('utf-8')
					#print author_url
					author_uri = URIRef(imdb[author_url])
					programmes_graph.add((info_uri,dc["creator"],author_uri))
					programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
					#print 'author %s' %author_url

				if date != '' and date != today:
					programmes_graph.add((info_uri,dc["created"],Literal(date)))
					#print 'date %s' %date
				if location != '' and location != 'BK':
					location_url='location/%s' %location.decode('utf-8')
					location_url= location_url.replace('/ ' ,'/').replace(' ','_').replace('__','_')
					location_uri = URIRef(imdb[location_url])
					programmes_graph.add((info_uri,imdb["location"],location_uri))
					programmes_graph.add((location_uri,rdf["type"],imdb['Location']))
					#print location_uri

				if journal != '':
					programmes_graph.add((info_uri,dc["source"],Literal(journal.decode('utf-8'))))
					#print 'journal %s' %journal.decode('utf-8')
				if other_info != '':
					other_info=other_info.replace('. ','') 
					programmes_graph.add((info_uri,dc["description"],Literal(other_info.decode('utf-8'))))
					#print 'other_info %s' %other_info.decode('utf-8')
				if title != '':
					programmes_graph.add((info_uri,dc["title"],Literal(title.decode('utf-8'))))
					#print 'title %s' %title.decode('utf-8')
			if type=='production process protocol':
				productionProcessProtocol_url='productionProcessProtocol/%s' %info.decode('utf-8')
				productionProcessProtocol_uri = URIRef(imdb[productionProcessProtocol_url])
				programmes_graph.add((program_uri,imdb["productionProcessProtocol"],productionProcessProtocol_uri))
				programmes_graph.add((productionProcessProtocol_uri,rdf["type"],imdb['ProductionProcessProtocol']))
			if type=='screenplay-teleplay':
				info_url = 'screenplayTeleplay/%s' %id
				info_uri = URIRef(imdb[info_url])
				programmes_graph.add((program_uri,imdb["screenplayTeleplay"],info_uri))	
				programmes_graph.add((info_uri,rdf["type"],imdb['ScreenplayTeleplay']))
				today = datetime.datetime.now().strftime('%d/%m/%Y')
				strings=[]
				if 'In: ' in info:
					author=''
					title=''
					strings = info.split('In: ')
					author_title = strings[0]
					rest = strings[1]
					if '"' in author_title:
						author_title=author_title.split('"')
						author = author_title[0]
						title = author_title[1].replace('"','')
					else:
						title = author_title.replace('"','')
					if '"' in author:
						title = author.split('"')[1]
						author=''
					rest=rest.split('"')
					if len(rest)>2:
						journal=rest[1]
						if len(rest)>3:
							other_info=rest[2]
							other_infos=rest[2].split(',')
							date=''
							other_info=''
							for other in other_infos:		
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info= other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
									other_infos = other_info.split('(')
							location=''
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
				
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')		
				elif 'by:' in info:
					date=''
					location=''
					other_info=''
					strings = info.split('by:')
					author_title = strings[1].split('"')
					journal_location = strings[0]		
					author = author_title[0]
					if len(author_title)>1:
						title = author_title[1]
						journal = ''
						if len(author_title)>2:
							other_infos = author_title[2].split(',')
							date=''
							other_info=''
							for other in other_infos:
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info = other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other

				
	
					if len(journal_location.split('"'))>2:
						journal = journal_location.split('"')[1]
						other_infos = journal_location.split('"')[2].split('(')
						location=''
						other_info=''
						if len(other_infos)>1:
							for other in other_infos:
								if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
									location = other.split('),')[0]
									other_info = other.split('),')[1]
								else:
									location = location
									other_info = other_info
						other_info = other_info.replace(', ','')
				elif 'by' in info:
					date=''
					location=''
					other_info=''
					strings = info.split('by')
					journal_title = strings[0]
					if len(strings[0].split('\''))>2:
						title = strings[0].split('\'')[1]
						journal = strings[0].split('\'')[0]
					author = strings[1].split('"')[0]
					#print author
					if ", " in author:
						author = author.split(", ")[0]
					if len(strings[1].split('"'))>2:
						for other in strings[1].split('"')[1].split(','):
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
								other_info = other_info
							except:
								date=date
								if other_info=='':
									other_info = other_info + other
								else:
									other_info = other_info + ', ' + other
				else:
					author_title=info.split('"')
					author = author_title[0]
					date=''
					location=''
					other_info=''
					journal=''
					title=''
					if len(author_title)>1:
						title = author_title[1]
						if len(author_title)>2:
							other_info=author_title[2]
							other_infos=author_title[2].split(',')
							for other in other_infos:
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info = other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
							other_infos = other_info.split('(')
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')
			

				authors=[]	
				if ' and ' in author:
					authors = author.split(' and ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:						
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')		
							authors[i] = authors[i].replace(':','')
						if authors[i][-1]=='_':
							authors[i] = authors[i][:-1]
						authors[i] = 'person/%s' %authors[i]
				if ' & ' in author:
					authors = author.split(' & ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')	
							authors[i] = authors[i].replace(':','')
						if authors[i][-1]=='_':
							authors[i] = authors[i][:-1]
						authors[i] = 'person/%s' %authors[i]	

				if authors !=[]:
					for i in range(0,len(authors)):
						authors[i] = authors[i].replace('__','_').decode('utf-8')
						#print 'author %s' %authors[i]
						author_uri = URIRef(imdb[authors[i]])
						programmes_graph.add((info_uri,dc["creator"],author_uri))
						programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
		
				if author != '' and author != 'Anonymous' and author!='. ':
					splitted = author.split(', ')
					if len(splitted)>1:
						author= splitted[1]+' '+ splitted[0]
						author=author.replace('.','')
						author=author.replace(':','')
						author=author.replace(' ','_')
						author=author.replace('__','_')
					else:	
						author=author.replace(':','')	
						author=author.replace(' ','_')	
						author=author.replace('.','')
					if author[-1]=='_':
							author = author[:-1]
					if author[0]=='_':
							author = author[1:]
					author_url = 'person/%s' %author.decode('utf-8')
					author_uri = URIRef(imdb[author_url])
					programmes_graph.add((info_uri,dc["creator"],author_uri))
					programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
					#print 'author %s' %author_url

				if date != '' and date != today:
					programmes_graph.add((info_uri,dc["created"],Literal(date)))
					#print 'date %s' %date
				if location != '' and location != 'BK':
					location_url='location/%s' %location.decode('utf-8')
					location_url= location_url.replace('/ ' ,'/').replace(' ','_').replace('__','_')
					location_uri = URIRef(imdb[location_url])
					programmes_graph.add((info_uri,imdb["location"],location_uri))
					programmes_graph.add((location_uri,rdf["type"],imdb['Location']))
					#print location_uri

				if journal != '':
					programmes_graph.add((info_uri,dc["source"],Literal(journal.decode('utf-8'))))
					#print 'journal %s' %journal.decode('utf-8')
				if other_info != '':
					other_info=other_info.replace('. ','') 
					programmes_graph.add((info_uri,dc["description"],Literal(other_info.decode('utf-8'))))
					#print 'other_info %s' %other_info.decode('utf-8')
				if title != '':
					programmes_graph.add((info_uri,dc["title"],Literal(title.decode('utf-8'))))
					#print 'title %s' %title.decode('utf-8')
			if type=='interviews':
				info_url = 'interview/%s' %id
				info_uri = URIRef(imdb[info_url])
				programmes_graph.add((program_uri,imdb["interview"],info_uri))	
				programmes_graph.add((info_uri,rdf["type"],imdb['Interview']))
				today = datetime.datetime.now().strftime('%d/%m/%Y')
				strings=[]
				if 'In: ' in info:
					author=''
					title=''
					strings = info.split('In: ')
					author_title = strings[0]
					rest = strings[1]
					if '"' in author_title:
						author_title=author_title.split('"')
						author = author_title[0]
						title = author_title[1].replace('"','')
					else:
						title = author_title.replace('"','')
					if '"' in author:
						title = author.split('"')[1]
						author=''
					rest=rest.split('"')
					if len(rest)>2:
						journal=rest[1]
						if len(rest)>3:
							other_info=rest[2]
							other_infos=rest[2].split(',')
							date=''
							other_info=''
							for other in other_infos:		
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info= other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
									other_infos = other_info.split('(')
							location=''
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
				
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')		
				elif 'by:' in info:
					date=''
					location=''
					other_info=''
					strings = info.split('by:')
					author_title = strings[1].split('"')
					journal_location = strings[0]		
					author = author_title[0]
					if len(author_title)>2:
						title = author_title[1]
						journal = ''
						if len(author_title)>3:
							other_infos = author_title[2].split(',')
							date=''
							other_info=''
							for other in other_infos:
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info = other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other

						
	
					if len(journal_location.split('"'))>2:
						journal = journal_location.split('"')[1]
						other_infos = journal_location.split('"')[2].split('(')
						location=''
						other_info=''
						if len(other_infos)>1:
							for other in other_infos:
								if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
									location = other.split('),')[0]
									other_info = other.split('),')[1]
								else:
									location = location
									other_info = other_info
						other_info = other_info.replace(', ','')
				elif 'by' in info:
					date=''
					location=''
					other_info=''
					strings = info.split('by')
					journal_title = strings[0]	
					if len(strings[0].split('\''))>2:
						title = strings[0].split('\'')[1]
						journal = strings[0].split('\'')[0]
					author = strings[1].split('"')[0]
					#print author
					if ", " in author:
						author = author.split(", ")[0]
					if len(strings[1].split('"'))>2:
						for other in strings[1].split('"')[1].split(','):
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
								other_info = other_info
							except:
								date=date
								if other_info=='':
									other_info = other_info + other
								else:
									other_info = other_info + ', ' + other
				else:
					author_title=info.split('"')
					author = author_title[0]
					date=''
					location=''
					other_info=''
					journal=''
					title=''
					if len(author_title)>1:
						title = author_title[1]
						if len(author_title)>2:
							other_info=author_title[2]
							other_infos=author_title[2].split(',')
							for other in other_infos:
								try:
									date = dparser.parse(other,fuzzy=False)
									date = date.strftime('%d/%m/%Y')
									other_info = other_info
								except:
									date=date
									if other_info=='':
										other_info = other_info + other
									else:
										other_info = other_info + ', ' + other
							other_infos = other_info.split('(')
							other_info=''
							if len(other_infos)>1:
								for other in other_infos:
									if '),' in other and 'BK' not in other and 'NP' not in other and 'MG' not in other:
										location = other.split('),')[0]
										other_info = other.split('),')[1]
									else:
										location = location
										other_info = other_info
							other_info = other_info.replace(', ','')
			

				authors=[]	
				if ' and ' in author:
					authors = author.split(' and ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')		
							authors[i] = authors[i].replace(':','')
						if authors[i][-1]=='_':
							authors[i] = authors[i][:-1]
						authors[i] = 'person/%s' %authors[i]
				if ' & ' in author:
					authors = author.split(' & ')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(', ')
						if len(splitted)>1:
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')	
							authors[i] = authors[i].replace(':','')
						if authors[i][-1]=='_':
							authors[i] = authors[i][:-1]
						authors[i] = 'person/%s' %authors[i]	

				if authors !=[]:
					for i in range(0,len(authors)):
						authors[i] = authors[i].replace('__','_').decode('utf-8')
						#print 'author %s' %authors[i]
						author_uri = URIRef(imdb[authors[i]])
						programmes_graph.add((info_uri,dc["creator"],author_uri))
						programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
		
				if author != '' and author != 'Anonymous' and author !='. ':
					splitted = author.split(', ')
					if len(splitted)>1:
						author= splitted[1]+' '+ splitted[0]
						author=author.replace('.','')
						author=author.replace(':','')
						author=author.replace(' ','_')
						author=author.replace('__','_')
					else:	
						author=author.replace(':','')	
						author=author.replace(' ','_')	
						author=author.replace('.','')
					if author[-1]=='_':
							author = author[:-1]
					if author[0]=='_':
							author = author[1:]
					author_url = 'person/%s' %author.decode('utf-8')
					author_uri = URIRef(imdb[author_url])
					programmes_graph.add((info_uri,dc["creator"],author_uri))
					programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
					#print 'author %s' %author_url

				if date != '' and date != today:
					programmes_graph.add((info_uri,dc["created"],Literal(date)))
					#print 'date %s' %date
				if location != '' and location != 'BK':
					location_url='location/%s' %location.decode('utf-8')
					location_url= location_url.replace('/ ' ,'/').replace(' ','_').replace('__','_')
					location_uri = URIRef(imdb[location_url])
					programmes_graph.add((info_uri,imdb["location"],location_uri))
					programmes_graph.add((location_uri,rdf["type"],imdb['Location']))
					#print location_uri

				if journal != '':
					programmes_graph.add((info_uri,dc["source"],Literal(journal.decode('utf-8'))))
					#print 'journal %s' %journal.decode('utf-8')
				if other_info != '':
					other_info=other_info.replace('. ','') 
					programmes_graph.add((info_uri,dc["description"],Literal(other_info.decode('utf-8'))))
					#print 'other_info %s' %other_info.decode('utf-8')
				if title != '':
					programmes_graph.add((info_uri,dc["title"],Literal(title.decode('utf-8'))))
					#print 'title %s' %title.decode('utf-8')
			if type=='mpaa':
				programmes_graph.add((program_uri,imdb["mpaa"],Literal(info)))
			if type=='plot':
				programmes_graph.add((program_uri,po["synopsis"],Literal(info)))
			if type=='certificates':
				certificate_url='certificate/%s' %info.decode('utf-8')
				certificate_uri = URIRef(imdb[certificate_url])
				programmes_graph.add((program_uri,imdb["certificate"],certificate_uri))
				programmes_graph.add((certificate_uri,rdf["type"],imdb['Certificate']))
			if type=='color info':
				info=info.replace(' ','_')
				color_url='color/%s' %info.decode('utf-8')
				color_uri = URIRef(imdb[color_url])
				programmes_graph.add((program_uri,imdb["colorInfo"],color_uri))
				programmes_graph.add((color_uri,rdf["type"],imdb['Color']))
			if type=='countries':
				location_url='location/%s' %info.decode('utf-8')
				location_uri = URIRef(imdb[location_url])
				programmes_graph.add((program_uri,imdb["location"],location_uri))
				programmes_graph.add((location_uri,rdf["type"],imdb['Location']))
			if type=='genres':
				genre_url='genre/%s' %info.decode('utf-8')
				genre_uri = URIRef(imdb[genre_url])
				programmes_graph.add((program_uri,po["category"],genre_uri))
				programmes_graph.add((genre_uri,rdf["type"],imdb['Genre']))
			if type=='languages':
				language_url='language/%s' %info.decode('utf-8')
				language_uri = URIRef(imdb[language_url])
				programmes_graph.add((program_uri,dc["language"],language_uri))
				programmes_graph.add((language_uri,rdf["type"],imdb['Language']))
			if type=='locations':
				info = info.replace(' ','_')
				location_url='location/%s' %info.decode('utf-8')
				location_uri = URIRef(imdb[location_url])
				programmes_graph.add((program_uri,imdb["shotLocation"],location_uri))
				programmes_graph.add((location_uri,rdf["type"],imdb['Location']))
			if type=='runtimes':
				time_splitted=info.split(':')
				if len(time_splitted)>1:
					time = time_splitted[1]
				else:
					time = time_splitted[0]
				programmes_graph.add((program_uri,po["duration"],Literal(time)))
			if type=='sound mix':
				programmes_graph.add((program_uri,imdb["soundMix"],Literal(info)))
			if type=='tech info':
				programmes_graph.add((program_uri,imdb["techInfo"],Literal(info)))
			if type=='release dates':
				date_place = info.split(':')
				location_url = "location/%s" %date_place[0].decode('utf-8')
				location_uri = URIRef(imdb[location_url])
				try:
					date = dparser.parse(date_place[1],fuzzy=False)
					programmes_graph.add((program_uri,dc["issued"],Literal(date.strftime('%d/%m/%Y'))))
				except:
					date=''
				programmes_graph.add((program_uri,imdb["issued_place"],location_uri))
				programmes_graph.add((location_uri,rdf["type"],imdb["Location"]))
			if type=='taglines':
				programmes_graph.add((program_uri,imdb["taglines"],Literal(info)))

		cursor.execute("SELECT info_type_id, info FROM movie_info_idx WHERE movie_id= %s",(movie_id))
		data = cursor.fetchall()
		for row in data :
			type = info_type[row[0]]
			if type == 'votes distribution':
				programmes_graph.add((program_uri,imdb["votesDistribution"],Literal(row[1])))
			if type == 'votes':
				programmes_graph.add((program_uri,imdb["votes"],Literal(int(row[1]))))
			if type == 'rating':
				programmes_graph.add((program_uri,imdb["rating"],Literal(float(row[1]))))

		cursor.execute("SELECT linked_movie_id, link_type_id FROM movie_link WHERE movie_id= %s",(movie_id))
		data = cursor.fetchall()
		for row in data :
			type_to_use=''
			type = link_type[row[1]]
			type_splitted=type.split()
			l=len(type_splitted)
			if l>1:
				for i in range(1,l):
					type_splitted[i]=type_splitted[i].capitalize()
				for i in range(0,l):
					type_to_use = type_to_use + type_splitted[i]
			else: 
				type_to_use = type
			linked_program_url='program/%s' %row[0]
			linked_program_uri = URIRef(imdb[linked_program_url])
			programmes_graph.add((program_uri,imdb[type_to_use],linked_program_uri))

		cursor.execute("SELECT keyword_id FROM movie_keyword WHERE movie_id= %s",(movie_id))
		data = cursor.fetchall()
		for row in data :
			keyword_url='keyword/%s' %keywords[row[0]]
			keyword_uri = URIRef(imdb[keyword_url])
			programmes_graph.add((program_uri,imdb["keyword"],keyword_uri))
			programmes_graph.add((keyword_uri,rdf["type"],imdb['Keyword']))
	
		cursor.execute("SELECT company_id, company_type_id FROM movie_companies WHERE movie_id= %s",(movie_id))
		data = cursor.fetchall()
		for row in data:
			type_to_use = ''
			name_to_use = ''
			name_company = company_name[row[0]]
			type = company_type[row[1]]
			type_splitted=type.split()
			l=len(type_splitted)
			if l>1:
				for i in range(1,l):
					type_splitted[i]=type_splitted[i].capitalize()
				for i in range(0,l):
					type_to_use = type_to_use + type_splitted[i]
			else: 
				type_to_use = type
	
			name_to_use = name_company.replace(' ','_')
			company_url='company/%s' %name_to_use
			company_uri = URIRef(imdb[company_url])
			programmes_graph.add((program_uri,imdb[type_to_use],company_uri))

		cursor.execute("SELECT person_id, role_id FROM cast_info WHERE movie_id= %s",(movie_id))
		data = cursor.fetchall()
		for row in data :
			role_to_use = ''
			role = role_type[row[1]]
			role_splitted=role.split()
			l = len(role_splitted)
			if l>1:
				for i in range(1,l):
					role_splitted[i]=role_splitted[i].capitalize()
				for i in range(0,l):
					role_to_use = role_to_use + role_splitted[i]
			else: 
				role_to_use = role
			person_url='person/%s' %row[0]
			person_uri = URIRef(imdb[person_url])
			programmes_graph.add((program_uri,imdb[role_to_use],person_uri))
	
		db.close()

		file_name = '%s.rdf' %movie_id
		programmes_graph.serialize(file_name, format="xml")		
	
	except:
		print 'movie %s not rdf-ized' %movie_id
		not_done.append(movie_id)

print not_done
#outfile = open('not_done.txt','w')
#outfile.write("\n".join(not_done))
#file_name = 'programmes_imdb.rdf'
#programmes_graph.serialize(file_name, format="xml")
