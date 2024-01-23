# ==============================================================================
# This Macro inserts rectagular plate at the best layout for the selected beams. Beams selected must enclose a space in
# a rectangle or square. ALL inside the space must be selected in order to determine the layout.
# ==============================================================================
# Change log and version number
# V001 -- 12/06/2019 -- Created and tested macro -- CVG
# ==============================================================================
# startup code begin
from param import *
from math import *
from Math3D import *
from Point3D import *
import math
import sys
from dialog import Dialog
from dialog.combobox import Combobox
from dialog.dimension import DimensionEntry
from dialog.dimension import DimensionStyled
from dialog import Dialog
from dialog.checkbox import CheckButtons
from dialog.dimension import DimensionEntry
from dialog.dimension import DimensionStyled
import Tkinter
from macrolib.MemSelection import mem_select, memAreaSelect
from fractions import Fraction

float(sum(Fraction(s) for s in '1 2/3'.split()))

Units("inch")
saved_sds2_version = '2018.17'
saved_python_version = (2, 7, 2, 'final', 0)
try:
    from shape import Shape
    from point import Point, PointLocate
    from member import Member, MemberLocate
    from mtrl_list import MtrlLocate, HoleLocate
    from cons_line import ConsLine
    from cons_circle import ConsCircle
    from rnd_plate import RndPlate
    from rect_plate import RectPlate
    from bnt_plate import BntPlate
    from rolled_section import RolledSection
    from weld_add import Weld
    from flat_bar import FlatBar
    from hole_add import Hole
    from bolt_add import Bolt
    from roll_plate import RollPl
    from sqr_bar import SqrBar
    from rnd_bar import RndBar
    from shr_stud import ShrStud
    from grate import Grate
    from grate_trd import GrateTrd
    from deck import Deck
    from mtrl_fit import MtrlFit
    from version import CurrentVersion, VersionCompare

    curr_version = CurrentVersion()
except ImportError:
    curr_version = 'None'


    def VersionCompare(v1, v2):
        return -1
if VersionCompare(curr_version, '6.311') >= 0:
    from job import Job
    from fab import Fabricator
if VersionCompare(curr_version, '6.312') >= 0:
    from plate_layout import PlateLayout
if VersionCompare(curr_version, '6.314') >= 0:
    from plate_layout import BntPlateLayout
if VersionCompare(curr_version, '6.4') >= 0:
    from mtrl_cut import MtrlCut
if VersionCompare(curr_version, '7.006') >= 0:
    from member import MemberAllocated
if VersionCompare(curr_version, '7.009') >= 0:
    from job import JobName
    from fab import FabricatorName
if VersionCompare(curr_version, '7.1') >= 0:
    from job import ProcessJob
    from job import ProcessOneMem
    from view import View
    from clevis import Clevis
    from turnbuckle import Turnbuckle
    from member import MultiMemberLocate
    from mtrl_list import MtrlByGuid
if VersionCompare(curr_version, '7.101') >= 0:
    from member import MemberProperties
    from member import MemberPropertySet
if VersionCompare(curr_version, '7.109') >= 0:
    from assembly import Assembly
    from assembly import AssemblyList
if VersionCompare(curr_version, '7.110') >= 0:
    from member import GroupMemberCreate
if VersionCompare(curr_version, '7.113') >= 0:
    from member import MarkMemberForProcess
if VersionCompare(curr_version, '7.132') >= 0:
    from mtrl_list import MtrlProperties
    from mtrl_list import MtrlPropertySet
    from job import JobProperties
    from job import JobPropertySet
# Classes--------------------------------------------------


class Beam:
    def __init__(self, left, right, flgw, ori=None):
        self.leftend = left
        self.rightend = right
        self.flangewidth = flgw
        self.orientation = ori


    def set_orientation(self):
        if self.leftend.x - self.rightend.x == 0:
            self.orientation = 'vertical'
        elif self.leftend.y - self.rightend.y == 0:
            beam.orientation = 'horizontal'


# Functions------------------------------------------------
# This function takes the list of all beams and separates them into xs and ys. It then removes any duplicates
# Then returns a list of xs and ys for each line of beams
def get_beam_lines(beams):
    xs = []
    ys = []
    temp_xs = [beam.leftend.x for beam in beams if beam.orientation == 'vertical']
    temp_ys = [beam.leftend.y for beam in beams if beam.orientation == 'horizontal']
    [xs.append(x) for x in temp_xs if x not in xs]  # Removes duplicates
    [ys.append(x) for x in temp_ys if x not in ys]  # Removes duplicates
    return xs, ys


