## **_To run:_**

```bash
# create and activate python environment
$ python -m venv .venv
$ .\.venv\Scripts\activate

# change directory
$ cd open-ai-app/

# install project requirements
$ pip install -r requirements.txt

# start application
$ flask run

# NOTE: All app configurations are inside .env file
```

## git stuff:
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/skandavivek/web-qa.git
git push -u origin main


## Things to improve:
- urls not just starting from http (maybe best to separate URL from text)
- possible issues with non standard string characters in free response
- removing saving of files and instead directly accessing scraped file
- session cookies can't read large text (can do upto 847 words, so not bad...)