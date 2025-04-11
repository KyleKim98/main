import os
from KK import utils
from importlib import reload
reload(utils)

def search_folders(root_folder):

    stage = hou.node('/stage')
    merge_node = stage.createNode('switch')
    
    for enum,entry in enumerate(os.scandir(root_folder)):
        if entry.is_dir():
            path = entry.path
            asset_name = path.split('/')[-1]
            ref_node = stage.createNode('reference::2.0')
            ref_node.setName(asset_name)
            
            ref_node.parm('filepath1').set(path+'/'+asset_name+'.usd')
            ref_node.parm('primpath1').set('/`@sourcename`')
            merge_node.setInput(enum,ref_node)
    
    stage.layoutChildren()
    

root_folder = hou.ui.selectFile(title="Select a folder", file_type=hou.fileType.Directory)
root_folder = utils.correct_path(root_folder)
search_folders(root_folder)
