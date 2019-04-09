import DialogueManager.FileBrowserDM.onto_fbrowser as fbrowser

g = fbrowser.graph

for s,p,o in g.triples((fbrowser.User,None,None)):
    print(s,p,o)