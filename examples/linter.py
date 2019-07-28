import os
import sys
import random
import datetime
from sqf.parser import parse
import sqf.analyzer
from sqf.exceptions import SQFParserError, SQFWarning

long=100
exceptions_problems=["(not private)"]
LINES=5
BRANCH="HEAD"
USER="local"
COMMIT="local_commit"
URL=""
LOGIN=""
TOCKEN=""
EMAIL=""
URL_CI=""
COMMIT_SHA=""

if len(sys.argv)>1:
    LINES=str(sys.argv[1])
    BRANCH=str(sys.argv[2])
    USER=str(sys.argv[3])
    COMMIT=str(sys.argv[4].replace("\n"," ").replace(" ","_"))
    URL=str(sys.argv[5])
    LOGIN=str(sys.argv[6])
    TOCKEN=str(sys.argv[7])
    EMAIL=str(sys.argv[8])
    URL_CI=str(sys.argv[9])
    COMMIT_SHA=str(sys.argv[10])


import os
DIR=str(os.path.abspath(os.path.join(str(os.path.dirname(os.path.realpath(__file__))), os.pardir)))
PATH=DIR+"/"+"sqf_linter"

INPUTS={
    "LINES":LINES,
    "BRANCH":BRANCH,
    "USER":USER,
    "COMMIT":COMMIT,
    "URL":URL,
    "LOGIN":LOGIN,
    "TOCKEN":TOCKEN,
    "EMAIL":EMAIL,
    "URL_CI":URL_CI,
    "COMMIT_SHA":COMMIT_SHA,
    "DIR":DIR,
    "PATH":PATH,
}

