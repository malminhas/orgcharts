#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# cat-reviews.py
# --------------
# (c) 2023 Mal Minhas, <mal.minhas@checkatrade.com>
#
# Description
# -----------
# Organisation Diagrammer which can be used to allow you to store an organisation structure in code as YAML
# and optionally generate a .dot file representation of it or a graphviz visualisation
#
# Installation:
# -------------
# pip install -r requirements.txt
# You will also need to install graphviz.  You can do this via Homebrew on your Mac
#
# Implementation:
# --------------
# There is one class in this module:
# OrganisationDiagrammer - ingests a YAML organisation file and converts it to:
# a) dot representation, b) graphviz visualisation
#
# Documentation:
# -------------
# See: https://betterprogramming.pub/auto-documenting-a-python-project-using-sphinx-8878f9ddc6e9
# $ pip install Sphinx
# $ mkdir docs
# $ cd docs                       => all the following happens in the docs directory
# $ sphinx-quickstart             => creates a Makefile, a make.bat file, as well as build and source directories.
# $ cd source                     => edit the conf.py file
# $ pip install sphinx-rtd-theme  => if this theme has been chosen
# $ cd ..                         => back to docs directory
# $ sphinx-apidoc -o source ..    => generates index.rst and cat-review.rst files into source directory
# $ make html
# $ open html/index.html
#
# History:
# -------
# 02.04.23    v0.1    First working version with graphviz and dot support
# 08.04.23    v0.2    Added CLI, logging, type support, ran through black and added initial Sphinx support
# 09.04.23    v0.3    Enhanced CLI
#
# ToDo:
# -------
# 1. Add support to ingest organisation input data from csv or xlsx file
#
"""
Welcome to organogram.py module!
This module has one main class:
* `OrganisationDiagrammer`
"""

import os
import sys
import time
import yaml
import logging
import docopt
from logging import Logger
from typing import List, Dict, Any, Optional
import networkx as nx  # type: ignore
from PIL import Image
import matplotlib.pyplot as plt  # type: ignore

PROGRAM = __file__.split("/")[-1]
VERSION = "0.3"
DATE = "09.04.23"
AUTHOR = "<mal.minhas@checkatrade.com>"

VALID_STATUS = ["perm", "contractor", "starting", "leaving", "moving", "new"]
VALID_TEAM = ["A", "B", "C", "D", "E", "F"]
VALID_RELATION = [1, 2, 3, 4]

DEFAULT_NODE_SIZE = 7500
DEFAULT_MARGIN = 0.1
DEFAULT_CSTYLE = "arc3"
DEFAULT_OFFSET = 7
DEFAULT_EDGE_LABEL_HEIGHT = 0.3
DEFAULT_FONT_SIZE = 16


def initLogger(verbose: bool) -> Logger:
    """
    Initialise standard Python console logging.

    **Parameters**

    verbose : `bool`
        Enable/disable logging

    **Returns**

    logger : `Logger`
        logger instance

    """
    if verbose:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s :: %(levelname)s :: %(message)s"
        )
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
    else:
        # this will silence all logging including from modules
        logger = logging.getLogger(__name__)
        logger.addHandler(logging.FileHandler(os.devnull))
    return logger


# By default when we import organogram we turn the logger off
"""
When we import organogram we turn the logger off.
"""
logger = initLogger(False)


def get_file_size(filename: str) -> float:
    """
    Get file size in kB.

    **Parameters**

    filename : `str`
        filename

    **Returns**

    file_size : `int`
        size of file in kB rounded to 2 decimal places.

    """
    file_size = round(os.path.getsize(filename) / 1024, 2)
    return file_size


def split_line(val: str) -> str:
    """
    Split the input string on first

    **Parameters**

    val : `str`
        input string to split

    **Returns**

    val : `str`
        output string with newline in first whitespace.

    """
    if val:
        val = "\n".join(val.split(" ", 1))
    return val


def proc_field(val: str, newline: bool = False, upper: bool = False) -> str:
    inputval = val
    if val:
        if newline:
            val = "\n".join(val.split(" ", 1))
        if upper:
            val = val.upper()
    else:
        val = ""
    logger.info(f"::proc_field() - converting {repr(inputval)} to {repr(val)}")
    return val


