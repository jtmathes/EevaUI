
import sys
import os
import csv
import subprocess
        
def write_to_csv(filepath, column_names, data):
    
    with open(filepath, 'wb') as outfile:
        writer = csv.writer(outfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(column_names)
        writer.writerows(data) 
        
'''
def write_to_matlab_data_file(filepath, column_names, data):
    
    try:
        import scipy.io
        import numpy as np
        data = np.array(data)
        scipy.io.savemat(filepath, mdict={'d': data})
        return True
    except ImportError:
        return False
'''
        
def write_to_matlab_script_file(filepath, column_names, data):
    
    with open(filepath, 'w') as outfile:
        outfile.write('% {}\n'.format(" ".join(column_names)))
        outfile.write('d = ...\n')
        outfile.write('[' + "\n ".join(" ".join("%g" % val for val in line) for line in data) + '];')

def open_output_directory_in_viewer(out_directory, controller=None):
    
    if sys.platform == 'win32':
        os.startfile(out_directory)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', out_directory])
    else:
        try:
            subprocess.Popen(['xdg-open', out_directory])
        except OSError:
            if controller:
                controller.display_message("OS not supported.")

def make_filepath_unique(path):
    
    _, fname = os.path.split(path)
    just_fname, ext = os.path.splitext(fname)[1]
    
    i = 1 # number to append_to file name
    while os.path.exists(path):

        new_fname = '{}_{}{}'.format(just_fname, i, ext)
        path = os.path.join(dir, new_fname)
        i += 1
        
    return path

def make_filename_unique(directory, fname_no_ext):
    
    original_fname = fname_no_ext
    dir_contents = os.listdir(directory)
    dir_fnames = [os.path.splitext(c)[0] for c in dir_contents]
    
    while fname_no_ext in dir_fnames:
        
        try:
            v = fname_no_ext.split('_')
            i = int(v[-1])
            i += 1
            fname_no_ext = '_'.join(v[:-1] + [str(i)])
        except ValueError:
            fname_no_ext = '{}_{}'.format(original_fname, 1)

    return fname_no_ext