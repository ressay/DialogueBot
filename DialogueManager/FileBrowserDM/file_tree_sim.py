import random
from rdflib import Graph, BNode, Literal
import Ontologies.python_from_ontology as onto
import Ontologies.onto_fbrowser as fbrowser

FILE = 1
DIR = 0


class FileTreeSimulator(object):
    def __init__(self, tree=None, name='~', parent=None) -> None:
        """
        creates a simulator of a file tree (add/delete/move/copy actions)
        :param (str) name: name of parent dir
        :param (FileTreeSimulator) parent: parent directory simulator
        :param (list) tree: if None: creates random file tree, else creates corresponding file tree
                            list contains couples of integer,dict:
                                - integer: 1 if regular file, 0 if directory
                                - dict: contains data about file such as name, tree (for subtree),
                                node (ontology BNode object)
        """
        super().__init__()
        self.tree_map = {}
        self.parent_node = BNode()
        self.parent = parent
        # if parent is not None:
        #     self.graph = parent.graph
        # else:
        #     self.graph = Graph()
        #     self.graph.add((self.parent_node, onto.rdf_type, fbrowser.Directory))
        #     self.graph.add((self.parent_node, fbrowser.has_name, Literal(name)))
        self.name = name
        if tree is None:
            tree = self.generate_random_tree()
        self.addAll_tree(tree)
        # self.graph, self.tree = self.create_rdfgraph_from_tree(tree)
        # if parent_graph is not None:
        #     parent_graph += self.graph
        #     self.graph = parent_graph

    def generate_random_tree(self, max_width=3, max_height=2, proba_width=0.5, counts=None):
        """
        generate file tree to be created by the dialogue manager
        :param (list) counts: contains 2 integers, count of created files, and count of created directories
        :param (int) max_width: max number of files/directories in same directory
        :param (int) max_height: max number of sub-directories in the tree
        :param (float) proba_width: ratio of files created (from max_width) in a single directory
        :return (list) : list of couples where first element is integer: 1 if it's a file, 0 directory
                         the second element is a list: empty if file, sub-tree if directory
        """
        if counts:
            countf, countd = counts
        else:
            countf, countd = 1, 1
            counts = [1, 1]
        if not max_height:
            return []
        tree = [(int(random.uniform(0, 2)), {'name': "", 'sub_tree': []})
                for i in range(max_width)
                if random.uniform(0, 1) < proba_width or not i]
        for i, l in tree:
            if i:
                name = 'file' + str(countf)
                countf += 1
            else:
                name = 'dir' + str(countd)
                countd += 1
            l['name'] = name
            if not i:
                counts[0], counts[1] = countf, countd
                sub_tree = self.generate_random_tree(max_width, max_height - 1, proba_width, counts)
                countf, countd = counts
                l['sub_tree'] = sub_tree
        return tree

    def create_rdfgraph_from_tree(self, tree, parent=None):
        """
        :param (list) tree: a tree as described above
        :param (rdflib.BNode) parent: parent directory of the tree
        :return (rdflib.Graph,list): couple contains:   - the resulting graph
                                                        - tree with updated dict (name + node entries)
        """

        g = Graph()
        for i, (file, m) in enumerate(tree):
            if file:
                Type = fbrowser.RegFile
            else:
                Type = fbrowser.Directory
            f = BNode()
            m['node'] = f
            g.add((f, onto.rdf_type, Type))
            g.add((f, fbrowser.has_name, Literal(m['name'])))
            if parent:
                g.add((parent, fbrowser.contains_file, f))

            if not file:
                subg = self.create_rdfgraph_from_tree(m['tree_sim'].tree, f)
                g += subg

        return g

    def get_first_dissimilarity(self, goal_tree, inverse=True):
        """
        gets first file which is not found in both trees
        :param (bool) inverse: if search dissimilarity from goal tree to self
        :param (FileTreeSimulator) goal_tree:
        :return (integer,dict,integer) : integer and dict are file's description if dissimilarity found
                                        last integer is 1 if found in goal_tree not in self
                                                        0 if found in self not in goal_tree
                                        None if no dissimilarity found
        """
        # look for file in self tree but not in goal_tree
        dir_stack = []
        for f, m in self.tree():
            n = m['name']
            if n not in goal_tree.tree_map:
                return f, m, 0
            f1, m1 = goal_tree.get_file_by_name(n)
            if f1 != f:
                return f1, m1, 1
            if not f:  # if it's a directory
                dir_stack.append((m, m1))
        for m, m1 in dir_stack:
            d = m['tree_sim'].get_first_dissimilarity(m1['tree_sim'])
            if d is not None:
                return d
        if inverse:
            d = goal_tree.get_first_dissimilarity(self, False)
            if d is not None:
                f, m, _ = d
                return f, m, 1
        return None

    def tree_similarity(self, goal_tree, inverse=True):
        """
        calculates how many files are shared in both trees at the same position in the tree
        :param (bool) inverse: if count similarity from goal_tree with self
        :param (FileTreeSimulator) goal_tree: tree to compare with self tree
        :return (integer,integer) : number of shared files and total number of files in self tree
        """
        total = goal_tree.r_size()
        found = 0
        for f, m in goal_tree.tree_map.values():
            n = m['name']
            if n in self.tree_map:
                f1, m1 = self.get_file_by_name(n)
                found += (f1 == f) * 1
                if not f:
                    found1, _ = m1['tree_sim'].tree_similarity(m['tree_sim'], False)
                    found += found1
        if inverse:
            total += self.r_size() - found
        # if inverse:
        #     f, t = goal_tree.tree_similarity(self, False)
        #     total += t
        #     found += f
        return found, total

    def create_random_tree_rdfgraph(self):
        tree = self.generate_random_tree()
        return self.create_rdfgraph_from_tree(tree)

    def get_file_dict_from_path(self, path):
        p = self.path()
        if path[:len(p)] == p:
            path = path[len(p):]
        dirs = path.split('/')
        if dirs[-1] == '':
            del dirs[-1]
        if not len(dirs):
            return None
        assert dirs[0] in self.tree_map, path + ' does not exist'
        f, m = self.get_file_by_name(dirs[0])
        for name in dirs[1:]:
            tree = m['tree_sim']
            assert tree.contains_file(name), path + ' does not exist'
            f, m = tree.get_file_by_name(name)
        return f, m

    def add_to_ontology(self, t, name, m, parent):
        f = m['tree_sim'].parent_node
        m['node'] = f
        if t:
            Type = fbrowser.RegFile
        else:
            Type = fbrowser.Directory
        self.graph.add((f, onto.rdf_type, Type))
        self.graph.add((f, fbrowser.has_name, Literal(name)))
        if parent:
            self.graph.add((parent, fbrowser.contains_file, f))

    def addAll_tree(self, tree):
        for f, l in tree:
            f, m = self.add_file(l['name'], f)
            if not f:
                if 'sub_tree' in l:
                    m['tree_sim'].addAll_tree(l['sub_tree'])
                elif 'tree_sim' in l:
                    m['tree_sim'].addAll_tree(l['tree_sim'].tree())

    def create_path(self,path):
        p = self.path()
        if path[:len(p)] == p:
            path = path[len(p):]
        dirs = path.split('/')
        if dirs[-1] == '':
            del dirs[-1]
        if not len(dirs):
            return
        if not self.contains_file(dirs[0]):
            f,m = self.add_file(dirs[0],DIR)
        else:
            f, m = self.get_file_by_name(dirs[0])
        for name in dirs[1:]:
            if not m['tree_sim'].contains_file(name):
                f,m = m['tree_sim'].add_file(name,DIR)
            else:
                f,m = m['tree_sim'].get_file_by_name(name)

    def add_file(self, file_name, t, p=None,create_path=False):
        if not p:
            tree_map = self.tree_map
            parent_node = self.parent_node
        else:
            if create_path:
                self.create_path(p)
            r = self.get_file_dict_from_path(p)
            if r is None:
                tree_map = self.tree_map
                parent_node = self.parent_node
            else:
                f, m = r
                parent = m['tree_sim']
                return parent.add_file(file_name, t)
        file_data = (t, {'tree_sim': FileTreeSimulator([], file_name, self),
                         'name': file_name, 'parent': self})
        tree_map[file_name] = file_data
        # self.add_to_ontology(t, file_name, file_data[1], parent_node)
        return file_data

    def remove_file(self, file_name, p=None):
        if not p:
            tree_map = self.tree_map
        else:
            r = self.get_file_dict_from_path(p)
            if r is None:
                tree_map = self.tree_map
            else:
                f, m = r
                parent = m['tree_sim']
                parent.remove_file(file_name)
                return
        if file_name not in tree_map:
            return False
        f, m = tree_map[file_name]
        del tree_map[file_name]
        # node = m['node']
        # self.graph.remove((node, None, None))
        # self.graph.remove((None, None, node))
        return True

    def get_file_by_name(self, name):
        """
        gets file type and dict of file data
        :param (str) name: name of file
        :return (integer,list): as described in tree content
        """
        return self.tree_map[name]

    def contains_file(self, name):
        return name in self.tree_map

    def lookup_file_name(self, name):
        if self.contains_file(name):
            return self.get_file_by_name(name)
        for f, m in self.tree_map.values():
            if not f:
                file = m['tree_sim'].lookup_file_name(name)
                if file is not None:
                    return file
        return None

    def get_random_directory(self):
        if not self.size():
            return self
        p1 = 0.33
        p2 = 2.0 / self.size()
        for f, m in self.tree():
            r = random.uniform(0, 1)
            if not f and r < p2:
                if random.uniform(0, 1) < p1:
                    return m['tree_sim']
                return m['tree_sim'].get_random_directory()
        return self

    def tree(self):
        return list(self.tree_map.values())

    def size(self):
        return len(self.tree_map)

    def r_size(self):
        total = self.size()
        for f,m in self.tree():
            if not f:
                total += m['tree_sim'].r_size()
        return total

    def path(self):
        if self.parent is None:
            return self.name + '/'
        return self.parent.path() + self.name + '/'

    def print_ontology(self):
        for s, p, o in self.graph:
            print(s, p, o)

    def print_tree(self, tree=None, offset='->'):
        if tree is None:
            tree = self.tree()
            print("root:")
        for f, m in tree:
            print(offset, m['name'])
            if not f:
                self.print_tree(m['tree_sim'].tree(), offset[:-1] + '-->')

    def copy(self):
        return FileTreeSimulator(self.tree(), name=self.name, parent=self.parent)


