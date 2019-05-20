import sys
import numpy as np
import pandas as pd
from scipy import interpolate
import matplotlib.pyplot as plt

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, \
    QWidget, QPushButton, QLabel, QSlider, QComboBox, QStyleFactory

import GpsCoordinates

matplotlib.use('Qt5Agg')

current_okato = 45293566000
agent_counter = 0

# probability_kindergarten = 0.05
# probability_household = 0.9 * probability_kindergarten
# probability_school = 0.9 * probability_household
# probability_work = 0.9 * probability_school
infection_probability_on_contact = 0.05
probability_of_self_infection = 0.01

kindergarten_probability_amplifier = 1.1
household_probability_amplifier = 1.0
school_probability_amplifier = 1.0
work_probability_amplifier = 0.9
work_metro_probability_amplifier = 1.0
# beta_kindergarten = 1
# beta_household = 1
# beta_school = 1
# beta_work = 1
# R = 1.5  # Seasonal flu basic reproductive number
# c = 30
# d = 24 * 7
# the expected number of individuals infected by one infectious individual in a completely susceptible population

kindergarten_number_of_hours = 10
school_number_of_hours = 7
work_number_of_hours = 9
# household_number_of_hours = 6
household_number_of_hours = 14

winter_boost = 1.1


def find_num_of_people_each_year(x):
    x_points = [1920, 1923, 1926, 1939, 1959, 1970, 1979, 1989, 2002, 2010, 2012]
    y_points = [1027.3, 1542.9, 2025.9, 4137.0, 5085.6, 7061.0, 7931.6, 8875.6, 10382.8, 11503.5, 11612.9]

    tck = interpolate.splrep(x_points, y_points)
    return interpolate.splev(x, tck)


class Agent:

    number_of_days_infected = -1
    number_of_days_recovered = -1
    working_group_using_metro_index = -1
    working_group_not_using_metro_index = -1
    kindergarten_group_index = -1
    school_group_index = -1
    isStayingHome = False

    def __init__(
            self, unique_id, sex, age, age_group,  health_status, economic_status,
            metro_use, marriage_status, education_status, household_id):
        # Id
        self.unique_id = unique_id
        # Sex: 0 - male, 1 - female
        self.sex = sex
        # Age
        self.age = age
        self.age_group = age_group
        # Status: 0 - susceptible, 1 - infected, recovered to be added
        self.health_status = health_status
        if health_status == 1:
            self.number_of_days_infected = np.random.randint(0, 3)
            if self.number_of_days_infected == 0:
                if age < 8:
                    if np.random.random() < 0.304:
                        self.isStayingHome = True
                elif age < 19:
                    if np.random.random() < 0.203:
                        self.isStayingHome = True
                else:
                    if np.random.random() < 0.1:
                        self.isStayingHome = True
            if self.number_of_days_infected == 1:
                if age < 8:
                    if np.random.random() < 0.575:
                        self.isStayingHome = True
                elif age < 19:
                    if np.random.random() < 0.498:
                        self.isStayingHome = True
                else:
                    if np.random.random() < 0.333:
                        self.isStayingHome = True
            elif self.number_of_days_infected == 2:
                if age < 8:
                    if np.random.random() < 0.324:
                        self.isStayingHome = True
                elif age < 19:
                    if np.random.random() < 0.375:
                        self.isStayingHome = True
                else:
                    if np.random.random() < 0.167:
                        self.isStayingHome = True

        elif health_status == 2:
            self.number_of_days_recovered = np.random.randint(0, 60)
        # Status: 0 - working, 1 - not working, 2 - inactive, 3 - child, 4 - retired
        self.economic_status = economic_status
        self.metro_use = metro_use
        self.marriage_status = marriage_status
        self.education_status = education_status
        self.household_id = household_id


class Household:
    agent_list = []

    def __init__(
            self, unique_id, pos, closest_school, closest_kindergarten, num_of_people_in_household, status,
            num_of_children, num_of_people_working, agent_list):
        self.unique_id = unique_id
        self.position = pos
        self.closest_school = closest_school
        self.closest_kindergarten = closest_kindergarten
        self.size = num_of_people_in_household
        self.status = status
        self.num_of_children = num_of_children
        self.num_of_people_working = num_of_people_working
        self.agent_list = agent_list


class Kindergarten:

    groups_by_age = {0: [[]], 1: [[]], 2: [[]], 3: [[]], 4: [[]],
                     5: [[]], 6: [[]]}
    index_of_the_group_by_age = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}

    def __init__(self, unique_id, pos):
        self.unique_id = unique_id
        self.position = pos

    def add_agent_to_the_group(self, agent):
        if len(self.groups_by_age[agent.age][self.index_of_the_group_by_age[agent.age]]) >= 20:
            self.groups_by_age[agent.age].append([])
            self.index_of_the_group_by_age[agent.age] += 1
        self.groups_by_age[agent.age][self.index_of_the_group_by_age[agent.age]].append(agent)
        agent.kindergarten_group_index = self.index_of_the_group_by_age[agent.age]


class School:

    groups_by_age = {7: [[]], 8: [[]], 9: [[]], 10: [[]], 11: [[]],
                     12: [[]], 13: [[]], 14: [[]], 15: [[]], 16: [[]],
                     17: [[]], 18: [[]]}
    index_of_the_group_by_age = {7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0}

    def __init__(self, unique_id, pos):
        self.unique_id = unique_id
        self.position = pos

    def add_agent_to_the_group(self, agent):
        if len(self.groups_by_age[agent.age][self.index_of_the_group_by_age[agent.age]]) >= 20:
            self.groups_by_age[agent.age].append([])
            self.index_of_the_group_by_age[agent.age] += 1
        self.groups_by_age[agent.age][self.index_of_the_group_by_age[agent.age]].append(agent)
        agent.school_group_index = self.index_of_the_group_by_age[agent.age]


class Work:
    groups = [[]]
    index_of_the_group = 0

    def __init__(self, unique_id):
        self.unique_id = unique_id

    def add_agent_to_the_group(self, agent):
        if len(self.groups[self.index_of_the_group]) >= 20:
            self.groups.append([])
            self.index_of_the_group += 1
        self.groups[self.index_of_the_group].append(agent)
        agent.working_group_not_using_metro_index = self.index_of_the_group
        agent.working_group_using_metro_index = self.index_of_the_group


