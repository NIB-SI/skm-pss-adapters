'''
Utility functions for PSS exports.
'''

#-------------------------------------
#  Utility functions
#-------------------------------------

def clean_list(l):
    ''' replace None with '' '''
    for i, v in enumerate(l):
        if v is None:
            l[i] = ''
    return l

