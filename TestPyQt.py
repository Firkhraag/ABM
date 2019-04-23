import sys
import numpy as np
import pandas as pd

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QHBoxLayout, QSizePolicy, QMessageBox, \
    QWidget, QPushButton, QLabel, QSlider

import GpsCoordinates

matplotlib.use('Qt5Agg')


class DiseaseAgent:

    def __init__(self, unique_id, sex, age, health_status, economic_status,  education_status):
        # Id
        self.unique_id = unique_id
        # Sex: 0 - male, 1 - female
        self.sex = sex
        # Age
        self.age = age
        # Status: 0 - susceptible, 1 - infected, exposed to be added
        self.health_status = health_status
        # Status: 0 - working, 1 - without work, 2 - inactive
        self.economic_status = economic_status
        # Education: to be added
        self.education_status = education_status


class Model:
    def __init__(self, num_of_agents, num_rows, num_cols, neighbor_distance):
        # Number of agents in population
        self.num_of_agents = num_of_agents

        # Grid width and height
        self.grid_width = num_cols
        self.grid_height = num_rows

        # Speed with which agents travel
        self.speed = 0.1

        # Current date and time
        self.hour = 0
        self.day = 1
        self.month = 1
        self.year = 1

        # Keep track of days
        self.global_days = 1

        # Number of susceptible, exposed, infected people right now
        self.infected = 0
        self.exposed = 0
        self.susceptible = num_of_agents

        # Status of the system: 0 - agents should be at home, 1 - agents should be at work
        self.system_status = 0

        # Unnecessary
        self.neighbor_distance = neighbor_distance

        # Agents list
        self.agent_list = []
        # Current agent positions
        self.agent_positions = np.zeros([num_of_agents, 2], dtype='int64')
        # Positions where agents work
        self.work_positions = np.zeros([num_of_agents, 2], dtype='int64')
        self.work_indexes = np.zeros(num_of_agents, dtype='int64')
        # Homes
        self.home_indexes = np.zeros(num_of_agents, dtype='int64')
        # Colors of agents
        self.agent_colors = np.zeros([self.num_of_agents, 3])
        self.agent_colors[:, 2] = 1.0
        # Grid
        self.grid = np.full((num_rows, num_cols, num_of_agents), -1)

        home_gps_coords = GpsCoordinates.get_home_coordinates()
        self.home_coords = []
        for coord in home_gps_coords:
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            self.home_coords.append(c)
        self.home_coords = np.array(self.home_coords)

        self.metro_coords = []
        for coord in GpsCoordinates.get_metro_coordinates():
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            self.metro_coords.append(c)
        self.metro_coords = np.array(self.metro_coords)

        self.closest_metro_stations = GpsCoordinates.get_closest_metro_stations_to_homes()
        self.closest_metro_stations_to_kindergartens = GpsCoordinates.get_closest_metro_stations_to_kindergartens()
        self.closest_metro_stations_to_schools = GpsCoordinates.get_closest_metro_stations_to_schools()
        self.closest_metro_stations_to_universities = GpsCoordinates.get_closest_metro_stations_to_universities()
        self.metro_ways = GpsCoordinates.get_ways_for_metro_stations()

        # -----------Age, sex, households, districts-------------
        dist_df = pd.read_excel('C:\\Users\\sigla\\Desktop\\MasterWork\\Population.xls')
        districts = dist_df['OKATO'].astype('int64')
        home_okato = pd.read_csv(r'C:\Users\sigla\Desktop\MasterWork\HomeOkato.csv', header=None, index_col=0)
        home_okato.index = pd.RangeIndex(len(home_okato))
        age_sex_districts = pd.read_csv(r'C:\Users\sigla\Desktop\MasterWork\AgeSexDistricts.csv', index_col='OKATO')
        age_districts_number_of_people = pd.read_csv(
            r'C:\Users\sigla\Desktop\MasterWork\AgeDistrictsNumberOfPeople.csv', index_col='Age')
        age_districts_economic_activities = pd.read_csv(
            r'C:\Users\sigla\Desktop\MasterWork\AgeDistrictsEconomicActivities.csv', index_col='Age')
        children_attendance = pd.read_csv(
            r'C:\Users\sigla\Desktop\MasterWork\ChildrenAttendance.csv', index_col=0)
        econimic_activity_districts = pd.read_csv(
            r'C:\Users\sigla\Desktop\MasterWork\EconimicActivityDistricts.csv', index_col=0)
        # --------------------------------------------------------

        # -----------Park zone-------------
        park_gps_coords = GpsCoordinates.read_osm(r'C:\Users\sigla\Desktop\MasterWork\osm\494.osm')
        self.park_coords = []
        for coord in park_gps_coords:
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            self.park_coords.append(c)
        self.park_coords = np.array(self.park_coords)
        # ---------------------------------

        # -----------Сinema zone-------------
        cinema_gps_coords = GpsCoordinates.read_osm(r'C:\Users\sigla\Desktop\MasterWork\osm\495.osm')
        self.cinema_coords = []
        for coord in cinema_gps_coords:
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            self.cinema_coords.append(c)
        self.cinema_coords = np.array(self.cinema_coords)
        # ---------------------------------

        # -----------Theatre zone-------------
        theatre_gps_coords = GpsCoordinates.read_osm(r'C:\Users\sigla\Desktop\MasterWork\osm\531.osm')
        self.theatre_coords = []
        for coord in theatre_gps_coords:
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            self.theatre_coords.append(c)
        self.theatre_coords = np.array(self.theatre_coords)
        # ---------------------------------

        # -----------Kindergarten zone-------------
        kindergarten_gps_coords = GpsCoordinates.get_kindergartens()
        self.kindergarten_coords = []
        for coord in kindergarten_gps_coords:
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            self.kindergarten_coords.append(c)
        self.kindergarten_coords = np.array(self.kindergarten_coords)
        # ---------------------------------

        # -----------Kindergarten2 zone-------------
        kindergarten2_gps_coords = GpsCoordinates.read_osm(r'C:\Users\sigla\Desktop\MasterWork\osm\540.osm')
        self.kindergarten2_coords = []
        for coord in kindergarten2_gps_coords:
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            self.kindergarten2_coords.append(c)
        self.kindergarten2_coords = np.array(self.kindergarten2_coords)
        # ---------------------------------

        # -----------School zone-------------
        school_gps_coords = GpsCoordinates.get_schools()
        self.school_coords = []
        for coord in school_gps_coords:
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            self.school_coords.append(c)
        self.school_coords = np.array(self.school_coords)
        # ---------------------------------

        # -----------School2 zone-------------
        school2_gps_coords = GpsCoordinates.read_osm(r'C:\Users\sigla\Desktop\MasterWork\osm\567.osm')
        self.school2_coords = []
        for coord in school2_gps_coords:
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            self.school2_coords.append(c)
        self.school2_coords = np.array(self.school2_coords)
        # ---------------------------------

        # -----------University zone-------------
        university_gps_coords = GpsCoordinates.get_universities()
        self.university_coords = []
        for coord in university_gps_coords:
            c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                         GpsCoordinates.bottom_right_gps_coord,
                                         num_cols, num_rows)
            self.university_coords.append(c)
        self.university_coords = np.array(self.university_coords)
        # ---------------------------------

        self.ways_to_work = []
        self.ways_to_home = []
        # self.closest_metro_stations_to_homes = []
        self.closest_metro_stations_to_works = []
        self.curr_positions_in_metro = []

        num_of_people_to_add_to_household = 0
        for i in range(num_of_agents):
            if num_of_people_to_add_to_household == 0:
                home_index = np.random.randint(0, len(self.home_coords) - 1)
                while home_index in self.home_indexes:
                    home_index = np.random.randint(0, len(self.home_coords) - 1)
                # self.closest_metro_stations_to_homes.append(self.closest_metro_stations[home_index])
                self.curr_positions_in_metro.append(-1)
                self.home_indexes[i] = home_index
            else:
                self.curr_positions_in_metro.append(-1)
                self.home_indexes[i] = self.home_indexes[i - 1]
            # x = self.home_coords[home_index, 0]
            # y = self.home_coords[home_index, 1]
            # pos = np.array((x, y))
            health_status = 0
            if np.random.random() < 0.1:
                health_status = 2
                self.susceptible -= 1
                self.infected += 1
                self.agent_colors[i, 2] = 0.0
                self.agent_colors[i, 0] = 1.0
            elif np.random.random() < 0.1:
                health_status = 1
                self.susceptible -= 1
                self.exposed += 1
                self.agent_colors[i, 2] = 0.0
                self.agent_colors[i, 1] = 1.0

            sex = 0
            age_group = 0
            if (np.random.random() > (age_sex_districts.loc[home_okato.loc[home_index], 'Mtotal'].values[0]
                                      / age_sex_districts.loc[home_okato.loc[home_index], 'Total'].values[0])):
                sex = 1
            age_rand_number = np.random.random()
            age_sex_district = age_sex_districts.loc[home_okato.loc[home_index].values[0], :]
            if sex == 0:
                cur_level = age_sex_district['M0-4'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 1
                cur_level += age_sex_district['M5-9'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 2
                cur_level += age_sex_district['M10-14'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 3
                cur_level += age_sex_district['M15-19'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 4
                cur_level += age_sex_district['M20-24'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 5
                cur_level += age_sex_district['M25-29'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 6
                cur_level += age_sex_district['M30-34'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 7
                cur_level += age_sex_district['M35-39'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 8
                cur_level += age_sex_district['M40-44'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 9
                cur_level += age_sex_district['M45-49'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 10
                cur_level += age_sex_district['M50-54'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 11
                cur_level += age_sex_district['M55-59'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 12
                cur_level += age_sex_district['M60-64'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 13
                cur_level += age_sex_district['M65-69'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 14
                cur_level += age_sex_district['M70-74'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 15
                cur_level += age_sex_district['M75-79'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 16
                cur_level += age_sex_district['M80-84'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 17
                cur_level += age_sex_district['M85-89'] / age_sex_district['Mtotal2']
                if age_rand_number > cur_level:
                    age_group = 18
            else:
                cur_level = age_sex_district['F0-4'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 1
                cur_level += age_sex_district['F5-9'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 2
                cur_level += age_sex_district['F10-14'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 3
                cur_level += age_sex_district['F15-19'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 4
                cur_level += age_sex_district['F20-24'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 5
                cur_level += age_sex_district['F25-29'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 6
                cur_level += age_sex_district['F30-34'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 7
                cur_level += age_sex_district['F35-39'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 8
                cur_level += age_sex_district['F40-44'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 9
                cur_level += age_sex_district['F45-49'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 10
                cur_level += age_sex_district['F50-54'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 11
                cur_level += age_sex_district['F55-59'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 12
                cur_level += age_sex_district['F60-64'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 13
                cur_level += age_sex_district['F65-69'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 14
                cur_level += age_sex_district['F70-74'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 15
                cur_level += age_sex_district['F75-79'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 16
                cur_level += age_sex_district['F80-84'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 17
                cur_level += age_sex_district['F85-89'] / age_sex_district['Ftotal2']
                if age_rand_number > cur_level:
                    age_group = 18

            # print(age_group)
            if age_group == 0:
                age_rand_number = np.random.random()
                age = 0
                if age_rand_number > 0.2:
                    age = 1
                if age_rand_number > 0.4:
                    age = 2
                if age_rand_number > 0.6:
                    age = 3
                if age_rand_number > 0.8:
                    age = 4
            elif age_group == 1:
                age_rand_number = np.random.random()
                age = 5
                if age_rand_number > 0.2:
                    age = 6
                if age_rand_number > 0.4:
                    age = 7
                if age_rand_number > 0.6:
                    age = 8
                if age_rand_number > 0.8:
                    age = 9
            elif age_group == 2:
                age_rand_number = np.random.random()
                age = 10
                if age_rand_number > 0.2:
                    age = 11
                if age_rand_number > 0.4:
                    age = 12
                if age_rand_number > 0.6:
                    age = 13
                if age_rand_number > 0.8:
                    age = 14
            elif age_group == 3:
                age_rand_number = np.random.random()
                age = 15
                if age_rand_number > 0.2:
                    age = 16
                if age_rand_number > 0.4:
                    age = 17
                if age_rand_number > 0.6:
                    age = 18
                if age_rand_number > 0.8:
                    age = 19
            elif age_group == 4:
                age_rand_number = np.random.random()
                age = 20
                if age_rand_number > 0.2:
                    age = 21
                if age_rand_number > 0.4:
                    age = 22
                if age_rand_number > 0.6:
                    age = 23
                if age_rand_number > 0.8:
                    age = 24
            elif age_group == 5:
                age_rand_number = np.random.random()
                age = 25
                if age_rand_number > 0.2:
                    age = 26
                if age_rand_number > 0.4:
                    age = 27
                if age_rand_number > 0.6:
                    age = 28
                if age_rand_number > 0.8:
                    age = 29
            elif age_group == 6:
                age_rand_number = np.random.random()
                age = 30
                if age_rand_number > 0.2:
                    age = 31
                if age_rand_number > 0.4:
                    age = 32
                if age_rand_number > 0.6:
                    age = 33
                if age_rand_number > 0.8:
                    age = 34
            elif age_group == 7:
                age_rand_number = np.random.random()
                age = 35
                if age_rand_number > 0.2:
                    age = 36
                if age_rand_number > 0.4:
                    age = 37
                if age_rand_number > 0.6:
                    age = 38
                if age_rand_number > 0.8:
                    age = 39
            elif age_group == 8:
                age_rand_number = np.random.random()
                age = 40
                if age_rand_number > 0.2:
                    age = 41
                if age_rand_number > 0.4:
                    age = 42
                if age_rand_number > 0.6:
                    age = 43
                if age_rand_number > 0.8:
                    age = 44
            elif age_group == 9:
                age_rand_number = np.random.random()
                age = 45
                if age_rand_number > 0.2:
                    age = 46
                if age_rand_number > 0.4:
                    age = 47
                if age_rand_number > 0.6:
                    age = 48
                if age_rand_number > 0.8:
                    age = 49
            elif age_group == 10:
                age_rand_number = np.random.random()
                age = 50
                if age_rand_number > 0.2:
                    age = 51
                if age_rand_number > 0.4:
                    age = 52
                if age_rand_number > 0.6:
                    age = 53
                if age_rand_number > 0.8:
                    age = 54
            elif age_group == 11:
                age_rand_number = np.random.random()
                age = 55
                if age_rand_number > 0.2:
                    age = 56
                if age_rand_number > 0.4:
                    age = 57
                if age_rand_number > 0.6:
                    age = 58
                if age_rand_number > 0.8:
                    age = 59
            elif age_group == 12:
                age_rand_number = np.random.random()
                age = 60
                if age_rand_number > 0.2:
                    age = 61
                if age_rand_number > 0.4:
                    age = 62
                if age_rand_number > 0.6:
                    age = 63
                if age_rand_number > 0.8:
                    age = 64
            elif age_group == 13:
                age_rand_number = np.random.random()
                age = 65
                if age_rand_number > 0.2:
                    age = 66
                if age_rand_number > 0.4:
                    age = 67
                if age_rand_number > 0.6:
                    age = 68
                if age_rand_number > 0.8:
                    age = 69
            elif age_group == 14:
                age_rand_number = np.random.random()
                age = 70
                if age_rand_number > 0.2:
                    age = 71
                if age_rand_number > 0.4:
                    age = 72
                if age_rand_number > 0.6:
                    age = 73
                if age_rand_number > 0.8:
                    age = 74
            elif age_group == 15:
                age_rand_number = np.random.random()
                age = 75
                if age_rand_number > 0.2:
                    age = 76
                if age_rand_number > 0.4:
                    age = 77
                if age_rand_number > 0.6:
                    age = 78
                if age_rand_number > 0.8:
                    age = 79
            elif age_group == 16:
                age_rand_number = np.random.random()
                age = 80
                if age_rand_number > 0.2:
                    age = 81
                if age_rand_number > 0.4:
                    age = 82
                if age_rand_number > 0.6:
                    age = 83
                if age_rand_number > 0.8:
                    age = 84
            elif age_group == 17:
                age_rand_number = np.random.random()
                age = 85
                if age_rand_number > 0.2:
                    age = 86
                if age_rand_number > 0.4:
                    age = 87
                if age_rand_number > 0.6:
                    age = 88
                if age_rand_number > 0.8:
                    age = 89
            elif age_group == 18:
                age_rand_number = np.random.random()
                age = 90
                if age_rand_number > 0.2:
                    age = 91
                if age_rand_number > 0.4:
                    age = 92
                if age_rand_number > 0.6:
                    age = 93
                if age_rand_number > 0.8:
                    age = 94

            age_index = 14
            if age > 14:
                age_index = 17
            if age > 17:
                age_index = 24
            if age > 24:
                age_index = 34
            if age > 34:
                age_index = 44
            if age > 44:
                age_index = 54
            if age > 54:
                age_index = 64
            if age > 64:
                age_index = 65

            age_index_ecomic_activity = 0
            if age > 14:
                age_index_ecomic_activity = 15
            if age > 19:
                age_index_ecomic_activity = 20
            if age > 29:
                age_index_ecomic_activity = 30
            if age > 39:
                age_index_ecomic_activity = 40
            if age > 49:
                age_index_ecomic_activity = 50
            if age > 59:
                age_index_ecomic_activity = 60

            dist_num = districts[districts == home_okato.loc[home_index].values[0]].index[0] + 1
            if num_of_people_to_add_to_household == 0:
                if age >= 16:
                    num_of_people_in_household = 1
                    rand_num = np.random.random()
                    total = age_districts_number_of_people.loc[age_index, 'DistrictTotal{}'.format(dist_num)]
                    cur_level = (age_districts_number_of_people.loc[age_index, 'District{}NumberOfPeople1'.
                                 format(dist_num)] / total)
                    if rand_num > cur_level:
                        num_of_people_in_household = 2
                    cur_level += (age_districts_number_of_people.loc[age_index, 'District{}NumberOfPeople2'.
                                 format(dist_num)] / total)
                    if rand_num > cur_level:
                        num_of_people_in_household = 3
                    cur_level += (age_districts_number_of_people.loc[age_index, 'District{}NumberOfPeople3'.
                                  format(dist_num)] / total)
                    if rand_num > cur_level:
                        num_of_people_in_household = 4
                    cur_level += (age_districts_number_of_people.loc[age_index, 'District{}NumberOfPeople4'.
                                  format(dist_num)] / total)
                    if rand_num > cur_level:
                        num_of_people_in_household = 5
                else:
                    num_of_people_in_household = 2
                    rand_num = np.random.random()
                    total = age_districts_number_of_people.loc[age_index, 'DistrictTotal{}'.format(dist_num)] \
                        - age_districts_number_of_people.loc[age_index, 'District{}NumberOfPeople1'.format(dist_num)]
                    cur_level = (age_districts_number_of_people.loc[age_index, 'District{}NumberOfPeople2'.
                                 format(dist_num)] / total)
                    if rand_num > cur_level:
                        num_of_people_in_household = 3
                    cur_level += (age_districts_number_of_people.loc[age_index, 'District{}NumberOfPeople3'.
                                  format(dist_num)] / total)
                    if rand_num > cur_level:
                        num_of_people_in_household = 4
                    cur_level += (age_districts_number_of_people.loc[age_index, 'District{}NumberOfPeople4'.
                                  format(dist_num)] / total)
                    if rand_num > cur_level:
                        num_of_people_in_household = 5
                        # HERE 6 PEOPLE IN ONE HOUSEHOLD!!!
                        # rand_num = np.random.random()
                        # if (rand_num > age_sex_districts.loc[home_okato.loc[home_index].values[0], '5People']
                        #         / age_sex_districts.loc[home_okato.loc[home_index].values[0], 'TotalBetween5And6People']):
                        #     num_of_people_in_household = 6

            # if num_of_people_in_household == 1:
            if (age >= 16) and (age <= 69):
                rand_num = np.random.random()
                economic_status = 0  # EconomicallyActive
                if sex == 0:
                    total = age_districts_economic_activities.loc['M{}'.format(age_index_ecomic_activity),
                                                                  'DistrictTotal{}'.format(dist_num)]
                    cur_level = age_districts_economic_activities.loc['M{}'.format(age_index_ecomic_activity),
                                                                      'District{}EconomicallyActive'.format(dist_num)] / total
                    if rand_num > cur_level:
                        economic_status = 1  # EconomicallyActiveWithoutWork
                    cur_level += age_districts_economic_activities.loc[
                        'M{}'.format(age_index_ecomic_activity),
                        'District{}EconomicallyActiveWithoutWork'.format(dist_num)] / total
                    if rand_num > cur_level:
                        economic_status = 2  # Inactive
                else:
                    total = age_districts_economic_activities.loc['F{}'.format(age_index_ecomic_activity),
                                                                  'DistrictTotal{}'.format(dist_num)]
                    cur_level = age_districts_economic_activities.loc['F{}'.format(age_index_ecomic_activity),
                                                                      'District{}EconomicallyActive'.format(dist_num)] / total
                    if rand_num > cur_level:
                        economic_status = 1  # EconomicallyActiveWithoutWork
                    cur_level += age_districts_economic_activities.loc[
                        'F{}'.format(age_index_ecomic_activity),
                        'District{}EconomicallyActiveWithoutWork'.format(dist_num)] / total
                    if rand_num > cur_level:
                        economic_status = 2  # Inactive
            else:
                economic_status = 2

            if num_of_people_to_add_to_household == 0:
                if num_of_people_in_household == 2:
                    rand_num = np.random.random()
                    if economic_status == 0:
                        household_economic_status = 1  # 1 Person Active
                        total = econimic_activity_districts.loc['2People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc['2People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]
                        cur_level = econimic_activity_districts.loc[
                            '2People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 2  # 2 People Active
                    else:
                        household_economic_status = 3  # 1 Person Active
                        total = econimic_activity_districts.loc[
                                    '2PeopleInactive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] \
                                + econimic_activity_districts.loc[
                                    '2People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]
                        cur_level = econimic_activity_districts.loc[
                                        '2People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 4  # 0 People Active
                    rand_num = np.random.random()
                    if age >= 18:
                        total = age_sex_districts.loc[home_okato.loc[home_index].values[0], '2People']
                        cur_level = age_sex_districts.loc[home_okato.loc[home_index].values[0], 'PairNoChildren'] / total
                        household_type = 0  # Pair no children
                        if rand_num > cur_level:
                            household_type = 1  # Single man 1 child
                        cur_level += age_sex_districts.loc[home_okato.loc[home_index].values[0], 'SingleMan1Children'] / total
                        if rand_num > cur_level:
                            household_type = 2  # Single woman 1 child
                        cur_level += age_sex_districts.loc[home_okato.loc[home_index].values[0], 'SingleWoman1Children'] / total
                        if rand_num > cur_level:
                            household_type = 3  # Person with parent
                    else:
                        total = age_sex_districts.loc[home_okato.loc[home_index].values[0], 'SingleMan1Children']\
                                + age_sex_districts.loc[home_okato.loc[home_index].values[0], 'SingleWoman1Children']
                        cur_level = age_sex_districts.loc[home_okato.loc[home_index].values[0], 'SingleMan1Children'] / total
                        household_type = 5  # Single man 1 child
                        if rand_num > cur_level:
                            household_type = 6  # Single woman 1 child

                if num_of_people_in_household == 3:
                    rand_num = np.random.random()
                    if economic_status == 0:
                        household_economic_status = 5  # 1 Person Active
                        total = econimic_activity_districts.loc['3People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc['3People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc['3People3PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]
                        cur_level = econimic_activity_districts.loc[
                            '3People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 6  # 2 People Active
                        cur_level += econimic_activity_districts.loc[
                                         '3People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 7  # 3 People Active
                    else:
                        household_economic_status = 8  # 2 Person Active
                        total = econimic_activity_districts.loc[
                                    '3PeopleInactive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] \
                                + econimic_activity_districts.loc[
                                    '3People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] \
                                + econimic_activity_districts.loc[
                                    '3People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]
                        cur_level = econimic_activity_districts.loc[
                                        '3People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 9  # 1 People Active
                        cur_level += econimic_activity_districts.loc[
                                         '3People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 10  # 0 People Active
                rand_num = np.random.random()
                if age >= 18:
                    total = age_sex_districts.loc[home_okato.loc[home_index].values[0], '3People']
                    cur_level = age_sex_districts.loc[home_okato.loc[home_index].values[0], 'Pair1Children'] / total
                    household_type = 7  # Pair 1 children
                    if rand_num > cur_level:
                        household_type = 8  # Single man 2 child
                    cur_level += age_sex_districts.loc[home_okato.loc[home_index].values[0], 'SingleMan2Children'] / total
                    if rand_num > cur_level:
                        household_type = 9  # Single woman 2 child
                    cur_level += age_sex_districts.loc[home_okato.loc[home_index].values[0], 'SingleWoman2Children'] / total
                    if rand_num > cur_level:
                        household_type = 10  # SinglePersonOneParent1Children
                    cur_level += age_sex_districts.loc[
                                     home_okato.loc[home_index].values[0], 'SinglePersonOneParent1Children'] / total
                    if rand_num > cur_level:
                        household_type = 11  # PairOneParentNoChildren
                    cur_level += age_sex_districts.loc[
                                     home_okato.loc[home_index].values[0], 'PairOneParentNoChildren'] / total
                    if rand_num > cur_level:
                        household_type = 12  # Other combinations
                else:
                    total = age_sex_districts.loc[home_okato.loc[home_index].values[0], 'Pair1Children'] \
                            + age_sex_districts.loc[home_okato.loc[home_index].values[0], 'SingleMan2Children']\
                            + age_sex_districts.loc[home_okato.loc[home_index].values[0], 'SingleWoman2Children']
                    cur_level = age_sex_districts.loc[home_okato.loc[home_index].values[0], 'Pair1Children'] / total
                    household_type = 13  # Pair 1 child
                    if rand_num > cur_level:
                        household_type = 14  # SingleMan2Children
                    cur_level += age_sex_districts.loc[home_okato.loc[home_index].values[0], 'SingleMan2Children'] / total
                    if rand_num > cur_level:
                        household_type = 15  # SingleWoman2Children
                    cur_level += age_sex_districts.loc[home_okato.loc[home_index].values[0], 'SingleWoman2Children'] / total
                    if rand_num > cur_level:
                        household_type = 16  # SinglePersonOneParent1Children

                if num_of_people_in_household == 4:
                    rand_num = np.random.random()
                    if economic_status == 0:
                        household_economic_status = 11  # 1 Person Active
                        total = econimic_activity_districts.loc['4People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc['4People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc['4People3PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc['4People4PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]
                        cur_level = econimic_activity_districts.loc[
                            '4People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 12  # 2 People Active
                        cur_level += econimic_activity_districts.loc[
                                         '4People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 13  # 3 People Active
                        cur_level += econimic_activity_districts.loc[
                                         '4People3PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 14  # 4 People Active
                    else:
                        household_economic_status = 15  # 3 Person Active
                        total = econimic_activity_districts.loc[
                                    '4PeopleInactive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc[
                                    '4People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc[
                                    '4People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc[
                                    '4People3PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]
                        cur_level = econimic_activity_districts.loc[
                                        '4People3PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 16  # 2 People Active
                        cur_level += econimic_activity_districts.loc[
                                         '4People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 17  # 1 People Active
                        cur_level += econimic_activity_districts.loc[
                                         '4People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 18  # 0 People Active
                    rand_num = np.random.random()
                    total = age_sex_districts.loc[home_okato.loc[home_index].values[0], '4People']
                    cur_level = age_sex_districts.loc[home_okato.loc[home_index].values[0], 'Pair2Children'] / total
                    household_type = 17  # Pair 2 children
                    if rand_num > cur_level:
                        household_type = 18  # Single man 3 child
                    cur_level += age_sex_districts.loc[
                                     home_okato.loc[home_index].values[0], 'SingleMan3Children'] / total
                    if rand_num > cur_level:
                        household_type = 19  # Single woman 3 child
                    cur_level += age_sex_districts.loc[
                                     home_okato.loc[home_index].values[0], 'SingleWoman3Children'] / total
                    if rand_num > cur_level:
                        household_type = 20  # SinglePersonOneParent2Children
                    cur_level += age_sex_districts.loc[
                                     home_okato.loc[home_index].values[0], 'SinglePersonOneParent2Children'] / total
                    if rand_num > cur_level:
                        household_type = 21  # Pair 1 Parent 1 Children
                    cur_level += age_sex_districts.loc[
                                     home_okato.loc[home_index].values[0], 'PairOneParent1Children'] / total
                    if rand_num > cur_level:
                        household_type = 22  # Other combinations

                if num_of_people_in_household == 5:
                    rand_num = np.random.random()
                    if economic_status == 0:
                        household_economic_status = 19  # 1 Person Active
                        total = econimic_activity_districts.loc['5People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc['5People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc['5People3PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc['5People4PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc['5People5PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]
                        cur_level = econimic_activity_districts.loc[
                            '5People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 20  # 2 People Active
                        cur_level += econimic_activity_districts.loc[
                                         '5People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 21  # 3 People Active
                        cur_level += econimic_activity_districts.loc[
                                         '5People3PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 22  # 4 People Active
                        cur_level += econimic_activity_districts.loc[
                                         '5People4PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 23  # 5 People Active
                    else:
                        household_economic_status = 24  # 4 Person Active
                        total = econimic_activity_districts.loc[
                                    '5PeopleInactive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc[
                                    '5People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc[
                                    '5People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc[
                                    '5People3PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]\
                                + econimic_activity_districts.loc[
                                    '5People4PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)]
                        cur_level = econimic_activity_districts.loc[
                                        '5People4PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 25  # 3 People Active
                        cur_level += econimic_activity_districts.loc[
                                         '5People3PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 26  # 2 People Active
                        cur_level += econimic_activity_districts.loc[
                                         '5People2PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 27  # 1 People Active
                        cur_level += econimic_activity_districts.loc[
                                         '5People1PeopleActive', 'NumberOfHouseholdsDistrict{}'.format(dist_num)] / total
                        if rand_num > cur_level:
                            household_economic_status = 28  # 0 People Active
                    rand_num = np.random.random()
                    total = age_sex_districts.loc[home_okato.loc[home_index].values[0], '5People']
                    cur_level = age_sex_districts.loc[home_okato.loc[home_index].values[0], 'Pair3Children'] / total
                    household_type = 18  # Pair 3 children
                    if rand_num > cur_level:
                        household_type = 19  # SinglePersonOneParent3Children
                    cur_level += age_sex_districts.loc[
                                     home_okato.loc[home_index].values[0], 'SinglePersonOneParent3Children'] / total
                    if rand_num > cur_level:
                        household_type = 20  # PairOneParent2Children
                    cur_level += age_sex_districts.loc[
                                     home_okato.loc[home_index].values[0], 'PairOneParent2Children'] / total
                    if rand_num > cur_level:
                        household_type = 21  # Other combinations

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
                    total = children_attendance.loc['M{}'.format(infancy_age_group), 'District{}TotalSurveyed'.format(dist_num)]
                    cur_level = children_attendance.loc['M{}'.format(infancy_age_group), 'District{}NotAttending'.format(dist_num)] / total
                    if rand_num > cur_level:
                        education_status = 1
                if sex == 1:
                    total = children_attendance.loc['F{}'.format(infancy_age_group), 'District{}TotalSurveyed'.format(dist_num)]
                    cur_level = children_attendance.loc['F{}'.format(infancy_age_group), 'District{}NotAttending'.format(dist_num)] / total
                    if rand_num > cur_level:
                        education_status = 1
            if 7 <= age <= 16:
                education_status = 2
            if (17 <= age <= 18) and (economic_status == 2):
                education_status = 2
            if (19 <= age <= 22) and (economic_status == 2):
                education_status = 3

            if economic_status == 0:
                work_index = np.random.randint(0, len(self.home_coords) - 1)
                self.closest_metro_stations_to_works.append(self.closest_metro_stations[work_index])
                self.ways_to_work.append(self.metro_ways[self.closest_metro_stations[home_index]
                                                         * 231 + self.closest_metro_stations[work_index]
                                                         + self.closest_metro_stations[home_index]])
                self.work_indexes[i] = work_index
                self.ways_to_home.append(self.metro_ways[self.closest_metro_stations[work_index]
                                                         * 231 + self.closest_metro_stations[home_index]
                                                         + self.closest_metro_stations[work_index]])
                x = self.home_coords[work_index, 0]
                y = self.home_coords[work_index, 1]
                pos = np.array((x, y))
                self.work_positions[i] = pos
            elif education_status == 1:
                work_index = np.random.randint(0, len(self.kindergarten_coords) - 1)
                self.closest_metro_stations_to_works.append(self.closest_metro_stations_to_kindergartens[work_index])
                self.ways_to_work.append(self.metro_ways[self.closest_metro_stations[home_index]
                                                         * 231 + self.closest_metro_stations_to_kindergartens[work_index]
                                                         + self.closest_metro_stations[home_index]])
                self.work_indexes[i] = work_index
                self.ways_to_home.append(self.metro_ways[self.closest_metro_stations_to_kindergartens[work_index]
                                                         * 231 + self.closest_metro_stations[home_index]
                                                         + self.closest_metro_stations_to_kindergartens[work_index]])
                x = self.kindergarten_coords[work_index, 0]
                y = self.kindergarten_coords[work_index, 1]
                pos = np.array((x, y))
                self.work_positions[i] = pos
            elif education_status == 2:
                work_index = np.random.randint(0, len(self.school_coords) - 1)
                self.closest_metro_stations_to_works.append(self.closest_metro_stations_to_schools[work_index])
                self.ways_to_work.append(self.metro_ways[self.closest_metro_stations[home_index]
                                                         * 231 + self.closest_metro_stations_to_schools[work_index]
                                                         + self.closest_metro_stations[home_index]])
                self.work_indexes[i] = work_index
                self.ways_to_home.append(self.metro_ways[self.closest_metro_stations_to_schools[work_index]
                                                         * 231 + self.closest_metro_stations[home_index]
                                                         + self.closest_metro_stations_to_schools[work_index]])
                x = self.school_coords[work_index, 0]
                y = self.school_coords[work_index, 1]
                pos = np.array((x, y))
                self.work_positions[i] = pos
            elif education_status == 3:
                work_index = np.random.randint(0, len(self.university_coords) - 1)
                self.closest_metro_stations_to_works.append(self.closest_metro_stations_to_universities[work_index])
                self.ways_to_work.append(self.metro_ways[self.closest_metro_stations[home_index]
                                                         * 231 + self.closest_metro_stations_to_universities[work_index]
                                                         + self.closest_metro_stations[home_index]])
                self.work_indexes[i] = work_index
                self.ways_to_home.append(self.metro_ways[self.closest_metro_stations_to_universities[work_index]
                                                         * 231 + self.closest_metro_stations[home_index]
                                                         + self.closest_metro_stations_to_universities[work_index]])
                x = self.university_coords[work_index, 0]
                y = self.university_coords[work_index, 1]
                pos = np.array((x, y))
                self.work_positions[i] = pos
            else:
                self.closest_metro_stations_to_works.append(-1)
                self.ways_to_work.append([-1])
                self.ways_to_home.append([-1])

            if num_of_people_to_add_to_household == 0:
                num_of_people_to_add_to_household = num_of_people_in_household
            else:
                num_of_people_to_add_to_household -= 1
            self.agent_list.append(DiseaseAgent(i, sex, age, health_status, economic_status, education_status))
            # print(economic_status)
            # print(sex, age)
            x = self.home_coords[home_index, 0]
            y = self.home_coords[home_index, 1]
            pos = np.array((x, y))
            self.agent_positions[i] = pos
            self.grid[y, x, i] = i
        self.home_positions = self.agent_positions.copy()

        # Dynamic array containing the number of susceptible, exposed, infected people at each time tick
        self.infected_by_ticks = [self.infected]
        self.exposed_by_ticks = [self.exposed]
        self.susceptible_by_ticks = [self.susceptible]

    # def get_neighbors(self, pos, distance):
    #     neighbors_list = []
    #     for agent in self.agent_list:
    #         if np.linalg.norm(pos - agent.pos) < distance:
    #             neighbors_list.append(agent)
    #     return neighbors_list
    #
    # def get_heading(self, pos_1, pos_2):
    #     heading = pos_1 - pos_2
    #     return heading

    def add_agent(self):
        return

    def populate_household(self):
        return

    def make_agent_steps(self, agent):
        # if (np.random.random() < 0.001) & (agent.status == 0):
        #     agent.status = 1
        #     self.susceptible -= 1
        #     self.infected += 1
        #     self.agent_colors[agent.unique_id] = [1, 0, 0]
        # print(agent.unique_id)
        # print('StART')
        pos_x = self.agent_positions[agent.unique_id, 0]
        pos_y = self.agent_positions[agent.unique_id, 1]
        if agent.health_status == 2:
            for agent_id in self.grid[pos_y, pos_x][(self.grid[pos_y, pos_x] > -1)]:
                other_agent = self.agent_list[agent_id]
                if (np.random.random() < 0.01) & (other_agent.health_status == 0):
                    other_agent.health_status = 1
                    self.susceptible -= 1
                    self.exposed += 1
                    self.agent_colors[other_agent.unique_id] = [0, 1, 0]
        elif agent.health_status == 1:
                if np.random.random() < 0.001:
                    agent.health_status = 2
                    self.exposed -= 1
                    self.infected += 1
                    self.agent_colors[agent.unique_id] = [1, 0, 0]
        if self.closest_metro_stations_to_works[agent.unique_id] == -1:
            return
        # if agent.economic_status != 0:
        #     return
        # if (agent.economic_status != 0) and (agent.education_status == 0):
        #     return

        # print('Age', agent.age)
        # print('System status', self.system_status)
        self.grid[pos_y, pos_x, agent.unique_id] = -1
        if self.system_status == 1:
            if self.curr_positions_in_metro[agent.unique_id] == -1:
                # print('first drop')
                self.agent_positions[agent.unique_id] =\
                    self.metro_coords[self.closest_metro_stations[self.home_indexes[agent.unique_id]]]
                self.curr_positions_in_metro[agent.unique_id] =\
                    self.closest_metro_stations[self.home_indexes[agent.unique_id]]
            elif self.curr_positions_in_metro[agent.unique_id] == \
                    self.closest_metro_stations_to_works[agent.unique_id]:
                # print('aaarrg')
                self.agent_positions[agent.unique_id] = self.work_positions[agent.unique_id]
                self.curr_positions_in_metro[agent.unique_id] = -2
            elif self.curr_positions_in_metro[agent.unique_id] != -2:
                print(self.ways_to_work[agent.unique_id])
                print('Cur pos', self.curr_positions_in_metro[agent.unique_id])
                next_station_index =\
                    np.argwhere(self.ways_to_work[agent.unique_id] ==
                                self.curr_positions_in_metro[agent.unique_id]).flatten()[0] + 1
                # print(next_station_index)
                next_station = self.ways_to_work[agent.unique_id][next_station_index]
                # print(next_station)
                self.agent_positions[agent.unique_id] = self.metro_coords[next_station]
                self.curr_positions_in_metro[agent.unique_id] = next_station
            print('End')


            # self.agent_positions[agent.unique_id] -= \
            #     ((self.agent_positions[agent.unique_id] - self.work_positions[agent.unique_id]) * self.speed)\
            #     .astype('int64')
        elif self.system_status == 0:
            # print(self.curr_positions_in_metro[agent.unique_id])
            if self.curr_positions_in_metro[agent.unique_id] == -2:
                self.agent_positions[agent.unique_id] =\
                    self.metro_coords[self.closest_metro_stations_to_works[agent.unique_id]]
                self.curr_positions_in_metro[agent.unique_id] = \
                    self.closest_metro_stations_to_works[agent.unique_id]
            elif self.curr_positions_in_metro[agent.unique_id] ==\
                    self.closest_metro_stations[self.home_indexes[agent.unique_id]]:
                self.agent_positions[agent.unique_id] = self.home_positions[agent.unique_id]
                self.curr_positions_in_metro[agent.unique_id] = -1
            elif self.curr_positions_in_metro[agent.unique_id] != -1:
                next_station_index =\
                    np.argwhere(self.ways_to_home[agent.unique_id] ==
                                self.curr_positions_in_metro[agent.unique_id]).flatten()[0] + 1
                next_station = self.ways_to_home[agent.unique_id][next_station_index]
                self.agent_positions[agent.unique_id] = self.metro_coords[next_station]
                self.curr_positions_in_metro[agent.unique_id] = next_station
        elif self.system_status == 2:
            park_index = np.random.randint(0, len(self.park_coords) - 1)
            x = self.park_coords[park_index, 0]
            y = self.park_coords[park_index, 1]
            pos = np.array((x, y))
            self.agent_positions[agent.unique_id] -= \
                ((self.agent_positions[agent.unique_id] - pos)
                 * self.speed).astype('int64')
        # pos_x = self.agent_positions[agent.unique_id, 0]
        # pos_y = self.agent_positions[agent.unique_id, 1]

        # print(self.agent_positions[agent.unique_id, 1], self.agent_positions[agent.unique_id, 0])
        self.grid[self.agent_positions[agent.unique_id, 1],
                  self.agent_positions[agent.unique_id, 0],
                  agent.unique_id] = agent.unique_id
        print('End2')
        # self.agent_positions[agent.unique_id][0] -= int((self.agent_positions[agent.unique_id][0]
        #                                           - self.work_positions[agent.unique_id][0]) * self.speed)
        # self.agent_positions[agent.unique_id][1] -= int((self.agent_positions[agent.unique_id][1]
        #                                                  - self.work_positions[agent.unique_id][1]) * self.speed)
        # self.agent_positions[agent.unique_id] += ((self.agent_positions[agent.unique_id]
        #                                          - self.work_positions[agent.unique_id]) * self.speed).astype(int)
        # self.agent_positions[agent.unique_id, 1] += np.random.randint(2) - np.random.randint(2)

    def step(self, i):
        if i % 20 == 0:
            self.hour += 1
        if (self.hour % 24 == 0) and (self.hour != 0):
            self.hour = 0
            self.day += 1
            self.global_days += 1
        if (self.month in {1, 3, 5, 7, 8, 10, 12}) and (self.day % 31 == 0):
            self.day = 1
            self.month += 1
        elif (self.month in {4, 6, 9, 11}) and (self.day % 30 == 0):
            self.day = 1
            self.month += 1
        elif (self.month == 2) and (self.day % 28 == 0): # Without leap years
            self.day = 1
            self.month += 1
        if self.month % 12 == 0:
            self.month = 1
            self.year += 1

        if (self.global_days % 6 != 0) and (self.global_days % 7 != 0):
            if self.hour == 7:
                self.system_status = 1
            elif self.hour == 17:
                self.system_status = 0
        # else:
        #     if self.hour == 10:
        #         self.system_status = 2
        #     elif self.hour == 20:
        #         self.system_status = 0

        for agent in self.agent_list:
            self.make_agent_steps(agent)

        # if i % 8760 != 0:
        #     for agent in self.agent_list:
        #         self.make_agent_steps(agent)
        # else:
        #     for agent in self.agent_list:
        #         self.make_agent_steps(agent)
        #         agent.age += 1
        self.susceptible_by_ticks.append(self.susceptible)
        self.exposed_by_ticks.append(self.exposed)
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
            slider_max = gr.bottom() - slider_length + 1;
        pr = pos - sr.center() + sr.topLeft()
        p = pr.x() if self.orientation() == QtCore.Qt.Horizontal else pr.y()
        return QtWidgets.QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), p - slider_min,
                                                        slider_max - slider_min, opt.upsideDown)


class ApplicationWindow(QMainWindow):

    def __init__(self, num_of_agents, size_of_agents_on_canvas, grid_height, grid_width, neighbor_distance):
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
        self.exposed_label = QLabel("Number of exposed: 0")
        self.exposed_label.setStyleSheet("font-size: 20px; color: green;")
        self.infected_label = QLabel("Number of infected: 0")
        self.infected_label.setStyleSheet("font-size: 20px; color: red;")

        header_box.addLayout(interval_slider_box)

        self.canvas = MyCanvas(width=10, height=10, dpi=100, x_lim=grid_width, y_lim=grid_height)
        self.graph_canvas = GraphCanvas(width=5, height=5, dpi=100, y_max=num_of_agents)
        self.graph_canvas.setFixedSize(400, 400)
        labels_box.addWidget(self.ticks_label)
        labels_box.addWidget(self.susceptible_label)
        labels_box.addWidget(self.exposed_label)
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

        self.model = Model(num_of_agents, grid_height, grid_width, neighbor_distance)

        rgb = np.random.random((10, 3))
        self.scat = self.canvas.ax.scatter(
            np.array([]), np.array([]), s=size_of_agents_on_canvas, lw=0.5, facecolors=rgb)

        self.line, = self.graph_canvas.ax.plot([0], [0], c='b')
        self.line2, = self.graph_canvas.ax.plot([0], [0], c='r')
        self.line3, = self.graph_canvas.ax.plot([0], [0], c='g')

        data_x = []
        data_y = []

        for okato, mun in GpsCoordinates.municipalities.items():
            if okato == 45268562000:
                for parts in mun:
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
                for coord in mun:
                    c = GpsCoordinates.gps_to_xy(coord, GpsCoordinates.top_left_gps_coord,
                                                 GpsCoordinates.bottom_right_gps_coord,
                                                 grid_width, grid_height)
                    data_x.append(c[0])
                    data_y.append(c[1])
                self.canvas.ax.plot(data_x, data_y, c='k', linewidth=2)
                data_x = []
                data_y = []

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
            data_x, data_y, s=15, lw=0.5, c="k", marker="x")

        self.running = -1

    def update_agent_animation(self, i):
        self.model.step(i + 1)
        self.scat.set_offsets(self.model.agent_positions)
        self.scat.set_color(self.model.agent_colors)
        self.ticks_label.setText("Number of ticks: {0}".format(str(i + 1)))
        return self.scat,

    def update_graph_animation(self, i):
        self.line.set_data(range(len(self.model.susceptible_by_ticks)), self.model.susceptible_by_ticks)
        self.line2.set_data(range(len(self.model.infected_by_ticks)), self.model.infected_by_ticks)
        self.line3.set_data(range(len(self.model.exposed_by_ticks)), self.model.exposed_by_ticks)
        self.graph_canvas.ax.relim()
        self.graph_canvas.ax.autoscale_view()
        self.susceptible_label.setText("Number of susceptible: {0}".format(str(self.model.susceptible)))
        self.exposed_label.setText("Number of exposed: {0}".format(str(self.model.exposed)))
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
    app = QApplication(sys.argv)
    window = ApplicationWindow(100, 19, 500, 500, 1)
    window.show()
    app.exec()