class Model:
    def __init__(self, num_of_agents, num_rows, num_cols):
        # Number of agents in population
        self.num_of_agents = num_of_agents

        # Grid width and height
        self.grid_width = num_cols
        self.grid_height = num_rows

        # Speed with which agents travel
        # self.speed = 0.1

        # Current date and time
        self.hour = 0
        self.day = 1
        self.day_of_the_week = 1
        self.week_of_the_month = 1
        self.month = 1

        self.year = 1
        self.day_of_the_year = 0

        self.weekday = True

        # Number of susceptible, recovered, infected people right now
        self.infected = 0
        self.recovered = 0
        self.susceptible = num_of_agents

        # Status of the system: 0 - agents should be at home, 1 - agents should be at work
        # self.system_status = 0

        # # Unnecessary
        # self.neighbor_distance = neighbor_distance

        # Agent list
        # self.agent_list = []
        # Household list
        # self.household_list = []
        # Current agent positions
        self.agent_positions = np.zeros([num_of_agents, 2], dtype='int64')

        self.infected_agents = []
        self.recovered_agents = []
        # Positions where agents work
        # self.work_positions = np.zeros([num_of_agents, 2], dtype='int64')
        # self.work_indexes = np.zeros(num_of_agents, dtype='int64')
        # Homes
        # self.home_indexes = np.zeros(num_of_agents, dtype='int64')
        # Colors of agents
        self.agent_colors = np.zeros([self.num_of_agents, 3])
        self.agent_colors[:, 2] = 1.0
        # Grid
        # self.grid = np.full((num_rows, num_cols, num_of_agents), -1)
        # self.grid = np.full((num_rows, num_cols), -1)

        self.work_list = [Work(0)]

        # self.work_groups_using_metro = [[]]
        # self.metro_group_index = 0
        #
        # self.work_groups_not_using_metro = [[]]
        # self.non_metro_group_index = 0

        # ----------------Home area------------------
        self.home_coords = []
        for coord in GpsCoordinates.get_home_coordinates(current_okato):
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            self.home_coords.append(c)
        self.home_coords = np.array(self.home_coords)
        # -------------------------------------------

        # ----------------Metro area-----------------
        self.metro_coords = []
        for coord in GpsCoordinates.get_metro_coordinates():
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            self.metro_coords.append(c)
        self.metro_coords = np.array(self.metro_coords)
        # --------------------------------------------

        # -----------Age, sex, households, districts-------------
        dist_df = pd.read_excel('C:\\Users\\sigla\\Desktop\\MasterWork\\Population.xls')
        self.districts = dist_df['OKATO'].astype('int64')
        # home_okato = pd.read_csv(r'C:\Users\sigla\Desktop\MasterWork\HomeOkato.csv', header=None, index_col=0)
        # home_okato.index = pd.RangeIndex(len(home_okato))
        self.age_sex_districts = pd.read_csv(r'C:\Users\sigla\Desktop\MasterWork\AgeSexDistricts.csv', index_col='OKATO')
        self.age_districts_number_of_people = pd.read_csv(
            r'C:\Users\sigla\Desktop\MasterWork\AgeDistrictsNumberOfPeople.csv', index_col='Age')
        self.age_districts_economic_activities = pd.read_csv(
            r'C:\Users\sigla\Desktop\MasterWork\AgeDistrictsEconomicActivities.csv', index_col='Age')
        self.age_districts_marriage = pd.read_csv(
            r'C:\Users\sigla\Desktop\MasterWork\AgeMarriageDistricts.csv', index_col='Age')
        self.children_attendance = pd.read_csv(
            r'C:\Users\sigla\Desktop\MasterWork\ChildrenAttendance.csv', index_col=0)
        self.economic_activity_districts = pd.read_csv(
            r'C:\Users\sigla\Desktop\MasterWork\EconimicActivityDistricts.csv', index_col=0)
        # --------------------------------------------------------

        # --------------Flu area----------------
        flu = pd.read_csv(r'C:\Users\sigla\Desktop\MasterWork\Flu.csv', index_col=0)
        self.mean_flu = pd.concat([flu.iloc[38:, :39].mean(axis=0), flu.iloc[38:-1, 39:].mean(axis=0)], axis=0)
        for i in range(len(self.mean_flu)):
            # mean_flu[i] = mean_flu[i] * (135000 / 10000000)
            # mean_flu[i] = mean_flu[i] * (100000 / 10000000)
            self.mean_flu[i] = self.mean_flu[i] * (140000 / 10000000)
        # population_number_list = []
        # for i in range(1997, 2003):
        #     population_number_list.append(find_num_of_people_each_year(i))
        # i = 0
        # for year in range(1997, 2003):
        #     for j in range(0, 52):
        #         flu.iloc[i, j] = flu.iloc[i, j] / (population_number_list[i] * 1000 * 7 * 24)
        #     i += 1

        # self.mean_flu = pd.concat([flu.iloc[38:, :39].mean(axis=0), flu.iloc[38:-1, 39:].mean(axis=0)], axis=0)
        # for i in range(len(self.mean_flu)):
        #     # print(self.mean_flu, 135 / 10000)
        #     self.mean_flu[i] = self.mean_flu[i] * (135000 / 10000000)
        # plt.figure()
        # plt.plot(range(1, len(self.mean_flu) + 1), self.mean_flu)
        # plt.show()

        # print('Mean flu', self.mean_flu)
        # --------------------------------------

        # # -----------Park zone-------------
        # park_gps_coords = GpsCoordinates.read_osm(r'C:\Users\sigla\Desktop\MasterWork\osm\494.osm')
        # self.park_coords = []
        # for coord in park_gps_coords:
        #     c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
        #                                  GpsCoordinates.bottom_right_gps_coord,
        #                                  num_cols, num_rows)
        #     self.park_coords.append(c)
        # self.park_coords = np.array(self.park_coords)
        # # ---------------------------------
        #
        # # -----------Сinema zone-------------
        # cinema_gps_coords = GpsCoordinates.read_osm(r'C:\Users\sigla\Desktop\MasterWork\osm\495.osm')
        # self.cinema_coords = []
        # for coord in cinema_gps_coords:
        #     c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
        #                                  GpsCoordinates.bottom_right_gps_coord,
        #                                  num_cols, num_rows)
        #     self.cinema_coords.append(c)
        # self.cinema_coords = np.array(self.cinema_coords)
        # # ---------------------------------
        #
        # # -----------Theatre zone-------------
        # theatre_gps_coords = GpsCoordinates.read_osm(r'C:\Users\sigla\Desktop\MasterWork\osm\531.osm')
        # self.theatre_coords = []
        # for coord in theatre_gps_coords:
        #     c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
        #                                  GpsCoordinates.bottom_right_gps_coord,
        #                                  num_cols, num_rows)
        #     self.theatre_coords.append(c)
        # self.theatre_coords = np.array(self.theatre_coords)
        # # ---------------------------------

        # -----------Kindergarten zone-------------
        kindergarten_coords = []
        for coord in GpsCoordinates.get_kindergartens():
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            kindergarten_coords.append(c)
        kindergarten_coords = np.array(kindergarten_coords)

        self.kindergarten_list = []
        for i in range(len(kindergarten_coords)):
            self.kindergarten_list.append(Kindergarten(i, kindergarten_coords[i]))
        self.closest_kindergartens = GpsCoordinates.find_closest_kindergarten_to_each_home(current_okato)
        # ---------------------------------

        # # -----------Kindergarten2 zone-------------
        # kindergarten2_gps_coords = GpsCoordinates.read_osm(r'C:\Users\sigla\Desktop\MasterWork\osm\540.osm')
        # self.kindergarten2_coords = []
        # for coord in kindergarten2_gps_coords:
        #     c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
        #                                  GpsCoordinates.bottom_right_gps_coord,
        #                                  num_cols, num_rows)
        #     self.kindergarten2_coords.append(c)
        # self.kindergarten2_coords = np.array(self.kindergarten2_coords)
        # # ---------------------------------

        # -----------School zone-------------
        school_coords = []
        for coord in GpsCoordinates.get_schools():
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            school_coords.append(c)
        school_coords = np.array(school_coords)

        self.school_list = []
        for i in range(len(school_coords)):
            self.school_list.append(School(i, school_coords[i]))
        self.closest_schools = GpsCoordinates.find_closest_school_to_each_home(current_okato)
        # ---------------------------------

        # # -----------School2 zone-------------
        # school2_gps_coords = GpsCoordinates.read_osm(r'C:\Users\sigla\Desktop\MasterWork\osm\567.osm')
        # self.school2_coords = []
        # for coord in school2_gps_coords:
        #     c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
        #                                  GpsCoordinates.bottom_right_gps_coord,
        #                                  num_cols, num_rows)
        #     self.school2_coords.append(c)
        # self.school2_coords = np.array(self.school2_coords)
        # # ---------------------------------

        # # -----------University zone-------------
        # university_gps_coords = GpsCoordinates.get_universities()
        # self.university_coords = []
        # for coord in university_gps_coords:
        #     c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
        #                                  GpsCoordinates.bottom_right_gps_coord,
        #                                  num_cols, num_rows)
        #     self.university_coords.append(c)
        # self.university_coords = np.array(self.university_coords)
        # # ---------------------------------

        self.closest_metro_stations = GpsCoordinates.get_closest_metro_stations_to_homes()
        # self.closest_metro_stations_to_kindergartens = GpsCoordinates.get_closest_metro_stations_to_kindergartens()
        # self.closest_metro_stations_to_schools = GpsCoordinates.get_closest_metro_stations_to_schools()
        # self.closest_metro_stations_to_universities = GpsCoordinates.get_closest_metro_stations_to_universities()
        self.metro_ways = GpsCoordinates.get_ways_for_metro_stations()

        self.ways_to_work = []
        self.ways_to_home = []
        # self.closest_metro_stations_to_homes = []
        self.closest_metro_stations_to_works = []
        self.curr_positions_in_metro = []
        self.dist_num = self.districts[self.districts == current_okato].index[0] + 1

        self.household_list = []
        household_num = 0
        while agent_counter < num_of_agents:
            print('Current number of agents:', agent_counter)
            household = self.generate_household(household_num)
            # for agent in household.agent_list:
            #     if agent.health_status == 1:
            #         household.num_of_infected += 1
            self.household_list.append(household)
            household_num += 1
        # print(self.num_of_agents_using_metro)
        # print(self.num_of_infected_using_metro)
        # print(self.num_of_agents_not_using_metro)
        # print(self.num_of_infected_not_using_metro)


            # # Debug
            # economic_status = 2
            # education_status = 1
            # if economic_status == 0:
            #     work_index = np.random.randint(0, len(self.home_coords) - 1)
            #     self.closest_metro_stations_to_works.append(self.closest_metro_stations[work_index])
            #     self.ways_to_work.append(self.metro_ways[self.closest_metro_stations[home_index]
            #                                              * (GpsCoordinates.num_of_stations - 1)
            #                                              + self.closest_metro_stations[work_index]
            #                                              + self.closest_metro_stations[home_index]])
            #     self.work_indexes[i] = work_index
            #     self.ways_to_home.append(self.metro_ways[self.closest_metro_stations[work_index]
            #                                              * (GpsCoordinates.num_of_stations - 1)
            #                                              + self.closest_metro_stations[home_index]
            #                                              + self.closest_metro_stations[work_index]])
            #     x = self.home_coords[work_index, 0]
            #     y = self.home_coords[work_index, 1]
            #     pos = np.array((x, y))
            #     self.work_positions[i] = pos
            # elif education_status == 1:
            #     work_index = np.random.randint(0, len(self.kindergarten_coords) - 1)
            #     # work_index = 1641
            #     self.closest_metro_stations_to_works.append(self.closest_metro_stations_to_kindergartens[work_index])
            #     self.ways_to_work.append(self.metro_ways[self.closest_metro_stations[home_index]
            #                                              * (GpsCoordinates.num_of_stations - 1)
            #                                              + self.closest_metro_stations_to_kindergartens[work_index]
            #                                              + self.closest_metro_stations[home_index]])
            #     self.work_indexes[i] = work_index
            #     self.ways_to_home.append(self.metro_ways[self.closest_metro_stations_to_kindergartens[work_index]
            #                                              * (GpsCoordinates.num_of_stations - 1)
            #                                              + self.closest_metro_stations[home_index]
            #                                              + self.closest_metro_stations_to_kindergartens[work_index]])
            #     x = self.kindergarten_coords[work_index, 0]
            #     y = self.kindergarten_coords[work_index, 1]
            #     pos = np.array((x, y))
            #     self.work_positions[i] = pos
            # elif education_status == 2:
            #     work_index = np.random.randint(0, len(self.school_coords) - 1)
            #     # work_index = 87
            #     self.closest_metro_stations_to_works.append(self.closest_metro_stations_to_schools[work_index])
            #     self.ways_to_work.append(self.metro_ways[self.closest_metro_stations[home_index]
            #                                              * (GpsCoordinates.num_of_stations - 1)
            #                                              + self.closest_metro_stations_to_schools[work_index]
            #                                              + self.closest_metro_stations[home_index]])
            #     self.work_indexes[i] = work_index
            #     self.ways_to_home.append(self.metro_ways[self.closest_metro_stations_to_schools[work_index]
            #                                              * (GpsCoordinates.num_of_stations - 1)
            #                                              + self.closest_metro_stations[home_index]
            #                                              + self.closest_metro_stations_to_schools[work_index]])
            #     x = self.school_coords[work_index, 0]
            #     y = self.school_coords[work_index, 1]
            #     pos = np.array((x, y))
            #     self.work_positions[i] = pos
            # elif education_status == 3:
            #     work_index = np.random.randint(0, len(self.university_coords) - 1)
            #     self.closest_metro_stations_to_works.append(self.closest_metro_stations_to_universities[work_index])
            #     self.ways_to_work.append(self.metro_ways[self.closest_metro_stations[home_index]
            #                                              * (GpsCoordinates.num_of_stations - 1)
            #                                              + self.closest_metro_stations_to_universities[work_index]
            #                                              + self.closest_metro_stations[home_index]])
            #     self.work_indexes[i] = work_index
            #     self.ways_to_home.append(self.metro_ways[self.closest_metro_stations_to_universities[work_index]
            #                                              * (GpsCoordinates.num_of_stations - 1)
            #                                              + self.closest_metro_stations[home_index]
            #                                              + self.closest_metro_stations_to_universities[work_index]])
            #     x = self.university_coords[work_index, 0]
            #     y = self.university_coords[work_index, 1]
            #     pos = np.array((x, y))
            #     self.work_positions[i] = pos
            # else:
            #     self.closest_metro_stations_to_works.append(-1)
            #     self.ways_to_work.append([-1])
            #     self.ways_to_home.append([-1])




            # if marriage_status == 0:
            #     rand_num = np.random.randint(low=0, high=100)
            #     cur_level = 2.6
            #     partner_age_diff = 0  # M15-20
            #     if rand_num > cur_level:
            #         partner_age_diff = 1  # M10-14
            #     cur_level += 4.8
            #     if rand_num > cur_level:
            #         partner_age_diff = 2  # M6-9
            #     cur_level += 11.6
            #     if rand_num > cur_level:
            #         partner_age_diff = 3  # M4-5
            #     cur_level += 13.3
            #     if rand_num > cur_level:
            #         partner_age_diff = 4  # M2-3
            #     cur_level += 20.4
            #     if rand_num > cur_level:
            #         partner_age_diff = 5  # M1
            #     cur_level += 33.2
            #     if rand_num > cur_level:
            #         partner_age_diff = 6  # W2-3
            #     cur_level += 6.5
            #     if rand_num > cur_level:
            #         partner_age_diff = 7  # W4-5
            #     cur_level += 3.3
            #     if rand_num > cur_level:
            #         partner_age_diff = 8  # W6-9
            #     cur_level += 2.7
            #     if rand_num > cur_level:
            #         partner_age_diff = 9  # W10-14
            #     if sex = 0:
            #         # add_partner(1, age)
            #     else:
            #         # add_partner(0, age)
            #     i += 2
            # else:
            #     i += 1

        self.infected_by_ticks = [self.infected]
        self.recovered_by_ticks = [self.recovered]
        self.susceptible_by_ticks = [self.susceptible]
        self.new_cases_by_ticks = []
        self.new_cases = 0

    def generate_agent(self, household_id, is_child, sex=-1, age_group=-1, parent_age=-1):
        if sex == -1:
            sex = 0
            if (np.random.random() > (self.age_sex_districts.loc[current_okato, 'Mtotal']
                                      / self.age_sex_districts.loc[current_okato, 'Total'])):
                sex = 1
        if age_group == 3:
            age_group = 4
        if is_child:
            if age_group == -1:
                age_group = self.get_child_agent_age_group(sex)
            age_index, age_index_marriage, age_index_economic_activity, age = self.get_child_agent_age(age_group)
            if parent_age != -1:
                # print(parent_age)
                # print(age)
                while age > parent_age - 18:
                    age_group = self.get_child_agent_age_group(sex)
                    age_index, age_index_marriage, age_index_economic_activity, age = self.get_child_agent_age(
                        age_group)
        else:
            if age_group == -1:
                age_group = self.get_adult_agent_age_group(sex)
            age_index, age_index_marriage, age_index_economic_activity, age = self.get_adult_agent_age(age_group)

        economic_status = self.get_agent_economic_status(sex, age, age_index_economic_activity)
        metro_use = 0
        if economic_status == 0:
            rand_num = np.random.random()
            metro_use = 1
            if rand_num > 7 / 12:
                metro_use = 0
        marriage_status = self.get_agent_marriage_status(age, sex, age_index_marriage)
        education_status = 0
        if 0 <= age <= 6:
            education_status = 1  # Kindergarten
        if 7 <= age <= 18:
            education_status = 2  # School
        health_status = 0  # Susceptible
        if np.random.random() < 0.005:
            health_status = 1  # Infected
        elif np.random.random() < 0.6:
            health_status = 2  # Resistant
        return Agent(
            agent_counter, sex, age, age_group, health_status, economic_status, metro_use,
            marriage_status, education_status, household_id)

    # Not used now
    def children_attendance(self, sex, age):
        education_status = 0
        if age < 7:
            infancy_age_group = 9
            if age < 3:
                infancy_age_group = 2
            elif age < 6:
                infancy_age_group = 5
            rand_num = np.random.random()
            education_status = -1
            if sex == 0:
                total = self.children_attendance.loc[
                    'M{}'.format(infancy_age_group), 'District{}TotalSurveyed'.format(self.dist_num)]
                cur_level = self.children_attendance.loc[
                                'M{}'.format(infancy_age_group), 'District{}NotAttending'.format(self.dist_num)] / total
                if rand_num > cur_level:
                    education_status = 1  # Kindergarten
            if sex == 1:
                total = self.children_attendance.loc[
                    'F{}'.format(infancy_age_group), 'District{}TotalSurveyed'.format(self.dist_num)]
                cur_level = self.children_attendance.loc[
                                'F{}'.format(infancy_age_group), 'District{}NotAttending'.format(self.dist_num)] / total
                if rand_num > cur_level:
                    education_status = 1  # Kindergarten
        return education_status

    # def get_agent_age_group(self, sex):
    #     age_group = 0
    #     rand_number = np.random.random()
    #     age_sex_district = self.age_sex_districts.loc[current_okato, :]
    #     if sex == 0:
    #         cur_level = age_sex_district['M0-4'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 1
    #         cur_level += age_sex_district['M5-9'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 2
    #         cur_level += age_sex_district['M10-14'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 3
    #         cur_level += age_sex_district['M15-19'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 4
    #         cur_level += age_sex_district['M20-24'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 5
    #         cur_level += age_sex_district['M25-29'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 6
    #         cur_level += age_sex_district['M30-34'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 7
    #         cur_level += age_sex_district['M35-39'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 8
    #         cur_level += age_sex_district['M40-44'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 9
    #         cur_level += age_sex_district['M45-49'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 10
    #         cur_level += age_sex_district['M50-54'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 11
    #         cur_level += age_sex_district['M55-59'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 12
    #         cur_level += age_sex_district['M60-64'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 13
    #         cur_level += age_sex_district['M65-69'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 14
    #         cur_level += age_sex_district['M70-74'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 15
    #         cur_level += age_sex_district['M75-79'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 16
    #         cur_level += age_sex_district['M80-84'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 17
    #         cur_level += age_sex_district['M85-89'] / age_sex_district['Mtotal2']
    #         if rand_number > cur_level:
    #             age_group = 18
    #     else:
    #         cur_level = age_sex_district['F0-4'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 1
    #         cur_level += age_sex_district['F5-9'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 2
    #         cur_level += age_sex_district['F10-14'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 3
    #         cur_level += age_sex_district['F15-19'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 4
    #         cur_level += age_sex_district['F20-24'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 5
    #         cur_level += age_sex_district['F25-29'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 6
    #         cur_level += age_sex_district['F30-34'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 7
    #         cur_level += age_sex_district['F35-39'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 8
    #         cur_level += age_sex_district['F40-44'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 9
    #         cur_level += age_sex_district['F45-49'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 10
    #         cur_level += age_sex_district['F50-54'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 11
    #         cur_level += age_sex_district['F55-59'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 12
    #         cur_level += age_sex_district['F60-64'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 13
    #         cur_level += age_sex_district['F65-69'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 14
    #         cur_level += age_sex_district['F70-74'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 15
    #         cur_level += age_sex_district['F75-79'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 16
    #         cur_level += age_sex_district['F80-84'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 17
    #         cur_level += age_sex_district['F85-89'] / age_sex_district['Ftotal2']
    #         if rand_number > cur_level:
    #             age_group = 18
    #     return age_group

    def get_adult_agent_age_group(self, sex):
        age_group = 3
        rand_number = np.random.random()
        age_sex_district = self.age_sex_districts.loc[current_okato, :]
        if sex == 0:
            total = age_sex_district['M15-19'] + age_sex_district['M20-24'] \
                    + age_sex_district['M25-29'] + age_sex_district['M30-34'] \
                    + age_sex_district['M35-39'] + age_sex_district['M40-44'] \
                    + age_sex_district['M45-49'] + age_sex_district['M50-54'] \
                    + age_sex_district['M55-59'] + age_sex_district['M60-64'] \
                    + age_sex_district['M65-69'] + age_sex_district['M70-74'] \
                    + age_sex_district['M75-79'] + age_sex_district['M80-84'] \
                    + age_sex_district['M85-89']
            cur_level = age_sex_district['M15-19'] / total
            if rand_number > cur_level:
                age_group = 4
            cur_level += age_sex_district['M20-24'] / total
            if rand_number > cur_level:
                age_group = 5
            cur_level += age_sex_district['M25-29'] / total
            if rand_number > cur_level:
                age_group = 6
            cur_level += age_sex_district['M30-34'] / total
            if rand_number > cur_level:
                age_group = 7
            cur_level += age_sex_district['M35-39'] / total
            if rand_number > cur_level:
                age_group = 8
            cur_level += age_sex_district['M40-44'] / total
            if rand_number > cur_level:
                age_group = 9
            cur_level += age_sex_district['M45-49'] / total
            if rand_number > cur_level:
                age_group = 10
            cur_level += age_sex_district['M50-54'] / total
            if rand_number > cur_level:
                age_group = 11
            cur_level += age_sex_district['M55-59'] / total
            if rand_number > cur_level:
                age_group = 12
            cur_level += age_sex_district['M60-64'] / total
            if rand_number > cur_level:
                age_group = 13
            cur_level += age_sex_district['M65-69'] / total
            if rand_number > cur_level:
                age_group = 14
            cur_level += age_sex_district['M70-74'] / total
            if rand_number > cur_level:
                age_group = 15
            cur_level += age_sex_district['M75-79'] / total
            if rand_number > cur_level:
                age_group = 16
            cur_level += age_sex_district['M80-84'] / total
            if rand_number > cur_level:
                age_group = 17
        else:
            total = age_sex_district['F15-19'] + age_sex_district['F20-24'] \
                    + age_sex_district['F25-29'] + age_sex_district['F30-34'] \
                    + age_sex_district['F35-39'] + age_sex_district['F40-44'] \
                    + age_sex_district['F45-49'] + age_sex_district['F50-54'] \
                    + age_sex_district['F55-59'] + age_sex_district['F60-64'] \
                    + age_sex_district['F65-69'] + age_sex_district['F70-74'] \
                    + age_sex_district['F75-79'] + age_sex_district['F80-84'] \
                    + age_sex_district['F85-89']
            cur_level = age_sex_district['F15-19'] / total
            if rand_number > cur_level:
                age_group = 4
            cur_level += age_sex_district['F20-24'] / total
            if rand_number > cur_level:
                age_group = 5
            cur_level += age_sex_district['F25-29'] / total
            if rand_number > cur_level:
                age_group = 6
            cur_level += age_sex_district['F30-34'] / total
            if rand_number > cur_level:
                age_group = 7
            cur_level += age_sex_district['F35-39'] / total
            if rand_number > cur_level:
                age_group = 8
            cur_level += age_sex_district['F40-44'] / total
            if rand_number > cur_level:
                age_group = 9
            cur_level += age_sex_district['F45-49'] / total
            if rand_number > cur_level:
                age_group = 10
            cur_level += age_sex_district['F50-54'] / total
            if rand_number > cur_level:
                age_group = 11
            cur_level += age_sex_district['F55-59'] / total
            if rand_number > cur_level:
                age_group = 12
            cur_level += age_sex_district['F60-64'] / total
            if rand_number > cur_level:
                age_group = 13
            cur_level += age_sex_district['F65-69'] / total
            if rand_number > cur_level:
                age_group = 14
            cur_level += age_sex_district['F70-74'] / total
            if rand_number > cur_level:
                age_group = 15
            cur_level += age_sex_district['F75-79'] / total
            if rand_number > cur_level:
                age_group = 16
            cur_level += age_sex_district['F80-84'] / total
            if rand_number > cur_level:
                age_group = 17
        return age_group

    def get_adult_parent_agent_age_group(self, sex):
        age_group = 3
        rand_number = np.random.random()
        age_sex_district = self.age_sex_districts.loc[current_okato, :]
        if sex == 0:
            total = age_sex_district['M35-39'] + age_sex_district['M40-44'] \
                    + age_sex_district['M45-49'] + age_sex_district['M50-54'] \
                    + age_sex_district['M55-59'] + age_sex_district['M60-64'] \
                    + age_sex_district['M65-69'] + age_sex_district['M70-74'] \
                    + age_sex_district['M75-79'] + age_sex_district['M80-84'] \
                    + age_sex_district['M85-89']
            cur_level = age_sex_district['M35-39'] / total
            if rand_number > cur_level:
                age_group = 8
            cur_level += age_sex_district['M40-44'] / total
            if rand_number > cur_level:
                age_group = 9
            cur_level += age_sex_district['M45-49'] / total
            if rand_number > cur_level:
                age_group = 10
            cur_level += age_sex_district['M50-54'] / total
            if rand_number > cur_level:
                age_group = 11
            cur_level += age_sex_district['M55-59'] / total
            if rand_number > cur_level:
                age_group = 12
            cur_level += age_sex_district['M60-64'] / total
            if rand_number > cur_level:
                age_group = 13
            cur_level += age_sex_district['M65-69'] / total
            if rand_number > cur_level:
                age_group = 14
            cur_level += age_sex_district['M70-74'] / total
            if rand_number > cur_level:
                age_group = 15
            cur_level += age_sex_district['M75-79'] / total
            if rand_number > cur_level:
                age_group = 16
            cur_level += age_sex_district['M80-84'] / total
            if rand_number > cur_level:
                age_group = 17
        else:
            total = age_sex_district['F35-39'] + age_sex_district['F40-44'] \
                    + age_sex_district['F45-49'] + age_sex_district['F50-54'] \
                    + age_sex_district['F55-59'] + age_sex_district['F60-64'] \
                    + age_sex_district['F65-69'] + age_sex_district['F70-74'] \
                    + age_sex_district['F75-79'] + age_sex_district['F80-84'] \
                    + age_sex_district['F85-89']
            cur_level = age_sex_district['F35-39'] / total
            if rand_number > cur_level:
                age_group = 8
            cur_level += age_sex_district['F40-44'] / total
            if rand_number > cur_level:
                age_group = 9
            cur_level += age_sex_district['F45-49'] / total
            if rand_number > cur_level:
                age_group = 10
            cur_level += age_sex_district['F50-54'] / total
            if rand_number > cur_level:
                age_group = 11
            cur_level += age_sex_district['F55-59'] / total
            if rand_number > cur_level:
                age_group = 12
            cur_level += age_sex_district['F60-64'] / total
            if rand_number > cur_level:
                age_group = 13
            cur_level += age_sex_district['F65-69'] / total
            if rand_number > cur_level:
                age_group = 14
            cur_level += age_sex_district['F70-74'] / total
            if rand_number > cur_level:
                age_group = 15
            cur_level += age_sex_district['F75-79'] / total
            if rand_number > cur_level:
                age_group = 16
            cur_level += age_sex_district['F80-84'] / total
            if rand_number > cur_level:
                age_group = 17
        return age_group

    def get_child_agent_age_group(self, sex):
        age_group = 0
        rand_number = np.random.random()
        age_sex_district = self.age_sex_districts.loc[current_okato, :]
        if sex == 0:
            total = age_sex_district['M0-4'] + age_sex_district['M5-9']\
                    + age_sex_district['M10-14'] + age_sex_district['M15-19']
            cur_level = age_sex_district['M0-4'] / total
            if rand_number > cur_level:
                age_group = 1
            cur_level += age_sex_district['M5-9'] / total
            if rand_number > cur_level:
                age_group = 2
            cur_level += age_sex_district['M10-14'] / total
            if rand_number > cur_level:
                age_group = 3
        else:
            total = age_sex_district['F0-4'] + age_sex_district['F5-9'] \
                    + age_sex_district['F10-14'] + age_sex_district['F15-19']
            cur_level = age_sex_district['F0-4'] / total
            if rand_number > cur_level:
                age_group = 1
            cur_level += age_sex_district['F5-9'] / total
            if rand_number > cur_level:
                age_group = 2
            cur_level += age_sex_district['F10-14'] / total
            if rand_number > cur_level:
                age_group = 3
        return age_group

    # def get_agent_age(self, age_group):
    #     if age_group == 0:
    #         age_index = 14
    #         age_index_economic_activity = 0
    #         age_index_marriage = 0
    #         rand_number = np.random.random()
    #         age = 0
    #         if rand_number > 0.2:
    #             age = 1
    #         if rand_number > 0.4:
    #             age = 2
    #         if rand_number > 0.6:
    #             age = 3
    #         if rand_number > 0.8:
    #             age = 4
    #     elif age_group == 1:
    #         age_index = 14
    #         age_index_economic_activity = 0
    #         age_index_marriage = 0
    #         rand_number = np.random.random()
    #         age = 5
    #         if rand_number > 0.2:
    #             age = 6
    #         if rand_number > 0.4:
    #             age = 7
    #         if rand_number > 0.6:
    #             age = 8
    #         if rand_number > 0.8:
    #             age = 9
    #     elif age_group == 2:
    #         age_index = 14
    #         age_index_economic_activity = 0
    #         age_index_marriage = 0
    #         rand_number = np.random.random()
    #         age = 10
    #         if rand_number > 0.2:
    #             age = 11
    #         if rand_number > 0.4:
    #             age = 12
    #         if rand_number > 0.6:
    #             age = 13
    #         if rand_number > 0.8:
    #             age = 14
    #     elif age_group == 3:
    #         age_index = 17
    #         age_index_economic_activity = 15
    #         age_index_marriage = 0
    #         rand_number = np.random.random()
    #         age = 15
    #         if rand_number > 0.2:
    #             age = 16
    #             age_index_marriage = 17
    #         if rand_number > 0.4:
    #             age = 17
    #             age_index_marriage = 17
    #         if rand_number > 0.6:
    #             age_index = 24
    #             age = 18
    #             age_index_marriage = 19
    #         if rand_number > 0.8:
    #             age_index = 24
    #             age = 19
    #             age_index_marriage = 19
    #     elif age_group == 4:
    #         age_index = 24
    #         age_index_marriage = 24
    #         age_index_economic_activity = 20
    #         rand_number = np.random.random()
    #         age = 20
    #         if rand_number > 0.2:
    #             age = 21
    #         if rand_number > 0.4:
    #             age = 22
    #         if rand_number > 0.6:
    #             age = 23
    #         if rand_number > 0.8:
    #             age = 24
    #     elif age_group == 5:
    #         age_index = 34
    #         age_index_marriage = 29
    #         age_index_economic_activity = 20
    #         rand_number = np.random.random()
    #         age = 25
    #         if rand_number > 0.2:
    #             age = 26
    #         if rand_number > 0.4:
    #             age = 27
    #         if rand_number > 0.6:
    #             age = 28
    #         if rand_number > 0.8:
    #             age = 29
    #     elif age_group == 6:
    #         age_index = 34
    #         age_index_marriage = 34
    #         age_index_economic_activity = 30
    #         rand_number = np.random.random()
    #         age = 30
    #         if rand_number > 0.2:
    #             age = 31
    #         if rand_number > 0.4:
    #             age = 32
    #         if rand_number > 0.6:
    #             age = 33
    #         if rand_number > 0.8:
    #             age = 34
    #     elif age_group == 7:
    #         age_index = 44
    #         age_index_marriage = 39
    #         age_index_economic_activity = 30
    #         rand_number = np.random.random()
    #         age = 35
    #         if rand_number > 0.2:
    #             age = 36
    #         if rand_number > 0.4:
    #             age = 37
    #         if rand_number > 0.6:
    #             age = 38
    #         if rand_number > 0.8:
    #             age = 39
    #     elif age_group == 8:
    #         age_index = 44
    #         age_index_marriage = 44
    #         age_index_economic_activity = 40
    #         rand_number = np.random.random()
    #         age = 40
    #         if rand_number > 0.2:
    #             age = 41
    #         if rand_number > 0.4:
    #             age = 42
    #         if rand_number > 0.6:
    #             age = 43
    #         if rand_number > 0.8:
    #             age = 44
    #     elif age_group == 9:
    #         age_index = 54
    #         age_index_marriage = 49
    #         age_index_economic_activity = 40
    #         rand_number = np.random.random()
    #         age = 45
    #         if rand_number > 0.2:
    #             age = 46
    #         if rand_number > 0.4:
    #             age = 47
    #         if rand_number > 0.6:
    #             age = 48
    #         if rand_number > 0.8:
    #             age = 49
    #     elif age_group == 10:
    #         age_index = 54
    #         age_index_marriage = 54
    #         age_index_economic_activity = 50
    #         rand_number = np.random.random()
    #         age = 50
    #         if rand_number > 0.2:
    #             age = 51
    #         if rand_number > 0.4:
    #             age = 52
    #         if rand_number > 0.6:
    #             age = 53
    #         if rand_number > 0.8:
    #             age = 54
    #     elif age_group == 11:
    #         age_index = 64
    #         age_index_marriage = 59
    #         age_index_economic_activity = 50
    #         rand_number = np.random.random()
    #         age = 55
    #         if rand_number > 0.2:
    #             age = 56
    #         if rand_number > 0.4:
    #             age = 57
    #         if rand_number > 0.6:
    #             age = 58
    #         if rand_number > 0.8:
    #             age = 59
    #     elif age_group == 12:
    #         age_index = 64
    #         age_index_marriage = 64
    #         age_index_economic_activity = 60
    #         rand_number = np.random.random()
    #         age = 60
    #         if rand_number > 0.2:
    #             age = 61
    #         if rand_number > 0.4:
    #             age = 62
    #         if rand_number > 0.6:
    #             age = 63
    #         if rand_number > 0.8:
    #             age = 64
    #     elif age_group == 13:
    #         age_index = 65
    #         age_index_marriage = 69
    #         age_index_economic_activity = 60
    #         rand_number = np.random.random()
    #         age = 65
    #         if rand_number > 0.2:
    #             age = 66
    #         if rand_number > 0.4:
    #             age = 67
    #         if rand_number > 0.6:
    #             age = 68
    #         if rand_number > 0.8:
    #             age = 69
    #     elif age_group == 14:
    #         age_index = 65
    #         age_index_marriage = 70
    #         age_index_economic_activity = 60
    #         rand_number = np.random.random()
    #         age = 70
    #         if rand_number > 0.2:
    #             age = 71
    #         if rand_number > 0.4:
    #             age = 72
    #         if rand_number > 0.6:
    #             age = 73
    #         if rand_number > 0.8:
    #             age = 74
    #     elif age_group == 15:
    #         age_index = 65
    #         age_index_marriage = 70
    #         age_index_economic_activity = 60
    #         rand_number = np.random.random()
    #         age = 75
    #         if rand_number > 0.2:
    #             age = 76
    #         if rand_number > 0.4:
    #             age = 77
    #         if rand_number > 0.6:
    #             age = 78
    #         if rand_number > 0.8:
    #             age = 79
    #     elif age_group == 16:
    #         age_index = 65
    #         age_index_marriage = 70
    #         age_index_economic_activity = 60
    #         rand_number = np.random.random()
    #         age = 80
    #         if rand_number > 0.2:
    #             age = 81
    #         if rand_number > 0.4:
    #             age = 82
    #         if rand_number > 0.6:
    #             age = 83
    #         if rand_number > 0.8:
    #             age = 84
    #     elif age_group == 17:
    #         age_index = 65
    #         age_index_marriage = 70
    #         age_index_economic_activity = 60
    #         rand_number = np.random.random()
    #         age = 85
    #         if rand_number > 0.2:
    #             age = 86
    #         if rand_number > 0.4:
    #             age = 87
    #         if rand_number > 0.6:
    #             age = 88
    #         if rand_number > 0.8:
    #             age = 89
    #     elif age_group == 18:
    #         age_index = 65
    #         age_index_marriage = 70
    #         age_index_economic_activity = 60
    #         rand_number = np.random.random()
    #         age = 90
    #         if rand_number > 0.2:
    #             age = 91
    #         if rand_number > 0.4:
    #             age = 92
    #         if rand_number > 0.6:
    #             age = 93
    #         if rand_number > 0.8:
    #             age = 94
    #     return age_index, age_index_marriage, age_index_economic_activity, age

    def get_adult_agent_age(self, age_group):
        if age_group == 3:
            age_index = 24
            age_index_economic_activity = 15
            age_index_marriage = 19
            rand_number = np.random.random()
            age = 18
            if rand_number > 0.5:
                age = 19
        elif age_group == 4:
            age_index = 24
            age_index_marriage = 24
            age_index_economic_activity = 20
            rand_number = np.random.random()
            age = 20
            if rand_number > 0.2:
                age = 21
            if rand_number > 0.4:
                age = 22
            if rand_number > 0.6:
                age = 23
            if rand_number > 0.8:
                age = 24
        elif age_group == 5:
            age_index = 34
            age_index_marriage = 29
            age_index_economic_activity = 20
            rand_number = np.random.random()
            age = 25
            if rand_number > 0.2:
                age = 26
            if rand_number > 0.4:
                age = 27
            if rand_number > 0.6:
                age = 28
            if rand_number > 0.8:
                age = 29
        elif age_group == 6:
            age_index = 34
            age_index_marriage = 34
            age_index_economic_activity = 30
            rand_number = np.random.random()
            age = 30
            if rand_number > 0.2:
                age = 31
            if rand_number > 0.4:
                age = 32
            if rand_number > 0.6:
                age = 33
            if rand_number > 0.8:
                age = 34
        elif age_group == 7:
            age_index = 44
            age_index_marriage = 39
            age_index_economic_activity = 30
            rand_number = np.random.random()
            age = 35
            if rand_number > 0.2:
                age = 36
            if rand_number > 0.4:
                age = 37
            if rand_number > 0.6:
                age = 38
            if rand_number > 0.8:
                age = 39
        elif age_group == 8:
            age_index = 44
            age_index_marriage = 44
            age_index_economic_activity = 40
            rand_number = np.random.random()
            age = 40
            if rand_number > 0.2:
                age = 41
            if rand_number > 0.4:
                age = 42
            if rand_number > 0.6:
                age = 43
            if rand_number > 0.8:
                age = 44
        elif age_group == 9:
            age_index = 54
            age_index_marriage = 49
            age_index_economic_activity = 40
            rand_number = np.random.random()
            age = 45
            if rand_number > 0.2:
                age = 46
            if rand_number > 0.4:
                age = 47
            if rand_number > 0.6:
                age = 48
            if rand_number > 0.8:
                age = 49
        elif age_group == 10:
            age_index = 54
            age_index_marriage = 54
            age_index_economic_activity = 50
            rand_number = np.random.random()
            age = 50
            if rand_number > 0.2:
                age = 51
            if rand_number > 0.4:
                age = 52
            if rand_number > 0.6:
                age = 53
            if rand_number > 0.8:
                age = 54
        elif age_group == 11:
            age_index = 64
            age_index_marriage = 59
            age_index_economic_activity = 50
            rand_number = np.random.random()
            age = 55
            if rand_number > 0.2:
                age = 56
            if rand_number > 0.4:
                age = 57
            if rand_number > 0.6:
                age = 58
            if rand_number > 0.8:
                age = 59
        elif age_group == 12:
            age_index = 64
            age_index_marriage = 64
            age_index_economic_activity = 60
            rand_number = np.random.random()
            age = 60
            if rand_number > 0.2:
                age = 61
            if rand_number > 0.4:
                age = 62
            if rand_number > 0.6:
                age = 63
            if rand_number > 0.8:
                age = 64
        elif age_group == 13:
            age_index = 65
            age_index_marriage = 69
            age_index_economic_activity = 60
            rand_number = np.random.random()
            age = 65
            if rand_number > 0.2:
                age = 66
            if rand_number > 0.4:
                age = 67
            if rand_number > 0.6:
                age = 68
            if rand_number > 0.8:
                age = 69
        elif age_group == 14:
            age_index = 65
            age_index_marriage = 70
            age_index_economic_activity = 60
            rand_number = np.random.random()
            age = 70
            if rand_number > 0.2:
                age = 71
            if rand_number > 0.4:
                age = 72
            if rand_number > 0.6:
                age = 73
            if rand_number > 0.8:
                age = 74
        elif age_group == 15:
            age_index = 65
            age_index_marriage = 70
            age_index_economic_activity = 60
            rand_number = np.random.random()
            age = 75
            if rand_number > 0.2:
                age = 76
            if rand_number > 0.4:
                age = 77
            if rand_number > 0.6:
                age = 78
            if rand_number > 0.8:
                age = 79
        elif age_group == 16:
            age_index = 65
            age_index_marriage = 70
            age_index_economic_activity = 60
            rand_number = np.random.random()
            age = 80
            if rand_number > 0.2:
                age = 81
            if rand_number > 0.4:
                age = 82
            if rand_number > 0.6:
                age = 83
            if rand_number > 0.8:
                age = 84
        elif age_group == 17:
            age_index = 65
            age_index_marriage = 70
            age_index_economic_activity = 60
            rand_number = np.random.random()
            age = 85
            if rand_number > 0.2:
                age = 86
            if rand_number > 0.4:
                age = 87
            if rand_number > 0.6:
                age = 88
            if rand_number > 0.8:
                age = 89
        return age_index, age_index_marriage, age_index_economic_activity, age

    def get_child_agent_age(self, age_group):
        if age_group == 0:
            age_index = 14
            age_index_economic_activity = 0
            age_index_marriage = 0
            rand_number = np.random.random()
            age = 0
            if rand_number > 0.2:
                age = 1
            if rand_number > 0.4:
                age = 2
            if rand_number > 0.6:
                age = 3
            if rand_number > 0.8:
                age = 4
        elif age_group == 1:
            age_index = 14
            age_index_economic_activity = 0
            age_index_marriage = 0
            rand_number = np.random.random()
            age = 5
            if rand_number > 0.2:
                age = 6
            if rand_number > 0.4:
                age = 7
            if rand_number > 0.6:
                age = 8
            if rand_number > 0.8:
                age = 9
        elif age_group == 2:
            age_index = 14
            age_index_economic_activity = 0
            age_index_marriage = 0
            rand_number = np.random.random()
            age = 10
            if rand_number > 0.2:
                age = 11
            if rand_number > 0.4:
                age = 12
            if rand_number > 0.6:
                age = 13
            if rand_number > 0.8:
                age = 14
        elif age_group == 3:
            age_index = 17
            age_index_economic_activity = 15
            age_index_marriage = 0
            rand_number = np.random.random()
            age = 15
            if rand_number > 0.33:
                age = 16
                age_index_marriage = 17
            if rand_number > 0.66:
                age = 17
                age_index_marriage = 17
        return age_index, age_index_marriage, age_index_economic_activity, age

    def get_agent_economic_status(self, sex, age, age_index_economic_activity):
        # Economic status
        if (age >= 19) and (age <= 64):  # 15
            rand_num = np.random.random()
            economic_status = 0  # Working
            if sex == 0:
                total = self.age_districts_economic_activities.loc['M{}'.format(age_index_economic_activity),
                                                              'DistrictTotal{}'.format(self.dist_num)]
                cur_level = self.age_districts_economic_activities.loc['M{}'.format(age_index_economic_activity),
                                                                  'District{}EconomicallyActive'.format(
                                                                      self.dist_num)] / total
                if rand_num > cur_level:
                    economic_status = 1  # Not working
                cur_level += self.age_districts_economic_activities.loc[
                                 'M{}'.format(age_index_economic_activity),
                                 'District{}EconomicallyActiveWithoutWork'.format(self.dist_num)] / total
                if rand_num > cur_level:
                    economic_status = 2  # Inactive
            else:
                total = self.age_districts_economic_activities.loc['F{}'.format(age_index_economic_activity),
                                                              'DistrictTotal{}'.format(self.dist_num)]
                cur_level = self.age_districts_economic_activities.loc['F{}'.format(age_index_economic_activity),
                                                                  'District{}EconomicallyActive'.format(
                                                                      self.dist_num)] / total
                if rand_num > cur_level:
                    economic_status = 1  # Not working
                cur_level += self.age_districts_economic_activities.loc[
                                 'F{}'.format(age_index_economic_activity),
                                 'District{}EconomicallyActiveWithoutWork'.format(self.dist_num)] / total
                if rand_num > cur_level:
                    economic_status = 2  # Inactive
        else:
            if age < 19:  # 15
                economic_status = 3  # Child
            elif age > 64:
                economic_status = 4  # Retired
        return economic_status

    def get_agent_marriage_status(self, age, sex, age_index_marriage):
        if age >= 19:  # 16
            marriage_status = 0  # Married
            rand_num = np.random.random()
            if sex == 0:
                total = self.age_districts_marriage.loc[
                            'M{}'.format(age_index_marriage), 'MarriedDistrict{}'.format(self.dist_num)] \
                        + self.age_districts_marriage.loc[
                            'M{}'.format(age_index_marriage), 'NeverMarriedDistrict{}'.format(self.dist_num)] \
                        + self.age_districts_marriage.loc[
                            'M{}'.format(age_index_marriage), 'DivorcedDistrict{}'.format(self.dist_num)] \
                        + self.age_districts_marriage.loc[
                            'M{}'.format(age_index_marriage), 'NotTogetherDistrict{}'.format(self.dist_num)] \
                        + self.age_districts_marriage.loc[
                            'M{}'.format(age_index_marriage), 'WidowedDistrict{}'.format(self.dist_num)]
                cur_level = self.age_districts_marriage.loc[
                                'M{}'.format(age_index_marriage), 'MarriedDistrict{}'.format(self.dist_num)] / total
                if rand_num > cur_level:
                    marriage_status = 1  # Never married
                cur_level += self.age_districts_marriage.loc[
                                 'M{}'.format(age_index_marriage), 'NeverMarriedDistrict{}'.format(self.dist_num)] / total
                if rand_num > cur_level:
                    marriage_status = 2  # Divorced
                cur_level += self.age_districts_marriage.loc[
                                 'M{}'.format(age_index_marriage), 'DivorcedDistrict{}'.format(self.dist_num)] / total
                if rand_num > cur_level:
                    marriage_status = 3  # Not together
                cur_level += self.age_districts_marriage.loc[
                                 'M{}'.format(age_index_marriage), 'NotTogetherDistrict{}'.format(self.dist_num)] / total
                if rand_num > cur_level:
                    marriage_status = 4  # Widowed
            else:
                total = self.age_districts_marriage.loc[
                            'F{}'.format(age_index_marriage), 'MarriedDistrict{}'.format(self.dist_num)] \
                        + self.age_districts_marriage.loc[
                            'F{}'.format(age_index_marriage), 'NeverMarriedDistrict{}'.format(self.dist_num)] \
                        + self.age_districts_marriage.loc[
                            'F{}'.format(age_index_marriage), 'DivorcedDistrict{}'.format(self.dist_num)] \
                        + self.age_districts_marriage.loc[
                            'F{}'.format(age_index_marriage), 'NotTogetherDistrict{}'.format(self.dist_num)] \
                        + self.age_districts_marriage.loc[
                            'F{}'.format(age_index_marriage), 'WidowedDistrict{}'.format(self.dist_num)]
                cur_level = self.age_districts_marriage.loc[
                                'F{}'.format(age_index_marriage), 'MarriedDistrict{}'.format(self.dist_num)] / total
                if rand_num > cur_level:
                    marriage_status = 1  # Never married
                cur_level += self.age_districts_marriage.loc[
                                 'F{}'.format(age_index_marriage), 'NeverMarriedDistrict{}'.format(
                                     self.dist_num)] / total
                if rand_num > cur_level:
                    marriage_status = 2  # Divorced
                cur_level += self.age_districts_marriage.loc[
                                 'F{}'.format(age_index_marriage), 'DivorcedDistrict{}'.format(self.dist_num)] / total
                if rand_num > cur_level:
                    marriage_status = 3  # Not together
                cur_level += self.age_districts_marriage.loc[
                                 'F{}'.format(age_index_marriage), 'NotTogetherDistrict{}'.format(self.dist_num)] / total
                if rand_num > cur_level:
                    marriage_status = 4  # Widowed
        else:
            marriage_status = -1
        return marriage_status

    def generate_household(self, household_id):
        # global agent_counter
        home_index = np.random.randint(0, len(self.home_coords) - 1)

        # while home_index in self.home_indexes:
        #     home_index = np.random.randint(0, len(self.home_coords) - 1)

        # self.closest_metro_stations_to_homes.append(self.closest_metro_stations[home_index])
        # print(economic_status)
        # print(sex, age)
        x = self.home_coords[home_index, 0] + np.random.randint(low=-8, high=8)
        y = self.home_coords[home_index, 1] + np.random.randint(low=-8, high=8)
        household_position = np.array((x, y))
        # [y, x, id] = id
        closest_school = self.closest_schools[home_index]
        closest_kindergarten = self.closest_kindergartens[home_index]
        if self.num_of_agents - agent_counter <= 6:
            num_of_people_in_household = self.num_of_agents - agent_counter
        else:
            num_of_people_in_household = self.get_num_of_people_in_household()
        household_type, num_of_children = self.get_household_type(num_of_people_in_household)
        num_of_people_working = self.get_num_of_people_working_in_household(num_of_people_in_household)
        agent_list = []
        if num_of_people_in_household == 1:
            agent = self.generate_agent(household_id, False)
            self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
            # agent_counter += 1
            agent_list.append(agent)
        # elif num_of_people_in_household == 2:
        #     children_left_to_add = num_of_children
        #     if household_type == 0:
        #         agent = self.generate_agent(household_id, False, 0)
        #         self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
        #         agent_list.append(agent)
        #         male_age = agent.age
        #         agent = self.generate_agent(household_id, False, 1)
        #         self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
        #         agent_list.append(agent)
        #     elif household_type == 1:
        #         agent = self.generate_agent(household_id, False, 1)
        #         self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
        #         agent_list.append(agent)
        else:
            children_left_to_add = num_of_children
            adult_left_to_add = num_of_people_in_household - num_of_children
            parent_age = -1
            if household_type == 0:
                agent = self.generate_agent(household_id, False, 1)
                self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
                agent_list.append(agent)
                parent_age = agent.age
                agent = self.generate_agent(household_id, False, 0, agent.age_group)
                self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
                agent_list.append(agent)
                adult_left_to_add -= 2
            elif household_type == 1:
                agent = self.generate_agent(household_id, False, 1)
                self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
                agent_list.append(agent)
                parent_age = agent.age
                adult_left_to_add -= 1
            elif household_type == 2:
                agent = self.generate_agent(household_id, False, 0)
                self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
                agent_list.append(agent)
                parent_age = agent.age
                adult_left_to_add -= 1
            elif household_type == 6:
                agent = self.generate_agent(household_id, False, 1)
                self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
                agent_list.append(agent)
                agent = self.generate_agent(household_id, False, 0, agent.age_group)
                self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
                agent_list.append(agent)
                adult_left_to_add -= 2
                agent = self.generate_agent(household_id, False, 1)
                self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
                agent_list.append(agent)
                parent_age = agent.age
                agent = self.generate_agent(household_id, False, 0, agent.age_group)
                self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
                agent_list.append(agent)
                adult_left_to_add -= 2
            for i in range(children_left_to_add):
                agent = self.generate_agent(household_id, True, parent_age=parent_age)
                self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
                # agent_counter += 1
                agent_list.append(agent)

            for i in range(adult_left_to_add):
                agent = self.generate_agent(household_id, False, parent_age=parent_age)
                self.change_information_about_agents(agent, closest_kindergarten, closest_school, household_position)
                # agent_counter += 1
                agent_list.append(agent)
        return Household(
            household_id, household_position, closest_school, closest_kindergarten,
            num_of_people_in_household, household_type, num_of_children, num_of_people_working, agent_list)

    def change_information_about_agents(self, agent, closest_kindergarten, closest_school, household_position):
        global agent_counter
        if agent.health_status == 1:
            self.susceptible -= 1
            self.infected += 1
            self.agent_colors[agent_counter, 2] = 0.0
            self.agent_colors[agent_counter, 0] = 1.0
        elif agent.health_status == 2:
            self.susceptible -= 1
            self.recovered += 1
            self.agent_colors[agent_counter, 2] = 0.0
            self.agent_colors[agent_counter, 1] = 1.0
        self.agent_positions[agent.unique_id] = household_position
        if agent.education_status == 1:
            self.kindergarten_list[closest_kindergarten].add_agent_to_the_group(agent)
            # self.kindergarten_list[closest_kindergarten].add_agent(agent)
            # self.kindergarten_list[closest_kindergarten].num_of_agents_by_age[agent.age] += 1
            # if agent.health_status == 1:
            #     self.kindergarten_list[closest_kindergarten].num_of_infected_by_age[agent.age] += 1
        elif agent.education_status == 2:
            self.school_list[closest_school].add_agent_to_the_group(agent)
            # self.school_list[closest_school].add_agent(agent)
            # self.school_list[closest_school].num_of_agents_by_age[agent.age] += 1
            # if agent.health_status == 1:
            #     self.school_list[closest_school].num_of_infected_by_age[agent.age] += 1
        if agent.economic_status == 0:
            self.work_list[0].add_agent_to_the_group(agent)
            # if agent.health_status == 1:
            #     self.change_working_infected_number(agent.economic_status, agent.metro_use, True)
            # if agent.metro_use:
            #     if len(self.work_groups_using_metro[self.metro_group_index].agent_list) >= 20:
            #         self.work_groups_using_metro.append(WorkGroup())
            #         self.metro_group_index += 1
            #     self.work_groups_using_metro[self.metro_group_index].agent_list.append(agent)
            #     if agent.health_status == 1:
            #         self.work_groups_using_metro[self.metro_group_index].num_of_infected += 1
            #     agent.working_group_using_metro_index = self.metro_group_index
            #     # self.num_of_agents_using_metro += 1
            # else:
            #     if len(self.work_groups_not_using_metro[self.non_metro_group_index].agent_list) >= 20:
            #         self.work_groups_not_using_metro.append(WorkGroup())
            #         self.non_metro_group_index += 1
            #     self.work_groups_not_using_metro[self.non_metro_group_index].agent_list.append(agent)
            #     if agent.health_status == 1:
            #         self.work_groups_not_using_metro[self.non_metro_group_index].num_of_infected += 1
            #     agent.working_group_not_using_metro_index = self.non_metro_group_index
            #     # self.num_of_agents_not_using_metro += 1
        agent_counter += 1
        # print(household_position)

    def get_num_of_people_in_household(self):
        num_of_people_in_household = 1
        rand_num = np.random.random()
        total = self.age_sex_districts.loc[current_okato, 'TotalHouseholds']
        cur_level = (self.age_sex_districts.loc[current_okato, '1People'] / total)
        if rand_num > cur_level:
            num_of_people_in_household = 2
        cur_level += (self.age_sex_districts.loc[current_okato, '2People'] / total)
        if rand_num > cur_level:
            num_of_people_in_household = 3
        cur_level += (self.age_sex_districts.loc[current_okato, '3People'] / total)
        if rand_num > cur_level:
            num_of_people_in_household = 4
        cur_level += (self.age_sex_districts.loc[current_okato, '4People'] / total)
        if rand_num > cur_level:
            num_of_people_in_household = 5
        cur_level += (self.age_sex_districts.loc[current_okato, '5People'] / total)
        if rand_num > cur_level:
            num_of_people_in_household = 6
        return num_of_people_in_household

    def get_num_of_people_working_in_household(self, num_of_people_in_household):
        if num_of_people_in_household == 1:
            return 0
        if num_of_people_in_household == 2:
            total = self.economic_activity_districts.loc['2People', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)]
            rand_num = np.random.random()
            num_of_people_working_in_household = 0  # 0 Person Working
            cur_level = self.economic_activity_districts.loc[
                            '2PeopleInactive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 1  # 1 People Working
            cur_level += self.economic_activity_districts.loc[
                            '2People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 2  # 2 People Working
        elif num_of_people_in_household == 3:
            total = self.economic_activity_districts.loc[
                '3People', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)]
            rand_num = np.random.random()
            num_of_people_working_in_household = 0  # 0 Person Working
            cur_level = self.economic_activity_districts.loc[
                            '3PeopleInactive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 1  # 1 People Working
            cur_level += self.economic_activity_districts.loc[
                             '3People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 2  # 2 People Working
            cur_level += self.economic_activity_districts.loc[
                             '3People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 3  # 3 People Working
        elif num_of_people_in_household == 4:
            total = self.economic_activity_districts.loc[
                '4People', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)]
            rand_num = np.random.random()
            num_of_people_working_in_household = 0  # 0 Person Working
            cur_level = self.economic_activity_districts.loc[
                            '4PeopleInactive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 1  # 1 People Working
            cur_level += self.economic_activity_districts.loc[
                             '4People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 2  # 2 People Working
            cur_level += self.economic_activity_districts.loc[
                             '4People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 3  # 3 People Working
            cur_level += self.economic_activity_districts.loc[
                             '4People3PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 4  # 4 People Working
        else:
            total = self.economic_activity_districts.loc[
                '5People', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)]
            rand_num = np.random.random()
            num_of_people_working_in_household = 0  # 0 Person Working
            cur_level = self.economic_activity_districts.loc[
                            '5PeopleInactive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 1  # 1 People Working
            cur_level += self.economic_activity_districts.loc[
                             '5People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 2  # 2 People Working
            cur_level += self.economic_activity_districts.loc[
                             '5People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 3  # 3 People Working
            cur_level += self.economic_activity_districts.loc[
                             '5People3PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 4  # 4 People Working
            cur_level += self.economic_activity_districts.loc[
                             '5People4PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(self.dist_num)] / total
            if rand_num > cur_level:
                num_of_people_working_in_household = 5  # 5 People Working
        return num_of_people_working_in_household

    def get_household_type(self, num_of_people_in_household):
        # print('Num of people', num_of_people_in_household)
        if num_of_people_in_household == 1:
            return -1, 0
        if num_of_people_in_household == 2:
            rand_num = np.random.random()
            total = self.age_sex_districts.loc[current_okato, 'PWOP2P']\
                    + self.age_sex_districts.loc[current_okato, 'SMWC2P']\
                    + self.age_sex_districts.loc[current_okato, 'SFWC2P']\
                    + self.age_sex_districts.loc[current_okato, 'O2P']
            household_type = 0  # Pair
            cur_level = self.age_sex_districts.loc[current_okato, 'PWOP2P'] / total
            if rand_num > cur_level:
                household_type = 1  # Single mother
            cur_level += self.age_sex_districts.loc[current_okato, 'SMWC2P'] / total
            if rand_num > cur_level:
                household_type = 2  # Single father
            cur_level += self.age_sex_districts.loc[current_okato, 'SFWC2P'] / total
            if rand_num > cur_level:
                household_type = 3  # Other

            if household_type == 0:
                num_of_children = 0
            elif household_type == 1:
                num_of_children = 1
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'SMWC2P']
                cur_level = self.age_sex_districts.loc[current_okato, 'SMWC2P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 2:
                num_of_children = 1
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'SFWC2P']
                cur_level = self.age_sex_districts.loc[current_okato, 'SFWC2P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 3:
                num_of_children = 1
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'O2P']
                cur_level = self.age_sex_districts.loc[current_okato, 'O2P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0

        elif num_of_people_in_household == 3:
            rand_num = np.random.random()
            total = self.age_sex_districts.loc[current_okato, 'PWOP3P'] \
                    + self.age_sex_districts.loc[current_okato, 'SMWC3P'] \
                    + self.age_sex_districts.loc[current_okato, 'SFWC3P'] \
                    + self.age_sex_districts.loc[current_okato, 'O3P'] \
                    + self.age_sex_districts.loc[current_okato, 'SPWCWP3P'] \
                    + self.age_sex_districts.loc[current_okato, 'SPWCWPWOP3P']
            household_type = 0  # Pair
            cur_level = self.age_sex_districts.loc[current_okato, 'PWOP3P'] / total
            if rand_num > cur_level:
                household_type = 1  # Single mother
            cur_level += self.age_sex_districts.loc[current_okato, 'SMWC3P'] / total
            if rand_num > cur_level:
                household_type = 2  # Single father
            cur_level += self.age_sex_districts.loc[current_okato, 'SFWC3P'] / total
            if rand_num > cur_level:
                household_type = 3  # Other
            cur_level += self.age_sex_districts.loc[current_okato, 'O3P'] / total
            if rand_num > cur_level:
                household_type = 4  # Single parent with parent
            cur_level += self.age_sex_districts.loc[current_okato, 'SPWCWP3P'] / total
            if rand_num > cur_level:
                household_type = 5  # Single parent with parent with other people

            if household_type == 0:
                num_of_children = 1
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'PWOP3P']
                cur_level = self.age_sex_districts.loc[current_okato, 'SMWC3P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 1:
                num_of_children = 2
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'SMWC3P']
                cur_level = self.age_sex_districts.loc[current_okato, 'SMWC3P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, 'SMWC3P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 2:
                num_of_children = 2
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'SFWC3P']
                cur_level = self.age_sex_districts.loc[current_okato, 'SFWC3P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, 'SFWC3P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 3:
                num_of_children = 2
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'O3P']
                cur_level = self.age_sex_districts.loc[current_okato, 'O3P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, 'O3P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 4:
                num_of_children = 1
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'SPWCWP3P']
                cur_level = self.age_sex_districts.loc[current_okato, 'SPWCWP3P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 5:
                num_of_children = 1
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'SPWCWPWOP3P']
                cur_level = self.age_sex_districts.loc[current_okato, 'SPWCWPWOP3P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0

        elif num_of_people_in_household == 4:
            rand_num = np.random.random()
            total = self.age_sex_districts.loc[current_okato, 'PWOP4P'] \
                    + self.age_sex_districts.loc[current_okato, 'SMWC4P'] \
                    + self.age_sex_districts.loc[current_okato, 'O4P'] \
                    + self.age_sex_districts.loc[current_okato, 'SPWCWP4P'] \
                    + self.age_sex_districts.loc[current_okato, 'SPWCWPWOP4P'] \
                    + self.age_sex_districts.loc[current_okato, '2PWOP4P']
            household_type = 0  # Pair
            cur_level = self.age_sex_districts.loc[current_okato, 'PWOP4P'] / total
            if rand_num > cur_level:
                household_type = 1  # Single mother
            cur_level += self.age_sex_districts.loc[current_okato, 'SMWC4P'] / total
            if rand_num > cur_level:
                household_type = 3  # Other
            cur_level += self.age_sex_districts.loc[current_okato, 'O4P'] / total
            if rand_num > cur_level:
                household_type = 4  # Single parent with parent
            cur_level += self.age_sex_districts.loc[current_okato, 'SPWCWP4P'] / total
            if rand_num > cur_level:
                household_type = 5  # Single parent with parent with other people
            cur_level += self.age_sex_districts.loc[current_okato, 'SPWCWPWOP4P'] / total
            if rand_num > cur_level:
                household_type = 6  # Two pairs

            if household_type == 0:
                num_of_children = 2
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'PWOP4P']
                cur_level = self.age_sex_districts.loc[current_okato, 'PWOP4P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, 'PWOP4P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 1:
                num_of_children = 3
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'SMWC4P']
                cur_level = self.age_sex_districts.loc[current_okato, 'SMWC4P3C'] / total
                if rand_num > cur_level:
                    num_of_children = 2
                cur_level += self.age_sex_districts.loc[current_okato, 'SMWC4P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, 'SMWC4P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 3:
                num_of_children = 2
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'O4P']
                cur_level = self.age_sex_districts.loc[current_okato, 'O4P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, 'O4P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 4:
                num_of_children = 2
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'SPWCWP4P']
                cur_level = self.age_sex_districts.loc[current_okato, 'SPWCWP4P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, 'SPWCWP4P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 5:
                num_of_children = 2
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'SPWCWPWOP4P']
                cur_level = self.age_sex_districts.loc[current_okato, 'SPWCWPWOP4P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, 'SPWCWPWOP4P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 6:
                num_of_children = 0

        elif num_of_people_in_household == 5:
            rand_num = np.random.random()
            total = self.age_sex_districts.loc[current_okato, 'PWOP5P'] \
                    + self.age_sex_districts.loc[current_okato, 'O5P'] \
                    + self.age_sex_districts.loc[current_okato, 'SPWCWPWOP5P'] \
                    + self.age_sex_districts.loc[current_okato, '2PWOP5P']
            household_type = 0  # Pair
            cur_level = self.age_sex_districts.loc[current_okato, 'PWOP5P'] / total
            if rand_num > cur_level:
                household_type = 3  # Other
            cur_level += self.age_sex_districts.loc[current_okato, 'O5P'] / total
            if rand_num > cur_level:
                household_type = 5  # Single parent with parent with other people
            cur_level += self.age_sex_districts.loc[current_okato, 'SPWCWPWOP5P'] / total
            if rand_num > cur_level:
                household_type = 6  # Two pairs

            if household_type == 0:
                num_of_children = 3
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'PWOP5P']
                cur_level = self.age_sex_districts.loc[current_okato, 'PWOP5P3C'] / total
                if rand_num > cur_level:
                    num_of_children = 2
                cur_level += self.age_sex_districts.loc[current_okato, 'PWOP5P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, 'PWOP5P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 3:
                num_of_children = 2
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'O5P']
                cur_level = self.age_sex_districts.loc[current_okato, 'O5P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, 'O5P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 5:
                num_of_children = 2
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'SPWCWPWOP5P']
                cur_level = self.age_sex_districts.loc[current_okato, 'SPWCWPWOP5P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, 'SPWCWPWOP5P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 6:
                num_of_children = 1
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, '2PWOP5P']
                cur_level = self.age_sex_districts.loc[current_okato, '2PWOP5P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
        else:
            rand_num = np.random.random()
            total = self.age_sex_districts.loc[current_okato, 'PWOP6P'] \
                    + self.age_sex_districts.loc[current_okato, '2PWOP6P']
            household_type = 0  # Pair
            cur_level = self.age_sex_districts.loc[current_okato, 'PWOP6P'] / total
            if rand_num > cur_level:
                household_type = 6  # Two pairs

            if household_type == 0:
                num_of_children = 3
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, 'PWOP6P']
                cur_level = self.age_sex_districts.loc[current_okato, 'PWOP6P3C'] / total
                if rand_num > cur_level:
                    num_of_children = 2
                cur_level += self.age_sex_districts.loc[current_okato, 'PWOP6P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, 'PWOP6P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
            elif household_type == 6:
                num_of_children = 2
                rand_num = np.random.random()
                total = self.age_sex_districts.loc[current_okato, '2PWOP6P']
                cur_level = self.age_sex_districts.loc[current_okato, '2PWOP6P2C'] / total
                if rand_num > cur_level:
                    num_of_children = 1
                cur_level += self.age_sex_districts.loc[current_okato, '2PWOP6P1C'] / total
                if rand_num > cur_level:
                    num_of_children = 0
        return household_type, num_of_children

    def make_agent_step(self, agent, household, system_status):

        if system_status == 1:
            if agent.economic_status == 0:
                if agent.metro_use == 1:
                    self.agent_positions[agent.unique_id] = np.array([self.grid_width - 1, self.grid_height - 1])
                else:
                    self.agent_positions[agent.unique_id] = np.array([int(self.grid_width / 2), int(self.grid_height / 2)])
            elif agent.education_status == 1:
                self.agent_positions[agent.unique_id] = self.kindergarten_list[household.closest_kindergarten].position
            elif agent.education_status == 2:
                self.agent_positions[agent.unique_id] = self.school_list[household.closest_school].position

        if system_status == 2:
            self.agent_positions[agent.unique_id] = household.position

    def step(self, i):
        global household_number_of_hours
        # print(self.week_of_the_month)
        # week_flu_coefficient = self.mean_flu[self.week_of_the_month - 1]
        # print(week_flu_coefficient)
        self.hour += 24
        if (self.hour == 24) and (self.hour != 0):
            self.day_of_the_week += 1
            self.hour = 0
            self.day += 1
            for household in self.household_list:
                for agent in household.agent_list:
                    if agent.health_status == 3:
                        agent.health_status = 4
                    if agent.health_status == 0:
                        if self.weekday:
                            if (agent.education_status == 1) and (not (self.month in {7, 8})):
                                for kindergarten_agent in self.kindergarten_list[household.closest_kindergarten].groups_by_age[agent.age][agent.kindergarten_group_index]:
                                    if (kindergarten_agent.health_status != 1) or (kindergarten_agent.isStayingHome):
                                        continue
                                    if np.random.random() < 0.28:
                                        agent.health_status = 3
                                        break
                            elif (agent.education_status == 2) and (not (self.month in {6, 7, 8})):
                                for school_agent in self.school_list[household.closest_school].groups_by_age[agent.age][agent.school_group_index]:
                                    if (school_agent.health_status != 1) or (school_agent.isStayingHome):
                                        continue
                                    if np.random.random() < 0.03:
                                        agent.health_status = 3
                                        break
                            elif agent.economic_status == 0:
                                for work_agent in self.work_list[0].groups[agent.working_group_using_metro_index]:
                                    if (work_agent.health_status != 1) or (work_agent.isStayingHome):
                                        continue
                                    if np.random.random() < 0.05:
                                        agent.health_status = 3
                                        break
                            if agent.health_status != 3:
                                for home_agent in household.agent_list:
                                    if home_agent.health_status != 1:
                                        continue
                                    if agent.age < 19:
                                        if home_agent.age < 19:
                                            if np.random.random() < 0.8:
                                                agent.health_status = 3
                                                break
                                            if self.month in {6, 7, 8}:
                                                if np.random.random() < 0.8:
                                                    agent.health_status = 3
                                                    break
                                        else:
                                            if np.random.random() < 0.25:
                                                agent.health_status = 3
                                                break
                                    else:
                                        if home_agent.age < 19:
                                            if np.random.random() < 0.35:
                                                agent.health_status = 3
                                                break
                                        else:
                                            if np.random.random() < 0.4:
                                                agent.health_status = 3
                                                break
                        else:
                            for home_agent in household.agent_list:
                                if home_agent.health_status != 1:
                                    continue
                                if agent.age < 19:
                                    if home_agent.age < 19:
                                        if np.random.random() < 0.8:
                                            agent.health_status = 3
                                            break
                                        if np.random.random() < 0.8:
                                            agent.health_status = 3
                                            break
                                    else:
                                        if np.random.random() < 0.25:
                                            agent.health_status = 3
                                            break
                                        if np.random.random() < 0.25:
                                            agent.health_status = 3
                                            break
                                else:
                                    if home_agent.age < 19:
                                        if np.random.random() < 0.35:
                                            agent.health_status = 3
                                            break
                                        if np.random.random() < 0.35:
                                            agent.health_status = 3
                                            break
                                    else:
                                        if np.random.random() < 0.4:
                                            agent.health_status = 3
                                            break
                                        if np.random.random() < 0.4:
                                            agent.health_status = 3
                                            break
                        if agent.health_status != 3:
                            if self.month in {12, 1, 2}:
                                if np.random.random() < 0.001:
                                    agent.health_status = 3
                            # elif self.month in {3, 11}:
                            #     if np.random.random() < 0.00075:
                            #         agent.health_status = 3
                            # elif self.month in {2, 10}:
                            #     if np.random.random() < 0.0006:
                            #         agent.health_status = 3
                            else:
                                if np.random.random() < 0.0005:
                                    agent.health_status = 3
                        if agent.health_status == 3:
                            self.new_cases += 1
            for household in self.household_list:
                # household_infected = household.num_of_infected
                for agent in household.agent_list:
                    if agent.health_status == 1:
                        # if agent.number_of_days_infected == 0:
                        #     if agent.age < 8:
                        #         if np.random.random() < 0.304:
                        #             agent.isStayingHome = True
                        #     elif agent.age < 19:
                        #         if np.random.random() < 0.203:
                        #             agent.isStayingHome = True
                        #     else:
                        #         if np.random.random() < 0.1:
                        #             agent.isStayingHome = True
                        if agent.number_of_days_infected == 1:
                            if agent.age < 8:
                                if np.random.random() < 0.575:
                                    agent.isStayingHome = True
                            elif agent.age < 19:
                                if np.random.random() < 0.498:
                                    agent.isStayingHome = True
                            else:
                                if np.random.random() < 0.333:
                                    agent.isStayingHome = True
                        elif agent.number_of_days_infected == 2:
                            if agent.age < 8:
                                if np.random.random() < 0.324:
                                    agent.isStayingHome = True
                            elif agent.age < 19:
                                if np.random.random() < 0.375:
                                    agent.isStayingHome = True
                            else:
                                if np.random.random() < 0.167:
                                    agent.isStayingHome = True
                        if agent.number_of_days_infected == 6:
                            agent.isStayingHome = False
                            agent.health_status = 2
                            agent.number_of_days_infected = -1
                            agent.number_of_days_recovered = 0
                            self.recovered += 1
                            self.infected -= 1
                            self.agent_colors[agent.unique_id] = [0, 1, 0]
                        else:
                            agent.number_of_days_infected += 1
                    elif agent.health_status == 2:
                        if agent.number_of_days_recovered >= 30:
                            if np.random.random() < 0.0025:
                                agent.health_status = 0
                                agent.number_of_days_recovered = -1
                                self.recovered -= 1
                                self.susceptible += 1
                                self.agent_colors[agent.unique_id] = [0, 0, 1]
                        # elif agent.number_of_days_recovered >= 61:
                        #     if np.random.random() < 0.08:
                        #         agent.health_status = 0
                        #         agent.number_of_days_recovered = -1
                        #         self.recovered -= 1
                        #         self.susceptible += 1
                        #         self.agent_colors[agent.unique_id] = [0, 0, 1]
                        else:
                            agent.number_of_days_recovered += 1
                    elif agent.health_status == 4:
                        agent.health_status = 1
                        agent.number_of_days_infected = 0
                        self.infected += 1
                        self.susceptible -= 1
                        self.agent_colors[agent.unique_id] = [1, 0, 0]
                        if agent.age < 8:
                            if np.random.random() < 0.304:
                                agent.isStayingHome = True
                        elif agent.age < 19:
                            if np.random.random() < 0.203:
                                agent.isStayingHome = True
                        else:
                            if np.random.random() < 0.1:
                                agent.isStayingHome = True
            self.day_of_the_year += 1
        if self.day_of_the_year == 365:
            self.day_of_the_year = 0
        if (self.month in {1, 3, 5, 7, 8, 10, 12}) and (self.day == 31):
            self.day = 1
            self.month += 1
            if self.month != 13:
                print('Month', self.month)
        elif (self.month in {4, 6, 9, 11}) and (self.day == 30):
            self.day = 1
            self.month += 1
            print('Month', self.month)
        elif (self.month == 2) and (self.day == 28):  # Without leap years
            self.day = 1
            self.month += 1
            print('Month', self.month)
        if self.month == 13:
            self.month = 1
            self.year += 1
            print('Month', self.month)
            # self.week_of_the_month = 1
        if len(self.new_cases_by_ticks) == 52:
            plt.figure()
            plt.plot(range(1, len(self.new_cases_by_ticks) + 1), self.new_cases_by_ticks)
            plt.xlabel('Неделя')
            plt.title('Промоделированная заболеваемость в Коньково')
            plt.ylabel('Случаев')
            plt.show()
            error_sum = 0
            print(len(self.mean_flu))
            pd.DataFrame(np.array(self.new_cases_by_ticks)).to_csv(r'D:\Downloads\Coursework\foo.csv')
            for i in range(52):
                error_sum += ((self.new_cases_by_ticks[i] - self.mean_flu[i]) / self.mean_flu[i])**2\
                             + ((self.new_cases_by_ticks[i] - self.mean_flu[i]) / self.new_cases_by_ticks[i])**2
                # error_sum += (self.new_cases_by_ticks[i] - self.mean_flu[i]) ** 2
            print('Error', error_sum)
            self.new_cases_by_ticks = []
        if (self.day_of_the_week == 6) or (self.day_of_the_week == 7):
            self.weekday = False
            household_number_of_hours = 12
        elif self.day_of_the_week == 8:
            self.day_of_the_week = 1
            self.week_of_the_month += 1
            self.weekday = True
            self.new_cases_by_ticks.append(self.new_cases)
            self.new_cases = 0
            household_number_of_hours = 6
        if self.week_of_the_month == 53:
            self.week_of_the_month = 1

        self.susceptible_by_ticks.append(self.susceptible)
        self.recovered_by_ticks.append(self.recovered)
        self.infected_by_ticks.append(self.infected)


class MyCanvas(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100, x_lim=500, y_lim=500):
        fig = Figure(figsize=(width, height), dpi=dpi)

        self.ax = fig.add_subplot(111)
        self.ax.set_xlim(0, x_lim)
        self.ax.set_ylim(0, y_lim)
        self.ax.tick_params(
            axis='both', which='both', bottom=False, left=False, labelleft=False, labelbottom=False)

        super().__init__(fig)


class GraphCanvas(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100, y_max=1000):
        fig = Figure(figsize=(width, height), dpi=dpi)

        self.ax = fig.add_subplot(111)
        self.ax.set_ylim(0, y_max)
        self.ax.tick_params(
            axis='x', which='both', bottom=False, labelbottom=False)

        super().__init__(fig)


class Slider(QtWidgets.QSlider):
    def mousePressEvent(self, event):
        super(Slider, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            val = self.pixelPosToRangeValue(event.pos())
            self.setValue(val)

    def pixelPosToRangeValue(self, pos):
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = self.style().subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderGroove, self)
        sr = self.style().subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self)

        if self.orientation() == QtCore.Qt.Horizontal:
            slider_length = sr.width()
            slider_min = gr.x()
            slider_max = gr.right() - slider_length + 1
        else:
            slider_length = sr.height()
            slider_min = gr.y()
            slider_max = gr.bottom() - slider_length + 1
        pr = pos - sr.center() + sr.topLeft()
        p = pr.x() if self.orientation() == QtCore.Qt.Horizontal else pr.y()
        return QtWidgets.QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), p - slider_min,
                                                        slider_max - slider_min, opt.upsideDown)


class ApplicationWindow(QMainWindow):

    # current_okato = 45293566000

    def __init__(self, num_of_agents, size_of_agents_on_canvas, grid_height, grid_width):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Disease Outbreak")
        self.setStyleSheet("background-color: white;")
        self.setWindowIcon(QtGui.QIcon("virus.png"))
        self.setGeometry(400, 150, 1200, 800)

        main_widget = QWidget()
        header_box = QHBoxLayout()
        interval_slider_box = QVBoxLayout()
        main_box = QVBoxLayout(main_widget)
        box_live_plot = QHBoxLayout()
        labels_box = QVBoxLayout()
        graph_box = QVBoxLayout()
        buttons_box = QHBoxLayout()

        self.ticks_label = QLabel("Number of ticks: 0")
        self.ticks_label.setStyleSheet("font-size: 20px;")

        self.slider_interval_label = QLabel("Interval between ticks: 1")

        self.interval_slider = Slider(QtCore.Qt.Horizontal)
        self.interval_slider.setMinimum(1)
        self.interval_slider.setMaximum(100)
        self.interval_slider.setValue(1)
        self.interval_slider.setSingleStep(1)
        self.interval_slider.setTickPosition(QSlider.TicksBelow)
        self.interval_slider.setTickInterval(5)
        self.interval_slider.setFixedWidth(300)
        self.interval_slider.valueChanged.connect(self.change_animation_interval)

        interval_slider_box.addWidget(self.slider_interval_label)
        interval_slider_box.addWidget(self.interval_slider)

        self.susceptible_label = QLabel("Number of susceptible: 0")
        self.susceptible_label.setStyleSheet("font-size: 20px; color:blue;")
        self.recovered_label = QLabel("Number of recovered: 0")
        self.recovered_label.setStyleSheet("font-size: 20px; color: green;")
        self.infected_label = QLabel("Number of infected: 0")
        self.infected_label.setStyleSheet("font-size: 20px; color: red;")

        cb = QComboBox()
        cb.setStyleSheet("selection-background-color: rgb(150,150,150)")
        cb.setFixedWidth(300)
        cb.addItems(["Konkovo", "Veshnyaki", "Vostochnoye Izmaylovo"])
        cb.currentIndexChanged.connect(self.selection_change)

        header_box.addWidget(cb)
        header_box.addLayout(interval_slider_box)

        self.canvas = MyCanvas(width=10, height=10, dpi=100, x_lim=grid_width, y_lim=grid_height)
        self.graph_canvas = GraphCanvas(width=5, height=5, dpi=100, y_max=num_of_agents)
        self.graph_canvas.setFixedSize(400, 400)
        labels_box.addWidget(self.ticks_label)
        labels_box.addWidget(self.susceptible_label)
        labels_box.addWidget(self.recovered_label)
        labels_box.addWidget(self.infected_label)
        labels_box.setContentsMargins(50, 0, 0, 100)

        graph_box.addWidget(self.graph_canvas)
        graph_box.addLayout(labels_box)
        graph_box.setContentsMargins(0, 35, 0, 0)  # layout.setContentsMargins(left, top, right, bottom)
        box_live_plot.addLayout(graph_box)
        box_live_plot.addWidget(self.canvas)

        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet("QPushButton {border: 1px solid black;\n border-radius: 4px;\n"
                                        + "background-color:#eee;}"
                                          "QPushButton:pressed {border: 2px inset black;\n border-radius: 4px;\n"
                                        + "background-color:#bbb;}"
                                        )
        self.start_button.setFixedWidth(100)
        self.start_button.setFixedHeight(40)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setFixedWidth(100)
        self.reset_button.setFixedHeight(40)
        self.reset_button.setStyleSheet("QPushButton {border: 1px solid black;\n border-radius: 4px;\n"
                                       + "background-color:#eee;}"
                                         "QPushButton:pressed {border: 2px inset black;\n border-radius: 4px;\n"
                                       + "background-color:#bbb;}"
                                       )

        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedWidth(100)
        self.exit_button.setFixedHeight(40)
        self.exit_button.setStyleSheet("QPushButton {border: 1px solid black;\n border-radius: 4px;\n"
                                       + "background-color:#eee;}"
                                         "QPushButton:pressed {border: 2px inset black;\n border-radius: 4px;\n"
                                       + "background-color:#bbb;}"
                                       )

        self.start_button.clicked.connect(self.on_start)
        self.reset_button.clicked.connect(self.on_reset)
        self.exit_button.clicked.connect(self.on_exit)

        buttons_box.addWidget(self.start_button)
        buttons_box.addWidget(self.reset_button)
        buttons_box.addWidget(self.exit_button)

        main_box.addLayout(header_box)
        main_box.addLayout(box_live_plot)
        main_box.addLayout(buttons_box)

        main_widget.setFocus()
        self.setCentralWidget(main_widget)

        self.model = Model(num_of_agents, grid_height, grid_width)

        rgb = np.random.random((10, 3))
        self.scat = self.canvas.ax.scatter(
            np.array([]), np.array([]), s=size_of_agents_on_canvas, lw=0.5, facecolors=rgb)

        self.line, = self.graph_canvas.ax.plot([0], [0], c='b')
        self.line2, = self.graph_canvas.ax.plot([0], [0], c='r')
        self.line3, = self.graph_canvas.ax.plot([0], [0], c='g')

        data_x = []
        data_y = []

        # print(GpsCoordinates.municipalities[current_okato])
        if current_okato == 45268562000:
            for parts in GpsCoordinates.municipalities[current_okato]:
                for coord in parts:
                    c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                                 GpsCoordinates.bottom_right_gps_coord,
                                                 grid_width, grid_height)
                    data_x.append(c[0])
                    data_y.append(c[1])
                self.canvas.ax.plot(data_x, data_y, c='k', linewidth=2)
                data_x = []
                data_y = []
        else:
            for coord in GpsCoordinates.municipalities[current_okato]:
                c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                             GpsCoordinates.bottom_right_gps_coord,
                                             grid_width, grid_height)
                data_x.append(c[0])
                data_y.append(c[1])
            self.canvas.ax.plot(data_x, data_y, c='k', linewidth=2)

        # for coord in mun:
        #     c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
        #                                  GpsCoordinates.bottom_right_gps_coord,
        #                                  grid_width, grid_height)
        #     data_x.append(c[0])
        #     data_y.append(c[1])
        # self.canvas.ax.plot(data_x, data_y, c='k', linewidth=2)
        # data_x = []
        # data_y = []

        # for okato, mun in GpsCoordinates.municipalities.items():
        #     if okato == 45268562000:
        #         for parts in mun:
        #             for coord in parts:
        #                 c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
        #                                              GpsCoordinates.bottom_right_gps_coord,
        #                                              grid_width, grid_height)
        #                 data_x.append(c[0])
        #                 data_y.append(c[1])
        #             self.canvas.ax.plot(data_x, data_y, c='k', linewidth=2)
        #             data_x = []
        #             data_y = []
        #     else:
        #         for coord in mun:
        #             c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
        #                                          GpsCoordinates.bottom_right_gps_coord,
        #                                          grid_width, grid_height)
        #             data_x.append(c[0])
        #             data_y.append(c[1])
        #         self.canvas.ax.plot(data_x, data_y, c='k', linewidth=2)
        #         data_x = []
        #         data_y = []

        # for okato, mun in GpsCoordinates.municipalities.items():
        #     if okato == 45268562000:
        #         for parts in mun:
        #             for coord in parts:
        #                 c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
        #                                              GpsCoordinates.bottom_right_gps_coord,
        #                                              grid_width, grid_height)
        #                 data_x.append(c[0])
        #                 data_y.append(c[1])
        #             self.canvas.ax.plot(data_x, data_y, c='k', linewidth=2)
        #             data_x = []
        #             data_y = []
        #     else:
        #         for coord in mun:
        #             c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
        #                                          GpsCoordinates.bottom_right_gps_coord,
        #                                          grid_width, grid_height)
        #             data_x.append(c[0])
        #             data_y.append(c[1])
        #         self.canvas.ax.plot(data_x, data_y, c='k', linewidth=2)
        #         data_x = []
        #         data_y = []

        # Metro scatter
        data_x = []
        data_y = []
        for coord in GpsCoordinates.get_metro_coordinates():
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         grid_width, grid_height)
            data_x.append(c[0])
            data_y.append(c[1])
        self.canvas.ax.scatter(
            data_x, data_y, s=20, lw=0.5, c="k", marker="X")

        # Kindergarten scatter pink
        data_x = []
        data_y = []
        for coord in GpsCoordinates.get_kindergartens():
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         grid_width, grid_height)
            data_x.append(c[0])
            data_y.append(c[1])
        self.canvas.ax.scatter(
            data_x, data_y, s=20, lw=0.5, c="k", marker="D")

        # School scatter green
        data_x = []
        data_y = []
        for coord in GpsCoordinates.get_schools():
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         grid_width, grid_height)
            data_x.append(c[0])
            data_y.append(c[1])
        self.canvas.ax.scatter(
            data_x, data_y, s=20, lw=0.5, c="k", marker="s")

        self.running = -1

    def selection_change(self, i):
        return
        # print
        # "Items in the list are :"
        #
        # for count in range(self.cb.count()):
        #     print
        #     self.cb.itemText(count)
        # print
        # "Current index", i, "selection changed ", self.cb.currentText()

    def update_agent_animation(self, i):
        # if i == 61:
        #     self.on_start()
        self.model.step(i + 1)
        self.scat.set_offsets(self.model.agent_positions)
        self.scat.set_color(self.model.agent_colors)
        self.ticks_label.setText("Number of ticks: {0}".format(str(i + 1)))
        return self.scat,

    def update_graph_animation(self, i):
        self.line.set_data(range(len(self.model.susceptible_by_ticks)), self.model.susceptible_by_ticks)
        self.line2.set_data(range(len(self.model.infected_by_ticks)), self.model.infected_by_ticks)
        self.line3.set_data(range(len(self.model.recovered_by_ticks)), self.model.recovered_by_ticks)
        self.graph_canvas.ax.relim()
        self.graph_canvas.ax.autoscale_view()
        self.susceptible_label.setText("Number of susceptible: {0}".format(str(self.model.susceptible)))
        self.recovered_label.setText("Number of recovered: {0}".format(str(self.model.recovered)))
        self.infected_label.setText("Number of infected: {0}".format(str(self.model.infected)))
        return self.line, self.line2, self.line3,

    def change_animation_interval(self):
        if self.running != -1:
            self.agent_animation.event_source.interval = self.interval_slider.value()
            self.graph_animation.event_source.interval = self.interval_slider.value()
        self.slider_interval_label.setText("Interval between ticks: {0}".format(str(self.interval_slider.value())))

    def on_start(self):
        if self.running == 1:
            self.agent_animation.event_source.stop()
            self.graph_animation.event_source.stop()
            self.start_button.setText('Continue')
            self.running = 0
        elif self.running == 0:
            self.agent_animation.event_source.start()
            self.graph_animation.event_source.start()
            self.start_button.setText('Stop')
            self.running = 1
        else:
            self.agent_animation = FuncAnimation(self.canvas.figure, self.update_agent_animation,
                                                 blit=True, interval=self.interval_slider.value())
            self.graph_animation = FuncAnimation(self.graph_canvas.figure, self.update_graph_animation,
                                                 blit=True, interval=self.interval_slider.value())

            self.running = 1
            self.start_button.setText('Stop')

    def on_reset(self):
        if self.running != -1:
            self.agent_animation._stop()
            self.graph_animation._stop()
            self.start_button.setText('Start')
            self.model = Model(
                self.model.num_of_agents, self.model.grid_height, self.model.grid_width, self.model.neighbor_distance)
            self.running = -1

    def on_exit(self):
        self.close()


if __name__ == "__main__":
    GpsCoordinates.find_boundary_coords(current_okato)
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    window = ApplicationWindow(14000, 8, 500, 500)
    window.show()
    app.exec()
