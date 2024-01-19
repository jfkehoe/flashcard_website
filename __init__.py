from flask import Flask, redirect, url_for, render_template, request, session, flash
import os
from . import math_problem_1
from . import math_problem_2
import time
import random
import csv
import getpass

app = Flask(__name__)
#app.secret_key = "temp_secret_key"
csv_path = os.path.dirname(__file__) + "/csvs"
csv_path.replace('\\', '/')

app.config["UPLOAD_FOLDER"] = "staic/pics"

#logfile = open("math_tests.log", "a")

def log(txt, pre=""):
    global logfile
    if pre:
        logfile.write(pre + " " + time.ctime() + " " + txt + "\n")
    logfile.flush()
    print(f"Wrote to log file: {txt}")

def log(txt, pre=""):
    print(pre + " " + time.ctime() + " " + txt + "\n")

@app.route("/", methods=["POST", "GET"])
def home():
    session["csvs"] = [i for i in sorted(os.listdir(csv_path)) if i.endswith("csv")]
    tst_csvs = session["csvs"]
    log(f"Start session {tst_csvs}", "\n")
    session["user"] = ""
    print(tst_csvs)
    return render_template("user_choice.html", my_title="Intro", cnt = len(tst_csvs), tst_csvs=tst_csvs)

@app.route("/settings", methods=["POST"])
def settings():
    global current_question
    session["choice"] = request.form["choice"]
    session["cnt"] = 0
    session["learn_mode"] = 1
    choice = session["choice"]
    log(f"Test Choice: {choice}", pre="START")
    if session["choice"] == "OG Math Word Problems":
        session["number_of_questions_to_ask"] = 20
        session["max_val"] = 1000
        session["score"] = 0
        current_question = None
        session["current_question"] = None
        return render_template("settings.html", my_title="OG Math Word Problems", cnt=session["number_of_questions_to_ask"])
    elif session["choice"] in session["csvs"]:
        #prep the csv here
        session["basic_4x"] = dict()
        session["basic_4x"]["questions"] = dict()
        session["basic_4x"]["current_question"] = None
        session["correct cnt"] = 0
        session["wrong cnt"] = 0
        with open(csv_path + "/" + session["choice"], newline='', encoding="utf-8") as f:
            reader = csv.reader(f)
            for r in list(reader)[1:]:
                #idx 0 expected to be count
                #r is [Question, Right Answer, Wrong Answers...]
                session["basic_4x"]["questions"][r[0]] = dict()
                session["basic_4x"]["questions"][r[0]]["remaining"] = 1
                session["basic_4x"]["questions"][r[0]]["right answer"] = r[1]
                session["basic_4x"]["questions"][r[0]]["wrong answers"] = [i for i in r[2:] if i != ""]
                q = r[0]
                remain = session["basic_4x"]["questions"][q]["remaining"]
                ans = session["basic_4x"]["questions"][q]["right answer"]
                wrong = session["basic_4x"]["questions"][q]["wrong answers"]
                print(f"question {q} right: {ans} wrong: {wrong}")
                
        session["score"] = len(session["basic_4x"]["questions"])
        session["basic_4x"]["start_flag"] = True
        return redirect(url_for("basic_4x"))
    else:
        return render_template("error.html")

def settings_old():
    global current_question
    session["user"] = request.form["user"]
    session["cnt"] = 0
    session["learn_mode"] = 1
    if session["user"] == "Child0":
        session["number_of_questions_to_ask"] = 10
        session["max_val"] = 1000
    elif session["user"] == "Child1":
        session["number_of_questions_to_ask"] = 10
        session["max_val"] = 10
    else:
        session["number_of_questions_to_ask"] = 10
        session["max_val"] = 1000

    session["score"] = 0
    usr = session["user"]
    log(f"User is {usr}")
    current_question = None
    return render_template("settings.html", my_title=session["user"], cnt=session["number_of_questions_to_ask"])


