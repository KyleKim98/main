import os,shutil,sys,hou
from KK import utils
from importlib import reload

reload(utils)
hou.hipFile.save()

hip_name = hou.getenv('HIPNAME')
hip_file = hou.getenv('HIPFILE')
mtl_files = []

for node in hou.node('/obj').children():
    if node.type().name() == 'geo':
        for i in node.children():
            if i.type().name() == 'USER::maxtreeconverter::1.0':
                maxtree_node = i


old_texture_folder =  utils.correctPath(maxtree_node.parm('tex_path').evalAsString())
save_dir = utils.correctPath(maxtree_node.parm('save_path').evalAsString())

trees_library = utils.correctPath(r'E:\MyLibrary\Trees')
original_library = trees_library+'Originals/'
download_dir = utils.correctPath(r'C:\Users\USER\Downloads')

shutil.move(save_dir,trees_library+hip_name+'/Arnold/')
shutil.move(hip_file,original_library)

for i in os.listdir(download_dir):
    if i == hip_name:       
        shutil.move(download_dir+i,original_library)

# shutil.rmtree(save_dir)
# shutil.rmtree(download_dir+i)