
from nltk.tokenize.punkt import PunktWordTokenizer
import networkx as nx

class TextToken:

    def __init__(self, ngram):

        self.value = ngram

class ElementToken:

    def __init__(self, element):

        self.name = element.name
        self.attributes = element.attrib

        # Generate a string consisting of the element name and concatenated attributes (for comparison using the edit distance)
        # Note: the attributes *must* be order by some arbitrary feature
        self.value = element.name

# The Fragment Entity passed to the Juxta visualization interface
class Fragment:

    def __init__(self, tokens):

        self.value

class Tokenizer:

    def __init__(self):

        pass

    # Construct the parse tree
    # Each element is a node distinct from the 
    def parse(node):

        token_tree = nx.Graph()
        token_tree_root = ElementToken(node)

        text_tokens = map(lambda token: (token_tree_root, Token(token)), PunktWordTokenizer().tokenize(text_node))
        token_tree.add_edges_from(text_tokens)
        
        if len(node.children) == 0:

            return token_tree
            
        return nx.compose(token_tree, map(self.parse, node.children))
