import numpy

#NOT WORKING
#this method should construct the finer phi files from the coarse ones
#...but I don't understand by now how this conversion should work
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

#constructs the fine versions of all files except for phi from the output of the coarse solver
#params
#inlines = lines from the coarse input file
#outlines = lines for the new fine file
def construct_fine_version_of_other_files(inlines,outlines):
    #the files share the common structure, that 
    #- the first block of values needs to be scaled by factor 4 (values in blocks)
    #- and the other parts need to be scaled by a factor of 2 (inlet/outlet)
    #Those blocks of values are surrounded by ( and ).
    #On top of a block of values the number of values in this block is denoted.
    #
    #example:
    #...
    #5800
    #(
    #value1
    #...
    #value5800
    #)
    #...
    firstpart_with_values = False
    otherparts_with_values = False
    processing_values = False   
    #for the scaling by factor 4 every entry 
    #- has to be doubled in its 'line' (*width_of_the_block* successive boxes from one block) 
    #- and then every 'line' needs to be doubled
    #the part variable is needed for the doubling of the 'line'
    part = "" 
    #counter is needed to keep track of the current box (only in the first part with values) 
    counter = 1
    #process line after line from the input file
    for line in inlines:
        #take care of lines that only contain one integer number - this is the number of following values
        #multiply depending on the following part of values (first part: 4; other parts: 2)
        if is_int(line):
            if not firstpart_with_values:
                line = str(int(line) * 4) + "\n"
            else:
                line = str(int(line) * 2) + "\n"
            outlines.append(line)
        #take care of the ending of a block of values
        elif (len(line) == 2 and ")" in line):
            processing_values = False
            outlines.append(line)
        #take care of block of values
        elif processing_values:
            #in the other parts every value needs added twice to the output
            if otherparts_with_values:
                outlines.append(line + line)
            #construct output from input depending on the current box
            #every entry 
            #- has to be doubled in its 'line' (*width_of_the_block* successive boxes from one block) 
            #- and then every 'line' needs to be doubled
            elif firstpart_with_values:
                if counter <= 100:
                    #box 1: 10 x 10 (coarse)
                    part,outlines = convert_coarse_to_fine(0,10,outlines,line,part,counter)
                elif counter <= 300:
                    #box 2: 20 x 10 (coarse)
                    part,outlines = convert_coarse_to_fine(100,20,outlines,line,part,counter)
                elif counter <= 1050:
                    #box 3: 75 x 10 (coarse)
                    part,outlines = convert_coarse_to_fine(300,75,outlines,line,part,counter)
                elif counter <= 1250:
                    #box 4: 10 x 20 (coarse)
                    part,outlines = convert_coarse_to_fine(1050,10,outlines,line,part,counter)
                elif counter <= 2750:
                    #box 5: 75 x 20 (coarse)
                    part,outlines = convert_coarse_to_fine(1250,75,outlines,line,part,counter)
                elif counter <= 2850:
                    #box 6: 10 x 10 (coarse)
                    part,outlines = convert_coarse_to_fine(2750,10,outlines,line,part,counter)
                elif counter <= 3050:
                    #box 7: 20 x 10 (coarse)
                    part,outlines = convert_coarse_to_fine(2850,20,outlines,line,part,counter)
                elif counter <= 3800:
                    #box 8: 75 x 10 (coarse)
                    part,outlines = convert_coarse_to_fine(3050,75,outlines,line,part,counter)
                elif counter <= 4300:
                    #box 9: 20 x 25 (coarse)
                    part,outlines = convert_coarse_to_fine(3800,20,outlines,line,part,counter)
                elif counter <= 4800:
                    #box 10: 25 x 20 (coarse)
                    part,outlines = convert_coarse_to_fine(4300,25,outlines,line,part,counter)
                elif counter <= 5300:
                    #box 11: 20 x 25 (coarse)
                    part,outlines = convert_coarse_to_fine(4800,20,outlines,line,part,counter)
                elif counter <= 5800:
                    #box 12: 25 x 20 (coarse)
                    part,outlines = convert_coarse_to_fine(5300,25,outlines,line,part,counter)
                counter = counter + 1
        #take care of the beginning of a block of values
        elif (len(line) == 2 and "(" in line):
            processing_values = True
            if not firstpart_with_values:
                firstpart_with_values = True
            else:
                otherparts_with_values = True
            outlines.append(line)
        #for other lines (e.g. text) simply copy to output
        else:
            outlines.append(line)
    return outlines

#OBVIOUSLY NOT WORKING
#this method should construct the coarser phi files from the fine ones
#...but I don't understand by now how this conversion should work
def construct_coarse_version_of_phi(inlines,outlines):
    pass

