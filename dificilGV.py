import re
import sys
import pdftotext  # 2.1.6 must be used, pdftotext > 2.1.6 has undesired result
import pandas as pd

from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

### USER OPTIONS

# candidate info, please check for typos
# home: your city to get distance from
# name: your name as surnames and then first name (case insensitive)
#       to get your position (only if pdf with final results is included)
# codes: codes to include in summary, check codes = f(your degree) in 
#        https://ceice.gva.es/documents/162909733/385996069/2024-25_%282%29_PROF.+DE+ENSE%C3%91ANZA+SECUNDARI_ESPECIALIDADES+Y+T%C3%8DTULOS.pdf
# provinces: provinces you want to look for (case insensitive), let's keep valencian and castilian names
CANDIDATE = {
    'home': 'Valencia',
    'name': 'Surname1 Surname2 Name',
    'codes': [
        '206', '207', '209', '219', '236', '237', '264', '266', '269', 
        '272', '273', '276', '292', '2A1', '2A4', '2A8', '2A9', '2B6',
    ],  # example for chemical engineer
    'provinces': [
        'ALACANT', 'CASTELLÓ', 'VALÈNCIA',
        'ALICANTE', 'CASTELLÓN', 'VALENCIA',
    ],
}

### END OF USER OPTIONS

DEBUG = False
DEFAULT_TIMEOUT = 10
IS_WINDOWS = sys.platform.startswith('win') == 'Windows'
CSV_SEPARATOR = ';' if IS_WINDOWS is True else ','
SPECIAL_ALPHANUMERIC_CHARS = ' \(\)A-ZÁÉÍÓÚÀÈÌÒÙÇÜÑ1234567890\'.-'
SPECIAL_ALPHA_CHARS = ' \(\)A-ZÁÉÍÓÚÀÈÌÒÙÇÜÑ\'.-'
DEFAULT_COLUMNS = ['code', 'subject', 'province', 'city', 'city_id', 'distance_km',
                    'school_name', 'school_id', 'hours', 'other']
EXTRA_COLUMNS = ['winner', 'you', 'total', 'groups']

p = f'^ESPECIALIDAD/ESPECIALITAT: (?P<code>[0-9A-Z]{{3}}) (?P<subject>[{SPECIAL_ALPHA_CHARS}]+)'
OFFERT_CODE_PATTERN = re.compile(p, re.MULTILINE | re.ASCII)

province_list = [f'({province.upper()})' for province in CANDIDATE['provinces']]
province_pattern = '|'.join(province_list)
p = f'^PROVÍNCIA/PROVINCIA: (?P<province>{province_pattern})'
OFFERT_PROVINCE_PATTERN = re.compile(p, re.MULTILINE | re.ASCII)

p = f'^(?P<city>[{SPECIAL_ALPHA_CHARS}]+) - (?P<city_id>\d+) - (?P<school_name>[{SPECIAL_ALPHANUMERIC_CHARS}]+) +(?P<school_id>\d+) +(?P<hours>\d+) +(?P<itinerant>[SINO]+) +(?P<other>.*)'
OFFERT_SCHOOL_PATTERN = re.compile(p, re.MULTILINE | re.ASCII)

p = f'^(?P<position>\d+) +(?P<assigned>-->)? +(?P<name>[{SPECIAL_ALPHA_CHARS}]+) *(?P<date>[0-9/]+) (?P<time>[0-9:]+) +(?P<number>[0-9A-Z/]+) +X? +(?P<ranking>\d+) +[SN]? +[SN] +(?P<group>\d) *(?P<place_id>\d+)?'
FINAL_CANDIDATE_PATTERN = re.compile(p, re.MULTILINE | re.ASCII)

p = f'^ +(?P<code>[0-9A-Z]{{3}}) (?P<subject>[{SPECIAL_ALPHA_CHARS}]+)'
FINAL_CODE_PATTERN = re.compile(p, re.MULTILINE | re.ASCII)

