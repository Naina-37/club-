from flask import Flask, flash, render_template, request, session, redirect, url_for
import hashlib
from hashlib import sha256
from session22C import MongoDBHelper  # Ensure this file is correctly imported
from bson import ObjectId
import json
from flask_socketio import SocketIO
from flask_socketio import emit
import os
from werkzeug.utils import secure_filename
import random


from cryptography.fernet import Fernet

# Flask app setup
web_app = Flask("PCTE Club Election")
web_app.secret_key = 'your_secret_key_here'
socketio = SocketIO(web_app)
# Initialize Fernet with a secret key (Store this securely)
key = Fernet.generate_key()
cipher_suite = Fernet(key)


web_app.config['UPLOAD_FOLDER'] = os.path.join(web_app.root_path, 'static/uploads')
if not os.path.exists(web_app.config['UPLOAD_FOLDER']):
    os.makedirs(web_app.config['UPLOAD_FOLDER'])


# Database helper instance
db_helper = MongoDBHelper()

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = hashlib.sha256("admin123".encode('utf-8')).hexdigest()  # Hashed password


# Home (Login Page)
@web_app.route("/", methods=["GET", "POST"])
def home():
    return render_template("register.html")
# Basketball Page
@web_app.route('/basketball')
def basketball():
    return render_template('basketball.html')

# Cricket Page
@web_app.route('/cricket')
def cricket():
    return render_template('cricket.html')
@web_app.route('/bad1')
def bad1():
    return render_template('bad1.html')
@web_app.route('/csr')
def csr():
    return render_template('csr.html')
@web_app.route('/the')
def the():
    return render_template('the.html')
@web_app.route('/tech')
def tech():
    return render_template('tech.html')
@web_app.route('/eoa')
def eoa():
    return render_template('eoa.html')
@web_app.route('/dance')
def dance():
    return render_template('dance.html')
@web_app.route('/football')
def football():
    return render_template('football.html')
@web_app.route('/music')
def music():
    return render_template('music.html')
@web_app.route('/table1')
def table1():
    return render_template('table1.html')
@web_app.route('/lie')
def lie():
    return render_template('lie.html')
@web_app.route('/about')
def about():
    return render_template('about.html')  # This will render the About Us page

@web_app.route('/contact')
def contact():
    return render_template('contact.html')  # This will render the Contact Us page
# Helper function to fetch candidates from the database
def get_candidates_from_db():
    try:
        # Fetch all the candidates from the 'candidates' collection
        candidates = db_helper.fetch({}, "candidates")  # 'candidates' is the collection name
        return candidates
    except Exception as e:
        print(f"Error fetching candidates: {e}")
        return []
# Route for viewing the candidates
@web_app.route("/view_candidates")
def view_candidates():
    # Fetch all candidates from the database using the helper function
    candidates = get_candidates_from_db()

    # Render the view_candidates.html template and pass the candidates data
    return render_template("view_candidates.html", candidates=candidates)




# User Registration
@web_app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        sports_club = request.form.getlist("sports_club")
        activity_club = request.form.getlist("activity_club")

        # Validation
        if not sports_club or not activity_club:
            flash("Please select at least one sport and one activity club.", "error")
            return redirect("/register")

        flash("Registration successful!", "success")
        return redirect("/login")
    return render_template("register.html")


# Login Page
@web_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check user credentials
        user = db_helper.find_one(
            collection_name="users",
            query={"username": username, "password": password}
        )
        
        if user:
            # Save user details in the session
            session['username'] = user['username']
            session['clubs'] = user['clubs']
            return redirect('/index')
        else:
            flash("Invalid username or password", "danger")
            return redirect('/login')
    return render_template('login.html')


# Fetch User from DB (Login Validation)
@web_app.route("/fetch-user", methods=["POST"])
def fetch_user_from_db():
    username = request.form["username"]
    password = hashlib.sha256(request.form["password"].encode('utf-8')).hexdigest()

    db_helper.collection = db_helper.db["users"]
    user = db_helper.fetch_one({"username": username, "password": password})

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session.update({"role": "admin", "username": ADMIN_USERNAME, "name": "Admin"})
        return redirect("/admin")

    if user:
        session.update({
            "role": "user",
            "username": user["username"],
            "name": user.get("name", ""),
            "registered_clubs": user.get("clubs", [])  # Save club IDs in the session
        })
        return redirect("/index")
    return render_template("error.html", message="Invalid credentials")


# User Dashboard

@web_app.route('/index')
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    # Fetch clubs the user is registered for
    clubs = session.get('clubs', [])
    
    # Fetch club details from the database
    clubs = db_helper.fetch(
        collection_name="clubs",
        query={"name": {"$in": clubs}}
    )
    return render_template('index.html', clubs=clubs)

