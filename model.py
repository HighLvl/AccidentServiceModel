import enum
import math
import random
import sys

import networkx as nx
import matplotlib.pyplot as plt

_WEIGHT_KEY = "weight"


class EmergencySite:
    def __init__(self, intensity, node):
        self.intensity = intensity
        self.node = node
        self._time_until_next_event = 0
        self._next_time_events_number = 0

    # Poisson process
    # returns True if number of events that occurred during dt > 0
    def emit_accident_event(self, dt):
        if self.intensity == 0:
            return False
        if self._time_until_next_event > dt:
            self._time_until_next_event -= dt
            return False
        time_for_event_emitting = dt - self._time_until_next_event
        event_number = self._next_time_events_number
        while time_for_event_emitting > 0:
            r = random.random()
            next_event_dt = -1.0 / self.intensity * math.log(r)
            time_for_event_emitting -= next_event_dt
            if time_for_event_emitting > 0:
                event_number += 1
        self._time_until_next_event = -time_for_event_emitting
        if self._time_until_next_event > 0:
            self._next_time_events_number = 1
        else:
            self._next_time_events_number = 0
        return event_number > 0


class MobileService:
    class State(enum.Enum):
        MOVE_TO_SITE = 1
        MOVE_TO_START = 2
        WAIT_ON_ACCIDENT_SITE = 3
        WAIT_ON_START_SITE = 4

    def __init__(self, start_site, wait_time, path_finder):
        self._start_site = start_site
        self._wait_time = wait_time
        self._current_site = start_site
        self._path_finder = path_finder
        self._state = MobileService.State.WAIT_ON_START_SITE
        self._accident_list = []
        self._remaining_travel_time = 0
        self._remaining_wait_time = 0
        self._travel_time = 0

        self._total_time = 0.0
        self._total_processed_accidents_number = 0

    def update(self, dt):
        if self._state == self.State.MOVE_TO_START:
            self._remaining_travel_time -= dt
            if self._remaining_travel_time <= 0:
                self._state = self.State.WAIT_ON_START_SITE

        elif self._state == self.State.MOVE_TO_SITE:
            self._remaining_travel_time -= dt
            if self._remaining_travel_time <= 0:
                self._remaining_wait_time = self._wait_time + self._remaining_travel_time
                self._remaining_travel_time = 0
                self._state = self.State.WAIT_ON_ACCIDENT_SITE

        elif self._state == self.State.WAIT_ON_ACCIDENT_SITE:
            self._remaining_wait_time -= dt
            if self._remaining_wait_time <= 0:
                self._total_processed_accidents_number += 1
                self._total_time += self._travel_time + self._wait_time

                self._accident_list.remove(self._current_site)

                if self._accident_list:
                    self._current_site, self._travel_time = self._path_finder.get_nearest_site(self._current_site,
                                                                                               self._accident_list)
                    self._remaining_travel_time += self._remaining_wait_time + self._travel_time
                    self._remaining_wait_time = 0
                    self._state = self.State.MOVE_TO_SITE
                else:
                    self._travel_time = self._path_finder.find_shortest_path_length(self._current_site,
                                                                                    self._start_site)
                    self._current_site = self._start_site
                    self._remaining_travel_time += self._remaining_wait_time + self._travel_time
                    self._remaining_wait_time = 0
                    self._state = self.State.MOVE_TO_START

        elif self._state == self.State.WAIT_ON_START_SITE:
            if self._accident_list:
                self._current_site, self._travel_time = self._path_finder.get_nearest_site(self._current_site,
                                                                                           self._accident_list)
                self._remaining_travel_time += self._travel_time
                self._state = self.State.MOVE_TO_SITE

    def add_site_to_accident_list(self, site):
        self._accident_list.append(site)

    def get_avg_time(self):
        return self._total_time / self._total_processed_accidents_number

    def get_total_time(self):
        return self._total_time

    def get_total_processed_accidents_number(self):
        return self._total_processed_accidents_number

    def get_start_site(self):
        return self._start_site


class PathFinder:
    def __init__(self, graph):
        self._graph = graph

    def find_shortest_path_length(self, source_site, target_site):
        return nx.shortest_path_length(self._graph,
                                       source_site.node,
                                       target_site.node,
                                       _WEIGHT_KEY)

    def get_nearest_site(self, source_site, site_list):
        nearest_site = None
        distance_to_nearest_site = sys.float_info.max
        for site in site_list:

            distance_to_site = nx.shortest_path_length(self._graph,
                                                       source_site.node,
                                                       site.node,
                                                       _WEIGHT_KEY)
            if distance_to_site < distance_to_nearest_site:
                nearest_site = site
                distance_to_nearest_site = distance_to_site
        return nearest_site, distance_to_nearest_site


