from scipy.signal import savgol_filter
from scipy.stats import zscore
import numpy as np
import matplotlib.pyplot as plt


def smoothing(inf_file, args_main):
    smoothing_type = args_main.smoothing_type
    if smoothing_type not in ["none", "savitzkygolay"]:
        raise Exception("Smoothing Type Name Error")
    show_graph = [args_main.show_smooth, args_main.show_norm]
    for file_data in inf_file.file_data:
        for instance_data in file_data.instance_data:
            for node_data in instance_data.node_data:
                if smoothing_type == "none":
                    smoothing_none(node_data)
                elif smoothing_type == "savitzkygolay":
                    window_length = args_main.window_length
                    polyorder = args_main.polyorder
                    smoothing_savitzkygolay(node_data, window_length, polyorder, show_graph)

    #print(node_data.x[400:440])
    #print(node_data.x_smoothing[400:440])
    if args_main.show_proofread_alert:
        smoothing_proofread(inf_file, args_main.z_criteria, show_graph)

def smoothing_none(node_data):
    node_data.x_smoothing = node_data.x
    node_data.y_smoothing = node_data.y

def smoothing_savitzkygolay(node_data, window_length, polyorder, show_graph):
    x_data = np.array(node_data.x, dtype=np.float64)
    y_data = np.array(node_data.y, dtype=np.float64)

    # Identify the indices of None values
    x_nans = np.isnan(x_data)
    x_indices = np.arange(len(x_data))
    y_nans = np.isnan(y_data)
    y_indices = np.arange(len(y_data))
    
    # Interpolate to fill None values
    x_data[x_nans] = np.interp(x_indices[x_nans], x_indices[~x_nans], x_data[~x_nans])
    y_data[y_nans] = np.interp(y_indices[y_nans], y_indices[~y_nans], y_data[~y_nans])

    node_data.x_smoothing = savgol_filter(x_data, window_length, polyorder, deriv=0, delta=1.0, axis=-1, mode='nearest', cval=0.0)
    node_data.y_smoothing = savgol_filter(y_data, window_length, polyorder, deriv=0, delta=1.0, axis=-1, mode='nearest', cval=0.0)
    
    if show_graph[0] != 0:
        plt.plot(x_indices, x_data, label='Original Data (interpolated)')
        plt.plot(x_indices, node_data.x_smoothing, label='Smoothed Data')
        plt.scatter(x_indices[x_nans], node_data.x_smoothing[x_nans], color='red', label='Estimated Nones')
        plt.legend()
        plt.show()
        show_graph[0] -=1

def smoothing_proofread(inf_file, z_criteria, show_graph):
    for file_data in inf_file.file_data:
        norm_list_file = []
        for instance_data in file_data.instance_data:
            norm_list_instance = []
            for frame in range(file_data.Nframe+1):
                # detect node norm
                norm = None
                coords_of_frame = []
                for node_data in instance_data.node_data:
                    coord = [None, None]
                    coord[0] = node_data.x_smoothing[frame]
                    coord[1] = node_data.y_smoothing[frame]
                    coords_of_frame.append(coord)
                norm = criteria_basic(coords_of_frame)
                norm_list_instance.append(norm)
            norm_list_file.append(norm_list_instance)

        if show_graph[1] != 0:
            plt.plot(norm_list_instance, label='norm change')
            plt.legend()
            plt.show()
            show_graph[1] -=1

        # calculate Zscore
        numframe = file_data.Nframe+1
        numinstance = len(file_data.instance)
        z = zscore(sum(norm_list_file, []), ddof=0, nan_policy='omit')
        z = [z[numframe*i:numframe*(i+1)] for i in range(numinstance)]
        file_data.instance_z = z

def criteria_basic(coords_of_frame):
    # calculate simple L2 norm without considering tail
    norm = 0
    for i in range(len(coords_of_frame)-1):
        for j in range(i):
            coord1 = coords_of_frame[i]
            coord2 = coords_of_frame[j]
            #print((coord1[0]-coord2[0])**2 + (coord1[1]-coord2[1])**2)
            #print(coord1[0], coord2[0], coord1[1], coord2[1])
            if coord1[0] == None or coord2[1] == None:
                return np.nan
            norm += (coord1[0]-coord2[0])**2 + (coord1[1]-coord2[1])**2
    #print(norm)
    return norm