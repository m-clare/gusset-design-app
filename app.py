import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq

from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State

import dash_flexbox_grid as dfx
import plotly.graph_objs as go
import sd_material_ui as mui
import json

# gusset design info
from gusset_design.elements.gusset_node import GussetNode
from gusset_design.elements.gusset_plate import GussetPlate
from gusset_design.visualization.plotly2D import PlotlyLineXY

from numpy import tan
from numpy import sin
from numpy import cos
from numpy import radians

# Compas classes
from compas.geometry import Point
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Vector

# Compas methods
from compas.geometry import angle_points
from compas.geometry import translate_points_xy
from compas.geometry import translate_points
from compas.geometry import offset_line
from compas.geometry import intersection_line_line_xy
from compas.geometry import distance_point_point
from compas.geometry.transformations.transformations import mirror_point_line
from compas.geometry.xforms.transformation import Transformation

app = dash.Dash(
    __name__,
    meta_tags=[{'name': 'viewport',
                'content': 'Width=device-width, initial-scale=1'}]
    )

server = app.server
# app.config['suppress_callback_exceptions'] = True
app.config.suppress_callback_exceptions = True

#  ----------------------------------------------------------------------------
#  Components
#  ----------------------------------------------------------------------------

test = GussetNode.from_json('../gusset_design/examples/sample_node.json')
# initialize gusset node
gusset_node = None

def build_app_banner():
    return html.Div(
        id='banner',
        className='banner',
        children=[
            html.Div(
                id='banner-text',
                children=[
                    html.H1('Gusset Design')
                ],
            )
        ]
    )


def build_main_app():
    return html.Div(id='main-app', children=[
                html.Div(className='row', children=[
                    html.Div(className='six columns', children=[
                        build_io_panel()
                        ]),
                    html.Div(className='six columns', children=[
                        dcc.Graph(figure=generate_visualization(test))
                        ])
                    ])
                ])


def build_tabs():
    categories = ['Main', 'Report']
    category_tabs = []
    for category in categories:
        category_tab = dcc.Tab(id=category + '-tab',
                               label=category,
                               value=category,
                               className='custom-tab',
                               selected_className=category +
                               '-custom-tab--selected',
                               children=[build_tab(category)])
        category_tabs.append(category_tab)
    return html.Div(
        id='tabs',
        className='twelve columns',
        children=[
            dcc.Tabs(
                id='app-tabs',
                value='Main',
                className='custom-tabs',
                children=category_tabs
                )
            ]
        )


def build_tab(category):
    if category == 'Main':
        return html.Div(className='pretty container', children=[
                    html.Div(className='row', children=[
                            html.Div(className='six columns', children=[
                                build_io_panel()
                                ]),
                            html.Div(className='six columns', children=[
                                build_adjustment_panel()
                                ])
                            ])
                    ])
    elif category == 'Report':
        return html.Div(className='row', children=[
                    html.Div(className='six columns', children=[html.Div()]),
                    html.Div(className='six columns', children=[html.Div()])
            ])


def build_io_panel():
    return html.Div(id='io-panel',
                    style={'justify-content': 'center'},
                    className='pretty container',
                    children=[
                        build_assembly_input(),
                        html.Br(),
                        mui.Divider(),
                        html.Br(),
                    ])


def build_adjustment_panel():
    return html.Div(id='adjust-panel',
                    style={'justify-content': 'center'},
                    className='pretty container',
                    children=[
                        build_gusset_parameters(),
                        html.Br(),
                        mui.Divider(),
                        html.Div(id='store-contents',
                                 style={'font-variant': 'small-caps',
                                        'justify-content': 'left'}),
                        build_design_checks(),
                    ])


slider_marks = {12: '12', 16: '16', 20: '20', 24: '24', 28: '28',
                32: '32', 36: '36', 40: '40'}


