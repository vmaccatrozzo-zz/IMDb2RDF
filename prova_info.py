import dateutil.parser as dparser
import datetime

from rdflib import URIRef
from rdflib import Literal
from rdflib import Namespace
imdb = Namespace('http://imdb.org/')

def extract(info):
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
		journal=rest[1]
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
	
		journal = journal_location.split('"')[1]
		
		if len(journal_location.split('"'))>2:
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
			if len(splitted)>1:
				splitted = authors[i].split(', ')
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
			authors[i] = authors[i].replace('__','_')
			#print 'author %s' %authors[i]
			author_uri = URIRef(imdb[authors[i]])
			programmes_graph.add((info_uri,dc["creator"],author_uri))
			programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
			
	if author != '' and author != 'Anonymous':
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
		author_url = 'person/%s' %author.encode('utf-8')
		author_uri = URIRef(imdb[author_url])
		programmes_graph.add((info_uri,dc["creator"],author_uri))
		programmes_graph.add((author_uri,rdf["type"],foaf["Person"]))
		#print 'author %s' %author_url
	
	if date != '' and date != today:
		programmes_graph.add((info_uri,dc["created"],Literal(date)))
		#print 'date %s' %date
	if location != '' and location != 'BK':
		location_url='location/%s' %location.encode('utf-8')
		location_url= location_url.replace('/ ' ,'/').replace(' ','_').replace('__','_')
		location_uri = URIRef(imdb[location_url])
		programmes_graph.add((info_uri,imdb["location"],location_uri))
		programmes_graph.add((location_uri,rdf["type"],imdb['Location']))
		#print location_uri
	
	if journal != '':
		programmes_graph.add((info_uri,dc["source"],Literal(journal.encode('utf-8'))))
		#print 'journal %s' %journal.encode('utf-8')
	if other_info != '':
		other_info=other_info.replace('. ','') 
		programmes_graph.add((info_uri,dc["description"],Literal(other_info.encode('utf-8'))))
		#print 'other_info %s' %other_info.encode('utf-8')
	if title != '':
		programmes_graph.add((info_uri,dc["title"],Literal(title.encode('utf-8'))))
		#print 'title %s' %title.encode('utf-8')
	
	return True		