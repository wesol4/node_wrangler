# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    'name': "Node Wrangler",
    'author': "Greg Zaal, Bartek Skorupa",
    'version': (2, 35),
    'blender': (2, 6, 9),
    'location': "Node Editor Properties Panel (Ctrl-SPACE)",
    'description': "Various tools to enhance and speed up node-based workflow",
    'warning': "",
    'wiki_url': "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Nodes_Efficiency_Tools", # which to use? Efficiency or Wrangler?
    'tracker_url': "http://projects.blender.org/tracker/index.php?func=detail&aid=33543&group_id=153&atid=469",
    'category': "Node",
    }

import bpy
import blf
import bgl
from bpy.types import Operator, Panel, Menu
from bpy.props import FloatProperty, EnumProperty, BoolProperty, StringProperty
from mathutils import Vector
from math import cos, sin, pi, sqrt

#################
# rl_outputs:
# list of outputs of Input Render Layer
# with attributes determinig if pass is used,
# and MultiLayer EXR outputs names and corresponding render engines
#
# rl_outputs entry = (render_pass, rl_output_name, exr_output_name, in_internal, in_cycles)
rl_outputs = (
    ('use_pass_ambient_occlusion', 'AO', 'AO', True, True),
    ('use_pass_color', 'Color', 'Color', True, False),
    ('use_pass_combined', 'Image', 'Combined', True, True),
    ('use_pass_diffuse', 'Diffuse', 'Diffuse', True, False),
    ('use_pass_diffuse_color', 'Diffuse Color', 'DiffCol', False, True),
    ('use_pass_diffuse_direct', 'Diffuse Direct', 'DiffDir', False, True),
    ('use_pass_diffuse_indirect', 'Diffuse Indirect', 'DiffInd', False, True),
    ('use_pass_emit', 'Emit', 'Emit', True, False),
    ('use_pass_environment', 'Environment', 'Env', True, False),
    ('use_pass_glossy_color', 'Glossy Color', 'GlossCol', False, True),
    ('use_pass_glossy_direct', 'Glossy Direct', 'GlossDir', False, True),
    ('use_pass_glossy_indirect', 'Glossy Indirect', 'GlossInd', False, True),
    ('use_pass_indirect', 'Indirect', 'Indirect', True, False),
    ('use_pass_material_index', 'IndexMA', 'IndexMA', True, True),
    ('use_pass_mist', 'Mist', 'Mist', True, False),
    ('use_pass_normal', 'Normal', 'Normal', True, True),
    ('use_pass_object_index', 'IndexOB', 'IndexOB', True, True),
    ('use_pass_reflection', 'Reflect', 'Reflect', True, False),
    ('use_pass_refraction', 'Refract', 'Refract', True, False),
    ('use_pass_shadow', 'Shadow', 'Shadow', True, True),
    ('use_pass_specular', 'Specular', 'Spec', True, False),
    ('use_pass_subsurface_color', 'Subsurface Color', 'SubsurfaceCol', False, True),
    ('use_pass_subsurface_direct', 'Subsurface Direct', 'SubsurfaceDir', False, True),
    ('use_pass_subsurface_indirect', 'Subsurface Indirect', 'SubsurfaceInd', False, True),
    ('use_pass_transmission_color', 'Transmission Color', 'TransCol', False, True),
    ('use_pass_transmission_direct', 'Transmission Direct', 'TransDir', False, True),
    ('use_pass_transmission_indirect', 'Transmission Indirect', 'TransInd', False, True),
    ('use_pass_uv', 'UV', 'UV', True, True),
    ('use_pass_vector', 'Speed', 'Vector', True, True),
    ('use_pass_z', 'Z', 'Depth', True, True),
    )
# list of blend types of "Mix" nodes in a form that can be used as 'items' for EnumProperty.
blend_types = [
    ('MIX', 'Mix', 'Mix Mode'),
    ('ADD', 'Add', 'Add Mode'),
    ('MULTIPLY', 'Multiply', 'Multiply Mode'),
    ('SUBTRACT', 'Subtract', 'Subtract Mode'),
    ('SCREEN', 'Screen', 'Screen Mode'),
    ('DIVIDE', 'Divide', 'Divide Mode'),
    ('DIFFERENCE', 'Difference', 'Difference Mode'),
    ('DARKEN', 'Darken', 'Darken Mode'),
    ('LIGHTEN', 'Lighten', 'Lighten Mode'),
    ('OVERLAY', 'Overlay', 'Overlay Mode'),
    ('DODGE', 'Dodge', 'Dodge Mode'),
    ('BURN', 'Burn', 'Burn Mode'),
    ('HUE', 'Hue', 'Hue Mode'),
    ('SATURATION', 'Saturation', 'Saturation Mode'),
    ('VALUE', 'Value', 'Value Mode'),
    ('COLOR', 'Color', 'Color Mode'),
    ('SOFT_LIGHT', 'Soft Light', 'Soft Light Mode'),
    ('LINEAR_LIGHT', 'Linear Light', 'Linear Light Mode'),
    ]
# list of operations of "Math" nodes in a form that can be used as 'items' for EnumProperty.
operations = [
    ('ADD', 'Add', 'Add Mode'),
    ('MULTIPLY', 'Multiply', 'Multiply Mode'),
    ('SUBTRACT', 'Subtract', 'Subtract Mode'),
    ('DIVIDE', 'Divide', 'Divide Mode'),
    ('SINE', 'Sine', 'Sine Mode'),
    ('COSINE', 'Cosine', 'Cosine Mode'),
    ('TANGENT', 'Tangent', 'Tangent Mode'),
    ('ARCSINE', 'Arcsine', 'Arcsine Mode'),
    ('ARCCOSINE', 'Arccosine', 'Arccosine Mode'),
    ('ARCTANGENT', 'Arctangent', 'Arctangent Mode'),
    ('POWER', 'Power', 'Power Mode'),
    ('LOGARITHM', 'Logatithm', 'Logarithm Mode'),
    ('MINIMUM', 'Minimum', 'Minimum Mode'),
    ('MAXIMUM', 'Maximum', 'Maximum Mode'),
    ('ROUND', 'Round', 'Round Mode'),
    ('LESS_THAN', 'Less Than', 'Less Thann Mode'),
    ('GREATER_THAN', 'Greater Than', 'Greater Than Mode'),
    ]
# in BatchChangeNodes additional types/operations in a form that can be used as 'items' for EnumProperty.
navs = [
    ('CURRENT', 'Current', 'Leave at current state'),
    ('NEXT', 'Next', 'Next blend type/operation'),
    ('PREV', 'Prev', 'Previous blend type/operation'),
    ]
# list of mixing shaders
merge_shaders_types = ('MIX', 'ADD')
# list of regular shaders. Entry: (identified, type, name for humans). Will be used in SwapShaders and menus.
# Keeping mixed case to avoid having to translate entries when adding new nodes in SwapNodes.
regular_shaders = (
    ('ShaderNodeBsdfDiffuse', 'BSDF_DIFFUSE', 'Diffuse BSDF'),
    ('ShaderNodeBsdfGlossy', 'BSDF_GLOSSY', 'Glossy BSDF'),
    ('ShaderNodeBsdfTransparent', 'BSDF_TRANSPARENT', 'Transparent BSDF'),
    ('ShaderNodeBsdfRefraction', 'BSDF_REFRACTION', 'Refraction BSDF'),
    ('ShaderNodeBsdfGlass', 'BSDF_GLASS', 'Glass BSDF'),
    ('ShaderNodeBsdfTranslucent', 'BSDF_TRANSLUCENT', 'Translucent BSDF'),
    ('ShaderNodeBsdfAnisotropic', 'BSDF_ANISOTROPIC', 'Anisotropic BSDF'),
    ('ShaderNodeBsdfVelvet', 'BSDF_VELVET', 'Velvet BSDF'),
    ('ShaderNodeBsdfToon', 'BSDF_TOON', 'Toon BSDF'),
    ('ShaderNodeSubsurfaceScattering', 'SUBSURFACE_SCATTERING', 'Subsurface Scattering'),
    ('ShaderNodeEmission', 'EMISSION', 'Emission'),
    ('ShaderNodeBackground', 'BACKGROUND', 'Background'),
    ('ShaderNodeAmbientOcclusion', 'AMBIENT_OCCLUSION', 'Ambient Occlusion'),
    ('ShaderNodeHoldout', 'HOLDOUT', 'Holdout'),
    )
shader_idents = list(x[0] for x in regular_shaders)
shader_types = list(x[1] for x in regular_shaders)
shader_names = list(x[2] for x in regular_shaders)

merge_shaders = (
    ('ShaderNodeMixShader', 'MIX_SHADER', 'Mix Shader'),
    ('ShaderNodeAddShader', 'ADD_SHADER', 'Add Shader'),
    )
mix_shader_types = list(x[1] for x in merge_shaders)

texture_list = [['ShaderNodeTexImage', 'TEX_IMAGE', 'Image'],
                ['ShaderNodeTexEnvironment', 'TEX_ENVIRONMENT', 'Environment'],
                ['ShaderNodeTexSky', 'TEX_SKY', 'Sky'],
                ['ShaderNodeTexNoise', 'TEX_NOISE', 'Noise'],
                ['ShaderNodeTexWave', 'TEX_WAVE', 'Wave'],
                ['ShaderNodeTexVoronoi', 'TEX_VORONOI', 'Voronoi'],
                ['ShaderNodeTexMusgrave', 'TEX_MUSGRAVE', 'Musgrave'],
                ['ShaderNodeTexGradient', 'TEX_GRADIENT', 'Gradient'],
                ['ShaderNodeTexMagic', 'TEX_MAGIC', 'Magic'],
                ['ShaderNodeTexChecker', 'TEX_CHECKER', 'Checker'],
                ['ShaderNodeTexBrick', 'TEX_BRICK', 'Brick']]
texture_idents = list(x[0] for x in texture_list)
texture_types = list(x[1] for x in texture_list)
texture_names = list(x[2] for x in texture_list)

output_types = ['OUTPUT_MATERIAL', 'OUTPUT_WORLD', 'OUTPUT_LAMP', 'COMPOSITE']

non_input_attrs = ['image',
                   'color_space',
                   'projection',
                   'distribution',
                   'component',
                   'falloff',
                   'sundirection',
                   'wave_type',
                   'coloring',
                   'musgrave_type',
                   'gradient_type',
                   'turbulence_depth',
                   'offset',
                   'offset_frequency',
                   'squash',
                   'squash_frequency']

draw_color_sets = {"red_white": [[1.0, 1.0, 1.0, 0.7],
                                 [1.0, 0.0, 0.0, 0.7],
                                 [0.8, 0.2, 0.2, 1.0]],
                   "green": [[0.0, 0.0, 0.0, 1.0],
                             [0.38, 0.77, 0.38, 1.0],
                             [0.38, 0.77, 0.38, 1.0]],
                   "yellow": [[0.0, 0.0, 0.0, 1.0],
                              [0.77, 0.77, 0.16, 1.0],
                              [0.77, 0.77, 0.16, 1.0]],
                   "purple": [[0.0, 0.0, 0.0, 1.0],
                             [0.38, 0.38, 0.77, 1.0],
                             [0.38, 0.38, 0.77, 1.0]],
                   "grey": [[0.0, 0.0, 0.0, 1.0],
                             [0.63, 0.63, 0.63, 1.0],
                             [0.63, 0.63, 0.63, 1.0]],
                   "black": [[1.0, 1.0, 1.0, 0.7],
                             [0.0, 0.0, 0.0, 0.7],
                             [0.2, 0.2, 0.2, 1.0]]}

def niceHotkeyName(punc):
    # convert the ugly string name into the actual character    
    if punc == 'LEFTMOUSE':
        return "LMB"
    elif punc == 'MIDDLEMOUSE':
        return "MMB"
    elif punc == 'RIGHTMOUSE':
        return "RMB"
    elif punc == 'SELECTMOUSE':
        return "Select"
    elif punc == 'WHEELUPMOUSE':
        return "Wheel Up"
    elif punc == 'WHEELDOWNMOUSE':
        return "Wheel Down"
    elif punc == 'WHEELINMOUSE':
        return "Wheel In"
    elif punc == 'WHEELOUTMOUSE':
        return "Wheel Out"
    elif punc == 'ZERO':
        return "0"
    elif punc == 'ONE':
        return "1"
    elif punc == 'TWO':
        return "2"
    elif punc == 'THREE':
        return "3"
    elif punc == 'FOUR':
        return "4"
    elif punc == 'FIVE':
        return "5"
    elif punc == 'SIX':
        return "6"
    elif punc == 'SEVEN':
        return "7"
    elif punc == 'EIGHT':
        return "8"
    elif punc == 'NINE':
        return "9"
    elif punc == 'OSKEY':
        return "Super"
    elif punc == 'RET':
        return "Enter"
    elif punc == 'LINE_FEED':
        return "Enter"
    elif punc == 'SEMI_COLON':
        return ";"
    elif punc == 'PERIOD':
        return "."
    elif punc == 'COMMA':
        return ","
    elif punc == 'QUOTE':
        return '"'
    elif punc == 'MINUS':
        return "-"
    elif punc == 'SLASH':
        return "/"
    elif punc == 'BACK_SLASH':
        return "\\"
    elif punc == 'EQUAL':
        return "="
    elif punc == 'NUMPAD_1':
        return "Numpad 1"
    elif punc == 'NUMPAD_2':
        return "Numpad 2"
    elif punc == 'NUMPAD_3':
        return "Numpad 3"
    elif punc == 'NUMPAD_4':
        return "Numpad 4"
    elif punc == 'NUMPAD_5':
        return "Numpad 5"
    elif punc == 'NUMPAD_6':
        return "Numpad 6"
    elif punc == 'NUMPAD_7':
        return "Numpad 7"
    elif punc == 'NUMPAD_8':
        return "Numpad 8"
    elif punc == 'NUMPAD_9':
        return "Numpad 9"
    elif punc == 'NUMPAD_0':
        return "Numpad 0"
    elif punc == 'NUMPAD_PERIOD':
        return "Numpad ."
    elif punc == 'NUMPAD_SLASH':
        return "Numpad /"
    elif punc == 'NUMPAD_ASTERIX':
        return "Numpad *"
    elif punc == 'NUMPAD_MINUS':
        return "Numpad -"
    elif punc == 'NUMPAD_ENTER':
        return "Numpad Enter"
    elif punc == 'NUMPAD_PLUS':
        return "Numpad +"
    else:
        return punc.replace("_", " ").title()

