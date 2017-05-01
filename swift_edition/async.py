
from swift_collate.collate import DifferenceText
from swift_collate.tokenize import SwiftSentenceTokenizer

def compare(args):
    """Compares two <tei:text> Element trees

    :param _args: The arguments passed (within the context of invocation using a ProcessPoolExecutor instance)
    :type _args: tuple
    """

    base_text = args[0]
    other_text = args[1]

    diff = DifferenceText(base_text, [other_text], SwiftSentenceTokenizer)
    diff.tokenize()
    
    return diff

def merge(args):
    """Merges the results of two DifferenceText instances

    :param args: Arguments passed from the ProcessPoolExecutor
    
    """

    text_u, text_v = args
    return text_u.merge(text_v, align=False)

def collate_async(executor, base_text, witness_texts, poem_id, base_id, log_callback, socket=True):
    """Collates a set of texts asynchronously

    :param executor: 
    :type executor: 
    """

    # Collate the witnesses in parallel
    compare_args = map( lambda witness_text: (base_text, witness_text), witness_texts )

    # Update the status of the collation
    for base_text, other_text in compare_args:
        if socket:
            log_callback("Comparing " + other_text.id + " to " + base_text.id + "...")

    diff_texts = executor.map( compare, compare_args )


    # Update the status of the collation
    for base_text, other_text in compare_args:
        if socket:
            log_callback("Collating " + other_text.id + "...")

    base_diff_text = DifferenceText(base_text, [], SwiftSentenceTokenizer)

#    merge_args = map( lambda diff_text: (base_diff_text, diff_text), diff_texts )
#    print merge_args
#    diff_texts = executor.map( merge, merge_args )

    # merge_args = [ base_diff_text ].extend(diff_texts)
    # results = executor.reduce( merge, merge_args )
    # return results

    for diff_text in diff_texts:
        # base_diff_text.merge(diff_text, align=False)
        executor.submit(merge, (base_diff_text, diff_text)).result()

    result = base_diff_text
    return result
