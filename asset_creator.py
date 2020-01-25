import os
from PIL import Image, ImageOps
# does not work on school computers

os.chdir("assets/za-hando-rackets")

def transparency(image):
    size = image.size
    image = bytearray(image.tobytes())

    for i in range(0, len(image), 4):
        #print(image[i:i+4])
        if image[i] == 0 and image[i+1] == 0 and image[i+2] == 0 and image[i+3] == 0:
            image[i] = 255
            image[i+1] = 255
            image[i+2] = 255
            image[i+3] = 0

    return Image.frombytes("RGBA", size, bytes(image))

base = Image.open("za-hando-racket-arm.gif").convert("RGBA")

bases = [base, ImageOps.mirror(base)]
names = ['left-', 'right-']

# hacky fix to avoid transparency issues at right angles with .rotate
def offset(x):
    if x%90 == 0:
        x += 0.01
    return x

for j in range(2):
    for i in range(0, 360, 5):
        transparency(bases[j].rotate(offset(i), expand=True)).save("za-hando-racket-arm-"+names[j]+str(i)+".gif", "GIF", transparency=0)