# This function takes in a list of points (lines), a starting point, and max dist (CPmax). Then, it generates a list
# of differences between each point in 'lines' and the start + CPmax.
# In short, this function generates a list of the differences bewteen each beam in the list so that the closest beam
# can be found. See get_spaced_beams()
def get_diff_list(lines, start, CPmax):
    diff_list = []
    for val in lines:  # for loop iterates every beam location and gets the difference from start + CPmax
        diff = abs(start + CPmax - val)
        diff_list.append(diff)
    return diff_list


# This function takes a list and and index of that list and returns the next smallest value from the list.
def next_smallest_index(lis, indexOfValue):
    val = lis[0]
    index = 0
    x = [ndx for (ndx, item) in enumerate(lis) if item > lis[indexOfValue]]
    if len(x) > 1:
        for item in x:
            if min(lis) == val:
                val = lis[item]
                continue
            elif val <= lis[item]:
                continue
            else:
                val = lis[item]
                index = item
    else:
        index = 'None'
    return index

# listest = [18.0, 66.0, 60.0]
# ndxtest = 0
# indextest = next_smallest_index(lis, ndx)
# print indextest

# This function takes in a list of points (lines), a starting point, and max dist (CPmax). Then, it loops through each
# diff_list generated by get_diff_list() to find the minimum distance and the corresponding beam location.
# The function then checks to see if the beam found is within the limits of max plate sizes; if not it will find the
# next closest beam. When a beam is found it appends to a list. The While loop breaks when the iteration has reached the
# last beam.
# Returns a list of the closest beams to the CP max relative to the top corner of the selected area.
def get_spaced_beams(lines, CPmax, start):
    lis = [start]
    while True:
        diff_list = get_diff_list(lines, start, CPmax)  # Gets the diff_list for lines
        index_min = min(xrange(len(diff_list)), key=diff_list.__getitem__)  # finds the index of the min in diff_list
        # Checks if the difference is less than max CP size
        if abs(start) - abs(lines[index_min]) <= abs(CPmax):
            # if statement checks if the algorithm has reached the last beam and tells the loop to stop
            if lines[index_min] == start:
                break
            else:  # if it has not reached the last beam, it will append the next beam and set a new start location
                lis.append(lines[index_min])  # Appends the beam with the corresponding 'index_min'
                start = lines[index_min]  # sets new start point as the closest beam found
        else:  # If difference is greater than max cp size, while loop finds next closest beam until satisfied
            while abs(start) - abs(lines[index_min]) >= abs(CPmax):
                index_min = next_smallest_index(diff_list, index_min)
                if index_min == 'None' or lines[index_min] == start:
                    break
            if index_min == 'None' or lines[index_min] == start:
                break
            else:
                lis.append(lines[index_min])
                start = lines[index_min]
    return lis


# This function takes in the list of beams, xlines, and y lines and compares the left and right end of each member
# to the min/max of the x and y. This will find the outer beams and set variables to return as flange width /2
# NOTE: If beams on these lines have different flange widths, this function will return the flange width that is
# last in the list. Need to update this function to return the max flange width on a given line.
def get_flange_width(memberlist, xlines, ylines):
    for memb in memberlist:
        if memb.leftend.x == min(xlines) and memb.rightend.x == min(xlines):
            flgw_left = memb.flangewidth/2
        elif memb.leftend.x == max(xlines) and memb.rightend.x == max(xlines):
            flgw_right = memb.flangewidth/2
        elif memb.leftend.y == max(ylines) and memb.rightend.y == max(ylines):
            flgw_top = memb.flangewidth/2
        elif memb.leftend.y == min(ylines) and memb.rightend.y == min(ylines):
            flgw_bottom = memb.flangewidth/2
    return flgw_left, flgw_right, flgw_top, flgw_bottom

# This function takes in x and y vales and generates a list of each corner of the beam and combines them to make a list
# of points for each plate. These points are to the center of the beams and need to be corrected for spacing and clrnc
# This function works by generating 4 lists, each correspond to each corner of the plate. each list is generated by
# iterating over x and y values in a specific way. i.e. all but last element, all but first element, ect
def gen_plate_ends(xvalues, yvalues):
    lefttop = [(x, y) for y in yvalues[:-1] for x in xvalues[:-1]]  # all but last in x and y
    righttop = [(x, y) for y in yvalues[1:] for x in xvalues[1:]]  # all but first in x and y
    botleft = [(x, y) for y in yvalues[1:] for x in xvalues[:-1]]  # all but first in x, all but last in y
    botright = [(x, y) for y in yvalues[:-1] for x in xvalues[1:]]  # all but last in x, all but first in y
    # Creates a list of lists for each point of the grid by iterating over zip, list contains lists of 4 points
    lis = [list(a) for a in zip(lefttop, righttop, botleft, botright)]
    return lis


