def setImageNode(standard_surface,parm_name,tex_name,tex_path,utility=0):

	subnet = standard_surface.parent()

	image_node = subnet.createNode('image')
	image_node.setName(parm_name)
	file_name = tex_path+tex_name
	image_node.parm('filename').set(file_name)


	if utility:
		image_node.parm('color_family').set('Utility')
		image_node.parm('color_space').set('Raw')

	else:
		image_node.parm('color_family').set('ACES')
		image_node.parm('color_space').set('ACEScg')	

	standard_surface.setNamedInput(parm_name,image_node,0)

def setBumpNode(standard_surface,parm_name,tex_name,tex_path):

	subnet = standard_surface.parent()

	image_node = subnet.createNode('image')
	image_node.setName(parm_name)
	file_name = tex_path+tex_name
	image_node.parm('filename').set(file_name)

	image_node.parm('color_family').set('Utility')
	image_node.parm('color_space').set('Raw')

	bump_node = subnet.createNode('arnold::bump2d')
	bump_node.setNamedInput('bump_map',image_node,0)
	standard_surface.setNamedInput('normal',bump_node,0)

def convertMtl(standard_surface,req_mtl,materials,tex_path):

	arnold_shader = {}
	data = materials[req_mtl]

	for enum,properties in enumerate(data.items()):
		#print(properties)
		#print(enum)
		if 'Mt' in properties:  # Custom Metalness          
			standard_surface.parm('metalness').set(properties[1])
		if 'Ns' in properties:  # Specular roughness   
			standard_surface.parm('specular_roughness').set(1.0-float(properties[1][0])/1000.0)
		if 'Ni' in properties:  # IOR   
			standard_surface.parm('specular_IOR').set(float(properties[1][0]))
		if 'Tr' in properties:  # Transparencys   
			standard_surface.parm('transmission').set(float(properties[1][0]))
		if 'Tf' in properties:  # Transmission Color         
			standard_surface.parmTuple('transmission_color').set(properties[1])
		if 'Kd' in properties:  # Diffuse color          
			standard_surface.parmTuple('base_color').set(properties[1])

		if 'map_Kd' in properties:  # Diffuse map   
			tex_name = properties[1][0].split('\\')[-1]
			setImageNode(standard_surface,'base_color',tex_name,tex_path)
		if 'map_bump' in properties:  # bump map 			
			tex_name = properties[1][0].split('\\')[-1]

			if 'Normal' in tex_name:
				setImageNode(standard_surface,'normal',tex_name,tex_path,1)
			else:
				setBumpNode(standard_surface,'bump_image',tex_name,tex_path)

		if 'map_refl' in properties:  # roughness map 			
			tex_name = properties[1][0].split('\\')[-1]
			setImageNode(standard_surface,'specular_roughness',tex_name,tex_path,1)

	standard_surface.parent().layoutChildren()
