# v9的特点是调整视频生成方式为一次生成，增加背景缩放与移动的功能
# 加入了动态小物件（用眨眼的方式代表其动作）
# v8的特点是角色行为的外部定义，增加cover自动保存功能
# 实测，有字幕的视频无法再次连接
# 改变方式：组合音频，视频一次生成完整的，直接音视频合并
# 因为视频连接的时候会导致音频错位
# 增加从横屏图片一键生成抖音模式竖屏的功能
import sys
sys.path.append(r'D:\2020综合\技术使用\智能接口')
sys.path.append(r'D:\2020综合\技术使用\pythonTools')
sys.path.append(r'D:\2020综合\技术使用\视频处理')
sys.path.append(r'D:\2020综合\技术使用\音频处理')
sys.path.append(r'D:\2020综合\技术使用\图片处理')

import os
import shutil
import re
import random
from PIL import Image

from TTS import text2mp3
from filetool import *
import effect
import pyffmepg
import mp3mute

def getTimeLineMp4(aPath):
    import moviepy.editor as mpy
    lst=[]
    lst2={}
    b= 0
    flist= list(getFileList(aPath, '.mp4'))
    flist.sort()
    i= 1
    for f1 in flist:
        print(f1)
        clip = mpy.VideoFileClip(f1)
        a= round(clip.duration* 1000)
        print(a)
        b+= a
        lst.append(a)
        lst2[i]=b
        i+=1
    return lst, lst2


parmDefine={}
parmDefine['back']=['pic','frompos','topos','dur']
parmDefine['read']=[]
parmDefine['cover']=[]
parmDefine['mute']=['time']
parmDefine['talk']=['actor', 'action']
parmDefine['end']=['parm']
parmDefine['effect']=['effect','parm']
parmDefine['text']=['text','fontsize','parm','layer']
parmDefine['action']=['cmd','parm','scale','duration','pos','last']
parmDefine['def']=['voice','speed','tone','pic','rate']
parmDefine['defobj']=['pic','rate']
parmDefault={}
parmDefault['read']={'actor':'reader'}
parmDefault['mute']={'actor':''}
parmDefault['end']={'actor':''}
parmDefault['def']={'rate':1,'init':'00'}
parmDefault['defobj']={'rate':1,'init':''}
parmDefault['talk']={'action':''}
def readParm(code, parms, default={}):
    '''辅助函数，只读取名义参数的部分 
    '''
    obj= default.copy()
    # 因为在括号、引号内不排除逗号，所以用特殊拆分法
    # 这一句只能识别括号
    # pList = re.split(r",(?![^(]*\))", code)
    # 这个实现的比较完美
    pList = re.split(''',(?=(?:[^'"\(\)]|\([^\)]*\)|'[^']*'|"[^"]*")*$)''', code)
    print(pList)
    parm1= parms.copy()
    # print(parm1)
    # 第一遍，首先提取命名参数
    for str1 in pList.copy():
        if '=' in str1:
            print(str1)
            key, value= str1.split('=', 1)
            obj[key]= value
            print(str1)
            if key in parm1:
                parm1.remove(key)
            pList.remove(str1)
    # 第二遍，所有未命名的参数，按顺序
    for i in range(len(pList)):
        obj[parm1[i]]= pList[i]
    # print(obj)
    return obj
def readCmd(line, parms=None, default=None):
    '''从一行文本line中，
    根据一个列表parmList所规定的参数，读取一个dict以包含全部信息
    可以使用顺序参数，也可以用命名参数
    基本格式为：主题命名，冒号，参数
    '''
    lst= line.strip().split(':')
    cmd= lst[0].lower()
    if default is None:
        default= parmDefault.get(cmd, {})
    if len(lst)>1:
        code= lst[1]
        if parms is None:
            parms= parmDefine.get(cmd, [])
        obj= readParm(code, parms, default)
    else:
        obj=default.copy()
    obj['cmd']= cmd
    return obj
def defineInto(space, line, parms, default={}):
    '''从line中读取一个对名字赋值的等式
    等号后面的结构，由objdef指定
    将名字放入space中
    '''
    name, value= line.split('=', 1)
    space[name]= readParm(value, parms, default)
    print(line)
    print(space[name])