# Addon prefs
class NodeWrangler(bpy.types.AddonPreferences):
    bl_idname = __name__

    # merge_hide = bpy.props.BoolProperty(
    #     name="Hide Mix Nodes on Creation",
    #     default=True,
    #     description="When merging nodes with the Ctrl+Numpad0 hotkey (and similar) specifiy whether to collapse them or show the full node with options expanded"
    # )
    merge_hide = bpy.props.EnumProperty(
        name="Hide Mix nodes",
        items=(("always", "Always", "Always collapse the new merge nodes"),
               ("non_shader", "Non-Shader", "Collapse in all cases except for shaders"),
               ("never", "Never", "Never collapse the new merge nodes")),
        default='non_shader',
        description="When merging nodes with the Ctrl+Numpad0 hotkey (and similar) specifiy whether to collapse them or show the full node with options expanded")
    merge_position = bpy.props.EnumProperty(
        name="Mix Node Position",
        items=(("center", "Center", "Place the Mix node between the two nodes"),
               ("bottom", "Bottom", "Place the Mix node at the same height as the lowest node")),
        default='center',
        description="When merging nodes with the Ctrl+Numpad0 hotkey (and similar) specifiy the position of the new nodes")
    bgl_antialiasing = bpy.props.BoolProperty(
        name="Line Antialiasing",
        default=False,
        description="Remove aliasing artifacts on lines drawn in interactive modes such as Lazy Connect (Alt+LMB) and Lazy Merge (Alt+RMB) - this may cause issues on some systems"
    )

    show_hotkey_list = bpy.props.BoolProperty(
        name="Show Hotkey List",
        default=False,
        description="Expand this box into a list of all the hotkeys for functions in this addon"
    )
    hotkey_list_filter = bpy.props.StringProperty(
        name="        Filter by Name",
        default="",
        description="Show only hotkeys that have this text in their name"
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "merge_position")
        col.prop(self, "merge_hide")
        col.prop(self, "bgl_antialiasing")

        box = col.box()
        col = box.column(align=True)

        hotkey_button_name = "Show Hotkey List"
        if self.show_hotkey_list:
            hotkey_button_name = "Hide Hotkey List"
        col.prop(self, "show_hotkey_list", text=hotkey_button_name, toggle=True)
        if self.show_hotkey_list:
            col.prop(self, "hotkey_list_filter", icon="VIEWZOOM")
            col.separator()
            for hotkey in kmi_defs:
                if hotkey[6]:
                    hotkey_name = hotkey[6]

                    if self.hotkey_list_filter.lower() in hotkey_name.lower():
                        row = col.row(align=True)
                        row.label(hotkey_name)
                        keystr = niceHotkeyName(hotkey[1])
                        if hotkey[3]:
                            keystr = "Shift " + keystr
                        if hotkey[4]:
                            keystr = "Alt " + keystr
                        if hotkey[2]:
                            keystr = "Ctrl " + keystr
                        row.label(keystr)


def hack_force_update(nodes):
    for node in nodes:
        if node.inputs:
            for inpt in node.inputs:
                try:
                    inpt.default_value = inpt.default_value # set value to itself to force update
                    return True
                except:
                    pass
    return False

def get_nodes_links(context):
    space = context.space_data
    tree = space.node_tree
    nodes = tree.nodes
    links = tree.links
    active = nodes.active
    context_active = context.active_node
    # check if we are working on regular node tree or node group is currently edited.
    # if group is edited - active node of space_tree is the group
    # if context.active_node != space active node - it means that the group is being edited.
    # in such case we set "nodes" to be nodes of this group, "links" to be links of this group
    # if context.active_node == space.active_node it means that we are not currently editing group
    is_main_tree = True
    if active:
        is_main_tree = context_active == active
    if not is_main_tree:  # if group is currently edited
        tree = active.node_tree
        nodes = tree.nodes
        links = tree.links

    return nodes, links

# Having two of these functions is not ideal, but I had trouble
# with the Auto-Arrange function and couldn't easily solve it
# by using one function (other things break when it works for 
# Auto-Arrange) - however since I plan to rewrite that whole
# function, which is the only thing that uses this second
# function, there's not much point in fixing it now.
def get_nodes_links_withsel(context):
    space = context.space_data
    tree = space.node_tree
    nodes = tree.nodes
    links = tree.links
    active = nodes.active
    context_active = context.active_node
    is_main_tree = True
    if active:
        is_main_tree = context_active == active
    if not is_main_tree:  # if group is currently edited
        tree = active.node_tree
        nodes = tree.nodes
        links = tree.links
    all_nodes = nodes
    newnodes = []   
    for node in nodes:
        if node.select == True:
            newnodes.append(node)
    if len(newnodes) == 0:
        newnodes = all_nodes
    nodes_sorted = sorted(newnodes, key=lambda x: x.name)        # Sort the nodes list to achieve consistent
    links_sorted = sorted(links, key=lambda x: x.from_node.name) # results (order was changed based on selection).
    return nodes_sorted, links_sorted


def isStartNode(node):
    bool = True
    if len(node.inputs):
        for input in node.inputs:
            if input.links != ():
                bool = False
    return bool


def isEndNode(node):
    bool = True
    if len(node.outputs):
        for output in node.outputs:
            if output.links != ():
                bool = False
    return bool


def between(b1, a, b2):
    #   b1 MUST be smaller than b2!
    bool = False
    if a >= b1 and a <= b2:
        bool = True
    return bool


def overlaps(node1, node2):
    dim1x = node1.dimensions.x
    dim1y = node1.dimensions.y
    dim2x = node2.dimensions.x
    dim2y = node2.dimensions.y
    boolx = False
    booly = False
    boolboth = False

    # check for x overlap
    if between(node2.location.x, node1.location.x, (node2.location.x + dim2x)) or between(node2.location.x, (node1.location.x + dim1x), (node2.location.x + dim2x)):  # if either edges are inside the second node
        boolx = True
    if between(node1.location.x, node2.location.x, node1.location.x + dim1x) and between(node1.location.x, (node2.location.x + dim2x), node1.location.x + dim1x):  # if each edge is on either side of the second node
        boolx = True

    # check for y overlap
    if between((node2.location.y - dim2y), node1.location.y, node2.location.y) or between((node2.location.y - dim2y), (node1.location.y - dim1y), node2.location.y):
        booly = True
    if between((node1.location.y - dim1y), node2.location.y, node1.location.y) and between((node1.location.y - dim1y), (node2.location.y - dim2y), node1.location.y):
        booly = True

    if boolx == True and booly == True:
        boolboth = True
    return boolboth


def nodeMidPt(node, axis):
    if axis == 'x':
        d = node.location.x+(node.dimensions.x/2)
    elif axis == 'y':
        d = node.location.y-(node.dimensions.y/2)
    else: d = 0
    return d


def treeMidPt(nodes):
    minx = (sorted(nodes, key=lambda k: k.location.x))[0].location.x
    miny = (sorted(nodes, key=lambda k: k.location.y))[0].location.y
    maxx = (sorted(nodes, key=lambda k: k.location.x, reverse=True))[0].location.x
    maxy = (sorted(nodes, key=lambda k: k.location.y, reverse=True))[0].location.y

    midx = minx + ((maxx - minx) / 2)
    midy = miny + ((maxy - miny) / 2)

    return midx, midy


def autolink (node1, node2, links):
    link_made = False
    for outp in node1.outputs:
        for inp in node2.inputs:
            if not inp.is_linked and inp.type == outp.type:
                link_made = True
                links.new(outp, inp)
                return True
    return link_made


def nodeAtPos(nodes, context, event):
    nodes_near_mouse = []
    nodes_under_mouse = []
    target_node = None

    store_mouse_cursor(context, event)
    x, y = context.space_data.cursor_location

    # nearest node
    nodes_near_mouse = sorted(nodes, key=lambda k: sqrt((x-nodeMidPt(k, 'x'))**2 + (y-nodeMidPt(k, 'y'))**2))

    for node in nodes:
        if between(node.location.x, x, node.location.x+node.dimensions.x) and \
           between(node.location.y-node.dimensions.y, y, node.location.y):
            nodes_under_mouse.append(node)

    if len(nodes_under_mouse) == 1:
        if nodes_under_mouse[0] != nodes_near_mouse[0]:
            target_node = nodes_under_mouse[0] # use the node under the mouse if there is one and only one
        else:
            target_node = nodes_near_mouse[0] # else use the nearest node
    else:
        target_node = nodes_near_mouse[0]


    return target_node


def store_mouse_cursor(context, event):
        space = context.space_data
        v2d = context.region.view2d
        tree = space.edit_tree

        # convert mouse position to the View2D for later node placement
        if context.region.type == 'WINDOW':
            space.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        else:
            space.cursor_location = tree.view_center


class NodeToolBase:
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR' and space.node_tree is not None


def drawLine(x1, y1, x2, y2, size, colour=[1.0, 1.0, 1.0, 0.7]):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(colour[0], colour[1], colour[2], colour[3])
    bgl.glLineWidth(size)

    bgl.glBegin(bgl.GL_LINE_STRIP)
    #bgl.glBegin(bgl.GL_LINES)
    try:
        bgl.glVertex2f(x1, y1)
        bgl.glVertex2f(x2, y2)
    except:
        pass
    bgl.glEnd()

def drawCircle(mx, my, radius, colour=[1.0, 1.0, 1.0, 0.7]):
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    bgl.glColor4f(colour[0], colour[1], colour[2], colour[3])
    radius = radius
    sides = 32
    #bgl.glVertex2f(m1x, m1y)
    for i in range(sides+1):
        cosine= radius * cos(i*2*pi/sides) + mx
        sine  = radius * sin(i*2*pi/sides) + my
        bgl.glVertex2f(cosine,sine)
    bgl.glEnd()


def draw_callback_mixnodes(self, context, mode="MIX"):

    if self.mouse_path:
        settings = context.user_preferences.addons[__name__].preferences
        if settings.bgl_antialiasing:
            bgl.glEnable(bgl.GL_LINE_SMOOTH)

        colors = []
        if mode == 'MIX':
            colors = draw_color_sets['red_white']
        elif mode == 'RGBA':
            colors = draw_color_sets['yellow']
        elif mode == 'VECTOR':
            colors = draw_color_sets['purple']
        elif mode == 'VALUE':
            colors = draw_color_sets['grey']
        elif mode == 'SHADER':
            colors = draw_color_sets['green']
        else:
            colors = draw_color_sets['black']

        m1x = self.mouse_path[0][0]
        m1y = self.mouse_path[0][1]
        m2x = self.mouse_path[-1][0]
        m2y = self.mouse_path[-1][1]

        # circle outline
        drawCircle(m1x, m1y, 6, colors[0])
        drawCircle(m2x, m2y, 6, colors[0])

        drawLine(m1x, m1y, m2x, m2y, 4, colors[0]) # line outline
        drawLine(m1x, m1y, m2x, m2y, 2, colors[1]) # line inner

        # circle inner
        drawCircle(m1x, m1y, 5, colors[2])
        drawCircle(m2x, m2y, 5, colors[2])

        # restore opengl defaults
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

        if settings.bgl_antialiasing:
            bgl.glDisable(bgl.GL_LINE_SMOOTH)


class NWMixNodes(bpy.types.Operator):
    """Add a Mix RGB/Shader node by interactively drawing lines between nodes"""
    bl_idname = "nw.mix_nodes"
    bl_label = "Mix Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.StringProperty(default='MIX')
    merge_type = bpy.props.StringProperty(default='AUTO')

    def modal(self, context, event):
        context.area.tag_redraw()
        nodes, links = get_nodes_links(context)
        cont = True

        start_pos = [event.mouse_region_x, event.mouse_region_y]

        node1=None
        if not context.scene.NWBusyDrawing:
            node1 = nodeAtPos(nodes, context, event)
            if node1:
                context.scene.NWBusyDrawing = node1.name
        else:
            if context.scene.NWBusyDrawing != 'STOP':
                node1 = nodes[context.scene.NWBusyDrawing]

        if event.type == 'MOUSEMOVE':
            self.mouse_path.append((event.mouse_region_x, event.mouse_region_y))

        elif event.type == 'RIGHTMOUSE':
            end_pos = [event.mouse_region_x, event.mouse_region_y]
            bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')

            node2=None
            node2 = nodeAtPos(nodes, context, event)
            if node2:
                context.scene.NWBusyDrawing = node2.name

            if node1 == node2:
                cont = False

            if cont:
                if node1 and node2:
                    for node in nodes:
                        node.select = False
                    node1.select = True
                    node2.select = True

                    bpy.ops.node.merge_nodes(mode=self.mode, merge_type=self.merge_type)


            context.scene.NWBusyDrawing = ""
            return {'FINISHED'}

        elif event.type == 'ESC':
            print ('cancelled')
            bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'NODE_EDITOR':
            # the arguments we pass the the callback
            args = (self, context, 'MIX')
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(draw_callback_mixnodes, args, 'WINDOW', 'POST_PIXEL')

            self.mouse_path = []

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


class NWLazyConnect(bpy.types.Operator):
    """Connect two nodes without clicking a specific socket (automatically determined"""
    bl_idname = "nw.lazy_connect"
    bl_label = "Lazy Connect"
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.StringProperty(default='MIX')
    merge_type = bpy.props.StringProperty(default='AUTO')

    def modal(self, context, event):
        context.area.tag_redraw()
        nodes, links = get_nodes_links(context)
        cont = True

        start_pos = [event.mouse_region_x, event.mouse_region_y]

        node1=None
        if not context.scene.NWBusyDrawing:
            node1 = nodeAtPos(nodes, context, event)
            if node1:
                context.scene.NWBusyDrawing = node1.name
        else:
            if context.scene.NWBusyDrawing != 'STOP':
                node1 = nodes[context.scene.NWBusyDrawing]

        if event.type == 'MOUSEMOVE':
            self.mouse_path.append((event.mouse_region_x, event.mouse_region_y))

        elif event.type == 'LEFTMOUSE':
            end_pos = [event.mouse_region_x, event.mouse_region_y]
            bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')

            node2=None
            node2 = nodeAtPos(nodes, context, event)
            if node2:
                context.scene.NWBusyDrawing = node2.name

            if node1 == node2:
                cont = False

            if cont:
                if node1 and node2:
                    original_sel = []
                    original_unsel = []
                    for node in nodes:
                        if node.select == True:
                            node.select = False
                            original_sel.append(node)
                        else:
                            original_unsel.append(node)
                    node1.select = True
                    node2.select = True

                    autolink(node1, node2, links) # TODO replace with own function

                    for node in original_sel:
                        node.select = True
                    for node in original_unsel:
                        node.select = False


            context.scene.NWBusyDrawing = ""
            return {'FINISHED'}

        elif event.type == 'ESC':
            bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'NODE_EDITOR':
            nodes, links = get_nodes_links(context)
            node = nodeAtPos(nodes, context, event)
            if node:
                context.scene.NWBusyDrawing = node.name
                if node.outputs:
                    context.scene.NWDrawColType = node.outputs[0].type
            else:
                context.scene.NWDrawColType = 'x'

            # the arguments we pass the the callback
            args = (self, context, context.scene.NWDrawColType)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(draw_callback_mixnodes, args, 'WINDOW', 'POST_PIXEL')

            self.mouse_path = []

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


