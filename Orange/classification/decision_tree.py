from Orange.data import Table

from math import log2
from collections import defaultdict


def calculate_entropy(table):

    # Compute the frequency of each class.
    frequencies = defaultdict(int)
    for instance in table:
        c = instance.get_class()
        frequencies[str(c)] += 1
    #print(frequencies)

    # Compute the entropy
    entropy = 0
    for cls, freq in frequencies.items():
        prob = float(freq) / float(len(table))
        entropy -= prob*log2(prob)

    return entropy

    
def split_data(table, attribute):
    indexLists = defaultdict(list)
  
    for i, instance in enumerate(table):
        attr_val = instance[attribute]
        indexLists[str(attr_val)].append(i)

    subtables = defaultdict(Table)
    for key in indexLists:
        subtables[key] = Table.from_table_rows(table, indexLists[key])

    return subtables


def attribute_states(attribute):
    states = set()
    for instance in lenses_table:
        attr_val = instance[attribute]
        attr_string = attr_val.variable.str_val(attr_val)
        states.add(attr_string)
    
    return states


def get_attributes():
    attributes = set()
    for attribute in lenses_table.domain.attributes:
        attr_string = attribute.name
        attributes.add(attr_string)
    
    return attributes
  
if __name__ == "__main__":
    lenses_table = Table(r"lenses.tab")
    # all_instance_ids = []
    # all_instance_ids.extend(range(0, len(lenses_table)))
    original_entropy = calculate_entropy(lenses_table)
    print('Original entropy = ', original_entropy)

    possibleAttributes = get_attributes()
    for attributeToTest in possibleAttributes:
        subtables = split_data(lenses_table, attributeToTest)
        #states = attribute_states(attributeToTest)
        newEntropy = 0
        for name, subtable in subtables.items():
            newEntropy += calculate_entropy(subtable) * (float(len(subtable) / len(lenses_table)))
        print('Entropy after splitting on', attributeToTest, '=', newEntropy)
