import os
import re
import shutil

path = "/home/jfkehoe/downloads/"

old_names = []
files = os.listdir(path)
old_names = [i for i in files if i.endswith(".csv")]

for f in files:
    r = re.match("^Danek.* (\d+.*)", f)
    if (r):
        f0 = path + f 
        f1 = "csvs/" + r[1]
        print(f"cp {f0} {f1}")
        shutil.copyfile(f0, f1)