def build_assembly_input():
    return html.Div(id='assembly',
                    children=[
                        html.Div(id='load-gusset-assembly',
                                 className='interior container',
                                 children=[
                                    html.H3('Assembly'),
                                    dcc.Input(
                                        id='assembly-input-field',
                                        type='text',
                                        placeholder='filepath/to/assembly.json',
                                        style={'width': '100%'}
                                    ),
                                    html.Div(style={'font-variant': 'small-caps'},
                                             children=[
                                                'Filepath'
                                            ]),
                                    html.Br(),
                                    html.Button('Submit', id='input-button'),
                                    ])
                        ])


def build_gusset_parameters():
    return html.Div(className='interior container',
                    children=[
                        html.H4('Gusset Parameters'),
                        html.Div(id='gusset-l2-value',
                                 style={'font-variant': 'small-caps',
                                        'justify-content': 'left'}),
                        html.Div(className='row', children=[
                            html.Div(className='two columns',
                                     style={'justify-content': 'center'},
                                     children=[
                                        html.Div(style={'margin': '1em', 'height': '400px'},
                                                 children=[
                                                    dcc.Slider(
                                                        id='l2-slider',
                                                        min=12,
                                                        max=40,
                                                        step=0.5,
                                                        value=24,
                                                        marks=slider_marks,
                                                        vertical=True,
                                                    )
                                                 ])
                                            ]),
                            html.Div(className='ten columns',
                                     children=[
                                        html.Div(className='row', children=[
                                            html.Div(className='twelve columns', children=[
                                                dcc.Graph(
                                                    id='plotly-2d-graph',
                                                    figure=create_default_plotly2d()),
                                                html.Div(style={'margin': '1em'},
                                                         children=[
                                                            dcc.Slider(
                                                                id='l1-slider',
                                                                min=12,
                                                                max=40,
                                                                step=0.5,
                                                                value=24,
                                                                marks=slider_marks)
                                                         ]),
                                                html.Br(),
                                                html.Div(id='gusset-l1-value',
                                                         style={'font-variant': 'small-caps',
                                                                'justify-content': 'left'}),
                                                ])
                                            ])
                                        ])
                                    ])
                        ])


def build_design_checks():
    return html.Div(id='gusset-design-checks',
                    children=[
                    html.H4('Design Checks'),
                    dfx.Row(center='xs',
                        children=[
                        html.Div(className='row', children=[
                            html.Div(className='four columns', children=[
                                html.H6('Beam Interface')
                                ]),
                            html.Div(className='eight columns', children=[
                                generate_beam_dcr_indicators()
                                ])
                            ]),
                        ]),
                    dfx.Row(center='xs',
                        children=[
                        html.Div(className='row', children=[
                            html.Div(className='four columns', children=[
                                html.H6('Column Interface')
                                ]),
                            html.Div(className='eight columns', children=[
                                generate_column_dcr_indicators()
                                ])
                            ]),
                        ]),
                    ])


dcr_list = ['axial-tension', 'moment', 'in-plane-shear',
            'out-of-plane-shear', 'Von-Mises']

dcr_key = {'axial-tension': 'P (+)', 'moment': 'M', 'in-plane-shear': 'V1', 
           'out-of-plane-shear': 'V2', 'Von-Mises': 'VM'}

def generate_beam_dcr_indicators():
    circles = [create_dcr_indicator('beam-' + item) for item in dcr_list]
    return dfx.Row(children=circles)

def generate_column_dcr_indicators():
    circles = [create_dcr_indicator('column-' + item) for item in dcr_list]
    return dfx.Row(children=circles,
                   center='xs')
# def generate_dcr_indicators():
#     circles = [create_dcr_indicator(item) for item in dcr_list]
#     return dfx.Row(children=circles,
#                    center='xs')

def create_dcr_indicator(item):
    id_abbrev = (item).split('-', 1)[1]
    circle = daq.Indicator(
             id=item + '-indicator',
             label=dcr_key[id_abbrev],
             value=True,
             color= "#000000"
             )
    styled_circle = html.Div(id=item + '-circle-container', style={'margin': '1em'},
                             children=[circle])
    circle_div = dfx.Col(children=[
                    styled_circle,
                    html.Div(id=item + '-circle-value')
                    ])
    return circle_div

