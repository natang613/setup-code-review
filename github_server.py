#######
# In order to run this server I used "ngrok" to obtain a public url address from my local ip.
# (This can be done only after the server is running. Every run there is a different url.
# I entered that new url to github web hooks and allowed the pull requests.
# I used Firebase as my database and used their storage to store the screenshot of the pull request.
# I received all notifications that had to do with the pull request and was able to decide if the pull
# request was closed or not
# created by @Natan Ginsberg
import os
import uuid

import chromedriver_autoinstaller
import firebase_admin
from firebase_admin import db, storage
from flask import Flask, request, render_template
from github import Github
from selenium import webdriver

cred_obj = firebase_admin.credentials.Certificate("auditech-877eb-firebase-adminsdk-2zdh1-68c67d54b7.json")
default_app = firebase_admin.initialize_app(cred_obj, {
    'databaseURL': "https://auditech-877eb-default-rtdb.firebaseio.com/",
    'storageBucket': "auditech-877eb.appspot.com"
})

app = Flask(__name__, template_folder='templates')

git = Github("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")


@app.route('/')
def open_html():
    return render_template('display.html')


def upload_image(url):
    fileName = "temp.png"
    bucket = storage.bucket()
    blob = bucket.blob(fileName + url)
    blob.upload_from_filename(fileName)
    UUID = uuid.uuid4()
    # adding a token to access the picture
    metadata = {"metadata": {"metadata": {"contentType": "image/png", "firebaseStorageDownloadTokens": UUID}}}
    blob.metadata = metadata
    blob.patch()
    blob.make_public()
    os.remove(fileName)
    return blob.public_url + "?alt=media&token=" + str(UUID)


def take_screenshot(url):
    chromedriver_autoinstaller.install()
    browser = webdriver.Chrome()
    browser.get(url)
    browser.save_screenshot('temp.png')


def upload_image_of_pr(url):
    try:
        take_screenshot(url)
        return upload_image(url)
    except:
        return ""


@app.route('/hooks', methods=["GET", "POST"])
def pull_requests():
    if request.method == "POST":
        data = request.json
        if "pull_request" in data:
            try:
                url_address = upload_image_of_pr(data["pull_request"]["html_url"])
                data_to_store = {}
                pr_number = data["number"]
                repo_name = data["pull_request"]["base"]["repo"]["full_name"]
                action = data["action"]
                if action != "opened" and action != "closed":
                    action = "opened"
                data_to_store["url"] = url_address
                data_to_store["status"] = action
                data_to_store["author"] = data["pull_request"]["base"]["user"]["login"]
                data_to_store["created_at"] = str(data["pull_request"]["created_at"]).replace("T", " ").replace("Z", "")
                data_to_store["updated_at"] = str(data["pull_request"]["updated_at"]).replace("T", " ").replace("Z", "")
                data_to_store["assignees"] = ",".join([x["login"] for x in data["pull_request"]["assignees"]])
                data_to_store["requested_reviewers"] = ",".join(
                    [x["login"] for x in data["pull_request"]["requested_reviewers"]])
                data_to_store["repo"] = repo_name
                ref = db.reference("/" + str(repo_name) + "/" + (str(pr_number)))
                ref.set(data_to_store)
            except:  # checking that this is the right format and in order that the server should not crash
                return ""
    else:
        try:
            ref = db.reference("/")
            prs = ref.get()
            return prs
        except:
            return "We are unable to process your request at this moment"
    return "success 200"


if __name__ == '__main__':
    app.run()
