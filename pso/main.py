import json
import math
import matplotlib.pyplot as plt
import numpy as np

import plotly.graph_objects as go

import pso

from scipy import interpolate
from shapely.geometry import LineString
from utils import plot_lines, get_closet_points

def main():
    # PARAMETERS
    N_SECTORS = 200
    N_PARTICLES = 150
    N_ITERATIONS = 300
    W = -0.2256
    CP = -0.1564
    CG = 3.8876
    PLOT = True
    
    # Read tracks from json file
    with open('data/tracks.json') as file:
        json_data = json.load(file)

    track_layout = json_data['test_track']['layout']
    track_width = json_data['test_track']['width']

    # Compute inner and outer tracks borders
    center_line = LineString(track_layout)
    inside_line = LineString(center_line.parallel_offset(track_width/2, 'left'))
    outside_line = LineString(center_line.parallel_offset(track_width/2, 'right'))

    if PLOT:
        plt.title("Track Layout Points")
        for p in track_layout:
            plt.plot(p[0], p[1], 'r.', markersize=2)
        plt.show()
        plt.title("Track layout")
        plot_lines([outside_line, inside_line])
        plt.show()
    
    # Define sectors' extreme points (in coordinates). Each sector segment is defined by an inside point and an outside point.
    inside_points, outside_points = define_sectors(center_line, inside_line, outside_line, N_SECTORS)

    if PLOT:
        plt.title("Sectors")
        for i in range(N_SECTORS):
            plt.plot([inside_points[i][0], outside_points[i][0]], [inside_points[i][1], outside_points[i][1]])
        plot_lines([outside_line, inside_line])
        plt.show()

    # Define the boundaries that will be passed to the pso algorithm [0 - trackwidth].
    # 0 correspond to the inner border, trackwidth to the outer border.
    boundaries = []
    for i in range(N_SECTORS):
        boundaries.append(np.linalg.norm(inside_points[i][:2] - outside_points[i][:2]))

    def myCostFunc(sectors):
        return get_lap_time(sectors_to_racing_line(sectors, inside_points, outside_points))

    global_solution, gs_eval, gs_history, gs_eval_history = pso.optimize(cost_func = myCostFunc,
                                                                         n_dimensions=N_SECTORS,
                                                                         boundaries=boundaries,
                                                                         n_particles=N_PARTICLES,
                                                                         n_iterations=N_ITERATIONS,
                                                                         w=W, cp=CP, cg=CG,
                                                                         verbose=True)

    _, v, x, y, z = get_lap_time(sectors_to_racing_line(global_solution, inside_points, outside_points), return_all=True)

    if PLOT:
        # plt.title("Racing Line History")
        # plt.ion()
        # for i in range(0, len(np.array(gs_history)), int(N_ITERATIONS/100)):
        #     lth, vh, xh, yh, zh = get_lap_time(sectors_to_racing_line(gs_history[i], inside_points, outside_points), return_all=True)
        #     plt.scatter(xh, yh, marker='.', c = vh, cmap='RdYlGn')
        #     plot_lines([outside_line, inside_line])
        #     plt.draw()
        #     plt.pause(0.00000001)
        #     plt.clf()
        # plt.ioff()
        
        plt.title("Final racing line")
        rl = np.array(sectors_to_racing_line(global_solution, inside_points, outside_points))
        plt.plot(rl[:,0], rl[:,1], 'ro') # Comment to remove red dot on sector lines
        plt.scatter(x, y, marker='.', c = v, cmap='RdYlGn')
        for i in range(N_SECTORS):
            plt.plot([inside_points[i][0], outside_points[i][0]], [inside_points[i][1], outside_points[i][1]])
        plot_lines([outside_line, inside_line])
        plt.show()

        plt.title("Global solution history")
        plt.ylabel("lap_time (s)")
        plt.xlabel("n_iteration")
        plt.plot(gs_eval_history)
        plt.show()
        
        plot_final_racing_line(inside_points, outside_points, x, y, v, global_solution)


def sectors_to_racing_line(sectors:list, inside_points:list, outside_points:list):
    '''Sectors to racing line coordinate
    
    This function converts the sector values (numeric value from 0 to the track's width) to cartesian coordinates using a parametric function.

    Parameters
    ----------
    sectors : list
        Position value of the sector inside the sector segment
    inside_points : list
        List coordinates corresponding to the internal point of each sector segment
    outside_points : list
        List coordinates corresponding to the external point of each sector segment

    Returns
    -------
    racing_line : list
        List of coordinates corresponding to the sectors' position
    '''
    
    racing_line = []
    for i in range(len(sectors)):
        x1, y1, z1 = inside_points[i]
        x2, y2, z2 = outside_points[i]
        m = (y2 - y1) / (x2 - x1)

        a = math.cos(math.atan(m))  # angle with x axis
        b = math.sin(math.atan(m))  # angle with x axis

        xp = x1 - sectors[i] * a
        yp = y1 - sectors[i] * b
        zp = z1 + sectors[i] * (z2 - z1) / math.dist([x1, y1], [x2, y2])

        if abs(math.dist([x1, y1], [xp, yp])) + abs(math.dist([x2, y2], [xp, yp])) - \
                abs(math.dist([x2, y2], [x1, y1])) > 0.1:
            xp = x1 + sectors[i] * a
            yp = y1 + sectors[i] * b
            zp = z1 - sectors[i] * (z2 - z1) / math.dist([x1, y1], [x2, y2])

        racing_line.append([xp, yp, zp])
    return racing_line