# def generate_dcr_indicators():
#     bars = [create_dcr_indicator(item) for item in dcr_list]
#     return dfx.Row(children=bars,
#                    center='xs')


# def create_dcr_indicator(item):
#     bar = daq.GraduatedBar(
#           id=item + '-indicator',
#           color={'gradient': True, 'ranges': {'green': [0, 85],
#                  'yellow': [85, 95], 'red': [95, 100]}},
#           showCurrentValue=True,
#           max=100,
#           value=90,
#           vertical=True,
#           step=1,
#           )
#     styled_bar = html.Div(id=item + '-bar-container', style={'margin': '1em'},
#                           children=bar)
#     bar_div = dfx.Col(children=[
#                 styled_bar,
#                 html.Div(id=item + '-bar-value')])
#     return bar_div


def create_default_plotly2d():
    figure = go.Figure(data={'x': [0], 'y': [0]})
    figure.update_layout(yaxis=dict(scaleanchor="x", scaleratio=1),
                         paper_bgcolor='rgba(0,0,0,0)',
                         plot_bgcolor='rgba(0,0,0,0)',
                         showlegend=False,
                         margin=dict(l=10, t=10, b=10))
    figure.update_xaxes(range=[0, 80], showgrid=False, zeroline=False, showticklabels=False)
    figure.update_yaxes(range=[0, 80], showgrid=False, zeroline=False, showticklabels=False)
    return figure

def build_visualization_panel():
    pass


def build_gusset_node_visualization():
    pass


def build_guidelines_visualization():
    pass


def build_outline_visualization():
    pass


def generate_visualization(GussetNode):
    meshes = GussetNode.to_meshes()
    fig = go.Figure(data=meshes)
    fig.update_layout(scene_aspectmode='data')
    return fig


def generate_3d_visualization(filepath):
    meshes = GussetNode.to_meshes()
    fig = go.Figure(data=meshes)
    fig.update_layout(scene_aspectmode='data')
    return fig

#  ----------------------------------------------------------------------------
#  Calculations
#  ----------------------------------------------------------------------------


def to_plotly_xy(line):
    x, y = [], []
    if len(line) == 2:
        pt0 = line[0]
        pt1 = line[1]
        gusset_guideline = {'x': [pt0[0], pt1[0]], 'y': [pt0[1], pt1[1]]}
        return gusset_guideline

#  ----------------------------------------------------------------------------
#  Layout
#  ----------------------------------------------------------------------------

app.layout = html.Div(id='grid', className='container', children=[
                mui.Paper(children=[
                    html.Div(className='row', children=[
                        html.Div(dcc.Store(id='local', storage_type='local')),
                        html.Div(className='twelve columns',
                                 children=[
                                    html.Div(id='app-container',
                                             children=[
                                                build_app_banner(),
                                                html.Div(children=[
                                                    build_tab('Main'),
                                                    ])
                                                ])
                                 ])
                        ])
                    ])
                ])

#  ----------------------------------------------------------------------------
#  Callbacks
#  ----------------------------------------------------------------------------

# Slider / Text Values
@app.callback(
    Output(component_id='gusset-l1-value', component_property='children'),
    [Input(component_id='l1-slider', component_property='value')]
)
def update_l1_textbox_value(input_value):
    return '{} inches'.format(input_value)


@app.callback(
    Output(component_id='gusset-l2-value', component_property='children'),
    [Input(component_id='l2-slider', component_property='value')]
)
def update_l2_textbox_value(input_value):
    return '{} inches'.format(input_value)


