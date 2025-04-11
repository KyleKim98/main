import os,hou
from KK import kitbashToArnold,utils
from importlib import reload

print('kitbashToArnold imported')

def convertMtl(standard_surface,req_mtl,tex_path,displacement=False):
	
	mat_dict = utils.findFiles((req_mtl,'tx'),tex_path,True)
	if displacement==False:
		key = req_mtl+'_tx'
		if 'height' in mat_dict[key]:
			mat_dict[req_mtl].remove('height')			

		elif 'displacement' in mat_dict[key]:
			mat_dict[req_mtl].remove('height')
			
	utils.buildArnoldShader(standard_surface,mat_dict,tex_path)
	

	standard_surface.parent().layoutChildren()
def split(me,item_list):

    pos = me.position()
    geo_node = me.parent()
    null_list = []    
    
    
    for enum,i in enumerate(item_list):

        blast_node = geo_node.createNode('blast')
        blast_node.setPosition(hou.Vector2(pos[0]+(float(enum)*1.5),pos[1]-2.5))
        blast_node.setInput(0,me)
        
        blast_node.parm('group').set('@item='+i)
        blast_node.parm('negate').set(1)
        
        wrangle_node = geo_node.createNode('attribwrangle')
        wrangle_node.parm('class').set('detail')
        wrangle_node.parm('snippet').set('s[]@material_list = uniquevals(0, "prim" ,"shop_materialpath");')
        wrangle_node.setInput(0,blast_node)
        wrangle_node.setPosition(hou.Vector2(pos[0]+(float(enum)*1.5),pos[1]-5))
        
        promoteB_node = geo_node.createNode('attribpromote')
        promoteB_node.setPosition(hou.Vector2(pos[0]+(float(enum)*1.5),pos[1]-7.5))
        promoteB_node.parm('inname').set('item')
        promoteB_node.parm('inclass').set(1)
        promoteB_node.parm('outclass').set(0)
        promoteB_node.setInput(0,wrangle_node)      

        null_node = geo_node.createNode('null')
        null_node.setPosition(hou.Vector2(pos[0]+(float(enum)*1.5),pos[1]-10))
        null_node.setName('OUT_'+i)
        null_node.setInput(0,promoteB_node)      
        
        null_list.append(null_node)    
        
    return null_list     