class NWArrangeNodes(bpy.types.Operator):

    'Automatically layout the selected nodes in a linear and non-overlapping fashion.'
    bl_idname = 'nw.layout'
    bl_label = 'Arrange Nodes'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        valid = False
        if context.space_data:
            if context.space_data.node_tree:
                if context.space_data.node_tree.nodes:
                    valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links_withsel(context)
        margin = context.scene.NWSpacing

        oldmidx, oldmidy = treeMidPt(nodes)

        if context.scene.NWDelReroutes:
            # Store selection
            selection = []
            for node in nodes:
                if node.select == True and node.type != "REROUTE":
                    selection.append(node.name)
            # Delete Reroutes
            for node in nodes:
                node.select = False  # deselect all nodes
            for node in nodes:
                if node.type == 'REROUTE':
                    node.select = True
                    bpy.ops.node.delete_reconnect()
            # Restore selection
            nodes, links = get_nodes_links(context)
            nodes = list(nodes)
            for node in nodes:
                if node.name in selection:
                    node.select = True
        else:
            # Store selection anyway
            selection = []
            for node in nodes:
                if node.select == True:
                    selection.append(node.name)

        if context.scene.NWFrameHandling == "delete":
            # Store selection
            selection = []
            for node in nodes:
                if node.select == True and node.type != "FRAME":
                    selection.append(node.name)
            # Delete Frames
            for node in nodes:
                node.select = False  # deselect all nodes
            for node in nodes:
                if node.type == 'FRAME':
                    node.select = True
                    bpy.ops.node.delete()
            # Restore selection
            nodes, links = get_nodes_links(context)
            nodes = list(nodes)
            for node in nodes:
                if node.name in selection:
                    node.select = True

        layout_iterations = len(nodes)*2
        for it in range(0, layout_iterations):
            for node in nodes:
                isframe = False
                if node.type == "FRAME" and context.scene.NWFrameHandling == 'ignore':
                    isframe = True
                if not isframe:
                    if isStartNode(node) and context.scene.NWStartAlign:  # line up start nodes
                        node.location.x = node.dimensions.x / -2
                        node.location.y = node.dimensions.y / 2
                    for link in links:
                        if link.from_node == node and link.to_node in nodes:
                            link.to_node.location.x = node.location.x + node.dimensions.x + margin
                            link.to_node.location.y = node.location.y - (node.dimensions.y / 2) + (link.to_node.dimensions.y / 2)
                else:
                    node.location.x = 0
                    node.location.y = 0

        backward_check_iterations = len(nodes)
        for it in range(0, backward_check_iterations):
            for link in links:
                if link.from_node.location.x + link.from_node.dimensions.x >= link.to_node.location.x and link.to_node in nodes:
                    link.to_node.location.x = link.from_node.location.x + link.from_node.dimensions.x + margin

        # line up end nodes
        if context.scene.NWEndAlign:
            for node in nodes:
                max_loc_x = (sorted(nodes, key=lambda x: x.location.x, reverse=True))[0].location.x
                if isEndNode(node) and not isStartNode(node):
                    node.location.x = max_loc_x

        overlap_iterations = len(nodes)
        for it in range(0, overlap_iterations):
            for node in nodes:
                isframe = False
                if node.type == "FRAME" and context.scene.NWFrameHandling == 'ignore':
                    isframe = True
                if not isframe:
                    for nodecheck in nodes:
                        isframe = False
                        if nodecheck.type == "FRAME" and context.scene.NWFrameHandling == 'ignore':
                            isframe = True
                        if not isframe:
                            if (node != nodecheck):  # dont look for overlaps with self
                                if overlaps(node, nodecheck):
                                    node.location.y = nodecheck.location.y - nodecheck.dimensions.y - 0.5 * margin

        newmidx, newmidy = treeMidPt(nodes)
        middiffx = newmidx - oldmidx
        middiffy = newmidy - oldmidy

        # put nodes back to the center of the old center
        for node in nodes:
            node.location.x = node.location.x - middiffx
            node.location.y = node.location.y - middiffy

        return {'FINISHED'}


class NWDeleteUnusedNodes(bpy.types.Operator):

    'Delete all nodes whose output is not used'
    bl_idname = 'nw.del_unused'
    bl_label = 'Delete Unused Nodes'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        valid = False
        if context.space_data:
            if context.space_data.node_tree:
                if context.space_data.node_tree.nodes:
                    valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        end_types = ['OUTPUT_MATERIAL', 'OUTPUT', 'VIEWER', 'COMPOSITE', 'SPLITVIEWER', 'OUTPUT_FILE', 'LEVELS', 'OUTPUT_LAMP', 'OUTPUT_WORLD', 'GROUP', 'GROUP_INPUT', 'GROUP_OUTPUT']

        # Store selection
        selection = []
        for node in nodes:
            if node.select == True:
                selection.append(node.name)

        deleted_nodes = []
        temp_deleted_nodes = []
        del_unused_iterations = len(nodes)
        for it in range(0, del_unused_iterations):
            temp_deleted_nodes = list(deleted_nodes) # keep record of last iteration
            for node in nodes:
                node.select = False
            for node in nodes:
                if isEndNode(node) and not node.type in end_types and node.type != 'FRAME':
                    node.select = True
                    deleted_nodes.append(node.name)
                    bpy.ops.node.delete()

            if temp_deleted_nodes == deleted_nodes: # stop iterations when there are no more nodes to be deleted
                break

        deleted_nodes = list(set(deleted_nodes))  # get unique list of deleted nodes (iterations would count the same node more than once)
        for n in deleted_nodes:
            self.report({'INFO'}, "Node " + n + " deleted")
        num_deleted = len(deleted_nodes)
        n=' node'
        if num_deleted>1:
            n+='s'
        if num_deleted:
            self.report({'INFO'}, "Deleted " + str(num_deleted) + n)
        else:
            self.report({'INFO'}, "Nothing deleted")

        # Restore selection
        nodes, links = get_nodes_links(context)
        for node in nodes:
            if node.name in selection:
                node.select = True
        return {'FINISHED'}


class NWSwapOutputs(bpy.types.Operator):

    "Swap the output connections of the two selected nodes"
    bl_idname = 'nw.swap_outputs'
    bl_label = 'Swap Outputs'
    newtype = bpy.props.StringProperty()
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return len(context.selected_nodes) == 2

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected_nodes = context.selected_nodes
        n1 = selected_nodes[0]
        n2 = selected_nodes[1]
        n1_outputs = []
        n2_outputs = []

        out_index = 0
        for output in n1.outputs:
            if output.links:
                for link in output.links:
                    n1_outputs.append([out_index, link.to_socket])
                    links.remove(link)
            out_index += 1

        out_index = 0
        for output in n2.outputs:
            if output.links:
                for link in output.links:
                    n2_outputs.append([out_index, link.to_socket])
                    links.remove(link)
            out_index += 1

        for connection in n1_outputs:
            try:
                links.new(n2.outputs[connection[0]], connection[1])
            except:
                self.report({'WARNING'}, "Some connections have been lost due to differing numbers of output sockets")
        for connection in n2_outputs:
            try:
                links.new(n1.outputs[connection[0]], connection[1])
            except:
                self.report({'WARNING'}, "Some connections have been lost due to differing numbers of output sockets")

        return {'FINISHED'}


class NWResetBG(bpy.types.Operator):

    'Reset the zoom and position of the background image'
    bl_idname = 'nw.bg_reset'
    bl_label = 'Reset Backdrop'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type == 'CompositorNodeTree'

    def execute(self, context):
        context.space_data.backdrop_zoom = 1
        context.space_data.backdrop_x = 0
        context.space_data.backdrop_y = 0
        return {'FINISHED'}


class NWAddUVNode(bpy.types.Operator):

    "Add an Attribute node for this UV layer"
    bl_idname = 'nw.add_uv_node'
    bl_label = 'Add UV map'
    uv_name = bpy.props.StringProperty()
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.node.add_node('INVOKE_DEFAULT', use_transform=True, type="ShaderNodeAttribute")
        nodes, links = get_nodes_links(context)
        nodes.active.attribute_name = self.uv_name
        return {'FINISHED'}


class NWUVMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_node_uvs_menu"
    bl_label = "UV Maps"

    @classmethod
    def poll(cls, context):
        if context.area.spaces[0].node_tree:
            if context.area.spaces[0].node_tree.type == 'SHADER':
                return True
            else:
                return False
        else:
            return False
            
    def draw(self, context):
        l = self.layout
        nodes, links = get_nodes_links(context)
        mat = context.object.active_material

        objs = []
        for obj in bpy.data.objects:
            for slot in obj.material_slots:
                if slot.material == mat:
                    objs.append(obj)
        uvs = []
        for obj in objs:
            if obj.data.uv_layers:
                for uv in obj.data.uv_layers:
                    uvs.append(uv.name)
        uvs = list(set(uvs)) # get a unique list

        if uvs:
            for uv in uvs:
                l.operator('nw.add_uv_node', text = uv).uv_name = uv
        else:
            l.label("No UV layers on objects with this material")


class NWEmissionViewer(bpy.types.Operator):
    bl_idname = "nw.emission_viewer"
    bl_label = "Emission Viewer"
    bl_description = "Connect active node to Emission Shader for shadeless previews"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            #if space.tree_type == 'ShaderNodeTree' and space.node_tree is not None and context.active_node is not None and context.active_node.type != "OUTPUT_MATERIAL":
            if space.tree_type == 'ShaderNodeTree' and space.node_tree is not None and context.active_node.type != "OUTPUT_MATERIAL":
                valid = True
        return valid

    def invoke(self, context, event):
    #def execute(self, context):

        # to select at specific mouse position:
        # bpy.ops.node.select(mouse_x=156, mouse_y=410, extend=False)

        mlocx = event.mouse_region_x
        mlocy = event.mouse_region_y
        select_node = bpy.ops.node.select(mouse_x=mlocx, mouse_y=mlocy, extend=False)
        if 'FINISHED' in select_node: # only run if mouse click is on a node
            nodes, links = get_nodes_links(context)
            in_group = context.active_node != context.space_data.node_tree.nodes.active
            active = nodes.active
            valid = False
            if active:
                if (active.name != "Emission Viewer") and (active.type not in output_types) and not in_group:
                    if active.select:
                        if active.type not in shader_types and active.type not in mix_shader_types:
                            valid = True
            if valid:                        
                # get material_output node
                materialout_exists=False
                materialout=None # placeholder node
                for node in nodes:
                    if node.type=="OUTPUT_MATERIAL":
                        materialout_exists=True
                        materialout=node
                if not materialout:
                    materialout = nodes.new('ShaderNodeOutputMaterial')
                    sorted_by_xloc = (sorted(nodes, key=lambda x: x.location.x))
                    max_xloc_node = sorted_by_xloc[-1]
                    if max_xloc_node.name == 'Emission Viewer':
                        max_xloc_node = sorted_by_xloc[-2]
                    materialout.location.x = max_xloc_node.location.x + max_xloc_node.dimensions.x + 80
                    sum_yloc = 0
                    for node in nodes:
                        sum_yloc += node.location.y
                    materialout.location.y = sum_yloc/len(nodes) #put material output at average y location
                    materialout.select=False
                # get Emission Viewer node
                emission_exists=False
                emission_placeholder=nodes[0]
                for node in nodes:
                    if "Emission Viewer" in node.name:
                        emission_exists=True
                        emission_placeholder=node
                        
                position=0
                for link in links: # check if Emission Viewer is already connected to active node
                    if link.from_node.name==active.name and "Emission Viewer" in link.to_node.name and "Emission Viewer" in materialout.inputs[0].links[0].from_node.name:
                        num_outputs=len(link.from_node.outputs)
                        index=0
                        for output in link.from_node.outputs:
                            if link.from_socket==output:
                                position=index
                            index=index+1
                        position=position+1
                        if position>=num_outputs:
                            position=0
                            
                # Store selection
                selection=[]
                for node in nodes:
                   if node.select==True:
                        selection.append(node.name)       
                
                locx = active.location.x
                locy = active.location.y
                dimx = active.dimensions.x
                dimy = active.dimensions.y
                if not emission_exists:
                    emission = nodes.new('ShaderNodeEmission')
                    emission.hide=True
                    emission.location = [materialout.location.x, (materialout.location.y+40)]
                    emission.label="Viewer"
                    emission.name="Emission Viewer"
                    emission.use_custom_color=True
                    emission.color=(0.6,0.5,0.4)
                else:
                    emission=emission_placeholder
                           
                nodes.active = emission
                links.new(active.outputs[position], emission.inputs[0])
                bpy.ops.nw.link_out()
                    
                # Restore selection
                emission.select=False
                nodes.active=active
                for node in nodes:
                    if node.name in selection:
                        node.select=True 
            else: # if active node is a shader, connect to output
                if (active.name != "Emission Viewer") and (active.type not in output_types) and not in_group:
                    bpy.ops.nw.link_out()

                    # ----Delete Emission Viewer----            
                    if len(list(x for x in nodes if x.name == 'Emission Viewer')) > 0:
                        # Store selection
                        selection=[]
                        for node in nodes:
                           if node.select==True:
                                selection.append(node.name)
                                node.select=False
                        # Delete it
                        nodes['Emission Viewer'].select = True
                        bpy.ops.node.delete()
                        # Restore selection
                        for node in nodes:
                            if node.name in selection:
                                node.select=True 

            return {'FINISHED'}
        else:
            return {'CANCELLED'}