@app.callback(
    [Output(component_id='store-contents', component_property='children'),
     Output('local', 'data')],
    [Input('input-button', 'n_clicks')],
    [State('assembly-input-field', 'value')]
)
def load_gusset_assembly(n_clicks, filepath):
    if n_clicks is None:
        raise PreventUpdate
    elif filepath is None:
        raise PreventUpdate
    else:
        gusset_node = GussetNode.from_json(filepath)
        gusset = GussetPlate(gusset_node.braces[0], gusset_node.column[0],
                             gusset_node.beams[0], 'i', brace_angle=37.6)
        V_c, H_c, M_c, V_b, H_b, M_b = gusset.calculate_interface_forces(400.)
        gusset_dict = {'eb': gusset.eb, 'ec': gusset.ec,
                       'offset': gusset.offset,
                       'design_angle': gusset.design_angle,
                       'brace_depth': gusset.get_brace_depth(),
                       'connection_length': gusset.connection_length,
                       'force': 400.,
                       'V_c': V_c,
                       'H_c': H_c,
                       'M_c': M_c,
                       'V_b': V_b,
                       'H_b': H_b,
                       'M_b': M_b}
        return gusset_dict, gusset_dict


hc_forces = {'V_c': 181.14828930285879, 'H_c': 94.52172458426533, 'M_c': -112.39593118392548, 'V_b': 135.76756803921745, 'H_b': 149.53634097624172, 'M_b': 108.85293208805035}


@app.callback(
    [Output('beam-axial-tension-indicator', 'color'),
     Output('beam-axial-tension-circle-value', 'children')],
    [Input('l1-slider', 'value')]
    #  Input('local', 'modified_timestamp')],
    # [State('local', 'data')]
    )
def get_axial_tension_dcr(l1):
    # if ts is None:
    #     raise PreventUpdate
    # data = gusset_data or {}
    # p_u = gusset_data['V_b']
    p_u = hc_forces['V_b']
    thickness = 1.
    phi_Pn = 0.9 * 50 * l1 * thickness
    at_dcr = p_u / phi_Pn
    if at_dcr > 0.95:
        color = 'red'
    elif at_dcr > 0.85:
        color = 'yellow'
    else:
        color = 'green'
    return color, "{:.0%}".format(at_dcr)

@app.callback(
    Output('beam-axial-compression-indicator', 'value'),
    [Input('l1-slider', 'value')]
    #  Input('local', 'modified_timestamp')],
    # [State('local', 'data')]
    )
def get_axial_tension_dcr(l1):
    # if ts is None:
    #     raise PreventUpdate
    # data = gusset_data or {}
    # p_u = gusset_data['V_b']
    p_u = hc_forces['V_b']
    thickness = 1.
    phi_Pn = 0.9 * 50 * l1 * thickness
    at_dcr = p_u / phi_Pn
    return at_dcr

