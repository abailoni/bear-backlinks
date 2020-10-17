import re

p = re.compile(r"\[.+")
m = p.findall("[asdatet\nsdfsdfs\ndsdfsdfst")
print(m)
