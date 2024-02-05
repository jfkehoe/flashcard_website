from flask import Flask, redirect, url_for, render_template, request, session, flash
import os
from .flashcardquestion import *
from . import math_problem_1
from . import math_problem_2
import time
import random
import csv
import getpass
import re
import gspread
from datetime import datetime

app = Flask(__name__)
#app.secret_key = "temp_secret_key"
csv_path = os.path.dirname(__file__) + "/csvs"
csv_path.replace('\\', '/')

app.config["UPLOAD_FOLDER"] = "staic/pics"



#I was putting all of this data into session, but it overwhelmed the 4k storage space of the cookie
global_flashcard_dict = dict()
#idx is the line number (shifted by 2), the order in which the lines were read in
#global_flashcard_dict["name_of_csv_file"][idx] = flashcardquestion()
#NOTE: this will be repurposed to use google sheets

#prepending everything with FCW (Flash Card Website) so I can find it in the Apache logs
def log(txt, pre="FCW::"):
    print(pre + " " + time.ctime() + " " + txt)

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



@app.route("/summary")
def summary():
    if session["score"] < 0:
        session["score"] = 0

    session["score"] = int(100*session["correct cnt"]/(session["correct cnt"] + session["wrong cnt"]))
    test_type = session["choice"]
    score = session["score"]
    log(f"Completed {test_type} with a score of {score}")
    
    #update google sheet with the score
    now = datetime.now()
    c_date = now.strftime("%Y-%m-%d %H:%M")
    
    try:
        wb = app.config["WORKBOOK"]
        log("1")
        report_sheet = wb.worksheet("Report")
        log("2")
        date_column = report_sheet.col_values(1)
        log("3")
        row_number = len(date_column) + 1
        log("4")

        report_row = [c_date, session["choice"], session["score"]]
        log("5")
        report_sheet.update([report_row], f"A{row_number}:C{row_number}")
        #done google sheet
    except:
        log("Unable to write report to Google Sheets")

    return render_template("summary.html", my_title="Summary", score=session["score"], correct=session["correct cnt"], wrong=session["wrong cnt"])

@app.route("/", methods=["POST", "GET"])
def main():
    session.clear()
    try:
        wb = app.config["WORKBOOK"]
        sheet = wb.worksheet("Contents")
        choices = sheet.col_values(1)[1:]
    except:
        return render_template("error.html", details="Something went wrong with Google Sheets while reading Contents sheet")
    
    session["state"] = "main"
    return render_template("choice.html", my_title="Main Menu", choices=choices, choices_cnt=len(choices))

@app.route("/process_choice", methods=["POST", "GET"])
def process_choice():
    choice = request.form["choice"]

    if session["state"] == "main"  and choice == "Pre-Algebra and Algebra I":
        try:
            wb = app.config["WORKBOOK"]
            sheet = wb.worksheet("Contents")
            choices = sheet.col_values(2)[1:]
        except:
            log("Unable to open Google Sheets for reading algebra list")
            return render_template("error.html", details="Something went wrong with Google Sheets while reading Contents sheet")

        session["state"] = "algebra"
        return render_template("choice.html", my_title="Main Menu", choices=choices, choices_cnt=len(choices))
    elif session["state"] == "main" and (choice == "Math Quiz" or choice == "OG Math Word Problems"):
        return render_template("info.html", details=f"User selected {choice} from main menu.. this one is handled special")
    elif session["state"] == "main":
        session["choice"] = choice
        flashcard_setup()
        return redirect(url_for("flashcard"))        
        #return render_template("info.html", details=f"User selected {choice} from main menu")
    elif session["state"] == "algebra":
        session["choice"] = choice
        flashcard_setup()
        return redirect(url_for("flashcard"))            
    return render_template("error.html", details=f"Process Choice fell through")    


    
#replace with main soon
@app.route("/old", methods=["POST", "GET"])
def home():
    session.clear()
    session["csvs"] = [i for i in sorted(os.listdir(csv_path)) if i.endswith("csv")]
    tst_csvs = session["csvs"]
    log(f"Start session {tst_csvs}", "\n")
    return render_template("user_choice.html", my_title="Intro", cnt = len(tst_csvs), tst_csvs=tst_csvs)

#get rid of this soon
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

