import os
import logging
from urllib.parse import urlparse
from web_qa2 import crawl, process, tokenize, answer_question
from flask import Flask, request, session, render_template, jsonify
from pandas import read_json
#from flask_sqlalchemy import SQLAlchemy
#from flask_migrate import Migrate
import psycopg2

from dotenv import load_dotenv
load_dotenv()

# url = urlparse(os.environ['DATABASE_URL'])
# dbname = url.path[1:]
# user = url.username
# password = url.password
# host = url.hostname
# port = url.port

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.secret_key = os.environ.get("SECRET_KEY")
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://khzjgfjukljxhl:84d6fc54ccf830b387f54d8cf0ca752653397c224d8b2789412190536e486758@ec2-3-209-124-113.compute-1.amazonaws.com:5432/d2si0e1uqohc5h'

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
    if not post_data:
        return jsonify(response_object), 200

    full_url = post_data.get("url")
    if not full_url:
        response_object["message"] = "url is required"
        return jsonify(response_object), 200

    crawl(full_url)
    domain = urlparse(full_url).netloc
    process(domain)

    max_tokens = os.environ.get("MAX_TOKENS")
    api_key = os.environ.get("OPENAI_API_KEY")
    logger.info(f"max_tokens: {max_tokens}")

    df = tokenize(api_key, int(max_tokens))

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

    # conn = psycopg2.connect(
    #             dbname=dbname,
    #             user=user,
    #             password=password,
    #             host=host,
    #             port=port
    #             )

    # # Open a cursor to perform database operations
    # cur = conn.cursor()
    # cur.execute('INSERT INTO qa2 (URL,question,answer)'
    #             'VALUES (%s, %s, %s)',
    #             (full_url,
    #             question,
    #             response_object["data"]["answer"])
    #             )

    # conn.commit()

    # cur.close()
    # conn.close()

    return jsonify(response_object), 200