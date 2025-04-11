import hou
geo_node = hou.selectedNodes()[0]
kit_name = geo_node.name()
geo_node.node('merge1').destroy()
merge_node = geo_node.createNode('merge')

fbx_path = hou.ui.selectFile(title='FBX Path: ',file_type=hou.fileType.Directory)


file_nodes = []

for enum,i in enumerate(geo_node.children()):
    if i.type().name() == 'file':
        file_nodes.append(i)
        asset_name = i.parm('file').evalAsString().split('/')[-1]
        i.parm('file').set(fbx_path+'/'+asset_name)
    elif i.type().name() == 'attribwrangle':
        i.destroy()
    elif i.type().name() == 'xform':
        merge_node.setInput(enum,i)

for enum,i in enumerate(file_nodes):
    transform_node = i.outputs()[0]
    file_name = '_'.join(i.name().split('_')[1:])
    
    primwrangle = geo_node.createNode('attribwrangle')
    primwrangle.parm('class').set('primitive')
    
    file_name = '_'.join(i.name().split('_')[1:])
    primwrangle.parm('snippet').set(f"s@name='{file_name}/+{file_name}';\ns@shop_materialpath=split(s@shop_materialpath,'/')[-1];")
    
    primwrangle.setInput(0,transform_node)
    
    merge_node.setInput(enum,primwrangle)
    
geo_node.layoutChildren()