class OrganisationDiagrammer(object):
    def __init__(
        self,
        node_size: int = DEFAULT_NODE_SIZE,
        margin: float = DEFAULT_MARGIN,
        cstyle: str = DEFAULT_CSTYLE,
        font_size: int = DEFAULT_FONT_SIZE,
        offset: int = DEFAULT_OFFSET,
    ):
        """
        Constructor method. Creates a :py:class: `OrganisationDiagrammer` instance
        """
        logger.info(f"OrganisationDiagrammer::__init__() - constructor")
        self._graph = None
        self._node_size = node_size
        self._margin = margin
        self._cstyle = cstyle
        self._font_size = font_size
        self._offset = offset
        self._validTeams = VALID_TEAM
        self._validStatus = VALID_STATUS
        self._validRelations = VALID_RELATION

    @property
    def valid_teams(self) -> List:
        """
        Return valid teams

        **Parameters**

        **Returns**

        validTeams : `List`
            list of current valid teams. eg. ["A", "B", "C", "D", "E", "F"]

        """
        return self._validTeams

    def set_valid_teams(self, teams: List):
        """
        Set valid teams list

        **Parameters**

        teams : `List`
            list of valid teams. eg. "A", "B", "C", "D", "E", "F"]

        **Returns**

        """
        assert isinstance(teams, list)
        logger.info(
            f'OrganisationDiagrammer::set_valid_teams() - setting valid teams to "{teams}"'
        )
        self._validTeams = teams

    @property
    def valid_status(self) -> List:
        """
        Return valid statuses

        **Parameters**

        **Returns**

        validStatus : `List`
            list of current valid statuses. eg. ["perm", "contractor","new"]

        """
        return self._validStatus

    def set_valid_status(self, status):
        """
        Set valid status list

        **Parameters**

        status : `List`
            list of valid status. eg. ["perm", "contractor","new"]

        **Returns**

        """
        assert isinstance(status, list)
        logger.info(
            f'OrganisationDiagrammer::set_valid_status() - setting valid status to "{status}"'
        )
        self._validStatus = status

    @property
    def valid_relations(self) -> List:
        """
        Return valid relations

        **Parameters**

        **Returns**

        validRelations : `List`
            list of current valid relations. eg. [1,2,3,4]

        """
        return self._validRelations

    def set_valid_relations(self, relations: List):
        """
        Set valid relations list

        **Parameters**

        relation : `List`
            list of valid relations. eg. [1,2,3,4]

        **Returns**

        """
        assert isinstance(relations, list)
        logger.info(
            f'OrganisationDiagrammer::set_valid_relations() - setting valid relations to "{relations}"'
        )
        self._validRelations = relations

    def load_yaml_file(self, file_path: str) -> Dict[Optional[Any], Optional[Any]]:
        """
        Load YAML organisation configuration file and convert to Dict

        **Parameters**

        file_path : `str`
            name of YAML file

        **Returns**

        data : `Dict`
            dictionary of `nodes` and `edges`

        """
        logger.info(
            f'OrganisationDiagrammer::load_yaml_file() - loading YAML from "{file_path}"'
        )
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
        return data

    def create_graph_from_yaml(
        self, yaml_data: Dict, newline: bool = True, validate: bool = False
    ) -> nx.DiGraph:
        """
        Create NetworkX graph from YAML data.

        **Parameters**

        yaml_data : `Dict`
            dictionary of `nodes` and `edges`
        newline : `bool`
            newline or not

        validate : `bool`
            validate teams, statuses, relations or not.

        **Returns**

        g : `nx.DiGraph`
            NetworkX graph of organisation built from yaml_data

        """
        logger.info(
            f"OrganisationDiagrammer::create_graph_from_yaml() - newline={newline},  validate={validate}"
        )
        g = nx.DiGraph()
        for node in yaml_data["nodes"]:
            name = proc_field(node.get("id"), newline)
            note = proc_field(node.get("note"))
            team = proc_field(node.get("team"))
            job = proc_field(node.get("label"), newline)
            rank = proc_field(node.get("rank"))
            manager = proc_field(node.get("manager"))
            if team:
                if validate:
                    assert team in self._validTeams
                team = proc_field(team, newline, upper=True)
            status = node.get("status")
            if validate and status:
                assert status in self._validStatus
            if name:
                g.add_node(
                    name,
                    rank=rank,
                    jobtitle=job,
                    status=status,
                    manager=manager,
                    note=note,
                    team=team,
                )
        for edge in yaml_data["edges"]:
            source = proc_field(edge.get("source"), newline)
            target = proc_field(edge.get("target"), newline)
            label = proc_field(edge.get("label"))
            relation = proc_field(edge.get("relationship"))
            if validate:
                assert relation in self._validRelations
            if source:
                g.add_edge(source, target, label=label, relationship=relation)
        return g

    def draw_networkx_nodes(
        self, g: nx.DiGraph, pos: Dict, margin: float, node_size: int, font_size: int
    ):
        """
        Draw nodes from NetworkX graph and corresponding node labels.

        **Parameters**

        g : `nx.DiGraph`
            NetworkX graph of organisation built from yaml_data
        pos : `Dict`
            Dictionary of tuples of (x,y) positions of all nodes
        margin : `float`
            Margin between nodes.  Default is 0.1
        node_size : `int`
            Size of node.  Default is `DEFAULT_NODE_SIZE` (7000)
        font_size : `int`
            Node text font size.

        **Returns**

        """
        logger.info(
            f"OrganisationDiagrammer::draw_networkx_nodes() - margin={margin}, node_size={node_size}, pos=\n{pos}"
        )
        # Pull out the different status cohorts for nodes
        # status can be: perm|contractor|new|hiring|starter|joining|leaving
        n_perm = [(u) for (u, d) in g.nodes(data=True) if d.get("status") == "perm"]
        n_contractor = [
            (u) for (u, d) in g.nodes(data=True) if d.get("status") == "contractor"
        ]
        n_all = [(u) for (u, d) in g.nodes(data=True)]
        n_starting = [
            (u) for (u, d) in g.nodes(data=True) if d.get("status") == "starting"
        ]
        n_hiring = [
            (u) for (u, d) in g.nodes(data=True) if d.get("status") == "hiring"
        ]
        n_leaving = [
            (u) for (u, d) in g.nodes(data=True) if d.get("status") == "leaving"
        ]
        n_moving = [(u) for (u, d) in g.nodes(data=True) if d.get("status") == "moving"]
        n_new = [(u) for (u, d) in g.nodes(data=True) if d.get("status") == "new"]
        n_manager = [(u) for (u, d) in g.nodes(data=True) if d.get("manager") == "yes"]

        # nodes - see: https://matplotlib.org/stable/api/markers_api.html#module-matplotlib.markers
        # colors - see: https://matplotlib.org/stable/gallery/color/named_colors.html
        def drawNetworkXNodes(
            nlist: List, color: str, lwidth: Any = None, ecolors: Any = None
        ):
            nx.draw_networkx_nodes(
                g,
                pos,
                node_shape="s",
                margins=margin,
                nodelist=nlist,
                node_color=color,
                linewidths=lwidth,
                edgecolors=ecolors,
                node_size=node_size,
            )

        drawNetworkXNodes(n_all, "green")
        drawNetworkXNodes(n_hiring, "red")
        drawNetworkXNodes(n_leaving, "orange")
        drawNetworkXNodes(n_starting, "teal")
        drawNetworkXNodes(n_new, "lightgreen")
        drawNetworkXNodes(n_moving, "yellowgreen")
        drawNetworkXNodes(n_contractor, "grey")
        drawNetworkXNodes(n_manager, "none", 5.0, "black")
        nx.draw_networkx_labels(
            g,
            pos,
            font_size=font_size,
            font_color="w",
            font_family="sans-serif",
            horizontalalignment="center",
            verticalalignment="bottom",
        )

    def draw_networkx_edges(self, g: nx.DiGraph, pos: Dict, cstyle: str):
        """
        Draw edges from NetworkX graph.

        **Parameters**

        g : `nx.DiGraph`
            NetworkX graph of organisation built from yaml_data
        pos : `Dict`
            Dictionary of tuples of (x,y) positions of all nodes
        cstyle : `str`
            Style to use for edges.  Can be one of: ['arc','arc3','angle','angle3'].

        **Returns**

        """
        logger.info(f"OrganisationDiagrammer::draw_networkx_edges() - cstyle={cstyle}")
        # 1. Pull out the different relationships for edges
        # Can be 1 for direct management, 2 for indirect management, 3 for a perm yet to join, 4 for a perm leaving.
        e_direct = [
            (u, v) for (u, v, d) in g.edges(data=True) if d.get("relationship") == 1
        ]
        e_indirect = [
            (u, v) for (u, v, d) in g.edges(data=True) if d.get("relationship") == 2
        ]
        e_starting = [
            (u, v) for (u, v, d) in g.edges(data=True) if d.get("relationship") == 3
        ]
        e_leaving = [
            (u, v) for (u, v, d) in g.edges(data=True) if d.get("relationship") == 4
        ]

        # styles - see: https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.Patch.html#matplotlib.patches.Patch.set_linestyle
        def drawNetworkXEdges(elist: List, w: int, a: float, color: str, style: str):
            nx.draw_networkx_edges(
                g,
                pos,
                connectionstyle=cstyle,
                edgelist=elist,
                width=w,
                alpha=a,
                edge_color=color,
                style=style,
            )

        drawNetworkXEdges(e_direct, 4, 0.8, "g", "solid")
        drawNetworkXEdges(e_indirect, 4, 0.8, "g", "dotted")
        drawNetworkXEdges(e_starting, 4, 0.8, "teal", "dotted")
        drawNetworkXEdges(e_leaving, 4, 0.8, "orange", "dotted")

    def draw_networkx_edge_labels(
        self,
        g: nx.DiGraph,
        pos: Dict,
        cstyle: str,
        font_size: int,
        using_edge_labels: bool,
        edge_label_height: float,
    ):
        """
        Draw edge labels from NetworkX graph controlling position and size.

        **Parameters**

        g : `nx.DiGraph`
            NetworkX graph of organisation built from yaml_data
        pos : `Dict`
            Dictionary of tuples of (x,y) positions of all nodes
        cstyle : `str`
            Style to use for edges.  Can be one of: ['arc','arc3','angle','angle3'].
        font_size : `int`
            Font size for text labels.  12 by default.
        using_edge_labels : `bool`
            True if we are using edge labels.
        edge_label_height : `int`
            Edge label height if we are using edge labels.

        **Returns**

        """
        logger.info(
            f"OrganisationDiagrammer::draw_networkx_edge_labels() - cstyle={cstyle}, using_edge_labels={using_edge_labels}"
        )
        # node that our edge labels are now pulled from our nodes
        # node labels - rotate edge labels to be horizontal
        size = font_size
        if using_edge_labels:
            edge_labels = dict(
                [
                    (
                        (
                            u,
                            v,
                        ),
                        d.get("label"),
                    )
                    for u, v, d in g.edges(data=True)
                ]
            )
            if cstyle in ["arc", "arc3"]:
                text = nx.draw_networkx_edge_labels(
                    g,
                    pos,
                    font_size=size,
                    edge_labels=edge_labels,
                    label_pos=edge_label_height,
                )
            elif cstyle in ["angle", "angle3"]:
                text = nx.draw_networkx_edge_labels(
                    g, pos, font_size=size, edge_labels=edge_labels, label_pos=0.15
                )
            for _, t in text.items():
                t.set_rotation("horizontal")

    def draw_networkx_text_labels(
        self, g: nx.DiGraph, pos: Dict, font_size: int, offset: float
    ):
        """
        Draw text annotations for note and team on node cells from NetworkX graph.

        **Parameters**

        g : `nx.DiGraph`
            NetworkX graph of organisation built from yaml_data
        pos : `Dict`
            Dictionary of tuples of (x,y) positions of all nodes
        font_size : `int`
            Font size for text labels.  12 by default.
        offset : `float`
            Offset for text elements.  Default is 0

        **Returns**

        """
        logger.info(
            f"OrganisationDiagrammer::draw_networkx_text_labels() - font_size={font_size}, offset={offset}"
        )

        # note labels - rotate edge labels to be horizontal
        def drawTextField(y: float, text: str, size: float, fcolor: str = "none"):
            plt.text(
                x,
                y,
                s=text,
                size=size,
                bbox=dict(facecolor=fcolor, edgecolor=ecolor, alpha=0.5),
                horizontalalignment="center",
            )

        n_note = [(u, d) for (u, d) in g.nodes(data=True) if d.get("note")]
        n_team = [(u, d) for (u, d) in g.nodes(data=True) if d.get("team")]
        n_jobtitle = [(u, d) for (u, d) in g.nodes(data=True) if d.get("jobtitle")]

        fcolor = "none"
        ecolor = "none"
        size = font_size
        for name, d in n_team:  # node team goes above the node
            x, y = pos.get(name)
            team = d.get("team")
            drawTextField(y + offset * 2, team, size * 1.5, fcolor)
        for name, d in n_note:  # node note goes inside the node
            x, y = pos.get(name)
            note = proc_field(d.get("note"), True)
            drawTextField(y - offset, note, size, fcolor)
        for name, d in n_jobtitle:  # jobtitle goes below the node
            x, y = pos.get(name)
            job = d.get("jobtitle")
            drawTextField(y - offset * 2, job, size * 1.25, fcolor)

    def create_graphviz_layout_from_graph(
        self,
        g: nx.DiGraph,
        cstyle: str,
        margin: float,
        offset: float,
        node_size: int,
        font_size: int,
        image_file: str = "org.png",
        scale: int = 5,
        resetScale: bool = True,
    ) -> nx.DiGraph:
        """
        Create graphviz generated visualisation of organisation from NetworkX graph.

        **Parameters**

        g : `nx.DiGraph`
            NetworkX graph of organisation built from yaml_data
        cstyle : `str`
            Style to use for edges.  Can be one of: ['arc','arc3','angle','angle3'].  Default is 'arc3'
        margin : `float`
            Margin between nodes.  Default is 0.1
        offset : `float`
            Offset for text elements.  Default is 0
        node_size : `int`
            Size of node.  Default is `DEFAULT_NODE_SIZE` (7000)
        font_size : `int`
            Size of node text
        image_file : `str`
            Target file for visualisation.  Default is `org.png`
        scale : `int`
            Scale of generated image
        resetScale : `bool`
            Whether to reset scale or not.

        **Returns**

        g : `nx.DiGraph`
            NetworkX graph of organisation built from yaml_data

        """
        logger.info(f"OrganisationDiagrammer::create_graphviz_layout_from_graph()")
        # Note the args here are inputs to dot.  Type dot -h to see options
        # See: https://renenyffenegger.ch/notes/tools/Graphviz/examples/organization-chart for an org chart example
        # See: https://stackoverflow.com/questions/57512155/how-to-draw-a-tree-more-beautifully-in-networkx for circo reference
        plt.clf()
        args = "-Gnodesep=3 -Granksep=0 -Gpad=0.1 -Grankdir=TB"
        pos = nx.nx_agraph.graphviz_layout(g, prog="dot", root=None, args=args)

        self.draw_networkx_nodes(g, pos, margin, node_size, font_size)
        self.draw_networkx_edges(g, pos, cstyle)
        using_edge_labels = False
        self.draw_networkx_edge_labels(
            g, pos, cstyle, font_size - 4, using_edge_labels, DEFAULT_EDGE_LABEL_HEIGHT
        )
        self.draw_networkx_text_labels(g, pos, font_size - 4, offset)

        logger.info(f'saving graph to "{image_file}"')
        plt.axis("off")
        params = plt.gcf()
        plSize = params.get_size_inches()
        params.set_size_inches((plSize[0] * scale, plSize[1] * scale))
        logger.info(f'plSize = {plSize}, setting image size to {plSize[0] * scale} by {plSize[1] * scale}')
        plt.savefig(image_file, bbox_inches="tight")
        if resetScale:
            # We need to reset the size of the figure to the original size
            params.set_size_inches((plSize[0], plSize[1]))
        return g

    def create_dotfile_from_graph(self, g: nx.DiGraph, dot_file: str) -> str:
        """
        Create dotfile from NetworkX graph.

        **Parameters**

        g : `nx.DiGraph`
            NetworkX graph of organisation built from yaml_data
        dot_file : `str`
            Name of target dot file to create.  eg. output.dot

        **Returns**

        dot_file : `str`
            Name of target dot file to create.  eg. output.dot

        """
        logger.info(
            f"OrganisationDiagrammer::create_dotfile_from_graph() - target={dot_file}"
        )
        # nx.drawing.nx_pydot is deprecated.
        # nx.drawing.nx_pydot.write_dot(g, dot_file)
        nx.nx_agraph.write_dot(g, dot_file)
        return dot_file