class NWFrameSelected(bpy.types.Operator):
    bl_idname = "nw.frame_selected"
    bl_label = "Frame Selected"
    bl_description = "Add a frame node and parent the selected nodes to it"
    bl_options = {'REGISTER', 'UNDO'}
    label_prop = bpy.props.StringProperty(name='Label', default = ' ', description='The visual name of the frame node')
    color_prop = bpy.props.FloatVectorProperty(name="Color", description="The color of the frame node", default=(0.6, 0.6, 0.6),
                                                min=0, max=1, step=1, precision=3, subtype='COLOR_GAMMA', size=3)

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.node_tree is not None:
                valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected = []
        for node in nodes:
            if node.select==True:
                selected.append(node)
                
        bpy.ops.node.add_node(type='NodeFrame')
        frm=nodes.active
        frm.label = self.label_prop
        frm.use_custom_color = True
        frm.color = self.color_prop
        
        for node in selected:
            node.parent=frm

        return {'FINISHED'}


class NWReloadImages(bpy.types.Operator):
    bl_idname = "nw.reload_images"
    bl_label = "Reload Images"
    bl_description = "Update all the image nodes to match their files on disk"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.node_tree is not None:
                valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        image_types = ["IMAGE", "TEX_IMAGE", "TEX_ENVIRONMENT", "TEXTURE"]
        num_reloaded = 0
        for node in nodes:
            if node.type in image_types:
                if node.type == "TEXTURE":
                    if node.texture: # node has texture assigned
                        if node.texture.type in ['IMAGE', 'ENVIRONMENT_MAP']:
                            if node.texture.image: # texture has image assigned
                                node.texture.image.reload()
                                num_reloaded += 1
                else:
                    if node.image:
                        node.image.reload()
                        num_reloaded += 1

        if num_reloaded:
            self.report({'INFO'}, "Reloaded images")
            print ("Reloaded "+str(num_reloaded)+" images")
            hack_force_update(nodes)
            # bpy.ops.node.mute_toggle()
            # bpy.ops.node.mute_toggle() # stupid hack to update the node tree
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No images found to reload in this node tree")
            return {'CANCELLED'}


class NWViewImage(bpy.types.Operator):
    bl_idname = "nw.view_image"
    bl_label = "View Image"
    bl_description = "Switch this window to an image editor and show the image for this node"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.node_tree is not None:
                node = space.node_tree.nodes.active
                if node.type == "TEXTURE":
                    if node.texture: # node has texture assigned
                        if node.texture.type in ['IMAGE', 'ENVIRONMENT_MAP']:
                            if node.texture.image: # texture has image assigned
                                valid = True
                elif node.type == 'MOVIECLIP':
                    if node.clip:
                        valid = True
                elif node.type in ['R_LAYERS', 'VIEWER', 'COMPOSITE']:
                    valid = True
                elif node.type == 'MASK':
                    if node.mask:
                        valid = True
                else:
                    if node.image:
                        valid = True
        return valid

    def execute(self, context):
        node = context.space_data.node_tree.nodes.active
        image = ""
        if node.type == "TEXTURE":
            image = node.texture.image
            context.area.type = 'IMAGE_EDITOR'
            context.space_data.image = image
            context.space_data.mode = 'VIEW'
        elif node.type == 'MOVIECLIP':
            image = node.clip
            context.area.type = 'CLIP_EDITOR'
            context.space_data.clip = image
        elif node.type in ['R_LAYERS', 'COMPOSITE']:
            if "Render Result" in [img.name for img in bpy.data.images]:
                context.area.type = 'IMAGE_EDITOR'
                context.space_data.image = bpy.data.images['Render Result']
                context.space_data.mode = 'VIEW'
            else:
                self.report({'ERROR'}, "Render Result not found, try rerendering")
        elif node.type == 'VIEWER':
            if "Viewer Node" in [img.name for img in bpy.data.images]:
                context.area.type = 'IMAGE_EDITOR'
                context.space_data.image = bpy.data.images['Viewer Node']
                context.space_data.mode = 'VIEW'
            else:
                self.report({'ERROR'}, "Viewer not found, try reconnecting it")
        elif node.type == 'MASK':
            image = node.mask
            context.area.type = 'IMAGE_EDITOR'
            if "Viewer Node" in [img.name for img in bpy.data.images]:
                context.space_data.image = bpy.data.images['Viewer Node']
            elif "Render Result" in [img.name for img in bpy.data.images]:
                context.space_data.image = bpy.data.images['Render Result']
            context.space_data.mode = 'MASK'
            context.space_data.mask = image
        else:
            image = node.image
            context.area.type = 'IMAGE_EDITOR'
            context.space_data.image = image
            context.space_data.mode = 'VIEW'
            
        return {'FINISHED'}


class MergeNodes(Operator, NodeToolBase):
    bl_idname = "node.merge_nodes"
    bl_label = "Merge Nodes"
    bl_description = "Merge Selected Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    mode = EnumProperty(
            name="mode",
            description="All possible blend types and math operations",
            items=blend_types + [op for op in operations if op not in blend_types],
            )
    merge_type = EnumProperty(
            name="merge type",
            description="Type of Merge to be used",
            items=(
                ('AUTO', 'Auto', 'Automatic Output Type Detection'),
                ('SHADER', 'Shader', 'Merge using ADD or MIX Shader'),
                ('MIX', 'Mix Node', 'Merge using Mix Nodes'),
                ('MATH', 'Math Node', 'Merge using Math Nodes'),
                ),
            )

    def execute(self, context):
        settings = context.user_preferences.addons[__name__].preferences
        merge_hide = settings.merge_hide
        merge_position = settings.merge_position # 'center' or 'bottom'

        do_hide = False
        do_hide_shader = False
        if merge_hide == 'always':
            do_hide = True
            do_hide_shader = True
        elif merge_hide == 'non_shader':
            do_hide = True


        tree_type = context.space_data.node_tree.type
        if tree_type == 'COMPOSITING':
            node_type = 'CompositorNode'
        elif tree_type == 'SHADER':
            node_type = 'ShaderNode'
        nodes, links = get_nodes_links(context)
        mode = self.mode
        merge_type = self.merge_type
        selected_mix = []  # entry = [index, loc]
        selected_shader = []  # entry = [index, loc]
        selected_math = []  # entry = [index, loc]

        for i, node in enumerate(nodes):
            if node.select and node.outputs:
                if merge_type == 'AUTO':
                    for (type, types_list, dst) in (
                            ('SHADER', merge_shaders_types, selected_shader),
                            ('RGBA', [t[0] for t in blend_types], selected_mix),
                            ('VALUE', [t[0] for t in operations], selected_math),
                            ):
                        output_type = node.outputs[0].type
                        valid_mode = mode in types_list
                        # When mode is 'MIX' use mix node for both 'RGBA' and 'VALUE' output types.
                        # Cheat that output type is 'RGBA',
                        # and that 'MIX' exists in math operations list.
                        # This way when selected_mix list is analyzed:
                        # Node data will be appended even though it doesn't meet requirements.
                        if output_type != 'SHADER' and mode == 'MIX':
                            output_type = 'RGBA'
                            valid_mode = True
                        if output_type == type and valid_mode:
                            dst.append([i, node.location.x, node.location.y])
                else:
                    for (type, types_list, dst) in (
                            ('SHADER', merge_shaders_types, selected_shader),
                            ('MIX', [t[0] for t in blend_types], selected_mix),
                            ('MATH', [t[0] for t in operations], selected_math),
                            ):
                        if merge_type == type and mode in types_list:
                            dst.append([i, node.location.x, node.location.y])
        # When nodes with output kinds 'RGBA' and 'VALUE' are selected at the same time
        # use only 'Mix' nodes for merging.
        # For that we add selected_math list to selected_mix list and clear selected_math.
        if selected_mix and selected_math and merge_type == 'AUTO':
            selected_mix += selected_math
            selected_math = []

        for nodes_list in [selected_mix, selected_shader, selected_math]:
            if nodes_list:
                count_before = len(nodes)
                # sort list by loc_x - reversed
                nodes_list.sort(key=lambda k: k[1], reverse=True)
                # get maximum loc_x
                loc_x = nodes_list[0][1] + 250.0
                nodes_list.sort(key=lambda k: k[2], reverse=True)
                if merge_position == 'center':
                    loc_y = ((nodes_list[len(nodes_list) - 1][2])+(nodes_list[len(nodes_list) - 2][2]))/2  # average yloc of last two nodes (lowest two)
                else:
                    loc_y = nodes_list[len(nodes_list) - 1][2]
                offset_y = 100
                if not do_hide:
                    offset_y = 200
                if nodes_list == selected_shader and not do_hide_shader:
                    offset_y = 150.0
                the_range = len(nodes_list) - 1
                if len(nodes_list) == 1:
                    the_range = 1
                for i in range(the_range):
                    if nodes_list == selected_mix:
                        add_type = node_type + 'MixRGB'
                        add = nodes.new(add_type)
                        add.blend_type = mode
                        add.show_preview = False
                        add.hide = do_hide
                        if do_hide:
                            loc_y = loc_y -50
                        first = 1
                        second = 2
                        add.width_hidden = 100.0
                    elif nodes_list == selected_math:
                        add_type = node_type + 'Math'
                        add = nodes.new(add_type)
                        add.operation = mode
                        add.hide = do_hide
                        if do_hide:
                            loc_y = loc_y -50
                        first = 0
                        second = 1
                        add.width_hidden = 100.0
                    elif nodes_list == selected_shader:
                        if mode == 'MIX':
                            add_type = node_type + 'MixShader'
                            add = nodes.new(add_type)
                            add.hide = do_hide_shader
                            if do_hide_shader:
                                loc_y = loc_y -50
                            first = 1
                            second = 2
                            add.width_hidden = 100.0
                        elif mode == 'ADD':
                            add_type = node_type + 'AddShader'
                            add = nodes.new(add_type)
                            add.hide = do_hide_shader
                            if do_hide_shader:
                                loc_y = loc_y -50
                            first = 0
                            second = 1
                            add.width_hidden = 100.0
                    add.location = loc_x, loc_y
                    loc_y += offset_y
                    add.select = True
                count_adds = i + 1
                count_after = len(nodes)
                index = count_after - 1
                first_selected = nodes[nodes_list[0][0]]
                # "last" node has been added as first, so its index is count_before.
                last_add = nodes[count_before]
                # add links from last_add to all links 'to_socket' of out links of first selected.
                for fs_link in first_selected.outputs[0].links:
                    # Prevent cyclic dependencies when nodes to be marged are linked to one another.
                    # Create list of invalid indexes.
                    invalid_i = [n[0] for n in (selected_mix + selected_math + selected_shader)]
                    # Link only if "to_node" index not in invalid indexes list.
                    if fs_link.to_node not in [nodes[i] for i in invalid_i]:
                        links.new(last_add.outputs[0], fs_link.to_socket)
                # add link from "first" selected and "first" add node
                links.new(first_selected.outputs[0], nodes[count_after - 1].inputs[first])
                # add links between added ADD nodes and between selected and ADD nodes
                for i in range(count_adds):
                    if i < count_adds - 1:
                        links.new(nodes[index - 1].inputs[first], nodes[index].outputs[0])
                    if len(nodes_list) > 1:
                        links.new(nodes[index].inputs[second], nodes[nodes_list[i + 1][0]].outputs[0])
                    index -= 1
                # set "last" of added nodes as active
                nodes.active = last_add
                for i, x, y in nodes_list:
                    nodes[i].select = False

        return {'FINISHED'}


class BatchChangeNodes(Operator, NodeToolBase):
    bl_idname = "node.batch_change"
    bl_label = "Batch Change"
    bl_description = "Batch Change Blend Type and Math Operation"
    bl_options = {'REGISTER', 'UNDO'}

    blend_type = EnumProperty(
            name="Blend Type",
            items=blend_types + navs,
            )
    operation = EnumProperty(
            name="Operation",
            items=operations + navs,
            )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        blend_type = self.blend_type
        operation = self.operation
        for node in context.selected_nodes:
            if node.type == 'MIX_RGB':
                if not blend_type in [nav[0] for nav in navs]:
                    node.blend_type = blend_type
                else:
                    if blend_type == 'NEXT':
                        index = [i for i, entry in enumerate(blend_types) if node.blend_type in entry][0]
                        #index = blend_types.index(node.blend_type)
                        if index == len(blend_types) - 1:
                            node.blend_type = blend_types[0][0]
                        else:
                            node.blend_type = blend_types[index + 1][0]

                    if blend_type == 'PREV':
                        index = [i for i, entry in enumerate(blend_types) if node.blend_type in entry][0]
                        if index == 0:
                            node.blend_type = blend_types[len(blend_types) - 1][0]
                        else:
                            node.blend_type = blend_types[index - 1][0]

            if node.type == 'MATH':
                if not operation in [nav[0] for nav in navs]:
                    node.operation = operation
                else:
                    if operation == 'NEXT':
                        index = [i for i, entry in enumerate(operations) if node.operation in entry][0]
                        #index = operations.index(node.operation)
                        if index == len(operations) - 1:
                            node.operation = operations[0][0]
                        else:
                            node.operation = operations[index + 1][0]

                    if operation == 'PREV':
                        index = [i for i, entry in enumerate(operations) if node.operation in entry][0]
                        #index = operations.index(node.operation)
                        if index == 0:
                            node.operation = operations[len(operations) - 1][0]
                        else:
                            node.operation = operations[index - 1][0]

        return {'FINISHED'}


class ChangeMixFactor(Operator, NodeToolBase):
    bl_idname = "node.factor"
    bl_label = "Change Factor"
    bl_description = "Change Factors of Mix Nodes and Mix Shader Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    # option: Change factor.
    # If option is 1.0 or 0.0 - set to 1.0 or 0.0
    # Else - change factor by option value.
    option = FloatProperty()

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        option = self.option
        selected = []  # entry = index
        for si, node in enumerate(nodes):
            if node.select:
                if node.type in {'MIX_RGB', 'MIX_SHADER'}:
                    selected.append(si)

        for si in selected:
            fac = nodes[si].inputs[0]
            nodes[si].hide = False
            if option in {0.0, 1.0}:
                fac.default_value = option
            else:
                fac.default_value += option

        return {'FINISHED'}