p = '^ +PUESTO : +(?P<school_id>\d+) +(?P<city_id>\d+)'
FINAL_PLACE_PATTERN = re.compile(p, re.MULTILINE | re.ASCII)


def print_help():

    print('')
    print('Usage:')
    print('=====')
    print('')
    print(' python dificilGV.py /path/to/offerts.pdf [/path/to/final/results.pdf]')
    print('')
    print(' - offerts.pdf: pdf file with place offerts')
    print(' - results.pdf: pdf file with final results (optional, if included more info is shown in summary)')
    print('')
    print(' Download both pdfs in \'https://ceice.gva.es/es/web/rrhh-educacion/convocatoria-y-peticion-telematica6\'')
    print('')
    print(' Visit GitHub page at https://github.com/girdeux31/dificilGV for more info.')
    print('')

def pdf2str(pdf_file: Path) -> str:
    """
    PURPOSE:

        Convert pdf to text

    MANDATORY ARGUMENTS:

        None
    """
    with open(pdf_file, 'rb') as f:
        pdf = pdftotext.PDF(f)  # pdftotext > 2.1.6 has undesired result
    # read all the text into one string
    # '\n\n' to separate pages in text
    return "\n\n".join(pdf)

def pdf2txt(pdf_file: Path, txt_file: Path) -> None:
    """
    PURPOSE:

        Convert pdf to txt file

    MANDATORY ARGUMENTS:

        None
    """
    text = pdf2str(pdf_file)
    with open(txt_file, 'w') as f:
        f.write(f'{text}')

def coordinates_of(city: str) -> tuple[float]:

    loc = Nominatim(user_agent="GetLoc", timeout=DEFAULT_TIMEOUT).geocode(city)
    if not loc:
        raise ValueError(f'Point \'{city}\' not found')
    return (loc.latitude, loc.longitude)
        
def distance_from_home(city: str) -> float:

    coords = coordinates_of(city)
    return geodesic(home_coordinates, coords).km

def is_in_df(df: pd.DataFrame, code: str, school_id: int, city_id: int) -> bool:

    df = df[(df['code']==code) & (df['school_id']==school_id) & (df['city_id']==city_id)]
    return not df.empty

def get_index(df: pd.DataFrame, code: str, school_id: int, city_id: int) -> list[int]:

    df = df[(df['code']==code) & (df['school_id']==school_id) & (df['city_id']==city_id)]
    return df.index.to_list()

def parse_offert_pdf(file: Path):

    text = pdf2str(file)
    lines = text.split('\n')

    # check that this is the pdf
    if not lines[1].strip().startswith('LLOCS DE DIFÍCIL'):
        raise RuntimeError(f'Wrong format for file \'{file}\'')

    if DEBUG is True:
        pdf2txt(file, file.with_suffix('.txt'))
    
    for line in lines:
        code_match = OFFERT_CODE_PATTERN.search(line)
        province_match = OFFERT_PROVINCE_PATTERN.search(line)
        school_match = OFFERT_SCHOOL_PATTERN.search(line)

        if code_match:
            code = code_match['code'].strip()
            subject = code_match['subject'].strip()

        if province_match:
            province = province_match['province'].strip().upper()

        if school_match:

            if code in CANDIDATE['codes'] and province in CANDIDATE['provinces']:
                city = school_match['city'].strip()
                city_id = school_match['city_id'].strip()
                school_name = school_match['school_name'].strip()
                school_id = school_match['school_id'].strip()
                hours = school_match['hours'].strip()
                # itinerant = school_match['itinerant'].strip()
                other = re.sub(r'\s+', ' ', school_match['other'].strip())
                distance = 0 if DEBUG is True else round(distance_from_home(city))
                row = {'code': code, 'subject': subject,'province': province, 'city': city, 'city_id': city_id, 'distance_km': distance,
                        'school_name': school_name, 'school_id': school_id, 'hours': hours, 'other': other}
                df.loc[len(df)+1] = row

    return df

