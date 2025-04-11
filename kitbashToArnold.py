import os, hou
from KK import kitbashToArnold, utils
from importlib import reload
#commit and pull test
print('kitbashToArnold imported')

def convertMtl(standard_surface, req_mtl, tex_path, displacement=False):
    mat_dict = utils.findFiles((req_mtl, 'tx'), tex_path, True)
    key = req_mtl + '_tx'

    if not displacement:
        if 'height' in mat_dict.get(key, []):
            mat_dict[req_mtl].remove('height')
        elif 'displacement' in mat_dict.get(key, []):
            mat_dict[req_mtl].remove('height')

    utils.buildArnoldShader(standard_surface, mat_dict, tex_path)
    standard_surface.parent().layoutChildren()

def split(me, item_list):
    pos = me.position()
    geo_node = me.parent()
    null_list = []

    for enum, item in enumerate(item_list):
        offset = hou.Vector2(pos[0] + enum * 1.5, pos[1])

        blast = geo_node.createNode('blast', node_name=f"blast_{item}")
        blast.setPosition(offset - hou.Vector2(0, 2.5))
        blast.setInput(0, me)
        blast.parm('group').set(f'@item={item}')
        blast.parm('negate').set(1)

        wrangle = geo_node.createNode('attribwrangle', node_name=f"wrangle_{item}")
        wrangle.setPosition(offset - hou.Vector2(0, 5))
        wrangle.setInput(0, blast)
        wrangle.parm('class').set(2)  # detail
        wrangle.parm('snippet').set('s[]@material_list = uniquevals(0, "prim", "shop_materialpath");')

        promote = geo_node.createNode('attribpromote', node_name=f"promote_{item}")
        promote.setPosition(offset - hou.Vector2(0, 7.5))
        promote.setInput(0, wrangle)
        promote.parm('inname').set('item')
        promote.parm('inclass').set(1)
        promote.parm('outclass').set(0)

        null = geo_node.createNode('null', node_name=f'OUT_{item}')
        null.setPosition(offset - hou.Vector2(0, 10))
        null.setInput(0, promote)
        null_list.append(null)

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
            keyword, *values = parts

            if keyword == 'newmtl':
                current_material = values[0]
                materials[current_material] = {}
            elif current_material:
                materials[current_material][keyword] = values

    return materials

def mtl_setup(mat_lib_node, req_mtls, tex_path):
    for mtl in req_mtls:
        mat_builder = mat_lib_node.createNode('arnold_materialbuilder', node_name=mtl)
        surface = mat_builder.createNode('arnold::standard_surface')
        mat_builder.node('OUT_material').setInput(0, surface)

        kitbashToArnold.convertMtl(surface, mtl, tex_path)

        if 'Glass' in mtl:
            surface.parm('transmission').set(0.95)

    mat_lib_node.layoutChildren()

def lop_setup(me, item_list, null_list):
    lopnet = me.parent().createNode('lopnet')
    ropnet = lopnet.createNode('ropnet')
    rop_merge = ropnet.createNode('merge')
    output_list = []

    for enum, null_node in enumerate(null_list):
        item_name = null_node.geometry().stringAttribValue('item')
        req_mtls = null_node.geometry().stringListAttribValue('material_list')

        comp_geo = lopnet.createNode('componentgeometry')
        comp_geo.parm('partitionattribs').set('shop_materialpath')
        geo_inside = comp_geo.node('sopnet/geo')

        obj_merge = geo_inside.createNode('object_merge')
        obj_merge.parm('objpath1').set(null_node.path())

        attr_del = geo_inside.createNode('attribdelete')
        attr_del.setInput(0, obj_merge)
        attr_del.parm('dtldel').set('all_material_list item item_list material_list path tempname')
        attr_del.parm('vtxdel').set('*Map*')

        geo_inside.node('default').setInput(0, attr_del)
        bound = geo_inside.createNode('bound')
        bound.setInput(0, obj_merge)
        geo_inside.node('proxy').setInput(0, bound)
        geo_inside.layoutChildren()

        mat_lib = lopnet.createNode('materiallibrary')
        mtl_setup(mat_lib, req_mtls, tex_path)

        comp_mat = lopnet.createNode('componentmaterial')
        comp_mat.setInput(0, comp_geo)
        comp_mat.setInput(1, mat_lib)
        comp_mat.parm('nummaterials').set(len(req_mtls))
        mat_lib.parm('matpathprefix').set('/ASSET/mtl/')

        for idx, mtl in enumerate(req_mtls):
            comp_mat.parm(f'primpattern{idx+1}').set(f'/ASSET/geo/render/{item_name}/shop_materialpath_{mtl}')
            comp_mat.parm(f'matspecpath{idx+1}').set(f'/ASSET/mtl/{mtl}')

        comp_out = lopnet.createNode('componentoutput', node_name=item_name)
        comp_out.setInput(0, comp_mat)
        comp_out.allowEditingOfContents()
        comp_out.parm('thumbnailmode').set(2)
        comp_out.parm('renderer').set('HdArnoldRendererPlugin')
        comp_out.parm('autothumbnail').set(1)
        comp_out.parm('lopoutput').set(save_path + "`chs('name')`/`chs('filename')`")
        comp_out.parm('payloadlayer').set('payload.usda')
        comp_out.parm('mtllayer').set('mtl.usda')
        comp_out.parm('localize').set(False)

        domelight = comp_out.createNode('domelight::2.0')
        domelight.setInput(0, comp_out.node('THUMBNAIL'))
        comp_out.node('thumbnail_render').setInput(0, domelight)
        output_list.append(comp_out)

        fetch = ropnet.createNode('fetch', node_name=null_node.name())
        fetch.parm('source').set(comp_out.node('rop').path())
        rop_merge.setInput(enum, fetch)

        if enum == len(null_list) - 1 and render_script == 1:
            comp_out.parm('postrender').set(
                'exec(open("C:/Users/USER/Documents/houdini20.5/python3.11libs/KK/postrenderscript.py").read())'
            )
            comp_out.parm('lpostrender').set('python')

    switch = lopnet.createNode('switch')
    dome = lopnet.createNode('domelight::2.0')
    for i, node in enumerate(output_list):
        switch.setInput(i, node)

    dome.setInput(0, switch)
    dome.setDisplayFlag(True)

    lopnet.layoutChildren()
    ropnet.layoutChildren()

def main(kwargs):
    global mtl_file, tex_path, save_path, use_mtl
    global single_mode, single_mode_index, render_script, export_usd

    me = kwargs['node']

    # reload(kitbashToArnold)
    # reload(utils)

    mtl_file = me.parm('mtl_file').evalAsString()
    tex_path = me.parm('tex_path').evalAsString()
    save_path = utils.tailSlash(me.parm('save_path').evalAsString())
    use_mtl = me.parm('use_mtl').eval()
    single_mode = me.parm('single_mode').eval()
    single_mode_index = me.parm('index').eval()
    render_script = me.parm('postrenderscript').eval()
    export_usd = me.parm('export_usd').eval()

    item_list = me.node('items').geometry().stringListAttribValue('item_list')
    if single_mode:
        item_list = [item_list[single_mode_index]]

    null_list = split(me, item_list)
    lop_setup(me, item_list, null_list)

    if export_usd == 1:
        me.parent().node('lopnet1').node('ropnet1').parm('execute').pressButton()