import codecs
import re

fileName = "msg.conf"
def getProperty(property):
    with codecs.open(fileName, encoding="utf-8") as f:
        if property != "message":
            for line in f.readlines():
                if line.startswith("{0} = ".format(property)):
                    value = line.split("{0} = ".format(property))[1]
                    print (value.strip('\n'))
                    return value.strip('\n')
        else:
            reg = re.compile(r"message = '''((.*\n)*)'''")
            result = reg.findall(f.read())
            print (result[0][0])
            return  result[0][0]

#getProperty("From")
#getProperty("To")
#getProperty("Subject")
#getProperty("message")