def main(arguments: Dict, open_image: bool=True):
    """
    main entry point for CLI.

    **Parameters**

    arguments : `Dict`
        Input arguments

    **Returns**

    """
    verbose = False
    cstyle = DEFAULT_CSTYLE
    node_size = DEFAULT_NODE_SIZE
    margin = DEFAULT_MARGIN
    offset = DEFAULT_OFFSET
    font_size = DEFAULT_FONT_SIZE
    logger = initLogger(False)
    target = "test.png"

    def setFloatValue(v, default):
        try:
            v = float(v)
        except:
            print(f"WARNING: Could not parse input margin, using {default}...")
            v = default
        return v

    if arguments.get("--verbose"):
        verbose = True
        logger = initLogger(verbose)
        logger.info(f"::main() - arguments =\n{arguments}")
    if arguments.get("--style"):
        cstyle = arguments.get("--style")[0]
        logger.info(f"cstyle = {cstyle}")
    if arguments.get("--margin"):
        margin = arguments.get("--margin")[0]
        margin = setFloatValue(margin, DEFAULT_MARGIN)
        logger.info(f"margin = {margin}")
    if arguments.get("--nodesize"):
        node_size = arguments.get("--nodesize")[0]
        node_size = int(setFloatValue(node_size, DEFAULT_NODE_SIZE))
        logger.info(f"node_size = {node_size}")
    if arguments.get("--fontsize"):
        font_size = arguments.get("--fontsize")[0]
        font_size = int(setFloatValue(font_size, DEFAULT_FONT_SIZE))
        logger.info(f"fontsize = {font_size}")
    if arguments.get("--offset"):
        offset = arguments.get("--offset")[0]
        offset = setFloatValue(offset, DEFAULT_OFFSET)
        logger.info(f"offset = {offset}")
    if arguments.get("--source"):
        source = str(arguments.get("--source")[0])
        try:
            assert os.path.exists(source)
            logger.info(f"source = {source}")
        except:
            print(f'ERROR: Could not find "{source}". Exiting...')
            sys.exit()
    if arguments.get("--version") or arguments.get("-V"):
        print(f"{PROGRAM} version {VERSION}.  Released {DATE} by {AUTHOR}")
    elif arguments.get("--help") or arguments.get("-h"):
        print(usage)
    else:
        t0 = time.time()
        org = OrganisationDiagrammer(margin=margin, node_size=node_size)
        data = org.load_yaml_file(source)
        graph = org.create_graph_from_yaml(data)
        target = source[:-5] + ".dot"
        dotfile = org.create_dotfile_from_graph(graph, target)
        print(
            f"Successfully created dot file {dotfile} of size"
            f" {get_file_size(dotfile)}kB"
        )
        image = source[:-5] + ".png"
        org.create_graphviz_layout_from_graph(
            graph,
            margin=margin,
            cstyle=cstyle,
            node_size=node_size,
            offset=offset,
            font_size=font_size,
            image_file=image,
        )
        print(
            f"Successfully generated organogram into file {image} of size"
            f" {get_file_size(image)}kB"
        )
        if open_image:
            Image.open(image).show()
        t1 = time.time()
        print(
            f"successfully processed {source} YAML to generate {image} in {round((t1-t0),2)} seconds"
        )

