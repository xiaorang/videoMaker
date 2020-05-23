import os

ffmepgPath= r'D:\tools\ffmpeg\bin\ffmpeg.exe'

def makeMp4(aPath, aName, aOutput, fps):
    '''将aPath中，以aName开头并跟4位数字的所有jpg文件连成MP4文件，保存在aOutpu中
    其中ffmpeg的位置在函数中硬编码指定
    每秒帧数由fps指定
    '''
    if(os.path.exists(aOutput)):
        os.remove(aOutput)
    cmd= ffmepgPath+ ' -y -r '+ str(fps)+ ' -i '+ aPath+ r'\\'+ aName+ r'%06d.jpg -vcodec mpeg4 '+ aOutput
    print(cmd)
    txt= os.system(cmd)
    # print(txt)

def combineMp3(mp4, mp3, out):
    '''将一个指定的mp4与mp3文件合并为out文件
    '''
    if(os.path.exists(out)):
        os.remove(out)
    # cmd= r'D:\tools\ffmpeg\bin\ffmpeg.exe -i '+ mp3+ ' -i '+ mp4+ ' '+ out
    cmd= ffmepgPath+ ' -i '+ mp3+ ' -i '+ mp4+ ' -vcodec copy -acodec copy '+ out
    print(cmd)
    txt= os.system(cmd)
    # print(txt)

def vedioLink(fList, output):
    '''将文件列表fList所标明的mp4文件连接为一个整体mp4文件
    输出为output
    中间会建立一个临时文件 '_vedio_temp.txt'
    '''
    if(os.path.exists(output)):
        os.remove(output)
    tempFile= '_vedio_temp.txt'
    with open(tempFile, 'w') as f1:
        for name in fList:
            f1.write("file '%s'\n"%name)
    cmd= ffmepgPath+ " -f concat -safe 0 -i %s -c copy %s"%(tempFile, output)
    txt= os.system(cmd)
    print(txt)

def combineSrcipt(mp4, srt, out):
    ''' 将mp4视频文件与srt字幕文件融合
    生成视频保存为out
    '''
    if(os.path.exists(out)):
        os.remove(out)
    cmd= ffmepgPath+ ' -i '+ mp4.replace('\\', '/')+ ' -vf subtitles="'+ srt.replace('\\', '/')+ '" '+ out.replace('\\', '\\\\')
    print(cmd)
    txt= os.system(cmd)
    # print(txt)    

def combineSrcipt2(mp4, srt, out):
    ''' 将mp4视频文件与srt字幕文件融合
    生成视频保存为out
    '''
    if(os.path.exists(out)):
        os.remove(out)
    cmd= ffmepgPath+ ' -i '+ mp4+ ' -lavfi "subtitles=\''+ srt+ '\':force_style=\'Alignment=0,MarginL=5,Fontsize=12,MarginV=100\'" '+ out
    print(cmd)
    txt= os.system(cmd)
    # print(txt)    