def makeMp3(mp3Path, codeLineName, timeLineName):
    '''从剧本定义中，提取文字内容和角色语音特征的定义
    调用text2mp3接口朗读为mp3文件
    并保存到mp3Path目录下，文件名为part开头跟00起始两位顺序数字的mp3文件
    同时，将朗读的内容形成列表，保存到由codeLineName指定的文件名中
    readAction函数为逐行驱动函数，是真正的入口
    '''
    clearDir(mp3Path)
    part= 0
    text= ''
    actors={}
    codeLine={}
    currentActor='reader'
    timeLine= {}
    def readBy(actorName, txt):
        def readByActor(name, tofile):
            actor= actors.get(name, None)
            if actor is not None:
                print('read by: ', actor)
                text2mp3(txt, tofile, actor['voice'], actor['speed'], actor['tone'])
            else:
                if name!="":
                    raise NameError('###error voice actor %s'%name)
        txt= txt.strip()
        print('-----------New read-------------- ')
        print('reader is: '+ actorName)
        print('txt is: '+ txt.split('\n')[0])
        file= os.path.join(mp3Path, 'part%02d.mp3'%part)
        if '+' not in actorName:
            # 单人朗读
            readByActor(actorName, file)
        else:
            # 多人朗读
            manyActor= actorName.split('+')
            a1= manyActor[0]
            readByActor(a1, file)
            tmpfile= os.path.join(mp3Path, 'temp.mp3')
            for a1 in manyActor[1:]:
                readByActor(a1, tmpfile)
                mp3mute.mp3overlay(file, tmpfile, file)
            # 最后删除临时文件
            os.remove(tmpfile)

        # 统一音频格式
        mp3mute.changeBitRate(file, file)
        recodeCode(mp3mute.getMp3Length(file), txt)
    def recodeCode(time, txt):
        print('rect part %d, %d'%(part, time))
        # obj={'time':time, 'code':txt}
        # timeLine[part]= obj
        timeLine[part]= time
        codeLine[part]= txt
    def readAction(line):
        nonlocal part, text, currentActor
        print(line)
        if line.strip()=='':
            text= text+ line
        elif line[0]=='#':
            line=line[1:]
            lst= line.strip().split(':')
            cmd= lst[0].lower()
            if cmd=='def':
                defineInto(actors, lst[1], parmDefine[cmd], parmDefault[cmd])
            elif cmd in ['read', 'talk', 'mute', 'end']:
                act= readCmd(line)
                # print(act)
                if part>0:
                    print('part: ', part)
                    readBy(currentActor, text)
                text= ''
                currentActor= act['actor']
                if currentActor!='':
                    readerName= currentActor
                else:
                    readerName= '<mute>'
                print('Reader now changed to %s'%readerName)
                part+= 1
                if cmd=='mute':
                    # 直接获取静音mp3
                    file= os.path.join(mp3Path, 'part%02d.mp3'%part)
                    mp3mute.getMute(eval(act['time'])* 1000, file)
                    print('-----mute to file------------- ')
                    print(file)
                    recodeCode(eval(act['time'])* 1000, '1')
                elif cmd=='end':
                    saveObj(codeLine, codeLineName)
                    saveObj(timeLine, timeLineName)
            else:
                print('---忽略指令：%s'%cmd)
        else:
            # 内容累加
            text= text+ line
    return readAction

