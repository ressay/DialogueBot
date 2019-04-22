# Auto generated file #
from rdflib import Graph,URIRef
import os
import inspect


graph = Graph()
root = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
root += '/OwlFiles/'
f = root+'onto_browser.owl'
graph.parse(f,format='turtle')

# PREFIXES #

prefix1 = "http://www.semanticweb.org/ressay/ontologies/2019/2/untitled-ontology-7#"


# CLASSES #

RegFile = URIRef(prefix1+"RegFile")
Create_file = URIRef(prefix1+"Create_file")
File = URIRef(prefix1+"File")
A_request = URIRef(prefix1+"A_request")
User = URIRef(prefix1+"User")
Act_parameter = URIRef(prefix1+"Act_parameter")
Open_file = URIRef(prefix1+"Open_file")
Dialogue_act = URIRef(prefix1+"Dialogue_act")
User_act = URIRef(prefix1+"User_act")
Desire = URIRef(prefix1+"Desire")
Agent = URIRef(prefix1+"Agent")
U_request = URIRef(prefix1+"U_request")
Directory = URIRef(prefix1+"Directory")
Agent_act = URIRef(prefix1+"Agent_act")
U_inform = URIRef(prefix1+"U_inform")
A_ask = URIRef(prefix1+"A_ask")
A_inform = URIRef(prefix1+"A_inform")
Change_directory = URIRef(prefix1+"Change_directory")
Dialogue = URIRef(prefix1+"Dialogue")
Agent_action = URIRef(prefix1+"Agent_action")
Delete_file = URIRef(prefix1+"Delete_file")


# RELATIONS #

# relation's domains: Dialogue
# relation's ranges: Dialogue_act
contains_act = URIRef(prefix1+"contains_act")
# relation's domains: RegFile
# relation's ranges: string
has_extension = URIRef(prefix1+"has_extension")
# relation's domains: Directory
# relation's ranges: File
contains_file = URIRef(prefix1+"contains_file")
# relation's domains: File
# relation's ranges: Literal
has_name = URIRef(prefix1+"has_name")
# relation's domains: Dialogue_act
# relation's ranges: Dialogue_act
next_act = URIRef(prefix1+"next_act")
# relation's domains: User
# relation's ranges: User_act
u_acted = URIRef(prefix1+"u_acted")
# relation's domains: Change_directory
# relation's ranges: Directory
change_dir_to = URIRef(prefix1+"change_dir_to")
# relation's domains: User
# relation's ranges: Desire
has_desire = URIRef(prefix1+"has_desire")
# relation's domains: Agent
# relation's ranges: Agent_act
a_acted = URIRef(prefix1+"a_acted")
# relation's domains: User
# relation's ranges: Agent_action
confirm = URIRef(prefix1+"confirm")
# relation's domains: Dialogue_act
# relation's ranges: Act_parameter
has_parameter = URIRef(prefix1+"has_parameter")
# relation's domains: User
# relation's ranges: Agent_action
deny = URIRef(prefix1+"deny")
