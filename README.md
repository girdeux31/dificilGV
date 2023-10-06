 # dificilGV

## Characteristics

 - Program: dificilGV
 - Version: 1.0
 - Author: Carles Mesado
 - Date: 06/10/2023
 - Size: ~ 5.4 MiB
 
## Purpose

 Get a CSV with summary of hard coverage places in secondary teaching in Generalitat Valenciana (GVA, Spain) only.

## Requirements

Python 3.10 and the following third-party modules:

 - pandas>=2.0.0
 - pdftotext==2.1.6
 - geopy==2.4.0

## Initial configuration

For Unix you may need to install the following packages for pdftotext:

``sudo apt-get install build-essential libpoppler-cpp-dev pkg-config python3-dev``
 
Install modules with pip:

``pip install -r requirements.txt``

## Usage

``python dificilGV.py /path/to/oferts.pdf [/path/to/final/results.pdf]``

 - oferts.pdf: pdf file with place oferts
 - results.pdf: pdf file with final results (optional, if included more info is shown in summary)

 Download both pdfs in https://ceice.gva.es/es/web/rrhh-educacion/resolucion1.

## Examples

``python3 dificilGV.py example/230929_pue_prov.pdf example/230929_par.pdf``

## Candidate

 Tune candidate parameters (city, name, codes, and provinces) in the script from line 14 to 17.

 - City: your city to get distance from, check for typos
 - Name: your name as surnames and then first name, just as in the pdf, check for typos, to get your position
   (only if pdf with final results is included)
 - Codes: list of codes to include in summary, check codes = f(your degree) in
   https://ceice.gva.es/documents/162909733/374747137/2023-24_%282%29_PROF.+DE+ENSE%C3%91ANZA+SECUNDARI_ESPECIALIDADES+Y+T%C3%8DTULOS.pdf
 - Provinces: list of provinces to include in summary, check for typos

## Output

 Columns in CSV are:

 - Code: Subject code, limited to candidate codes supplied in line 16
 - Subject: Subject name according to the code given
 - Province: Province where the school is, provinces can be filtered out according to line 18
 - City: City where the shool is
 - City ID: City ID according to GV
 - Distance: Distance in km to candidate city according to city supplied in line 14
 - School Name: School name
 - School ID:: School ID according to GV
 - Hours: Hours of lectures
 - Other: Other information (type of substitution and requirements)
 - * Winner: Winner position
 - * You: Your position according to you name in line 15
 - * Total: Total number of participants for that place
 - * Groups: Candidates in group 1/group 2/group 3

 (*) Columns are only included if results are supplied through a second input argument as a pdf.

## Bugs

 - Candidates in final result file whose first name is longer than 16 characters are skipped since
   candidate entry (see pattern in 'final_candidate_pattern' is split in two lines and format mixed.
   
## License

This project includes MIT License. A short and simple permissive license with conditions only requiring preservation of copyright and license notices. Licensed works, modifications, and larger works may be distributed under different terms and without source code.

## Contact

Visit GitHub page at https://github.com/girdeux31/dificilGV for more info.

Feel free to contact mesado31@gmail.com for any suggestion or bug.
     