class NodesCopySettings(Operator):
    bl_idname = "node.copy_settings"
    bl_label = "Copy Settings"
    bl_description = "Copy Settings of Active Node to Selected Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if (space.type == 'NODE_EDITOR' and
                space.node_tree is not None and
                context.active_node is not None and
                context.active_node.type is not 'FRAME'
                ):
            valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected = [n for n in nodes if n.select]
        reselect = []  # duplicated nodes will be selected after execution
        active = nodes.active
        if active.select:
            reselect.append(active)

        for node in selected:
            if node.type == active.type and node != active:
                # duplicate active, relink links as in 'node', append copy to 'reselect', delete node
                bpy.ops.node.select_all(action='DESELECT')
                nodes.active = active
                active.select = True
                bpy.ops.node.duplicate()
                copied = nodes.active
                # Copied active should however inherit some properties from 'node'
                attributes = (
                    'hide', 'show_preview', 'mute', 'label',
                    'use_custom_color', 'color', 'width', 'width_hidden',
                    )
                for attr in attributes:
                    setattr(copied, attr, getattr(node, attr))
                # Handle scenario when 'node' is in frame. 'copied' is in same frame then.
                if copied.parent:
                    bpy.ops.node.parent_clear()
                locx = node.location.x
                locy = node.location.y
                # get absolute node location
                parent = node.parent
                while parent:
                    locx += parent.location.x
                    locy += parent.location.y
                    parent = parent.parent
                copied.location = [locx, locy]
                # reconnect links from node to copied
                for i, input in enumerate(node.inputs):
                    if input.links:
                        link = input.links[0]
                        links.new(link.from_socket, copied.inputs[i])
                for out, output in enumerate(node.outputs):
                    if output.links:
                        out_links = output.links
                        for link in out_links:
                            links.new(copied.outputs[out], link.to_socket)
                bpy.ops.node.select_all(action='DESELECT')
                node.select = True
                bpy.ops.node.delete()
                reselect.append(copied)
            else:  # If selected wasn't copied, need to reselect it afterwards.
                reselect.append(node)
        # clean up
        bpy.ops.node.select_all(action='DESELECT')
        for node in reselect:
            node.select = True
        nodes.active = active

        return {'FINISHED'}


class NodesCopyLabel(Operator, NodeToolBase):
    bl_idname = "node.copy_label"
    bl_label = "Copy Label"
    bl_options = {'REGISTER', 'UNDO'}

    option = EnumProperty(
            name="option",
            description="Source of name of label",
            items=(
                ('FROM_ACTIVE', 'from active', 'from active node',),
                ('FROM_NODE', 'from node', 'from node linked to selected node'),
                ('FROM_SOCKET', 'from socket', 'from socket linked to selected node'),
                )
            )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        option = self.option
        active = nodes.active
        if option == 'FROM_ACTIVE':
            if active:
                src_label = active.label
                for node in [n for n in nodes if n.select and nodes.active != n]:
                    node.label = src_label
        elif option == 'FROM_NODE':
            selected = [n for n in nodes if n.select]
            for node in selected:
                for input in node.inputs:
                    if input.links:
                        src = input.links[0].from_node
                        node.label = src.label
                        break
        elif option == 'FROM_SOCKET':
            selected = [n for n in nodes if n.select]
            for node in selected:
                for input in node.inputs:
                    if input.links:
                        src = input.links[0].from_socket
                        node.label = src.name
                        break

        return {'FINISHED'}


class NodesClearLabel(Operator, NodeToolBase):
    bl_idname = "node.clear_label"
    bl_label = "Clear Label"
    bl_options = {'REGISTER', 'UNDO'}

    option = BoolProperty()

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        for node in [n for n in nodes if n.select]:
            node.label = ''

        return {'FINISHED'}

    def invoke(self, context, event):
        if self.option:
            return self.execute(context)
        else:
            return context.window_manager.invoke_confirm(self, event)


class NodesModifyLabels(Operator, NodeToolBase):
    """Modify Labels of all selected nodes."""
    bl_idname = "node.modify_labels"
    bl_label = "Modify Labels"
    bl_options = {'REGISTER', 'UNDO'}

    prepend = StringProperty(
        name = "Add to Beginning"
        )
    append = StringProperty(
        name = "Add to End"
        )
    replace_from = StringProperty(
        name = "Text to Replace"
        )
    replace_to = StringProperty(
        name = "Replace with"
        )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        for node in [n for n in nodes if n.select]:
            node.label = self.prepend + node.label.replace(self.replace_from, self.replace_to) + self.append

        return {'FINISHED'}

    
    def invoke(self, context, event):
        self.prepend = ""
        self.append = ""
        self.remove = ""
        return context.window_manager.invoke_props_dialog(self)


class NodesAddTextureSetup(Operator):
    bl_idname = "node.add_texture"
    bl_label = "Texture Setup"
    bl_description = "Add Texture Node Setup to Selected Shaders"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.tree_type == 'ShaderNodeTree' and space.node_tree is not None:
                valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        active = nodes.active
        valid = False
        if active:
            if active.select:
                if active.type in shader_types or active.type in texture_types:
                    if not active.inputs[0].is_linked:
                        valid = True
        if valid:
            locx = active.location.x
            locy = active.location.y
            
            xoffset = [500.0, 700.0]
            isshader=True
            if active.type not in shader_types:
                xoffset=[290.0, 500.0]
                isshader=False
                
            coordout=2
            image_type='ShaderNodeTexImage'
            
            if (active.type in texture_types and active.type != 'TEX_IMAGE') or (active.type == 'BACKGROUND'):
                coordout=0 # image texture uses UVs, procedural textures and Background shader use Generated
                if active.type == 'BACKGROUND':
                    image_type='ShaderNodeTexEnvironment'
                    
            if isshader:
                tex = nodes.new (image_type)
                tex.location = [locx - 200.0, locy + 28.0]
                
            map = nodes.new('ShaderNodeMapping')
            map.location = [locx - xoffset[0], locy + 80.0]
            map.width=240
            coord = nodes.new('ShaderNodeTexCoord')            
            coord.location = [locx - xoffset[1], locy+40.0]
            active.select=False
            
            if isshader:
                nodes.active = tex
                links.new(tex.outputs[0], active.inputs[0])
                links.new(map.outputs[0], tex.inputs[0])
                links.new(coord.outputs[coordout], map.inputs[0])
                
            else:
                nodes.active = map
                links.new(map.outputs[0], active.inputs[0])
                links.new(coord.outputs[coordout], map.inputs[0])

        return {'FINISHED'}


class NodesAddReroutes(Operator, NodeToolBase):
    bl_idname = "node.add_reroutes"
    bl_label = "Add Reroutes"
    bl_description = "Add Reroutes to Outputs"
    bl_options = {'REGISTER', 'UNDO'}

    option = EnumProperty(
            name="option",
            items=[
                ('ALL', 'to all', 'Add to all outputs'),
                ('LOOSE', 'to loose', 'Add only to loose outputs'),
                ('LINKED', 'to linked', 'Add only to linked outputs'),
                ]
            )

    def execute(self, context):
        tree_type = context.space_data.node_tree.type
        option = self.option
        nodes, links = get_nodes_links(context)
        # output valid when option is 'all' or when 'loose' output has no links
        valid = False
        post_select = []  # nodes to be selected after execution
        # create reroutes and recreate links
        for node in [n for n in nodes if n.select]:
            if node.outputs:
                x = node.location.x
                y = node.location.y
                width = node.width
                # unhide 'REROUTE' nodes to avoid issues with location.y
                if node.type == 'REROUTE':
                    node.hide = False
                # When node is hidden - width_hidden not usable.
                # Hack needed to calculate real width
                if node.hide:
                    bpy.ops.node.select_all(action='DESELECT')
                    helper = nodes.new('NodeReroute')
                    helper.select = True
                    node.select = True
                    # resize node and helper to zero. Then check locations to calculate width
                    bpy.ops.transform.resize(value=(0.0, 0.0, 0.0))
                    width = 2.0 * (helper.location.x - node.location.x)
                    # restore node location
                    node.location = x, y
                    # delete helper
                    node.select = False
                    # only helper is selected now
                    bpy.ops.node.delete()
                x = node.location.x + width + 20.0
                if node.type != 'REROUTE':
                    y -= 35.0
                y_offset = -22.0
                loc = x, y
            reroutes_count = 0  # will be used when aligning reroutes added to hidden nodes
            for out_i, output in enumerate(node.outputs):
                pass_used = False  # initial value to be analyzed if 'R_LAYERS'
                # if node is not 'R_LAYERS' - "pass_used" not needed, so set it to True
                if node.type != 'R_LAYERS':
                    pass_used = True
                else:  # if 'R_LAYERS' check if output represent used render pass
                    node_scene = node.scene
                    node_layer = node.layer
                    # If output - "Alpha" is analyzed - assume it's used. Not represented in passes.
                    if output.name == 'Alpha':
                        pass_used = True
                    else:
                        # check entries in global 'rl_outputs' variable
                        for render_pass, out_name, exr_name, in_internal, in_cycles in rl_outputs:
                            if output.name == out_name:
                                pass_used = getattr(node_scene.render.layers[node_layer], render_pass)
                                break
                if pass_used:
                    valid = ((option == 'ALL') or
                             (option == 'LOOSE' and not output.links) or
                             (option == 'LINKED' and output.links))
                    # Add reroutes only if valid, but offset location in all cases.
                    if valid:
                        n = nodes.new('NodeReroute')
                        nodes.active = n
                        for link in output.links:
                            links.new(n.outputs[0], link.to_socket)
                        links.new(output, n.inputs[0])
                        n.location = loc
                        post_select.append(n)
                    reroutes_count += 1
                    y += y_offset
                    loc = x, y
            # disselect the node so that after execution of script only newly created nodes are selected
            node.select = False
            # nicer reroutes distribution along y when node.hide
            if node.hide:
                y_translate = reroutes_count * y_offset / 2.0 - y_offset - 35.0
                for reroute in [r for r in nodes if r.select]:
                    reroute.location.y -= y_translate
            for node in post_select:
                node.select = True

        return {'FINISHED'}


class NodesSwap(Operator, NodeToolBase):
    bl_idname = "node.swap_nodes"
    bl_label = "Swap Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    option = EnumProperty(
            items=[
                ('CompositorNodeSwitch', 'Switch', 'Switch'),
                ('NodeReroute', 'Reroute', 'Reroute'),
                ('NodeMixRGB', 'Mix Node', 'Mix Node'),
                ('NodeMath', 'Math Node', 'Math Node'),
                ('CompositorNodeAlphaOver', 'Alpha Over', 'Alpha Over'),
                ('ShaderNodeMixShader', 'Mix Shader', 'Mix Shader'),
                ('ShaderNodeAddShader', 'Add Shader', 'Add Shader'),
                ('ShaderNodeBsdfDiffuse', 'Diffuse BSDF', 'Diffuse BSDF'),
                ('ShaderNodeBsdfGlossy', 'Glossy BSDF', 'Glossy BSDF'),
                ('ShaderNodeBsdfTransparent', 'Transparent BSDF', 'Transparent BSDF'),
                ('ShaderNodeBsdfRefraction', 'Refraction BSDF', 'Refraction BSDF'),
                ('ShaderNodeBsdfGlass', 'Glass BSDF', 'Glass BSDF'),
                ('ShaderNodeBsdfTranslucent', 'Translucent BSDF', 'Translucent BSDF'),
                ('ShaderNodeBsdfAnisotropic', 'Anisotropic BSDF', 'Anisotropic BSDF'),
                ('ShaderNodeBsdfVelvet', 'Velvet BSDF', 'Velvet BSDF'),
                ('ShaderNodeBsdfToon', 'Toon BSDF', 'Toon BSDF'),
                ('ShaderNodeSubsurfaceScattering', 'SUBSURFACE_SCATTERING', 'Subsurface Scattering'),
                ('ShaderNodeEmission', 'Emission', 'Emission'),
                ('ShaderNodeBackground', 'Background', 'Background'),
                ('ShaderNodeAmbientOcclusion', 'Ambient Occlusion', 'Ambient Occlusion'),
                ('ShaderNodeHoldout', 'Holdout', 'Holdout'),
                ]
            )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        tree_type = context.space_data.tree_type
        if tree_type == 'CompositorNodeTree':
            prefix = 'Compositor'
        elif tree_type == 'ShaderNodeTree':
            prefix = 'Shader'
        option = self.option
        selected = [n for n in nodes if n.select]
        reselect = []
        mode = None  # will be used to set proper operation or blend type in new Math or Mix nodes.
        # regular_shaders - global list. Entry: (identifier, type, name for humans)
        # example: ('ShaderNodeBsdfTransparent', 'BSDF_TRANSPARENT', 'Transparent BSDF')
        swap_shaders = option in (s[0] for s in regular_shaders)
        swap_merge_shaders = option in (s[0] for s in merge_shaders)
        if swap_shaders or swap_merge_shaders:
            # replace_types - list of node types that can be replaced using selected option
            shaders = regular_shaders + merge_shaders
            replace_types = [type[1] for type in shaders]
            new_type = option
        elif option == 'CompositorNodeSwitch':
            replace_types = ('REROUTE', 'MIX_RGB', 'MATH', 'ALPHAOVER')
            new_type = option
        elif option == 'NodeReroute':
            replace_types = ('SWITCH')
            new_type = option
        elif option == 'NodeMixRGB':
            replace_types = ('REROUTE', 'SWITCH', 'MATH', 'ALPHAOVER')
            new_type = prefix + option
        elif option == 'NodeMath':
            replace_types = ('REROUTE', 'SWITCH', 'MIX_RGB', 'ALPHAOVER')
            new_type = prefix + option
        elif option == 'CompositorNodeAlphaOver':
            replace_types = ('REROUTE', 'SWITCH', 'MATH', 'MIX_RGB')
            new_type = option
        for node in selected:
            if node.type in replace_types:
                hide = node.hide
                if node.type == 'REROUTE':
                    hide = True
                new_node = nodes.new(new_type)
                # if swap Mix to Math of vice-verca - try to set blend type or operation accordingly
                if new_node.type in {'MIX_RGB', 'ALPHAOVER'}:
                    new_node.inputs[0].default_value = 1.0
                    if node.type == 'MATH':
                        if node.operation in [entry[0] for entry in blend_types]:
                            if hasattr(new_node, 'blend_type'):
                                new_node.blend_type = node.operation
                        for i in range(2):
                            new_node.inputs[i+1].default_value = [node.inputs[i].default_value] * 3 + [1.0]
                    elif node.type in {'MIX_RGB', 'ALPHAOVER'}:
                        for i in range(3):
                            new_node.inputs[i].default_value = node.inputs[i].default_value
                elif new_node.type == 'MATH':
                    if node.type in {'MIX_RGB', 'ALPHAOVER'}:
                        if hasattr(node, 'blend_type'):
                            if node.blend_type in [entry[0] for entry in operations]:
                                new_node.operation = node.blend_type
                        for i in range(2):
                            channels = []
                            for c in range(3):
                                channels.append(node.inputs[i+1].default_value[c])
                            new_node.inputs[i].default_value = max(channels)
                old_inputs_count = len(node.inputs)
                new_inputs_count = len(new_node.inputs)
                replace = []  # entries - pairs: old input index, new input index.
                if swap_shaders:
                    for old_i, old_input in enumerate(node.inputs):
                        for new_i, new_input in enumerate(new_node.inputs):
                            if old_input.name == new_input.name:
                                replace.append((old_i, new_i))
                                new_input.default_value = old_input.default_value
                                break
                elif option == 'ShaderNodeAddShader':
                    if node.type == 'ADD_SHADER':
                        replace = ((0, 0), (1, 1))
                    elif node.type == 'MIX_SHADER':
                        replace = ((1, 0), (2, 1))
                elif option == 'ShaderNodeMixShader':
                    if node.type == 'ADD_SHADER':
                        replace = ((0, 1), (1, 2))
                    elif node.type == 'MIX_SHADER':
                        replace = ((1, 1), (2, 2))
                elif new_inputs_count == 1:
                    replace = ((0, 0), )
                elif new_inputs_count == 2:
                    if old_inputs_count == 1:
                        replace = ((0, 0), )
                    elif old_inputs_count == 2:
                        replace = ((0, 0), (1, 1))
                    elif old_inputs_count == 3:
                        replace = ((1, 0), (2, 1))
                elif new_inputs_count == 3:
                    if old_inputs_count == 1:
                        replace = ((0, 1), )
                    elif old_inputs_count == 2:
                        replace = ((0, 1), (1, 2))
                    elif old_inputs_count == 3:
                        replace = ((0, 0), (1, 1), (2, 2))
                if replace:
                    for old_i, new_i in replace:
                        if node.inputs[old_i].links:
                            in_link = node.inputs[old_i].links[0]
                            links.new(in_link.from_socket, new_node.inputs[new_i])
                for out_link in node.outputs[0].links:
                    links.new(new_node.outputs[0], out_link.to_socket)
                for attr in {'location', 'label', 'mute', 'show_preview', 'width_hidden', 'use_clamp'}:
                    if hasattr(node, attr) and hasattr(new_node, attr):
                        setattr(new_node, attr, getattr(node, attr))
                new_node.hide = hide
                nodes.active = new_node
                reselect.append(new_node)
                bpy.ops.node.select_all(action="DESELECT")
                node.select = True
                bpy.ops.node.delete()
            else:
                reselect.append(node)
        for node in reselect:
            node.select = True

        return {'FINISHED'}


