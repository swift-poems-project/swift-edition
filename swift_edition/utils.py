
import importlib

tokenizer_modules = {'SwiftSentenceTokenizer': 'swift_collate.tokenize',
                     'PunktSentenceTokenizer': 'swift_collate.tokenize',
                     'TreebankWordTokenizer': 'nltk.tokenize.treebank',
                     'StanfordTokenizer': 'nltk.tokenize.stanford'}

def tokenizer_module(tokenizer_class_name):

    if tokenizer_class_name in tokenizer_modules:
        module = tokenizer_modules[tokenizer_class_name]
    else:
        raise Exception("Failed to locate the tokenizer Module for %s" % tokenizer_class_name)

    return module

tagger_modules = {'AveragedPerceptron': 'nltk.tag.perceptron.AveragedPerceptron',
                  'UnigramTagger': 'nltk.tag.sequential.UnigramTagger'}
def tagger_module(tagger_class_name):

    if tagger_class_name == 'disabled':
        module = None
    elif tagger_class_name in tagger_modules:
        module = tagger_modules[tagger_class_name]
    else:
        raise Exception("Failed to locate the tagger Module for %s" % tagger_class_name)

    return module

class TokenizerFactory:

    def __init__(self, tokenizer_class_name):
        try:
            module_name = tokenizer_module(tokenizer_class_name)
            m = importlib.import_module(module_name)
            self.klass = getattr(m, tokenizer_class_name)
        except:
            raise "Could not load the selected tokenizer"

class TaggerFactory:

    def __init__(self, tagger_class_name):

        if tagger_class_name == 'disabled':
            self.tagger = None
        else:
            try:
                module_name = tagger_module(tagger_class_name)
                m = importlib.import_module(module_name)
                tagger_class = getattr(m, tagger_class_name)
                self.tagger = tagger_class()
            except Exception as tagger_ex:
                raise Exception("Could not load the selected part-of-speech tagger %s" % tagger_ex)

# See https://github.com/jupyter/nbviewer/blob/master/nbviewer/utils.py
def url_path_join(*pieces):
    """Join components of url into a relative url
    Use to prevent double slash when joining subpath. This will leave the
    initial and final / in place
    """
    initial = pieces[0].startswith('/')
    final = pieces[-1].endswith('/')
    stripped = [s.strip('/') for s in pieces]
    result = '/'.join(s for s in stripped if s)
    if initial:
        result = '/' + result
    if final:
        result += '/'
    if result == '//':
        result = '/'
    return result