def makeActionReader(timeLine, codeline, movieLineName):
    '''从剧本定义中，读取信息，形成核心脚本movie
    并保存到由全局变量movieLineName指定的文件名中
    readAction函数为逐行驱动函数，是真正的入口
    '''
    part= 0
    text= ''
    actors={}
    consts={}
    actionList=[]
    def calcTime():
        t= 0
        i= 1
        # 根据音频调整时间起点
        while i< part:
            t+= timeLine[i]
            i+= 1
        if len(codeline[part])> 0:
            t1= round(timeLine[part]* len(text.strip())/ len(codeline[part]))
        else:
            t1= 0
        print(part, t+t1)
        return t+ t1
    def addAction(obj):
        obj['part']= part
        obj['time']= calcTime()
        obj['duration']= timeLine[part]
        actionList.append(obj)                
    def readAction(line):
        nonlocal part, text
        if line.strip()=='':
            text= text+ line
        elif line[0]=='#':
            line=line[1:]
            lst= line.strip().split(':',1)
            cmd= lst[0].lower()
            if cmd=='def' or cmd=='defobj':
                defineInto(actors, lst[1], parmDefine[cmd], parmDefault[cmd])
            elif cmd=='defpos' or cmd=='var':
                defineInto(consts, lst[1], ['value'])
            elif cmd in ['effect', 'text', 'cover', 'back', 'end']:
                act= readCmd(line)
                addAction(act)
                if cmd=='end':
                    movie={}
                    movie['actors']= actors
                    movie['vars']= consts
                    movie['list']= actionList
                    print(movie)
                    saveObj(movie, movieLineName)
            elif cmd in ['read', 'mute', 'talk']:
                text= ''
                if part>0:
                    # 前一段结束
                    act= {'cmd':'end'}
                    addAction(act)
                # 旁白朗读
                part+= 1
                act= readCmd(line)
                addAction(act)
            else:
                if cmd in actors.keys():
                    # 分角色行为控制
                    parm= lst[1]
                    act= readParm(parm, parmDefine['action'])
                    act['actor']= cmd
                    if act['cmd'] not in ['leftin', 'leftout', 'rightin', 'rightout', 'centerin', 'centerout', 'rotmove', 'moveto', 'show', 'hide', 'action']:
                        print('action error %s'% act['cmd'])
                    addAction(act)
                else:
                    str1= '###cmd error: %s'%cmd
                    print(str1)
                    raise NameError(str1)
        else:
            # 内容累加
            text= text+ line
    return readAction

def resize(size, rate):
    return (round(size[0]* rate), round(size[1]* rate))


