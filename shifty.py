# Mission Planner Flight Plan Shifter
# Version 0.1.3
# Last updated: 2025-05-06
# Dominic L. Filiano, with help from chatGPT
#
# Purpose: Shift a HA Mission Planner Flight Plan by a set distance along a set heading#
#
#
# Section 1: define the variables to be input by the user
#   inputWaypoints = the waypoints file to be shifted
#   shiftedPlan = the waypoints file to be created - "open" creates the file if it doesn't already exist
#   antAngle = the angle of the radar antenna
#   txAGL = The height above ground of the transmit aircraft
#   vertOffset = the vertical offset between the TX aircraft and the RX aircraft
#   horizOffset = the distance to shift the flight plan along the heading
#   heading = the heading toward which to shift the fligt plan
  
import os, pyproj, math, csv
inputWaypoints = open(input("Enter the file name of the waypoints mission to be shifted: "), 'r')
shiftedPlan = open(input("Enter output waypoints file name: "), 'w') 
antAngle = abs(float(input("Enter the antenna angle: ")))
txAGL = float(input("Enter the AGL of the Transmit Aircraft: "))
vertOffset = float(input("Enter the Vertical Offset Distance: "))
heading = float(input("Enter Heading (North = 0, East = 90): "))

# Section 2: Perform the calculation
#   To perform this calculation we convert the lat long to UTM coordinates, then add the easting and northing components
#   of the shift before converting back to lat long. p is the "function" that does the coordinate conversion. It uses PyProj.
#   you must have PyProj installed in your conda environment for this to run.

if vertOffset == 0:
        shiftType = input("Shift along track? (yes/no): ")
        if shiftType == "yes":
                horizOffset = float(input("Enter the horizontal offset distance: "))
                azmuth = math.radians(heading-1.7805) # azmuth = heading - a correction factor
                dN = float(horizOffset)*math.cos(azmuth)
                dE = float(horizOffset)*math.sin(azmuth)
                print(dN, dE, math.sqrt((dN*dN)+(dE*dE)))
                reader = csv.reader(inputWaypoints, delimiter='\t')
                writer = csv.writer(shiftedPlan, delimiter='\t')
                first_row = next(reader)
                writer.writerow(first_row) # skip the first row
                home_point = next(reader)
                writer.writerow(home_point) # skip the home point

                for row in reader:
                        utmZone = math.floor(((float(row[9]) + 180) % 360) / 6) + 1
                        p = pyproj.Proj(proj='utm', zone=utmZone, ellps='WGS84')
                        E,N = p(row[9],row[8]) # LL -> EN
                        newE = E+dE # shift East
                        newN = N+dN # shift North
                        lon,lat = (p(newE,newN,inverse=True)) # EN -> LL
                        row[8]=lat
                        row[9]=lon
                        writer.writerow(row)
                print("Done!")
        else:
                bounceMode = input("Bounce Configuration? (yes/no): ")
                if bounceMode == "yes":
                        horizOffset = 2*txAGL*math.tan(math.radians(90-antAngle))
                        azmuth = math.radians(heading + 90) # clockwise perpendicular angle to the heading
                        dN = float(horizOffset)*math.cos(azmuth)
                        dE = float(horizOffset)*math.sin(azmuth) 

                        reader = csv.reader(inputWaypoints, delimiter='\t')
                        writer = csv.writer(shiftedPlan, delimiter='\t')
                        first_row = next(reader)
                        writer.writerow(first_row) # skip the first row
                        home_point = next(reader)
                        writer.writerow(home_point) # skip the home point

                        for row in reader:
                                utmZone = math.floor(((float(row[9]) + 180) % 360) / 6) + 1
                                p = pyproj.Proj(proj='utm', zone=utmZone, ellps='WGS84')
                                E,N = p(row[9],row[8]) # LL -> EN
                                newE = E+dE # shift East
                                newN = N+dN # shift North
                                lon,lat = (p(newE,newN,inverse=True)) # EN -> LL
                                row[8]=lat
                                row[9]=lon
                                writer.writerow(row)
                        print("Done!")
                else:
                        horizOffset = input("Enter the horizontal offset: ")
                        azmuth = math.radians(heading + 90) # clockwise perpendicular angle to the heading
                        dN = float(horizOffset)*math.cos(azmuth)
                        dE = float(horizOffset)*math.sin(azmuth) 

                        reader = csv.reader(inputWaypoints, delimiter='\t')
                        writer = csv.writer(shiftedPlan, delimiter='\t')
                        first_row = next(reader)
                        writer.writerow(first_row) # skip the first row
                        home_point = next(reader)
                        writer.writerow(home_point) # skip the home point

                        for row in reader:
                                utmZone = math.floor(((float(row[9]) + 180) % 360) / 6) + 1
                                p = pyproj.Proj(proj='utm', zone=utmZone, ellps='WGS84')
                                E,N = p(row[9],row[8]) # LL -> EN
                                newE = E+dE # shift East
                                newN = N+dN # shift North
                                lon,lat = (p(newE,newN,inverse=True)) # EN -> LL
                                row[8]=lat
                                row[9]=lon
                                writer.writerow(row)
                        print("Done!")

else:
        horizOffset = vertOffset*math.tan(math.radians(90-antAngle))
        azmuth = math.radians(heading + 90) # clockwise perpendicular angle to the heading
        dN = float(horizOffset)*math.cos(azmuth)
        dE = float(horizOffset)*math.sin(azmuth)

        reader = csv.reader(inputWaypoints, delimiter='\t')
        writer = csv.writer(shiftedPlan, delimiter='\t')
        first_row = next(reader)
        writer.writerow(first_row) # skip the first row
        home_point = next(reader)
        writer.writerow(home_point) # skip the home point

        for row in reader:
                utmZone = math.floor(((float(row[9]) + 180) % 360) / 6) + 1
                p = pyproj.Proj(proj='utm', zone=utmZone, ellps='WGS84')
                E,N = p(row[9],row[8]) # LL -> EN
                z = float(row[10])
                newE = E+dE # shift East
                newN = N+dN # shift North
                lon,lat = (p(newE,newN,inverse=True)) # EN -> LL
                row[8]=lat
                row[9]=lon
                row[10]=z-vertOffset
                writer.writerow(row)
        print("Done!")