@app.route("/basic_4x", methods=["POST", "GET"])
def basic_4x():
    print("Called basic_4x")
    new_question = True
    if session["basic_4x"]["start_flag"]:
        #no need to check the previous result, as there was none
        session["basic_4x"]["start_flag"] = False
    else:
        if session["basic_4x"]["current_possible_answer_list"][0].endswith(".png"):
            last_ans = request.form.get("ans")
            #can't get the value, need to get the src name somehow.  
        else:
            last_ans = request.form["ans"]

        #complete hack
        #somehow my tex strings are getting murdered coming back from the js function
        #so I will pull the correct string from the session answer list
        silly_list = ["__one", "__two", "__three", "__four"]
        if last_ans in silly_list:
            idx = silly_list.index(last_ans)
            last_ans = session["basic_4x"]["current_possible_answer_list"][idx]

        print(f"Last Answer: {last_ans}")

        c_question = session["basic_4x"]["current_question"]
        right_ans = session["basic_4x"]["questions"][c_question]["right answer"]
        if right_ans == last_ans:
            log(f"{c_question} :: {last_ans}", pre="CORRECT")
            session["basic_4x"]["questions"][c_question]["remaining"] -= 1
            session["correct cnt"] += 1
        else:
            new_question = False
            log(f"{c_question} :: !{last_ans} :: {right_ans}", pre="INCORRECT")
            session["wrong cnt"] += 1
            if session["basic_4x"]["questions"][c_question]["remaining"] < 6:
                session["basic_4x"]["questions"][c_question]["remaining"] += 1
            #disable wrong answers TBD
            idx = session["basic_4x"]["current_possible_answer_list"].index(last_ans)
            session["disabled_list"][idx] = "disabled"
            

        #need user feedback if incorrect       
        #TBD

    remaining_question_cnt = sum([session["basic_4x"]["questions"][i]["remaining"] for i in session["basic_4x"]["questions"]])

    if remaining_question_cnt == 0:
        #we are done, go to summary
        return redirect(url_for("summary"))
    
    if new_question:
        #I want questions that have more than copy to appear multiple times in the list
        remaining_questions = []
        for q in session["basic_4x"]["questions"]:
            for i in range(session["basic_4x"]["questions"][q]["remaining"]):
                remaining_questions.append(q)

        session["basic_4x"]["current_question"] = random.choice(remaining_questions)    
    
        session["disabled_list"] = [""] * 4

        cq = session["basic_4x"]["current_question"]
        right_ans = session["basic_4x"]["questions"][cq]["right answer"]
        wrong_answers = session["basic_4x"]["questions"][cq]["wrong answers"][:]
        random.shuffle(wrong_answers)
        possible_answers = [right_ans] + wrong_answers[0:3]
        random.shuffle(possible_answers)    
        session["basic_4x"]["current_possible_answer_list"] = possible_answers

    #might want to enhance this later... 
    #disable answering already wrongly answered questions. 
    
    cq = session["basic_4x"]["current_question"]

    possible_answers = session["basic_4x"]["current_possible_answer_list"]
    print(f"possible answers: {possible_answers}")
    if cq.endswith(".png") and not possible_answers[0].endswith(".png"):
        print("Using image template")
        return render_template("4x_choice_pic.html", my_title="Question", remaining_cnt=remaining_question_cnt, img=f"static/pics/{cq}", possible_answers=session["basic_4x"]["current_possible_answer_list"], disable_list=session["disabled_list"] )
    elif cq.endswith(".png"):
        return render_template("4x_choice_pics.html", img_path="static/pics/", my_title="Question", remaining_cnt=remaining_question_cnt, img=f"static/pics/{cq}", possible_answers=session["basic_4x"]["current_possible_answer_list"], disable_list=session["disabled_list"] )
    elif possible_answers[0].endswith(".png"):
        return render_template("4x_choice_pics_text_prompt.html", img_path="static/pics/", my_title="Question", remaining_cnt=remaining_question_cnt, my_question=cq, possible_answers=session["basic_4x"]["current_possible_answer_list"], disable_list=session["disabled_list"] )

    else:
        return render_template("basic_4x_choice.html", my_title="Question", remaining_cnt=remaining_question_cnt, my_question=session["basic_4x"]["current_question"], possible_answers=session["basic_4x"]["current_possible_answer_list"], disable_list=session["disabled_list"])

