import os


def write_file(bk, s):
    with open(os.path.join(os.path.dirname(__file__), "session_id." + bk), 'w') as file:
        file.write(s)


def read_file(bk, s):
    try:
        with open(os.path.join(os.path.dirname(__file__), "session_id." + bk), 'r') as file:
            return file.read()
    except:
        pass


# write_file('olimp', 'xxx')
print(read_file('olimp', 'asdf'))