def parse_final_pdf(file: Path, df: pd.DataFrame):

    idx, last_idx = None, None
    text = pdf2str(file)
    lines = text.split('\n')

    # check that this is the pdf
    if not lines[0].strip().startswith('PARTICIPANTS I LLOC'):
        raise RuntimeError(f'Wrong format for file \'{file}\'')

    if DEBUG is True:
        pdf2txt(file, file.with_suffix('.txt'))
    
    for line in lines:

        code_match = FINAL_CODE_PATTERN.search(line)
        place_match = FINAL_PLACE_PATTERN.search(line)
        candidate_match = FINAL_CANDIDATE_PATTERN.search(line)

        if code_match:
            code = code_match['code'].strip()
            # subject = code_match['subject'].strip()

        if place_match:
            school_id = place_match['school_id'].strip()
            city_id = place_match['city_id'].strip()

            # if this place is in df, then get row index nad if it is a new place reset variables
            if is_in_df(df, code, school_id, city_id):
                idx = get_index(df, code, school_id, city_id)

                if len(idx) > 1:
                    raise ValueError(f'Multiple rows with {(code, school_id, city_id)} entries')

                idx = idx[0]
                new_place = True if idx != last_idx else False

                if new_place:
                    groups = {'1': 0, '2': 0, '3': 0}
                    your_position = None
                    assigned_position = None

                last_idx = idx

            else:
                idx = None

        if idx and candidate_match:
                position = candidate_match['position'].strip()
                assigned = candidate_match['assigned']
                name = candidate_match['name'].strip()
                # date = candidate_match['date'].strip()
                # time = candidate_match['time'].strip()
                # number = candidate_match['number'].strip().split('/')[-1]
                # ranking = candidate_match['ranking'].strip()
                group = candidate_match['group'].strip()
                # place_id = candidate_match['place_id']

                if assigned:
                    df['winner'].loc[idx] = position

                if name.replace(' ', '') == CANDIDATE['name'].replace(' ', '').upper():
                    df['you'].loc[idx] = position

                if int(group) < 4:
                    groups[group] += 1
                
                df['total'].loc[idx] = position
                df['groups'].loc[idx]= f'{groups["1"]}/{groups["2"]}/{groups["3"]}'

    return df
    

if __name__ == '__main__':
    
    if DEBUG is True:
        pdf_offert_file = Path(r'251024/251024_pue_prov.pdf')
        pdf_final_file = None  # Path(r'251024/251024_par.pdf')

    else:
        if len(sys.argv) not in [2, 3]:
            print_help()
            raise RuntimeError('Arguments are missing or incorrect')
        
        pdf_offert_file = Path(sys.argv[1])
        pdf_final_file = Path(sys.argv[2]) if len(sys.argv) == 3 else None

    if not Path(pdf_offert_file).exists():
        raise FileNotFoundError(f'File \'{pdf_offert_file}\' not found')

    if pdf_final_file and not Path(pdf_final_file).exists():
        raise FileNotFoundError(f'File \'{pdf_final_file}\' not found')

    columns = DEFAULT_COLUMNS + EXTRA_COLUMNS if pdf_final_file else DEFAULT_COLUMNS
    df = pd.DataFrame(columns=columns)
    csv_file = pdf_offert_file.with_suffix('.csv')
    home_coordinates = coordinates_of(CANDIDATE['home'])

    print(f'Processing {pdf_offert_file} file ')
    df = parse_offert_pdf(pdf_offert_file)

    if pdf_final_file:
        print(f'Processing {pdf_final_file} file ')
        df = parse_final_pdf(pdf_final_file, df)

    df.to_csv(csv_file, sep=CSV_SEPARATOR, index=False)
    print(f'See summary in \'{csv_file}\'')
