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
import iterate as iterate

#merging all files except for phi
def compute_new_value_from_3_files_not_phi(inlines1, inlines2, inlines3, outlines, adjustment):
    #the files share the common structure, that
    #blocks of values are surrounded by ( and ).
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
    #check that input files have same length
    if len(inlines1) != len(inlines2) or len(inlines2) != len(inlines3):
        print("len1 " + str(len(inlines1)))
        print("len2 " + str(len(inlines2)))
        print("len3 " + str(len(inlines3)))
        exit("ERROR: not able to merge files")
    processing_values = False   

    #U_j+1^k+1 = G(t_j , t_j+1 , U_j^k+1) + F(t_j , t_j+1 , U_j^k) - G(t_j , t_j+1 , U_j^k)
    result = 0.0
    #process line after line from the input file
    for position in range(0,len(inlines1)):
        line1 = inlines1[position]
        line2 = inlines2[position]
        line3 = inlines3[position]
        #take care of lines that only contain one integer number - this is the number of following values
        if (len(line1) == 2 and ")" in line1):
            processing_values = False
            outlines.append(line1)
        #take care of block of values
        elif processing_values:
            result,adjustment = process_values(line1,line2,line3,adjustment)
            outlines.append(result + "\n")
        #take care of the beginning of a block of values
        elif (len(line1) == 2 and "(" in line1):
            processing_values = True
            outlines.append(line1)
        #for other lines (e.g. text) simply copy to output
        else:
            outlines.append(line1)
    return outlines,adjustment

def process_values(line1,line2,line3,adjustment):
    result = ""
    if "(" in line1:
        new_value,value_fine_last_iteration = process_block_of_values(line1,line2,line3,0,1,None)
        adjustment = adjustment + ((new_value - value_fine_last_iteration)**2)
        result = "(" + str(new_value)

        new_value,value_fine_last_iteration = process_block_of_values(line1,line2,line3,1,None,None)
        adjustment = adjustment + ((new_value - value_fine_last_iteration)**2)
        result = result + " " + str(new_value)

        new_value,value_fine_last_iteration = process_block_of_values(line1,line2,line3,2,None,-2)
        adjustment = adjustment + ((new_value - value_fine_last_iteration)**2)
        result = result + " " + str(new_value) + ")\n"
    else:
        new_value,value_fine_last_iteration = process_block_of_values(line1,line2,line3,0,None,None)
        adjustment = adjustment + ((new_value - value_fine_last_iteration)**2)
        result = str(new_value) + "\n"
    return result,adjustment

def process_block_of_values(line1,line2,line3,part,offset_start,offset_end):
    #G(t_j , t_j+1 , U_j^k+1)
    value_coarse_this_iteration = float(((line1.split(" "))[part])[offset_start:offset_end])
    #F(t_j , t_j+1 , U_j^k)
    value_fine_last_iteration = float(((line2.split(" "))[part])[offset_start:offset_end])
    #G(t_j , t_j+1 , U_j^k)
    value_coarse_last_iteration = float(((line3.split(" "))[part])[offset_start:offset_end])
    
    #U_j+1^k+1 = G(t_j , t_j+1 , U_j^k+1) + F(t_j , t_j+1 , U_j^k) - G(t_j , t_j+1 , U_j^k)
    new_value = value_coarse_this_iteration + value_fine_last_iteration - value_coarse_last_iteration

    return new_value,value_fine_last_iteration