#constructs the coarse versions of all files except for phi from the output of the fine solvers
#params
#inlines = lines from the fine input file
#outlines = lines for the new coarse file
def construct_coarse_version_of_other_files(inlines,outlines):
    #the files share the common structure, that 
    #- the first block of values needs to be scaled by factor 4 (values in blocks)
    #- and the other parts need to be scaled by a factor of 2 (inlet/outlet)
    #Those blocks of values are surrounded by ( and ).
    #On top of a block of values the number of values in this block is denoted.
    #
    #example:
    #...
    #5800
    #(
    #value1
    #...
    #value5800
    #)
    #...
    firstpart_with_values = False
    otherparts_with_values = False
    processing_values = False   
    #for the scaling by factor 4 every entry 
    #- two successive 'lines' need to be merged and
    #- in every line groups of two neighbor values need to be merged
    #the part variable is needed for memorizing the first 'line' that needs to be merged with a second 'line'
    part = []
    #counter is needed to keep track of the current box (only in the first part with values) 
    counter = 1
    #process line after line from the input file
    for line in inlines:
        #take care of lines that only contain one integer number - this is the number of following values
        #divide depending on the following part of values (first part: 4; other parts: 2)
        if is_int(line):
            if not firstpart_with_values:
                line = str(int(line) / 4) + "\n"
            else:
                line = str(int(line) / 2) + "\n"
            outlines.append(line)
        #take care of the ending of a block of values
        elif (len(line) == 2 and ")" in line):
            processing_values = False
            outlines.append(line)
        #take care of block of values
        elif processing_values:
            #in the other parts every value needs added twice to the output
            if otherparts_with_values:
                outlines.append(line + line)
            #construct output from input depending on the current box
            #every entry 
            #- has to be doubled in its 'line' (*width_of_the_block* successive boxes from one block) 
            #- and then every 'line' needs to be doubled
            elif firstpart_with_values:
                if counter <= 400:
                    #box 1: 20 x 20 (fine)
                    #offset,box_width_fine,outlines,line,part,counter,values_to_merge,first_line
                    part,outlines = convert_fine_to_coarse(0,20,outlines,line,part,counter)
                elif counter <= 1200:
                    #box 2: 40 x 20 (fine)
                    part,outlines = convert_fine_to_coarse(400,40,outlines,line,part,counter)
                elif counter <= 4200:
                    #box 3: 150 x 20 (fine)
                    part,outlines = convert_fine_to_coarse(1200,150,outlines,line,part,counter)
                elif counter <= 5000:
                    #box 4: 20 x 40 (fine)
                    part,outlines = convert_fine_to_coarse(4200,20,outlines,line,part,counter)
                elif counter <= 11000:
                    #box 5: 150 x 40 (fine)
                    part,outlines = convert_fine_to_coarse(5000,150,outlines,line,part,counter)
                elif counter <= 11400:
                    #box 6: 20 x 20 (fine)
                    part,outlines = convert_fine_to_coarse(11000,20,outlines,line,part,counter)
                elif counter <= 12200:
                    #box 7: 40 x 20 (fine)
                    part,outlines = convert_fine_to_coarse(11400,40,outlines,line,part,counter)
                elif counter <= 15200:
                    #box 8: 150 x 20 (fine)
                    part,outlines = convert_fine_to_coarse(12200,150,outlines,line,part,counter)
                elif counter <= 17200:
                    #box 9: 40 x 50 (fine)
                    part,outlines = convert_fine_to_coarse(15200,40,outlines,line,part,counter)
                elif counter <= 19200:
                    #box 10: 50 x 40 (fine)
                    part,outlines = convert_fine_to_coarse(17200,50,outlines,line,part,counter)
                elif counter <= 21200:
                    #box 11: 40 x 50 (coarse)
                    part,outlines = convert_fine_to_coarse(19200,40,outlines,line,part,counter)
                elif counter <= 23200:
                    #box 12: 50 x 40 (fine)
                    part,outlines = convert_fine_to_coarse(21200,50,outlines,line,part,counter)
                counter = counter + 1
        #take care of the beginning of a block of values
        elif (len(line) == 2 and "(" in line):
            processing_values = True
            if not firstpart_with_values:
                firstpart_with_values = True
            else:
                otherparts_with_values = True
            outlines.append(line)
        #for other lines (e.g. text) simply copy to output
        else:
            outlines.append(line)
    return outlines

#converts depending on the current box
#params:
#offset = number of values processed before current box (needs to be subtracted to calculate end of 'line')
#box_width_coarse = width of the box in the coarse grid (length of 'line')
#outlines = outlines from above
#line = current line
def convert_coarse_to_fine(offset,box_width_coarse,outlines,line,part,counter):
    #add the current value twice
    part = part + line + line
    #if the end of the 'line' is reached, then add it to the output twice
    if ((counter-offset) % box_width_coarse) == 0:
        outlines.append(part + part)
        part = ""
    return part, outlines

#converts depending on the current box
#params:
#offset = number of values processed before current box (needs to be subtracted to calculate end of 'line')
#box_width_fine = width of the box in the fine grid (length of 'line')
#outlines = outlines from above
#line = current line
def convert_fine_to_coarse(offset,box_width_fine,outlines,line,part,counter,values_to_merge,first_line):
    if ((counter-offset) % box_width_fine) == 0:
        first_line = not first_line
        if first_line:
            part = []
    if first_line:
        part.append(float(line))
    else
        values_to_merge.append(float(line))
        values_to_merge.append(part.pop())
        if counter % 2 == 0:
            values_to_merge.append(float(line))
            values_to_merge.append(part.pop())
            outlines.append(str(numpy.mean(values_to_merge)) + "\n")
            values_to_merge = []
    return part, outlines

#checks whether a given input is an integer value
#params:
#v = value that should be checked
def is_int(v):
    try:
        int(v)
    except ValueError:
        return False
    return True