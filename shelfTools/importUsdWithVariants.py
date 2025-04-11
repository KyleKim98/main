import os

def search_folders(root_folder):

    stage = hou.node('/stage')

    for enum,entry in enumerate(os.scandir(root_folder)):
        if entry.is_dir():
            path = entry.path
            asset_name = path.split('/')[-1]
            ref_node = stage.createNode('reference::2.0')
            ref_node.setName(asset_name)
            
            ref_node.parm('filepath1').set(path+'/'+asset_name+'.usd')
            ref_node.parm('primpath1').set('/`@sourcename`')
            
            explore_node = stage.createNode('explorevariants')
            explore_node.parm('primpath').set('/prototypes')
            explore_node.parm('variantsetfilter').set('variants')
            explore_node.parm('mode').set(1)
            explore_node.parm('spacing').set(0)
            
            configure_node = stage.createNode('configurelayer')
            configure_node.parm('flattenop').set('stage')
            
            collection_node = stage.createNode('collection::2.0')
            collection_node.parm('collectionname1').set(collection_name)
            snippet = '/prototypes/'+asset_name+'/variants_componentgeometry*'
            collection_node.parm('includepattern1').set(snippet)
            
            explore_node.setInput(0,ref_node)
            configure_node.setInput(0,explore_node)
            collection_node.setInput(0,configure_node)           
    
    stage.layoutChildren()

root_folder = hou.ui.selectFile(title="Select a folder", file_type=hou.fileType.Directory)
collection_name = hou.ui.readInput(message='Collection Name')[1]

search_folders(root_folder)
