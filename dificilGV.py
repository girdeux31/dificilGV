import re
import sys
import pdftotext
import pandas as pd

from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

candidate = dict()

### USER OPTIONS

# your city to get distance from, check for typos
candidate['home'] = 'Valencia'

# your name as surnames and then first name, just as in the pdf, check for typos, to get your position (only if pdf with final results is included)
candidate['name'] = 'Surname1 Surname2 Firstname'

# codes to include in summary, check codes = f(your degree) in https://ceice.gva.es/documents/162909733/374747137/2023-24_%282%29_PROF.+DE+ENSE%C3%91ANZA+SECUNDARI_ESPECIALIDADES+Y+T%C3%8DTULOS.pdf
candidate['codes'] = ['206', '207', '209', '219', '236', '237', '264', '266', '269', '272', '273', '276', '292', '2A1', '2A4', '2A8', '2A9', '2B6']  # example for chemical engineer

# provinces to include in summary, check for typos
candidate['provinces'] = ['Alacant', 'Castelló', 'València']

### END OF USER OPTIONS

debug = False
special_alphanumeric_chars = ' \(\)A-ZÁÉÍÓÚÀÈÌÒÙÇÜÑ1234567890\'.-'
special_alpha_chars = ' \(\)A-ZÁÉÍÓÚÀÈÌÒÙÇÜÑ\'.-'
default_columns = ['code', 'subject', 'province', 'city', 'city_id', 'distance',
                    'school_name', 'school_id', 'hours', 'other']
extra_columns = ['winner', 'you', 'total', 'groups']

p = '^ESPECIALIDAD/ESPECIALITAT: (?P<code>[0-9A-Z]{3}) (?P<subject>[' + special_alpha_chars + ']+)'
ofert_code_pattern = re.compile(p, re.MULTILINE | re.ASCII)

p = '^PROVÍNCIA/PROVINCIA: (?P<province>(Alacant)|(València)|(Castelló))'
ofert_province_pattern = re.compile(p, re.MULTILINE | re.ASCII)

p = '^(?P<city>[' + special_alpha_chars + ']+) - (?P<city_id>\d+) - (?P<school_name>[' + special_alphanumeric_chars + ']+) +(?P<school_id>\d+) (?P<hours>\d+) +(?P<itinerant>[SINO]+) +(?P<other>.*)'
ofert_school_pattern = re.compile(p, re.MULTILINE | re.ASCII)

p = '^(?P<position>\d+) +(?P<assigned>-->)? +(?P<name>[' + special_alpha_chars + ']+) *(?P<date>[0-9/]+) (?P<time>[0-9:]+) +(?P<number>[0-9A-Z/]+) +X? +(?P<ranking>\d+) +[SN]? +[SN] +(?P<group>\d) *(?P<place_id>\d+)?'
final_candidate_pattern = re.compile(p, re.MULTILINE | re.ASCII)

p = '^ +(?P<code>[0-9A-Z]{3}) (?P<subject>[' + special_alpha_chars + ']+)'
final_code_pattern = re.compile(p, re.MULTILINE | re.ASCII)

p = '^ +PUESTO : +(?P<school_id>\d+) +(?P<city_id>\d+)'
final_place_pattern = re.compile(p, re.MULTILINE | re.ASCII)


def print_help():

    print('')
    print('Usage:')
    print('=====')
    print('')
    print(' python dificilGV.py /path/to/oferts.pdf [/path/to/final/results.pdf]')
    print('')
    print(' - oferts.pdf: pdf file with place oferts')
    print(' - results.pdf: pdf file with final results (optional, if included more info is shown in summary)')
    print('')
    print(' Download both pdfs in \'https://ceice.gva.es/es/web/rrhh-educacion/resolucion1\'')
    print('')
    print(' Visit GitHub page at https://github.com/girdeux31/dificilGV for more info.')
    print('')

def pdf2str(pdf_file):
    """
    PURPOSE:

        Convert pdf to text

    MANDATORY ARGUMENTS:

        None
    """
    with open(pdf_file, 'rb') as f:
        pdf = pdftotext.PDF(f)  # pdftotext 2.2.x has undisered result

    # read all the text into one string
    # '\n\n' to separate pages in text
    return "\n\n".join(pdf)

def pdf2txt(pdf_file, txt_file):
    """
    PURPOSE:

        Convert pdf to txt file

    MANDATORY ARGUMENTS:

        None
    """
    text = pdf2str(pdf_file)

    with open(txt_file, 'w') as f:
        f.write(f'{text}')

