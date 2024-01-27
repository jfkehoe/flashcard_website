from flask import Flask, redirect, url_for, render_template, request, session, flash
import os
from . import math_problem_1
from . import math_problem_2
import time
import random
import csv
import getpass
import re

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

#prepending everything with FCW (Flash Card Website) so I can find it in the Apache logs
def log(txt, pre="FCW::"):
    print(pre + " " + time.ctime() + " " + txt + "\n")

def calc_answer(in_prob, in_ans=None):
    in_prob = re.sub("=\s*$", "", in_prob)
    if in_ans:
        in_ans = re.sub("=\s*$", "", in_ans)
    
    try:
        r0 = eval(in_prob)
    except:
        r0 = None
    
    if (in_ans):
        try:
            r1 = eval(in_ans)
        except:
            r1 = None
    
    if (in_ans): 
        return (r0, r1)
    else:
        return r0
    

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
        flashcard_setup()
        #now go to the real "game loop"
        return redirect(url_for("flashcard"))
    else:
        return render_template("error.html")

def flashcard_setup():
    log("Running flashcard_setup")
    #essentially globals
    session["csv_flashcard"] = dict()
    session["csv_flashcard"]["questions"] = dict()
    session["csv_flashcard"]["current_question"] = None
    session["correct cnt"] = 0
    session["wrong cnt"] = 0
    

    #two more globals set at the bottom 

    #csv
    #Question, Right Answer, Wrong Answer, Wrong Answer...
    #If question or right answer ends with .png it is based on an image and changes the mode
    #If there is no wrong answers or no right answer it is a free form instead of multiple choice
    #All expressions in free form with be checked with eval statements
    with open(csv_path + "/" + session["choice"], newline='', encoding="utf-8") as f:
        reader = csv.reader(f)
        for init_line in list(reader)[1:]:
            #all question types have similar fields 
            question = init_line[0]
            session["csv_flashcard"]["questions"][question] = dict()
            session["csv_flashcard"]["questions"][question]["remaining"] = 1
            #remaining will be set to 0 if the question is not valid
            
            #clean up the blank spaces in the line, this helps classify the questions
            cleaned_line = [i for i in init_line if i != ""] 
            if len(cleaned_line) == 1:
                session["csv_flashcard"]["questions"][question]["type"] = "free_form"
                ans = calc_answer(question)
                session["csv_flashcard"]["questions"][question]["right answer"] = ans
                if not ans:
                    log(f"Issue with question, ignoring:: {question}  :: {ans}")
                    session["csv_flashcard"]["questions"][question]["remaining"] = 0 

            elif len(cleaned_line) == 2:
                session["csv_flashcard"]["questions"][question]["type"] = "free_form"
                ans = calc_answer(cleaned_line[1])
                session["csv_flashcard"]["questions"][question]["right answer"] = ans
                if not ans:
                    log(f"Issue with question, ignoring:: {question} :: {cleaned_line[1]}  :: {ans}")
                    session["csv_flashcard"]["questions"][question]["remaining"] = 0 

            elif cleaned_line[1].endswith(".png") and cleaned_line[2].endswith(".png"):
                session["csv_flashcard"]["questions"][question]["type"] = "flashcard_4x_choice_pics"
            elif cleaned_line[1].endswith(".png") and cleaned_line[2].endswith(".png"):
                session["csv_flashcard"]["questions"][question]["type"] = "flashcard_4x_choice_pic"
            elif cleaned_line[1].endswith(".png") and cleaned_line[2].endswith(".png"):
                session["csv_flashcard"]["questions"][question]["type"] = "flashcard_4x_choice_pics_text_prompt"
            else:
                session["csv_flashcard"]["questions"][question]["type"] = "flashcard_text_only"

            if session["csv_flashcard"]["questions"][question]["type"] != "free_form":
                session["csv_flashcard"]["questions"][question]["remaining"] = 1
                session["csv_flashcard"]["questions"][question]["right answer"] = cleaned_line[1]
                session["csv_flashcard"]["questions"][question]["wrong answers"] = cleaned_line[2:]

    #globals
    #score starts high and goes down. 
    session["score"] = len(session["csv_flashcard"]["questions"])
    session["csv_flashcard"]["current_question"] = None
    #doing away with the start flag, if no current question is selected and we are in the loop, assume we don't need to eval
    #session["csv_flashcard"]["start_flag"] = True
            
