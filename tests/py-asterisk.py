from Asterisk import Manager


if __name__ == '__main__':
    manager = Manager.Manager(('localhost', 4321),
                              'plop', "plop",
                              listen_events=False)
    print manager.Command("group show channels")[2:-1]
