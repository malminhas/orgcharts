import os
import yaml
import pytest
from organogram import OrganisationDiagrammer, split_line, proc_field

# To get code coverage support:
# 1. pip install coverage, pytest-cov
# 2. create a tests directory, add this file to it
# 3. add a blank __init__.py to the tests directory
# 4. run the following CLI from the parent directory:
# pytest --exitfirst --failed-first --cov=. --cov-report html -vv

# ---- FIXTURES -----

@pytest.fixture
def diagrammer():
    return OrganisationDiagrammer()

# Example YAML data for testing
yaml_data = {
    "nodes": [
        {
            "id": "A",
            "label": "CEO",
            "status": "perm",
            "manager": "yes",
            "team": "Team A"
        },
        {
            "id": "B",
            "label": "CTO",
            "status": "perm",
            "manager": "no",
            "team": "Team B"
        }
    ],
    "edges": [
        {
            "source": "A",
            "target": "B",
            "relationship": 1
        }
    ]
}
yaml_data_mini = {
    "nodes": [
        {
            "id": "A",
            "status": "perm",
            "team": "Team A"
        },
        {
            "id": "B",
            "status": "perm",
            "team": "Team B"
        }
    ],
    "edges": [
        {
            "source": "A",
            "target": "B",
            "relationship": 1
        }
    ]
}
yaml_data_none = {
    "nodes": [
        {
        },
        {
        }
    ],
    "edges": [
        {
        }
    ]
}
yaml_data_zero = {
}

# ---- TESTS -----

def test_load_yaml_file(diagrammer):
    yaml_file = "example.yaml"
    with open(yaml_file, 'w') as f:
        f.write(yaml.dump(yaml_data))
    loaded_data = diagrammer.load_yaml_file(yaml_file)
    assert loaded_data == yaml_data

def test_create_graph_from_yaml(diagrammer):
    graph = diagrammer.create_graph_from_yaml(yaml_data)
    
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.has_node(proc_field("A"))
    assert graph.has_node(proc_field("B"))
    assert graph.has_edge(proc_field("A"), proc_field("B"))

def test_create_valid_teams_and_status(diagrammer):
    validTeams = ['Team A', 'Team B']
    validStatus = ['perm']
    diagrammer.set_valid_teams(validTeams)
    diagrammer.set_valid_status(validStatus)
    assert(diagrammer.valid_teams == validTeams)
    assert(diagrammer.valid_status == validStatus)
           
def test_create_graph_from_yaml_validate(diagrammer):
    diagrammer.set_valid_teams(['Team A', 'Team B'])
    diagrammer.set_valid_status(['perm'])
    graph = diagrammer.create_graph_from_yaml(yaml_data, validate=True)

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.has_node(proc_field("A"))
    assert graph.has_node(proc_field("B"))
    assert graph.has_edge(proc_field("A"), proc_field("B"))

def test_create_dotfile_from_graph(diagrammer):
    target = "test_output.dot"
    graph = diagrammer.create_graph_from_yaml(yaml_data)
    dotfile = diagrammer.create_dotfile_from_graph(graph, dot_file=target)
    
    assert(dotfile == target)
    size = os.path.getsize(target)
    assert isinstance(size, int)
    assert size > 0

def test_create_graphviz_layout_from_graph(diagrammer):
    target = "test_output.png"
    graph = diagrammer.create_graph_from_yaml(yaml_data)
    layout_graph = diagrammer.create_graphviz_layout_from_graph(graph, scale=5, cstyle='angle', margin=0.1, offset=2, node_size=10000, image_file=target)

    assert len(layout_graph.nodes) == 2
    assert len(layout_graph.edges) == 1
    assert layout_graph.has_node(proc_field("A"))
    assert layout_graph.has_node(proc_field("B"))
    assert layout_graph.has_edge(proc_field("A"), proc_field("B"))
    size = os.path.getsize(target)
    assert isinstance(size, int)
    assert size > 0

def test_load_yaml_file_zero(diagrammer):
    yaml_file = "example_zero.yaml"
    with open(yaml_file, 'w') as f:
        f.write(yaml.dump(yaml_data_zero))
    loaded_data = diagrammer.load_yaml_file(yaml_file)
    assert loaded_data == yaml_data_zero
    
def test_load_yaml_file_none(diagrammer):
    yaml_file = "example_none.yaml"
    with open(yaml_file, 'w') as f:
        f.write(yaml.dump(yaml_data_none))
    loaded_data = diagrammer.load_yaml_file(yaml_file)
    assert loaded_data == yaml_data_none

def test_create_graph_from_yaml_none(diagrammer):
    graph = diagrammer.create_graph_from_yaml(yaml_data_none)
    
    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0

def test_load_yaml_file_mini(diagrammer):
    yaml_file = "example_mini.yaml"
    with open(yaml_file, 'w') as f:
        f.write(yaml.dump(yaml_data_mini))
    loaded_data = diagrammer.load_yaml_file(yaml_file)
    assert loaded_data == yaml_data_mini

def test_create_graph_from_yaml_mini(diagrammer):
    graph = diagrammer.create_graph_from_yaml(yaml_data_mini)
    
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.has_node(proc_field("A"))
    assert graph.has_node(proc_field("B"))
    assert graph.has_edge(proc_field("A"), proc_field("B"))

def test_create_graph_from_yaml_mini_validate(diagrammer):
    diagrammer.set_valid_teams(['Team A', 'Team B'])
    diagrammer.set_valid_status(['perm'])
    graph = diagrammer.create_graph_from_yaml(yaml_data_mini, validate=True)

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.has_node(proc_field("A"))
    assert graph.has_node(proc_field("B"))
    assert graph.has_edge(proc_field("A"), proc_field("B"))