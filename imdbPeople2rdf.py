import MySQLdb
import re
import os
from rdflib import URIRef
from rdflib import Literal
from rdflib import BNode
from rdflib import Namespace
from rdflib.graph import Graph
from rdflib import plugin
from rdflib.serializer import Serializer
import dateutil.parser as dparser
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

db = MySQLdb.connect("127.0.0.1","root","","imdb2",use_unicode=True,charset='latin1')
cursor = db.cursor()
not_done=[]
#create dictionaries

info_type=dict()
cursor.execute("SELECT * FROM info_type")
data = cursor.fetchall()
for row in data :
	info_type[row[0]]=row[1]
db.close()



#get data
#for person_id in range(4109291,4109292):
with open("not_done.csv", "rU") as infile:
    reader = csv.reader(infile)
    for person_id in reader:        
		people_graph = Graph()
		person_url='person/%s' %person_id
		person_uri = URIRef(imdb[person_url])
		person_id = person_id[0]
		print person_id
		#try:
		db = MySQLdb.connect("127.0.0.1","root","","imdb2",use_unicode=True,charset='latin1')
		cursor = db.cursor()	
		cursor.execute("SELECT id, person_id, info_type_id, info FROM person_info WHERE person_id = %s", (person_id))
		data = cursor.fetchall()
		for row in data:
			id=row[0]
			type = info_type[row[2]].encode('utf-8')
			info = row[3].encode('utf-8')
			people_graph.add((person_uri,rdf["type"], foaf["Person"]))
			if type == 'birth date':
				people_graph.add((person_uri,foaf['birthday'],Literal(info)))
			if type == 'birth notes':
				people_graph.add((person_uri,imdb['birth_place'],Literal(info)))
			if type == 'trivia':
				people_graph.add((person_uri,imdb['trivia'],Literal(info)))
			if type == 'nick names':
				people_graph.add((person_uri,foaf['nick'],Literal(info)))
			if type== 'spouse':
				name, sep, after = info.rpartition("'")
				name = re.sub('\'', '', name)
				if '(' in name:
					names = name.split('(')[0].split()		
				else:
					names = name.split()
				l = len(names)
				if l>1:
					name_spouse = names[l-1] + ', '
					for i in range (0,l-1):
						name_spouse = name_spouse + names[i] + ' '
				elif l==0:
					name_spouse = ''
				else:
					name_spouse = names[0]
	
				cursor.execute("SELECT id FROM name WHERE name = %s", (name_spouse))
				data = cursor.fetchall()
				if len(data)>0:
					for row in data[0]:
						spouse_url='person/%s' %row
					spouse_uri = URIRef(imdb[spouse_url])
					people_graph.add((person_uri,dbpedia['spouse'],spouse_uri))
				else:
					people_graph.add((person_uri,dbpedia['spouse'],Literal(name_spouse)))
			if type == 'height':
				people_graph.add((person_uri,dbpedia['Person/height'],Literal(info)))
			if type == 'mini biography':
				people_graph.add((person_uri,imdb['biography'],Literal(info)))
			if type == 'quotes':
				people_graph.add((person_uri,imdb['quotes'],Literal(info)))
			if type == 'death notes':
				people_graph.add((person_uri,imdb['deathNotes'],Literal(info)))
			if type == 'death date':
				people_graph.add((person_uri,dbpedia['deathDate'],Literal(info)))
			if type == 'other works':
				people_graph.add((person_uri,imdb['otherWork'],Literal(info)))
			if type == 'interviews':
				info_url = 'interview/%s' %id
				info_uri = URIRef(imdb[info_url])
				people_graph.add((person_uri,imdb["interview"],info_uri))	
				people_graph.add((info_uri,rdf["type"],imdb['Interview']))
				infos = info.split(',')
				journal = infos[0]
				journals = journal.split('"')		
				if len(journals)>2:
					journal = journals[1]
					country = journals[2].replace('(','').replace(')','')
				date=''
				author=''
				title=''
				if 'by: ' in info:
					author = info.split('by: ')[1].split(',')[0]
					if len(info.split('by: ')[1].split(','))>1:
						title=info.split('by: ')[1].split(',')[1].replace('"','')
				if infos[len(infos)-1] == '"':
					title = infos[len(infos)-1].replace('"','')
				try:
					date = dparser.parse(infos[1],fuzzy=False)
					date = date.strftime('%d/%m/%Y')
				except:
					date=''	

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
							if authors[i][-1]=='_':
								authors[i] = authors[i][:-1]
						else:		
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')
				if '/' in author:
					authors = author.split('/')
					author=''
					for i in range(0,len(authors)):
						splitted = authors[i].split(' ')
						if len(splitted)>1:			
							authors[i]= splitted[1]+'_'+ splitted[0]
							authors[i] = authors[i].replace(', ','_')
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')		
							if authors[i][-1]=='_':
								authors[i] = authors[i][:-1]
						else:		
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')
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
							if authors[i][-1]=='_':
								authors[i] = authors[i][:-1]
						else:		
							authors[i] = authors[i].replace(' ','_')	
							authors[i] = authors[i].replace('.','')
				if authors !=[]:
					for i in range(0,len(authors)):
						names = authors[i].split('_')
						l = len(names)
						if l>1:
							name_author = names[l-1] + ', '
							for n in range (0,l-1):
								name_author = name_author + names[n] + ' '
						elif l==0:
							name_author = ''
						else:
							name_author = names[0].replace('_',' ')		
						cursor.execute("SELECT id FROM name WHERE name = %s", (name_author))
						data = cursor.fetchall()
						if len(data)>0:
							for row in data[0]:
								author_url='person/%s' %row
							author_uri = URIRef(imdb[author_url])
							people_graph.add((info_uri,dc["creator"],author_uri))
						else:
							authors[i] = 'person/%s' %authors[i].replace(' ' ,'_').decode('utf-8')
							author_uri = URIRef(imdb[authors[i]])
							people_graph.add((info_uri,dc["creator"],author_uri))
							people_graph.add((author_uri,rdf["type"],foaf["Person"]))
							people_graph.add((author_uri,foaf["name"],Literal(name_author)))
				if author != '' and author != 'Anonymous':
					splitted = author.split(', ')
					if len(splitted)>1:
						author= splitted[1]+' '+ splitted[0]
						author=author.replace('.','')
						author=author.replace(' ','_')
						author=author.replace('__','_')
					else:		
						author=author.replace(' ','_')	
						author=author.replace('.','')
					if author[-1]=='_':
							author = author[:-1]
			
					names = author.split('_')
					l = len(names)
					if l>1:
						name_author = names[l-1] + ', '
						for i in range (0,l-1):
							name_author = name_author + names[i] + ' '
					elif l==0:
						name_author = ''
					else:
						name_author = names[0].replace('_',' ').replace(', ','') .replace(', ','') 
	
	
					cursor.execute("SELECT id FROM name WHERE name = %s", (name_author))
					data = cursor.fetchall()
					if len(data)>0:
						for row in data[0]:
							author_url='person/%s' %row
						author_uri = URIRef(imdb[author_url])
						people_graph.add((info_uri,dc["creator"],author_uri))
		
					else:
						author = 'person/%s' %author.replace(' ' ,'_').decode('utf-8')
						author_uri = URIRef(imdb[author])
						people_graph.add((info_uri,dc["creator"],author_uri))
						people_graph.add((author_uri,rdf["type"],foaf["Person"]))
						people_graph.add((author_uri,foaf["name"],Literal(name_author)))

				if journal !='':
					journal_url='journal/%s' %journal
					journal_url= journal_url.replace('/ ' ,'/').replace(' ','_').decode('utf-8')
					journal_uri = URIRef(imdb[journal_url])
					people_graph.add((info_uri,imdb["journal"],journal_uri))
					people_graph.add((journal_uri,rdf["type"],imdb['Journal']))
	
					if country != '':
						country_url='country/%s' %country.decode('utf-8')
						country_url= country_url.replace('/ ' ,'/').replace(' ','_')
						country_uri = URIRef(imdb[country_url])
						people_graph.add((journal_uri,imdb["country"],country_uri))
						people_graph.add((country_uri,rdf["type"],imdb['Country']))
		
				if date != '':
	
					people_graph.add((info_uri,dc["created"],Literal(date)))
				if title != '':
					if title[0]==' ':
						title=title[1:]
					else:
						title=title
					people_graph.add((info_uri,dc["title"],Literal(title)))	
			if type== 'where now':
				info = info.replace(' ','_')
				location_url='location/%s' %info.decode('utf-8')
				location_uri = URIRef(imdb[location_url])
				people_graph.add((person_uri,imdb["whereNow"],location_uri))
				#people_graph.add((location_uri,rdf["type"],imdb['Location']))
		
			if type== 'article':
				info_url = 'article/%s' %id
				info_uri = URIRef(imdb[info_url])
				people_graph.add((person_uri,imdb["article"],info_uri))	
				people_graph.add((info_uri,rdf["type"],imdb['Article']))
				infos = info.split(',')
				journal = infos[0]
				journals = journal.split('"')				
				if len(journals)>2:
					journal = journals[1]
					country = journals[2].replace('(','').replace(')','')
				date=''
				author=''
				title=''
				if 'by: ' in info:
					author = info.split('by: ')[1].split(',')[0]
					if len(info.split('by: ')[1].split(','))>1:
						title=info.split('by: ')[1].split(',')[1].replace('"','')
				elif infos[len(infos)-1] == '"':
					title = infos[len(infos)-1].replace('"','')
				try:
					date = dparser.parse(infos[1],fuzzy=False)
					date = date.strftime('%d/%m/%Y')
				except:
					date=''	
				if author !='':
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
								if authors[i][-1]=='_':
									authors[i] = authors[i][:-1]
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
							if authors[i][-1]=='_':
								authors[i] = authors[i][:-1]
					if authors !=[]:
						for i in range(0,len(authors)):
							names = authors[i].split('_')
							l = len(names)
							if l>1:
								name_author = names[l-1] + ', '
								for n in range (0,l-1):
									name_author = name_author + names[n] + ' '
							elif l==0:
								name_author = ''
							else:
								name_author = names[0].replace('_',' ')			
							cursor.execute("SELECT id FROM name WHERE name = %s", (name_author))
							data = cursor.fetchall()
							if len(data)>0:
								for row in data[0]:
									author_url='person/%s' %row
								author_uri = URIRef(imdb[author_url])
								people_graph.add((info_uri,dc["creator"],author_uri))
							else:
								authors[i] = 'person/%s' %authors[i].replace(' ' ,'_').decode('utf-8')
								author_uri = URIRef(imdb[authors[i]])
								people_graph.add((info_uri,dc["creator"],author_uri))
								people_graph.add((author_uri,rdf["type"],foaf["Person"]))
								people_graph.add((author_uri,foaf["name"],Literal(name_author)))
				
					if author != '' and author != 'Anonymous':
						splitted = author.split(', ')
						if len(splitted)>1:
							author= splitted[1]+' '+ splitted[0]
							author=author.replace('.','')
							author=author.replace(' ','_')
							author=author.replace('__','_')
						else:		
							author=author.replace(' ','_')	
							author=author.replace('.','')
						if author[-1]=='_':
								author = author[:-1]
						names = author.split('_')				
						l = len(names)
						if l>1:
							name_author = names[l-1] + ', '
							for i in range (0,l-1):
								name_author = name_author + names[i] + ' '
						elif l==0:
							name_author = ''
						else:
							name_author = names[0].replace('_',' ')	
						cursor.execute("SELECT id FROM name WHERE name = %s", (name_author))
						data = cursor.fetchall()
		
						if len(data)>0:
							for row in data[0]:
								author_url='person/%s' %row
							author_uri = URIRef(imdb[author_url])
							people_graph.add((info_uri,dc["creator"],author_uri))
						else:
							author= 'person/%s' %author.replace(' ','_').decode('utf-8')
							author_uri = URIRef(imdb[author])
							people_graph.add((info_uri,dc["creator"],author_uri))
							people_graph.add((author_uri,rdf["type"],foaf["Person"]))
							people_graph.add((author_uri,foaf["name"],Literal(name_author)))
			
				if journal !='':
					journal_url='journal/%s' %journal
					journal_url= journal_url.replace('/ ' ,'/').replace(' ','_').decode('utf-8')
					journal_uri = URIRef(imdb[journal_url])
					people_graph.add((info_uri,imdb["journal"],journal_uri))
					people_graph.add((journal_uri,rdf["type"],imdb['Journal']))
					if country != '':
						country_url='country/%s' %country.decode('utf-8')
						country_url= country_url.replace('/ ' ,'/').replace(' ','_')
						country_uri = URIRef(imdb[country_url])
						people_graph.add((journal_uri,imdb["country"],country_uri))
						people_graph.add((country_uri,rdf["type"],imdb['Country']))
				if date != '':
					people_graph.add((info_uri,dc["created"],Literal(date)))
				if title != '':
					if title[0]==' ':
						title=title[1:]
					else:
						title=title
					people_graph.add((info_uri,dc["title"],Literal(title)))		
			if type== 'portrayed in':
				if len(info.split('_')) > 2:
					infos = info.split('_')[1].split('{')
					title = infos[0].split('(')[0].replace('"','')
					try:
						date = dparser.parse(infos[0].split('(')[1].replace(')',''),fuzzy=False)
						date = date.strftime('%d/%m/%Y')
					except:
						date=''
					if len(infos)>1:
						sub_title = infos[1].replace('}','')
					else:
						sub_title=''

					if sub_title!='':
						only_sub_title = sub_title.split('(')[0]
						cursor.execute("SELECT id FROM title WHERE title = %s", (only_sub_title))
						data = cursor.fetchall()
						if len(data)>0:
							for row in data:
								info_url='program/%s' %row[0]
						info_uri = URIRef(imdb[info_url])
						people_graph.add((person_uri,imdb["portrayedIn"],info_uri))	
						people_graph.add((info_uri,rdf["type"],imdb['Portray']))
	
					elif title != '':
						cursor.execute("SELECT id FROM title WHERE title = %s", (title))
						data = cursor.fetchall()
						if len(data)>0:
							for row in data:
								info_url='program/%s' %row[0]
							info_uri = URIRef(imdb[info_url])
							people_graph.add((person_uri,imdb["portrayedIn"],info_uri))	
							people_graph.add((info_uri,rdf["type"],imdb['Portray']))
						else:
							info_url = 'portrayedIn/%s' %id
							info_uri = URIRef(imdb[info_url])
							people_graph.add((person_uri,imdb["portrayedIn"],info_uri))	
							people_graph.add((info_uri,rdf["type"],imdb['Portray']))
						if title[0]==' ':
							title=title[1:]
						else:
							title=title
						people_graph.add((info_uri,dc["title"],Literal(title)))
						if date != '':
							people_graph.add((info_uri,dc["created"],Literal(date)))		
			if type== 'biographical movies':
				if len(info.split('_')) > 2:
					infos = info.split('_')[1].split('{')
					title = infos[0].split('(')[0].replace('"','')
					try:
						date = dparser.parse(infos[0].split('(')[1].replace(')',''),fuzzy=False)
						date = date.strftime('%d/%m/%Y')
					except:
						date=''
					if len(infos)>1:
						sub_title = infos[1].replace('}','')
					else:
						sub_title=''

					if sub_title!='':
						only_sub_title = sub_title.split('(')[0]
						cursor.execute("SELECT id FROM title WHERE title = %s", (only_sub_title))
						data = cursor.fetchall()
						if len(data)>0:
							for row in data:
								info_url='program/%s' %row[0]
						info_uri = URIRef(imdb[info_url])
						people_graph.add((person_uri,imdb["portrayedIn"],info_uri))	
						people_graph.add((info_uri,rdf["type"],imdb['Portray']))
					elif title != '':
						cursor.execute("SELECT id FROM title WHERE title = %s", (title))
						data = cursor.fetchall()
						if len(data)>0:
							for row in data:
								info_url='program/%s' %row[0]
						info_uri = URIRef(imdb[info_url])
						people_graph.add((person_uri,imdb["portrayedIn"],info_uri))	
						people_graph.add((info_uri,rdf["type"],imdb['Portray']))
					else:
						info_url = 'portrayedIn/%s' %id
						info_uri = URIRef(imdb[info_url])
						people_graph.add((person_uri,imdb["portrayedIn"],info_uri))	
						people_graph.add((info_uri,rdf["type"],imdb['Portray']))
						if title[0]==' ':
							title=title[1:]
						else:
							title=title
						people_graph.add((info_uri,dc["title"],Literal(title)))
						if date != '':
							people_graph.add((info_uri,dc["created"],Literal(date)))
			if type== 'books':
				info_url = 'book/%s' %id
				info_uri = URIRef(imdb[info_url])
				people_graph.add((person_uri,imdb["book"],info_uri))	
				people_graph.add((info_uri,rdf["type"],imdb['Book']))
				other_info = ''
				date=''
				infos = info.split('_')
				author = infos[0]
				author = author.replace('.','')
				author = author.replace('\'','')
				if len(infos)>2:
					title = infos[1]
					title = title.replace('.','')
					title = title.replace('\'','')
					other_info = infos[2]
					other_infos = other_info.split('.')
					if len(other_infos)>0:
						for other in other_infos:
							try:
								date = dparser.parse(other,fuzzy=False)
								date = date.strftime('%d/%m/%Y')
							except:
								date=date
				if author !='':
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
								if authors[i][-1]=='_':
									authors[i] = authors[i][:-1]
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
							if authors[i][-1]=='_':
								authors[i] = authors[i][:-1]
					if authors !=[]:
						for i in range(0,len(authors)):
							names = authors[i].split('_')
						l = len(names)
						if l>1:
							name_author = names[l-1] + ', '
							for n in range (0,l-1):
								name_author = name_author + names[n] + ' '
						elif l==0:
							name_author = ''
						else:
							name_author = names[0].replace('_',' ')			
						cursor.execute("SELECT id FROM name WHERE name = %s", (name_author))
						data = cursor.fetchall()
						if len(data)>0:
							for row in data[0]:
								author_url='person/%s' %row
							author_uri = URIRef(imdb[author_url])
							people_graph.add((info_uri,dc["creator"],author_uri))
						else:
							authors[i] = 'person/%s' %authors[i].replace(' ' ,'_').decode('utf-8')
							author_uri = URIRef(imdb[authors[i]])
							people_graph.add((info_uri,dc["creator"],author_uri))
							people_graph.add((author_uri,rdf["type"],foaf["Person"]))
							people_graph.add((author_uri,foaf["name"],Literal(name_author)))
	
					if author != '' and author != 'Anonymous':
						splitted = author.split(', ')
						if len(splitted)>1:
							author= splitted[1]+' '+ splitted[0]
							author=author.replace('.','')
							author=author.replace(' ','_')
							author=author.replace('__','_')
						else:		
							author=author.replace(' ','_')	
							author=author.replace('.','')
						if author[-1]=='_':
								author = author[:-1]
						names = author.split()
						l = len(names)
						if l>1:
							name_author = names[l-1] + ', '
							for i in range (0,l-1):
								name_author = name_author + names[i] + ' '
						elif l==0:
							name_author = ''
						else:
							name_author = names[0].replace('_',' ')		
						cursor.execute("SELECT id FROM name WHERE name = %s", (name_author))
						data = cursor.fetchall()
						if len(data)>0:
							for row in data[0]:
								author_url='person/%s' %row
							author_uri = URIRef(imdb[author_url])
							people_graph.add((info_uri,dc["creator"],author_uri))
						else:
							author = 'person/%s' %author.replace(' ' ,'_').decode('utf-8')
							author_uri = URIRef(imdb[author])
							people_graph.add((info_uri,dc["creator"],author_uri))
							people_graph.add((author_uri,rdf["type"],foaf["Person"]))
							people_graph.add((author_uri,foaf["name"],Literal(name_author)))
		
				if date != '':
					people_graph.add((info_uri,dc["created"],Literal(date)))
				if title != '':
					if title[0]==' ':
						title=title[1:]
					else:
						title=title
					people_graph.add((info_uri,dc["title"],Literal(title)))
				if other_info != '':
					other_info=other_info.replace('. ','') 
					people_graph.add((info_uri,dc["description"],Literal(other_info)))		
			if type== 'pictorial':
				info_url = 'pictorial/%s' %id
				info_uri = URIRef(imdb[info_url])
				people_graph.add((person_uri,imdb["pictorial"],info_uri))	
				people_graph.add((info_uri,rdf["type"],imdb['Pictorial']))
				infos = info.split(',')
				journal = infos[0]
				journals = journal.split('"')
				
				if len(journals)>2:
					journal = journals[1]
					country = journals[2].replace('(','').replace(')','')
				date=''
				author=''
				title=''
				if 'by: ' in info:
					author = info.split('by: ')[1].split(',')[0]
					if len(info.split('by: ')[1].split(','))>1:
						title=info.split('by: ')[1].split(',')[1].replace('"','')
				elif infos[len(infos)-1] == '"':
					title = infos[len(infos)-1].replace('"','')
				try:
					date = dparser.parse(infos[1],fuzzy=False)
					date = date.strftime('%d/%m/%Y')
				except:
					date=''	
				if author !='':
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
								if authors[i][-1]=='_':
									authors[i] = authors[i][:-1]
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
							if authors[i][-1]=='_':
								authors[i] = authors[i][:-1]
					if authors !=[]:
						for i in range(0,len(authors)):
							names = authors[i].split('_')
							l = len(names)
							if l>1:
								name_author = names[l-1] + ', '
								for n in range (0,l-1):
									name_author = name_author + names[n] + ' '
							elif l==0:
								name_author = ''
							else:
								name_author = names[0].replace('_',' ')
			
							cursor.execute("SELECT id FROM name WHERE name = %s", (name_author))
							data = cursor.fetchall()
							if len(data)>0:
								for row in data[0]:
									author_url='person/%s' %row
								author_uri = URIRef(imdb[author_url])
								people_graph.add((info_uri,dc["creator"],author_uri))
							else:
								authors[i] = 'person/%s' %authors[i].replace(' ' ,'_').decode('utf-8')
								author_uri = URIRef(imdb[authors[i]])
								people_graph.add((info_uri,dc["creator"],author_uri))
								people_graph.add((author_uri,rdf["type"],foaf["Person"]))
								people_graph.add((author_uri,foaf["name"],Literal(name_author)))
	
					if author != '' and author != 'Anonymous':
						splitted = author.split(', ')
						if len(splitted)>1:
							author= splitted[1]+' '+ splitted[0]
							author=author.replace('.','')
							author=author.replace(' ','_')
							author=author.replace('__','_')
						else:		
							author=author.replace(' ','_')	
							author=author.replace('.','')
						if author[-1]=='_':
								author = author[:-1]
						names = author.split('_')
						l = len(names)
						if l>1:
							name_author = names[l-1] + ', '
							for i in range (0,l-1):
								name_author = name_author + names[i] + ' '
						elif l==0:
							name_author = ''
						else:
							name_author = names[0].replace('_',' ')
					
						cursor.execute("SELECT id FROM name WHERE name = %s", (name_author))
						data = cursor.fetchall()
						if len(data)>0:
							for row in data[0]:
								author_url='person/%s' %row
							author_uri = URIRef(imdb[author_url])
							people_graph.add((info_uri,dc["creator"],author_uri))
						else:
							author = 'person/%s' %author.replace(' ' ,'_').decode('utf-8')
							author_uri = URIRef(imdb[author])
							people_graph.add((info_uri,dc["creator"],author_uri))
							people_graph.add((author_uri,rdf["type"],foaf["Person"]))
							people_graph.add((author_uri,foaf["name"],Literal(name_author)))
			
				if journal !='':
					journal_url='journal/%s' %journal
					journal_url= journal_url.replace('/ ' ,'/').replace(' ','_').decode('utf-8')
					journal_uri = URIRef(imdb[journal_url])
					people_graph.add((info_uri,imdb["journal"],journal_uri))
					people_graph.add((journal_uri,rdf["type"],imdb['Journal']))

					if country != '':
						country_url='country/%s' %country.decode('utf-8')
						country_url= country_url.replace('/ ' ,'/').replace(' ','_')
						country_uri = URIRef(imdb[country_url])
						people_graph.add((journal_uri,imdb["country"],country_uri))
						people_graph.add((country_uri,rdf["type"],imdb['Country']))

				if date != '':
					people_graph.add((info_uri,dc["created"],Literal(date)))
				if title != '':

					if title[0]==' ':
						title=title[1:]
					else:
						title=title
					people_graph.add((info_uri,dc["title"],Literal(title)))	
			if type== 'magazine cover photo':
				info_url = 'magazineCoverPhoto/%s' %id
				info_uri = URIRef(imdb[info_url])
				people_graph.add((person_uri,imdb["magazineCoverPhoto"],info_uri))	
				people_graph.add((info_uri,rdf["type"],imdb['MagazineCoverPhoto']))
				infos = info.split(',')
				journal = infos[0]
				journals = journal.split('"')
				
				if len(journals)>2:
					journal = journals[1]
					country = journals[2].replace('(','').replace(')','')
				date=''
				try:
					date = dparser.parse(infos[1],fuzzy=False)
					date = date.strftime('%d/%m/%Y')
				except:
					date=''	
				if date != '':
	
					people_graph.add((info_uri,dc["created"],Literal(date)))
				if journal != '':
					journal_url='journal/%s' %journal
					journal_url= journal_url.replace('/ ' ,'/').replace(' ','_').decode('utf-8')
					journal_uri = URIRef(imdb[journal_url])
					people_graph.add((info_uri,imdb["journal"],journal_uri))
					people_graph.add((journal_uri,rdf["type"],imdb['Journal']))
					if country != '':
						country_url='country/%s' %country.decode('utf-8')
						country_url= country_url.replace('/ ' ,'/').replace(' ','_')
						country_uri = URIRef(imdb[country_url])
						people_graph.add((journal_uri,imdb["country"],country_uri))
						people_graph.add((country_uri,rdf["type"],imdb['Country']))		
			if type== 'trade mark':
				people_graph.add((person_uri,imdb['tradeMark'],Literal(info)))
			if type== 'salary history':
				people_graph.add((person_uri,dbpedia['salary'],Literal(info)))

		cursor.execute("SELECT name, gender FROM name WHERE id = %s", (person_id))
		data = cursor.fetchall()
		for row in data:
			people_graph.add((person_uri,foaf['name'],Literal(row[0])))
			if row[1] == 'f':
				people_graph.add((person_uri,foaf['gender'],Literal('Female')))
			elif row[1] =='m':
				people_graph.add((person_uri,foaf['gender'],Literal('Male')))
		db.close()
		file_name = '%s.rdf' %person_id
		people_graph.serialize(file_name, format="xml")					
	#except:
		#not_done.append(person_id)
		#print 'person not rdf-ized id: %s' % person_id

#outfile = open('not_done.txt','w')
#outfile.write("\n".join(not_done))
#file_name = 'people_imdb.rdf'
#people_graph.serialize(file_name, format="xml")
