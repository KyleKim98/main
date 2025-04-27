import hou,KK,os,shutil,pathlib
from importlib import reload
from pprint import pprint
from . import treeToArnold

def split(me,item_list):

    pos = me.position()
    geo_node = me.parent()
    null_list = []
    
    for enum,i in enumerate(item_list):

        blast_node = geo_node.createNode('blast')
        blast_node.setPosition(hou.Vector2(pos[0]+(float(enum)*1.5),pos[1]-2.5))
        blast_node.setInput(0,me)
        
        blast_node.parm('group').set('@name='+i)
        blast_node.parm('negate').set(1)
        
        null_node = geo_node.createNode('null')
        null_node.setPosition(hou.Vector2(pos[0]+(float(enum)*1.5),pos[1]-5))
        null_node.setName('OUT_'+i)
        null_node.setInput(0,blast_node)      
        
        null_list.append(null_node)        
        
    return null_list     

def mtl_setup(mat_lib_node,req_mtls,tex_path):    
    print(req_mtls)
    for enum,i in enumerate(req_mtls):        
        mat_builder_node = mat_lib_node.createNode('arnold_materialbuilder')
        mat_builder_node.setName(req_mtls[enum])
        standard_surface = mat_builder_node.createNode('arnold::standard_surface')
        mat_builder_node.node('OUT_material').setInput(0,standard_surface)
        
        KK.treeToArnold.convertMtl(standard_surface,i,tex_path)
        
    mat_lib_node.layoutChildren()    
    
def lop_setup(me,item_list,null_list):

    lopnet = me.parent().createNode('lopnet')
    asset_name = '_'.join(item_list[0].split('_')[:-2])    

    comp_geo_variants_node = lopnet.createNode('componentgeometryvariants')
    comp_geo_variants_node.parm('variantset').set('variants')
    
    comp_out_node = lopnet.createNode('componentoutput')
    comp_out_node.parm('thumbnailmode').set(2)
    comp_out_node.parm('renderer').set('HdArnoldRendererPlugin')
    comp_out_node.parm('autothumbnail').set(0)
    comp_out_node.parm('variantlayers').set(1)
    comp_out_node.setInput(0,comp_geo_variants_node)
    comp_out_node.setName(asset_name)
    
    
    comp_out_node.allowEditingOfContents()
    comp_out_node.parm('lopoutput').set(save_path+'`chs(''name'')`/`chs(''filename'')`')
    comp_out_node.parm('payloadlayer').set('payload.usda')
    comp_out_node.parm('mtllayer').set('mtl.usda')   

    null_node = comp_out_node.node('THUMBNAIL')
    rop_node = comp_out_node.node('thumbnail_render')
    domelight = comp_out_node.createNode('domelight::2.0')
    domelight.setInput(0,null_node)
    rop_node.setInput(0,domelight)

    mat_lib_node = lopnet.createNode('materiallibrary')
    req_mtls = null_list[0].geometry().stringListAttribValue('material_list')
    mtl_setup(mat_lib_node,req_mtls,tex_path)
    mat_lib_node.parm('matpathprefix').set('/ASSET/mtl/')
    
    for enum,i in enumerate(null_list):
        item_name = item_list[enum]
        
        comp_geo_node = lopnet.createNode('componentgeometry')
        comp_geo_inside_node = comp_geo_node.node('sopnet/geo')
        comp_geo_node.parm('partitionattribs').set('shop_materialpath')
        
        comp_mat_node = lopnet.createNode('componentmaterial')       
        
        obj_merge_node = comp_geo_inside_node.createNode('object_merge')
        obj_merge_node.parm('objpath1').set(null_list[enum].path())

        attr_delete_node = comp_geo_inside_node.createNode('attribdelete')
        attr_delete_node.parm('dtldel').set('material_list name_list')
        attr_delete_node.setInput(0,obj_merge_node)
        comp_geo_inside_node.node('default').setInput(0,attr_delete_node)
        shrink_node = comp_geo_inside_node.createNode('shrinkwrap::2.0')
        shrink_node.setInput(0,attr_delete_node)
        comp_geo_inside_node.node('proxy').setInput(0,shrink_node)
        
        comp_geo_inside_node.layoutChildren()
        
        comp_mat_node.setInput(0,comp_geo_node)
        comp_mat_node.setInput(1,mat_lib_node)
        
        comp_mat_node.parm('nummaterials').set(len(req_mtls))
        
        name_list = i.geometry().stringListAttribValue('name_list')
        comp_geo_variants_node.setInput(enum,comp_mat_node)
        
        for enum,i in enumerate(req_mtls):
            primpattern = '/ASSET/geo/render/' + item_name + '/shop_materialpath_' + str(i)
            comp_mat_node.parm('primpattern'+str(enum+1)).set(primpattern)
            comp_mat_node.parm('matspecpath'+str(enum+1)).set('/ASSET/mtl/'+str(i)) 

    os.makedirs(os.path.join(save_path,asset_name))
    thumbnail_copy_path = os.path.join(save_path,asset_name,'thumbnail.png')
    if os.path.isfile(thumbnail_copy_path) == 0 and copy_thumbnail == 1:            
        for i,j,k in os.walk(pathlib.Path(tex_path).parent):
            for file in k:
                if asset_name in file and 'Thumbnail' in i:
                    thumbnail_path = os.path.join(i,file)
                    shutil.copy(thumbnail_path,thumbnail_copy_path)
                    break
                
    if post_render == 1:
        comp_out_node.parm('postrender').set(
            'exec(open("C:/Users/USER/Documents/houdini20.5/python3.11libs/KK/maxtreepostrenderscript.py").read())'
        )
        comp_out_node.parm('lpostrender').set('python')
   
    if at_once:
        comp_out_node.parm('execute').pressButton()
            
    ref_node = lopnet.createNode('reference::2.0')
    ref_node.parm('filepath1').set(comp_out_node.parm('lopoutput').evalAsString())
    ref_node.parm('reload').pressButton()
    explore_node = lopnet.createNode('explorevariants')
    explore_node.parm('variantsetfilter').set('variants')
    explore_node.parm('mode').set(1)
    explore_node.parm('spacing').set(10)
    dome_light_node = lopnet.createNode('domelight::2.0')
    render_node = lopnet.createNode('arnold_rendersettings') 
    
    explore_node.setInput(0,ref_node)
    dome_light_node.setInput(0,explore_node)
    render_node.setInput(0,dome_light_node)  
    render_node.setDisplayFlag(1)
    lopnet.layoutChildren()
    
def main(kwargs): 

    reload(treeToArnold)    
    me = kwargs['node']
    
    global tex_path,save_path,at_once,post_render,copy_thumbnail
    
    # mtl_file = me.parm('fbx_path').evalAsString()
    tex_path = me.parm('tex_path').evalAsString()
    save_path = me.parm('save_path').evalAsString()
    at_once = me.parm('at_once').eval()
    post_render = me.parm('post_render_script').eval()
    copy_thumbnail = me.parm('copy_thumbnail').eval()
    
    items_null = me.node('items')    
    item_list = items_null.geometry().stringListAttribValue('name_list')
    null_list = split(me,item_list)
    lop_setup(me,item_list,null_list)
    hou.hscript(('sopcache -c'))