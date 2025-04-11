import os,hou,shutil,sys
from KK import utils
from importlib import reload

reload(utils)
mtl_files = []

for node in hou.node('/obj').children():
    if node.type().name() == 'geo':
        for i in node.children():
            if i.type().name() == 'USER::kitbash_converter::1.0':
                kitbash_node = i


old_texture_folder =  utils.correct_path(kitbash_node.parm('tex_path').evalAsString())
save_dir = utils.correct_path(kitbash_node.parm('save_path').evalAsString())
new_texture_folder = save_dir+'textures'

os.mkdir(new_texture_folder)

for i in os.listdir(old_texture_folder):
    if i.split('.')[-1] == 'tx':
        copy_from = old_texture_folder+'/'+i
        copy_to = new_texture_folder+'/'+i
        shutil.copy(copy_from,copy_to)

for i,j,k in os.walk(save_dir):
    for file in k:
        if file == 'mtl.usda':
            mtl_files.append(i+'/'+file)

for mtl_file in mtl_files:
    with open(mtl_file,'r') as file:
        content = file.read()
        refs = utils.extract_usda_references(mtl_file,'filename')
        refs = list(set(refs))
        new_refs = []
        
        for i in refs:
            temp = i.split('/')[-1]
            new_ref = '../textures/'+temp
            content = content.replace(i,new_ref)

    with open(mtl_file,'w') as file:
        file.write(content)