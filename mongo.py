import pymongo as pm
import json
'''uri = "mongodb+srv://avanish63:avanish2003@cluster0.vy9p2rm.mongodb.net/?retryWrites=true&w=majority"
client = pm.MongoClient(uri)
db = client["Project_Catalog"]
collection = db['Upload_Data']
with open("uploadps.json", encoding = "utf-8") as f:
    data = json.load(f)
x = collection.insert_many(data)
print(x.inserted_ids)
'''

from pymongo import MongoClient
# Connect to MongoDB
#client = MongoClient('mongodb://localhost:27017/')
uri = "mongodb+srv://avanish63:avanish2003@cluster0.vy9p2rm.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["Project_Catalog"]
collection = db['Projects']
# Retrieve data
data = collection.find()
# Print data
for document in data:
    print(document)


import json
with open("uploadps.json", encoding = "utf-8") as f:
    data = json.load(f)
print(data[0])

from pymongo import MongoClient
# Connect to MongoDB
#client = MongoClient('mongodb://localhost:27017/')
uri = "mongodb+srv://avanish63:avanish2003@cluster0.vy9p2rm.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["Project_Catalog"]
collection = db['Upload_Data']
results = collection.find({'Guide': {"$regex": "MILIND"}})
# print(type(results))
for res in results:
    print(res['Title'])


from bs4 import BeautifulSoup
import requests
import pandas as pd

url = "https://facultyprofile.vit.edu/department/vit-Computer"
response = requests.get(url)
# Check if the response was successful
if response.status_code == 200:
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, "html.parser")
    faculty = []
    for d in soup.find_all('div', {'class':'col-md-6 col-sm-8 col-lg-3'}):
        prof = []
        img = d.find('img')['src']
        name = d.find("h5", {'class':"font-wt-semi-light name-text"}).text.replace('\n', '')
        try:
            profile = "https://facultyprofile.vit.edu/" + d.find('a')['href'][3:]
        except:
            profile = "https://facultyprofile.vit.edu/profile/" + name.replace(' ', '-')
        designation = d.find('span', {'class':'ft-size-14 text-light-black desig-text'}).text.replace('\n', '')
        new = requests.get(profile)
        soup_new = BeautifulSoup(new.text, "html.parser")
        try:
            department = soup_new.find_all('div', {'class':'col-lg-4 col-md-5 col-sm-6 text100'})[1].text.replace('\n', '')
        except:
            department = "NA"
        try:
            email = soup_new.find_all('div', {'class':'col-lg-4 col-md-5 col-sm-6 text100'})[2].text.replace('\n', '')
        except:
            email = "NA"
        prof.extend([name, img, designation, department, email])
        faculty.append(prof)
faculty_csv = pd.DataFrame(faculty, columns=['Name', 'Image', 'Designation', 'Department', 'Email'])
faculty_csv.to_csv("faculty.csv", encoding='utf-8', index = False)