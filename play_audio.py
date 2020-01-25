import winsound

while True:
    cmd = input()
    instruction, file = cmd.split("|")
    if instruction == "loop":
        winsound.PlaySound("assets/"+file+".wav", winsound.SND_LOOP | winsound.SND_ASYNC)
    else:
        winsound.PlaySound("assets/"+file+".wav", winsound.SND_ASYNC)
