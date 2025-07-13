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
# return String
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
		existing_tokens = {row[1] for row in cursor.fetchall()}
		for token in tokens:
			if token not in existing_tokens:
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


# Create a df-table in the database, including all tokenized terms within every document in the database
# @param None
# return None
def create_dfs_table():
	table_tfs = "tfs"
	table_dfs = "dfs"
	with sqlite3.connect(DB_PATH) as conn:
		cursor = conn.cursor()
		# Get Total number of indexed documents
		indexed_documents = cursor.execute(f"SELECT COUNT (*) FROM {table_tfs}").fetchone()[0]
		# Fetch all Terms out of the tf-table in the database
		cursor.execute(f"PRAGMA table_info({table_tfs});")
		terms_and_id = cursor.fetchall()
		terms = [row[1] for row in terms_and_id[1:]]
		# Calculate DFs (Parsing a single command to save runtime)
		df_seperated = []
		for term in terms:
			df_part = (f"SUM(CASE WHEN) {term} <> 0 THEN 1 ELSE 0 END * 1.0 / {indexed_documents} AS {term}")
			df_seperated.append(df_part)
			dfs_select = ("SELECT" + ", ".join(df_seperated) + f" FROM {table_tfs}")
		dfs = cursor.execute(dfs_select).fetchone()
		# (Re)Initialize dfs-table
		cursor.execute(f"DROP TABLE IF EXISTS {table_dfs};")
		term_command = " ,".join(f"{term}" for term in terms)
		cursor.execute(f"CREATE TABLE {table_dfs} ({term_command});")
		placeholder_symbols = " ,".join("?" for _ in terms)
		cursor.execute(f"INSERT INTO {table_dfs} VALUES ({placeholder_symbols})", dfs)