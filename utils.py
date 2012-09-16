

import re
from urlparse import urljoin
#from BeautifulSoup import BeautifulSoup
#
#def sanitizeHtml(value, base_url=None):
#    rjs = r'[\s]*(&#x.{1,7})?'.join(list('javascript:'))
#    rvb = r'[\s]*(&#x.{1,7})?'.join(list('vbscript:'))
#    re_scripts = re.compile('(%s)|(%s)' % (rjs, rvb), re.IGNORECASE)
#    validTags = 'p i strong b u a h1 h2 h3 pre br img'.split()
#    validAttrs = 'href src width height'.split()
#    urlAttrs = 'href src'.split() # Attributes which should have a URL
#    soup = BeautifulSoup(value)
#    for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
#        # Get rid of comments
#        comment.extract()
#    for tag in soup.findAll(True):
#        if tag.name not in validTags:
#            tag.hidden = True
#        attrs = tag.attrs
#        tag.attrs = []
#        for attr, val in attrs:
#            if attr in validAttrs:
#                val = re_scripts.sub('', val) # Remove scripts (vbs & js)
#                if attr in urlAttrs:
#                    val = urljoin(base_url, val) # Calculate the absolute url
#                tag.attrs.append((attr, val))
#
#    return soup.renderContents().decode('utf8')


def get_context(request):
    context = {}

    username = request.cookies.get('username', None)
    if username:
        context['username'] = username

    is_admin = request.cookies.get('is_admin', None)
    if is_admin:
        context['is_admin'] = True
    else:
        context['is_admin'] = False

    is_employee = request.cookies.get('is_employee', None)
    if is_employee:
        context['is_employee'] = True
    else:
        context['is_employee'] = False

    return context

def make_employees():
    ''