if __name__ == '__main__':
    sim1 = FileTreeSimulator([])
    sim2 = FileTreeSimulator([])
    sim1.add_file('my_file', FILE)
    sim1.add_file('direct', DIR)
    print(sim2.get_first_dissimilarity(sim1))
    sim2.add_file('my_file', FILE)
    print(sim1.get_first_dissimilarity(sim2))
    sim2.add_file('direct', DIR)
    print(sim1.get_first_dissimilarity(sim2))
    f, m = sim1.add_file('ff', FILE, '~/direct/')
    sim1.print_tree()
    print(sim1.get_first_dissimilarity(sim2))
    print(m['tree_sim'].path())
    print(sim1.lookup_file_name('ff'))

    sim1_copy = sim1.copy()
    sim1_copy.add_file('khobz', DIR, "~/")
    sim1.print_tree()
    sim1_copy.print_tree()
    print(sim1_copy.r_size())
    sim1.print_tree()
    sim1.create_path('lala/lolo/lili')
    sim1.print_tree()
    sim1.add_file('newf',1,'lala/haha',True)
    sim1.print_tree()
    # sim1.print_ontology()
    # sim1.remove_file('my_file')
    # sim1.print_tree()
    # sim1.print_ontology()
    # print(sim1.generate_random_tree())
    # sim3 = FileTreeSimulator()
    # sim3.print_tree()
    # sim4 = FileTreeSimulator()
    # sim4.print_tree()
    # print(sim3.tree_similarity(sim4))
    # sim3.print_ontology()