def get_lap_time(racing_line:list, return_all=False):
    '''Fitness function

    Computes the laptime given a racing line made of sector points.
    This function computes a racing line passing through the sector points and compute the vehicle speed in each point of the racing line.

    Parameters
    ----------
    racing_line : array
        Racing line in sector points
    return_all : boolean
        A flag to return the optional values (default is False)

    Returns
    -------
    lap_time : float
        Lap time in seconds
    v : list[float], optional
        Speed value for each point in the computed racing line
    x : int, optional
        x coordinate for each point of the computed racing line
    y : int, optional
        y coordinate for each point of the computed racing line
    z : int, optional
        z coordinate (elevation) for each point of the computed racing line
    '''
    # Computing the spline function passing through the racing_line points
    rl = np.array(racing_line)
    tck, _ = interpolate.splprep([rl[:,0], rl[:,1], rl[:,2]], s=0.0, per=0)
    x, y, z = interpolate.splev(np.linspace(0, 1, 1000), tck)

    # Computing derivatives
    dx, dy, dz = np.gradient(x), np.gradient(y), np.gradient(z)
    d2x, d2y, d2z = np.gradient(dx), np.gradient(dy), np.gradient(dz)

    curvature = np.abs(dx * d2y - d2x * dy) / (dx * dx + dy * dy)**1.5
    radius = [1/c for c in curvature]

    us = 0.13  # Coefficient of friction

    # Computing speed at each point
    v = [min(10, math.sqrt(us * r * 9.81)) for r in radius]

    # Computing lap time around the track
    lap_time = sum([math.sqrt((x[i] - x[i+1])**2 + (y[i] - y[i+1])**2 + (z[i] - z[i+1])**2) / v[i] for i in range(len(x)-1)])
    
    if return_all:
        return lap_time, v, x, y, z
    return lap_time

def define_sectors(center_line : LineString, inside_line : LineString, outside_line : LineString, n_sectors : int):
    '''Defines sectors' search space
    
    Parameters
    ----------
    center_line : LineString
        Center line of the track
    inside_line : LineString
        Inside line of the track
    outside_line : LineString
        Outside line of the track
    n_sectors : int
        Number of sectors

    Returns
    -------
    inside_points : list
        List coordinates corresponding to the internal point of each sector segment
    outside_points : list
        List coordinates corresponding to the external point of each sector segment
    '''
    
    distances = np.linspace(0, center_line.length, n_sectors)
    center_points_temp = [center_line.interpolate(distance) for distance in distances]
    center_points = np.array([[point.x, point.y, point.z] for point in center_points_temp])

    distances = np.linspace(0, inside_line.length, 1000)
    inside_border = [inside_line.interpolate(distance) for distance in distances]
    inside_border = np.array([[e.x, e.y] for e in inside_border])
    inside_points = np.array([get_closet_points([center_points[i][0], center_points[i][1]], inside_border) for i in range(len(center_points))])
    inside_points = np.array([[point[0], point[1], center_points[i][2]] for i, point in enumerate(inside_points)])

    distances = np.linspace(0, outside_line.length, 1000)
    outside_border = [outside_line.interpolate(distance) for distance in distances]
    outside_border = np.array([[e.x, e.y] for e in outside_border])
    outside_points = np.array([get_closet_points([center_points[i][0], center_points[i][1]], outside_border) for i in range(len(center_points))])
    outside_points = np.array([[point[0], point[1], center_points[i][2]] for i, point in enumerate(outside_points)])

    return inside_points, outside_points

import plotly.graph_objects as go

def plot_final_racing_line(inside_points, outside_points, x, y, v, global_solution):
    # Create plot
    fig = go.Figure()

    # Add racing line
    rl = np.array(sectors_to_racing_line(global_solution, inside_points, outside_points))
    fig.add_trace(go.Scatter(x=rl[:,0], y=rl[:,1], mode='lines', name='Racing Line', line=dict(color='red')))

    # Add scatter points
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', marker=dict(size=6, color=v, colorscale='RdYlGn'), line=dict(width=4, color='grey'), name='Speed Points'))

    # Add inside and outside track lines
    inside_line = np.array(inside_points)
    outside_line = np.array(outside_points)
    fig.add_trace(go.Scatter(x=inside_line[:,0], y=inside_line[:,1], mode='lines', name='Inside Line', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=outside_line[:,0], y=outside_line[:,1], mode='lines', name='Outside Line', line=dict(color='blue')))

    # Update layout
    fig.update_layout(title="Final Racing Line", showlegend=True)

    fig.show()


if __name__ == "__main__":    
    main()
