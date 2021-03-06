import time, subprocess


class ServerManager(object):

    def __init__(self, path, server_file, xms=1, xmx=1, gui=False):
        self.process = None
        self.path = path
        self.server_file = server_file
        self.online = False
        self.xms = xms
        self.xmx = xmx
        self.gui = gui

    def start(self):
        command = 'java -jar -Xms' + str(self.xms) + 'G -Xmx' + str(self.xmx) + 'G ' + self.path + '' + self.server_file
        if not self.gui: command += ' nogui'
        print('--- Started server with command: ' + command)
        if self.path == '':
            self.process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        else:
            self.process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, cwd=self.path)
        self.online = True

    def shutdown(self):
        self.message('Server will be shutting down for maintenance in 1 minute.')
        time.sleep(30)
        self.message('Shutting down for maintenance in 30 seconds.')
        time.sleep(20)
        self.message('Shutting down for maintenance in 10 seconds.')
        #self.message('Have some diamonds for the trouble.')
        #self.message('give @a minecraft:diamond 5', True)
        time.sleep(10)
        self.message('stop', True)
        time.sleep(30)
        self.online = False
        self.process.terminate()

    def crash_check(self):
        self.process.poll()
        if self.process.returncode in (0, 1):
            print(self.process.returncode)
            return True
        else:
            print(self.process.returncode)
            return False

    # Server chat can be passed as ServerManager.message('hello')
    def message(self, message, command=False):
        if not command:
            #self.process.stdin.write(b'say ### SMSW Message: \n')
            #self.process.stdin.flush()
            self.process.stdin.write(bytes('say ' + message + '\n', 'utf-8'))
            self.process.stdin.flush()
        else:
            self.process.stdin.write(bytes(message + '\n', 'utf-8'))
            self.process.stdin.flush()
