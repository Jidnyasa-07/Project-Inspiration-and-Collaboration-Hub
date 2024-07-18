from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from flask_mysqldb import MySQL
from functools import wraps
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash
import re
import requests
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_mail import Mail
from flask_caching import Cache
import redis
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import json
import requests


app = Flask(__name__)
# cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_HOST': 'localhost', 'CACHE_REDIS_PORT': 6379})


cache = Cache(app, config={'CACHE_TYPE': 'simple'})


app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'your_gmail'
app.config['MAIL_PASSWORD'] = 'your_password'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
posta = Mail(app)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'login_signup_db'

# Secret key for session management
app.secret_key = secrets.token_hex(32)
# Initialize MySQL
mysql = MySQL(app)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Signup page
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Hash password
        hashed_password = generate_password_hash(password)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO users VALUES (NULL, % s, % s, % s)', (username, email, hashed_password, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
            return redirect(url_for('login'))
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)

name = []

# Login page
# @app.route('/')
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        result = cursor.execute('SELECT * FROM users WHERE email = %s', (username, ))#
        account = cursor.fetchone()
        if result:
            if check_password_hash(account['password'], password):
                # Set session variables
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['email']
                session['name'] = account['name']
                msg = 'Logged in successfully !'
                name = [{'profile': account['name']}]
                # return render_template("index.html", name = name)
                return redirect(url_for("home_login", name = name))
            else:
                msg = 'Incorrect username / password !'
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)

@app.route('/profile.html', methods = ['GET'])
@login_required
@cache.cached(timeout=120)
def profile():
    if 'loggedin' in session:
        profile = []
        profile.append({'name': session['name'], 'username': session['username'], 'id': session['id']})
        return render_template('profile.html', profile = profile)
    else:
        return redirect(url_for('login'))


# Logout
@app.route('/logout')
@login_required
def logout():
    session.clear()
    # redirect user to login page
    response = make_response(redirect(url_for('login')))
    # set cache control headers to prevent back button access
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response



