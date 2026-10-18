import csv
import functools
import time

import requests


class HttpError(Exception):
    pass


class NotFoundError(HttpError):
    pass


class AccessDeniedError(HttpError):
    pass


def download_file(url: str, filename: str = "latest.txt"):
    response = requests.get(url)
    if response.status_code == 404:
        raise NotFoundError(f"Resource not found: {url}")
    if response.status_code == 403:
        raise AccessDeniedError(f"Access denied to resource: {url}")
    response.raise_for_status()
    with open(filename, "wb") as file:
        file.write(response.content)


def read_lines(filename: str):
    """ETAP 1 (Extract): generator wczytujący plik linijka po linijce."""
    with open(filename, newline="") as file:
        for row in csv.reader(file):
            yield row


def parse_row(row: list[str]):
    """Dla jednego wiersza zwraca (indeksy braków, wartości liczbowe).

    Pierwsza kolumna (indeks 0) to numer porządkowy i nie jest brana pod
    uwagę w obliczeniach.
    """
    missing = [i for i, value in enumerate(row[1:], start=1) if value == "-"]
    values = [float(value) for value in row[1:] if value != "-"]
    return missing, values


def log_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[START] {func.__name__} - {time.strftime('%H:%M:%S')}, {int(time.time() * 1000) % 1000:03d} ms")
        result = func(*args, **kwargs)
        print(f"[END]   {func.__name__} - {time.strftime('%H:%M:%S')}, {int(time.time() * 1000) % 1000:03d} ms")
        return result

    return wrapper


class ETL:
    """Prosty proces ETL oparty na generatorach."""

    def __init__(self, filename: str = "latest.txt"):
        self.filename = filename

    def extract(self):
        """ETAP 1: wczytanie pliku linijka po linijce."""
        return read_lines(self.filename)

    def transform(self, rows):
        """ETAP 2: suma, średnia i indeksy brakujących wartości."""
        for row in rows:
            missing, values = parse_row(row)
            row_sum = sum(values)
            row_avg = row_sum / len(values) if values else 0.0
            yield (row[0], row_sum, row_avg), missing

    def load(self, transformed):
        """ETAP 3: zapis values.csv i missing_values.csv."""
        with open("values.csv", "w", newline="") as values_file, open(
            "missing_values.csv", "w", newline=""
        ) as missing_file:
            values_writer = csv.writer(values_file)
            missing_writer = csv.writer(missing_file)
            values_writer.writerow(["index", "sum", "avg"])
            missing_writer.writerow(["index", "missing"])
            for (idx, row_sum, row_avg), missing in transformed:
                values_writer.writerow([idx, f"{row_sum:.3f}", f"{row_avg:.3f}"])
                missing_writer.writerow([idx, " ".join(map(str, missing))])

    @log_time
    def run(self):
        self.load(self.transform(self.extract()))


if __name__ == "__main__":
    download_file("https://oleksandr-fedoruk.com/sggw/podyplomowe/file")
    ETL().run()