class NodesLinkActiveToSelected(Operator):
    bl_idname = "node.link_active_to_selected"
    bl_label = "Link Active Node to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    replace = BoolProperty()
    use_node_name = BoolProperty()
    use_outputs_names = BoolProperty()

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.node_tree is not None and context.active_node is not None:
                if context.active_node.select:
                    valid = True
        return valid

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        replace = self.replace
        use_node_name = self.use_node_name
        use_outputs_names = self.use_outputs_names
        active = nodes.active
        selected = [node for node in nodes if node.select and node != active]
        outputs = []  # Only usable outputs of active nodes will be stored here.
        for out in active.outputs:
            if active.type != 'R_LAYERS':
                outputs.append(out)
            else:
                # 'R_LAYERS' node type needs special handling.
                # outputs of 'R_LAYERS' are callable even if not seen in UI.
                # Only outputs that represent used passes should be taken into account
                # Check if pass represented by output is used.
                # global 'rl_outputs' list will be used for that
                for render_pass, out_name, exr_name, in_internal, in_cycles in rl_outputs:
                    pass_used = False  # initial value. Will be set to True if pass is used
                    if out.name == 'Alpha':
                        # Alpha output is always present. Doesn't have representation in render pass. Assume it's used.
                        pass_used = True
                    elif out.name == out_name:
                        # example 'render_pass' entry: 'use_pass_uv' Check if True in scene render layers
                        pass_used = getattr(active.scene.render.layers[active.layer], render_pass)
                        break
                if pass_used:
                    outputs.append(out)
        doit = True  # Will be changed to False when links successfully added to previous output.
        for out in outputs:
            if doit:
                for node in selected:
                    dst_name = node.name  # Will be compared with src_name if needed.
                    # When node has label - use it as dst_name
                    if node.label:
                        dst_name = node.label
                    valid = True  # Initial value. Will be changed to False if names don't match.
                    src_name = dst_name  # If names not used - this asignment will keep valid = True.
                    if use_node_name:
                        # Set src_name to source node name or label
                        src_name = active.name
                        if active.label:
                            src_name = active.label
                    elif use_outputs_names:
                        src_name = (out.name, )
                        for render_pass, out_name, exr_name, in_internal, in_cycles in rl_outputs:
                            if out.name in {out_name, exr_name}:
                                src_name = (out_name, exr_name)
                    if dst_name not in src_name:
                        valid = False
                    if valid:
                        for input in node.inputs:
                            if input.type == out.type or node.type == 'REROUTE':
                                if replace or not input.is_linked:
                                    links.new(out, input)
                                    if not use_node_name and not use_outputs_names:
                                        doit = False
                                    break

        return {'FINISHED'}


class AlignNodes(Operator, NodeToolBase):
    bl_idname = "node.align_nodes"
    bl_label = "Align nodes"
    bl_options = {'REGISTER', 'UNDO'}

    # option: 'Vertically', 'Horizontally'
    option = EnumProperty(
            name="option",
            description="Direction",
            items=(
                ('AXIS_X', "Align Vertically", 'Align Vertically'),
                ('AXIS_Y', "Aligh Horizontally", 'Aligh Horizontally'),
                )
            )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected = []  # entry = [index, loc.x, loc.y, width, height]
        frames_reselect = []  # entry = frame node. will be used to reselect all selected frames
        active = nodes.active
        for i, node in enumerate(nodes):
            if node.select:
                if node.type == 'FRAME':
                    node.select = False
                    frames_reselect.append(i)
                else:
                    locx = node.location.x
                    locy = node.location.y
                    parent = node.parent
                    while parent is not None:
                        locx += parent.location.x
                        locy += parent.location.y
                        parent = parent.parent
                    selected.append([i, locx, locy])
        count = len(selected)
        # add reroute node then scale all to 0.0 and calculate widths and heights of nodes
        if count > 1:  # aligning makes sense only if at least 2 nodes are selected
            helper = nodes.new('NodeReroute')
            helper.select = True
            bpy.ops.transform.resize(value=(0.0, 0.0, 0.0))
            # store helper's location for further calculations
            zero_x = helper.location.x
            zero_y = helper.location.y
            nodes.remove(helper)
            # helper is deleted but its location is stored
            # helper's width and height are 0.0.
            # Check loc of other nodes in relation to helper to calculate their dimensions
            # and append them to entries of "selected"
            total_w = 0.0  # total width of all nodes. Will be calculated later.
            total_h = 0.0  # total height of all nodes. Will be calculated later
            for j, [i, x, y] in enumerate(selected):
                locx = nodes[i].location.x
                locy = nodes[i].location.y
                # take node's parent (frame) into account. Get absolute location
                parent = nodes[i].parent
                while parent is not None:
                        locx += parent.location.x
                        locy += parent.location.y
                        parent = parent.parent
                width = abs((zero_x - locx) * 2.0)
                height = abs((zero_y - locy) * 2.0)
                selected[j].append(width)  # complete selected's entry for nodes[i]
                selected[j].append(height)  # complete selected's entry for nodes[i]
                total_w += width  # add nodes[i] width to total width of all nodes
                total_h += height  # add nodes[i] height to total height of all nodes
            selected_sorted_x = sorted(selected, key=lambda k: (k[1], -k[2]))
            selected_sorted_y = sorted(selected, key=lambda k: (-k[2], k[1]))
            min_x = selected_sorted_x[0][1]  # min loc.x
            min_x_loc_y = selected_sorted_x[0][2]  # loc y of node with min loc x
            min_x_w = selected_sorted_x[0][3]  # width of node with max loc x
            max_x = selected_sorted_x[count - 1][1]  # max loc.x
            max_x_loc_y = selected_sorted_x[count - 1][2]  # loc y of node with max loc.x
            max_x_w = selected_sorted_x[count - 1][3]  # width of node with max loc.x
            min_y = selected_sorted_y[0][2]  # min loc.y
            min_y_loc_x = selected_sorted_y[0][1]  # loc.x of node with min loc.y
            min_y_h = selected_sorted_y[0][4]  # height of node with min loc.y
            min_y_w = selected_sorted_y[0][3]  # width of node with min loc.y
            max_y = selected_sorted_y[count - 1][2]  # max loc.y
            max_y_loc_x = selected_sorted_y[count - 1][1]  # loc x of node with max loc.y
            max_y_w = selected_sorted_y[count - 1][3]  # width of node with max loc.y
            max_y_h = selected_sorted_y[count - 1][4]  # height of node with max loc.y

            if self.option == 'AXIS_Y':  # Horizontally. Equivelent of s -> x -> 0 with even spacing.
                loc_x = min_x
                #loc_y = (max_x_loc_y + min_x_loc_y) / 2.0
                loc_y = (max_y - max_y_h / 2.0 + min_y - min_y_h / 2.0) / 2.0
                offset_x = (max_x - min_x - total_w + max_x_w) / (count - 1)
                for i, x, y, w, h in selected_sorted_x:
                    nodes[i].location.x = loc_x
                    nodes[i].location.y = loc_y + h / 2.0
                    parent = nodes[i].parent
                    while parent is not None:
                        nodes[i].location.x -= parent.location.x
                        nodes[i].location.y -= parent.location.y
                        parent = parent.parent
                    loc_x += offset_x + w
            else:  # if self.option == 'AXIS_Y'
                #loc_x = (max_y_loc_x + max_y_w / 2.0 + min_y_loc_x + min_y_w / 2.0) / 2.0
                loc_x = (max_x + max_x_w / 2.0 + min_x + min_x_w / 2.0) / 2.0
                loc_y = min_y
                offset_y = (max_y - min_y + total_h - min_y_h) / (count - 1)
                for i, x, y, w, h in selected_sorted_y:
                    nodes[i].location.x = loc_x - w / 2.0
                    nodes[i].location.y = loc_y
                    parent = nodes[i].parent
                    while parent is not None:
                        nodes[i].location.x -= parent.location.x
                        nodes[i].location.y -= parent.location.y
                        parent = parent.parent
                    loc_y += offset_y - h

            # reselect selected frames
            for i in frames_reselect:
                nodes[i].select = True
            # restore active node
            nodes.active = active

        return {'FINISHED'}


class SelectParentChildren(Operator, NodeToolBase):
    bl_idname = "node.select_parent_child"
    bl_label = "Select Parent or Children"
    bl_options = {'REGISTER', 'UNDO'}

    option = EnumProperty(
            name="option",
            items=(
                ('PARENT', 'Select Parent', 'Select Parent Frame'),
                ('CHILD', 'Select Children', 'Select members of selected frame'),
                )
            )

    def execute(self, context):
        nodes, links = get_nodes_links(context)
        option = self.option
        selected = [node for node in nodes if node.select]
        if option == 'PARENT':
            for sel in selected:
                parent = sel.parent
                if parent:
                    parent.select = True
        else:  # option == 'CHILD'
            for sel in selected:
                children = [node for node in nodes if node.parent == sel]
                for kid in children:
                    kid.select = True

        return {'FINISHED'}


class DetachOutputs(Operator, NodeToolBase):
    bl_idname = "node.detach_outputs"
    bl_label = "Detach Outputs"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        nodes, links = get_nodes_links(context)
        selected = context.selected_nodes
        bpy.ops.node.duplicate_move_keep_inputs()
        new_nodes = context.selected_nodes
        bpy.ops.node.select_all(action="DESELECT")
        for node in selected:
            node.select = True
        bpy.ops.node.delete_reconnect()
        for new_node in new_nodes:
            new_node.select = True
        bpy.ops.transform.translate('INVOKE_DEFAULT')
        
        return {'FINISHED'}


class LinkToOutputNode(Operator, NodeToolBase):
    bl_idname = "nw.link_out"
    bl_label = "Connect to Output"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        return (space.type == 'NODE_EDITOR' and space.node_tree is not None and context.active_node is not None)
    
    def execute(self, context):
        nodes, links = get_nodes_links(context)
        active = nodes.active
        output_node = None
        tree_type = context.space_data.tree_type
        for node in nodes:
            if node.type in output_types:
                output_node = node
                break
        if not output_node:
            bpy.ops.node.select_all(action="DESELECT")
            if tree_type == 'ShaderNodeTree':
                output_node = nodes.new('ShaderNodeOutputMaterial')
            elif tree_type == 'CompositorNodeTree':
                output_node = nodes.new('CompositorNodeComposite')
            output_node.location.x = active.location.x + active.dimensions.x + 80
            output_node.location.y = active.location.y
        if (output_node and active.outputs):
            output_index = 0
            for i, output in enumerate(active.outputs):
                if output.type == output_node.inputs[0].type:
                    output_index = i
                    break

            out_input_index = 0
            if tree_type == 'ShaderNodeTree':
                if active.outputs[output_index].type != 'SHADER': # connect to displacement if not a shader
                    out_input_index = 2
            links.new(active.outputs[output_index], output_node.inputs[out_input_index])

        hack_force_update(nodes) # viewport render does not update

        return {'FINISHED'}


#############################################################
#  P A N E L S
#############################################################

