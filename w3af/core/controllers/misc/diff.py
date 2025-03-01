"""
diff.py

Copyright 2008 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import difflib
import diff_match_patch as dmp_module

from w3af.core.data.misc.encoding import smart_str_ignore, smart_unicode

# 20 seconds it the max time we'll wait for a diff, the good thing
# about the `diff_match_patch` library is that even when the timeout
# is reached, a (partial) result is returned
MAX_DIFF_TIME = 20

#
# Translation table to split strings by multiple chars
#
# The only issue with this method is that it will yield "false positives" when
# the string to split has null bytes, but that is acceptable due to the performance
# improvement gains
#
TRANSLATION_TABLE = str.maketrans('\n\t\r"\'<',
                                     '\0\0\0\0\0\0')


def diff_dmp(a, b):
    """
    :param a: A string
    :param b: A string (similar to a)
    :return: Two strings (a_mod, b_mod) which are basically:

                a_mod = a - (a intersection b)
                b_mod = b - (a intersection b)

             Or if you want to see it in another way, the results are the
             parts of the string that make it unique between each other.
    """
    a = smart_unicode(a)
    b = smart_unicode(b)

    dmp = dmp_module.diff_match_patch()
    dmp.Diff_Timeout = MAX_DIFF_TIME

    changes = dmp.diff_main(a,
                            b,
                            checklines=True)

    dmp.diff_cleanupSemantic(changes)

    a_changes = []
    b_changes = []

    for op, change in changes:
        if op == -1:
            a_changes.append(change)

        if op == 1:
            b_changes.append(change)

    a_changes = '\n'.join(a_changes)
    b_changes = '\n'.join(b_changes)

    return a_changes, b_changes


def diff_difflib(a, b):
    """
    WARNING! WARNING! WARNING! WARNING!

        This code is really slow! Use only if you need a lot of precision
        in the diff result! Use chunked_diff if precision is not what you
        aim for.

    WARNING! WARNING! WARNING! WARNING!

    :param a: A string
    :param b: A string (similar to a)
    :return: Two strings (a_mod, b_mod) which are basically:

                a_mod = a - (a intersection b)
                b_mod = b - (a intersection b)

             Or if you want to see it in another way, the results are the
             parts of the string that make it unique between each other.
    """
    # Performance enhancement: if the two strings are equal, don't even bother
    # calling difflib.SequenceMatcher()
    if a == b:
        return '', ''

    matching_blocks = difflib.SequenceMatcher(None, a, b).get_matching_blocks()
    removed_a = 0
    removed_b = 0

    for block in matching_blocks:
        a_index, b_index, size = block
        a = a[:a_index - removed_a] + a[a_index - removed_a + size:]
        b = b[:b_index - removed_b] + b[b_index - removed_b + size:]
        removed_a += size
        removed_b += size

    return a, b

def chunked_diff(a, b):
    """
    This is a performance hack around diff() which was required due to the large
    amount of time diff() took to process some HTTP responses.
    This method does the same as diff() but it will cut the string in chunks and
    process the list of chunks instead of the strings. This makes the whole process
    faster and more inaccurate.

    :param a: A string
    :param b: A string (similar to a)
    :return: See diff_difflib()
    """
    # Performance enhancement: if the two strings are equal, don't even bother
    # calling split_by_sep and diff_difflib()
    if a == b:
        return '', ''

    a_split = split_by_sep(a)
    b_split = split_by_sep(b)

    a_chunks, b_chunks = diff_difflib(a_split, b_split)
    return ''.join(a_chunks), ''.join(b_chunks)


def split_by_sep(sequence):
    """
    This method will split the HTTP response body by various separators,
    such as new lines, tabs, <, double and single quotes.

    This method is very important for the precision we get in chunked_diff!

    If you're interested in a little bit of history take a look at the git log
    for this file and you'll see that at the beginning this method was splitting
    the input in chunks of equal length (32 bytes). This was a good initial
    approach but after a couple of tests it was obvious that when a difference
    (something that was in A but not B) was found the SequenceMatcher got
    desynchronized and the rest of the A and B strings were also shown as
    different, even though they were the same but "shifted" by a couple of
    bytes (the size length of the initial difference).

    After detecting this I changed the algorithm to separate the input strings
    to this one, which takes advantage of the HTML format which is usually
    split by lines and organized by tabs:
        * \n
        * \r
        * \t

    And also uses tags and attributes:
        * <
        * '
        * "

    The single and double quotes will serve as separators for other HTTP
    response content types such as JSON.

    Splitting by <space> was an option, but I believe it would create multiple
    chunks without much meaning and reduce the performance improvement we
    have achieved.

    :param sequence: A string which we will split
    :return: A list of strings (chunks) for the input string
    """
    #
    # There was a previous version of this algorithm which used python code
    # and a few performance tricks [0], but this is MUCH faster and easier to
    # read.
    #
    # This code with translate and split runs 1000 loops of test_split_by_sep_perf
    # in 0.17 seconds, while the older code [0] run the same test in 4.5 seconds.
    #
    # Just when you think it is impossible to improve the performance of a simple
    # algorithm... a new idea appears and reduces the time from 4.5 to 0.17...
    # amazing!
    #
    # [0] https://github.com/andresriancho/w3af/blob/2ded693c959c91dc3e4daca276460d6c64ada479/w3af/core/controllers/misc/diff.py#L173
    #
    if isinstance(sequence, bytes):
        sequence = smart_unicode(sequence)
    try:
        translated_seq = str.translate(sequence, TRANSLATION_TABLE)
    except UnicodeDecodeError:
        translated_seq = str.translate(sequence.encode('utf-8'), TRANSLATION_TABLE)
    return translated_seq.split('\0')
