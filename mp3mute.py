# 直接获得的静音mp3与TTS生成的mp3帧率不一样
# 如果直接使用，无法正常连接视频，必须先做统一
from pydub import AudioSegment

import time


muteName= r'bgm.mp3'

def getMute(time, outMp3):
    # print('mute %d'%time)
    song1= AudioSegment.from_mp3(muteName)
    song2= song1[:time]
    song2= song2.set_frame_rate(16000)
    song2.export(outMp3, format="mp3", bitrate='64k') #导出为MP3格式

def changeBitRate(file, outfile):
    mute= AudioSegment.from_mp3(muteName)
    song1= AudioSegment.from_mp3(file)
    a= len(song1)
    step= 100
    print(a)
    if a%step!=0:
        # 将音频补满0.1秒
        b= (a//step+ 1)* step
        c= b- a
        song1= song1+ mute[:c]
    print(len(song1))
    song2= song1.set_frame_rate(16000)
    # print(song1.sample_width, song1.frame_rate, song1.channels)
    song2.export(outfile, format="mp3", bitrate='64k') #导出为MP3格式

def mp3overlay(f1, f2, outfile):
    song1= AudioSegment.from_mp3(f1)
    song2= AudioSegment.from_mp3(f2)
    song3= song1.overlay(song2)
    song3.export(outfile, format="mp3", bitrate='64k') #导出为MP3格式

def getMp3Length(aName):
    song = AudioSegment.from_mp3(aName)
    return len(song)

def mp3merge(mp3list, output):
    #加载MP3文件
    song1 = AudioSegment.from_mp3(mp3list[0])
    for f in mp3list[1:]:
        print(len(song1))
        song2 = AudioSegment.from_mp3(f)
        #拼接两个音频文件
        song1 = song1 + song2
     
    print(len(song1))
    #导出音频文件
    song1.export(output, format="mp3") #导出为MP3格式