class EfficiencyToolsPanel(Panel, NodeToolBase):
    bl_idname = "NODE_PT_efficiency_tools"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Efficiency Tools (Ctrl-SPACE)"
    
    prepend = StringProperty(
        name = 'prepend',
        )
    append = StringProperty()
    remove = StringProperty()

    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout

        box = layout.box()
        box.menu(MergeNodesMenu.bl_idname)
        if type == 'ShaderNodeTree':
            box.operator(NodesAddTextureSetup.bl_idname, text="Add Image Texture (Ctrl T)")
        box.menu(BatchChangeNodesMenu.bl_idname, text="Batch Change...")
        box.menu(NodeAlignMenu.bl_idname, text="Align Nodes (Shift =)")
        box.menu(CopyToSelectedMenu.bl_idname, text="Copy to Selected (Shift-C)")
        box.operator(NodesClearLabel.bl_idname).option = True
        box.operator(NodesModifyLabels.bl_idname)
        box.operator(DetachOutputs.bl_idname)
        box.menu(AddReroutesMenu.bl_idname, text="Add Reroutes ( / )")
        box.menu(NodesSwapMenu.bl_idname, text="Swap Nodes (Shift-S)")
        box.menu(LinkActiveToSelectedMenu.bl_idname, text="Link Active To Selected ( \\ )")
        box.operator(LinkToOutputNode.bl_idname)


#############################################################
#  M E N U S
#############################################################

class EfficiencyToolsMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_node_tools_menu"
    bl_label = "Efficiency Tools"

    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout
        layout.menu(MergeNodesMenu.bl_idname, text="Merge Selected Nodes")
        if type == 'ShaderNodeTree':
            layout.operator(NodesAddTextureSetup.bl_idname, text="Add Image Texture with coordinates")
        layout.menu(BatchChangeNodesMenu.bl_idname, text="Batch Change")
        layout.menu(NodeAlignMenu.bl_idname, text="Align Nodes")
        layout.menu(CopyToSelectedMenu.bl_idname, text="Copy to Selected")
        layout.operator(NodesClearLabel.bl_idname).option = True
        layout.operator(DetachOutputs.bl_idname)
        layout.menu(AddReroutesMenu.bl_idname, text="Add Reroutes")
        layout.menu(NodesSwapMenu.bl_idname, text="Swap Nodes")
        layout.menu(LinkActiveToSelectedMenu.bl_idname, text="Link Active To Selected")
        layout.operator(LinkToOutputNode.bl_idname)


class MergeNodesMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_merge_nodes_menu"
    bl_label = "Merge Selected Nodes"

    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout
        if type == 'ShaderNodeTree':
            layout.menu(MergeShadersMenu.bl_idname, text="Use Shaders")
        layout.menu(MergeMixMenu.bl_idname, text="Use Mix Nodes")
        layout.menu(MergeMathMenu.bl_idname, text="Use Math Nodes")


class MergeShadersMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_merge_shaders_menu"
    bl_label = "Merge Selected Nodes using Shaders"

    def draw(self, context):
        layout = self.layout
        for type in merge_shaders_types:
            props = layout.operator(MergeNodes.bl_idname, text=type)
            props.mode = type
            props.merge_type = 'SHADER'


class MergeMixMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_merge_mix_menu"
    bl_label = "Merge Selected Nodes using Mix"

    def draw(self, context):
        layout = self.layout
        for type, name, description in blend_types:
            props = layout.operator(MergeNodes.bl_idname, text=name)
            props.mode = type
            props.merge_type = 'MIX'


class MergeMathMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_merge_math_menu"
    bl_label = "Merge Selected Nodes using Math"

    def draw(self, context):
        layout = self.layout
        for type, name, description in operations:
            props = layout.operator(MergeNodes.bl_idname, text=name)
            props.mode = type
            props.merge_type = 'MATH'


class BatchChangeNodesMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_batch_change_nodes_menu"
    bl_label = "Batch Change Selected Nodes"

    def draw(self, context):
        layout = self.layout
        layout.menu(BatchChangeBlendTypeMenu.bl_idname)
        layout.menu(BatchChangeOperationMenu.bl_idname)


class BatchChangeBlendTypeMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_batch_change_blend_type_menu"
    bl_label = "Batch Change Blend Type"

    def draw(self, context):
        layout = self.layout
        for type, name, description in blend_types:
            props = layout.operator(BatchChangeNodes.bl_idname, text=name)
            props.blend_type = type
            props.operation = 'CURRENT'


class BatchChangeOperationMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_batch_change_operation_menu"
    bl_label = "Batch Change Math Operation"

    def draw(self, context):
        layout = self.layout
        for type, name, description in operations:
            props = layout.operator(BatchChangeNodes.bl_idname, text=name)
            props.blend_type = 'CURRENT'
            props.operation = type


class CopyToSelectedMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_copy_node_properties_menu"
    bl_label = "Copy to Selected"

    def draw(self, context):
        layout = self.layout
        layout.operator(NodesCopySettings.bl_idname, text="Settings from Active")
        layout.menu(CopyLabelMenu.bl_idname)


class CopyLabelMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_copy_label_menu"
    bl_label = "Copy Label"

    def draw(self, context):
        layout = self.layout
        layout.operator(NodesCopyLabel.bl_idname, text="from Active Node's Label").option = 'FROM_ACTIVE'
        layout.operator(NodesCopyLabel.bl_idname, text="from Linked Node's Label").option = 'FROM_NODE'
        layout.operator(NodesCopyLabel.bl_idname, text="from Linked Output's Name").option = 'FROM_SOCKET'


class AddReroutesMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_add_reroutes_menu"
    bl_label = "Add Reroutes"
    bl_description = "Add Reroute Nodes to Selected Nodes' Outputs"

    def draw(self, context):
        layout = self.layout
        layout.operator(NodesAddReroutes.bl_idname, text="to All Outputs").option = 'ALL'
        layout.operator(NodesAddReroutes.bl_idname, text="to Loose Outputs").option = 'LOOSE'
        layout.operator(NodesAddReroutes.bl_idname, text="to Linked Outputs").option = 'LINKED'


class NodesSwapMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_swap_menu"
    bl_label = "Swap Nodes"

    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout
        if type == 'ShaderNodeTree':
            layout.menu(ShadersSwapMenu.bl_idname, text="Swap Shaders")
        layout.operator(NodesSwap.bl_idname, text="Change to Mix Nodes").option = 'NodeMixRGB'
        layout.operator(NodesSwap.bl_idname, text="Change to Math Nodes").option = 'NodeMath'
        if type == 'CompositorNodeTree':
            layout.operator(NodesSwap.bl_idname, text="Change to Alpha Over").option = 'CompositorNodeAlphaOver'
        if type == 'CompositorNodeTree':
            layout.operator(NodesSwap.bl_idname, text="Change to Switches").option = 'CompositorNodeSwitch'
            layout.operator(NodesSwap.bl_idname, text="Change to Reroutes").option = 'NodeReroute'


class ShadersSwapMenu(Menu):
    bl_idname = "NODE_MT_shaders_swap_menu"
    bl_label = "Swap Shaders"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid = False
        if space.type == 'NODE_EDITOR':
            if space.tree_type == 'ShaderNodeTree' and space.node_tree is not None:
                valid = True
        return valid

    def draw(self, context):
        layout = self.layout
        shaders = merge_shaders + regular_shaders
        for opt, type, txt in shaders:
            layout.operator(NodesSwap.bl_idname, text=txt).option = opt


class LinkActiveToSelectedMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_link_active_to_selected_menu"
    bl_label = "Link Active to Selected"

    def draw(self, context):
        layout = self.layout
        layout.menu(LinkStandardMenu.bl_idname)
        layout.menu(LinkUseNodeNameMenu.bl_idname)
        layout.menu(LinkUseOutputsNamesMenu.bl_idname)


class LinkStandardMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_link_standard_menu"
    bl_label = "To All Selected"

    def draw(self, context):
        layout = self.layout
        props = layout.operator(NodesLinkActiveToSelected.bl_idname, text="Don't Replace Links")
        props.replace = False
        props.use_node_name = False
        props.use_outputs_names = False
        props = layout.operator(NodesLinkActiveToSelected.bl_idname, text="Replace Links")
        props.replace = True
        props.use_node_name = False
        props.use_outputs_names = False


class LinkUseNodeNameMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_link_use_node_name_menu"
    bl_label = "Use Node Name/Label"

    def draw(self, context):
        layout = self.layout
        props = layout.operator(NodesLinkActiveToSelected.bl_idname, text="Don't Replace Links")
        props.replace = False
        props.use_node_name = True
        props.use_outputs_names = False
        props = layout.operator(NodesLinkActiveToSelected.bl_idname, text="Replace Links")
        props.replace = True
        props.use_node_name = True
        props.use_outputs_names = False


class LinkUseOutputsNamesMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_link_use_outputs_names_menu"
    bl_label = "Use Outputs Names"

    def draw(self, context):
        layout = self.layout
        props = layout.operator(NodesLinkActiveToSelected.bl_idname, text="Don't Replace Links")
        props.replace = False
        props.use_node_name = False
        props.use_outputs_names = True
        props = layout.operator(NodesLinkActiveToSelected.bl_idname, text="Replace Links")
        props.replace = True
        props.use_node_name = False
        props.use_outputs_names = True


class NodeAlignMenu(Menu, NodeToolBase):
    bl_idname = "NODE_MT_node_align_menu"
    bl_label = "Align Nodes"

    def draw(self, context):
        layout = self.layout
        layout.operator(AlignNodes.bl_idname, text="Horizontally").option = 'AXIS_X'
        layout.operator(AlignNodes.bl_idname, text="Vertically").option = 'AXIS_Y'


#############################################################
#  MENU ITEMS
#############################################################

def select_parent_children_buttons(self, context):
    layout = self.layout
    layout.operator(SelectParentChildren.bl_idname, text="Select frame's members (children)").option = 'CHILD'
    layout.operator(SelectParentChildren.bl_idname, text="Select parent frame").option = 'PARENT'


#############################################################
#  APPENDAGES TO EXISTING UI
#############################################################

def uvs_menu_func(self, context):
    self.layout.menu("NODE_MT_node_uvs_menu")


def bgreset_menu_func(self, context):
    self.layout.operator("nw.bg_reset")


def showimage_menu_func(self, context):
    node = context.space_data.node_tree.nodes.active
    if node.type in ["IMAGE", "TEX_IMAGE", "TEX_ENVIRONMENT", "TEXTURE", "R_LAYERS", "MOVIECLIP", "VIEWER", "COMPOSITE", "MASK"]:
        txt = "View Image"
        if node.type in ['R_LAYERS', 'COMPOSITE']:
            txt = "View Render Result"
        elif node.type == 'MOVIECLIP':
            txt = "View Clip"
        elif node.type == 'MASK':
            txt = "Edit Mask"
        if node.type == 'TEXTURE':
            if node.texture.type != 'IMAGE':
                txt = 'INVALID'
        
        if txt != 'INVALID':
            self.layout.operator("nw.view_image", icon="UI", text=txt)


#############################################################
#  REGISTER/UNREGISTER CLASSES AND KEYMAP ITEMS
#############################################################

