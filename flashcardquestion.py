import re
import random

def question_from_csv_line(in_line):
    cleaned_line = [i for i in in_line if i != ""] 
    my_question = FlashCardQuestion(cleaned_line[0])
    if len(cleaned_line) == 1:
        my_question.calc_answer()
    elif len(cleaned_line) == 2:
       my_question.set_eval_answer(cleaned_line[1])
    else:
       my_question.right_answer = cleaned_line[1]
       my_question.wrong_answers = cleaned_line[2:]

    if my_question.right_answer in my_question.wrong_answers:
        my_question.wrong_answers.remove(my_question.right_answer)
        
    my_question.update_type()
    return my_question


class FlashCardQuestion():
    def __init__(self, question_text):
        self.question = question_text
        self.right_answer = None
        self.wrong_answers = []
        self.type = None
        self.valid = True

    def check_answer(self, ans):
        if self.right_answer == ans:
            return True
        return False
    
    def give_four_choices(self):
        if self.type == "free_form":
            return []
        
        other = self.wrong_answers[:]
        random.shuffle(other)
    
        rtn = [self.right_answer] + other[0:3]
        random.shuffle(rtn)
        return rtn


    def set_eval_answer(self, ans):
        try:
            self.right_answer = eval(ans)
        except:
            self.valid = False
            print(f"Cannot eval {ans} {self.question} marked invalid")

    def calc_answer(self):
        str0 = re.sub("=\s*$", "", self.question)
        try:
            self.right_answer = eval(str0)
        except:
            self.valid = False
            print(f"Cannot eval {self.question} marked invalid")

    def update_type(self):
        #(free_form, flashcard_4x_choice_pics flashcard_4x_choice_pic flashcard_4x_choice_pics_text_prompt flashcard_text_only)
        if len(self.wrong_answers) == 0:
            self.type = "free_form"
            if self.right_answer == None:
                self.calc_answer()
        elif self.question.endswith(".png") and self.right_answer.endswith(".png"):
            self.type = "flashcard_4x_choice_pics"
        elif self.question.endswith(".png"):
            self.type = "flashcard_4x_choice_pic"
        elif self.right_answer.endswith(".png"):
            self.type = "flashcard_4x_choice_pics_text_prompt"
        else:
            self.type = "flashcard_text_only"
        



    