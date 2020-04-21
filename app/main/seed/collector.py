import datetime
import uuid

from app.main.model.collector import DebtCollector
from app.main import db

def seed_debt_collectors():
    """ Seeds known Debt Collectors """
    # Seeding first 100 known Collectors to get started. Will seed remaining after performing ETL on rest
    debt_collectors = [
        {'name': 'A- 1 Collection Service', 'phone': '6097719200', 'fax': '', 'address': '2297 State Highway 33 Suite 906 ', 'city': 'Hamilton Square', 'state': 'New', 'zip_code':'8690'},
        {'name': 'A R Concepts Inc ', 'phone': '8474264503', 'fax': '8474284059', 'address': '18 E Dundee Rd #330 ', 'city': 'Barrington ', 'state': 'Illinois', 'zip_code': '60010'},
        {'name': 'A&J Collection Agency INC.', 'phone': '7878805046', 'fax': '7878815048', 'address': 'P.O. Box 1010 ', 'city': 'Camuy', 'state': 'Puerto', 'zip_code': '00627'},
        {'name': 'A1 Collections LLC', 'phone': '9702412075', 'fax': '9706835252', 'address': 'PO Box 1929', 'city': 'GRAND JUNCTION', 'state': 'Colorado', 'zip_code': '81502'},
        {'name': 'AA Action Collection', 'phone': '9738459900', 'fax': '', 'address': '517 S Livingston Ave 2nd Floor', 'city': 'Livingston ', 'state': 'New', 'zip_code':'07039'},
        {'name': 'AAMS ', 'phone': '5152247552', 'fax': '5154401080', 'address': '4800 Mills Civic Parkway Suite 202 ', 'city': 'WEST DES MOINES', 'state': 'Iowa', 'zip_code': '50265'},
        {'name': 'Aargon Collection Agency', 'phone': '7022207037', 'fax': '7022207036', 'address': '8668 Spring Mountain Rd.', 'city': 'LAS VEGAS', 'state': 'Nevada', 'zip_code': '89117'},
        {'name': 'Ability Recovery Services, LLC', 'phone': '8552071892', 'fax': '5702072682', 'address': 'PO Box 4262', 'city': 'SCRANTON', 'state': 'Pennsylvania', 'zip_code': '18505'},
        {'name': 'Absolute Resolutions Corp ', 'phone': '', 'fax': '6192953650', 'address': 'PO Box 880306 ', 'city': 'San Diego', 'state': 'California', 'zip_code': '92168'},
        {'name': 'Absolute Resolutions Investments, LLC ', 'phone': '8007130670', 'fax': '', 'address': '8000 Norman Center Drive, Ste. 860 ', 'city': 'Bloomington', 'state': 'Minnesota', 'zip_code': '55437'},
        {'name': 'Accelerated Financial Solutions ', 'phone': '8662468778', 'fax': '8649913198', 'address': 'PO BOX 5714', 'city': 'Greenville ', 'state': 'South', 'zip_code': '29606'},
        {'name': 'Accelerated Receivables Solutions', 'phone': '8883028444', 'fax': '3086323308', 'address': 'PO BOX 70', 'city': 'Scottsbluff', 'state': 'Nebraska', 'zip_code': '69363'},
        {'name': 'Access Receivables Management', 'phone': '4435784448', 'fax': '', 'address': 'Po box 1377', 'city': 'Cockeysville', 'state': 'Maryland', 'zip_code': '21030'},
        {'name': 'Acclaim Credit Technologies', 'phone': '5597417111', 'fax': '', 'address': 'P.O. Box 3028 ', 'city': 'Visalia ', 'state': 'California', 'zip_code': '93277'},
        {'name': 'Account Brokers of Larimer County, Inc', 'phone': '9704947700', 'fax': '3034580912', 'address': '2001 S Shields St #103 Building H', 'city': 'Fort Collins', 'state': 'Colorado', 'zip_code': '80526'},
        {'name': 'Account Control Systems, Inc ', 'phone': '', 'fax': '2017677051', 'address': '148 Veterans Drive, Suite D', 'city': 'Northvale', 'state': 'New', 'zip_code':'07647'},
        {'name': 'Account Control Technology, Inc.', 'phone': '8888307770', 'fax': '5137700601', 'address': 'P.O. Box 471', 'city': 'Kings Mills', 'state': 'Ohio', 'zip_code': '45034'},
        {'name': 'Account Management Resources ', 'phone': '8667232455', 'fax': '', 'address': '726 West Sheridan Ave', 'city': 'Oklahoma City ', 'state': 'Oklahoma', 'zip_code': '73102'},
        {'name': 'ACCOUNT RECOVERY SERVICE', 'phone': '4804832190', 'fax': '4804833754', 'address': 'PO BOX 7648', 'city': 'Goodyear', 'state': 'Arizona', 'zip_code': '85338'},
        {'name': 'Account Recovery Services ', 'phone': '8063538691', 'fax': '8063539833', 'address': '3144 SW 28th Avenue Suite A', 'city': 'Amarillo', 'state': 'Texas', 'zip_code': '79109'},
        {'name': 'Account Recovery Specialist', 'phone': '6202278510', 'fax': '6202276524', 'address': 'PO BOX 136 ', 'city': 'Dodge City ', 'state': 'Kansas', 'zip_code': '67801'},
        {'name': 'Account Resolution Corporation', 'phone': '6367333346', 'fax': '6367333328', 'address': 'PO Box 3860', 'city': 'Chesterfield', 'state': 'Missouri', 'zip_code': '63006'},
        {'name': 'Account Resolution Serv', 'phone': '9543215957', 'fax': '9543273352', 'address': '1643 NW 136th Ave. Building H Suite 100', 'city': 'Fort Lauderdale', 'state': 'Florida', 'zip_code': '33323'},
        {'name': 'Account Resolution Services', 'phone': '8006943048', 'fax': '9543273352', 'address': 'PO BOX 459079 ', 'city': 'Fort Lauderdale', 'state': 'Florida', 'zip_code': '33345'},
        {'name': 'Account Resolution Team INC', 'phone': '4235867613', 'fax': '4235819362', 'address': '221 East Main Street', 'city': 'Morristown ', 'state': 'Tennessee', 'zip_code': '37816'},
        {'name': 'Account Services ', 'phone': '8007775102', 'fax': '2108211234', 'address': '1802 N.E. Loop 410 Suite 400 ', 'city': 'San Antonio', 'state': 'Texas', 'zip_code': '78217'},
        {'name': 'AD Astra Recovery Services Inc', 'phone': '', 'fax': '3167718880', 'address': 'suite 118 7330 W. 33rd street N ', 'city': 'Wichita ', 'state': 'Kansas', 'zip_code': '67205'},
        {'name': 'Adam N Bush Attorneys at Law ', 'phone': '4058892326', 'fax': '', 'address': 'PO BOX 60864', 'city': 'Oklahoma City ', 'state': 'Oklahoma', 'zip_code': '73146'},
        {'name': 'Admin Recovery, LLC ', 'phone': '8667037961', 'fax': '7162768818', 'address': '45 Earhart Drive, Suite 102', 'city': 'Williamsville ', 'state': 'New', 'zip_code': '14221'},
        {'name': 'Advance Bureau of Collections, LLP ', 'phone': '9127427581', 'fax': '4787434643', 'address': '45 Earhart Drive, Suite 102', 'city': 'Macon', 'state': 'Georgia', 'zip_code': '31204'},
        {'name': 'Advanced Call Center Technologies, LLC', 'phone': '8444583451', 'fax': '8666946580', 'address': 'PO Box 9091', 'city': 'Johnson City', 'state': 'Tennessee', 'zip_code': '37615'},
        {'name': 'Advanced Collection Services, Inc', 'phone': '8006400545', 'fax': '2077952227', 'address': 'P.O. Box 7103 ', 'city': 'Lewistonc', 'state': 'Maryland', 'zip_code': '04243'},
        {'name': 'Advanced Recovery Systems ', 'phone': '6013555211', 'fax': '6013551142', 'address': 'Po Box 321472 ', 'city': 'Flowood ', 'state': 'Mississippi', 'zip_code': '39232'},
        {'name': 'Advantage Financial Services, LLC', 'phone': '2082582272', 'fax': '2082582277', 'address': '10 S Cole Road', 'city': 'Boise', 'state': 'Idaho', 'zip_code': '83709'},
        {'name': 'Affiliate Asset Solutions, LLC', 'phone': '8558205237', 'fax': '6785674368', 'address': '145 Technology Parkway NW, Suite 100', 'city': 'Peachtree Corners', 'state': 'Georgia', 'zip_code': '30092'},
        {'name': 'Affiliated Credit Services', 'phone': '', 'fax': '6516952488', 'address': 'P.O. Box 7739 ', 'city': 'Rochester', 'state': 'Minnesota', 'zip_code': '55903'},
        {'name': 'AFNI Collections ', 'phone': '3098285226', 'fax': '3098207055', 'address': '1310 Martin Luther King Drive ', 'city': 'Bloomington', 'state': 'Illinois', 'zip_code': '61702'},
        {'name': 'Agency Credit Control', 'phone': '3037575147', 'fax': '8669281906', 'address': '2014 S Pontiac Way', 'city': 'Denver', 'state': 'Colorado', 'zip_code': '80224'},
        {'name': 'Albuquerque Collection Services ', 'phone': '5052653476', 'fax': '5052665808', 'address': '110 Richmond SE', 'city': 'Albuquerque', 'state': 'New', 'zip_code':'87194'},
        {'name': 'Aldous and Associates, PLLC', 'phone': '8882215155', 'fax': '', 'address': 'Po Box 171374 ', 'city': 'Holladay', 'state': 'Utah', 'zip_code': '84117'},
        {'name': 'Aldridge Pite Haan, LLP', 'phone': '4702403440', 'fax': '6195901385', 'address': 'PO Box 52815', 'city': 'Atlanta ', 'state': 'Georgia', 'zip_code': '30355'},
        {'name': 'Aldridge, Hammar & Wexler, P.A. ', 'phone': '', 'fax': '5052554029', 'address': '1212 Pennsylvania NE', 'city': 'Albuquerque', 'state': 'New', 'zip_code':'87110'},
        {'name': 'Alliance Collection Agencies, Inc. ', 'phone': '7153847107', 'fax': '7153849230', 'address': '3916 S. Business Park Ave.', 'city': 'Marshfield ', 'state': 'Wisconsin', 'zip_code': '54449'},
        {'name': 'Alliance Collection Services Inc', 'phone': '8887643449', 'fax': '', 'address': 'P.O. Box 49', 'city': 'Tupelo', 'state': 'Mississippi', 'zip_code': '38802'},
        {'name': 'Alliance N, Receivables Management, Inc.', 'phone': '8665442755', 'fax': '2153967255', 'address': '4850 Street Road, Ste. 300', 'city': 'Trevose ', 'state': 'Pennsylvania', 'zip_code': '19053'},
        {'name': 'Allied Account Services', 'phone': '5087923990', 'fax': '', 'address': '90 Madison Street Suite 302', 'city': 'Worcester', 'state': 'Massachusetts', 'zip_code':'1608'},
        {'name': 'Allied Business Services', 'phone': '8883819616', 'fax': '6167416501', 'address': '400 Allied Court ', 'city': 'Zeeland ', 'state': 'Michigan', 'zip_code': '49464'},
        {'name': 'Allied Collection Services of California ', 'phone': '8182214900', 'fax': '8189333383', 'address': 'Allied Collection Services of California ', 'city': 'Northridge ', 'state': 'California', 'zip_code': '91325'},
        {'name': 'Allied Collection Services, Inc.', 'phone': '7027375506', 'fax': '', 'address': 'Allied Collection Services, Inc.', 'city': 'LAS VEGAS', 'state': 'Nevada', 'zip_code': '89117'},
        {'name': 'Allied International Credit Corporation', 'phone': '', 'fax': '9054708155', 'address': '6800 Paragon Place, Suite400 ', 'city': 'Richmond', 'state': 'Virginia', 'zip_code': '23230'},
        {'name': 'Allied Interstate LLC', 'phone': '8668756562', 'fax': '9736307015', 'address': '7525 West Campus Road', 'city': 'New Albany ', 'state': 'Ohio', 'zip_code': '43054'},
        {'name': 'Alltran Financial , LP ', 'phone': '8887390745', 'fax': '7139770119', 'address': 'PO Box 722910 ', 'city': 'Houston ', 'state': 'Texas', 'zip_code': '77272'},
        {'name': 'Alltran Health, Inc.', 'phone': '8446176998', 'fax': '3202537860', 'address': 'Po Box 519 ', 'city': 'Sauk Rapids', 'state': 'Minnesota', 'zip_code': '56379'},
        {'name': 'Ally Asset Recovery Center', 'phone': '', 'fax': '6023811225', 'address': 'Po Box 78369', 'city': 'Phoenix ', 'state': 'Arizona', 'zip_code': '85062'},
        {'name': 'ALPHA RECOVERY CORP ', 'phone': '8773598714', 'fax': '8666306881', 'address': '5660 Greenwood Plaza Blvd, Suite 101', 'city': 'Greenwood Village', 'state': 'Colorado', 'zip_code': '80111'},
        {'name': 'ALPINE CREDIT INC', 'phone': '3032399100', 'fax': '3032399077', 'address': '12191 W 64th Ave STE 210, ', 'city': 'Arvada', 'state': 'Colorado', 'zip_code': '80004'},
        {'name': 'Alternative Recovery Management ', 'phone': '6194696194', 'fax': '6194699956', 'address': '7373 University Ave Ste 209', 'city': 'La Mesa ', 'state': 'California', 'zip_code': '91942'},
        {'name': 'AMCA Collection Agency ', 'phone': '8445152622', 'fax': '9149928935', 'address': '4 Westchester Plaza, building 4 ', 'city': 'Elmsford', 'state': 'New', 'zip_code': '10523'},
        {'name': 'AMCOL Systems ', 'phone': '8032173800', 'fax': '8032173204', 'address': 'PO BOX 21625', 'city': 'Columbia', 'state': 'South', 'zip_code': '29221'},
        {'name': 'AMERASSIST AR SOLUTIONS INC', 'phone': '6146351290', 'fax': '8779006300', 'address': 'PO BOX 26095 # 500', 'city': 'Columbus', 'state': 'Ohio', 'zip_code': '43226'},
        {'name': 'American Adjustment Bureau, Inc.', 'phone': '8664805562', 'fax': '8443671789', 'address': '73 Fields Street ', 'city': 'Waterbury', 'state': 'Conneticut', 'zip_code': '06702'},
        {'name': 'American Capital Enterprises ', 'phone': '9516953372', 'fax': '', 'address': 'PO Box 893580 ', 'city': 'Temecula', 'state': 'California', 'zip_code': '92589'},
        {'name': 'American Collections Enterprise, Inc', 'phone': '7032537000', 'fax': '7037199587', 'address': 'PO BOX 30096', 'city': 'Alexandria ', 'state': 'Virginia', 'zip_code': '22310'},
        {'name': 'American Coradius International LLC', 'phone': '8884007793', 'fax': '7166897084', 'address': '2420 Sweet Home Road, Ste 150', 'city': 'Amherst ', 'state': 'New', 'zip_code': '14228'},
        {'name': 'American Credit Bureau ', 'phone': '8007509422', 'fax': '8003613888', 'address': '1200 N Federal Highway ', 'city': 'Boca Raton ', 'state': 'Florida', 'zip_code': '33427'},
        {'name': 'American Credit Systems', 'phone': '6309805500', 'fax': '6309808642', 'address': '400 West Lake Street Suite 111', 'city': 'Roselle ', 'state': 'Illinios', 'zip_code': '60172'},
        {'name': 'American Management Services ', 'phone': '4056036474', 'fax': '', 'address': 'PO BOX 44069', 'city': 'OKLAHOMA CITY ', 'state': 'Oklahoma', 'zip_code': '73144'},
        {'name': 'American Medical Collection Agency ', 'phone': '8445152622', 'fax': '9149928935', 'address': '4 Westchester Plaza Suite 110', 'city': 'Elmsford', 'state': 'New', 'zip_code': '10523'},
        {'name': 'American Profit Recovery', 'phone': '8776348900', 'fax': '2489481254', 'address': '33 Boston Post Road W #140', 'city': 'Marlborough', 'state': 'Massachusetts', 'zip_code': '01752'},
        {'name': 'American Recovery Service Inc.', 'phone': '8053798500', 'fax': '8053798530', 'address': '555 Street Charles Drive, Suite 100', 'city': 'Thousand Oaks ', 'state': 'California', 'zip_code': '91360'},
        {'name': 'Americollect, Inc.', 'phone': '8886820396', 'fax': '9206820313', 'address': 'PO Box 1566', 'city': 'Manitowoc', 'state': 'Wisconsin', 'zip_code': '54221'},
        {'name': 'AmeriFinancial Solutions, LLC', 'phone': '8007537100', 'fax': '4437536097', 'address': 'P.O. Box 65018', 'city': 'BALTIMORE', 'state': 'Maryland', 'zip_code': '21264'},
        {'name': 'AmeriMark Direct LLC', 'phone': '8008165310', 'fax': '4402348925', 'address': '100 Nixon Lane', 'city': 'Edison', 'state': 'New', 'zip_code':'08837'},
        {'name': 'Amo Recoveries', 'phone': '8662460758', 'fax': '', 'address': '19401 40th Ave W #130', 'city': 'Lynnwood', 'state': 'Washington', 'zip_code': '98036'},
        {'name': 'Amsher Collection Services Inc', 'phone': '8779361171', 'fax': '2052510448', 'address': '4524 Southlake Pkwy Ste. 15', 'city': 'Hoover', 'state': 'Alabama', 'zip_code': '35244'},
        {'name': 'Andreu, Palma, Lavin & Solis, PLLC ', 'phone': '3056310175', 'fax': '3056311816', 'address': '1000 NW 57th Court Suite 400 ', 'city': 'Miami', 'state': 'Florida', 'zip_code': '33126'},
        {'name': 'Apelles ', 'phone': '', 'fax': '6148992733', 'address': '3700 corporate drive suite 240', 'city': 'Columbus', 'state': 'Ohio', 'zip_code': '43231'},
        {'name': 'Apex Asset Management', 'phone': '7175191770', 'fax': '8885922149', 'address': '2501 Oregon Pike Suite 120', 'city': 'Lancaster', 'state': 'Pennsylvania', 'zip_code': '17601'},
        {'name': 'Apothaker Scian P.C ', 'phone': '8006720215', 'fax': '8007574928', 'address': '520 Fellowship Road Suite C306', 'city': 'Mt. Laurel ', 'state': 'New', 'zip_code':'08054'},
        {'name': 'AR Resources, Inc', 'phone': '8663010222', 'fax': '2674640299', 'address': 'PO Box 1056', 'city': 'Blue Bell', 'state': 'Pennsylvania', 'zip_code': '19422'},
        {'name': 'Arbor Professional Solutions ', 'phone': '8007416955', 'fax': '7346692119', 'address': '2090 South MAIN STREET ', 'city': 'Ann arbor', 'state': 'Michigan', 'zip_code': '48103'},
        {'name': 'Arcadia Recovery Bureau, llc ', 'phone': '', 'fax': '4082971426', 'address': 'po box 70256', 'city': 'Philadelphia', 'state': 'Pennsylvania', 'zip_code': '19176'},
        {'name': 'ARS National Services, Inc.', 'phone': '8009760960', 'fax': '8664220765', 'address': 'PO Box 463023 ', 'city': 'Escondido', 'state': 'California', 'zip_code': '92046'},
        {'name': 'ASSET RECOVERY SOLUTIONS, LLC', 'phone': '8886789006', 'fax': '8477890007', 'address': '2200 Devon Avenue Suite #200 ', 'city': 'Des Plaines', 'state': 'Illinois', 'zip_code': '60018'},
        {'name': 'AssetCare', 'phone': '8889933596', 'fax': '9037713629', 'address': '2222 Texoma Pkwy , Ste 180', 'city': 'Sherman ', 'state': 'Texas', 'zip_code': '75090'},
        {'name': 'Associated Collectors, Inc', 'phone': '6087544425', 'fax': '6087540637', 'address': 'PO BOX 1039', 'city': 'Janesville ', 'state': 'Wisconsin', 'zip_code': '53547'},
        {'name': 'Associated Credit Services Inc', 'phone': '', 'fax': '5083660222', 'address': 'po box 5171', 'city': 'Westborough', 'state': 'Massachusetts', 'zip_code': '01581'},
        {'name': 'ATG Credit LLC', 'phone': '8009694523', 'fax': '7732276870', 'address': 'po box 14895', 'city': 'Chicago ', 'state': 'Illinois', 'zip_code': '60614'},
        {'name': 'Atkins & Ogle Law Office, L.C.', 'phone': '3049374919', 'fax': '3049374986', 'address': 'P.O. Box 300 105 River Vista Dr. ', 'city': 'Buffalo ', 'state': 'West', 'zip_code':'25033'},
        {'name': 'Atlantic Collection Agency, Inc.', 'phone': '8004909026', 'fax': '8606910567', 'address': '194 Boston Post Road', 'city': 'East Lyme', 'state': 'Conneticut', 'zip_code': '06333'},
        {'name': 'Atlantic Credit and Finance Inc.', 'phone': '5407727800', 'fax': '5407727895', 'address': 'PO Box 11887', 'city': 'Roanoke ', 'state': 'Virginia', 'zip_code': '24022'},
        {'name': 'Atlantic Recovery Solutions', 'phone': '', 'fax': '7166890760', 'address': 'po box 156 ', 'city': 'Eash Amherst', 'state': 'New', 'zip_code': '14051'},
        {'name': 'Automated Accounts', 'phone': '5092521041', 'fax': '5092522815', 'address': '430 W. Sharp Ave ', 'city': 'Spokane ', 'state': 'Washington', 'zip_code': '99201'},
        {'name': 'Autovest LLC', 'phone': '8002218160', 'fax': '2483592664', 'address': 'Po box 2247', 'city': 'Southfield ', 'state': 'Michigan', 'zip_code': '48037'},
        {'name': 'Avant, LLC ', 'phone': '8007125407', 'fax': '8666250930', 'address': '222 North LaSalle Street  Suite 1700', 'city': 'Chicago ', 'state': 'Illinois', 'zip_code': '60601'},
        {'name': 'AVANTE USA ', 'phone': '8324761739', 'fax': '2818726261', 'address': '3600 south gessner suite 225 ', 'city': 'Houston ', 'state': 'Texas', 'zip_code': '77063'},
        {'name': 'AWA COLLECTIONS', 'phone': '', 'fax': '7147715999', 'address': 'po box 6605', 'city': 'Orange', 'state': 'California', 'zip_code': '92856'},
        {'name': 'Axiom Acquisition Ventures LLC', 'phone': '7277244200', 'fax': '8137746008', 'address': '12425 Race Track Rd #100', 'city': 'Tampa', 'state': 'Florida', 'zip_code': '33626'},
        {'name': 'B & P Collection Service', 'phone': '7753334255', 'fax': '', 'address': '816 Center St ', 'city': 'Reno ', 'state': 'Nevada', 'zip_code': '89501'},
        {'name': 'Bay Area Credit Service', 'phone': '6782295010', 'fax': '7707179085', 'address': '4145 Shackleford Rd Suite 330B', 'city': 'Nocross ', 'state': 'Georgia', 'zip_code': '30095'}
    ]

    for collector_item in debt_collectors:
        existing_collector = DebtCollector.query.filter_by(name=collector_item['name']).first()
        if not existing_collector:
            print(f"Phone is {collector_item['phone']}, Fax is {collector_item['fax']}, and Zip Code is {collector_item['zip_code']}")
            new_collector = DebtCollector(
                public_id= str(uuid.uuid4()),
                name=collector_item['name'],
                phone=collector_item['phone'],
                fax=collector_item['fax'],
                address=collector_item['address'],
                city=collector_item['city'],
                state=collector_item['state'],
                zip_code=collector_item['zip_code'],
                inserted_on= datetime.datetime.utcnow(),
                updated_on= datetime.datetime.utcnow()
            )
            db.session.add(new_collector)

    db.session.commit()