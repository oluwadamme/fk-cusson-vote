import requests
from faker import Faker
def main():
    

    url = "https://www.cussonsbaby.com.ng/wp-admin/admin-ajax.php"

    payload = {'action': 'baby_competition_vote',
    'entry_id': '282',
    'voter_email': 'bigdee02@gmail.com',
    'nonce': '4d27efc39a',}
    files=[

    ]
    headers = {
    'Cookie': '__cf_bm=Sx4WQh8gkxHhO2dhgDcZIhAVfRxNb1V3i6GiorJLvwI-1767662729-1.0.1.1-rkQXFdFmd3uQN1KGou6maBCHD1i1BcRRJkGBmQdN0xxQDUO1D3CJX3IdhYPg9e8csr4rFUzfLL.qIzaKM6EHY3wgw3mBuxUI4C_teAus4sM; baby_competition_voted=282'
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    print(response.text)