addon_keymaps = []
# kmi_defs entry: (identifier, key, CTRL, SHIFT, ALT, props, nice name)
# props entry: (property name, property value)
kmi_defs = (
    # MERGE NODES
    # MergeNodes with Ctrl (AUTO).
    (MergeNodes.bl_idname, 'NUMPAD_0', True, False, False,
        (('mode', 'MIX'), ('merge_type', 'AUTO'),), "Merge Nodes (Automatic)"),
    (MergeNodes.bl_idname, 'ZERO', True, False, False,
        (('mode', 'MIX'), ('merge_type', 'AUTO'),), "Merge Nodes (Automatic)"),
    (MergeNodes.bl_idname, 'NUMPAD_PLUS', True, False, False,
        (('mode', 'ADD'), ('merge_type', 'AUTO'),), "Merge Nodes (Add)"),
    (MergeNodes.bl_idname, 'EQUAL', True, False, False,
        (('mode', 'ADD'), ('merge_type', 'AUTO'),), "Merge Nodes (Add)"),
    (MergeNodes.bl_idname, 'NUMPAD_ASTERIX', True, False, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'AUTO'),), "Merge Nodes (Multiply)"),
    (MergeNodes.bl_idname, 'EIGHT', True, False, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'AUTO'),), "Merge Nodes (Multiply)"),
    (MergeNodes.bl_idname, 'NUMPAD_MINUS', True, False, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'AUTO'),), "Merge Nodes (Subtract)"),
    (MergeNodes.bl_idname, 'MINUS', True, False, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'AUTO'),), "Merge Nodes (Subtract)"),
    (MergeNodes.bl_idname, 'NUMPAD_SLASH', True, False, False,
        (('mode', 'DIVIDE'), ('merge_type', 'AUTO'),), "Merge Nodes (Divide)"),
    (MergeNodes.bl_idname, 'SLASH', True, False, False,
        (('mode', 'DIVIDE'), ('merge_type', 'AUTO'),), "Merge Nodes (Divide)"),
    (MergeNodes.bl_idname, 'COMMA', True, False, False,
        (('mode', 'LESS_THAN'), ('merge_type', 'MATH'),), "Merge Nodes (Less than)"),
    (MergeNodes.bl_idname, 'PERIOD', True, False, False,
        (('mode', 'GREATER_THAN'), ('merge_type', 'MATH'),), "Merge Nodes (Greater than)"),
    # MergeNodes with Ctrl Alt (MIX)
    (MergeNodes.bl_idname, 'NUMPAD_0', True, False, True,
        (('mode', 'MIX'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Mix)"),
    (MergeNodes.bl_idname, 'ZERO', True, False, True,
        (('mode', 'MIX'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Mix)"),
    (MergeNodes.bl_idname, 'NUMPAD_PLUS', True, False, True,
        (('mode', 'ADD'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Add)"),
    (MergeNodes.bl_idname, 'EQUAL', True, False, True,
        (('mode', 'ADD'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Add)"),
    (MergeNodes.bl_idname, 'NUMPAD_ASTERIX', True, False, True,
        (('mode', 'MULTIPLY'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Multiply)"),
    (MergeNodes.bl_idname, 'EIGHT', True, False, True,
        (('mode', 'MULTIPLY'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Multiply)"),
    (MergeNodes.bl_idname, 'NUMPAD_MINUS', True, False, True,
        (('mode', 'SUBTRACT'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Subtract)"),
    (MergeNodes.bl_idname, 'MINUS', True, False, True,
        (('mode', 'SUBTRACT'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Subtract)"),
    (MergeNodes.bl_idname, 'NUMPAD_SLASH', True, False, True,
        (('mode', 'DIVIDE'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Divide)"),
    (MergeNodes.bl_idname, 'SLASH', True, False, True,
        (('mode', 'DIVIDE'), ('merge_type', 'MIX'),), "Merge Nodes (Color, Divide)"),
    # MergeNodes with Ctrl Shift (MATH)
    (MergeNodes.bl_idname, 'NUMPAD_PLUS', True, True, False,
        (('mode', 'ADD'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Add)"),
    (MergeNodes.bl_idname, 'EQUAL', True, True, False,
        (('mode', 'ADD'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Add)"),
    (MergeNodes.bl_idname, 'NUMPAD_ASTERIX', True, True, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Multiply)"),
    (MergeNodes.bl_idname, 'EIGHT', True, True, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Multiply)"),
    (MergeNodes.bl_idname, 'NUMPAD_MINUS', True, True, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Subtract)"),
    (MergeNodes.bl_idname, 'MINUS', True, True, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Subtract)"),
    (MergeNodes.bl_idname, 'NUMPAD_SLASH', True, True, False,
        (('mode', 'DIVIDE'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Divide)"),
    (MergeNodes.bl_idname, 'SLASH', True, True, False,
        (('mode', 'DIVIDE'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Divide)"),
    (MergeNodes.bl_idname, 'COMMA', True, True, False,
        (('mode', 'LESS_THAN'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Less than)"),
    (MergeNodes.bl_idname, 'PERIOD', True, True, False,
        (('mode', 'GREATER_THAN'), ('merge_type', 'MATH'),), "Merge Nodes (Math, Greater than)"),
    # BATCH CHANGE NODES
    # BatchChangeNodes with Alt
    (BatchChangeNodes.bl_idname, 'NUMPAD_0', False, False, True,
        (('blend_type', 'MIX'), ('operation', 'CURRENT'),), "Batch change blend type (Mix)"),
    (BatchChangeNodes.bl_idname, 'ZERO', False, False, True,
        (('blend_type', 'MIX'), ('operation', 'CURRENT'),), "Batch change blend type (Mix)"),
    (BatchChangeNodes.bl_idname, 'NUMPAD_PLUS', False, False, True,
        (('blend_type', 'ADD'), ('operation', 'ADD'),), "Batch change blend type (Add)"),
    (BatchChangeNodes.bl_idname, 'EQUAL', False, False, True,
        (('blend_type', 'ADD'), ('operation', 'ADD'),), "Batch change blend type (Add)"),
    (BatchChangeNodes.bl_idname, 'NUMPAD_ASTERIX', False, False, True,
        (('blend_type', 'MULTIPLY'), ('operation', 'MULTIPLY'),), "Batch change blend type (Multiply)"),
    (BatchChangeNodes.bl_idname, 'EIGHT', False, False, True,
        (('blend_type', 'MULTIPLY'), ('operation', 'MULTIPLY'),), "Batch change blend type (Multiply)"),
    (BatchChangeNodes.bl_idname, 'NUMPAD_MINUS', False, False, True,
        (('blend_type', 'SUBTRACT'), ('operation', 'SUBTRACT'),), "Batch change blend type (Subtract)"),
    (BatchChangeNodes.bl_idname, 'MINUS', False, False, True,
        (('blend_type', 'SUBTRACT'), ('operation', 'SUBTRACT'),), "Batch change blend type (Subtract)"),
    (BatchChangeNodes.bl_idname, 'NUMPAD_SLASH', False, False, True,
        (('blend_type', 'DIVIDE'), ('operation', 'DIVIDE'),), "Batch change blend type (Divide)"),
    (BatchChangeNodes.bl_idname, 'SLASH', False, False, True,
        (('blend_type', 'DIVIDE'), ('operation', 'DIVIDE'),), "Batch change blend type (Divide)"),
    (BatchChangeNodes.bl_idname, 'COMMA', False, False, True,
        (('blend_type', 'CURRENT'), ('operation', 'LESS_THAN'),), "Batch change blend type (Current)"),
    (BatchChangeNodes.bl_idname, 'PERIOD', False, False, True,
        (('blend_type', 'CURRENT'), ('operation', 'GREATER_THAN'),), "Batch change blend type (Current)"),
    (BatchChangeNodes.bl_idname, 'DOWN_ARROW', False, False, True,
        (('blend_type', 'NEXT'), ('operation', 'NEXT'),), "Batch change blend type (Next)"),
    (BatchChangeNodes.bl_idname, 'UP_ARROW', False, False, True,
        (('blend_type', 'PREV'), ('operation', 'PREV'),), "Batch change blend type (Previous)"),
    # LINK ACTIVE TO SELECTED
    # Don't use names, don't replace links (K)
    (NodesLinkActiveToSelected.bl_idname, 'K', False, False, False,
        (('replace', False), ('use_node_name', False), ('use_outputs_names', False),), "Link active to selected (Don't replace links)"),
    # Don't use names, replace links (Shift K)
    (NodesLinkActiveToSelected.bl_idname, 'K', False, True, False,
        (('replace', True), ('use_node_name', False), ('use_outputs_names', False),), "Link active to selected (Replace links)"),
    # Use node name, don't replace links (')
    (NodesLinkActiveToSelected.bl_idname, 'QUOTE', False, False, False,
        (('replace', False), ('use_node_name', True), ('use_outputs_names', False),), "Link active to selected (Don't replace links, node names)"),
    # Use node name, replace links (Shift ')
    (NodesLinkActiveToSelected.bl_idname, 'QUOTE', False, True, False,
        (('replace', True), ('use_node_name', True), ('use_outputs_names', False),), "Link active to selected (Replace links, node names)"),
    # Don't use names, don't replace links (;)
    (NodesLinkActiveToSelected.bl_idname, 'SEMI_COLON', False, False, False,
        (('replace', False), ('use_node_name', False), ('use_outputs_names', True),), "Link active to selected (Don't replace links, output names)"),
    # Don't use names, replace links (')
    (NodesLinkActiveToSelected.bl_idname, 'SEMI_COLON', False, True, False,
        (('replace', True), ('use_node_name', False), ('use_outputs_names', True),), "Link active to selected (Replace links, output names)"),
    # CHANGE MIX FACTOR
    (ChangeMixFactor.bl_idname, 'LEFT_ARROW', False, False, True, (('option', -0.1),), "Reduce Mix Factor by 0.1"),
    (ChangeMixFactor.bl_idname, 'RIGHT_ARROW', False, False, True, (('option', 0.1),), "Increase Mix Factor by 0.1"),
    (ChangeMixFactor.bl_idname, 'LEFT_ARROW', False, True, True, (('option', -0.01),), "Reduce Mix Factor by 0.01"),
    (ChangeMixFactor.bl_idname, 'RIGHT_ARROW', False, True, True, (('option', 0.01),), "Increase Mix Factor by 0.01"),
    (ChangeMixFactor.bl_idname, 'LEFT_ARROW', True, True, True, (('option', 0.0),), "Set Mix Factor to 0.0"),
    (ChangeMixFactor.bl_idname, 'RIGHT_ARROW', True, True, True, (('option', 1.0),), "Set Mix Factor to 1.0"),
    (ChangeMixFactor.bl_idname, 'NUMPAD_0', True, True, True, (('option', 0.0),), "Set Mix Factor to 0.0"),
    (ChangeMixFactor.bl_idname, 'ZERO', True, True, True, (('option', 0.0),), "Set Mix Factor to 0.0"),
    (ChangeMixFactor.bl_idname, 'NUMPAD_1', True, True, True, (('option', 1.0),), "Mix Factor to 1.0"),
    (ChangeMixFactor.bl_idname, 'ONE', True, True, True, (('option', 1.0),), "Set Mix Factor to 1.0"),
    # CLEAR LABEL (Alt L)
    (NodesClearLabel.bl_idname, 'L', False, False, True, (('option', False),), "Clear node labels"),
    # MODIFY LABEL (Alt Shift L)
    (NodesModifyLabels.bl_idname, 'L', False, True, True, None, "Modify node labels"),
    # Copy Label from active to selected
    (NodesCopyLabel.bl_idname, 'V', False, True, False, (('option', 'FROM_ACTIVE'),), "Copy label from active to selected"),
    # DETACH OUTPUTS (Alt Shift D)
    (DetachOutputs.bl_idname, 'D', False, True, True, None, "Detach outputs"),
    # LINK TO OUTPUT NODE (O)
    (LinkToOutputNode.bl_idname, 'O', False, False, False, None, "Link to output node"),
    # SELECT PARENT/CHILDREN
    # Select Children
    (SelectParentChildren.bl_idname, 'RIGHT_BRACKET', False, False, False, (('option', 'CHILD'),), "Select children"),
    # Select Parent
    (SelectParentChildren.bl_idname, 'LEFT_BRACKET', False, False, False, (('option', 'PARENT'),), "Select Parent"),
    # Add Texture Setup
    (NodesAddTextureSetup.bl_idname, 'T', True, False, False, None, "Add texture setup"),
    # Reset backdrop
    ('nw.bg_reset', 'Z', False, False, False, None, "Reset backdrop image zoom"),
    # Auto-Arrange
    ('nw.layout', 'Q', False, False, False, None, "Arrange nodes"),
    # Delete unused
    ('nw.del_unused', 'X', False, False, True, None, "Delete unused nodes"),
    # Frame Seleted
    ('nw.frame_selected', 'P', False, True, False, None, "Frame selected nodes"),
    # Swap Outputs
    ('nw.swap_outputs', 'S', False, False, True, None, "Swap Outputs"),
    # Emission Viewer
    ('nw.emission_viewer', 'LEFTMOUSE', True, True, False, None, "Connect to Cycles Viewer node"),
    # Reload Images
    ('nw.reload_images', 'R', False, False, True, None, "Reload images"),
    # Interactive Mix
    ('nw.mix_nodes', 'RIGHTMOUSE', False, False, True, None, "Lazy Mix"),
    # Lazy Connect
    ('nw.lazy_connect', 'LEFTMOUSE', False, False, True, None, "Lazy Connect"),
    # MENUS
    ('wm.call_menu', 'SPACE', True, False, False, (('name', EfficiencyToolsMenu.bl_idname),), "Node Wranger menu"),
    ('wm.call_menu', 'SLASH', False, False, False, (('name', AddReroutesMenu.bl_idname),), "Add Reroutes menu"),
    ('wm.call_menu', 'NUMPAD_SLASH', False, False, False, (('name', AddReroutesMenu.bl_idname),), "Add Reroutes menu"),
    ('wm.call_menu', 'EQUAL', False, True, False, (('name', NodeAlignMenu.bl_idname),), "Node alignment menu"),
    ('wm.call_menu', 'BACK_SLASH', False, False, False, (('name', LinkActiveToSelectedMenu.bl_idname),), "Link active to selected (menu)"),
    ('wm.call_menu', 'C', False, True, False, (('name', CopyToSelectedMenu.bl_idname),), "Copy to selected (menu)"),
    ('wm.call_menu', 'S', False, True, False, (('name', NodesSwapMenu.bl_idname),), "Swap node menu"),
    )


def register():
    # props
    bpy.types.Scene.NWStartAlign = bpy.props.BoolProperty(
        name="Align Start Nodes",
        default=True,
        description="Put all nodes with no inputs on the left of the tree")
    bpy.types.Scene.NWEndAlign = bpy.props.BoolProperty(
        name="Align End Nodes",
        default=True,
        description="Put all nodes with no outputs on the right of the tree")
    bpy.types.Scene.NWSpacing = bpy.props.FloatProperty(
        name="Spacing",
        default=80.0,
        min=0.0,
        description="The horizonal space between nodes (vertical is half this)")
    bpy.types.Scene.NWDelReroutes = bpy.props.BoolProperty(
        name="Delete Reroutes",
        default=True,
        description="Delete all Reroute nodes to avoid unexpected layouts")
    bpy.types.Scene.NWFrameHandling = bpy.props.EnumProperty(
        name="Frames",
        items=(("ignore", "Ignore", "Do nothing about Frame nodes (can be messy)"), ("delete", "Delete", "Delete Frame nodes")),
        default='ignore',
        description="How to handle Frame nodes")
    bpy.types.Scene.NWBusyDrawing = bpy.props.StringProperty(
        name="Busy Drawing!",
        default="",
        description="An internal property used to store only the first mouse position")
    bpy.types.Scene.NWDrawColType = bpy.props.StringProperty(
        name="Color Type!",
        default="x",
        description="An internal property used to store the line color")

    bpy.utils.register_module(__name__)

    # keymaps
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Node Editor', space_type="NODE_EDITOR")
    for (identifier, key, CTRL, SHIFT, ALT, props, nicename) in kmi_defs:
        kmi = km.keymap_items.new(identifier, key, 'PRESS', ctrl=CTRL, shift=SHIFT, alt=ALT)
        if props:
            for prop, value in props:
                setattr(kmi.properties, prop, value)
        addon_keymaps.append((km, kmi))

    # menu items
    bpy.types.NODE_MT_select.append(select_parent_children_buttons)
    bpy.types.NODE_MT_category_SH_NEW_INPUT.prepend(uvs_menu_func)
    bpy.types.NODE_PT_backdrop.append(bgreset_menu_func)
    bpy.types.NODE_PT_active_node_properties.append(showimage_menu_func)


def unregister():
    # props
    del bpy.types.Scene.NWStartAlign
    del bpy.types.Scene.NWEndAlign
    del bpy.types.Scene.NWSpacing
    del bpy.types.Scene.NWDelReroutes
    del bpy.types.Scene.NWFrameHandling
    del bpy.types.Scene.NWBusyDrawing
    del bpy.types.Scene.NWDrawColType

    bpy.utils.unregister_module(__name__)

    # keymaps
    bpy.types.NODE_MT_select.remove(select_parent_children_buttons)
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # menuitems
    bpy.types.NODE_MT_select.remove(select_parent_children_buttons)
    bpy.types.NODE_MT_category_SH_NEW_INPUT.remove(uvs_menu_func)
    bpy.types.NODE_PT_backdrop.remove(bgreset_menu_func)
    bpy.types.NODE_PT_active_node_properties.remove(showimage_menu_func)

if __name__ == "__main__":
    register()