if __name__ == "__main__":
    usage = """
    {}
    ----------------
    Usage:
    {} -s <source> [-m <margin>] [-n <nodesize>] [-f <style>] [-o <offset>] [-x <fontsize>] [-v]
    {} -h | --help
    {} -V | --version
    Options:
    -h, --help                              Show this screen.
    -v, --verbose                           Verbose mode.
    -V, --version                           Show version.
    -s <source>, --source <source>          Source YAML.
    -n <nodesize>, --nodesize <nodesize>    Node size.  Default is 7000.
    -m <margin>, --margin <margin>          Margin.  Default 0.1.
    -f <style>, --style <style>             Edge style. Default is arc3.
    -o <offset>, --offset <offset>          Offset.  Default is 0.
    -x <fontsize>, --fontsize <fontsize>    Font size of node text.  Default is 12.
    Examples
    1. Generate verbose graphviz visualisation of test.yaml:
    {} -s test.yaml --margin 0.2 -f angle3 -n 7500 --offset 8 -x 16 -v
    2. Generate graphviz visualisation of tycoon.yaml:
    {} -s tycoon.yaml --margin 0.2 -f angle -n 15000 --offset 3 -x 18
    3. Generate graphviz visualisation of homeowner.yaml:
    {} -s homeowner.yaml --margin 0.01 -f arc -n 7500 -o 5 -x 14
    """.format(
        *tuple([PROGRAM] * 7)
    )
    arguments = docopt.docopt(usage)
    main(arguments)
