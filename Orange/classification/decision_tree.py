from Orange.data import Table

from math import log2
from collections import defaultdict


def calculate_entropy(instance_ids):

    # Compute the frequency of each class.
    frequencies = defaultdict(int)
    for instanceID in instance_ids:
        c = lenses_table[instanceID].get_class()
        frequencies[str(c)] += 1
    #print(frequencies)

    # Compute the entropy
    entropy = 0
    for cls, freq in frequencies.items():
        prob = float(freq) / float(len(instance_ids))
        entropy -= prob*log2(prob)
  
    return entropy

    
def split_data(instance_ids, attribute):
    tables = defaultdict(list)
  
    for instance_id in instance_ids:
        attr_val = lenses_table[instance_id][attribute]
        tables[str(attr_val)].append(instance_id)

    return tables


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
    all_instance_ids = []
    all_instance_ids.extend(range(0, len(lenses_table)))
    original_entropy = calculate_entropy(all_instance_ids)
    print('Original entropy = ', original_entropy)

    possibleAttributes = get_attributes()
    for attributeToTest in possibleAttributes:
        tables = split_data(all_instance_ids, attributeToTest)
        states = attribute_states(attributeToTest)
        newEntropy = 0
        for state in states:
            newEntropy += calculate_entropy(tables[state]) * (float(len(tables[state]) / len(lenses_table)))
        print('Entropy after splitting on', attributeToTest, '=', newEntropy)
