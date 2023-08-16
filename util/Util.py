
def getRGBfromI(RGBint):
    blue = RGBint & 255
    green = (RGBint >> 8) & 255
    red = (RGBint >> 16) & 255
    return red, green, blue


def generate_96_mutation_types():
    mutation_types = {}
    substitution_classes = ["C>A", "C>G", "C>T", "T>A", "T>C", "T>G"]
    possible_nucleotides = ["A", "C", "G", "T"]
    for n1 in substitution_classes:
        if n1 not in mutation_types:
            mutation_types[n1] = {}
        for start in possible_nucleotides:
            for end in possible_nucleotides:
                mutation_type = start + n1 + end
                mutation_types[n1][mutation_type] = 0
    return mutation_types
