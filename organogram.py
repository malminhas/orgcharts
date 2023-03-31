import os
import yaml
import networkx as nx
import matplotlib.pyplot as plt

VALID_STATUS = ['perm','contractor','starting','leaving','moving','new']
VALID_TEAM = ['Reviews','Jobs Board','Jobs Mgmt','HEX','Search','Octo']
VALID_RELATION = [1,2,3,4]
NODE_SIZE = 7000
EDGE_LABEL_HEIGHT = 0.3

def split_line(val):
    return '\n'.join(val.split(' ',1))
    
def proc_field(val, newline, upper=False):
    if newline:
        val = '\n'.join(val.split(' ',1))
    if upper:
        val = val.upper()
    return val

class OrganisationDiagrammer(object):
    def __init__(self):
        self._graph = None
    
    def load_yaml_file(self, file_path):
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        return data

    def create_graph_from_yaml(self, yaml_data, newline=True, validate=False):
        g = nx.Graph()
        for node in yaml_data['nodes']:
            name = proc_field(node['id'], newline)
            note = node.get('note')
            team = node.get('team')
            if team:
                if validate:
                    assert(team in VALID_TEAM)
                team = proc_field(team, newline, upper=True)
            status = node['status']
            if validate:
                assert(status in VALID_STATUS)
            g.add_node(name, level=node['level'], status=status, manager=node['manager'], note=note, team=team)
        for edge in yaml_data['edges']:
            source = proc_field(edge['source'], newline)
            target = proc_field(edge['target'], newline)
            relation = edge['relationship']
            if validate:
                assert(relation in VALID_RELATION)
            g.add_edge(source, target, label=edge['label'], relationship=relation)
        return g

    def create_graphviz_layout_from_graph(self, g, scale=4, offset=16, margin=0.1, node_size=NODE_SIZE, image_file='org.png'):
        # 1. Pull out the different relationships for edges
        # Can be 1 for direct management, 2 for indirect management, 3 for a perm yet to join, 4 for a perm leaving.
        e_direct = [(u, v) for (u, v, d) in g.edges(data=True) if d['relationship'] == 1 ]
        e_indirect = [(u, v) for (u, v, d) in g.edges(data=True) if d['relationship'] == 2 ]
        e_starting = [(u, v) for (u, v, d) in g.edges(data=True) if d['relationship'] == 3 ]
        e_leaving = [(u, v) for (u, v, d) in g.edges(data=True) if d['relationship'] == 4 ]

        # 2. Pull out the different status cohorts for nodes
        # status can be: perm|contractor|starter|joining|leaving
        n_perm = [(u) for (u, d) in g.nodes(data=True) if d['status'] == 'perm' ]
        n_contractor = [(u) for (u, d) in g.nodes(data=True) if d['status'] == 'contractor' ]
        n_starting = [(u) for (u, d) in g.nodes(data=True) if d['status'] == 'starting' ]
        n_leaving = [(u) for (u, d) in g.nodes(data=True) if d['status'] == 'leaving' ]
        n_moving = [(u) for (u, d) in g.nodes(data=True) if d['status'] == 'moving' ]
        n_new = [(u) for (u, d) in g.nodes(data=True) if d['status'] == 'new' ]
        n_manager = [(u) for (u, d) in g.nodes(data=True) if d['manager'] == 'yes' ]
        n_note = [(u, d) for (u, d) in g.nodes(data=True) if d.get('note') ]
        n_team = [(u, d) for (u, d) in g.nodes(data=True) if d.get('team') ]

        edge_labels=dict([((u,v,),d['label']) for u,v,d in g.edges(data=True)])

        pos = nx.nx_agraph.graphviz_layout(g, prog='dot')

        # nodes - see: https://matplotlib.org/stable/api/markers_api.html#module-matplotlib.markers
        # colors - see: https://matplotlib.org/stable/gallery/color/named_colors.html
        nx.draw_networkx_nodes(g, pos, node_shape='s', margins=margin, node_color='green', node_size=node_size) # box common to all
        nx.draw_networkx_nodes(g, pos, node_shape='s', margins=margin, nodelist=n_leaving, node_color='orange', node_size=node_size) # overlay for leavers
        nx.draw_networkx_nodes(g, pos, node_shape='s', margins=margin, nodelist=n_starting, node_color='teal', node_size=node_size) # overlay for new starters
        nx.draw_networkx_nodes(g, pos, node_shape='s', margins=margin, nodelist=n_moving, node_color='yellowgreen', node_size=node_size) # overlay for movers
        nx.draw_networkx_nodes(g, pos, node_shape='s', margins=margin, nodelist=n_contractor, node_color='grey', node_size=node_size) # overlay for new starters
        nx.draw_networkx_nodes(g, pos, node_shape='s', margins=margin, nodelist=n_manager, node_color='none', linewidths=5.0, edgecolors='black', node_size=node_size) # overlay for managers

        # edges
        # styles - see: https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.Patch.html#matplotlib.patches.Patch.set_linestyle
        nx.draw_networkx_edges(g, pos, edgelist=e_direct, width=4, alpha=0.8, edge_color='g', style='solid')
        nx.draw_networkx_edges(g, pos, edgelist=e_indirect, width=4, alpha=0.8, edge_color='g', style='dotted')
        nx.draw_networkx_edges(g, pos, edgelist=e_starting, width=4, alpha=0.8, edge_color='teal', style='dotted')
        nx.draw_networkx_edges(g, pos, edgelist=e_leaving, width=4, alpha=0.8, edge_color='orange', style='dotted')

        # node labels - rotate edge labels to be horizontal
        text = nx.draw_networkx_edge_labels(g, pos, font_size=12, edge_labels=edge_labels, label_pos=EDGE_LABEL_HEIGHT)
        for _, t in text.items():
            t.set_rotation('horizontal')
        nx.draw_networkx_labels(g, pos, font_size=18, font_color='w', font_family='sans-serif', horizontalalignment='center', verticalalignment='bottom')

        # note labels - rotate edge labels to be horizontal
        fcolor = 'none'
        ecolor = 'none'
        for (name, d) in n_note:  # note - goes below the node
            x,y = pos.get(name)
            note = proc_field(d.get('note'), True)
            plt.text(x,y-offset/2,s=note, size=offset, bbox=dict(facecolor='none', edgecolor=ecolor, alpha=0.5), horizontalalignment='center')
        for (name, d) in n_team:  # team - goes above the node
            x,y = pos.get(name)
            team = d.get('team')
            plt.text(x,y+offset, s=team, size=offset+4, bbox=dict(facecolor=fcolor, edgecolor=ecolor, alpha=0.5), horizontalalignment='center')

        plt.axis('off')
        params = plt.gcf()
        plSize = params.get_size_inches()
        params.set_size_inches( (plSize[0]*scale, plSize[1]*scale) )
        plt.savefig(image_file, bbox_inches="tight")
        return g

    def create_dotfile_from_graph(self, g, dot_file):
        ''' Need to pip install pydot for this '''
        nx.drawing.nx_pydot.write_dot(g, dot_file)
        return dot_file

if __name__ == '__main__':
    target = 'homeowner.png'
    org = OrganisationDiagrammer()
    data = org.load_yaml_file('homeowner.yaml')
    g = org.create_graph_from_yaml(data)
    org.create_graphviz_layout_from_graph(g, scale=4, image_file=target)
    print(f'Successfully generated organogram into file {target} of size {os.path.getsize(target)/1024}kB')