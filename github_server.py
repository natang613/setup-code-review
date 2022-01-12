import firebase_admin
from firebase_admin import db
from flask import Flask, request, render_template
from github import Github

cred_obj = firebase_admin.credentials.Certificate("auditech-877eb-firebase-adminsdk-2zdh1-68c67d54b7.json")
default_app = firebase_admin.initialize_app(cred_obj, {
    'databaseURL': "https://auditech-877eb-default-rtdb.firebaseio.com/"
})

app = Flask(__name__, template_folder='templates')

git = Github("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")


@app.route('/')
def open_html():
    return render_template('display.html')


@app.route('/hooks', methods=["GET", "POST"])
def pull_requests():
    if request.method == "POST":

        data = request.json
        if "pull_request" in data:
            data_to_store = {}
            pr_number = data["number"]
            action = data["action"]
            if action != "opened" and action != "closed":
                action = "opened"
            data_to_store["status"] = action
            data_to_store["author"] = data["pull_request"]["base"]["user"]["login"]
            data_to_store["created_at"] = str(data["pull_request"]["created_at"]).replace("T", " ").replace("Z", "")
            data_to_store["updated_at"] = str(data["pull_request"]["updated_at"]).replace("T", " ").replace("Z", "")
            data_to_store["assignees"] = ",".join([x["login"] for x in data["pull_request"]["assignees"]])
            data_to_store["requested_reviewers"] = ",".join(
                [x["login"] for x in data["pull_request"]["requested_reviewers"]])
            data_to_store["repo"] = data["pull_request"]["base"]["repo"]["full_name"]
            ref = db.reference("/" + str(pr_number))
            ref.set(data_to_store)
    else:
        ref = db.reference("/")
        prs = ref.get()
        return prs
    return "welcome guys"


if __name__ == '__main__':
    app.run(debug=True)
