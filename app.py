import os
import logging
from urllib.parse import urlparse
from web_qa2 import crawl, process, tokenize, answer_question
from flask import Flask, request, session, render_template, jsonify
from pandas import read_json

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.secret_key = os.environ.get("SECRET_KEY")

logger = logging.getLogger(__name__)


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

    return jsonify(response_object), 200