def read_input(input_file_path):
    file = open(input_file_path, "r")
    site_delay = float(file.readline())
    dt = float(file.readline())
    run_time = float(file.readline())
    run_number = int(file.readline())

    n = int(file.readline())
    site_dict = dict()
    edge_matrix = dict()
    for i in range(n):
        tokens = file.readline().split()
        site_number, intensity = [int(tokens[0]), float(tokens[1])]
        site_dict[site_number] = intensity
        edge_matrix[site_number] = dict()
    n = int(file.readline())
    for i in range(n):
        tokens = file.readline().split()
        site_number_1, site_number_2, travel_time = [int(tokens[0]), int(tokens[1]), float(tokens[2])]
        edge_matrix[site_number_1][site_number_2] = {_WEIGHT_KEY: travel_time}
        edge_matrix[site_number_2][site_number_1] = {_WEIGHT_KEY: travel_time}

    return site_dict, edge_matrix, run_time, run_number, site_delay, dt


def show_graph(graph, node_info_dict):
    pos = nx.spring_layout(graph)
    labels = {n: (str(n) + ": " + f"i=" + str(f"{node_info_dict[n][1]:.4f}")) for n in graph.nodes}
    nx.draw(graph, pos=pos, labels=labels)
    labels = {e: str(graph.get_edge_data(*e)[_WEIGHT_KEY]) for e in graph.edges}
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels)

    optimal_node = min(node_info_dict.items(), key=lambda x: x[1][0])[0]
    nx.draw_networkx_nodes(graph, pos=pos, nodelist=[optimal_node], node_color="Red")

    info_text = "\n".join([(str(item[0]) + ": "
                                           f"intensity=" + str(f"{item[1][1]:.4f}, "
                                                               "avg_time=" + str(f"{item[1][0]:.2f}"
                                                                                 )))
                           for item in sorted(node_info_dict.items(), key=lambda x: x[1][0])])
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    axes = plt.gca()
    xlim = axes.get_xlim()
    axes.set_xlim((xlim[0] * 2, xlim[1]))
    x = axes.get_xlim()[0] * 0.9
    y = axes.get_ylim()[1] * 0.9
    plt.text(x, y, info_text, fontsize=14,
             verticalalignment='top', horizontalalignment="left", bbox=props)

    plt.show()


def run_model(input_file_path, test_mode=False):
    (site_dict, edge_matrix, run_time, run_number, site_delay, dt) = read_input(input_file_path)
    site_list = [EmergencySite(intensity, site_number) for site_number, intensity in site_dict.items()]
    graph = nx.from_dict_of_dicts(edge_matrix)

    for i in range(run_number):
        remaining_time = run_time

        # сервис для поиска оптимального пути
        path_finder = PathFinder(graph)
        #для всех участков создаются мобильные службы
        mobile_service_list = []
        for start_site in site_list:
            service = MobileService(start_site, site_delay, path_finder)
            mobile_service_list.append(service)

        while remaining_time > 0:
            remaining_time -= dt

            # для всех участков генерируются события аварий
            accident_list = list(filter(lambda x: x.emit_accident_event(dt), site_list))
            # все мобильные службы оповещаются о событиях
            for accident_site in accident_list:
                for mobile_service in mobile_service_list:
                    mobile_service.add_site_to_accident_list(accident_site)
            # обновляется поведение мобильных служб
            for mobile_service in mobile_service_list:
                mobile_service.update(dt)

        # список сортируется по среднему времени, затраченному на один выезд службы на аварию
        # таким образом, первая служба в списке имеет самую оптимальную стартовую позицию
        mobile_service_list.sort(key=lambda x: x.get_avg_time())

        stat = [(x.get_start_site().node,
                 x.get_total_time(),
                 x.get_total_processed_accidents_number(),
                 x.get_avg_time())
                for x in mobile_service_list]

        if not test_mode:
            # вывод статистики
            # (номер участка) (общее время работы) (число обработанных событий) (среднее время обработки события)
            for x in stat:
                print(x[0], x[1], x[2], x[3])

            # вывод графа
            node_info_dict = dict()
            for service in mobile_service_list:
                node_info_dict[service.get_start_site().node] = (
                    service.get_avg_time(), service.get_start_site().intensity)
            show_graph(graph, node_info_dict)

        return stat
