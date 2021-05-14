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
from numpy import abs
from numpy import sqrt

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
from compas.geometry import mirror_points_line
from compas.geometry import Transformation

app = dash.Dash(
    __name__,
    meta_tags=[{'name': 'viewport',
                'content': 'Width=device-width, initial-scale=1'}]
    )

server = app.server
app.config.suppress_callback_exceptions = True

#  ----------------------------------------------------------------------------
#  Components
#  ----------------------------------------------------------------------------

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
                                build_assembly_input(),
                                build_force_input(),
                                ]),
                    html.Br(),
                    mui.Divider(),
                    html.Div(className='row', children=[
                        build_3d_visualization(),
                        build_2d_visualization(),
                        ]),
                    html.Br(),
                    mui.Divider(),
                    html.H4('Design Checks'),
                    html.Div(className='row', children=[
                        build_beam_design_checks(),
                        build_column_design_checks()
                        ])
                    ])
    elif category == 'Report':
        return html.Div(className='row', children=[
                    html.Div(className='six columns', children=[html.Div()]),
                    html.Div(className='six columns', children=[html.Div()])
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

def build_3d_visualization():
    return html.Div(className='six columns', style={'height': '660px'}, children=[
            html.H4('3D Member Visualization'),
            dcc.Graph(id='connection-3d-visualization',
                      figure=build_default_3d_visualization())
            ])

def build_2d_visualization():
    return html.Div(className='six columns', style={'height': '660px'}, children=[
        build_gusset_parameters()
        ])
slider_marks = {12: '12', 16: '16', 20: '20', 24: '24', 28: '28',
                32: '32', 36: '36', 40: '40'}


def build_assembly_input():
    return html.Div(id='assembly', className='six columns',
                    children=[
                        html.Div(id='gusset-assembly',
                                 children=[
                                    html.H4('Assembly'),
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
def build_force_input():
    return html.Div(id='force-input', className='six columns',
                    children=[
                        html.Div(id='force-field',
                                 children=[
                                    html.H4('Brace Force'),
                                    dcc.Input(
                                        id='force-input-field',
                                        type='number',
                                        placeholder='400.0',
                                        style={'width': '50%'}
                                        ),
                                    html.Div(style={'font-variant': 'small-caps'},
                                             children=[
                                                'kips (lb-force x 1000)'
                                            ])
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
                                                ])
                                            ])
                                        ]),
                            ]),
                        html.Div(className='row', children=[
                            html.Div(className='two columns',
                                     children=[
                                        dfx.Row(center='xs',
                                                children=[
                                                    daq.NumericInput(
                                                        id='gusset-thickness',
                                                        label='Plate Thickness',
                                                        labelPosition='top',
                                                        value=1.,
                                                        min=0.5,
                                                        max=4
                                                        ),
                                                    html.Div('inches', style={'justify-content': 'center',
                                                        'font-variant': 'small-caps'})
                                        ])
                                     ]),
                            html.Div(className='ten columns',
                                     children=[
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

def build_beam_design_checks():
    return html.Div(className='six columns', children=[
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
                ])
        ])


def build_column_design_checks():
    return html.Div(className='six columns', children=[
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
                ])
        ])


dcr_list = ['axial-tension', 'moment', 'shear', 'Von-Mises']

dcr_key = {'axial-tension': 'P (+)', 'moment': 'M', 'shear': 'V', 'Von-Mises': 'VM'}


def generate_beam_dcr_indicators():
    circles = [create_dcr_indicator('beam-' + item) for item in dcr_list]
    return dfx.Row(children=circles)


def generate_column_dcr_indicators():
    circles = [create_dcr_indicator('column-' + item) for item in dcr_list]
    return dfx.Row(children=circles,
                   center='xs')


def create_dcr_indicator(item):
    id_abbrev = (item).split('-', 1)[1]
    circle = daq.Indicator(
             id=item + '-indicator',
             label=dcr_key[id_abbrev],
             value=True,
             color= "#000000"
             )
    styled_circle = html.Div(id=item + '-circle-container', style={'margin': '1em', 'width': '30px'},
                             children=[circle])
    circle_div = dfx.Col(children=[
                    styled_circle,
                    html.Div(id=item + '-circle-value')
                    ])
    return circle_div


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


def build_default_3d_visualization():

    figure = go.Figure(data=go.Scatter3d({'x': [0], 'y': [0], 'z': [0]}, visible=False))
    figure.update_layout(showlegend=False,
                         margin=dict(l=10, t=10, b=10),
                         scene_xaxis=dict(range=[-10, 10]),
                         scene_yaxis=dict(range=[0, 100]),
                         scene_zaxis=dict(range=[0, 200]))
    figure.update_layout(scene_aspectmode='manual', scene_aspectratio=dict(x=1, y=1, z=1))
    return figure

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
                        html.Div(dcc.Store(id='local')),
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


@app.callback(
    Output(component_id='gusset-l1-value', component_property='children'),
    [Input(component_id='l1-slider', component_property='value')]
)
def update_l1_textbox_value(input_value):
    return 'L1 = {} inches'.format(input_value)


@app.callback(
    Output(component_id='gusset-l2-value', component_property='children'),
    [Input(component_id='l2-slider', component_property='value')]
)
def update_l2_textbox_value(input_value):
    return 'L2 = {} inches'.format(input_value)


@app.callback(
    [Output(component_id='connection-3d-visualization', component_property='figure'),
     Output('local', 'data')],
    [Input('input-button', 'n_clicks')],
    [State('assembly-input-field', 'value'),
     State('force-input-field', 'value')]
)
def load_gusset_assembly(n_clicks, filepath, force_value):
    if n_clicks is None:
        raise PreventUpdate
    elif filepath is None:
        raise PreventUpdate
    else:
        gusset_node = GussetNode.from_json(filepath)
        gusset = GussetPlate(gusset_node.braces[0], gusset_node.column[0],
                             gusset_node.beams[0], 'i', brace_angle=37)
        V_c, H_c, M_c, V_b, H_b, M_b = gusset.calculate_interface_forces(force_value)
        gusset_dict = {'eb': gusset.eb, 'ec': gusset.ec,
                       'offset': gusset.offset,
                       'design_angle': gusset.design_angle,
                       'brace_depth': gusset.get_brace_depth(),
                       'connection_length': gusset.connection_length,
                       'V_c': V_c,
                       'H_c': H_c,
                       'M_c': M_c,
                       'V_b': V_b,
                       'H_b': H_b,
                       'M_b': M_b}
        meshes = gusset_node.to_meshes()
        fig = go.Figure(data=meshes)
        fig.update_layout(scene_aspectmode='data',
                          height=620,
                          margin=dict(l=10, t=10, b=10))
        return fig, gusset_dict


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
    if gusset_data is None:
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
        pt_mirrored = mirror_points_line([brace_pt], brace_CL)[0]
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
    print(gusset_outline)
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

#  ----------------------------------------------------------------------------
#  Calculator Callbacks
#  ----------------------------------------------------------------------------


@app.callback(
    [Output('beam-axial-tension-indicator', 'color'),
     Output('beam-axial-tension-circle-value', 'children')],
    [Input('l1-slider', 'value'),
     Input('gusset-thickness', 'value'),
     Input('local', 'modified_timestamp')],
    [State('local', 'data')]
    )
def get_l1_axial_tension_dcr(l1, thickness, ts, data):
    if ts is None:
        raise PreventUpdate
    if data is None:
        raise PreventUpdate
    p_u = data['V_b']
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
    [Output('column-axial-tension-indicator', 'color'),
     Output('column-axial-tension-circle-value', 'children')],
    [Input('l2-slider', 'value'),
     Input('gusset-thickness', 'value'),
     Input('local', 'modified_timestamp')],
    [State('local', 'data')]
    )
def get_l2_axial_tension_dcr(l2, thickness, ts, data):
    if ts is None:
        raise PreventUpdate
    if data is None:
        raise PreventUpdate
    p_u = data['H_c']
    phi_Pn = 0.9 * 50 * l2 * thickness
    at_dcr = p_u / phi_Pn
    if at_dcr > 0.95:
        color = 'red'
    elif at_dcr > 0.85:
        color = 'yellow'
    else:
        color = 'green'
    return color, "{:.0%}".format(at_dcr)


@app.callback(
    [Output('beam-moment-indicator', 'color'),
     Output('beam-moment-circle-value', 'children')],
    [Input('l1-slider', 'value'),
     Input('gusset-thickness', 'value'),
     Input('local', 'modified_timestamp')],
    [State('local', 'data')]
    )
def get_l1_moment_dcr(l1, thickness, ts, data):
    if ts is None:
        raise PreventUpdate
    if data is None:
        raise PreventUpdate
    m_u = data['M_b']
    Z_gusset = thickness * l1 ** 2.0 / 4
    phi_Mn = 0.9 * 50 * Z_gusset
    m_dcr = abs(m_u) / phi_Mn
    if m_dcr > 0.95:
        color = 'red'
    elif m_dcr > 0.85:
        color = 'yellow'
    else:
        color = 'green'
    return color, "{:.0%}".format(m_dcr)


@app.callback(
    [Output('column-moment-indicator', 'color'),
     Output('column-moment-circle-value', 'children')],
    [Input('l2-slider', 'value'),
     Input('gusset-thickness', 'value'),
     Input('local', 'modified_timestamp')],
    [State('local', 'data')]
    )
def get_l2_moment_dcr(l2, thickness, ts, data):
    if ts is None:
        raise PreventUpdate
    if data is None:
        raise PreventUpdate
    m_u = data['M_c']
    Z_gusset = thickness * l2 ** 2.0 / 4
    phi_Mn = 0.9 * 50 * Z_gusset
    m_dcr = abs(m_u) / phi_Mn
    if m_dcr > 0.95:
        color = 'red'
    elif m_dcr > 0.85:
        color = 'yellow'
    else:
        color = 'green'
    return color, "{:.0%}".format(m_dcr)


@app.callback(
    [Output('beam-shear-indicator', 'color'),
     Output('beam-shear-circle-value', 'children')],
    [Input('l1-slider', 'value'),
     Input('gusset-thickness', 'value'),
     Input('local', 'modified_timestamp')],
    [State('local', 'data')]
    )
def get_l1_in_plane_shear_dcr(l1, thickness, ts, data):
    if ts is None:
        raise PreventUpdate
    if data is None:
        raise PreventUpdate
    v_u = data['H_b']
    A_gusset = thickness * l1
    phi_Vn = 0.9 * 50 * A_gusset * 0.6
    v_dcr = abs(v_u) / phi_Vn
    if v_dcr > 0.95:
        color = 'red'
    elif v_dcr > 0.85:
        color = 'yellow'
    else:
        color = 'green'
    return color, "{:.0%}".format(v_dcr)


@app.callback(
    [Output('column-shear-indicator', 'color'),
     Output('column-shear-circle-value', 'children')],
    [Input('l2-slider', 'value'),
     Input('gusset-thickness', 'value'),
     Input('local', 'modified_timestamp')],
    [State('local', 'data')]
    )
def get_l2_in_plane_shear_dcr(l2, thickness, ts, data):
    if ts is None:
        raise PreventUpdate
    if data is None:
        raise PreventUpdate
    v_u = data['V_c']
    A_gusset = thickness * l2
    phi_Vn = 0.9 * 50 * A_gusset * 0.6
    v_dcr = abs(v_u) / phi_Vn
    if v_dcr > 0.95:
        color = 'red'
    elif v_dcr > 0.85:
        color = 'yellow'
    else:
        color = 'green'
    return color, "{:.0%}".format(v_dcr)


@app.callback(
    [Output('beam-Von-Mises-indicator', 'color'),
     Output('beam-Von-Mises-circle-value', 'children')],
    [Input('l1-slider', 'value'),
     Input('gusset-thickness', 'value'),
     Input('local', 'modified_timestamp')],
    [State('local', 'data')]
    )
def get_l1_von_mises_dcr(l1, thickness, ts, data):
    if ts is None:
        raise PreventUpdate
    if data is None:
        raise PreventUpdate
    p_u = data['V_b']
    v_u = data['H_b']
    A_gusset = thickness * l1
    sigma_p = p_u / A_gusset
    sigma_v = v_u / A_gusset
    sigma_vm = (sigma_p ** 2.0 + sigma_v ** 2.0) ** 0.5
    phi_vm = 0.9 * 50.
    vm_dcr = sigma_vm / phi_vm
    if vm_dcr > 0.95:
        color = 'red'
    elif vm_dcr > 0.85:
        color = 'yellow'
    else:
        color = 'green'
    return color, "{:.0%}".format(vm_dcr)


@app.callback(
    [Output('column-Von-Mises-indicator', 'color'),
     Output('column-Von-Mises-circle-value', 'children')],
    [Input('l2-slider', 'value'),
     Input('gusset-thickness', 'value'),
     Input('local', 'modified_timestamp')],
    [State('local', 'data')]
    )
def get_l2_von_mises_dcr(l2, thickness, ts, data):
    if ts is None:
        raise PreventUpdate
    if data is None:
        raise PreventUpdate
    p_u = data['H_c']
    v_u = data['V_c']
    A_gusset = thickness * l2
    sigma_p = p_u / A_gusset
    sigma_v = v_u / A_gusset
    sigma_vm = (sigma_p ** 2.0 + sigma_v ** 2.0) ** 0.5
    phi_vm = 0.9 * 50.
    vm_dcr = sigma_vm / phi_vm
    if vm_dcr > 0.95:
        color = 'red'
    elif vm_dcr > 0.85:
        color = 'yellow'
    else:
        color = 'green'
    return color, "{:.0%}".format(vm_dcr)


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
