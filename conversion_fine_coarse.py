import subprocess
import os
from os import listdir
from os.path import isfile, join

import shutil
import time
import select
import sys
import numpy

import parareal_openFoam as main_program
import initialize as init
import options as opt
import merge_results as merge
import iterate as iterate

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
    #true in first line and false in second line of two lines that should be merged
    first_line = True
    # collects four values that need to be merged into one
    values_to_merge = []
    #process line after line from the input file
    for line in inlines:
        #take care of lines that only contain one integer number - this is the number of following values
        #divide depending on the following part of values (first part: 4; other parts: 2)
        if is_int(line):
            if not firstpart_with_values:
                line = str(int(int(line) / 4)) + "\n"
            else:
                line = str(int(int(line) / 2)) + "\n"
            outlines.append(line)
        #take care of the ending of a block of values
        elif (len(line) == 2 and ")" in line):
            processing_values = False
            outlines.append(line)
        #take care of block of values
        elif processing_values:
            #in the other parts every value needs added twice to the output
            if otherparts_with_values:
                values_to_merge.append(line)
                if counter % 2 == 0:
                    outlines.append(merge_two_values(values_to_merge))
                    values_to_merge = []
                if first_line:
                    first_line = not first_line
                counter = counter + 1
            #construct output from input depending on the current box
            #every entry
            #- has to be doubled in its 'line' (*width_of_the_block* successive boxes from one block)
            #- and then every 'line' needs to be doubled
            elif firstpart_with_values:
                if counter <= 400:
                    #box 1: 20 x 20 (fine)
                    #offset,box_width_fine,outlines,line,part,counter,values_to_merge,first_line
                    part,outlines,values_to_merge,first_line = convert_fine_to_coarse(0,20,outlines,line,part,counter,values_to_merge,first_line)
                elif counter <= 1200:
                    #box 2: 40 x 20 (fine)
                    part,outlines,values_to_merge,first_line = convert_fine_to_coarse(400,40,outlines,line,part,counter,values_to_merge,first_line)
                elif counter <= 4200:
                    #box 3: 150 x 20 (fine)
                    part,outlines,values_to_merge,first_line = convert_fine_to_coarse(1200,150,outlines,line,part,counter,values_to_merge,first_line)
                elif counter <= 5000:
                    #box 4: 20 x 40 (fine)
                    part,outlines,values_to_merge,first_line = convert_fine_to_coarse(4200,20,outlines,line,part,counter,values_to_merge,first_line)
                elif counter <= 11000:
                    #box 5: 150 x 40 (fine)
                    part,outlines,values_to_merge,first_line = convert_fine_to_coarse(5000,150,outlines,line,part,counter,values_to_merge,first_line)
                elif counter <= 11400:
                    #box 6: 20 x 20 (fine)
                    part,outlines,values_to_merge,first_line = convert_fine_to_coarse(11000,20,outlines,line,part,counter,values_to_merge,first_line)
                elif counter <= 12200:
                    #box 7: 40 x 20 (fine)
                    part,outlines,values_to_merge,first_line = convert_fine_to_coarse(11400,40,outlines,line,part,counter,values_to_merge,first_line)
                elif counter <= 15200:
                    #box 8: 150 x 20 (fine)
                    part,outlines,values_to_merge,first_line = convert_fine_to_coarse(12200,150,outlines,line,part,counter,values_to_merge,first_line)
                elif counter <= 17200:
                    #box 9: 40 x 50 (fine)
                    part,outlines,values_to_merge,first_line = convert_fine_to_coarse(15200,40,outlines,line,part,counter,values_to_merge,first_line)
                elif counter <= 19200:
                    #box 10: 50 x 40 (fine)
                    part,outlines,values_to_merge,first_line = convert_fine_to_coarse(17200,50,outlines,line,part,counter,values_to_merge,first_line)
                elif counter <= 21200:
                    #box 11: 40 x 50 (coarse)
                    part,outlines,values_to_merge,first_line = convert_fine_to_coarse(19200,40,outlines,line,part,counter,values_to_merge,first_line)
                elif counter <= 23200:
                    #box 12: 50 x 40 (fine)
                    part,outlines,values_to_merge,first_line = convert_fine_to_coarse(21200,50,outlines,line,part,counter,values_to_merge,first_line)
                counter = counter + 1
        #take care of the beginning of a block of values
        elif (len(line) == 2 and "(" in line):
            processing_values = True
            first_line = True
            counter = 1
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
    if first_line:
        part.append(line)
    else:
        values_to_merge.append(line)
        values_to_merge.append(part.pop())
        if counter % 2 == 0:
            outlines.append(merge_four_values(values_to_merge))
            values_to_merge = []
    if ((counter-offset) % box_width_fine) == 0:
        first_line = not first_line
        if first_line:
            part = []
    return part, outlines, values_to_merge, first_line