@app.route("/flashcard", methods=["POST", "GET"])
def flashcard():
    #initial setup, parse csv
    #-- called before we got here

    #There are a few variables that are live for a given game loop
    #session["csv_flashcard"]["current_question"]
    #session["csv_flashcard"]["disabled_list"]
    #session["csv_flashcard"]["current_possible_answer_list"]
    #session["csv_flashcard"]["current_right_answer"]
    #session["csv_flashcard"]["current_type"]

    #current_question let's us reference the session["csv_flashcard"]["questions"] which stores all the data for all of the questions
    #session["csv_flashcard"]["disabled_list"] is a list of incorrect answers alread chosen, so we can disable the user from guessing them again
    #session["csv_flashcard"]["current_possible_answer_list"] is the list of possible choices we give to the user, this is randomized each time a new question is chosen
    #session["csv_flashcard"]["current_right_answer"] obvious, I hope

    #evaluate last answer
    cq = session["csv_flashcard"]["current_question"]
    log(f"Current Question {cq}")
    #if no current question is selected and we are in the loop, assume we don't need to eval
    if cq and session["csv_flashcard"]["current_type"] == "free_form":
        last_ans = request.form["ans"]
        log(f"Free form ans {last_ans}")
        try:
            c_ans = float(last_ans)
        except:
            log(f"User gave none NaN to question {last_ans}")
            c_ans = None
        
        if c_ans == session["csv_flashcard"]["current_right_answer"]:
            session["csv_flashcard"]["questions"][cq]["remaining"] -= 1
            session["correct cnt"] += 1
            session["csv_flashcard"]["current_question"] = None
        else:
            session["csv_flashcard"]["questions"][cq]["remaining"] += 1
            session["wrong cnt"] += 1
            #probably need a better feedback mechanism so the user knows when they got it wrong

    elif cq:
        #currently this must be a multiple choice, they are all handled the same way
        last_ans = request.form["ans"]
        #return answer is expected to be an int corresponding to the possible answer array
        #This is done rather than a text comparison because the tex strings are getting changed when
        #returned from the webpage
        #this should not break if the webpage is returning the right value
        #I should have an assert that won't break the website. 
        c_ans = session["csv_flashcard"]["current_possible_answer_list"][int(last_ans)]
        log(f"Current Question: {cq} Current Answer: {c_ans}")
        if c_ans == session["csv_flashcard"]["current_right_answer"]:
            session["csv_flashcard"]["questions"][cq]["remaining"] -= 1
            session["correct cnt"] += 1
            session["csv_flashcard"]["current_question"] = None
        else:
            session["csv_flashcard"]["questions"][cq]["remaining"] += 1
            session["wrong cnt"] += 1
            session["csv_flashcard"]["disabled_list"][int(last_ans)] = "disabled"

    #evaluate if all answers have been completed, if so go to summary
    remaining_question_cnt = sum([session["csv_flashcard"]["questions"][i]["remaining"] for i in session["csv_flashcard"]["questions"]])

    if remaining_question_cnt == 0:
        #we are done, go to summary
        return redirect(url_for("summary"))

    #choose next question
    if not session["csv_flashcard"]["current_question"]:
        #Pick a question
        #I want questions that have more than copy to appear multiple times in the list
        remaining_questions = []
        for q in session["csv_flashcard"]["questions"]:
            for i in range(session["csv_flashcard"]["questions"][q]["remaining"]):
                remaining_questions.append(q)

        cq = random.choice(remaining_questions)
        right_answer =  session["csv_flashcard"]["questions"][cq]["right answer"]
        type_ = session["csv_flashcard"]["questions"][cq]["type"]
        
        #For the multiple choice, select some wrong answers
        if type_ == "free_form":
            this_one = None
            possible_answers = []
        else:
            wrong_answers = session["csv_flashcard"]["questions"][cq]["wrong answers"][:]
            random.shuffle(wrong_answers)
            possible_answers = [right_answer] + wrong_answers[0:3]
            random.shuffle(possible_answers)
            this_one = possible_answers.index(right_answer)    
        
        log(f"Setting current question {cq}")
        session["csv_flashcard"]["current_question"] = cq    
        session["csv_flashcard"]["current_right_answer"] = right_answer
        session["csv_flashcard"]["disabled_list"] = [""] * 4
        session["csv_flashcard"]["current_type"]= type_ 
        session["csv_flashcard"]["current_possible_answer_list"] = possible_answers
        session["csv_flashcard"]["this_one"] = this_one

    #1. text only (includes tex math) -- default
    #2. picture as a prompt, text answers
    #3. Picture prompt and answers
    #4. Text prompt, free form answer
    type_ =  session["csv_flashcard"]["current_type"]
    cq = session["csv_flashcard"]["current_question"]
    
    #DO NOT REMOVE
    #I can't explain why, but session["csv_flashcard"]["current_question"] will be None unless this line is here
    session["junk"] = True

    if type_ == "free_form":
        return render_template("free_form.html", this_one=session["csv_flashcard"]["this_one"], my_title="Question", remaining_cnt=remaining_question_cnt, my_question=session["csv_flashcard"]["current_question"])
    elif type_ == "flashcard_text_only":
         return render_template("basic_4x_choice.html", this_one=session["csv_flashcard"]["this_one"], my_title="Question", remaining_cnt=remaining_question_cnt, my_question=session["csv_flashcard"]["current_question"], possible_answers=session["csv_flashcard"]["current_possible_answer_list"], disable_list=session["csv_flashcard"]["disabled_list"])
    elif type_ == "flashcard_4x_choice_pics":
         return render_template("4x_choice_pics.html", this_one=session["csv_flashcard"]["this_one"], img_path="static/pics/", my_title="Question", remaining_cnt=remaining_question_cnt, img=f"static/pics/{cq}", possible_answers=session["csv_flashcard"]["current_possible_answer_list"], disable_list=session["csv_flashcard"]["disabled_list"] )
    elif  type_== "flashcard_4x_choice_pic":
         return render_template("4x_choice_pic.html", this_one=session["csv_flashcard"]["this_one"], my_title="Question", remaining_cnt=remaining_question_cnt, img=f"static/pics/{cq}", possible_answers=session["csv_flashcard"]["current_possible_answer_list"], disable_list=session["csv_flashcard"]["disabled_list"] )
    elif type_ == "flashcard_4x_choice_pics_text_prompt":
        return render_template("4x_choice_pics_text_prompt.html", this_one=session["csv_flashcard"]["this_one"], img_path="static/pics/", my_title="Question", remaining_cnt=remaining_question_cnt, my_question=cq, possible_answers=session["csv_flashcard"]["current_possible_answer_list"], disable_list=session["csv_flashcard"]["disabled_list"] )
    else:
        log(f"Invalid question type {_type}")
        return render_template("error.html")


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
    log(f"Completed {test_type} with a score of {score}")
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