def makeKeyFrame(movie, picPath, framePath):
    '''从核心脚本movie中提取信息制作视频的关键帧图片
    视频大小，由剧本中的变量width, height指定
    每秒帧数，由剧本中变量fps指定
    保存在framePath目录中
    使用到的图片资源，在picPath中
    首先建立每层独立的图片，并保存
    最后再统一根据时间合并
    '''
    # 脚本中定义的变量
    consts={}
    # 载入角色动作定义
    actionDefine= readObj(os.path.join(picPath, 'actors.txt'))
    def setActorValue(name, time, prop, value):
        st={}
        st['value']=value
        st['time']=time
        actors[name][prop].append(st)
        actors[name][prop].sort(key=lambda x:x['time'], reverse=True)
    def getActorValue(name, time, prop):
        if prop in ['state', 'pos', 'scale', 'visible']:
            return findPreFrame(actors[name][prop], time)['value']
        elif prop=='pic':
            return getActorPic(name, time)
    def getMaxTime():
        return movie['list'][-1]['time']
    def getTimeStep():
        return 1000//eval('fps', consts)
    def frameSize():
        return eval('(width, height)', consts)
    def findPreFrame(flist, time):
        for fm in flist:
            if fm['time']<= time:
                return fm
        return None
    def addBlink(name, fromTime, toTime):
        i= fromTime
        pic= actors[name]['pic']
        act= actionDefine[pic]['blink']
        while i<= toTime:
            for fm in act:
                setActorValue(name, i, 'state', fm['state'])
                i+= random.randint(fm['time'][0], fm['time'][1])

    clearTree(framePath)
    makeSubPath(framePath, 'All')
    # 图层
    layer={}
    # 每个角色的图片（表情）、当前位置、可见性、当前状态
    actors={}
    frameId= 0
    picId= 0
    frameList={}
    # 角色定义信息获取
    actors= movie['actors']
    for name in actors.keys():
        actors[name]['pos']=[]
        setActorValue(name, 0, 'pos', (0,0))
        actors[name]['state']=[]
        st= actors[name].get('init')
        setActorValue(name, 0, 'state', st)
        if actors[name].get('blink'):
            addBlink(name, 0, getMaxTime())
        actors[name]['scale']=[]
        setActorValue(name, 0, 'scale', actors[name]['rate'])
        actors[name]['visible']=[]
        setActorValue(name, 0, 'visible', False)
        # print(actors[name])
    # 全部参数读入到local中，以备eval使用
    for var in movie['vars'].keys():
        # print(var, movie['vars'][var])
        str1= '%s=%s'%(var, movie['vars'][var]['value'])
        # print('var define: '+ str1)
        exec(str1, None, consts)
        # 变量名在函数内生效，可以出现在eval中
        print(var, '->', eval(var, consts))
    # 关键参数直接取用
    width= eval('width', consts)
    height= eval('height', consts)
    fps= eval('fps', consts)
    def getActorPic(name, time):
        act= actors[name]
        state= getActorValue(name, time, 'state')
        scale= float(getActorValue(name, time, 'scale'))
        file= os.path.join(picPath, act['pic']+ state+ '.png')
        if not os.path.exists(file):
            raise NameError('File not exists: %s'%file)
        pic= Image.open(file)
        # print(name, file, time, scale)
        if scale!= 1:
            pic= pic.resize(resize(pic.size, scale), Image.ANTIALIAS)
        return pic        
    def getActorLayer(name, time):
        visible= getActorValue(name, time, 'visible')
        if visible:
            pic= getActorPic(name, time)
            pos= getActorValue(name, time, 'pos')
            # print(name, time, pos)
            img= Image.new('RGBA', frameSize())
            img.paste(pic, posRound(pos))
        else:
            img= None
        return img
    def addMotion(name, fromTime, fromPos, toTime=None, toPos=None):
        if toTime is None:
            toTime= fromTime
        if toPos is None:
            toPos- fromPos
        i= fromTime
        a= toTime- fromTime
        setActorValue(name, i, 'visible', True)
        while i<= toTime:
            b= i- fromTime
            x= fromPos[0]+ (toPos[0]- fromPos[0])* b/ a
            y= fromPos[1]+ (toPos[1]- fromPos[1])* b/ a
            # print(name, fromPos, toPos, (x, y), i)
            setActorValue(name, i, 'pos', (x, y))
            i+= getTimeStep()
    def addAction(name, fromTime, toTime, actionName):
        pic= actors[name]['pic']
        act= actionDefine[pic][actionName]
        print(act)
        if toTime is None:
            toTime= fromTime+ getTimeStep()* len(act)* delay
        i= fromTime
        cc= 0
        while i<= toTime:
            for fm in act:
                # print(fm)
                setActorValue(name, i, 'state', fm['state'])
                i+= random.randint(fm['time'][0], fm['time'][1])
    def clearLayer(aLayer):
        layer[aLayer]= Image.new('RGBA', frameSize())
    def posAdd(pos, dPos):
        return (pos[0]+ dPos[0], pos[1]+ dPos[1])
    def posRound(pos):
        return (round(pos[0]), round(pos[1]))
    def circleEnd(part, fromTime, toTime, center):
        rad= width// 2
        step= (toTime- fromTime)/ (1000/ fps)
        clearLayer('mask')
        while fromTime< toTime:
            # print(fromTime, toTime)
            effect.blackRect(layer['mask'], 255)
            effect.emptyCircle(layer['mask'], center, rad)
            rad= rad- 10
            fromTime+= 1000/fps
            savePic('mask', fromTime)
    def savePic(aName, tim):
        layerPath= os.path.join(framePath, aName)
        if not os.path.exists(layerPath):
            os.makedirs(layerPath)

        outFile= os.path.join(layerPath, 'time%06d.png'%(tim))
        layer[aName].save(outFile)
        keyFrame= {}
        keyFrame['time']= '%06d'%(tim)
        keyFrame['pic']= outFile
        if aName not in frameList.keys():
            frameList[aName]= []
        frameList[aName].append(keyFrame)
    def blackOut(part, fromTime, toTime):
        alpha= 0
        step= 255 // (toTime- fromTime)/ (1000/ fps)
        clearLayer('mask')
        while fromTime< toTime:
            print(fromTime, toTime)
            effect.blackRect(layer['mask'], alpha)
            alpha= round(alpha+ step)
            fromTime+= 1000/fps
            savePic('mask', part, fromTime)
    def getNewestPic(tim, lay):
        if not lay in frameList.keys():
            return None
        else:
            for fm in frameList[lay][::-1]:
                if fm['time']<= '%06d'%(tim):
                    return fm['pic']
    def getFrame(time):
        crtImg= Image.new('RGB', frameSize(), 'black')
        # 背景
        file= getNewestPic(time, 'back')
        if file is not None:
            layImg= Image.open(file)
            crtImg.paste(layImg, (0, 0))
        # 文字放在底层
        file= getNewestPic(time, 'text')
        if file is not None:
            layImg= Image.open(file)
            r, g, b, a= layImg.split()
            crtImg.paste(layImg, (0, 0), mask= a)
        # 角色层
        for name in actors:
            img= getActorLayer(name, time)
            if img is not None:
                r, g, b, a= img.split()
                crtImg.paste(img, (0, 0), mask= a)
        # 遮罩层
        file= getNewestPic(time, 'mask')
        if file is not None:
            layImg= Image.open(file)
            r, g, b, a= layImg.split()
            crtImg.paste(layImg, (0, 0), mask= a)
        return crtImg

    # 执行所有指令
    for frame in movie['list']:
        print(frame)
        partId= int(frame['part'])
        if partId> maxPart:
            break
        time= int(frame['time'])
        actor= frame.get('actor')
        file= os.path.join(picPath, frame.get('pic',''))
        parm= frame.get('parm', None)
        if frame['cmd']== 'back':
            clearLayer('back')
            pic= Image.open(file).resize(frameSize(), Image.ANTIALIAS)
            pos1= frame.get('frompos', None)
            if pos1 is None:
                layer['back'].paste(pic, (0,0))
                savePic('back', time)
            else:
                pos1= eval(pos1, consts)
                pos2= eval(frame.get('topos', None), consts)
                a= time
                for i in range(20):
                    sc= pos1[0]+ (pos2[0]- pos1[0])* i/ 20
                    x= round(pos1[1]+ (pos2[1]- pos1[1])* i/ 20)
                    y= round(pos1[2]+ (pos2[2]- pos1[2])* i/ 20)
                    pic2= pic.resize(resize(frameSize(), sc), Image.ANTIALIAS)
                    layer['back'].paste(pic2, (x, y))
                    savePic('back', a)
                    a+= getTimeStep()
            # 切换背景的时候，所有的前景都应当被清空
        elif frame['cmd']== 'leftin':
            size= getActorPic(actor, time).size
            top= round(height- size[1])
            pos1= (-size[0], top)
            pos2= (eval(parm, consts), top)
            addMotion(actor, time, pos1, time+ 1000, pos2)
        elif frame['cmd']== 'leftout':
            pos= getActorValue(actor, time, 'pos')
            size= getActorPic(actor, time).size
            top= round(height- size[1])
            pos2= (round(- size[0]), top)
            toTime= time+ 1000
            addMotion(actor, time, pos, toTime, pos2)
            setActorValue(actor, toTime, 'visible', False)
        elif frame['cmd']== 'rightin':
            size= getActorPic(actor, time).size
            top= round(height- size[1])
            rtpos= round(width)- eval(parm, consts)- size[0]
            pos1= (width, top)
            pos2= (rtpos, top)
            addMotion(actor, time, pos1, time+ 1000, pos2)
        elif frame['cmd']== 'rightout':
            pos= getActorValue(actor, time, 'pos')
            size= getActorPic(actor, time).size
            top= round(height- size[1])
            pos2= (width, top)
            toTime= time+ 1000
            addMotion(actor, time, pos, toTime, pos2)
            setActorValue(actor, toTime, 'visible', False)
        elif frame['cmd']== 'centerin':
            size= getActorPic(actor, time).size
            top= round(height- size[1])
            mdpos= round(width/2- size[0])
            pos1= (mdpos, height)
            pos2= (mdpos, top)
            addMotion(actor, time, pos1, time+ 1000, pos2)
        elif frame['cmd']== 'centerout':
            pos= getActorValue(actor, time, 'pos')
            size= getActorPic(actor, time).size
            top= round(height- size[1])
            pos2= (pos[0], height)
            toTime= time+ 1000
            addMotion(actor, time, pos, toTime, pos2)
            setActorValue(actor, toTime, 'visible', False)
        elif frame['cmd']== 'show':
            setActorValue(actor, time, 'visible', True)
            if parm is not None:
                pos= eval(parm, consts)
                if isinstance(pos, int):
                    size= getActorValue(actor, time, 'pic').size
                    x= pos
                    y= round(height- size[1])
                    pos= (x, y)
                setActorValue(actor, time, 'pos', pos)
        elif frame['cmd']== 'hide':
            setActorValue(actor, time, 'visible', False)
        elif frame['cmd']== 'rotmove' or frame['cmd']=='moveto':
            pos= getActorValue(actor, time, 'pos')
            pos2= eval(parm,consts)
            dur= frame.get('last', None)
            if dur is not None:
                offset= eval(dur, consts)*1000
            else:
                offset= 2000
            addMotion(actor, time, pos, time+ offset, pos2)
        elif frame['cmd']== 'action':
            if parm=='blink':
                pos= getActorPos(actor, time)
                actors[actor]['state']= '00'
                pic0= getPic(actor,time)
                actors[actor]['state']= '01'
                pic1= getPic(actor,time)
                showActor(actor, partId, time, pic1, pos)
                showActor(actor, partId, time+ 500, pic0, pos)
            elif parm in ['00', '01', '02']:
                pos= getActorPos(actor, time)
                actors[actor]['state']= parm
                pic0= getPic(actor,time)
                showActor(actor, partId, time, pic0, pos)
        elif frame['cmd']=='cover':
            img= getFrame(time)
            img.save(os.path.join(framePath, 'cover%06d.jpg'%time))
        elif frame['cmd']=='text':
            clearLayer('text')
            code= frame['text'].strip()
            textCenter= eval(parm, consts)
            fontName= r'.\happy1.ttf'
            fontSize= int(frame['fontsize'])
            effect.drawText(layer['text'], code, textCenter, fontName, fontSize, 'white')
            savePic('text', time)
        elif frame['cmd']=='effect':
            dur= int(frame['duration'])
            # print(frame)
            if frame['effect']=='circle':
                circleEnd(partId, time, dur, (width//2, height//3))
            elif frame['effect']=='blackout':
                blackOut(partId, time- 1000, time)
        elif frame['cmd']=='read':
            # 新段落开始，时间清零
            time= 0
        elif frame['cmd']=='end':
            step= getTimeStep()
            dur= frame['duration']
            # 制作本段各帧
            for i in range(time, time+dur, step):
                outFile= os.path.join(framePath, 'All', 'frame%06d.jpg'%(picId))
                crtImg= getFrame(i)
                crtImg.save(outFile)
                picId+= 1
        elif frame['cmd']=='talk':
            # 新段落开始，时间清零
            dur= int(frame['duration'])
            show= frame['action']
            if show=='action':
                talkList= actor.split('+')
                for name in talkList:
                    addAction(name, time, time+dur, 'talk')

        frameId+= 1
    # file= os.path.join(framePath, 'frame.txt')
    # saveObj(frameList, file)
    # print('总图片：%d张，时间长度%d秒，合%d分%d秒'%(picId,picId//8,picId//8//60,picId//8%60))

def makeSrt(movie, timeLine, codeLine, output):
    '''从核心脚本movie中提取信息制作字幕文件，时间线定义来自timeLine
    保存为output文件
    '''
    srtId= 0
    def calcTime(part, allText, baseText, calcText):
        t= 0
        i= 1
        # 根据音频调整时间起点
        while i< part:
            t+= timeLine[i]
            i+= 1
        dura= timeLine[part]
        if len(allText)> 0:
            t1= dura* len(baseText)/ len(allText)
            t2= dura* len(calcText)/ len(allText)
        else:
            t1= 0
            t2= 0
        return t+t1, t2
    def getTimeStr(time):
        a1= time % 1000
        b1= time // 1000
        a2= b1 % 60
        b2= b1 // 60
        a3= b2 % 60
        b3= b2 // 60
        return '%02d:%02d:%02d,%03d'%(b3, a3, a2, a1)
    with open(output, 'w', encoding='utf-8') as f1:
        for frame in movie['list']:
            if frame['cmd']=='talk':
                partId= int(frame['part'])
                code= codeLine[partId].strip()
                print(code)
                # 多行拆分
                cdList= code.split('\n')
                code1= ''
                for lin in cdList:
                    srtId+= 1
                    time, dur= calcTime(partId, code, code1, lin)
                    code1+= lin
                    # dur= int(frame['duration'])
                    f1.write(str(srtId)+ '\n')
                    f1.write(getTimeStr(time)+ ' --> '+ getTimeStr(time+ dur)+ '\n')
                    f1.write(lin+ '\n\n')

def makeNovel(basePath, picPath, scriptFile):
    # 0、基础中间参数
    mp3Path= makeSubPath(basePath, '音频')
    framePath= makeSubPath(basePath, 'Frame')
    mp4Path= makeSubPath(basePath, 'movie')
    segPath= makeSubPath(basePath, '分段')
    tempPath= makeSubPath(basePath, 'temp')
    output4= os.path.join(tempPath,'combine.mp4')
    output3= os.path.join(tempPath,'combine.mp3')
    output5= os.path.join(tempPath,'result.mp4')
    srtName= os.path.join(tempPath,'combine.srt')
    srtName= '_combine.srt'
    outfile= os.path.join(basePath, gOutFile)
    # print(srtName)
    # 中间生成的辅助文件
    timeLineName= os.path.join(tempPath,'timeLine.txt')
    Mp4timeLineName= os.path.join(tempPath,'timeLine2.txt')
    Mp4timeSumName= os.path.join(tempPath,'timeLine2Sum.txt')
    codeLineName= os.path.join(tempPath,'codeLine.txt')
    movieLineName= os.path.join(tempPath,'movie.txt')
    # 加速测试及调试使用的参数
    TTS= 1
    MakeKeyFrame= 1
    allother= 1
    CombineMp4= allother
    CombineMp3= allother
    MakeSrt= allother
    LinkResult= allother
    LinkSrt= allother
    # 1、分角色生成音频
    #   同时，从剧本中提取对话，为了精确计算动作时间点
    #   以及每个MP3的实际时间
    if TTS==1:
        readFileLine(scriptFile, makeMp3(mp3Path, codeLineName, timeLineName))
    # 2、完整获取动作的时间线
    timeline= readObj(timeLineName)
    codeline= readObj(codeLineName)
    readFileLine(scriptFile, makeActionReader(timeline, codeline, movieLineName))
    # 3、根据完整的时间线生成所有帧
    movie= readObj(movieLineName)
    if MakeKeyFrame==1:
        makeKeyFrame(movie, picPath, framePath)
    # 4、根据图片帧，制作视频
    if CombineMp4==1:
        pyffmepg.makeMp4(os.path.join(framePath, 'all'), 'frame', output4, 20)
    # 5、音频合并
    if CombineMp3==1:
        mergeMp3(mp3Path, output3)
    # 6、用时间线制作完整的字幕文件
    if MakeSrt==1:
        makeSrt(movie, timeline, codeline, srtName)
    # 7、音视频合并
    if LinkResult==1:
        pyffmepg.combineMp3(output4, output3, output5)
        # linkMp4(segPath, timeline, output)
    # 8、字幕合并
    if LinkSrt==1:
        pyffmepg.combineSrcipt(output5, srtName, outfile)

def makeVertical(basePath, title):
    tempPath= makeSubPath(basePath, 'temp')
    framePath= makeSubPath(basePath, 'Frame')
    vert_frame= os.path.join(framePath, 'frame2')
    output3= os.path.join(tempPath,'combine.mp3')
    srtName= '_combine.srt'
    # srtName= r'D:\2020综合\视频制作\_combine.srt'
    outfile= os.path.join(basePath,'out_v.mp4')
    frameVertical(os.path.join(framePath, 'all'), vert_frame, title)
    verticalLastState(vert_frame, basePath, output3, srtName, outfile)
    
def verticalLastState(framePath, basePath, mp3Name, srtName, outName):
    CombineMp4= 1
    LinkResult= 1
    LinkSrt= 1
    tempPath= makeSubPath(basePath, 'temp')
    output4= os.path.join(tempPath,'combine_v.mp4')
    output5= os.path.join(tempPath,'result_v.mp4')
    # 1、根据图片帧，制作视频
    if CombineMp4==1:
        pyffmepg.makeMp4(framePath, 'frame', output4, 20)
    # 2、音视频合并
    if LinkResult==1:
        pyffmepg.combineMp3(output4, mp3Name, output5)
        # linkMp4(segPath, timeline, output)
    # 3、字幕合并
    if LinkSrt==1:
        pyffmepg.combineSrcipt2(output5, srtName, outName)

def frameVertical(framePath, toPath, title):
    imgList= getFileList(framePath, '.jpg')
    for file1 in imgList:
        img= Image.open(file1)
        pic= img.resize((720, 405), Image.ANTIALIAS)
        crtImg= Image.new('RGB', (720, 1280), 'black')
        textCenter= (360, 120)
        fontName= r'.\happy1.ttf'
        fontSize= 75
        effect.drawText(crtImg, title, textCenter, fontName, fontSize, 'white')
        crtImg.paste(pic, (0, 295))
        name= getFileName(file1)
        file2= os.path.join(toPath, name)
        crtImg.save(file2)

def mergeMp3(segPath, output):
    fList= list(getFileList(segPath, '.mp3'))
    fList.sort()
    lst=[]
    for f1 in fList:
        lst.append(f1)
        print(f1)
    mp3mute.mp3merge(lst, output)

def backupAll(picPath, scriptName, back):
    print(__file__)
    lst1= getFileList(picPath, '.jpg')
    lst2= getFileList(picPath, '.jfif')
    lst3= getFileList(picPath, '.png')
    f1= os.path.join(r'D:\2020综合\技术使用\语音生成', 'TTS.py')
    f2= os.path.join(r'D:\2020综合\技术使用\pythonTools', 'filetool.py')
    f3= (__file__)
    f4= os.path.join(os.path.dirname(__file__), 'effect.py')
    f5= scriptName
    f6= os.path.join(r'D:\2020综合\技术使用\视频改大小并组合', 'vedioCombine.py')
    f7= os.path.join(r'D:\2020综合\视频制作\技术', 'mp3mute.py')
    print(f5)
    lst= list(lst1)+ list(lst2)+ list(lst3)+ [f1, f2, f3, f4, f5, f6]
    if not os.path.exists(back):
        os.makedirs(back)
    for file in lst:
        toFile= os.path.join(back, getFileName(file))
        print(toFile)
        shutil.copyfile(file, toFile)
        
if __name__ == '__main__':
    # 所有默认参数，都可以在剧本中设置
    # 视频大小
    # width= 1280
    # height= 720
    # 每秒帧数
    inter= 20
    # 默认输出文件名
    gOutFile= 'out.mp4'
    maxPart= 1126
    # 项目根路径
    base= r'D:\2020综合\视频制作\真话国'
    pic= r'D:\2020综合\视频制作\素材\truth'
    script= os.path.join(base, '剧本_答案_分析.txt')
    makeNovel(base, pic, script)
    # scriptFile= os.path.join(basePath, '剧本_答案.txt')
    # 最终mp4文件名
    base= r'D:\2020综合\视频制作\测试'
    pic= r'D:\2020综合\视频制作\素材\truth'
    script= os.path.join(base, '剧本.txt')
    # makeNovel(base, pic, script)
    str1= r'D:\2020综合\视频制作\喝啤酒\Frame\all'
    str2= r'D:\2020综合\视频制作\喝啤酒\Frame\frame2'
    str3= r'D:\2020综合\视频制作\喝啤酒\out4.mp4'
    str4= r'D:\2020综合\视频制作\喝啤酒\out2.mp3'
    str5= r'D:\2020综合\视频制作\喝啤酒\out5.mp4'
    str6= r'D:\2020综合\视频制作\喝啤酒\out6.mp4'
    # frameVertical(str1, str2, '《谁喝啤酒》')
    # makeVertical(base)
    # makeVertical(base, '《谁喝啤酒》')
    # 
    # changeName(str1, str2)
    # pyffmepg.makeMp4(str2, 'frame', str3, 20)
    # pyffmepg.combineMp3(str3, str4, str5)
    # pyffmepg.combineSrcipt(str5, '_combine.srt', str6)

    # makeVertical(str1, str2)
    # scriptAllMp4()
    # mergeMp3(str1, str2)
    # linkMp4Graduate(str1, tl, str2, 20)
    # linkMp4(str1, tl, str2)
    # txt= 
    # text2mp3(txt, tofile, actor['voice'], actor['speed'], actor['tone'])

    # 将全部内容做备份(包括剧本、图片素材与代码)
    backPath= os.path.join(r'D:\2020综合\将来也许\以前项目\系列视频', 'classQuiz')
    # backupAll(base, script, backPath)
    str1= 'text:《来杯啤酒》,fontsize=75,pos=title,layer=t1'
    str1= 'up,init=00,blink=True'
    # a= readCmd(str1)
    a= readParm(str1, parmDefine['defobj'], parmDefault['defobj'])
    print(a)  # v7版本，行数763
