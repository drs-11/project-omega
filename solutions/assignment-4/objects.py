import gzip
import shutil
import hashlib
import os
import json
import time

class NgcObject:

    BUF_SIZE = 65536
    HASHING_FUNCTION = 'sha1'
    COMPRESSION_METHOD = 'zlib'

    def __init__(self):
        pass

    def compress_obj(self, obj_path, dst):
        with open(obj_path, 'rb') as f_in:
            with gzip.open(dst, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out, self.BUF_SIZE)

    def extract_obj(self, obj_path, dst):
        pass


    def _get_file_hash(self, file_path):
        hashf = hashlib.new(self.HASHING_FUNCTION)

        with open(file_path, "rb") as f_in:
            while True:
                data = f_in.read(self.BUF_SIZE)
                if not data:
                    break
                hashf.update(data)

        return hashf.hexdigest()


    def _get_string_hash(self, string):
        string_stream = io.StringIO(string)

        with string_stream as str_s:
            pass

class Blob(NgcObject):

    def __init__(self):
        pass

    def create(self, file_path, obj_path):
        compressed_filename = self._get_file_hash(file_path)
        header = bytes(self._create_header(os.path.getsize(file_path)), 'ascii')

        with open(file_path, 'rb') as f_in:
            with gzip.open(os.path.join(obj_path, compressed_filename), "wb") as f_out:
                f_out.write(header)
                shutil.copyfileobj(f_in, f_out, self.BUF_SIZE)

        return compressed_filename

    def read_header(self, file_path):
        header = b''

        with open(file_path, "rb") as blob_obj:
            while b"\x00" not in header:
                header = blob_obj.read(1)
        return header.decode()

    def get_content_chunk(self, file_path, fptr):

        with open(file_path, "rb") as blob_obj:
            blob_obj.seek(fptr)
            data_chunk = blob_obj.read(self.BUF_SIZE)

        return data_chunk

    def _get_file_hash(self, file_path):
        #print("AM I NOT BEING REDIRECTED HERE?")
        compressed_filename = None
        hashf = hashlib.new(self.HASHING_FUNCTION)
        header = self._create_header(os.path.getsize(file_path))

        hashf.update(bytes(header, 'ascii'))

        with open(file_path, "rb") as f_in:
            while True:
                #print("OKAY WHAT ABOUT HERE?")
                data = f_in.read(self.BUF_SIZE)
                #print("WE GOT DATA BITCHES:", data)
                if not data:
                    break
                hashf.update(data)
                #print("UPDATED HASH: %s" % (hashf.hexdigest()))

        compressed_filename = hashf.hexdigest()
        return compressed_filename

    def _create_header(self, content_length):
        return f"blob {content_length}\x00"

class Tree(NgcObject):

    FILES = 'files'
    SUBDIRS = 'subdirs'

    def __init__(self, logger, path=os.getcwd()):
        self.path = path
        self.obj_path = os.path.join(self.path, '.ngc/objects')
        if not os.path.exists(self.obj_path): os.makedirs(self.obj_path)
        self.logger = logger
        self.root = None
        self.blob = Blob()

    def create(self, path=None):
        if not path: path = self.path
        tree_obj = dict()
        files = dict()
        subdirs = dict()

        for item in os.listdir(path):
            self.logger.info("location traversing-%s" % (path))
            self.logger.debug("item - %s" % (item))
            item_path = os.path.join(path, item)
            self.logger.debug("item path: %s" % (item_path))

            if item.startswith("."):
                continue

            if os.path.isfile(item_path):
                file_hash = self.blob._get_file_hash(item_path)
                #self.logger.debug("hash: %s" % (file_hash))
                if not os.path.exists(os.path.join(self.obj_path, file_hash)):
                    file_hash = self.blob.create(item_path, self.obj_path)
                    self.logger.debug("%s blob created" % (item))
                files[item] = file_hash
                self.logger.info("%s done" % (item))

            elif os.path.isdir(item_path):

                subdir_hash = self.create(item_path)
                subdirs[item] = subdir_hash
                self.logger.info("%s dir done" % (item))
            else:
                pass #handle error here

        tree_obj[self.FILES] = files
        tree_obj[self.SUBDIRS] = subdirs
        tree_json = json.dumps(tree_obj)
        tree_json_bytes = tree_json.encode()

        hashf = hashlib.new(self.HASHING_FUNCTION)
        hashf.update(tree_json_bytes)
        hashed_value = hashf.hexdigest()
        tree_obj_path = os.path.join(self.obj_path, hashed_value)

        with open(tree_obj_path, 'wb') as tree_file:
            tree_file.write(tree_json_bytes)

        return hashed_value

    def read(self, file_path):

        with open(file_path, 'rb') as tree_file:
            tree_data = tree_file.read().decode()

        return json.loads(tree_data)

    def readline(self, file_path):
        pass


class Commit(NgcObject):

    TREE = "tree"
    PARENT = "parent"
    AUTHOR = 'author'
    COMMITTER = 'committer'
    MSG = 'message'

    def __init__(self, path=os.getcwd()):
        self.path = path
        self.obj_path = os.path.join(path, ".ngc/objects")

    def create(self, tree_hash, author_details, committer_details, message, parent_hash=None):
        commit_obj = dict()
        #if not committcommitter_details = dict()
        time_stamp = time.time()

        commit_obj[self.TREE] = tree_hash
        commit_obj[self.AUTHOR] = author_details
        commit_obj[self.COMMITTER] = committer_details
        commit_obj[self.MSG] = message
        if parent_hash:
            commit_obj[self.PARENT] = parent_hash

        commit_json = json.dumps(commit_obj)
        commit_json_bytes = commit_json.encode()

        hashf = hashlib.new(self.HASHING_FUNCTION)
        hashf.update(commit_json_bytes)
        hashed_value = hashf.hexdigest()
        commit_obj_path = os.path.join(self.obj_path, hashed_value)

        with open(commit_obj_path, 'wb') as tree_file:
            tree_file.write(commit_json_bytes)

        return hashed_value

    def read(self, commit_hash):
        pass

    def print_commit_data(self, commit_hash):
        commit_path = os.path.join(self.obj_path, commit_hash)

        with open(commit_path, 'rb') as commit_file:
            commit_json = json.load(commit_file)

        print(self.TREE, commit_json[self.TREE])
        if self.PARENT in commit_json: print(self.PARENT, commit_json[self.PARENT])
        print(self.AUTHOR, commit_json[self.AUTHOR])
        print(self.COMMITTER, commit_json[self.COMMITTER])
        print('\n', commit_json[self.MSG])
