from oncall import db

import re
from unicodedata import normalize
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def slugify(text, delim=u'-'):
    """Generates an slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', unicode(word)).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))

class Team(db.Model):
    __tablename__ = 'teams'
    slug = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(200))

    # TODO: This needs to be in a higher class and is inherited
    _hide_command = []

    def __init__(self, name):
        '''
        name - Team name
        '''
        self.name = name
        self.slug = slugify(name)

    def to_json(self):
        return dict(name=self.name,
                    id=self.slug)

    def __repr__(self):
        return '<Team %r>' % self.name
