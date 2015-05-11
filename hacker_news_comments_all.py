import urllib2
import json
import datetime
import time
import pytz
import psycopg2
import re
import HTMLParser

###
### Define database parameters here
###

host = "localhost"
dbname = "hacker_news"
user = "postgres"
password = "1234"

# Set up database connection settings and other parameters

ts = str(int(time.time()))
hitsPerPage = 1000
tag = re.compile(r'<[^>]+>')
h = HTMLParser.HTMLParser()
conn_string = "host=%s dbname=%s user=%s password=%s" % (host, dbname, user, password)
db = psycopg2.connect(conn_string)
cur = db.cursor()

# Set up HN comment database table schema
cur.execute("DROP TABLE IF EXISTS hn_comments;")
cur.execute("CREATE TABLE hn_comments (objectID int PRIMARY KEY, story_id int, parent_id int, comment_text varchar, num_points int, author varchar, created_at timestamp);")

num_processed = 0

while True:
	try:
		# Retrieve HN comments from the Algolia API; finds all comments before timestamp of last known submission time
		url = 'https://hn.algolia.com/api/v1/search_by_date?tags=comment&hitsPerPage=%s&numericFilters=created_at_i<%s' % (hitsPerPage, ts)
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		
		data = json.loads(response.read())
		comments = data['hits']
		ts = comments[-1 + len(comments)]['created_at_i']
		
		for comment in comments:
		
			# if a comment does *not* have a parent_id key, it's definitely [dead] and should not be recorded
			if 'parent_id' in comment.keys():
		
				# make sure we remove smartquotes/HTML tags/other unicode from comment text
				comment_text = tag.sub(' ', h.unescape(comment['comment_text'])).translate(dict.fromkeys([0x201c, 0x201d, 0x2011, 0x2013, 0x2014, 0x2018, 0x2019, 0x2026, 0x2032])).encode('utf-8')
				
				# EST timestamp since USA activity reflects majority of HN activity
				created_at = datetime.datetime.fromtimestamp(int(comment['created_at_i']), tz=pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')
				
				parent_id = None if comment['parent_id'] is None else int(comment['parent_id'])
				story_id = None if comment['story_id'] is None else int(comment['story_id'])
				
				SQL = "INSERT INTO hn_comments (objectID, story_id, parent_id, comment_text, num_points, author, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)"
				insert_data = (int(comment['objectID']), story_id, parent_id, comment_text, comment['points'], comment['author'], created_at,)
				
				try:
					cur.execute(SQL, insert_data)
					db.commit()
					
				except Exception, e:
					print insert_data
					print e
		
		# If there are no more HN comments, we're done!
		if (data["nbHits"] < hitsPerPage):
			break
		
		num_processed += hitsPerPage
		
		if num_processed % 100000 == 0:
			# write to console periodically to make sure everything's working
			print "%s HN Comments Processed: %s" % (num_processed, datetime.datetime.now())
		
		# make sure we stay within API limits
		time.sleep(3600/10000)

	except Exception, e:
		print e

# Create sensible indices and vacuum the inserted data
cur.execute('CREATE UNIQUE INDEX objectID_commentx ON hn_comments (objectID);')
cur.execute('CREATE INDEX created_at_commentx ON hn_comments (created_at);')
cur.execute('CREATE INDEX story_id_commentx ON hn_comments (story_id);')
db.commit()

db.set_isolation_level(0)
cur.execute('VACUUM ANALYZE hn_comments;')
db.close()