@app.callback(
     Output('plotly-2d-graph', 'figure'),
     [Input('l1-slider', 'value'),
      Input('l2-slider', 'value'),
      Input('local', 'modified_timestamp')],
     [State('local', 'data')]
)
def update_2d_plot(l1, l2, ts, gusset_data):
    if ts is None:
        raise PreventUpdate
    data = gusset_data or {}
    gusset_lines = []
    work_point = [0, 0, 0]
    pt0 = list(Point(data['eb'], data['ec']))
    pt1 = translate_points_xy([pt0], Vector(l1, 0, 0))[0]
    pt2 = translate_points_xy([pt1], Vector(0, data['offset'], 0))[0]
    pt6 = translate_points_xy([pt0], Vector(0, l2, 0))[0]
    pt5 = translate_points_xy([pt6], Vector(data['offset'], 0, 0))[0]

    # Brace CL
    brace_vector = Vector(sin(radians(data['design_angle'])),
                          cos(radians(data['design_angle'])), 0)
    brace_vector.unitize()
    brace_vector.scale(200)
    brace_pt = translate_points_xy([work_point], brace_vector)[0]
    test = brace_vector.copy()
    test.scale(1)
    brace_pt_out = translate_points_xy([work_point], test)[0]
    brace_CL = Line([0, 0, 0], brace_pt)

    gusset_lines.append(Line([0, 0, 0], brace_pt_out))

    brace_vector.unitize()
    brace_vector.scale(data['connection_length'])


    # Brace shoulder lines
    brace_depth = data['brace_depth']
    column_offset = brace_depth * 0.5 + data['offset']
    beam_offset = -(brace_depth * 0.5 + data['offset'])
    column_line = Line(pt5, Point(pt5[0], 0, 0))
    beam_line = Line(pt2, Point(0, pt2[1], 0))

    gusset_lines.append(column_line)
    gusset_lines.append(beam_line)

    def get_brace_points(offset_value, offset_member,
                         brace_CL, brace_vector, offset_dir='+'):
        offset_brace = offset_line(brace_CL, offset_value)
        if offset_dir == '+':
            offset_brace_signed = offset_line(brace_CL, offset_value - data['offset'])
        elif offset_dir == '-':
            offset_brace_signed = offset_line(brace_CL, offset_value + data['offset'])
        else: 
            raise ValueError

        brace_member_int = intersection_line_line_xy(offset_brace,
                                                     offset_member)
        brace_pt = translate_points_xy([brace_member_int], brace_vector)[0]
        pt_mirrored = mirror_point_line(brace_pt, brace_CL)
        line_segment = Line(brace_pt, pt_mirrored)
        pt_CL = intersection_line_line_xy(line_segment, brace_CL)
        pt_distance = distance_point_point(work_point, pt_CL)
        return line_segment, pt_distance, offset_brace, offset_brace_signed

    column_line, col_dist, os_brace_column, os_column = get_brace_points(column_offset, column_line,
                                                                         brace_CL, brace_vector, offset_dir='+')
    beam_line, beam_dist, os_brace_beam, os_beam = get_brace_points(beam_offset, beam_line,
                                            brace_CL, brace_vector, offset_dir='-')

    gusset_lines.append(os_brace_column)
    gusset_lines.append(os_brace_beam)
    gusset_lines.append(os_column)
    gusset_lines.append(os_beam)
    gusset_lines.append(column_line)
    gusset_lines.append(beam_line)

    if col_dist > beam_dist:
        pt3 = column_line[1]
        pt4 = column_line[0]
    else:
        pt3 = beam_line[0]
        pt4 = beam_line[1]

    # set check to make sure gusset is non concave (force points to line
    # between pt2 and pt5)
    # Points list to point
    pt0 = Point(pt0[0], pt0[1], pt0[2])
    pt1 = Point(pt1[0], pt1[1], pt1[2])
    pt2 = Point(pt2[0], pt2[1], pt2[2])
    pt6 = Point(pt6[0], pt6[1], pt6[2])
    pt5 = Point(pt5[0], pt5[1], pt5[2])
    pt3 = Point(pt3[0], pt3[1], pt3[2])
    pt4 = Point(pt4[0], pt4[1], pt4[2])

    gusset_points = [pt0, pt1, pt2, pt3, pt4, pt5, pt6, pt0]

    x = []
    y = []
    for pt in gusset_points:
        x.append(pt[0])
        y.append(pt[1])
    gusset_outline = {'x': x, 'y': y}
    plotly_styled = PlotlyLineXY.from_geometry(gusset_outline)
    gusset_lines_styled = [plotly_styled]
    for line in gusset_lines:
        line_formatted = to_plotly_xy(line)
        line_info = PlotlyLineXY.from_geometry(line_formatted, line={'color': 'gray', 'dash': 'dash'})
        gusset_lines_styled.append(line_info)
    figure = go.Figure(data=gusset_lines_styled)
    figure.update_layout(yaxis=dict(scaleanchor="x", scaleratio=1),
                         paper_bgcolor='rgba(0,0,0,0)',
                         plot_bgcolor='rgba(0,0,0,0)',
                         showlegend=False,
                         margin=dict(l=10, t=10, b=10))
    figure.update_xaxes(range=[0, 80], showgrid=False, zeroline=False, showticklabels=False)
    figure.update_yaxes(range=[0, 80], showgrid=False, zeroline=False, showticklabels=False)
    return figure


if __name__ =='__main__':
    app.run_server(debug=True, port=8050)