@app.route('/hack.html', methods = ['GET'])
@cache.cached(timeout=120)
# @login_required
def hack():
    # if 'loggedin' in session:
        api_url = 'https://devpost.com/api/hackathons?page={}'
        headers = {'authority': 'devpost.com',
                    'method': 'GET',
                    'path': '/api/hackathons',
                    'scheme': 'https',
                    'accept': '*/*',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'en-US,en;q=0.9',
                    'cookie': '__mp_opt_in_out_1c828346e9fae00dbc3a117657f65895=1; _ga=GA1.2.1551603842.1678371556; _gid=GA1.2.496634131.1678371556; ln_or=eyIxNTE2MDEiOiJkIn0%3D; __hstc=261817746.457209b0a2055c66739254be367ca00e.1678371556858.1678371556858.1678371556858.1; hubspotutk=457209b0a2055c66739254be367ca00e; __hssrc=1; mp_1c828346e9fae00dbc3a117657f65895_mixpanel=%7B%22distinct_id%22%3A%20%221d00a18e5f968121848821242445edeb9668acefdbe3a3724f08eb0a361ccc7d3ffbd715ce26dee7313dfe7dcc19cbe0585c%22%2C%22%24device_id%22%3A%20%22186c6bd8365501-0cf4dfa8fc0a1c-26031951-100200-186c6bd83664a3%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22%24user_id%22%3A%20%221d00a18e5f968121848821242445edeb9668acefdbe3a3724f08eb0a361ccc7d3ffbd715ce26dee7313dfe7dcc19cbe0585c%22%2C%22%24search_engine%22%3A%20%22google%22%7D; __atuvc=2%7C10; __atuvs=6409eae34e6a6651001; __atssc=google%3B1; __hssc=261817746.2.1678371556859; AWSALB=lFcQfSzaYmvhfYvzmL3ONcrEEm3Jhem66C2XZyBWzPxl/CaaG7bVX1NbNFR2H8vIGOktjC+4IplZHXTHYtJVXl5hDw6lAMvZD4OFZtMgY6CJ8p1KS9WjTke5bGLD; AWSALBCORS=lFcQfSzaYmvhfYvzmL3ONcrEEm3Jhem66C2XZyBWzPxl/CaaG7bVX1NbNFR2H8vIGOktjC+4IplZHXTHYtJVXl5hDw6lAMvZD4OFZtMgY6CJ8p1KS9WjTke5bGLD; _devpost=TnZsRTd1bWNPQ1RoczJEK3IvckVTVldRVjQ3T004ZjZpZTg3ZmtYdkZuTjZ6VmdqNElYRVg0SU02a3dkZmwvMkFyKzlPZGdzNElMRmhqdU16VHV4Y2VONGRZT2pQa0FUdzJCVThOa0h6T2xYb2NidjZJOGhOelhJN28xWk44R0p2SHlmZWw4MXdPdVlUUlU5bEk2ck45NDhkUlpJS3pLSWlhN1ZSSzRJODVadmxZdXNzb0tXZlU1b3dEdEk2ZldBT0drQ1o0Wkg2M29nWHMxUEV6cnYxNTBaeE1WVlFGa3JmbnBPdkpKd09oK3ozc01CSWZRWDdrbGs4K3RwcGtTM040V2VWb2k5NzY5NG40WW5iK3hwckpKY3pRWk9vUWZaQ1BqUkxZRmFVYTFOMll6ejcwdVBEUkdKeG9DeEtpODVwSjMwWkM2Vkhsd29HNVdYeU9mYmxjZ2xiRUNlSlNwYUg2T09nS1l1YzRCNmt6c3k0TW13NTM4MnpxWGRJZ2w5V2F5ZnBsQm41U01Ia0RwU0ZaM0FEOVJlTVJVUk1lU2ZDZkxIaU5mZ2hDdz0tLVhTN2xPVXZiS0k1TC9FV1lISkN0L0E9PQ%3D%3D--ec701d85a43139ea66fe40ff2406a2dfcc0f1981',  
                    'if-none-match': 'W/"6dc57e137c1ac6cac457513c739439e5"',
                    'referer': 'https://devpost.com/hackathons',
                    'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
        hack_results = []
        for p in range(3):
            r = requests.get(api_url.format(p+1),headers=headers)
            data = r.json()
            for h in data['hackathons']:
                hack_results.append({'title':h['title'], "link":h['url'], "date": h['submission_period_dates'], "img":h['thumbnail_url']})
        # Render hackathon data on HTML page using CSS
        return render_template('hack.html', hackathons=hack_results, name =["loggedin"])
    # else:
        # return redirect(url_for('login'))

@app.route("/research.html", methods=["GET", "POST"])
@login_required
def research():
    if "loggedin" in session:
        if request.method == "POST":
            results = []
            # Get the search query from the form
            query = request.form["query"]
            # Create the URL for the search
            url = f"https://scholar.google.com/scholar?q={query}"
            # Send a GET request to the URL
            response = requests.get(url)
            # Check if the response was successful
            if response.status_code == 200:
                # Parse the HTML content of the page
                soup = BeautifulSoup(response.text, "html.parser")
                # Find the links to the research papers
                links = soup.find_all("h3", class_="gs_rt")
                # Add the links to the results list
                for link in links:
                    title = link.find("a").text
                    href = link.find("a")["href"]
                    results.append({"title": title, "link": href})
                return render_template("research.html", results=results)
        else:
            return render_template("research.html", name =["loggedin"])
    else:
        return redirect(url_for("login"))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = % s', (email, ))
        account = cursor.fetchone()
        if account:
            token = secrets.token_hex(16)
            sender_email = 'hirkanihaider@gmail.com'
            sender_password = 'habfvsqquiwaiwqb'
            recipient_email = email
            subject = 'Password reset request'
            body = f'To reset your password, click the following link: {url_for("reset_password", token=token, _external=True)}'
            message = MIMEMultipart()
            message['From'] = sender_email
            message['To'] = recipient_email
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                smtp.starttls()
                smtp.login(sender_email, sender_password)
                smtp.send_message(message)
            flash('An email has been sent to your email address with instructions to reset your password.')
            return redirect(url_for('login'))
        else:
            return render_template('forgot_password.html')
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm_password']
        if password == confirm:
            # Hash password
            hashed_password = generate_password_hash(password)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE email = % s', (email, ))
            account = cursor.fetchone()
            if account:
                cursor.execute('UPDATE users SET password = %s WHERE email = %s', (hashed_password, email,))
                mysql.connection.commit()
            else:
                return render_template('reset_password.html', token=token)
        else:
            return render_template('reset_password.html', token=token)
        flash('Your password has been reset. Please login with your new password.')
        return redirect(url_for('login'))
    # If the token is valid, display the password reset form
    return render_template('reset_password.html', token=token)


@app.route('/projects.html', methods = ['GET'])
@cache.cached(timeout=120)
def project():
    return render_template('projects.html')

def link_replace(x):
    x = x.replace(" ", "")
    newlink = "https://drive.google.com/"
    l = x.split("/")
    s = l[3]
    upd = "uc?export=view&id="+s.replace("open?id=","")
    return newlink+upd

@app.route('/projects.html', methods = ['POST'])
def project_post():
        domain = request.form['dropdown']
        search = request.form['search']
        client = MongoClient('mongodb://localhost:27017/')
        uri = "mongodb+srv://avanish63:avanish2003@cluster0.vy9p2rm.mongodb.net/?retryWrites=true&w=majority"
        client = MongoClient(uri)
        db = client["Project_Catalog"]
        collection = db['Final-Catalogue-Of-Project']
        results = collection.find({domain: {"$regex": search}})
        l = []
        for doc in results:
            try:
                doc["Photos"] = list(map(lambda x: link_replace(x), doc['Photos'].split(',')))
            except:
                doc["Photos"] = []
            l.append(doc)
        return render_template('projects.html', results = l)
    
@app.route('/blogs.html', methods = ['GET','POST'])
def blogs_post():
    if request.method=="POST":
        domain = request.form['dropdown']
        search = request.form['search']
        client = MongoClient('mongodb://localhost:27017/')
        uri = "mongodb+srv://avanish63:avanish2003@cluster0.vy9p2rm.mongodb.net/?retryWrites=true&w=majority"
        client = MongoClient(uri)
        db = client["Project_Catalog"]
        collection = db['Blogs-Catalogue']
        results = collection.find({domain: {"$regex": search}})
        l = []
        for doc in results:
            r = requests.get(doc['Link'])
            soup = BeautifulSoup(r.text,"html.parser")  
            for d in soup.select('source'):
                imglink = (d['srcset'])
                break
            doc['Img'] = imglink.split(",")[0]
            l.append(doc)
        return render_template('blogs.html', blogs = l)
    else:
        return render_template('blogs.html')



headers = {
    "Authorization":"Bearer ya29.a0AWY7CkkOnZT4VfrGJqcIiLvDgy9vyAPqqzo4423wXAjMBI4I1u1TzvxAVjEbwhDZVDpGk0bkFxY6tzz4jiMyS6LJQWU8pNoylLbkdua2f2e7b0XpyB1N3cHmZpd4Klplk28GuFx-vOMbwqKKWz21Z30OsGtjaCgYKAVQSARESFQG1tDrps1Tn8Y7GdL6ppyOrFScqqg0163"
}
 
para = {
    "name":"image.jpg",
    "parents":["1GXxI8ip5SJS9aRAfQhFM1jFtB_Ar0V6pJfe1f7ZEvhPDUOEWp5ojJK77pztmDAEGAOsm5KsS"]  #drive of folders
    # "parents":["1Ygfpjlk7WzPi6EP6eavdGVwgdteAn_FV"] 
}


@app.route("/upload_projects.html",methods=['GET','POST'])
def upload():
    status = ""
    # if request.method=='POST' and  'email' in request.form and  'name' in request.form and  'year' in request.form and  'projectTitle' in request.form and  'domain' in request.form and  'Description' in request.form and  'Technology' in request.form and  'Members' in request.form and  'Contact' in request.form and  'Guide' in request.form:
    if request.method == 'POST': 
        uri = "mongodb+srv://avanish63:avanish2003@cluster0.vy9p2rm.mongodb.net/?retryWrites=true&w=majority"
        client = MongoClient(uri)
        db = client["Project_Catalog"]
        collection = db['Final-Catalogue-Of-Project']
    
        email = request.form['email']
        project_name = request.form['name']
        year = request.form['year']
        title = request.form['projectTitle']
        domain = request.form['domain']
        description = request.form['Description']
        technology = request.form['Technology']
        members = request.form['Members']
        contact = request.form['Contact']
        guide = request.form['Guide']
        img = request.files['image']
        filename = secure_filename(img.filename)

        img.stream.seek(0)
        f = img.read()
    
        para['name'] = filename
        files = {
            'data':('metadata',json.dumps(para),'application/json;charset=UTF-8'),
            # 'file':open('C:/dev/html/static/images/{fname}'.format(fname=filename),'rb')
            'file':f
        }
        r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            headers=headers,
            files=files
        )
        id = r.json()['id']
        photo_link= "https://drive.google.com/open?id="+id

        collection.insert_one({
                'Email' : email,
                'Name' : project_name,
                'Year' : year,
                'Title' : title,
                'Domain' : domain,
                'Description' : description,
                'Technology' : technology,
                'Members' : members,
                'Contact' : contact,
                'Guide' : guide,
                'Photos' : photo_link
            })
        status = "Submited"
    else:
        status = "invalid data please fill the form again"
    return render_template("upload_projects.html",status = status)

