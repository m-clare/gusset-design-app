import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq

from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State

import dash_flexbox_grid as dfx
import plotly.graph_objs as go
import sd_material_ui as mui
import numpy as np
import json

# my_gusset_node = GussetNode

app = dash.Dash(
    __name__,
    meta_tags=[{'name': 'viewport',
                'content': 'Width=device-width, initial-scale=1'}]
    )

server = app.server
app.config['suppress_callback_exceptions'] = True

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


def build_main_app():
    return html.Div(
        id='main-app',
        children=[
            dfx.Row(children=[
                dfx.Col(xs=6, children=[
                    build_io_panel()
                    ]
                    ),
                dfx.Col(xs=6, children=[
                    dcc.Graph(figure=generate_visualization())
                    ])
                ])
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
                               selected_className=category + '-custom-tab--selected',
                               children=build_tab(category))
        category_tabs.append(category_tab)
    return html.Div(
        id='tabs',
        className='tabs',
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
        return [dfx.Grid(id=category+'-grid', fluid=True,
                         children=[
                            dfx.Row(children=[
                                    dfx.Col(xs=6, children=[build_io_panel()]),
                                    dfx.Col(xs=6, children=[
                                        dcc.Graph(figure=generate_visualization())
                                            ])
                                    ])
                            ])]
    elif category == 'Report':
        return [dfx.Grid(id=category+'-grid',
                         children=[
                            dfx.Row(children=[
                                dfx.Col(xs=6, children=html.Div()),
                                dfx.Col(xs=6, children=html.Div()),
                                ])
                         ])]



def build_io_panel():
    return html.Div(id='io-panel',
             children=[
                build_assembly_input(),
                html.Br(),
                mui.Divider(),
                build_gusset_parameters(),
                html.Br(),
                mui.Divider(),
                build_design_checks(),
             ])


slider_marks = {12: '12', 16: '16', 20: '20', 24: '24', 28:'28',
                32: '32', 36: '36', 40: '40'}


def build_assembly_input():
    return html.Div(id='assembly',
                    children=[
                        html.Div(id='load-gusset-assembly',
                                 className='pretty-shadowless-container',
                                 children=[
                                    html.H3('Assembly'),
                                    dcc.Input(
                                        id='assembly-input-field',
                                        type='text',
                                        placeholder='filepath/to/assembly.json'
                                    ),
                                    html.Div(style={'font-variant': 'small-caps'},
                                             children=[
                                                'Filepath'
                                            ])
                                    ])
                        ])


def build_gusset_parameters():
    return html.Div(id='gusset-parameters',
                    className='pretty-shadowless-container',
                    children=[
                        html.H4('Gusset Parameters'),
                        html.H6('L1'),
                        dcc.Slider(
                            id='l1' + '-slider',
                            min=12,
                            max=40,
                            step=0.5,
                            value=24,
                            marks=slider_marks
                            ),
                        html.Br(),
                        html.Div(id='gusset-l1-value',
                                 style={'font-variant': 'small-caps'}
                                 ),
                        html.Br(),
                        html.H6('L2'),
                        dcc.Slider(
                            id='l2' + '-slider',
                            min=12,
                            max=40,
                            step=0.5,
                            value=24,
                            marks=slider_marks,
                            ),
                        html.Br(),
                        html.Div(id='gusset-l2-value',
                                 style={'font-variant': 'small-caps'}),
                        html.Br(),
                        html.Br(),
                        daq.NumericInput(
                            label='Gusset plate thickness (inches)',
                            labelPosition='bottom',
                            value=1,
                            min=0.5,
                            max=4,
                            style={'font-variant': 'small-caps'}
                        )])

def build_design_checks():
    return html.Div(id='gusset-design-checks',
                    className='pretty-shadowless-container',
                    children=create_dcr_indicators())

dcr_list = ['axial-tension', 'axial-compression', 'moment', 'in-plane-shear',
            'out-of-plane-shear', 'Whitmore-section']

def create_dcr_indicators():
    dcr_graduated_bars = []
    for item in dcr_list:
        bar = daq.GraduatedBar(
              id=item + '-indicator',
              color={'gradient': True, 'ranges': {'green': [0, 85], 'yellow': [85, 95], 'red': [95, 100]}},
              showCurrentValue=True,
              max=100,
              value=90,
              vertical=True,
              step=10,
              )
        dcr_graduated_bars.append(bar)
    return dcr_graduated_bars


def build_visualization_panel():
    pass


def build_gusset_node_visualization():
    pass


def build_guidelines_visualization():
    pass


def build_outline_visualization():
    pass


def generate_visualization():
    fig = go.Figure(data=[{'x': [0, 1], 'y': [1, 0]}])
    fig.update_layout(scene_aspectmode='data')
    return fig

#  ----------------------------------------------------------------------------
#  Layout
#  ----------------------------------------------------------------------------


app.layout = dfx.Grid(id='grid', fluid=True, children=[
                dfx.Row(children=[
                    dfx.Col(lg=1),
                    dfx.Col(xs=12, lg=10,
                            className='pretty-container',
                            children=[
                                html.Div(
                                    id='big-app-container',

                                    children=[
                                        build_app_banner(),
                                        html.Div(
                                            id='app-container',
                                            children=[
                                                build_tabs(),
                                                ]
                                            ),
                                        ]
                                    )
                                ]),
                    dfx.Col(lg=1)
                    ])
                ])

#  ----------------------------------------------------------------------------
#  Callbacks
#  ----------------------------------------------------------------------------


@app.callback(
    Output(component_id='gusset-l1-value', component_property='children'),
    [Input(component_id='l1-slider', component_property='value')]
)
def update_l1_slider_value(input_value):
    return '{} inches'.format(input_value)


@app.callback(
    Output(component_id='gusset-l2-value', component_property='children'),
    [Input(component_id='l2-slider', component_property='value')]
)
def update_l2_slider_value(input_value):
    return '{} inches'.format(input_value)

if __name__ =='__main__':
    app.run_server(debug=True, port=8050)