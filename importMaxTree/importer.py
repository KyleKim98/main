import hou,os

def loadfbx(dirs):
    paths = []
    for i in dirs:
        path = str(i.replace('\\','/'))
        paths.append(path+'/')

    FBX_path = paths[0]
    tex_path = paths[1]
    save_path = paths[2]

    obj = hou.node('/obj')

    FBXs = []

    for i in os.listdir(FBX_path):
       FBXs.append(i)

    for i in FBXs:

       file_name = i.split('.')[0]
       file_path = FBX_path+'/'+i
       extension = i.split('.')[-1]

       if extension == 'fbx':
           geo_node = obj.createNode('geo')
           geo_node.setName(file_name)
           geo_node.setDisplayFlag(0)
           file_node = geo_node.createNode('file')  
           file_node.parm('file').set(file_path)
           convert_node = geo_node.createNode('USER::maxtreeconverter::1.0')
           convert_node.parm('fbx_path').set(i)
           convert_node.parm('tex_path').set(tex_path)
           convert_node.parm('save_path').set(save_path)    
           convert_node.setInput(0,file_node)

       geo_node.layoutChildren()

    obj.layoutChildren()


