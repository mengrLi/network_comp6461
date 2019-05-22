import cmd
import threading

# from httpcobj import httpcobj
import httpcobj
import httplib
# from httplib import post, get


class Multihttpc (cmd.Cmd):
    prompt = 'httpc '

    def do_help(self, arg):
        print('httpc is a curl-like application but supports HTTP protocol only.')
        print('Usage:')
        print('\t httpc command [arguments]')
        print('The commands are:')
        print('get \t executes a HTTP GET request and prints the response.')
        print('post \t executes a HTTP POST request and prints the response.')
        print('help \t prints this screen.')
        print('Use "httpc help [command]" for more information about a command.')

        if arg == 'get':
            print('usage: httpc get [-v] [-h key:value] URL')
            print ('Get executes a HTTP GET request for a given URL.')
            print('-v \t Prints the detail of the response such as protocol, status,and headers.')
            print('-h key:value  \t Associates headers to HTTP Request with the format key:value.')

        elif arg == 'post':
            print('usage: httpc post [-v] [-h key:value] [-d inline-data] [-f file] URL')
            print('Post executes a HTTP POST request for a given URL with inline data or from file.')
            print('-v \t Prints the detail of the response such as protocol, status,and headers.')
            print("-h key:value \t Associates headers to HTTP Request with the format'key:value'.")
            print('-d string \t Associates an inline data to the body HTTP POST request.')
            print('-f file \t Associates the content of a file to the body HTTP POST request.')
            print('Either [-d] or [-f] can be used but not both.')



    def do_get(self,arg):
        arguments = arg.split(' ')
        url = eval(arguments[-1])


        # -v Prints the detail of the response such as protocol, status,and headers.
        is_v = False
        if '-v' in arguments:
            is_v = True

        # bonus -o.

        o_filepath = ''
        if '-o' in arguments:
            o_index = arguments.index('-o')
            o_filepath = arguments[o_index+1]

        # -h key:value Associates headers to HTTP Request with the format'key:value'.
        headers = {}
        if '-h' in arguments:
            h_index = 0
            for i in arguments:
                if i == '-h':
                    header = arguments[h_index + 1].split(':')
                    headers[header[0]] = header[1]
                h_index += 1

        httplib.get(url,headers,is_v,o_filepath)



    def do_post(self, arg):
        print ("arg"+arg)
        arguments = arg.split(' ')

        url = eval(arguments[-1])
         # -v
        is_v = False
        if '-v' in arguments:
            is_v = True
         #-h
        headers = {}
        if '-h' in  arguments:
            h_index = 0
            for i in arguments:
                if i == '-h':
                    header =  arguments[h_index+1].split(':')
                    headers[header[0]] = header[1]
                h_index+=1
         # -o
        o_filepath = ''
        if '-o' in arguments:
            o_index = arguments.index('-o')
            o_filepath = arguments[o_index + 1]


         # -d
        data = ''
        if '-d' in arguments:
            d_index = arguments.index('-d')
            data = arguments[d_index + 1]

        # -f
        file = ''
        if '-f' in arguments:
            f_index = arguments.index('-f')
            file= arguments[f_index + 1]




        httplib.post(url,headers,is_v,o_filepath,file,data)



    def do_multiclient(self,arg):
        num_of_client = int(arg)
        httpc_list=[]
        for i in range(num_of_client):
            temp=httpcobj(i)
            httpc_list.append(temp)

        for j in httpc_list:
            if j.id % 2 == 0:

                thread = threading.Thread(target=handler_get, args=(j,))
                thread.start()
                # thread.join()

            else:

                thread = threading.Thread(target=handler_post, args=(j,))
                thread.start()
                # thread.join()


    def do_exit(self,arg):
         return True

def handler_get(multihttp_obj):
    multihttp_obj.do_get("get -v -h Content-Type:Text/Plain 'http://localhost/test.txt'")

def handler_post(multihttp_obj):
    multihttp_obj.do_post("post -v -d '\"Midterm\":2018-11-03'  'http://localhost/1.txt'")


if __name__ == '__main__':
    Multihttpc().cmdloop()

