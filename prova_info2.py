import dateutil.parser as dparser
import MySQLdb
from rdflib import URIRef
from rdflib import Literal
from rdflib import Namespace
imdb = Namespace('http://imdb.org/')

def prova(info):
	#db = MySQLdb.connect("127.0.0.1","root","","imdb2",use_unicode=True,charset='utf8')
	#cursor = db.cursor()
	info_url = 'interview/%s' %id
	info_uri = URIRef(imdb[info_url])
	#people_graph.add((person_uri,imdb["interview"],info_uri))	
	#people_graph.add((info_uri,rdf["type"],imdb['Interview']))
	infos = info.split(',')
	#print infos
	journal = infos[0]
	print infos
	journals = journal.split('"')
	journal = journals[1]
	country = journals[2].replace('(','').replace(')','')
	date=''
	author=''
	title=''
	if 'by: ' in info:
		author=info.split('by: ')[1].split(',')[0]
		title=info.split('by: ')[1].split(',')[1].replace('"','')
	elif infos[len(infos)-1][-1] == '"':
		title = infos[len(infos)-1].replace('"','')
	try:
		date = dparser.parse(infos[1],fuzzy=False)
		date = date.strftime('%d/%m/%Y')
	except:
		date=''	
	if author !='':
		author = author.replace(' ','_')		
		author_url = 'person/%s' %author
		author_uri = URIRef(imdb[author_url])
		#people_graph.add((info_uri,dc["creator"],author_uri))
		#people_graph.add((author_uri,rdf["type"],foaf["Person"]))
		#people_graph.add((author_uri,foaf["name"],Literal(author)))
		print author
	if journal !='':
		journal_url='journal/%s' %journal
		journal_uri = URIRef(imdb[journal_url])
		#people_graph.add((info_uri,imdb["journal"],journal_uri))
		#people_graph.add((journal_uri,rdf["type"],imdb['Journal']))
		print journal
	if date != '':
		print date
		#people_graph.add((info_uri,dc["created"],Literal(date)))
	if title != '':
		print title
		#people_graph.add((info_uri,dc["title"],Literal(title)))
	if country != '':

		country_url='country/%s' %country
		country_url= country_url.replace('/ ' ,'/').replace(' ','_')
		country_uri = URIRef(imdb[country_url])
		#people_graph.add((info_uri,imdb["country"],country_uri))
		#people_graph.add((country_uri,rdf["type"],imdb['Country']))
		print country_uri
	

	#db.close()
	

	