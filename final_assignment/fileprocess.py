import os
import fcntl
import json
import threading

global lock
lock = threading.Lock()

def Get_file_list(dir_path, content_type):
    respond_dictionary = {}
    respond_dictionary['Directory'] = dir_path
    respond_dictionary['File_list_name'] = file_name_list(dir_path)
    status_num = 200
    respond_message = resp_content_type(respond_dictionary,content_type)
    return respond_message, status_num, content_type

def Get_file_content(dir_path, url, content_type):
    respond_dictionary = {}
    url_list = url.split('/')
    if url.find('../') != -1:
        # GET /../path
        status_num = 400
        respond_dictionary['Error'] = 400
        respond_dictionary['Message'] ='Bad Request.'
        respond_dictionary['Notice'] = 'Please enter correct url.'
        respond_message = resp_content_type(respond_dictionary,content_type)
        return respond_message, status_num, content_type
    else:
        file_list = file_name_list(dir_path)
        if url_list[-1] not in file_list:
            status_num = 404
            respond_dictionary['Error'] = 404
            respond_dictionary['Message'] ='Not Found.'
            respond_dictionary['Notice'] = 'Please enter the filename that exists.'
            respond_message = resp_content_type(respond_dictionary,content_type)
            return respond_message, status_num, content_type
        else:
            lock.acquire()
            respond_message = ''
            try:
                with open(dir_path + url, 'rb') as file_obj:

                    file_content = file_obj.read().rstrip()

            finally:
                lock.release()
            status_num = 200
            respond_message = respond_message + str(file_content)


            content_type = get_file_content_type(url_list[-1])
        return respond_message, status_num, content_type


def Post_file(dir_path, url, content_type, file_content):
    respond_dictionary = {}
    url_list = url.split('/')
    if url.find('../') != -1:
        status_num = 400
        respond_dictionary['Error'] = 400
        respond_dictionary['Message'] ='Bad Request.'
        respond_dictionary['Notice'] = 'Please enter correct url.'
        respond_message = resp_content_type(respond_dictionary,content_type)
        return respond_message, status_num
    else:
        lock.acquire()
        try:
            with open(dir_path + url, 'w') as file_obj:

                file_obj.writelines(file_content)

        finally:
            lock.release()
        respond_dictionary['write in file'] = str(url_list[-1])
        respond_dictionary['File path'] = str(dir_path + '/' + url_list[-1])
        respond_message = resp_content_type(respond_dictionary,content_type)
        status_num = 200
        return respond_message,status_num, content_type

def file_name_list (path):
    message = []
    for maindir, subdir, file_name_list in os.walk(path):
            for filename in file_name_list:
                apath = os.path.join(maindir,filename).split('/')
                apath = apath[-1]
                message.append(apath)
    return message

def resp_content_type (respond_message, content_type):
    content_type = content_type[content_type.find('/')+1:]
    content_type = content_type.lower()
    if content_type == 'json':
        respond_message = json.dumps(respond_message)
    elif content_type == 'plain':
        respond_message = str(respond_message)
    return respond_message

def get_file_content_type(filename):
    content_type = ''
    suffix = os.path.splitext(filename)[-1][1:]
    if suffix == 'json':
        content_type = 'Application/Json'
    elif suffix == 'html':
        content_type = 'Text/HTML'
    elif suffix == 'xml':
        content_type = 'Text/XML'
    else:content_type = 'Text/Plain'
    return content_type