from flask_socketio import SocketIO, emit
from flask import render_template, session, redirect

# Initialize SocketIO
socketio = SocketIO(web_app)

@web_app.route("/admin")
def admin_dashboard():
    if session.get("role") == "admin":
        # Fetch all users, clubs, and candidates
        users = db_helper.fetch({}, "users")  # Fetch all users
        clubs = db_helper.fetch({}, "clubs")  # Fetch all clubs
        candidates = db_helper.fetch({}, "candidates")  # Fetch all candidates
        
        # Fetch voting data
        votes = db_helper.fetch({}, "votes")
        
        # Map club names to users
        club_map = {club["_id"]: club["club_name"] for club in clubs}
        for user in users:
            user["club_name"] = club_map.get(user.get("club_id"), "No Club Assigned")
        
        # Group vote counts by position and candidate
        voting_stats = {}
        for candidate in candidates:
            position = candidate["position"]
            if position not in voting_stats:
                voting_stats[position] = []
            vote_count = sum(1 for vote in votes if vote["candidate_id"] == str(candidate["_id"]))
            voting_stats[position].append({
                "candidate_name": candidate["candidate_name"],
                "votes": vote_count
            })

        # Render the admin page with fetched data and voting stats
        return render_template(
            "admin.html",
            users=users,
            clubs=clubs,
            candidates=candidates,
            voting_stats=voting_stats,  # Send voting stats to the template
        )
    return redirect("/login")






# Add User

@web_app.route("/add-user", methods=["POST"])
def add_user_in_db():
    try:
        clubs = json.loads(request.form["clubs"])  # Convert the JSON string into a Python list

        # Ensure clubs is a valid list
        if not isinstance(clubs, list):
            raise ValueError("Clubs should be a list.")

        # Prepare the user document
        document = {
            "name": request.form["name"],
            "username": request.form["username"],
            "password": hashlib.sha256(request.form["password"].encode('utf-8')).hexdigest(),
            "role": "user",
            "clubs": clubs  # Store clubs correctly as a list
        }

        # Inserting user data into the database
        db_helper.insert("users", document)  # Pass collection name ("users") and document

        # Set session for the user
        session['name'] = document["name"]
        session['username'] = document["username"]
        session['role'] = "user"  # Set default role as "user"
        session['clubs'] = clubs  # Store clubs in the session

        # Redirect to user dashboard
        return redirect("/index")

    except ValueError as ve:
        return render_template("error.html", message=f"ValueError: {str(ve)}")

    except Exception as e:
        return render_template("error.html", message=f"Error: {str(e)}")

# Add Club


@web_app.route("/admin/add_club", methods=["GET", "POST"])
def add_club():
    if session.get("role") == "admin":
        if request.method == "POST":
            # Retrieve form data
            club_name = request.form.get("club_name")
            club_head = request.form.get("head")
            club_type = request.form.get("club_type")

            # Ensure all fields are filled
            if not club_name or not club_head or not club_type:
                flash("All fields are required!", "danger")
                return redirect("/admin/add_club")

            # Prepare the club data
            club_data = {
                "club_name": club_name,
                "club_head": club_head,
                "club_type": club_type
            }

            try:
                # Insert the data into your MongoDB 'clubs' collection
                db_helper.insert(collection_name="clubs", document=club_data)

                # Flash message and redirect
                flash("Club added successfully!", "success")

                # Get the updated club count from the database
            

                # Redirect to admin page with updated club count
                return redirect("/admin")  # Or wherever you want to show the updated count

            except Exception as e:
                flash(f"An error occurred: {e}", "danger")
                return redirect("/admin/add_club")  # Redirect back to the add club page in case of error

        # Handle GET request (render add club form)
        return render_template("add_club.html")

    else:
        flash("You are not authorized to access this page!", "danger")
        return redirect("/")  # Redirect to home or login page if not admin



            
# Helper function to fetch clubs from the database
def get_clubs_from_db():
    try:
        # Fetch all the clubs from the 'clubs' collection
        clubs = db_helper.fetch({}, "clubs")  # 'clubs' is the collection name
        return clubs
    except Exception as e:
        print(f"Error fetching clubs: {e}")
        return []

# Route for viewing the clubs
@web_app.route("/view_club")
def view_club():
    # Fetch all clubs from the database
    clubs = get_clubs_from_db()

    # Render the view_club.html template and pass the clubs data
    return render_template("view_club.html", clubs=clubs)
