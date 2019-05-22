import cmd

# from server import run_server
import server

class httpfs (cmd.Cmd):
    prompt = ''
    print ('Please initial server: ')
    def do_httpfs(self,arg):
        arguments = arg.split(' ')
        is_v = False
        port = 9988
        dir_path = '../ass3'

        if '-v' in arguments:
            is_v = True

        if '-p' in arguments:
            p_index = arguments.index('-p')
            port = int(arguments[p_index + 1])

        if '-d' in arguments:
            d_index = arguments.index('-d')
            dir_path = arguments[d_index + 1]

        server.run_server(is_v, port, dir_path)

    def do_exit(self, arg):
        return True


if __name__ == '__main__':
    httpfs().cmdloop()