def coordinates_of(point):

    loc = Nominatim(user_agent="GetLoc").geocode(point)

    if not loc:
        raise ValueError(f'Point \'{point}\' not found')

    return (loc.latitude, loc.longitude)
        
def distance_from_home(point):

    coords = coordinates_of(point)

    return geodesic(home_coordinates, coords).km

def is_in_df(df, code, school_id, city_id):

    df = df[(df['code']==code) & (df['school_id']==school_id) & (df['city_id']==city_id)]

    return not df.empty

def get_index(df, code, school_id, city_id):

    df = df[(df['code']==code) & (df['school_id']==school_id) & (df['city_id']==city_id)]
    
    return df.index.to_list()

def parse_ofert_pdf(file, debug=False):

    text = pdf2str(file)
    lines = text.split('\n')

    # check that this is the pdf
    if not lines[1].strip().startswith('LLOCS DE DIFÍCIL'):
        raise RuntimeError(f'Wrong format for file \'{file}\'')

    if debug:
        pdf2txt(file, file.replace('.pdf', '.txt'))
    
    for line in lines:

        code_match = ofert_code_pattern.search(line)
        province_match = ofert_province_pattern.search(line)
        school_match = ofert_school_pattern.search(line)

        if code_match:
            
            code = code_match['code'].strip()
            subject = code_match['subject'].strip()

        if province_match:
            province = province_match['province'].strip()

        if school_match:

            if code in candidate['codes'] and province in candidate['provinces']:

                city = school_match['city'].strip()
                city_id = school_match['city_id'].strip()
                school_name = school_match['school_name'].strip()
                school_id = school_match['school_id'].strip()
                hours = school_match['hours'].strip()
                # itinerant = school_match['itinerant'].strip()
                other = school_match['other'].strip()
                
                distance = 0 if debug else round(distance_from_home(city))

                row = {'code': code, 'subject': subject,'province': province, 'city': city, 'city_id': city_id, 'distance': distance,
                        'school_name': school_name, 'school_id': school_id, 'hours': hours, 'other': other}
                        
                df.loc[len(df)+1] = row

    return df

def parse_final_pdf(file, df, debug=False):

    idx, last_idx = None, None

    text = pdf2str(file)
    lines = text.split('\n')

    # check that this is the pdf
    if not lines[0].strip().startswith('PARTICIPANTS I LLOC'):
        raise RuntimeError(f'Wrong format for file \'{file}\'')

    if debug:
        pdf2txt(file, file.replace('.pdf', '.txt'))
    
    for line in lines:

        code_match = final_code_pattern.search(line)
        place_match = final_place_pattern.search(line)
        candidate_match = final_candidate_pattern.search(line)

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

                if name.replace(' ', '') == candidate['name'].replace(' ', '').upper():
                    df['you'].loc[idx] = position

                if int(group) < 4:
                    groups[group] += 1
                
                df['total'].loc[idx] = position
                df['groups'].loc[idx]= f'{groups["1"]}/{groups["2"]}/{groups["3"]}'

    return df
    

if __name__ == '__main__':
    
    if debug:

        pdf_ofert_file = f'example/230929_pue_prov.pdf'
        pdf_final_file = f'example/230929_par.pdf'

    else:

        if len(sys.argv) == 2:
            pdf_ofert_file = sys.argv[1]
            pdf_final_file = None
        elif len(sys.argv) == 3:
            pdf_ofert_file = sys.argv[1]
            pdf_final_file = sys.argv[2]
        else:
            print_help()
            raise RuntimeError('Arguments are missing or incorrect')

    if not Path(pdf_ofert_file).exists():
        raise FileNotFoundError(f'File \'{pdf_ofert_file}\' not found')

    if pdf_final_file and not Path(pdf_final_file).exists():
        raise FileNotFoundError(f'File \'{pdf_final_file}\' not found')

    columns = default_columns + extra_columns if pdf_final_file else default_columns
    df = pd.DataFrame(columns=columns)
    csv_file = pdf_ofert_file.replace('.pdf', '.csv')
    home_coordinates = coordinates_of(candidate['home'])

    df = parse_ofert_pdf(pdf_ofert_file, debug=debug)

    if pdf_final_file:
        df = parse_final_pdf(pdf_final_file, df, debug=debug)

    df.to_csv(csv_file, sep='\t')

    print(f'See summary in \'{csv_file}\'')
