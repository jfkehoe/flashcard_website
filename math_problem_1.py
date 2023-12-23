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

        self.print_order = "a b"
        self.a = None
        self.b = None


templates = []
templates.append(problem_template("+", "Add %d and %d"))
templates.append(problem_template("+", "What is %d and %d"))
templates.append(problem_template("+", "What is the sum of %d and %d?"))
templates.append(problem_template("+", "What is %d increased by %d"))
templates.append(problem_template("+", "What is the total of %d and %d"))
templates.append(problem_template("+", "What is %d more than %d?"))

templates.append(problem_template("-", "What is %d minus %d?"))
templates.append(problem_template("-", "What is %d less %d?"))
templates.append(problem_template("-", "What is %d fewer than %d"))
templates[-1].print_order = "b a"
templates.append(problem_template("-", "Take away %d from %d"))
templates[-1].print_order = "b a"
templates.append(problem_template("-", "Reduce %d by %d"))
templates.append(problem_template("-", "Subtract %d from %d"))
templates[-1].print_order = "b a"
templates.append(problem_template("-", "What remains from a group of %d after taking away %d?"))

templates.append(problem_template("x", "What is double of %d?"))
templates[-1].print_order = "b"
templates[-1].a = 2
templates.append(problem_template("x", "What is triple %d?"))
templates[-1].print_order = "b"
templates[-1].a = 3
templates.append(problem_template("x", "What is %d times %d?"))
templates.append(problem_template("x", "What is %d multipled %d?"))

templates.append(problem_template("÷", "Divide %d by %d"))
templates.append(problem_template("÷", "What is half of %d?"))
templates[-1].print_order = "a"
templates[-1].b = 2
templates.append(problem_template("÷", "What is one quarter of %d?"))
templates[-1].print_order = "a"
templates[-1].b = 4
templates.append(problem_template("÷", "What is one third of %d?"))
templates[-1].print_order = "a"
templates[-1].b = 3
templates.append(problem_template("÷", "If I have %d in %d equal groups, how large are the groups?"))
templates.append(problem_template("÷", "What is %d split equally into %d parts?"))

class simple_problem():
    def __init__(self, max_val):
        self.max_val = max_val
        self.c = random.randint(2, max_val)
        self.a = random.randint(1, self.c)
        self.b = self.c - self.a
        self.text = f"{self.a} + {self.b} ="
        self.right_ans = self.c
        print(self.text)

    def get_possible_answers(self, cnt):
        r = [self.right_ans]
        r0 = self.wrong_answers()
        random.shuffle(r0)
        r += r0[0:cnt-1]
        random.shuffle(r)
        return [str(i) for i in r]

    def wrong_answers(self):
        r = list(range(self.max_val+1))
        r.remove(self.right_ans)
        return r

    def right_answer(self):
        return self.right_ans

    def check_correct(self, ans):
        if ans == str(self.right_ans):
            return True
        else:
            return False





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
        if self.template.print_order == "a b":
            self.text = self.template.text%(self.a, self.b)
        elif (self.template.print_order == "a"):
            self.text = self.template.text%(self.a)
        elif (self.template.print_order == "b"):
            self.text = self.template.text%(self.b)
        else:
            self.text = self.template.text%(self.b, self.a)

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


if __name__ == '__main__':
    ...