# Update Club
@web_app.route("/admin/update_club/<club_name>", methods=["GET", "POST"])
def update_club(club_name):
    if session.get("role") == "admin":
        club = db_helper.find_one("clubs", {"club_name": club_name})  # Fetch the club by club_name
        if club:
            if request.method == "POST":
                # Get the updated information from the form
                club_name = request.form["club_name"]
                club_head = request.form["club_head"]
                club_type = request.form["club_type"]
                
                # Update the club details in the database
                db_helper.update(
                    collection_name="clubs",
                    query={"club_name": club_name},  # Find the club by name
                    updated_data={"$set": {"club_name": club_name, "club_head": club_head, "club_type": club_type}},
                )
                flash("Club updated successfully!", "success")
                return redirect("/view_club")
            return render_template("update_club.html", club=club)
        else:
            flash("Club not found.", "danger")
            return redirect("/admin")
    return redirect("/login")
@web_app.route("/admin/delete_club/<club_name>", methods=["POST"])
def delete_club(club_name):
    if session.get("role") == "admin":
        club = db_helper.find_one("clubs", {"club_name": club_name})  # Fetch the club by club_name
        if club:
            # Delete the club from the database
            db_helper.delete(
                collection_name="clubs",
                query={"club_name": club_name}  # Find the club by club_name to delete
            )
            flash("Club deleted successfully!", "success")
            return redirect("/view_club")
        else:
            flash("Club not found.", "danger")
            return redirect("/admin")
    return redirect("/login")

# Add Candidate
@web_app.route("/admin/add_candidate", methods=["GET", "POST"])
def add_candidate():
    if session.get("role") == "admin":
        clubs = db_helper.fetch({}, "clubs")
        club_names = [club["club_name"] for club in clubs]

        if request.method == "POST":
            candidate_name = request.form.get("candidate_name")
            department = request.form.get("department")
            position = request.form.get("position")
            club_name = request.form.get("club_name")
            gender = request.form.get("gender")
            filename = None

            if not candidate_name or not department or not position or not club_name or not gender:
                flash("All fields are required!", "danger")
                return redirect("/admin/add_candidate")

            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    print(f"Uploading file: {filename}")  # Debugging line
                    try:
                        file.save(os.path.join(web_app.config['UPLOAD_FOLDER'], filename))
                        print("File saved successfully!")
                    except Exception as e:
                        print("Error saving file:", e)

            candidate_data = {
                "candidate_name": candidate_name,
                "department": department,
                "position": position,
                "club_name": club_name,
                "gender": gender,
                "image": filename or "default.jpg"
            }

            insert_result = db_helper.insert("candidates", candidate_data)

            if insert_result:
                flash("Candidate added successfully!", "success")
                return redirect("/admin")
            else:
                flash("Failed to add candidate.", "danger")
                return redirect("/admin/add_candidate")

        return render_template("add_candidate.html", clubs=club_names)

    flash("You are not authorized to access this page!", "danger")
    return redirect("/")

    
@web_app.route("/index/vote/<candidate_id>", methods=["GET", "POST"])
def vote(candidate_id):
    if request.method == "POST":
        # Your existing POST logic for handling votes
        if session.get("role") == "user":
            username = session.get("username")
            club_name = session.get("club_name")
            position = session.get("position")
            candidate_name = session.get("candidate_name")

            if not username:
                flash("You need to log in to vote.", "danger")
                return redirect("/login")

            # Check if the user has already voted for this position
            existing_vote = db_helper.find_one(
                collection_name="votes",
                query={"username": username, "position": position}
            )

            if existing_vote:
                flash("You have already voted for this position.", "warning")
                return redirect("/index")

            # Encrypt the username
            encrypted_username = cipher_suite.encrypt(username.encode()).decode()

            # Store the vote in the database
            vote_data = {
                "candidate_id": candidate_id,
                "username": encrypted_username,  # Store encrypted username
                "club_name": club_name,
                "position": position,
                "candidate_name": candidate_name
            }

            db_helper.insert("votes", vote_data)
            flash("Your vote has been recorded successfully!", "success")
            # Emit the new vote event to all clients (admin dashboard)
            socketio.emit('new_vote', {'candidate_id': candidate_id}, broadcast=True)

            
            # Redirect to the same page after vote submission
            return redirect(url_for("vote", candidate_id=candidate_id))
        else:
            flash("Unauthorized access.", "danger")
            return redirect("/login")
    else:
        # Correctly access the collection using the db_helper
        candidates = db_helper.db['candidates'].find()  # Corrected here

        # Group candidates by position
        candidates_by_position = {}
        for candidate in candidates:
            position = candidate.get("position")
            if position not in candidates_by_position:
                candidates_by_position[position] = []
            candidates_by_position[position].append(candidate)

        # Render the voting page with candidates grouped by position
        return render_template("voting.html", candidate_id=candidate_id, candidates_by_position=candidates_by_position)

