"""
encoding.py

Copyright 2012 Andres Riancho

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
import codecs
import urllib.request, urllib.parse, urllib.error
import chardet
import logging
import io

from w3af.core.data.constants.encodings import DEFAULT_ENCODING

# Hiding awful logging messages generated by chardet module when running
# almost any unit test
logging.getLogger('chardet.charsetprober').setLevel(logging.WARNING)

# Custom error handling schemes registration
ESCAPED_CHAR = 'backslashreplace'
PERCENT_ENCODE = 'percent_encode'
HTML_ENCODE = 'html_encode_char'

def _return_html_encoded(encodingexc):
    """
    :return: &#xff when input is \xff
    """
    st = encodingexc.start
    en = encodingexc.end
    hex_encoded = "".join(hex(c)[2:] for c in encodingexc.object[st:en])

    return str('&#x' + hex_encoded), en

def _percent_encode(encodingexc):
    if not isinstance(encodingexc, UnicodeEncodeError):
        raise encodingexc

    st = encodingexc.start
    en = encodingexc.end

    return (
        '%s' % (urllib.parse.quote(encodingexc.object[st:en].encode('utf8')),),
        en
    )

codecs.register_error(PERCENT_ENCODE, _percent_encode)
codecs.register_error(HTML_ENCODE, _return_html_encoded)

def smart_unicode(s,
                  encoding=DEFAULT_ENCODING,
                  errors='strict',
                  on_error_guess=True,

                  # http://jamesls.com/micro-optimizations-in-python-code-speeding-up-lookups.html
                  _isinstance=isinstance,
                  _unicode=str,
                  _str=bytes
                  ):
    """
    Return the unicode representation of 's'. Decodes byte-strings using
    the 'encoding' codec.
    """
    if s is None:
        return ''

    if _isinstance(s, _unicode):
        return s
    
    if _isinstance(s, _str):
        try:
            s = s.decode(encoding, errors)
        except UnicodeDecodeError:
            if not on_error_guess:
                raise

            try:
                guessed_encoding = chardet.detect(s)['encoding']
            except TypeError:
                # https://github.com/andresriancho/w3af/issues/13819
                guessed_encoding = None

            if guessed_encoding is None:
                # Chardet failed to guess the encoding! This is really broken
                s = s.decode(encoding, 'ignore')
            else:
                try:
                    s = s.decode(guessed_encoding, errors)
                except UnicodeDecodeError:
                    s = s.decode(encoding, 'ignore')
    else:
        if hasattr(s, '__unicode__'):
            try:
                # Read the pyar thread "__unicode__ deberia tomar los mismos
                # parametros que unicode() ?" to better understand why I can't
                # pass encoding and errors parameters here:
                s = _unicode(s)
            except UnicodeDecodeError:
                # And why I'm doing it here:
                s = _str(s)
                s = smart_unicode(s, encoding=encoding, errors=errors,
                                  on_error_guess=on_error_guess)
        else:
            s = _str(s)
            s = smart_unicode(s, encoding=encoding, errors=errors,
                              on_error_guess=on_error_guess)

    return s


def smart_str(s,
              encoding=DEFAULT_ENCODING,
              errors='strict',

              # http://jamesls.com/micro-optimizations-in-python-code-speeding-up-lookups.html
              _isinstance=isinstance,
              _unicode=str,
              _str=bytes):
    """
    Return a byte-string version of 's', encoded as specified in 'encoding'.
    """
    if s is None:
        return b''

    if _isinstance(s, _unicode):
        return s.encode(encoding, errors)

    # Already a byte-string, nothing to do here
    if _isinstance(s, _str):
        return s

    if _isinstance(s, io.BytesIO):
        return s.__str__()

    if hasattr(s, '__bytes__'):
        return s.__bytes__()

    # Handling objects is hard! Each implements __str__ in a different way
    # which might trigger issues
    try:
        return _str(s)
    except UnicodeEncodeError:
        # This will raise an exception if errors is strict, or return a
        # string representation of the object
        try:
            unicode_s = _unicode(s)
        except UnicodeEncodeError:
            if errors == 'strict':
                raise

            return ''
        else:
            return smart_str(unicode_s, encoding=encoding, errors=errors)


def smart_str_ignore(s, encoding=DEFAULT_ENCODING):
    return smart_str(s, encoding=encoding, errors='ignore')


def is_known_encoding(encoding):
    """
    :return: True if the encoding name is known.

    >>> is_known_encoding('foo')
    False
    >>> is_known_encoding('utf-8')
    True
    """
    try:
        codecs.lookup(encoding)
        return True
    except LookupError:
        return False
