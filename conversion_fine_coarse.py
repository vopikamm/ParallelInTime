def construct_fine_version_of_phi(inlines,outlines):
    firstpart_with_values = False
    otherparts_with_values = False
    processing_values = False           
    counter = 1
    part1 = ""
    part2 = "" 
    for line in inlines:
        if is_int(line):
            if not firstpart_with_values:
                line = str(23200*2-(210+80+80)) + "\n"
            else:
                line = str(int(line) * 2) + "\n"
            outlines.append(line)
        elif (len(line) == 2 and ")" in line):
            processing_values = False
            outlines.append(part1)
            outlines.append(part2)
            part1 = ""
            part2 = ""
            outlines.append(line)
        elif processing_values:
            if otherparts_with_values:
                outlines.append(line)
            elif firstpart_with_values:
                #needs 23200*2-(210+80+80) values 
                #generated from the 5800*2-(105+40+40) values from the coarse file
                #
                #so number_of_grid_points*2 - (grid_points_top + grid_points_inlet + grid_points_outlet)
                #
                #by now this is done by taking the first x values 5 times 
                #and the remaining y factors 4 times
                #
                #OF COURSE THIS DOES NOT CONSTRUCT A CORRECT FILE...!!!
                #
                if counter <= 370:
                    part1 = part1 + line
                    part1 = part1 + line
                    part2 = part2 + line
                    part1 = part1 + line
                    part2 = part2 + line
                    counter = counter + 1
                else:
                    part1 = part1 + line
                    part2 = part2 + line
                    part1 = part1 + line
                    part2 = part2 + line
        elif (len(line) == 2 and "(" in line):
            processing_values = True
            if not firstpart_with_values:
                firstpart_with_values = True
            else:
                otherparts_with_values = True
            outlines.append(line)
        else:
            outlines.append(line)
    return outlines

def construct_fine_version_of_other_files(inlines,outlines):
    firstpart_with_values = False
    otherparts_with_values = False
    processing_values = False   
    part1 = ""
    part2 = ""     
    for line in inlines:
        if is_int(line):
            if not firstpart_with_values:
                line = str(int(line) * 4) + "\n"
            else:
                line = str(int(line) * 2) + "\n"
            outlines.append(line)
        elif (len(line) == 2 and ")" in line):
            processing_values = False
            outlines.append(part1)
            outlines.append(part2)
            part1 = ""
            part2 = ""
            outlines.append(line)
        elif processing_values:
            if otherparts_with_values:
                part1 = part1 + line
                part2 = part2 + line
            elif firstpart_with_values:
                part1 = part1 + line
                part2 = part2 + line
                part1 = part1 + line
                part2 = part2 + line
        elif (len(line) == 2 and "(" in line):
            processing_values = True
            if not firstpart_with_values:
                firstpart_with_values = True
            else:
                otherparts_with_values = True
            outlines.append(line)
        else:
            outlines.append(line)
    return outlines

def is_int(v):
    try:
        int(v)
    except ValueError:
        return False
    return True

#TODO: automize creation of new blockMesh file
#def create_new_blockMesh():
