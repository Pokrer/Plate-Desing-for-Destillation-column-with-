import numpy as np


class CEPCI:
    # Datos de años y sus respectivos índices CEPCI desde 1958 hasta el año más reciente disponible (2023)
    years = np.array([
        1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970,
        1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982,
        1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994,
        1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006,
        2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018,
        2019, 2020, 2021, 2022, 2023
    ])

    cepci_indices = np.array([
        103.8, 108.4, 112.5, 114.4, 117.3, 119.0, 121.0, 123.7, 125.7, 127.9,
        131.1, 135.2, 140.2, 144.8, 171.3, 203.2, 227.3, 223.1, 229.1, 254.1,
        297.0, 318.4, 355.4, 390.6, 389.5, 394.1, 390.0, 357.6, 358.2, 381.1,
        400.0, 418.1, 394.3, 381.1, 359.2, 368.1, 381.7, 381.1, 386.5, 389.5,
        412.0, 394.0, 395.6, 402.0, 416.2, 468.2, 500.0, 509.0, 525.4, 556.8,
        584.6, 607.5, 585.7, 607.5, 585.7, 595.2, 556.8, 558.2, 550.8, 556.8,
        567.5, 603.1, 596.2, 596.1, 689.9, 708.0, 725.8, 739.3, 785.6
    ])

    @staticmethod
    def adjust_for_inflation_walas(value):
        start_year = 1964
        if start_year not in CEPCI.years:
            raise ValueError("Año de inicio fuera del rango de los datos disponibles.")

        # Índice CEPCI para el año de inicio (1964)
        start_index = CEPCI.cepci_indices[np.where(CEPCI.years == start_year)][0]
        # Índice CEPCI para el año más reciente (2023)
        end_index = CEPCI.cepci_indices[-1]

        # Ajuste del valor según la inflación
        adjusted_value = value * (end_index / start_index)
        return adjusted_value

    @staticmethod
    def adjust_for_inflation_sinot(value):
        start_year = 1980
        if start_year not in CEPCI.years:
            raise ValueError("Año de inicio fuera del rango de los datos disponibles.")

        # Índice CEPCI para el año de inicio (1980)
        start_index = CEPCI.cepci_indices[np.where(CEPCI.years == start_year)][0]
        # Índice CEPCI para el año más reciente (2023)
        end_index = CEPCI.cepci_indices[-1]

        # Ajuste del valor según la inflación
        adjusted_value = value * (end_index / start_index)
        return adjusted_value