def read_quiz_sheet(sheet_name):
    log(f"Entered def read_quiz_sheet({sheet_name})")
    global global_flashcard_dict
    if sheet_name in global_flashcard_dict and len(global_flashcard_dict[sheet_name]) > 0:
        return
    

    try:
        wb = app.config["WORKBOOK"]
        sheet = wb.worksheet(sheet_name)
        all_vals = sheet.get_all_values()
    except:
        return render_template("error.html", details="Something went wrong with Google Sheets while reading Contents sheet")
    
    for row in all_vals[1:]:
        global_flashcard_dict[sheet_name] = []
        question_obj = question_from_csv_line(row)
        global_flashcard_dict[sheet_name].append(question_obj)
    
def read_csv(sheet_name):
    global global_flashcard_dict
    if sheet_name in global_flashcard_dict:
        log(f"Rereading {sheet_name}")
        
    global_flashcard_dict[sheet_name] = []
    with open(csv_path + "/" + sheet_name, newline='', encoding="utf-8") as f:
        reader = csv.reader(f)
        #first line has column headers, which I will assume match what I want
        for init_line in list(reader)[1:]:
            #remove any blank entries in csv line
            #> question, right ans, wrong, wrong, wrong,,,,,,            
            
            question_obj = question_from_csv_line(init_line)
            global_flashcard_dict[sheet_name].append(question_obj)

def flashcard_setup():
    log("Enter def flashcard_setup")
    global global_flashcard_dict
    
    #essentially globals
    choice = session["choice"]

    session["flashcard"] = dict()
    session["flashcard"]["sheet_name"] = session["choice"]
    global_flashcard_dict[session["choice"]] = [] 
    if choice.endswith(".csv"):
        session["flashcard"]["choice_type"] = "csv_name"
    else:
        session["flashcard"]["choice_type"] = "sheet_name"

    session["flashcard"]["current_question_idx"] = None
    session["flashcard"]["current_question"] = None
    session["correct cnt"] = 0
    session["wrong cnt"] = 0
    
    if session["flashcard"]["choice_type"] == "csv_name":
        read_csv(session["flashcard"]["sheet_name"])
    else:
        read_quiz_sheet(session["flashcard"]["sheet_name"])

    number_of_questions = len(global_flashcard_dict[session["choice"]])
    session["flashcard"]["idxes"] = list(range(0, number_of_questions))
    session["score"] = number_of_questions
    
            