def parse_mtl(mtl_file):

    materials = {}
    current_material = None

    with open(mtl_file, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            keyword = parts[0]
            values = parts[1:]

            if keyword == 'newmtl':
                current_material = values[0]
                materials[current_material] = {}
            elif current_material is not None:
                materials[current_material][keyword] = values

    return materials

def mtl_setup(mat_lib_node,req_mtls,tex_path):    

    for enum,i in enumerate(req_mtls):
    
        mat_builder_node = mat_lib_node.createNode('arnold_materialbuilder')
        mat_builder_node.setName(req_mtls[enum])
        standard_surface = mat_builder_node.createNode('arnold::standard_surface')
        mat_builder_node.node('OUT_material').setInput(0,standard_surface)

        kitbashToArnold.convertMtl(standard_surface,i,tex_path)
        
        if 'Glass' in str(i):
            standard_surface.parm('transmission').set(0.95)
    
    mat_lib_node.layoutChildren()    
    
def lop_setup(me,item_list,null_list):
        
    lopnet = me.parent().createNode('lopnet')
    output_list = []
    ropnet = lopnet.createNode('ropnet')
    rop_merge_node = ropnet.createNode('merge')
    
    for enum,i in enumerate(null_list):
            
        item_name = i.geometry().stringAttribValue('item')
        
        comp_geo_node = lopnet.createNode('componentgeometry')
        comp_geo_node.parm('partitionattribs').set('shop_materialpath')
        comp_geo_inside_node = comp_geo_node.node('sopnet/geo')
        mat_lib_node = lopnet.createNode('materiallibrary')
        comp_mat_node = lopnet.createNode('componentmaterial')
        comp_out_node = lopnet.createNode('componentoutput')
        
        comp_out_node.setName(item_name)   
        comp_out_node.parm('thumbnailmode').set(2)
        comp_out_node.parm('renderer').set('HdArnoldRendererPlugin')
        comp_out_node.parm('autothumbnail').set(1)
        
        obj_merge_node = comp_geo_inside_node.createNode('object_merge')
        obj_merge_node.parm('objpath1').set(null_list[enum].path())
        attr_delete_node = comp_geo_inside_node.createNode('attribdelete')
        attr_delete_node.parm('dtldel').set('all_material_list item item_list material_list path tempname')
        attr_delete_node.parm('vtxdel').set('*Map*')
        attr_delete_node.setInput(0,obj_merge_node)
        
        comp_geo_inside_node.node('default').setInput(0,attr_delete_node)
        bound_node = comp_geo_inside_node.createNode('bound')
        bound_node.setInput(0,obj_merge_node)
        comp_geo_inside_node.node('proxy').setInput(0,bound_node)
        
        comp_geo_inside_node.layoutChildren()
        
        comp_mat_node.setInput(0,comp_geo_node)
        comp_mat_node.setInput(1,mat_lib_node)
        comp_out_node.setInput(0,comp_mat_node)
        
        req_mtls = null_list[enum].geometry().stringListAttribValue('material_list')
        mtl_setup(mat_lib_node,req_mtls,tex_path)
        
        comp_mat_node.parm('nummaterials').set(len(req_mtls))
        mat_lib_node.parm('matpathprefix').set('/ASSET/mtl/')
        
        comp_out_node.allowEditingOfContents()
        comp_out_node.parm('lopoutput').set(save_path+'`chs(''name'')`/`chs(''filename'')`')
        comp_out_node.parm('payloadlayer').set('payload.usda')
        comp_out_node.parm('mtllayer').set('mtl.usda')
        comp_out_node.parm('localize').set(False)
        
        null_node = comp_out_node.node('THUMBNAIL')
        rop_node = comp_out_node.node('thumbnail_render')
        domelight = comp_out_node.createNode('domelight::2.0')
        domelight.setInput(0,null_node)
        rop_node.setInput(0,domelight)
        output_list.append(comp_out_node)
        
        fetch_node = ropnet.createNode('fetch')
        fetch_node.setName(i.name())
        fetch_node.parm('source').set(comp_out_node.node('rop').path())
        rop_merge_node.setInput(enum,fetch_node)
        
        
        if enum == len(null_list)-1 and render_script == 1:
            comp_out_node.parm('postrender').set('exec(open("C:/Users/USER/Documents/houdini20.5/python3.11libs/KK/postrenderscript.py").read())')
            comp_out_node.parm('lpostrender').set('python')
        
        for enum,i in enumerate(req_mtls):
        
            prim_pattern = '/ASSET/geo/render/' + item_name + '/shop_materialpath_' + str(i)
                    
            comp_mat_node.parm('primpattern'+str(enum+1)).set(prim_pattern)
            comp_mat_node.parm('matspecpath'+str(enum+1)).set('/ASSET/mtl/'+str(i)) 
    
    switch_node = lopnet.createNode('switch')
    domelight_node = lopnet.createNode('domelight::2.0')
    
    for enum,i in enumerate(output_list):
        switch_node.setInput(enum,i)
    
    domelight_node.setInput(0,switch_node)
    domelight_node.setDisplayFlag(1)
    
    lopnet.layoutChildren()
    ropnet.layoutChildren()

def main(kwargs): 

    # reload(kitbashToArnold)
    # reload(utils)
    
    me = kwargs['node']    
    
    global mtl_file,tex_path,save_path,use_mtl,single_mode,single_mode_index,render_script,export_usd
    
    mtl_file = me.parm('mtl_file').evalAsString()
    tex_path = me.parm('tex_path').evalAsString()
    save_path = me.parm('save_path').evalAsString()
    save_path = utils.tailSlash(save_path)
    use_mtl = me.parm('use_mtl').eval()
    single_mode = me.parm('single_mode').eval()
    single_mode_index = me.parm('index').eval()
    render_script = me.parm('postrenderscript').eval()
    export_usd = me.parm('export_usd').eval()
    
    items_null = me.node('items')    
    item_list = items_null.geometry().stringListAttribValue('item_list')
    
    if single_mode:
        item_list = [item_list[single_mode_index]]
        
    null_list = split(me,item_list)    
    lop_setup(me,item_list,null_list)
    
    if export_usd == 1:
        me.parent().node('lopnet1').node('ropnet1').parm('execute').pressButton()