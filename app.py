import os
import logging
from urllib.parse import urlparse
from web_qa2 import crawls, process, tokenize, answer_question
from flask import Flask, request, session, render_template, jsonify
from pandas import read_json
import pandas as pd
#from flask_sqlalchemy import SQLAlchemy
#from flask_migrate import Migrate
import psycopg2

from dotenv import load_dotenv
load_dotenv()

url = urlparse(os.environ['DATABASE_URL'])
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.secret_key = os.environ.get("SECRET_KEY")

logger = logging.getLogger(__name__)

#db = SQLAlchemy(app)
#migrate = Migrate(app, db)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/crawl', methods=["POST"])
def crawl_url():
    response_object = {
        "status": False,
        "message": "Invalid payload"
    }

    post_data = request.get_json()
    #print(post_data)
    if not post_data:
        return jsonify(response_object), 200

    full_url = post_data.get("url")
    if not full_url:
        response_object["message"] = "url or text is required"
        return jsonify(response_object), 200

    if full_url.startswith('http'):
        crawls(full_url)
        domain = full_url.replace('/','').replace(':','')
        process(domain)
    else:
        domain = full_url[:10]

    max_tokens = os.environ.get("MAX_TOKENS")
    api_key = os.environ['OPENAI_KEYV']
    logger.info(f"max_tokens: {max_tokens}")

    df = tokenize(full_url, api_key, int(max_tokens))

    # store the dataframe as json file
    file_name = f"{domain}.json"
    with open(os.path.join("processed", file_name), "w") as f:
        f.write(df.to_json())

    session[full_url] = domain + ".json"

    response_object["status"] = True
    response_object["message"] = "Crawling and processing completed successfully"
    response_object["data"] = {
        "df": df.to_json()
    }

    return jsonify(response_object), 200


@app.route('/question', methods=["POST"])
def question():
    response_object = {
        "status": False,
        "message": "Invalid payload"
    }

    post_data = request.get_json()
    if not post_data:
        return jsonify(response_object), 200

    full_url = post_data.get("url")
    if not full_url:
        response_object["message"] = "url is required"
        return jsonify(response_object), 200

    question = post_data.get("question")
    if not question:
        response_object["message"] = "question is required"
        return jsonify(response_object), 200

    df = None
    if full_url in session:
        # load the dataframe from json file
        file_name = session[full_url]
        with open(os.path.join("processed", file_name), "r") as f:
            df = read_json(f)

    else:
        response_object["message"] = "url not found"
        return jsonify(response_object), 200

    response_object["status"] = True
    response_object["message"] = "Question answered successfully"
    response_object["data"] = {
        "answer": answer_question(df, question=question)
    }

    df_text=pd.read_csv('processed/scraped.csv')
    conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
                )

    # Open a cursor to perform database operations
    cur = conn.cursor()
    cur.execute('INSERT INTO qa2 (link,question,answer,text_data)'
                'VALUES (%s, %s, %s, %s)',
                (full_url,
                question,
                response_object["data"]["answer"],df_text.iloc[0]['text'])
                )

    conn.commit()

    cur.close()
    conn.close()

    return jsonify(response_object), 200