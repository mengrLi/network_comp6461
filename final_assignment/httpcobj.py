# from httplib import post, get
# from httplib import post
# from httplib import get
import httplib


class httpcobj:
    def __init__(self,obj_id):
        self.id = obj_id

    def do_get(self, arg):
        # print  arg
        print(" ------ httpc [" + str(self.id) + "] sent a get request ------")
        # print arg
        args = arg.split(' ')
        is_v = False
        o_path = ''
        headers = {}
        url = eval(args[-1])

        if '-v' in args:
            is_v = True

        if '-o' in args:
            o_index = args.index('-o')
            o_path = args[o_index + 1]

        if '-h' in args:
            h_index = 0
            for i in args:
                if i == '-h':
                    header = args[h_index + 1].split(':')
                    headers[header[0]] = header[1]
                h_index += 1

        httplib.get(url, headers, is_v, o_path)
        print(" ------ httpc [" + str(self.id) + "] end the get request ------")

    def do_post(self, arg):
        # print arg
        print(" ------ httpc [" + str(self.id) + "] sent a post request ------")
        args = arg.split(' ')
        is_v = False
        o_path = ''
        headers = {}
        url = eval(args[-1])
        data = ''
        file_path = ''

        if '-v' in args:
            is_v = True

        if '-o' in args:
            o_index = args.index('-o')
            o_path = args[o_index + 1]

        if '-h' in args:
            h_index = 0
            for i in args:
                if i == '-h':
                    header = args[h_index + 1].split(':')
                    headers[header[0]] = header[1]
                h_index += 1

        if '-d' in args:
            d_index = args.index('-d')
            data = args[d_index + 1]

        if '-f' in args:
            f_index = args.index('-f')
            file_path = args[f_index + 1]

        httplib.post(url, headers, is_v, o_path, file_path, data)
        print(" ------ httpc [" + str(self.id) + "] end the post request ------")

