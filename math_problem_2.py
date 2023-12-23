

import random

class problem_template():
    def __init__(self, operator, text):
        self.text = text
        self.valid = True
        if operator in "+ - x ÷":
            self.operator = operator
        elif operator.startswith("add"):
            self.operator = "+"
        elif operator.startswith("sub"):
            self.operator = "-"
        elif operator.startswith("mul"):
            self.operator = "x"
        elif operator.startswith("div"):
            self.operator = "÷"
        else:
            self.valid = False
            print(f"Invalid operator {operator}")


names = dict()
#names["%n"] = ["%sp", "%op", "%pp"]
names["John"] = ["he", "him", "his"]
names["James"] = ["he", "him", "his"]
names["Robert"] = ["he", "him", "his"]
names["Michael"] = ["he", "him", "his"]
names["William"] = ["he", "him", "his"]
names["David"] = ["he", "him", "his"]
names["Joseph"] = ["he", "him", "his"]
names["Richard"] = ["he", "him", "his"]
names["Charles"] = ["he", "him", "his"]
names["Thomas"] = ["he", "him", "his"]
names["Mary"] = ["she", "her", "her's"]
names["Elizabeth"] = ["she", "her", "her's"]
names["Jennifer"] = ["she", "her", "her's"]
names["Linda"] = ["she", "her", "her's"]
names["Susan"] = ["she", "her", "her's"]
names["Sarah"] = ["she", "her", "her's"]
names["Jessica"] = ["she", "her", "her's"]
names["Helen"] = ["she", "her", "her's"]
names["Nancy"] = ["she", "her", "her's"]
names["Betty"] = ["she", "her", "her's"]

#template fields
#%d1, %d2, %d3... digits, constrained by problem
#%n name
#%sp subject pronoun he / she
#%op object pronoun him / her
#%pp possesive pronoun his / her's

templates = []
templates.append(problem_template("+", "Add %a and %b"))
templates.append(problem_template("+","On the weekend, there are %a adults and %b children in a train car.  How many pasengers are on board?"))
templates.append(problem_template("+","%n0 collects %a pine cones. %sp0 brother Mike gives %sp0 %b more.  How many pine cones does %n0 have?"))
templates.append(problem_template("+","%a students from 1st grade enroll in a Kung Fu class.  After a few days, %b more join.  How many total students are in the class?"))
templates.append(problem_template("+","A ball pit has %a colored balls in it. %n0 throws %b more balls into the pit. How many balls are in the pit now?"))
templates.append(problem_template("+","A baby beaver weighed %a pounds in October.  The weight increased by %b pounds in three months.  What would the new weight be?"))
templates.append(problem_template("+","%n0 ordered a pizza and a chocolate chip cookie.  The pizza cost $%a and the cookie was $%b. How much money did %sp0 spend?"))


class problem():
    def __init__(self, max_val):
        #a+b = c
        #a op b = c
        self.template = random.choice(templates)
        print(self.template.operator + " :: " + self.template.text)
        self.operator = self.template.operator
        if self.template.operator == "+" :
            self.c = random.randint(10, max_val)
            self.a = random.randint(1,self.c)
            self.b = self.c - self.a
        elif self.template.operator == "-":
            self.a = random.randint(10, max_val)
            self.b = random.randint(1,self.a)
        elif self.template.operator == "x":
            if self.template.a:
                self.a = self.template.a
            else:
                self.a = random.randint(1,int(max_val/3))

            self.b = random.randint(1,int(max_val/self.a))
        elif self.template.operator == "÷":
            if self.template.b:
                self.b = self.template.b
            else:
                self.b = random.randint(1,int(max_val/3))

            self.c = random.randint(1,int(max_val/self.b))
            self.a = int(self.c * self.b)

        print(f"a: {self.a}  b: {self.b}")
        my_names = random.sample(names.keys(), 3)
        self.text = self.template.text
        for i in range(0,3):
            self.text = self.text.replace(f"%n{i}", my_names[i])
            self.text = self.text.replace(f"%sp{i}", my_names[i])
            self.text = self.text.replace(f"%op{i}", my_names[i])
            self.text = self.text.replace(f"%pp{i}", my_names[i])

        self.text = self.text.replace("%a", str(self.a))
        self.text = self.text.replace("%b", str(self.b))

        self.right_ans = f"{self.a} {self.operator} {self.b}"

    def get_possible_answers(self, cnt):
        r = [self.right_ans]
        r0 = self.wrong_answers()
        random.shuffle(r0)
        r += r0[0:cnt-1]
        random.shuffle(r)
        return r

    def wrong_answers(self):
        r = []
        operators = "+ - x ÷".split(" ")
        if self.operator == "+" or self.operator == "x":
            operators.remove(self.operator)

        for op in operators:
            r.append(f"{self.a} {op} {self.b}")
            r.append(f"{self.b} {op} {self.a}")

        if self.right_ans in r:
            r.remove(self.right_ans)

        return r

    def right_answer(self):
        return self.right_ans

    def check_correct(self, ans):
        if ans == self.right_ans:
            return True
        else:
            return False
