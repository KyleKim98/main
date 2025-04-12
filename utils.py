import os,re,shutil,hou
from pathlib import Path

def BtF(string):
    return string.replace('\\','/')

def FtB(string):
    return string.replace('/','\\')

def tailSlash(string):
    if string[-1] != '/':
        return string+'/'
    else:
        return string


def findFiles(patterns, directory, match_all_patterns=False, deep_search=False):
    """
    Search for files in a directory that match given patterns.

    :param patterns: Tuple of strings to compare.
    :param directory: Directory to search.
    :param match_all_patterns: If True, matches all patterns (AND); otherwise, matches any (OR).
    :param deep_search: If True, searches subdirectories using os.walk().
    :return: Dictionary of matched files.
    """

    if deep_search:
        all_files = []
        for root, _, files in os.walk(directory):
            all_files.extend(BtF(os.path.join(root, file)) for file in files)
    else:
        all_files = [BtF(os.path.join(directory, file)) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]

    matched_files = {pattern: [] for pattern in patterns}

    if match_all_patterns:
        # Store indices of files matching each pattern
        matching_sets = {pattern: {i for i, file in enumerate(all_files) if pattern in file} for pattern in patterns}
        
        # Find intersection (AND logic)
        common_indices = set.intersection(*matching_sets.values())

        return {"_".join(patterns): [all_files[i] for i in common_indices]}
    
    else:
        # OR logic - add files that match any pattern
        for pattern in patterns:
            matched_files[pattern] = [file for file in all_files if pattern in file]


        return matched_files



def filterExtension(strings,extension):
    
    l = []
    for i in strings:
        if i.split('.')[-1] == extension:
            l.append(i)

    return l

def getExtension(string):    
    return string.split('.')[-1]


def buildArnoldShader(standard_surface,mat_dict,tex_path):

    subnet = standard_surface.parent()
    existing_images = []

    for i in mat_dict:
        for file in mat_dict[i]:
            mat_type = file.split('_')[-3]

            if mat_type in existing_images:
                break

            image_node = subnet.createNode('image')         
            image_node.parm('filename').set(file)
            image_node.parm('color_family').set('Utility')
            image_node.parm('color_space').set('Raw')

            if 'albedo' in file or 'basecolor' in file:
                image_node.parm('color_family').set('ACES')
                image_node.parm('color_space').set('ACEScg')
                image_node.setName('basecolor')    
                standard_surface.setNamedInput('base_color',image_node,0)   
                existing_images.append('basecolor')

            elif 'glossiness' in file:
                comp_node = subnet.createNode('arnold::complement')
                comp_node.setInput(0,image_node,0)
                image_node.setName('glossiness')
                standard_surface.setNamedInput('specular_roughness',comp_node,0)
                existing_images.append('glossiness')

            elif 'roughness' in file:   
                image_node.setName('roughness')
                standard_surface.setNamedInput('specular_roughness',image_node,0)  
                existing_images.append('roughness')

            elif 'normal' in file:
                normal_node = subnet.createNode('arnold::normal_map')
                normal_node.setInput(0,image_node,0)                
                image_node.setName('normal')
                standard_surface.setNamedInput('normal',normal_node,0)   
                existing_images.append('normal')

            elif 'metallic' in file:                
                image_node.setName('metallic')
                standard_surface.setNamedInput('metalness',image_node,0)      
                existing_images.append('metallic')

            elif 'ao' in file:                
                image_node.setName('ao')
                standard_surface.setNamedInput('base',image_node,0)            
                existing_images.append('ao')  

            elif 'height' in file or 'displacement' in file:
                image_node.setName('displacement')
                color_node = subnet.createNode('arnold::color_correct')
                color_node.parmTuple('multiply').set((0,0,0))
                color_node.setNamedInput('input',image_node,0)
                subnet.node('OUT_material').setNamedInput('displacement',color_node,0)       
                existing_images.append(mat_type)                   

            elif 'translucency' in file:
                image_node.parm('color_family').set('ACES')
                image_node.parm('color_space').set('ACEScg')  
                standard_surface.parm('subsurface').set(.25)
                standard_surface.parmTuple('subsurface_radius').set((.05,.05,.05)) 
                image_node.setName('translucency')
                standard_surface.setNamedInput('subsurface_color',image_node,0)   
                existing_images.append('translucency')             

            elif 'opacity' in file:
                
                image_node.setName('opacity')
                standard_surface.setNamedInput('opacity',image_node,0)        
                existing_images.append('opacity')

            elif 'refraction' in file:
                
                image_node.setName('refraction')
                standard_surface.setNamedInput('transmission',image_node,0)       
                existing_images.append('refraction')



def extract_usda_references(filepath,keyword):
    references = []
    filepath = str(filepath)

    # Regex to match @...@ paths used in references
    reference_pattern = re.compile(keyword+r'\s*=\s*(?:@([^@]+)@|\[(.*?)\])', re.DOTALL)

    with open(filepath, 'r') as f:
        content = f.read()

        # Find all direct references and lists
        for match in reference_pattern.finditer(content):
            if match.group(1):  # Single reference
                references.append(match.group(1).strip())
            elif match.group(2):  # List of references
                list_content = match.group(2)
                # Find all @...@ inside the list
                list_references = re.findall(r'@([^@]+)@', list_content)
                references.extend([ref.strip() for ref in list_references])

    return references

def usdAbsPath(scene_path,rel_path):

    asset_name = rel_path.split('/')[-1].split('.')[0]
    tokens = rel_path.split('/')
    counter = 0
    curr_folder = Path(scene_path)

    #let's count how many ../ we have and that's the number of the parents dirs to meet the first string folder 
    #ex) ../../Buildings/A/B/item.usda -> go up 2 times from the save path then there will be the 'Building' folder 
    #we are counting how many times we go up with the couner var.

    for enum,j in enumerate(tokens):
        if j == '..':                    
            curr_folder = curr_folder.parent.absolute()
            counter += 1
        else:
            break

    #now we know the absolute path to reach the first string folder.
    #ex) ../../ becomes E:/MyLibrary. this is front abs path
    fron_path = tailSlash(BtF(str(curr_folder.absolute())))

    
    #now we are only acquiring the absolute part of reference by using starting the splitted string from the 'counter' var point
    #ex)../../Buildings/A/B/item.usda -> Buildings/A/B/item.usda this is back abs path
    back_path = '/'.join(rel_path.split('/')[counter:-1])


    #combine front abs path and back abs path to complete the path
    #ex) E:/MyLibrary/Buildings/A/B/item.usda
    path = fron_path+back_path
    return path
    #since we just need the folder, not the usda file itself, get rid of the last portion of / split
    #ex) E:/MyLibrary/Buildings/A/B/item.usda -> E:/MyLibrary/Buildings/A/B
    #copy_path = '/'.join(path.split('/')[:-1])
def alias_to_abs(string,seperator):

    temp = string.split(seperator)

    for enum,i in enumerate(temp):
        if '$' in i:
            temp[enum] = hou.getenv(i[1:])
    return seperator.join(temp)

def correctPath(string):

    if '/' in string:
        temp = alias_to_abs(string,'/')
        return tailSlash(temp)

    elif '\\' in string:
        temp = BtF(string)
        temp = alias_to_abs(string,'/')
        return tailSlash(temp)
