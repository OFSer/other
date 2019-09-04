import os
import xlwt
import time
import shutil
import codecs
import smtplib
import email.header
import email.mime.text
import email.mime.multipart
import email.mime.application
from util import getProperty
from email.mime.image import MIMEImage

class SendMail(object):
    def __init__(self):
        self.sendFrom = getProperty("From")
        self.sendTo = getProperty("To").split(",")
        self.connect = getProperty("message")
        self.sendFile = list()
        for i in getProperty("File").split(","):
            self.sendFile.append(i.replace("\r", ""))
        self.msg = None

    def setEmailHeader(self):
        self.msg = email.mime.multipart.MIMEMultipart()
        self.msg['from'] = self.sendFrom
        self.msg['to'] = ";".join(self.sendTo)
        self.msg['subject'] = email.header.Header(getProperty("Subject"))

    def setMessage(self):
        text = email.mime.text.MIMEText(self.connect, 'plain', 'utf-8')
        self.msg.attach(text)

    def setFile(self):
        for file in self.sendFile:
            if os.path.exists(file):
                with codecs.open(file, "rb") as f:
                    attr = email.mime.application.MIMEApplication(f.read())
                attr.add_header('Content-Disposition', 'attachment',filename=('utf-8', '', file))
                self.msg.attach(attr)
            else:
                print ("{0} file is not exists!".format(file))

    def sendemailLast(self):
        smtp = smtplib.SMTP()
        smtp.connect("xxxxxx.net", 2525)
        smtp.login('username', 'password')
        smtp.sendmail(self.sendFrom, self.sendTo, self.msg.as_string())

    def planFile(self):
        startrow = 0
        startcol = 0
        tmpfile = "annex.txt"
        excfile = "annex.xls"
        tmpbool = os.path.exists(tmpfile)
        excbool = os.path.exists(excfile)
        if tmpbool:
            os.remove(tmpfile)
        if excbool:
            os.remove(excfile)
        day = time.strftime("%Y%m%d", time.localtime())
        filepath = "/data/count/cam_count/{0}/cam_count_{0}.log".format(day)
        shutil.copy(filepath, tmpfile)
        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet("camera_restart")
        with codecs.open(tmpfile, encoding="utf-8") as fw:
            text_list = fw.readlines()
        for line in text_list:
            ws.write(startrow, startcol, line)
            startrow += 1
            wb.save(excfile)

def main():
    sendMail = SendMail()
    sendMail.planFile()
    sendMail.setEmailHeader()
    sendMail.setMessage()
    sendMail.setFile()
    sendMail.sendemailLast()

if __name__ == '__main__':
    main()