@app.route('/web.html', methods = ['GET'])
@login_required
@cache.cached(timeout=120)
def udemy(): 
    if 'loggedin' in session:
        p = 1
        lang = 'en'
        pg_size = 60
        api_url = 'https://www.udemy.com/api-2.0/discovery-units/all_courses/?p={}&page_size={}&subcategory=&instructional_level=&lang={}&price=price-free&duration=&closed_captions=&subs_filter_type=&sort=newest&category_id=283&source_page=category_page&locale=en_US&currency=inr&navigation_locale=en_US&skip_price=true&sos=pc&fl=cat'
        r = requests.get(api_url.format(p, pg_size, lang))
        pages_api_url = ['https://www.udemy.com' + i['url'] for i in r.json()['unit']['pagination']['pages']]
        items = []
        for pg_api_url in pages_api_url:
            items += requests.get(pg_api_url).json()['unit']['items']
        udemy_courses_list = []
        for i in items:
            udemy_courses_list.append({'title':i['title'],'url':'https://www.udemy.com'+i['url'],'img':i['image_240x135'], 'desc': i['headline']})
        return render_template('web.html', results=udemy_courses_list, name =["loggedin"])
    else:
        return redirect(url_for('login'))

@app.route('/web.html', methods = ['POST'])
@login_required
def coursera(): 
    if 'loggedin' in session:
        q = request.form['options']
        ses = HTMLSession()
        URL = 'https://www.coursera.org/courses?query={}'.format(q)
        r = ses.get(URL)
        soup = BeautifulSoup(r.text, "html.parser")
        coursera_courses = []   
        for d in soup.select('div.css-1j8ushu'):
            name_c = d.find('h2').text
            img = d.select_one('img[src]')
            link = d.select_one('a[href]')
            ulink = 'https://www.coursera.org'+link['href']
            coursera_courses.append({'title':name_c,'url':ulink,'img':img['src']})
        return render_template('web.html', courses=coursera_courses, name =["loggedin"])
    else:
        return redirect(url_for('login'))

@app.route("/card.html", methods=['GET'])
def cards():
    client = MongoClient('mongodb://localhost:27017/')
    uri = "mongodb+srv://avanish63:avanish2003@cluster0.vy9p2rm.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri)
    db = client["Project_Catalog"]
    collection = db['Faculty-DB']
    l = []
    for doc in collection.find():
        l.append(doc)
    return render_template('card.html', cards=l)

# Define the index (home) page
# @app.route('/index.html')
# @login_required
@app.route('/', methods = ['GET'])
def home():
    if 'loggedin' not in session:
        return render_template("index.html")
    return redirect(url_for('home_login'))

@app.route('/index.html', methods = ['GET'])
@login_required
def home_login():
    return render_template("index.html", name =["loggedin"])

# after request hook to set no-cache headers for all responses
@app.after_request
def add_no_cache_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == "__main__":
    app.run(debug=True)