def linter(INPUTS):
    count_file=0
    count=0
    count_problem=0
    problems=[]
    for root, dirs, files in os.walk(INPUTS["DIR"]):
        for file in files:
            if file.endswith(".sqf"):
                count_file+=1
    if count_file>0: 
        for root, dirs, files in os.walk(INPUTS["DIR"]):
            for file in files:
                if file.endswith(".sqf"):
                    file_path=os.path.join(root, file)
                    print((file_path+" "*103)[:103])
                    count+=1
                    print('\r%s |%s| %s%% %s' % ('', '█' * int(100 * count // count_file) + '|' * (100 - int(100 * count // count_file)), ("{0:." + str(1) + "f}").format(100 * (count / float(count_file))), ''), end = '\r')
                    writer=[]

                    with open(file_path) as f:
                        exceptions_list=[]
                        try:
                            result = parse(f.read())
                        except SQFParserError as e:
                            writer.append('[%d,%d]:%s\n' % (e.position[0], e.position[1] - 1, e.message))
                            exceptions_list += [e]
                        exceptions = sqf.analyzer.analyze(result).exceptions
                        for e in exceptions:
                            writer.append('[%d,%d]:%s\n' % (e.position[0], e.position[1] - 1, e.message))
                        exceptions_list += exceptions
                        
                    if len(writer)>0:
                        for string in writer:
                            _str=""
                            count_problem+=1
                            isError=":error:" in string
                            line=string[string.find("[")+1:string.find(",")]
                            column=string[string.find(",")+1:string.find("]")]
                            
                            if isError:
                                exception=string[string.find(":error:")+7:-1]
                            else:
                                exception=string[string.find(":warning:")+9:-1]
                            
                            isException=False
                            for i in exceptions_problems:
                                if i in exception:
                                    isException=True
                            
                            problem=[file_path,line,column,exception,count_problem]
                            if isException:
                                if isError:
                                    problem.append("error_e")
                                else:
                                    problem.append("warning_e")
                            else:
                                
                                if isError:
                                    problem.append("error")
                                else:
                                    problem.append("warning")
                            problems.append(problem)
    return problems
def badge(label="",message="",link="",color=""):
    label=str(label)
    label=label.replace("/","")
    label=label.replace("-","--")
    label=label.replace(" ","_")
    message=str(message)
    message=message.replace("/","")
    message=message.replace("-","--")
    message=message.replace(" ","_")
    if color=="":
        random.seed(message)
        color=str("%03x" % random.randint(0, 0xFFFFFF))
    return "[![badge]("+"https://img.shields.io/badge/"+label+"-"+message+"-"+color+")]("+link+")"

def hinter(INPUTS,problems):
    text_log=(long*".")+"  \n"
    text_result=""
    
    count_warning=0
    count_error_e=0
    count_error=0
    count_warning_e=0
    
    for problem in problems:
        file_path=problem[0]
        line=problem[1]
        column=problem[2]
        exception=problem[3]
        id=problem[4]
        type=problem[5]
        
        if type=="error_e":
            count_error_e+=1
        elif type=="warning_e":
            count_warning_e+=1
        elif type=="error":
            count_error+=1
        elif type=="warning":
            count_warning+=1
        
        text_log+=(long*".")+"  \n"
        text_log+="FILE: "+str(file_path)+"  \n"
        text_log+="LINE: "+str(line)+"  \n"
        text_log+="COLUMN: "+str(column)+"  \n"
        text_log+="EXCEPTION: "+str(exception)+"  \n"
        text_log+="ID: "+str(id)+"  \n"
        text_log+="TYPE: "+str(type)+"  \n"
    
    count_total=count_warning+count_error_e+count_error+count_warning_e
    _state="succes"
    if count_error>0:
        _color="red"
        _state="failed"
    else:
        if count_warning>0:
            _color="orange"
            _state="warning"
        if count_error_e>0:
            _color="yellow"
            _state="succes_e"
        if count_warning_e>0:
            _color="yellowgreen"
            _state="succes_w"
        else:
            _color="green"
    text_result+=badge(link=INPUTS["URL"]+"/commit/"+INPUTS["COMMIT_SHA"],label=datetime.datetime.now().strftime("%a-%d "+"%H"+"h"+"%M"),message=INPUTS["COMMIT"])+" "       
    text_result+=badge(link=INPUTS["URL"]+"/tree/"+INPUTS["COMMIT_SHA"],message=INPUTS["USER"],label=INPUTS["BRANCH"])+" "
    text_result+=badge(link=INPUTS["URL_CI"]+"/artifacts/raw/public/errors.txt",label=_state,message=str(count_error)+"-"+str(count_warning)+"-"+str(count_error_e)+"-"+str(count_warning_e),color=_color)+" "

    text_result+=" \n"
    return text_log,text_result
def writer(INPUTS,text_log,text_result):
    try:
        _tmp=open(INPUTS['DIR']+"/README.md","r+")
        _str_readme=_tmp.read()
        _tmp.close()
    except:
        _str_readme=""
    _text_readme=text_result
    lines=_str_readme.split("  \n")
    stop=False
    startText='[![badge]('
    for l in range(len(lines)):
        line=lines[l]
        if len(line)>len(startText) and not(stop):
            if line[:len(startText)]==startText:
                if l>=int(INPUTS['LINES'])-1:
                    stop=True
                else:
                    _text_readme+=line
                    if l<len(lines)-1:
                        _text_readme+="  \n"
            else:
                stop=True
                _text_readme+=line
                if l<len(lines)-1:
                    _text_readme+="  \n"
        else:
            stop=True
            _text_readme+=line
            if l<len(lines)-1:
                _text_readme+="  \n"
    _tmp=open(INPUTS['DIR']+"/README.md","w")
    _tmp.write(_text_readme)
    _tmp.close()
    try:
        f=open(INPUTS['DIR']+"/public/errors.txt","w")
    except:
        os.mkdir(INPUTS['DIR']+"/public/")
        f=open(INPUTS['DIR']+"/public/errors.txt","w")
    _text=text_log
    f.write(_text)
    print(_text)
    f.close() 

problems=linter(INPUTS)
text_log,text_result=hinter(INPUTS,problems)  # Print result and return all string
writer(INPUTS,text_log,text_result)
