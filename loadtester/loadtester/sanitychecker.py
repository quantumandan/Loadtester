import re
import string
from utils import all

class RegTemplate(string.Template):
    """
    Takes a $ delimited string and a dictionary of regular expressions
    who's keys are the template identifiers.  Each identifier is replaced by its 
    corresponding regular expression, forming the pattern for each log-entry.
    """
    
    # python automatically converts spaces to \s internally so no need
    # to explicitly account for them.  this is not true for all whitespace
    # so Your Mileage May Vary for regular expressions containing newlines,
    # carriage returns, etc.  also, not all special or non-alphanumeric 
    # characters are accounted for so caution.

    specials = [ '[' , ']' , ',' , '.', '\'' , '"' , '{', '}' , '?' , '-' , '+' , '(' , ')', '^', '&', '$', '|', '@']

    
    def __init__(self, template):
        super(RegTemplate, self).__init__(template)
        self.__isCompiled = False # prevents repeat compilation
        self.regex_dict = {}
        self.p = ''
        
    def compile(self, regex_dict):
        """
        Replaces each identifier with its corresponding regular expression.
        Additionally, turns each expression into a named group, indexed
        by its key in regex_dict.
        """        
        if not self.__isCompiled:
            self.__isCompiled = True
            for k, v in regex_dict.iteritems():
                self.regex_dict[k] = '(?P<%s>%s)' % (k, v)
            for s in RegTemplate.specials:
                # delimiter is normally $ sign, if this is not the case
                # the $ sign must be escaped while the delimiter is
                # left untouched. this feature may be removed in future versions
                if s == self.delimiter: continue
                # escape special characters
                self.template = self.template.replace(s, '\\' + s)
            # make private to prevent overriding string.Template.pattern
            self.p = self.substitute(**self.regex_dict)
        return self

    def xgroupdict(self, entry):
        if self.__isCompiled:
            named_groups = {}
            for name in self.regex_dict.keys():
                pattern = self.regex_dict[name]
                try:
                    named_groups[name] = re.search(pattern, entry).group(name)
                except:
                    named_groups[name] = None
            return named_groups
        else:
            raise 'RegTemplate object must be compiled'

    def groupdict(self, entry):
        """
        Returns a dictionary of the named groups.  Similar to re's
        groupdict method accept that in the case that a group isn't
        found its value is set to None.
        """
        named_groups = {}
        if self.__isCompiled:
            for name in self.regex_dict.keys():
                pattern = self.regex_dict[name]
                try:
                    named_groups[name] = re.match(pattern, entry).group(name)
                except:
                    named_groups[name] = None
            return named_groups
        else:
            raise 'RegTemplate object must be compiled'

    def verify(self, entry):
        if self.__isCompiled:
            d1 = self.groupdict(entry)
            line = self.substitute(d1).replace('\\', '')
            d2 = self.groupdict(line)
            tvs = []
            for name in self.regex_dict.keys():
                if d1[name] is None or d2[name] is None:
                    return False
                tvs.append(d1[name] == d2[name])
            return all(tvs)                    
        else:
            raise 'RegTemplate object must be compiled'
        

