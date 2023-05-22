import os
import logging
from urllib.parse import urlparse
from web_qa2 import crawls, process, tokenize, answer_question, answer_question2
from flask import Flask, request, session, render_template, jsonify
from pandas import read_json
import pandas as pd
import uuid
#from flask_sqlalchemy import SQLAlchemy
#from flask_migrate import Migrate
import psycopg2
import json

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
app.config['SESSION_COOKIE_MAX_SIZE'] = 20000

logger = logging.getLogger(__name__)

#db = SQLAlchemy(app)
#migrate = Migrate(app, db)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subscribe', methods=["POST"])
def register():
    response_object = {
        "status": False,
        "message": "Invalid payload"
    }

    post_data = request.get_json()
    if not post_data:
        return jsonify(response_object), 200

    email = post_data.get("email")

    #try:
    #     user = User.query.filter_by(email=email).first()
    #     if not user:
    #         user = User(email=email)
    #         user.insert()

    conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
                )

    # Open a cursor to perform database operations
    cur = conn.cursor()
    cur.execute('INSERT INTO accounts (email_id,details)'
                'VALUES (%s, %s)',
                (email,'')
                )
    conn.commit()

    cur.close()
    conn.close()


    response_object["status"] = True
    response_object["message"] = f"{email} was added!"
    response_object["data"] = {
        "email_id": email
    }
    return jsonify(response_object), 200

    # except Exception as e:
    #     response_object["message"] = "Try again"
    #     return jsonify(response_object), 200

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


    if full_url.startswith('http'):
        df_text = pd.read_csv('processed/scraped.csv', index_col=0)
    else:
        df_text=pd.DataFrame(['0',full_url]).T
    df_text.columns = ['title', 'text']


    response_object["status"] = True
    response_object["message"] = "Crawling and processing completed successfully!"
    if(len(df_text.iloc[0]['text'])<=100):
        response_object["message"]+="\n\nWARNING: length of scraped text less than 100 characters!"

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
        response_object["message"] = "url or text is required"
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
    text_d=[]
    if full_url.startswith('http'):
        text_d=df_text.iloc[0]['text']
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
                response_object["data"]["answer"],text_d)
                )

    conn.commit()

    cur.close()
    conn.close()

    return jsonify(response_object), 200



@app.route('/qa877', methods=["POST"])
def qa877():
    response_object = {
        "status": False,
        "message": "Invalid payload"
    }

    post_data = request.get_json()
    if not post_data:
        return jsonify(response_object), 200

    max_tokens = os.environ.get("MAX_TOKENS")
    api_key = os.environ['OPENAI_KEYV']
    
    text = post_data.get("text")
    query = post_data.get("query")
    a_id = post_data.get("id")
    msg = post_data.get("mesg")
    if not query and not(text and a_id):
        response_object["message"] = "query and text or article_id are required"
        return jsonify(response_object), 200
    
    conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
                )

    if not a_id:
        a_id=str(uuid.uuid4())





        df = tokenize(text, api_key, int(max_tokens))

        if not msg:
            answer,msg=answer_question2(df, question=query)
        else:
            answer,msg=answer_question2(df, question=query,mesg=msg)


        # Open a cursor to perform database operations
        cur = conn.cursor()
        cur.execute('INSERT INTO qa2 (link,question,answer,text_data,article_id,df,message)'
                    'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (text,
                    query,
                    answer,[],a_id,json.dumps(df.to_json()),json.dumps(msg))
                    )

        conn.commit()

        cur.close()
        conn.close()

    else:
        cur = conn.cursor()
        sql="""select df from qa2 where article_id = %s order by created_at asc limit 1"""
        #I've checked for potential issues where you submit just an id without text, and hence 
        # for multiple rows for same  article id df is null.
        #However in these cases, the query just selects the non-null (unique) df value, so all good!
        
        cur.execute(sql,[a_id])
        results = cur.fetchall()
        print("---------------------------------")
        #print(results)
        print("---------------------------------")
        #print(results[0][0])
        
        df = pd.DataFrame.from_dict(json.loads(results[0][0]))

        if not msg:
            answer,msg=answer_question2(df, question=query)
        else:
            answer,msg=answer_question2(df, question=query,mesg=msg)

        cur.execute('INSERT INTO qa2 (link,question,answer,text_data,article_id,message)'
                'VALUES (%s, %s, %s, %s, %s, %s)',
                ([],
                query,
                answer,[],a_id,json.dumps(msg))
                )


        conn.commit()

        cur.close()
        conn.close()        
 




    response_object["message"] = msg
    response_object["status"] = True
    response_object["answer"] = answer
    response_object["id"] = a_id
    return jsonify(response_object), 200