# returns material locations before they are corrected with the clearances. Need these points to determine beam side.
# This function is needed because the points from find_square_points() do not corespond to the correct sides fo the
# member. This function finds the material points by finding the min and max of the points. Where min x is the left end,
# max x is the right end, max y is the top, and min y is the bottom.
def get_material_locations(pnts):
    # finds the left and right x from a list of points
    x = [pnt[0] for pnt in pnts]
    index_minx = min(xrange(len(x)), key=x.__getitem__)
    index_maxx = max(xrange(len(x)), key=x.__getitem__)
    left_x = x[index_minx] + dig1.plate_clearance/2
    right_x = x[index_maxx] - dig1.plate_clearance/2
    # finds the top and bottom y from a list of points
    y = [pnt[1] for pnt in pnts]
    index_maxy = max(xrange(len(y)), key=y.__getitem__)
    index_miny = min(xrange(len(y)), key=y.__getitem__)
    top_y = y[index_maxy] - dig1.plate_clearance/2
    bot_y = y[index_miny] + dig1.plate_clearance/2
    # generates the material points with respect to left and right ends
    mtrl_left = left_x, top_y, beams[0].leftend.z
    mtrl_right = right_x, top_y, beams[0].leftend.z
    mtrl_width = abs(left_x - right_x)
    mtrl_length = abs(top_y - bot_y)
    return mtrl_left, mtrl_right, mtrl_length, mtrl_width

# This Function takes in lists of x and y lines generated by get_beam_lines(). The max and min x and y are corrected
# for the flange width of the outside beams and the clearance entered by the user. This function calls get_flange_width
# in order to get the correct flange widths for the correct beams
def adjust_beam_lines(xlines, ylines):
    flgw_left, flgw_right, flgw_top, flgw_bottom = get_flange_width(beams, x_lines_temp, y_lines_temp)
    #  if statments that get user input and set the flange width to zero of the user enters 'Beam Center Line'
    if dig1.top_side[0] == 'Beam Center Line':
        flgw_top = 0
    if dig1.bottom_side[0] == 'Beam Center Line':
        flgw_bottom = 0
    if dig1.left_side[0] == 'Beam Center Line':
        flgw_left = 0
    if dig1.right_side[0] == 'Beam Center Line':
        flgw_right = 0
    #  List comprehesions: first xs generates a list that replaces the max x with x + user clearance +/- plate clearance
    #  +/- flange width/2. The second xs does the same as the first except with the min x.
    #  The plate clearance/2 is just a correction for the max and min because is it applyed to all
    #  points before this function. The plate clearance does not apply to the outer plates so it needs to be corrected.
    xs = [(x + dig1.right_clr + dig1.plate_clearance/2 + flgw_right) if x == max(xlines) else x for x in xlines]
    xs = [(x + dig1.left_clr - dig1.plate_clearance/2 - flgw_left) if x == min(xs) else x for x in xs]
    ys = [(y + dig1.top_clr + dig1.plate_clearance/2 + flgw_top) if y == max(ylines) else y for y in ylines]
    ys = [(y + dig1.bot_clr - dig1.plate_clearance/2 - flgw_bottom) if y == min(ylines) else y for y in ys]
    return xs, ys

