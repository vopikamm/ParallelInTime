import numpy

def merge_files_phi(inlines1_fine, inlines2, inlines3, end_time, adjustment):
    #
    #
    #CURRENTLY JUST A WORKAROUND
    #
    #
    file_for_workaround = open("workaround/phi" + str(end_time),'r')
    adjustment = adjustment + 0.0
    outlines = file_for_workaround.readlines()
    return outlines, adjustment

def merge_other_files(file, inlines1_fine, inlines2, inlines3, outlines, adjustment):
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
    if len(inlines1_fine) != len(inlines2) or len(inlines2) != len(inlines3):
        print("len1 " + str(len(inlines1_fine)))
        print("len2 " + str(len(inlines2)))
        print("len3 " + str(len(inlines3)))
        exit("ERROR: not able to merge files")
    processing_values = False   

    #U_j+1^k+1 = G(t_j , t_j+1 , U_j^k+1) + F(t_j , t_j+1 , U_j^k) - G(t_j , t_j+1 , U_j^k)
    result = 0.0
    #process line after line from the input file
    for position in range(0,len(inlines1_fine)):
        line1 = inlines1_fine[position]
        line2 = inlines2[position]
        line3 = inlines3[position]
        #take care of lines that only contain one integer number - this is the number of following values
        if (len(line1) == 2 and ")" in line1):
            processing_values = False
            outlines.append(line1)
        #take care of block of values
        elif processing_values:
            result,adjustment = process_values(file,line1,line2,line3,adjustment)
            outlines.append(result + "\n")
        #take care of the beginning of a block of values
        elif (len(line1) == 2 and "(" in line1):
            processing_values = True
            outlines.append(line1)
        #for other lines (e.g. text) simply copy to output
        else:
            outlines.append(line1)
    return outlines,adjustment

def process_values(file,line1,line2,line3,adjustment):
    #G(t_j , t_j+1 , U_j^k+1)
    value_coarse_this_iteration = 0.0
    #F(t_j , t_j+1 , U_j^k)
    value_fine_last_iteration = 0.0
    #G(t_j , t_j+1 , U_j^k)
    value_coarse_last_iteration = 0.0
    #U_j+1^k+1 = G(t_j , t_j+1 , U_j^k+1) + F(t_j , t_j+1 , U_j^k) - G(t_j , t_j+1 , U_j^k)
    result = 0.0
    if "(" in line1:
        #G(t_j , t_j+1 , U_j^k+1)
        value_coarse_this_iteration = float(((line1.split(" "))[0])[1:])
        #F(t_j , t_j+1 , U_j^k)
        value_fine_last_iteration = float(((line2.split(" "))[0])[1:])
        #G(t_j , t_j+1 , U_j^k)
        value_coarse_last_iteration = float(((line3.split(" "))[0])[1:])
        #U_j+1^k+1 = G(t_j , t_j+1 , U_j^k+1) + F(t_j , t_j+1 , U_j^k) - G(t_j , t_j+1 , U_j^k)
        new_value = value_coarse_this_iteration + value_fine_last_iteration - value_coarse_last_iteration
        adjustment = adjustment + ((new_value - value_fine_last_iteration)**2)
        result = "(" + str(new_value)

        #G(t_j , t_j+1 , U_j^k+1)
        value_coarse_this_iteration = float((line1.split(" "))[1])
        #F(t_j , t_j+1 , U_j^k)
        value_fine_last_iteration = float((line2.split(" "))[1])
        #G(t_j , t_j+1 , U_j^k)
        value_coarse_last_iteration = float((line3.split(" "))[1])
        #U_j+1^k+1 = G(t_j , t_j+1 , U_j^k+1) + F(t_j , t_j+1 , U_j^k) - G(t_j , t_j+1 , U_j^k)
        new_value = value_coarse_this_iteration + value_fine_last_iteration - value_coarse_last_iteration
        adjustment = adjustment + ((new_value - value_fine_last_iteration)**2)
        result = result + " " + str(new_value)

        #G(t_j , t_j+1 , U_j^k+1)
        value_coarse_this_iteration = float(((line1.split(" "))[2])[:-2])
        #F(t_j , t_j+1 , U_j^k)
        value_fine_last_iteration = float(((line2.split(" "))[2])[:-2])
        #G(t_j , t_j+1 , U_j^k)
        value_coarse_last_iteration = float(((line2.split(" "))[2])[:-2])
        #U_j+1^k+1 = G(t_j , t_j+1 , U_j^k+1) + F(t_j , t_j+1 , U_j^k) - G(t_j , t_j+1 , U_j^k)
        new_value = value_coarse_this_iteration + value_fine_last_iteration - value_coarse_last_iteration
        adjustment = adjustment + ((new_value - value_fine_last_iteration)**2)
        result = result + " " + str(new_value) + ")\n"
    else:
        #G(t_j , t_j+1 , U_j^k+1)
        value_coarse_this_iteration = float(line1)
        #F(t_j , t_j+1 , U_j^k)
        value_fine_last_iteration = float(line2)
        #G(t_j , t_j+1 , U_j^k)
        value_coarse_last_iteration = float(line3)
        #U_j+1^k+1 = G(t_j , t_j+1 , U_j^k+1) + F(t_j , t_j+1 , U_j^k) - G(t_j , t_j+1 , U_j^k)
        new_value = value_coarse_this_iteration + value_fine_last_iteration - value_coarse_last_iteration
        adjustment = adjustment + ((new_value - value_fine_last_iteration)**2)
        result = str(new_value) + "\n"
    return result,adjustment