def merge_four_values(values_to_merge):
    #in file U we have values that look like
    #(value1 value2 value3)
    #these need to be merged differently since every of the three values needs to be merged seperately
    value1 = 0
    value2 = 0
    value3 = 0
    value4 = 0
    merge = 0
    result = ""
    if "(" in values_to_merge[0]:
        value1  = float(((values_to_merge[0].split(" "))[0])[1:])
        value2  = float(((values_to_merge[1].split(" "))[0])[1:])
        value3  = float(((values_to_merge[2].split(" "))[0])[1:])
        value4  = float(((values_to_merge[3].split(" "))[0])[1:])
        merge = (value1 + value2 + value3 + value4)/4.0
        result = "(" + str(merge)

        value1  = float((values_to_merge[0].split(" "))[1])
        value2  = float((values_to_merge[1].split(" "))[1])
        value3  = float((values_to_merge[2].split(" "))[1])
        value4  = float((values_to_merge[3].split(" "))[1])
        merge = (value1 + value2 + value3 + value4)/4.0
        result = result + " " + str(merge)

        value1  = float(((values_to_merge[0].split(" "))[2])[:-2])
        value2  = float(((values_to_merge[1].split(" "))[2])[:-2])
        value3  = float(((values_to_merge[2].split(" "))[2])[:-2])
        value4  = float(((values_to_merge[3].split(" "))[2])[:-2])
        merge = (value1 + value2 + value3 + value4)/4.0
        return result + " " + str(merge) + ")\n"
    else:
        value1  = float(values_to_merge[0])
        value2  = float(values_to_merge[1])
        value3  = float(values_to_merge[2])
        value4  = float(values_to_merge[3])
        merge = (value1 + value2 + value3 + value4)/4.0
        return str(merge) + "\n"

def merge_two_values(values_to_merge):
    value1 = 0
    value2 = 0
    merge = 0
    result = ""
    if "(" in values_to_merge[0]:
        value1  = float(((values_to_merge[0].split(" "))[0])[1:])
        value2  = float(((values_to_merge[1].split(" "))[0])[1:])
        merge = (value1 + value2)/2.0
        result = "(" + str(merge)

        value1  = float((values_to_merge[0].split(" "))[1])
        value2  = float((values_to_merge[1].split(" "))[1])
        merge = (value1 + value2)/2.0
        result = result + " " + str(merge)

        value1  = float(((values_to_merge[0].split(" "))[2])[:-2])
        value2  = float(((values_to_merge[1].split(" "))[2])[:-2])
        merge = (value1 + value2)/2.0
        return result + " " + str(merge) + ")\n"
    else:
        value1  = float(values_to_merge[0])
        value2  = float(values_to_merge[1])
        merge = (value1 + value2)/2.0
        return str(merge) + "\n"

#checks whether a given input is an integer value
#params:
#v = value that should be checked
def is_int(v):
    try:
        int(v)
    except ValueError:
        return False
    return True