# Main Section---------------------------------------------------------------------------------------------------------
while True:
    members = MultiMemberLocate("Select Beams and Columns")
    beams = [mem for mem in members if mem.Type == 'Beam']
    columns = [mem for mem in members if mem.Type == 'Column']
    # Opens Dialog box for user input
    dig1 = Dialog( 'Checker Plate Plan Macro' )
    Entry1 = DimensionEntry( dig1, 'plate_thickness', label="Plate Thickness:",style="inch-fraction2", default=.25 )
    Entry2 = DimensionEntry( dig1, 'plate_clearance', label="Plate Clearance:",style="inch-fraction2", default=.25 )
    Entry3 = DimensionEntry( dig1, 'CPmax_width', label="Max Plate Width:",style='feet', default=72 )
    Entry4 = DimensionEntry( dig1, 'CPmax_length', label="Max Plate Length:",style='feet', default=120 )
    Check_boxes3 = CheckButtons( dig1, 'top_side', ("Beam Flange", "Beam Center Line"),label="Top Reference Point", default=['Beam Flange'])
    Entry5 = DimensionEntry(Check_boxes3, 'top_clr', label="Offset:", style="inch-fraction2",  default=-.25)
    Check_boxes4 = CheckButtons( dig1, 'left_side', ("Beam Flange", "Beam Center Line"),label="Left Reference Point", default=["Beam Flange"])
    Entry6 = DimensionEntry(Check_boxes4, 'left_clr', label="Offset:", style="inch-fraction2", default=.25)
    Check_boxes5 = CheckButtons( dig1, 'right_side', ("Beam Flange", "Beam Center Line"),label="Right Reference Point", default=["Beam Flange"])
    Entry7 = DimensionEntry(Check_boxes5, 'right_clr', label="Offset:", style="inch-fraction2", default=-.25)
    Check_boxes6 = CheckButtons( dig1, 'bottom_side', ("Beam Flange", "Beam Center Line"),label="Bottom Reference Point", default=["Beam Flange"])
    Entry8 = DimensionEntry(Check_boxes6, 'bot_clr', label="Offset:", style="inch-fraction2", default=.25)
    dd = dig1.done()
    # Dialog end
    # Using a for loop to create beam instances and set attributes
    for n, mem in enumerate(beams):
        leftend = mem.left.location
        rightend = mem.right.location
        flgwidth = mem.FlangeWidth
        beams[n] = Beam(leftend, rightend, flgwidth)
    # Runs method to set orientaion of beam to be used to find x and y lines
    for beam in beams:
        beam.set_orientation()

    # Defining lists of beam lines and adjusting them for user inputed clearance
    x_lines_temp, y_lines_temp = get_beam_lines(beams)
    x_lines, y_lines = adjust_beam_lines(x_lines_temp, y_lines_temp)
    # This section runs get_spaced_beams with cp length and width in both directions and returns 4 lists
    CPmax_width = dig1.CPmax_width - 3
    CPmax_len = dig1.CPmax_length - 3



    #  This if statements are just to save the macro from running function that dont need to run. In this case, if
    #  len(closest_x_vert/horz) are less than 1 then they will not be used anyway so there is no need to run the y lines
    closest_x_vert = get_spaced_beams(x_lines, CPmax_width, min(x_lines))
    if len(closest_x_vert) > 1:
        closest_y_vert = get_spaced_beams(y_lines, -CPmax_len, max(y_lines))
        eff_vert = len(closest_x_vert) * len(closest_y_vert)
    else:
        eff_vert = 'None'

    closest_x_horz = get_spaced_beams(x_lines, CPmax_len, min(x_lines))
    if len(closest_x_horz) > 1:
        closest_y_horz = get_spaced_beams(y_lines, -CPmax_width, max(y_lines))
        eff_horz = len(closest_x_horz) * len(closest_y_horz)
    else:
        eff_vert = 'None'
    # This section determines which orientation the checkered plate will span by minimizing the number of plates
    # returns a list of points that make up the grid of plates
    if eff_vert != 'None' and eff_horz != 'None':
        if eff_vert <= eff_horz:
            grid = gen_plate_ends(closest_x_vert, closest_y_vert)
        else:
            grid = gen_plate_ends(closest_x_horz, closest_y_horz)
    elif eff_vert != 'None':
        grid = gen_plate_ends(closest_x_vert, closest_y_vert)
    elif eff_horz != 'None':
        grid = gen_plate_ends(closest_x_horz, closest_y_horz)
    else:
        Warning('Error: No valid layout.')

    #  This for loops is the main loop that puts in the material. For each points in 'grid' it runs a function to get
    #  Material location for each piece.
    for pnt in grid:
        leftend, rightend, length, width = get_material_locations(pnt)
        # member begin
        memadd2 = Member('Misc Rectangular Plate')
        memadd2.LeftEnd.Location = leftend
        memadd2.RightEnd.Location = rightend
        memadd2.Thickness = dig1.plate_thickness
        memadd2.width = length
        memadd2.OrderLength = length
        memadd2.WorkpointSlopeDistance = memadd2.LeftEnd.Location.Distance(memadd2.RightEnd.Location)
        memadd2.MaterialGrade = 'A36'
        memadd2.TopOperationTypeLeftEnd = 'None'
        memadd2.TopOperationTypeRightEnd = 'None'
        memadd2.BottomOperationTypeLeftEnd = 'None'
        memadd2.BottomOperationTypeRightEnd = 'None'
        memadd2.MaterialType = 'Plate'
        memadd2.SurfaceFinish = 'None'
        memadd2.MaterialColor3d = '6.3_red_oxide'
        memadd2.Add()
        memadd2.Rotate((0.000000, 0.000000, 0.000000))
        # member end
        ClearSelection()
    break

