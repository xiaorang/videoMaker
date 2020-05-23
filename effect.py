from PIL import Image, ImageDraw, ImageFont

def transparent_back(img):
    # img = img.convert('RGBA')
    L, H = img.size
    color_0 = (255, 255, 255, 255)
    # print(color_0)
    for h in range(H):
        for l in range(L):
            dot = (l,h)
            color_1 = img.getpixel(dot)
            if color_1 == color_0:
                color_1 = color_1[:-1] + (0,)
                img.putpixel(dot,color_1)
    # return img

def drawText(img, txt, pos, fontName, fontSize, fontColor):
    # 颜色顺序：蓝色，绿色，红色
    # color2=(156, 238, 255)
    draw = ImageDraw.Draw(im=img)
    code= txt.strip()
    font= ImageFont.truetype(fontName, fontSize)
    textSize= draw.textsize(text=code, font=font)
    tx= pos[0]- textSize[0]// 2
    ty= pos[1]- textSize[1]// 2
    draw.text(xy=(tx, ty), text=code, fill=fontColor, font=font)

def emptyCircle(img, center, rad):
    draw = ImageDraw.Draw(img)
    x1= center[0]- rad
    y1= center[1]- rad
    x2= center[0]+ rad
    y2= center[1]+ rad
    draw.ellipse((x1, y1, x2, y2), fill=(0,0,0,0), outline='white', width=1)
    # transparent_back(img)
    # return img

def blackRect(img, alpha):
    draw = ImageDraw.Draw(img)
    x1= 0
    y1= 0
    x2= img.size[0]
    y2= img.size[1]
    draw.rectangle((x1, y1, x2, y2), fill=(0, 0, 0, alpha), outline='black', width=1)
    return img

if __name__=='__main__':
    width= 1208
    height= 720
    img= Image.new('RGBA', (width, height))
    blackRect(img)
    emptyCircle(img, (width//2, height//3), 100)
    im2= Image.open('part01_frame0000.jpg')
    r, g, b, a= img.split()
    im2.paste(img, (0,0), mask=a)
    im2.save('round1.png')
    