@app.route("/flashcard", methods=["POST", "GET"])
def flashcard():
    log("Enter def flashcard")
    global global_flashcard_dict
    sheet_name = session["flashcard"]["sheet_name"]

    #if the tid (thread ID) changes in apache, the global variable can be wiped out. So I might need to re-read
    if sheet_name not in global_flashcard_dict:
        if session["flashcard"]["choice_type"] == "csv_name":
            read_csv(sheet_name)
        else:
            read_quiz_sheet(sheet_name)

    #initial setup, parse csv
    #-- called before we got here

    #evaluate last answer
    cq_idx = session["flashcard"]["current_question_idx"]

    cq = session["flashcard"]["current_question"]
    log(f"Current Question {cq}")
    #if no current question is selected and we are in the loop, assume we don't need to eval
    if cq_idx != None and session["flashcard"]["current_type"] == "free_form":
        cq_obj = global_flashcard_dict[sheet_name][cq_idx]
        last_ans = request.form["ans"]
        log(f"Free form ans {last_ans}")
        try:
            c_ans = calc_answer(last_ans)
        except:
            log(f"User gave none NaN to question {last_ans}")
            c_ans = None
        
        if cq_obj.check_answer(c_ans):
            session["flashcard"]["idxes"].remove(cq_idx)
            session["correct cnt"] += 1
            session["flashcard"]["current_question_idx"] = None
        else:
            session["flashcard"]["idxes"].append(cq_idx)
            session["wrong cnt"] += 1
            #probably need a better feedback mechanism so the user knows when they got it wrong

    elif cq_idx != None:
        cq_obj = global_flashcard_dict[sheet_name][cq_idx]
        #currently this must be a multiple choice, they are all handled the same way
        last_ans = request.form["ans"]
        #return answer is expected to be an int corresponding to the possible answer array
        #This is done rather than a text comparison because the tex strings are getting changed when
        #returned from the webpage
        #this should not break if the webpage is returning the right value
        #I should have an assert that won't break the website. 
        c_ans = session["flashcard"]["current_possible_answer_list"][int(last_ans)]
        log(f"Current Question: {cq_obj.question} Current Answer: {c_ans}")
        if c_ans == session["flashcard"]["current_right_answer"]:
            indices = session["flashcard"]["idxes"]
            log(f"Removing {cq_idx} index from {indices}")
            session["flashcard"]["idxes"].remove(cq_idx)
            indices = session["flashcard"]["idxes"]
            
            session["correct cnt"] += 1
            session["flashcard"]["current_question_idx"] = None        
        else:
            session["flashcard"]["idxes"].append(cq_idx)
            session["wrong cnt"] += 1
            session["flashcard"]["disabled_list"][int(last_ans)] = "disabled"

    #evaluate if all answers have been completed, if so go to summary
    indices = session["flashcard"]["idxes"]
    log(f"Remaining indices: {indices}")
    remaining_question_cnt = len(indices)

    if remaining_question_cnt == 0:
        #we are done, go to summary
        return redirect(url_for("summary"))

    #choose next question
    if not session["flashcard"]["current_question_idx"]:
        cq_idx = random.choice(session["flashcard"]["idxes"])
        cq_obj = global_flashcard_dict[sheet_name][cq_idx]

        right_answer = cq_obj.right_answer
        type_ = cq_obj.type
        
        if type_ == "free_form":
            this_one = None
            possible_answers = []
        else:
            #possible answers is randomized 3 wrong answers and one right answer
            possible_answers = cq_obj.give_four_choices()
            this_one = possible_answers.index(right_answer)    
        
        log(f"Setting current question {cq_obj.question}")
        session["flashcard"]["current_question_idx"] = cq_idx
        session["flashcard"]["current_question"] = cq_obj.question    
        session["flashcard"]["current_right_answer"] = right_answer
        session["flashcard"]["disabled_list"] = [""] * 4
        session["flashcard"]["current_type"]= type_ 
        session["flashcard"]["current_possible_answer_list"] = possible_answers
        session["flashcard"]["this_one"] = this_one

    #1. text only (includes tex math) -- default
    #2. picture as a prompt, text answers
    #3. Picture prompt and answers
    #4. Text prompt, free form answer
    type_ =  session["flashcard"]["current_type"]
    cq = session["flashcard"]["current_question"]
    
    #DO NOT REMOVE
    #I can't explain why, but session["flashcard"]["current_question"] will be None unless this line is here
    session["junk"] = True

    if type_ == "free_form":
        log("return html render free_form.html")
        return render_template("free_form.html", this_one=session["flashcard"]["this_one"], my_title="Question", remaining_cnt=remaining_question_cnt, my_question=session["flashcard"]["current_question"])
    elif type_ == "flashcard_text_only":
        log("return html render basic_4x_choice.html")
        return render_template("basic_4x_choice.html", this_one=session["flashcard"]["this_one"], my_title="Question", remaining_cnt=remaining_question_cnt, my_question=session["flashcard"]["current_question"], possible_answers=session["flashcard"]["current_possible_answer_list"], disable_list=session["flashcard"]["disabled_list"])
    elif type_ == "flashcard_4x_choice_pics":
        log("return html render 4x_choice_pics.html")
        return render_template("4x_choice_pics.html", this_one=session["flashcard"]["this_one"], img_path="static/pics/", my_title="Question", remaining_cnt=remaining_question_cnt, img=f"static/pics/{cq}", possible_answers=session["flashcard"]["current_possible_answer_list"], disable_list=session["flashcard"]["disabled_list"] )
    elif  type_== "flashcard_4x_choice_pic":
        log("return html render 4x_choice_pic.html")
        return render_template("4x_choice_pic.html", this_one=session["flashcard"]["this_one"], my_title="Question", remaining_cnt=remaining_question_cnt, img=f"static/pics/{cq}", possible_answers=session["flashcard"]["current_possible_answer_list"], disable_list=session["flashcard"]["disabled_list"] )
    elif type_ == "flashcard_4x_choice_pics_text_prompt":
        log("return html render 4x_choice_pics_text_prompt.html")
        return render_template("4x_choice_pics_text_prompt.html", this_one=session["flashcard"]["this_one"], img_path="static/pics/", my_title="Question", remaining_cnt=remaining_question_cnt, my_question=cq, possible_answers=session["flashcard"]["current_possible_answer_list"], disable_list=session["flashcard"]["disabled_list"] )
    else:
        log(f"Invalid question type {type_}")
        return render_template("error.html")

#need a sheets version of this
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
      
        log("Possible answers: %s"%(str(session["possible_answers"])))
        session["cnt"] += 1

    return render_template("4x_multiple_choice.html", my_title="Question", my_question=session["current_question"], possible_ans=session["possible_answers"], disable_list=session["disabled_list"])

@app.route("/admin")
def admin():
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run()
    #app.run(debug=True)
