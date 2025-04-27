import os
from . import utils
from importlib import reload
reload(utils)
print('treeToArnold imported')


def convertMtl(standard_surface,req_mtl,tex_path):	
	print('requested material : '+req_mtl)

	mat_dict = utils.findFiles((req_mtl,'tx'),tex_path,True)

	utils.buildArnoldShader(standard_surface,mat_dict,tex_path)
	
	print('Shader built: ' + str(mat_dict))
	standard_surface.parent().layoutChildren()

