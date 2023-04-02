# orgcharts

### Overview
Thsi repo contains a Jupyterlab notebook called [`engineering-org-chart-zero.ipynb`](engineering-org-chart-zero.ipynb) which contains support to allow us to create organograms using the [`organogram.py`](organogram.py) module.  This module leverages the Python `networkx.py` library to draw an organisation diagram directly from a dot file.  

### Installation
Create a virtualenv and 
```
$ pip install -r requirements.txt
```

### Generating the dot file
The following code illustrates how to create a dot file from a YAML organisation structure held in [test.yaml](test.yaml).

```
import os
from organogram import OrganisationDiagrammer

org = OrganisationDiagrammer()
g = org.create_graph_from_yaml(org.load_yaml_file('test.yaml'),newline=True)
dotfile = org.create_dotfile_from_graph(g, dot_file='test.dot')
```

The generated dot file can be loaded into a corresponding editor tool such as [Graphity](https://www.graphity.com/).  Graphity allows us to modify the visualisation to a hierarchical layout as follows:

<img width="1715" alt="image" src="https://user-images.githubusercontent.com/12896870/228997347-f14454d6-12e7-4d78-beaa-ec9c619af93f.png">

Once loaded into Graphity, the organisation diagram elements can then be individually updated and stylee:

<img width="1715" alt="image" src="https://user-images.githubusercontent.com/12896870/228997547-14efeb67-614e-4c32-8685-5175673e971b.png">

### Generating a standalone org chart
Alternatively we can generate an inline image as follows:

```
import os
from organogram import OrganisationDiagrammer

target = 'test.png'
org.create_graphviz_layout_from_graph(g, scale=4, cstyle='arc', node_size=12000, image_file=target)
size = os.path.getsize(target)/1024
print(f'Successfully generated organogram into file {target} of size {size}kB')
```

Note the following:
* Managers have a thick black border around their box.
* Employees who are leaving are in orange
* Employees who are yet to join are in teal
* Employees who are moving to another team are in light green
* Contractors are in grey
* All other employees are in dark green
* Direct line management in indicated in a solid line
* Indirect management/supervision is indicated by a dotted line

<img width="1500" alt="image" src="test.png">

We can generate a version with right angles that looks more like an org chart as follows:

```
import os
from organogram import OrganisationDiagrammer

target = 'test.png'
org.create_graphviz_layout_from_graph(g, scale=4, cstyle='angle', node_size=12000, image_file=target)
size = os.path.getsize(target)/1024
print(f'Successfully generated organogram into file {target} of size {size}kB')
```

<img width="1500" alt="image" src="test2.png">

### Tests
Run the test code from the same directory with coverage as follows:
```
$ pytest --exitfirst --failed-first --cov=. --cov-report html -vv
```