@app.route("/display_check")
def list_csv():
    session["csvs"] = [i for i in sorted(os.listdir(csv_path)) if i.endswith("csv")]
    return render_template("display_choice.html", cnt=len(session["csvs"]), tst_csvs=session["csvs"])



@app.route("/review_csv_display", methods=["POST"])
def display_check():
    lines = []
    last_ans = request.form["choice"]
    line_idx = 2

    with open(csv_path + "/" + last_ans, newline='', encoding="utf-8") as f:
        reader = csv.reader(f)
        for r in list(reader)[1:]:
            col_idx = 65
            #idx 0 expected to be count
            #r is [Question, Right Answer, Wrong Answers...]
            for cell in r:
                if cell != "":                    
                    display_str = str(line_idx) + chr(col_idx) + "  " + cell
                    lines.append(display_str)
                    col_idx += 1
            line_idx +=1 
            
    return render_template("display_check.html", my_title=last_ans, cnt=len(lines), my_lines=lines)

@app.route("/question", methods=["POST"])
def question():
    new_question = False
    if session["cnt"] == 0:
        session["correct cnt"] = 0
        session["wrong cnt"] = 0
        new_question = True
    elif session["right_answer"] == request.form["ans"]:
        log("Correct Answer")
        session["correct cnt"] += 1
        session["score"] += 1
        new_question = True
    elif not session["right_answer"] == request.form["ans"]:
        #need to set disabled list correctly
        wrong_ans = request.form["ans"]
        log(f"Wrong answer: {wrong_ans}")

        #sliding scale of wrong plenty to the score
        divisor = 4 - session["disabled_list"].count("disabled")
        session["score"] -= 1/divisor

        idx = session["possible_answers"].index(wrong_ans)
        session["disabled_list"].pop(idx)
        session["disabled_list"].insert(idx, "disabled")
        session["wrong cnt"] += 1
    else:
        #undetermined mode.
        #figure out flash.
        return redirect(url_for("logout"))

    if session["cnt"] == session["number_of_questions_to_ask"]:
        return redirect(url_for("summary"))
    elif new_question:

        session["disabled_list"] = [""] * 4
        if session["user"] == "Odin":
            current_question = math_problem_1.simple_problem(session["max_val"])
        else:
            current_question = math_problem_1.problem(session["max_val"])
        log(f"Current question: {current_question.text}")

        session["possible_answers"] = current_question.get_possible_answers(4)
        session["right_answer"] = current_question.right_answer()
        session["current_question"] = current_question.text
        print(session["possible_answers"])
        log("Possible answers: %s"%(str(session["possible_answers"])))
        session["cnt"] += 1

    return render_template("4x_multiple_choice.html", my_title="Question", my_question=session["current_question"], possible_ans=session["possible_answers"], disable_list=session["disabled_list"])

@app.route("/summary")
def summary():
    if session["score"] < 0:
        session["score"] = 0

    session["score"] = int(100*session["correct cnt"]/(session["correct cnt"] + session["wrong cnt"]))
    test_type = session["choice"]
    score = session["score"]
    log(f"Completed {test_type} with a score of {score}", pre="COMPLETE")
    return render_template("summary.html", my_title="Summary", score=session["score"], correct=session["correct cnt"], wrong=session["wrong cnt"])


@app.route("/logout")
def logout():
    session.pop("peep", None)


@app.route("/test", methods=["POST", "GET"])
def test():
    my_question = "What is 2 and 3??"
    my_list = []
    my_list.append("3+2=")
    my_list.append("3x2=")
    my_list.append("3-2=")
    my_list.append("3%2=")
    if (request.method=="GET"):
        return render_template("base_template.html", my_question=my_question, possible_ans=my_list)
    elif (request.method=="POST"):
        return redirect(url_for("home"))


@app.route("/admin")
def admin():
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run()
    #app.run(debug=True)
