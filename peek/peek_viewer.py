import datetime
import os
import time

from peek.log_statistics import LogStatistics


class PeekViewer:
    def __init__(self, log_file_path, db_path, refresh_rate=5):
        self._log_file_path = log_file_path
        self._db_path = db_path
        self._refresh_rate = refresh_rate
        self._last_total_request_count = 0
        self._last_check_timestamp = 0
        self._log_statistics = LogStatistics(persist=True)

    def get_requests_per_second(self, new_request_count):
        current_check_timestamp = int(time.time())
        seconds_since_last_check = current_check_timestamp - self._last_check_timestamp
        rps = (new_request_count - self._last_total_request_count) / seconds_since_last_check
        self._last_check_timestamp = current_check_timestamp
        self._last_total_request_count = new_request_count
        return round(rps, 1)
        # current_time = int(time.time())
        # one_minute_ago = int(time.time()) - 60
        # rps = round(self._log_statistics.get_requests_per_second_in_timespan(
        #     timespan_start=one_minute_ago,
        #     timespan_end=current_time), 2)
        # return rps

    def get_total_request_count(self, request_verb='GET'):
        return self._log_statistics.get_verb_occurrences()[request_verb]

    def get_unique_ip_address_count(self, time_limited=False):
        if time_limited:
            now = int(time.time())
            one_minute_ago = now - 60
            return self._log_statistics.get_number_of_distinct_ip_addresses(
                timespan_start=one_minute_ago,
                timespan_end=now)
        return self._log_statistics.get_number_of_distinct_ip_addresses()

    @staticmethod
    def _format_bytes_string(byte_count, byte_format='B', rounding=2):
        byte_words = {
            'B': 'Bytes',
            'KB': 'Kilobytes',
            'MB': 'Megabytes',
            'GB': 'Gigabytes'
        }
        if byte_format == 'KB':
            byte_count /= 1000
        elif byte_format == 'MB':
            byte_count /= 1000000
        return '{} {}'.format(round(byte_count, rounding), byte_words[byte_format])

    def get_total_bytes_sent(self, byte_format='B'):
        byte_count = self._log_statistics.get_total_byte_count()
        return self._format_bytes_string(byte_count=byte_count, byte_format=byte_format, rounding=1)

    @staticmethod
    def get_last_checked_time():
        return ['Last check timestamp', datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S')]

    def get_access_log_size_row(self, byte_format):
        access_log_size = os.path.getsize(self._log_file_path)
        return self._format_bytes_string(byte_count=access_log_size, byte_format=byte_format, rounding=1)

    def get_db_size_row(self, byte_format):
        db_size = 0
        if not self._log_statistics.db_path == ':memory:':
            db_size = os.path.getsize(self._log_statistics.db_path)
        return self._format_bytes_string(byte_count=db_size, byte_format=byte_format, rounding=1)

    def draw_screen(self, screen):
        # draw the border
        self.draw_border(screen=screen)
        # print layout once
        for data in self.get_static_screen_data():
            screen.print_at(data[0], data[1], data[2])
        while True:
            # update only the values
            for data in self.get_dynamic_screen_data():
                screen.print_at(data[0], data[1], data[2])
            ev = screen.get_key()
            if ev in (ord('Q'), ord('q')):
                return
            screen.refresh()
            time.sleep(self._refresh_rate)

    @staticmethod
    def draw_border(screen):
        # Top Bar
        screen.move(1, 0)
        screen.draw(79, 0, char='-')
        # Left Bar
        screen.move(0, 1)
        screen.draw(0, 24, char='|')
        # Bottom Bar
        screen.move(1, 23)
        screen.draw(79, 23, char='-')
        # Right Bar
        screen.move(79, 1)
        screen.draw(79, 24, char='|')
        # Corners
        screen.print_at('+', 0, 0)
        screen.print_at('+', 79, 0)
        screen.print_at('+', 0, 23)
        screen.print_at('+', 79, 23)

    def draw_static_data(self, screen):
        pass

    def draw_dynamic_data(self, screen):
        pass

    @staticmethod
    def get_static_screen_data():
        static_x_coord = 1
        return (
            ('Nginx Statistics', static_x_coord, 1),
            ('Requests per second:', static_x_coord, 2),
            ('Total request count:', static_x_coord, 3),
            ('Unique IP Address count:', static_x_coord, 4),
            # ('Recent Unique IP count:', static_x_coord, 5),
            ('Total data sent:', static_x_coord, 6),
            ('Current access log size:', static_x_coord, 7),
            ('Current access DB size:', static_x_coord, 8),
            ('Last checked timestamp:', static_x_coord, 9)
        )

    @staticmethod
    def _pad(string_to_pad, required_length, pad_character, left=True):
        string_to_pad = str(string_to_pad)
        string_length = len(string_to_pad)
        if string_length < required_length:
            for i in range(0, required_length - string_length):
                if left:
                    string_to_pad = '{}{}'.format(pad_character, string_to_pad)
                else:
                    string_to_pad = '{}{}'.format(string_to_pad, pad_character)
        return string_to_pad

    def get_dynamic_screen_data(self):
        dynamic_x_coord = 26
        total_request_count = self.get_total_request_count()
        rps = str(self.get_requests_per_second(new_request_count=total_request_count))
        # unique_ip_count_time_limited = self.get_unique_ip_address_count(time_limited=True)
        unique_ip_count = self.get_unique_ip_address_count()
        total_data_sent = self.get_total_bytes_sent(byte_format='MB')
        log_file_size = self.get_access_log_size_row(byte_format='MB')
        db_size = self.get_db_size_row(byte_format='MB')
        last_checked_timestamp = self.get_last_checked_time()
        return (
            (self._pad(rps, required_length=5, pad_character=' ', left=False), dynamic_x_coord, 2),
            (str(total_request_count), dynamic_x_coord, 3),
            (str(unique_ip_count), dynamic_x_coord, 4),
            # (self._pad(unique_ip_count_time_limited, 3, '0'), dynamic_x_coord, 5),
            (total_data_sent, dynamic_x_coord, 6),
            (log_file_size, dynamic_x_coord, 7),
            (db_size, dynamic_x_coord, 8),
            (last_checked_timestamp, dynamic_x_coord, 9)
        )


if __name__ == '__main__':
    # import cProfile
    # cProfile.run('pv.get_dynamic_screen_data()', sort=1)
    pass