@web_app.route("/admin/results", methods=["GET"])
def result_page():
    if session.get("role") != "admin":
        flash("Unauthorized access.", "danger")
        return redirect("/login")

    # Aggregation pipeline to calculate votes and join candidate details
    pipeline = [
        {
            "$group": {
                "_id": "$candidate_id",
                "total_votes": {"$sum": 1}  # Count votes for each candidate
            }
        },
        {
            "$lookup": {
                "from": "candidates",  # Name of the candidates collection
                "localField": "_id",  # Candidate ID in the votes collection
                "foreignField": "_id",  # Candidate ID in the candidates collection
                "as": "candidate_details"
            }
        },
        {
            "$unwind": "$candidate_details"  # Flatten the candidate details
        },
        {
            "$project": {
                "_id": 1,
                "total_votes": 1,
                "candidate_name": "$candidate_details.candidate_name",
                "position": "$candidate_details.position",
                "club_name": "$candidate_details.club_name"
            }
        }
    ]

    # Run the aggregation query
    results = list(db_helper.db['votes'].aggregate(pipeline))

    # Pass the results to the admin results template
    return render_template("admin_results.html", results=results)



# Route to view users in the admin panel
@web_app.route("/view_users")
def users():
    # Fetch all users from the database using a helper function
    users = get_users_from_db()

    # Render the view_users.html template and pass the users data
    return render_template("view_users.html", users=users)
# Helper function to fetch users from the database
# Helper function to fetch users from the database
def get_users_from_db():
    # Assuming you're using MongoDB, and db_helper.fetch() is fetching data from MongoDB
    users_collection = db_helper.fetch({}, "users")  # Fetch the users from the 'users' collection
    
    # If db_helper.fetch() already returns a list of users, just return it
    return users_collection








@web_app.route("/admin/delete_candidate/<candidate_name>", methods=['GET', 'POST'])
def delete_candidate(candidate_name):
    if session.get("role") == "admin":
        # Deleting candidate from the database using candidate_name
        success = db_helper.delete(
            collection_name="candidates", query={"candidate_name": candidate_name}
        )
        if success:
            flash("Candidate deleted successfully!", "success")
        else:
            flash("Failed to delete candidate. Candidate not found or error occurred.", "danger")
        return redirect("/admin")
    return redirect("/login")





@web_app.route('/admin/update_candidate/<candidate_name>', methods=['GET', 'POST'])
def update_candidate(candidate_name):

    if session.get("role") == "admin":
        # Handle the GET request: Display the form
        if request.method == "GET":
            # Fetch the candidate details from the database using candidate_name
            candidate = db_helper.find_one(collection_name="candidates", query={"candidate_name": candidate_name})
            return render_template("update_candidate.html", candidate=candidate)
        
        # Handle the POST request: Process the form submission
        if request.method == "POST":
            # Get the updated candidate data from the form and update the database
            new_name = request.form.get("candidate_name")
            db_helper.update(
                collection_name="candidates", 
                query={"candidate_name": candidate_name}, 
                updated_data={"$set": {"candidate_name": new_name}}
            )
            flash("Candidate updated successfully!", "success")
            return redirect("/admin")
    return redirect("/login")


def get_user_club(username):
    # You can fetch the user's club from the session
    if 'clubs' in session:
        return session['clubs']
    
    # Alternatively, you can fetch the user's club from the database
    db_helper.collection = db_helper.db["users"]
    user = db_helper.find_one({"username": username})
    return user.get("clubs", [])  # Return an empty list if no clubs found
def get_user_position(username):
    # You can fetch the user's position from the session if stored there
    if 'position' in session:
        return session['position']
    
    # Or fetch the user's position from the database
    db_helper.collection = db_helper.db["users"]
    user = db_helper.find_one({"username": username})
    return user.get("position", "default")  # Return a default position if not found
def set_voting_status(status):
    # status should be 'on' or 'off' to enable or disable voting
    db_helper.collection = db_helper.db["voting_status"]
    existing_status = db_helper.find_one({"status_key": "voting"})
    
    if existing_status:
        # Update the existing voting status
        db_helper.update_one({"status_key": "voting"}, {"$set": {"status": status}})
    else:
        # Insert the voting status if it does not exist
        db_helper.insert({"status_key": "voting", "status": status})


# Helper Functions

# Get candidates from the database (Dummy implementation)
def get_candidates_from_db():
    try:
        # Using the fetch method to get candidates
        candidates = db_helper.fetch({}, "candidates")
        return candidates
    except Exception as e:
        print(f"Error fetching candidates: {e}")
        return []
# Logout
@web_app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# Main Function
def main():
    web_app.run(debug=True)


if __name__ == "__main__":
    main()
