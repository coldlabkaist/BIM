import os

class CoordofNode():
    def __init__(self, frames):
        self.x = [None]*(int(frames)+1)
        self.y = [None]*(int(frames)+1)
        self.x_smoothing = [None]*(int(frames)+1)
        self.y_smoothing = [None]*(int(frames)+1)
        self.x_proofread = [None]*(int(frames)+1)
        self.y_proofread = [None]*(int(frames)+1)

    def add_coord(self, frame, coord):
        #print(len(self.x), frame)
        if coord[0] == '':
            return
        self.x[int(frame)] = float(coord[0])
        self.y[int(frame)] = float(coord[1])
        self.x_proofread[int(frame)] = float(coord[0])
        self.y_proofread[int(frame)] = float(coord[1])
        #print(self.x[:20])

class NodeofInstance():
    def __init__(self):
        self.node = []
        self.node_data = []

    def detect_nodes(self, nodes, frames):
        self.node = nodes
        self.node_data = [CoordofNode(frames) for i in range(len(nodes))]

    def find_node_data(self, node):
        ind = self.node.index(node)
        return self.node_data[ind]

class InstanceofFile():
    def __init__(self):
        self.instance = []
        self.instance_data = []
        self.instnace_z = []
        self.data = None
        self.Nframe = 0

    def detect_instance(self, file_lines, nodes):
        for lines in file_lines[1:]:
            if not lines[0] in self.instance:
                self.instance.append(lines[0])
                node_info = NodeofInstance()
                self.instance_data.append(node_info)
                node_info.detect_nodes(nodes, self.Nframe)    
    
    def detect_Nframe(self, file_lines):
        lines = file_lines[-1]
        self.Nframe = int(lines[1])

    def find_instance_data(self, instance):
        ind = self.instance.index(instance)
        return self.instance_data[ind]
    
    def find_instance_z(self, instance):
        ind = self.instance.index(instance)
        return self.instance_z[ind]
    
    #def assign_data(self):
    #    pass

class FileInfo():
    def __init__(self, dir_inf, inf_list):
        self.dir_inf = dir_inf
        self.inf_list = inf_list
        self.full_file_lines = [None for i in range(len(self.inf_list))]
        self.file_data = []
        self.node_list = []
        self.num_nodes = 0
        self.smoothing = "savitzkygolay"

    def read_file(self):
        for i in range(len(self.inf_list)):
            file_name = self.inf_list[i]
            # open each files
            full_file_dir = self.dir_inf+'/'+file_name
            with open(full_file_dir, mode='r', newline='', encoding='utf-8') as f:
                # load csv file
                file_lines = f.readlines()
            # split lines
            for l in range(len(file_lines)):
                file_lines[l] = file_lines[l].split(',')
            self.full_file_lines[i] = file_lines
            
            # load node information
            if len(self.node_list) == 0:
                self.load_node()

    def load_node(self):
        first_list = self.full_file_lines[0][0][3:]
        node_list = []
        for i in range(int(len(first_list)/3)):
            node_list.append(first_list[3*i][:-2])
        self.node_list = node_list
        self.num_nodes = len(node_list)

def load_file(dir_inf, list_inf):
    file = FileInfo(dir_inf, list_inf)
    file.read_file()
    # load files into class
    nodes = file.node_list
    for i in range(len(file.inf_list)):
        file_name = file.inf_list[i]
        instance_info = InstanceofFile()
        instance_info.detect_Nframe(file.full_file_lines[i])
        instance_info.detect_instance(file.full_file_lines[i], file.node_list)

        file.file_data.append(instance_info)
        
        # make whole structure of data
        for line in file.full_file_lines[i][1:]:
            instance = line[0]
            frame = line[1]
            node_info = instance_info.find_instance_data(instance)
            for i in range(len(nodes)):
                coord = node_info.find_node_data(nodes[i])
                coord.add_coord(frame, line[3+i*3:5+i*3])

    return file
    #print(file.file_data[0].instance_data[0].node_data[0].x[:5])
    