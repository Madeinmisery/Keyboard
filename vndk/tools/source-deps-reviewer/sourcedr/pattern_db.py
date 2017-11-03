#!/usr/bin/env python3


class PatternDB(object):
    """Pattern database for patterns to be searched in the source tree.
    """

    DEFAULT_NAME = 'pattern_db.csv'


    @classmethod
    def create_default_database(cls, path):
        with open(path, 'w') as f:
            f.write('1,\\bdlopen\\b\n')


    def __init__(self, path):
        self.path = path
        self.data = self._load()


    def _load(self):
        with open(self.path, 'r') as f:
            patterns = []
            is_regexs = []
            for line in f:
                line = line.rstrip('\n')
                sp = line.split(',')
                is_regexs.append(sp[0])
                patterns.append(','.join(sp[1:]))
        return (patterns, is_regexs)


    def load(self):
        self.data = self._load()
        return self.data


    def save_new_pattern(self, patt, is_regex):
        """Add a pattern to the database."""
        with open(self.path, 'a') as f:
            f.write(str(int(is_regex)) + ',' + patt + '\n')
