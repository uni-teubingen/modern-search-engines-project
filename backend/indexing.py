# 1. Web Crawling & Indexing
#Crawl the web to discover **English content related to Tübingen**. The crawled content should be stored locally. 
#If interrupted, your crawler should be able to re-start and pick up the crawling process at any time.
import sqlite3
import os
from tokenization import tokenize
from db import DB_PATH
import warnings


# Return the entire textual content of a webpage saved in the db via its id
# @parm id : int
# return content : String
def retrieve_content_by_id(id):
	table = "pages"
	with sqlite3.connect(DB_PATH) as conn:
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute(f"SELECT content FROM {table} WHERE id = ?;", (id,))
		row = cursor.fetchone()
		return row["content"]

# Add tokenized terms with their frequency and corresponding ID into the database
# @param id : int
# @param tokens(token, frequency) : set(String, int)
# return None
def add_tokens_to_db(id, tokens):
	table = "tfs"
	with sqlite3.connect(DB_PATH) as conn:
		cursor = conn.cursor()
		# Add nonexistent tokens to the DB
		cursor.execute(f"PRAGMA table_info({table});")
		exisitng_tokens = {row[1] for row in cursor.fetchall()}
		for token in tokens:
			if token not in exisitng_tokens:
				cursor.execute(f"ALTER TABLE {table} ADD COLUMN {token} INTEGER DEFAULT 0;")
		# Add Values to DB (Parsing a single command to save runtime)
		update_token = ", ".join(f"{token} = ?" for token in tokens)
		update_command = f"UPDATE {table} SET {update_token} WHERE idxid = ?;"
		value_pair = list(tokens.values()) + [id]
		cursor.execute(update_command, value_pair)


# Index a page by tokenizing its contence in a term-frequency table
# @param id : int
# return None
def index(id):
    # Get Raw textual content as an unparsed String
	RAW_CONTENT = retrieve_content_by_id(id)
	#Just there for potential errors
	if RAW_CONTENT is None:
		warnings.warn('Page with id : ' + str(id) + " does not have any content")
		return None
	# Tokenize content to get library with terms and their frequencies
	TOKENIZED_CONTENT = tokenize(RAW_CONTENT)
	# Update the DB to include the term frequencies of the new documents
	add_tokens_to_db(id, TOKENIZED_CONTENT)