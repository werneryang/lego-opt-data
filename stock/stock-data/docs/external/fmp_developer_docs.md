# Financial Modeling Prep API 离线手册 (含 Python 源码)
# 需要 FMP API Key的权限！！！


## Stock Symbol SearchAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-symbol

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| query * | string | AAPL |
| limit | number | 50 |
| exchange | string | NASDAQ |


## Company Name SearchAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-name

### Endpoint

https://financialmodelingprep.com/stable/search-name?query=AA&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| query * | string | AA |
| limit | number | 50 |
| exchange | string | NASDAQ |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/search-name?query=AA
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAGUSD",
    "name": "AAG USD",
    "currency": "USD",
    "exchangeFullName": "CCC",
    "exchange": "CRYPTO"
  }
]
```


## CIKAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-cik

### Endpoint

https://financialmodelingprep.com/stable/search-cik?cik=320193&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| cik * | string | 320193 |
| limit | number | 50 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/search-cik?cik=320193
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "companyName": "Apple Inc.",
    "cik": "0000320193",
    "exchangeFullName": "NASDAQ Global Select",
    "exchange": "NASDAQ",
    "currency": "USD"
  }
]
```


## CUSIPAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-cusip

### Endpoint

https://financialmodelingprep.com/stable/search-cusip?cusip=037833100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| cusip * | string | 037833100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/search-cusip?cusip=037833100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "companyName": "Apple Inc.",
    "cusip": "037833100",
    "marketCap": 3542555295744
  }
]
```


## ISINAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-isin

### Endpoint

https://financialmodelingprep.com/stable/search-isin?isin=US0378331005&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| isin * | string | US0378331005 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/search-isin?isin=US0378331005
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "isin": "US0378331005",
    "marketCap": 3427916386000
  }
]
```


## Stock ScreenerAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-company-screener

### Endpoint

https://financialmodelingprep.com/stable/company-screener?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| marketCapMoreThan | number | 1000000 |
| marketCapLowerThan | number | 1000000000 |
| sector | string | Technology |
| industry | string | Consumer Electronics |
| betaMoreThan | number | 0.5 |
| betaLowerThan | number | 1.5 |
| priceMoreThan | number | 10 |
| priceLowerThan | number | 200 |
| dividendMoreThan | number | 0.5 |
| dividendLowerThan | number | 2 |
| volumeMoreThan | number | 1000 |
| volumeLowerThan | number | 1000000 |
| exchange | string | NASDAQ |
| country | string | US |
| isEtf | boolean | false |
| isFund | boolean | false |
| isActivelyTrading | boolean | true |
| limit | number | 1000 |
| includeAllShareClasses | boolean | false |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/company-screener
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "companyName": "Apple Inc.",
    "marketCap": 3435062313000,
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "beta": 1.24,
    "price": 225.93,
    "lastAnnualDividend": 1,
    "volume": 43010091,
    "exchange": "NASDAQ Global Select",
    "exchangeShortName": "NASDAQ",
    "country": "US",
    "isEtf": false,
    "isFund": false,
    "isActivelyTrading": true
  }
]
```


## Exchange VariantsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-exchange-variants

### Endpoint

https://financialmodelingprep.com/stable/search-exchange-variants?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/search-exchange-variants?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "price": 225.46,
    "beta": 1.24,
    "volAvg": 54722288,
    "mktCap": 3427916386000,
    "lastDiv": 1,
    "range": "164.08-237.23",
    "changes": -7.54,
    "companyName": "Apple Inc.",
    "currency": "USD",
    "cik": "0000320193",
    "isin": "US0378331005",
    "cusip": "037833100",
    "exchange": "NASDAQ Global Select",
    "exchangeShortName": "NASDAQ",
    "industry": "Consumer Electronics",
    "website": "https://www.apple.com",
    "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allow customers to discov...",
    "ceo": "Mr. Timothy D. Cook",
    "sector": "Technology",
    "country": "US",
    "fullTimeEmployees": "161000",
    "phone": "408 996 1010",
    "address": "One Apple Park Way",
    "city": "Cupertino",
    "state": "CA",
    "zip": "95014",
    "dcfDiff": 62.45842,
    "dcf": 161.68157666868984,
    "image": "https://financialmodelingprep.com/image-stock/AAPL.png",
    "ipoDate": "1980-12-12",
    "defaultImage": false,
    "isEtf": false,
    "isActivelyTrading": true,
    "isAdr": false,
    "isFund": false
  }
]
```


## Company Symbols ListAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/company-symbols-list

### Endpoint

https://financialmodelingprep.com/stable/stock-list?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/stock-list
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "6898.HK",
    "companyName": "China Aluminum Cans Holdings Limited"
  }
]
```


## Financial Statement Symbols ListAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/financial-symbols-list

### Endpoint

https://financialmodelingprep.com/stable/financial-statement-symbol-list?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/financial-statement-symbol-list
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "6898.HK",
    "companyName": "China Aluminum Cans Holdings Limited",
    "tradingCurrency": "HKD",
    "reportingCurrency": "HKD"
  }
]
```


## CIK ListAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cik-list

### Endpoint

https://financialmodelingprep.com/stable/cik-list?page=0&limit=1000&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| page | number | 0 |
| limit | number | 1000 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/cik-list?page=0&limit=1000
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0002036063",
    "companyName": "LUZ Capital Partners, LLC"
  }
]
```


## Symbol Changes ListAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/symbol-changes-list

### Endpoint

https://financialmodelingprep.com/stable/symbol-change?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| invalid | string | false |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/symbol-change
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-03",
    "companyName": "XPLR Infrastructure, LP Common Units representing limited partner interests",
    "oldSymbol": "NEP",
    "newSymbol": "XIFR"
  }
]
```


## ETF Symbol SearchAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/etfs-list

### Endpoint

https://financialmodelingprep.com/stable/etf-list?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/etf-list
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "GULF",
    "name": "WisdomTree Middle East Dividend Fund"
  }
]
```


## Actively Trading ListAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/actively-trading-list

### Endpoint

https://financialmodelingprep.com/stable/actively-trading-list?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/actively-trading-list
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "6898.HK",
    "name": "China Aluminum Cans Holdings Limited"
  }
]
```


## Earnings Transcript ListAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/earnings-transcript-list

### Endpoint

https://financialmodelingprep.com/stable/earnings-transcript-list?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/earnings-transcript-list
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "MCUJF",
    "companyName": "Medicure Inc.",
    "noOfTranscripts": "16"
  }
]
```


## Available ExchangesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/available-exchanges

### Endpoint

https://financialmodelingprep.com/stable/available-exchanges?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/available-exchanges
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "exchange": "AMEX",
    "name": "New York Stock Exchange Arca",
    "countryName": "United States of America",
    "countryCode": "US",
    "symbolSuffix": "N/A",
    "delay": "Real-time"
  }
]
```


## Available SectorsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/available-sectors

### Endpoint

https://financialmodelingprep.com/stable/available-sectors?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/available-sectors
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "sector": "Basic Materials"
  }
]
```


## Available IndustriesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/available-industries

### Endpoint

https://financialmodelingprep.com/stable/available-industries?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/available-industries
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "industry": "Steel"
  }
]
```


## Available CountriesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/available-countries

### Endpoint

https://financialmodelingprep.com/stable/available-countries?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/available-countries
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "country": "FK"
  }
]
```


## Company Profile DataAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/profile-symbol

### Endpoint

https://financialmodelingprep.com/stable/profile?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/profile?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "price": 232.8,
    "marketCap": 3500823120000,
    "beta": 1.24,
    "lastDividend": 0.99,
    "range": "164.08-260.1",
    "change": 4.79,
    "changePercentage": 2.1008,
    "volume": 0,
    "averageVolume": 50542058,
    "companyName": "Apple Inc.",
    "currency": "USD",
    "cik": "0000320193",
    "isin": "US0378331005",
    "cusip": "037833100",
    "exchangeFullName": "NASDAQ Global Select",
    "exchange": "NASDAQ",
    "industry": "Consumer Electronics",
    "website": "https://www.apple.com",
    "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allow customers to discov...",
    "ceo": "Mr. Timothy D. Cook",
    "sector": "Technology",
    "country": "US",
    "fullTimeEmployees": "164000",
    "phone": "(408) 996-1010",
    "address": "One Apple Park Way",
    "city": "Cupertino",
    "state": "CA",
    "zip": "95014",
    "image": "https://images.financialmodelingprep.com/symbol/AAPL.png",
    "ipoDate": "1980-12-12",
    "defaultImage": false,
    "isEtf": false,
    "isActivelyTrading": true,
    "isAdr": false,
    "isFund": false
  }
]
```


## Company Profile by CIKAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/profile-cik

### Endpoint

https://financialmodelingprep.com/stable/profile-cik?cik=320193&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| cik * | string | 320193 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/profile-cik?cik=320193
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "price": 232.8,
    "marketCap": 3500823120000,
    "beta": 1.24,
    "lastDividend": 0.99,
    "range": "164.08-260.1",
    "change": 4.79,
    "changePercentage": 2.1008,
    "volume": 0,
    "averageVolume": 50542058,
    "companyName": "Apple Inc.",
    "currency": "USD",
    "cik": "0000320193",
    "isin": "US0378331005",
    "cusip": "037833100",
    "exchangeFullName": "NASDAQ Global Select",
    "exchange": "NASDAQ",
    "industry": "Consumer Electronics",
    "website": "https://www.apple.com",
    "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allow customers to discov...",
    "ceo": "Mr. Timothy D. Cook",
    "sector": "Technology",
    "country": "US",
    "fullTimeEmployees": "164000",
    "phone": "(408) 996-1010",
    "address": "One Apple Park Way",
    "city": "Cupertino",
    "state": "CA",
    "zip": "95014",
    "image": "https://images.financialmodelingprep.com/symbol/AAPL.png",
    "ipoDate": "1980-12-12",
    "defaultImage": false,
    "isEtf": false,
    "isActivelyTrading": true,
    "isAdr": false,
    "isFund": false
  }
]
```


## Company NotesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/company-notes

### Endpoint

https://financialmodelingprep.com/stable/company-notes?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/company-notes?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0000320193",
    "symbol": "AAPL",
    "title": "1.000% Notes due 2022",
    "exchange": "NASDAQ"
  }
]
```


## Stock Peer ComparisonAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/peers

### Endpoint

https://financialmodelingprep.com/stable/stock-peers?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/stock-peers?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "GPRO",
    "companyName": "GoPro, Inc.",
    "price": 0.9668,
    "mktCap": 152173717
  }
]
```


## Delisted CompaniesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/delisted-companies

### Endpoint

https://financialmodelingprep.com/stable/delisted-companies?page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/delisted-companies?page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "BRQSF",
    "companyName": "Borqs Technologies, Inc.",
    "exchange": "PNK",
    "ipoDate": "2017-08-24",
    "delistedDate": "2025-02-03"
  }
]
```


## Company Employee CountAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/employee-count

### Endpoint

https://financialmodelingprep.com/stable/employee-count?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/employee-count?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "cik": "0000320193",
    "acceptanceTime": "2024-11-01 06:01:36",
    "periodOfReport": "2024-09-28",
    "companyName": "Apple Inc.",
    "formType": "10-K",
    "filingDate": "2024-11-01",
    "employeeCount": 164000,
    "source": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123-index.htm"
  }
]
```


## Company Historical Employee CountAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-employee-count

### Endpoint

https://financialmodelingprep.com/stable/historical-employee-count?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-employee-count?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "cik": "0000320193",
    "acceptanceTime": "2024-11-01 06:01:36",
    "periodOfReport": "2024-09-28",
    "companyName": "Apple Inc.",
    "formType": "10-K",
    "filingDate": "2024-11-01",
    "employeeCount": 164000,
    "source": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123-index.htm"
  }
]
```


## Company Market CapAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/market-cap

### Endpoint

https://financialmodelingprep.com/stable/market-capitalization?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/market-capitalization?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-02-04",
    "marketCap": 3500823120000
  }
]
```


## Batch Market CapAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/batch-market-cap

### Endpoint

https://financialmodelingprep.com/stable/market-capitalization-batch?symbols=AAPL,MSFT,GOOG&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbols * | string | AAPL,MSFT,GOOG |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/market-capitalization-batch?symbols=AAPL,MSFT,GOOG
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-02-04",
    "marketCap": 3500823120000
  }
]
```


## Historical Market CapAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-market-cap

### Endpoint

https://financialmodelingprep.com/stable/historical-market-capitalization?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 100 |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-market-capitalization?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2024-02-29",
    "marketCap": 2784608472000
  }
]
```


## Company Share Float & LiquidityAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/shares-float

### Endpoint

https://financialmodelingprep.com/stable/shares-float?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/shares-float?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-02-04 17:01:35",
    "freeFloat": 99.9095,
    "floatShares": 15024290700,
    "outstandingShares": 15037900000
  }
]
```


## All Shares FloatAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/all-shares-float

### Endpoint

https://financialmodelingprep.com/stable/shares-float-all?page=0&limit=1000&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| limit | number | 1000 |
| page | number | 0 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/shares-float-all?page=0&limit=1000
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "6898.HK",
    "date": "2025-02-04 17:27:01",
    "freeFloat": 33.2536,
    "floatShares": 318128880,
    "outstandingShares": 956675009
  }
]
```


## Latest Mergers & AcquisitionsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/latest-mergers-acquisitions

### Endpoint

https://financialmodelingprep.com/stable/mergers-acquisitions-latest?page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/mergers-acquisitions-latest?page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "NLOK",
    "companyName": "NortonLifeLock Inc.",
    "cik": "0000849399",
    "targetedCompanyName": "MoneyLion Inc.",
    "targetedCik": "0001807846",
    "targetedSymbol": "ML",
    "transactionDate": "2025-02-03",
    "acceptedDate": "2025-02-03 06:01:10",
    "link": "https://www.sec.gov/Archives/edgar/data/849399/000114036125002752/ny20039778x6_s4.htm"
  }
]
```


## Search Mergers & AcquisitionsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-mergers-acquisitions

### Endpoint

https://financialmodelingprep.com/stable/mergers-acquisitions-search?name=Apple&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| name * | string | Apple |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/mergers-acquisitions-search?name=Apple
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "PEGY",
    "companyName": "Pineapple Energy Inc.",
    "cik": "0000022701",
    "targetedCompanyName": "Communications Systems, Inc.",
    "targetedCik": "0000022701",
    "targetedSymbol": "JCS",
    "transactionDate": "2021-11-12",
    "acceptedDate": "2021-11-12 09:54:22",
    "link": "https://www.sec.gov/Archives/edgar/data/22701/000089710121000932/a211292_s-4.htm"
  }
]
```


## Company ExecutivesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/company-executives

### Endpoint

https://financialmodelingprep.com/stable/key-executives?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/key-executives?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "title": "Vice President of Worldwide Sales",
    "name": "Mr. Michael  Fenger",
    "pay": null,
    "currencyPay": "USD",
    "gender": "male",
    "yearBorn": null,
    "active": null
  }
]
```


## Executive CompensationAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/executive-compensation

### Endpoint

https://financialmodelingprep.com/stable/governance-executive-compensation?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/governance-executive-compensation?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0000320193",
    "symbol": "AAPL",
    "companyName": "Apple Inc.",
    "filingDate": "2025-01-10",
    "acceptedDate": "2025-01-10 16:31:18",
    "nameAndPosition": "Kate Adams Senior Vice President, General Counsel and Secretary",
    "year": 2023,
    "salary": 1000000,
    "bonus": 0,
    "stockAward": 22323641,
    "optionAward": 0,
    "incentivePlanCompensation": 3571150,
    "allOtherCompensation": 46914,
    "total": 26941705,
    "link": "https://www.sec.gov/Archives/edgar/data/320193/000130817925000008/0001308179-25-000008-index.htm"
  }
]
```


## Executive Compensation BenchmarkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/executive-compensation-benchmark

### Endpoint

https://financialmodelingprep.com/stable/executive-compensation-benchmark?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| year | string | 2024 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/executive-compensation-benchmark
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "industryTitle": "ABRASIVE, ASBESTOS & MISC NONMETALLIC MINERAL PRODS",
    "year": 2023,
    "averageCompensation": 694313.1666666666
  }
]
```


## Stock QuoteAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/quote

### Endpoint

https://financialmodelingprep.com/stable/quote?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/quote?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "price": 232.8,
    "changePercentage": 2.1008,
    "change": 4.79,
    "volume": 44489128,
    "dayLow": 226.65,
    "dayHigh": 233.13,
    "yearHigh": 260.1,
    "yearLow": 164.08,
    "marketCap": 3500823120000,
    "priceAvg50": 240.2278,
    "priceAvg200": 219.98755,
    "exchange": "NASDAQ",
    "open": 227.2,
    "previousClose": 228.01,
    "timestamp": 1738702801
  }
]
```


## Stock Quote ShortAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/quote-short

### Endpoint

https://financialmodelingprep.com/stable/quote-short?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/quote-short?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "price": 232.8,
    "change": 4.79,
    "volume": 44489128
  }
]
```


## Aftermarket TradeAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/aftermarket-trade

### Endpoint

https://financialmodelingprep.com/stable/aftermarket-trade?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/aftermarket-trade?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "price": 232.53,
    "tradeSize": 132,
    "timestamp": 1738715334311
  }
]
```


## Aftermarket QuoteAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/aftermarket-quote

### Endpoint

https://financialmodelingprep.com/stable/aftermarket-quote?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/aftermarket-quote?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "bidSize": 1,
    "bidPrice": 232.45,
    "askSize": 3,
    "askPrice": 232.64,
    "volume": 41647042,
    "timestamp": 1738715334311
  }
]
```


## Stock Price ChangeAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/quote-change

### Endpoint

https://financialmodelingprep.com/stable/stock-price-change?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/stock-price-change?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "1D": 2.1008,
    "5D": -2.45946,
    "1M": -4.33925,
    "3M": 4.86014,
    "6M": 5.88556,
    "ytd": -4.53147,
    "1Y": 24.04092,
    "3Y": 35.04264,
    "5Y": 192.05871,
    "10Y": 678.8558,
    "max": 181279.04168
  }
]
```


## Stock Batch QuoteAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/batch-quote

### Endpoint

https://financialmodelingprep.com/stable/batch-quote?symbols=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbols * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-quote?symbols=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "price": 232.8,
    "changePercentage": 2.1008,
    "change": 4.79,
    "volume": 44489128,
    "dayLow": 226.65,
    "dayHigh": 233.13,
    "yearHigh": 260.1,
    "yearLow": 164.08,
    "marketCap": 3500823120000,
    "priceAvg50": 240.2278,
    "priceAvg200": 219.98755,
    "exchange": "NASDAQ",
    "open": 227.2,
    "previousClose": 228.01,
    "timestamp": 1738702801
  }
]
```


## Stock Batch Quote ShortAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/batch-quote-short

### Endpoint

https://financialmodelingprep.com/stable/batch-quote-short?symbols=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbols * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-quote-short?symbols=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "price": 232.8,
    "change": 4.79,
    "volume": 44489128
  }
]
```


## Batch Aftermarket TradeAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/batch-aftermarket-trade

### Endpoint

https://financialmodelingprep.com/stable/batch-aftermarket-trade?symbols=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbols * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-aftermarket-trade?symbols=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "price": 232.53,
    "tradeSize": 132,
    "timestamp": 1738715334311
  }
]
```


## Batch Aftermarket QuoteAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/batch-aftermarket-quote

### Endpoint

https://financialmodelingprep.com/stable/batch-aftermarket-quote?symbols=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbols * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-aftermarket-quote?symbols=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "bidSize": 1,
    "bidPrice": 232.45,
    "askSize": 3,
    "askPrice": 232.64,
    "volume": 41647042,
    "timestamp": 1738715334311
  }
]
```


## Exchange Stock QuotesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/full-exchange-quotes

### Endpoint

https://financialmodelingprep.com/stable/batch-exchange-quote?exchange=NASDAQ&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| exchange * | string | NASDAQ |
| short | boolean | true |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-exchange-quote?exchange=NASDAQ
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAACX",
    "price": 6.38,
    "change": 0,
    "volume": 0
  }
]
```


## Mutual Fund Price QuotesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/full-mutualfund-quotes

### Endpoint

https://financialmodelingprep.com/stable/batch-mutualfund-quotes?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| short | boolean | true |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-mutualfund-quotes
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "ARCFX",
    "price": 9.84,
    "change": 0.01,
    "volume": 0
  }
]
```


## ETF Price QuotesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/full-etf-quotes

### Endpoint

https://financialmodelingprep.com/stable/batch-etf-quotes?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| short | boolean | true |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-etf-quotes
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "GULF",
    "price": 16.335,
    "change": 0.13,
    "volume": 3032
  }
]
```


## Full Commodities QuotesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/full-commodities-quotes

### Endpoint

https://financialmodelingprep.com/stable/batch-commodity-quotes?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| short | boolean | true |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-commodity-quotes
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "DCUSD",
    "price": 19.89,
    "change": 0.23,
    "volume": 442
  }
]
```


## Full Cryptocurrency QuotesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/full-cryptocurrency-quotes

### Endpoint

https://financialmodelingprep.com/stable/batch-crypto-quotes?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| short | boolean | true |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-crypto-quotes
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "00USD",
    "price": 0.03071157,
    "change": -0.0026034,
    "volume": 169600
  }
]
```


## Full Forex QuoteAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/full-forex-quotes

### Endpoint

https://financialmodelingprep.com/stable/batch-forex-quotes?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| short | boolean | true |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-forex-quotes
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AEDAUD",
    "price": 0.43575,
    "change": 0.0009547891,
    "volume": 344
  }
]
```


## Full Index QuotesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/full-index-quotes

### Endpoint

https://financialmodelingprep.com/stable/batch-index-quotes?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| short | boolean | true |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-index-quotes
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "^DJBGIE",
    "price": 4277.52,
    "change": -15.7,
    "volume": 0
  }
]
```


## Income StatementAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/income-statement

### Endpoint

https://financialmodelingprep.com/stable/income-statement?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | Q1Q2Q3Q4FYannualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/income-statement?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-09-28",
    "symbol": "AAPL",
    "reportedCurrency": "USD",
    "cik": "0000320193",
    "filingDate": "2024-11-01",
    "acceptedDate": "2024-11-01 06:01:36",
    "fiscalYear": "2024",
    "period": "FY",
    "revenue": 391035000000,
    "costOfRevenue": 210352000000,
    "grossProfit": 180683000000,
    "researchAndDevelopmentExpenses": 31370000000,
    "generalAndAdministrativeExpenses": 0,
    "sellingAndMarketingExpenses": 0,
    "sellingGeneralAndAdministrativeExpenses": 26097000000,
    "otherExpenses": 0,
    "operatingExpenses": 57467000000,
    "costAndExpenses": 267819000000,
    "netInterestIncome": 0,
    "interestIncome": 0,
    "interestExpense": 0,
    "depreciationAndAmortization": 11445000000,
    "ebitda": 134661000000,
    "ebit": 123216000000,
    "nonOperatingIncomeExcludingInterest": 0,
    "operatingIncome": 123216000000,
    "totalOtherIncomeExpensesNet": 269000000,
    "incomeBeforeTax": 123485000000,
    "incomeTaxExpense": 29749000000,
    "netIncomeFromContinuingOperations": 93736000000,
    "netIncomeFromDiscontinuedOperations": 0,
    "otherAdjustmentsToNetIncome": 0,
    "netIncome": 93736000000,
    "netIncomeDeductions": 0,
    "bottomLineNetIncome": 93736000000,
    "eps": 6.11,
    "epsDiluted": 6.08,
    "weightedAverageShsOut": 15343783000,
    "weightedAverageShsOutDil": 15408095000
  }
]
```


## Balance Sheet StatementAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/balance-sheet-statement

### Endpoint

https://financialmodelingprep.com/stable/balance-sheet-statement?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | Q1Q2Q3Q4FYannualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/balance-sheet-statement?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-09-28",
    "symbol": "AAPL",
    "reportedCurrency": "USD",
    "cik": "0000320193",
    "filingDate": "2024-11-01",
    "acceptedDate": "2024-11-01 06:01:36",
    "fiscalYear": "2024",
    "period": "FY",
    "cashAndCashEquivalents": 29943000000,
    "shortTermInvestments": 35228000000,
    "cashAndShortTermInvestments": 65171000000,
    "netReceivables": 66243000000,
    "accountsReceivables": 33410000000,
    "otherReceivables": 32833000000,
    "inventory": 7286000000,
    "prepaids": 0,
    "otherCurrentAssets": 14287000000,
    "totalCurrentAssets": 152987000000,
    "propertyPlantEquipmentNet": 45680000000,
    "goodwill": 0,
    "intangibleAssets": 0,
    "goodwillAndIntangibleAssets": 0,
    "longTermInvestments": 91479000000,
    "taxAssets": 19499000000,
    "otherNonCurrentAssets": 55335000000,
    "totalNonCurrentAssets": 211993000000,
    "otherAssets": 0,
    "totalAssets": 364980000000,
    "totalPayables": 95561000000,
    "accountPayables": 68960000000,
    "otherPayables": 26601000000,
    "accruedExpenses": 0,
    "shortTermDebt": 20879000000,
    "capitalLeaseObligationsCurrent": 1632000000,
    "taxPayables": 26601000000,
    "deferredRevenue": 8249000000,
    "otherCurrentLiabilities": 50071000000,
    "totalCurrentLiabilities": 176392000000,
    "longTermDebt": 85750000000,
    "deferredRevenueNonCurrent": 10798000000,
    "deferredTaxLiabilitiesNonCurrent": 0,
    "otherNonCurrentLiabilities": 35090000000,
    "totalNonCurrentLiabilities": 131638000000,
    "otherLiabilities": 0,
    "capitalLeaseObligations": 12430000000,
    "totalLiabilities": 308030000000,
    "treasuryStock": 0,
    "preferredStock": 0,
    "commonStock": 83276000000,
    "retainedEarnings": -19154000000,
    "additionalPaidInCapital": 0,
    "accumulatedOtherComprehensiveIncomeLoss": -7172000000,
    "otherTotalStockholdersEquity": 0,
    "totalStockholdersEquity": 56950000000,
    "totalEquity": 56950000000,
    "minorityInterest": 0,
    "totalLiabilitiesAndTotalEquity": 364980000000,
    "totalInvestments": 126707000000,
    "totalDebt": 106629000000,
    "netDebt": 76686000000
  }
]
```


## Cash Flow StatementAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cashflow-statement

### Endpoint

https://financialmodelingprep.com/stable/cash-flow-statement?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | Q1Q2Q3Q4FYannualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/cash-flow-statement?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-09-28",
    "symbol": "AAPL",
    "reportedCurrency": "USD",
    "cik": "0000320193",
    "filingDate": "2024-11-01",
    "acceptedDate": "2024-11-01 06:01:36",
    "fiscalYear": "2024",
    "period": "FY",
    "netIncome": 93736000000,
    "depreciationAndAmortization": 11445000000,
    "deferredIncomeTax": 0,
    "stockBasedCompensation": 11688000000,
    "changeInWorkingCapital": 3651000000,
    "accountsReceivables": -5144000000,
    "inventory": -1046000000,
    "accountsPayables": 6020000000,
    "otherWorkingCapital": 3821000000,
    "otherNonCashItems": -2266000000,
    "netCashProvidedByOperatingActivities": 118254000000,
    "investmentsInPropertyPlantAndEquipment": -9447000000,
    "acquisitionsNet": 0,
    "purchasesOfInvestments": -48656000000,
    "salesMaturitiesOfInvestments": 62346000000,
    "otherInvestingActivities": -1308000000,
    "netCashProvidedByInvestingActivities": 2935000000,
    "netDebtIssuance": -5998000000,
    "longTermNetDebtIssuance": -9958000000,
    "shortTermNetDebtIssuance": 3960000000,
    "netStockIssuance": -94949000000,
    "netCommonStockIssuance": -94949000000,
    "commonStockIssuance": 0,
    "commonStockRepurchased": -94949000000,
    "netPreferredStockIssuance": 0,
    "netDividendsPaid": -15234000000,
    "commonDividendsPaid": -15234000000,
    "preferredDividendsPaid": 0,
    "otherFinancingActivities": -5802000000,
    "netCashProvidedByFinancingActivities": -121983000000,
    "effectOfForexChangesOnCash": 0,
    "netChangeInCash": -794000000,
    "cashAtEndOfPeriod": 29943000000,
    "cashAtBeginningOfPeriod": 30737000000,
    "operatingCashFlow": 118254000000,
    "capitalExpenditure": -9447000000,
    "freeCashFlow": 108807000000,
    "incomeTaxesPaid": 26102000000,
    "interestPaid": 0
  }
]
```


## Latest Financial StatementsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/latest-financial-statements

### Endpoint

https://financialmodelingprep.com/stable/latest-financial-statements?page=0&limit=250&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| page | number | 0 |
| limit | number | 250 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/latest-financial-statements?page=0&limit=250
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "FGFI",
    "calendarYear": 2024,
    "period": "Q4",
    "date": "2024-12-31",
    "dateAdded": "2025-03-13 17:03:59"
  }
]
```


## Income Statements TTMAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/income-statements-ttm

### Endpoint

https://financialmodelingprep.com/stable/income-statement-ttm?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/income-statement-ttm?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-12-28",
    "symbol": "AAPL",
    "reportedCurrency": "USD",
    "cik": "0000320193",
    "filingDate": "2025-01-31",
    "acceptedDate": "2025-01-31 06:01:27",
    "fiscalYear": "2025",
    "period": "Q1",
    "revenue": 395760000000,
    "costOfRevenue": 211657000000,
    "grossProfit": 184103000000,
    "researchAndDevelopmentExpenses": 31942000000,
    "generalAndAdministrativeExpenses": 0,
    "sellingAndMarketingExpenses": 0,
    "sellingGeneralAndAdministrativeExpenses": 26486000000,
    "otherExpenses": 0,
    "operatingExpenses": 58428000000,
    "costAndExpenses": 270085000000,
    "netInterestIncome": 0,
    "interestIncome": 0,
    "interestExpense": 0,
    "depreciationAndAmortization": 11677000000,
    "ebitda": 137352000000,
    "ebit": 125675000000,
    "nonOperatingIncomeExcludingInterest": 0,
    "operatingIncome": 125675000000,
    "totalOtherIncomeExpensesNet": 71000000,
    "incomeBeforeTax": 125746000000,
    "incomeTaxExpense": 29596000000,
    "netIncomeFromContinuingOperations": 96150000000,
    "netIncomeFromDiscontinuedOperations": 0,
    "otherAdjustmentsToNetIncome": 0,
    "netIncome": 96150000000,
    "netIncomeDeductions": 0,
    "bottomLineNetIncome": 96150000000,
    "eps": 6.31,
    "epsDiluted": 6.3,
    "weightedAverageShsOut": 15081724000,
    "weightedAverageShsOutDil": 15150865000
  }
]
```


## Balance Sheet Statements TTMAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/balance-sheet-statements-ttm

### Endpoint

https://financialmodelingprep.com/stable/balance-sheet-statement-ttm?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/balance-sheet-statement-ttm?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-12-28",
    "symbol": "AAPL",
    "reportedCurrency": "USD",
    "cik": "0000320193",
    "filingDate": "2025-01-31",
    "acceptedDate": "2025-01-31 06:01:27",
    "fiscalYear": "2025",
    "period": "Q1",
    "cashAndCashEquivalents": 30299000000,
    "shortTermInvestments": 23476000000,
    "cashAndShortTermInvestments": 53775000000,
    "netReceivables": 59306000000,
    "accountsReceivables": 29639000000,
    "otherReceivables": 29667000000,
    "inventory": 6911000000,
    "prepaids": 0,
    "otherCurrentAssets": 13248000000,
    "totalCurrentAssets": 133240000000,
    "propertyPlantEquipmentNet": 46069000000,
    "goodwill": 0,
    "intangibleAssets": 0,
    "goodwillAndIntangibleAssets": 0,
    "longTermInvestments": 87593000000,
    "taxAssets": 0,
    "otherNonCurrentAssets": 77183000000,
    "totalNonCurrentAssets": 210845000000,
    "otherAssets": 0,
    "totalAssets": 344085000000,
    "totalPayables": 61910000000,
    "accountPayables": 61910000000,
    "otherPayables": 0,
    "accruedExpenses": 0,
    "shortTermDebt": 12843000000,
    "capitalLeaseObligationsCurrent": 0,
    "taxPayables": 0,
    "deferredRevenue": 8461000000,
    "otherCurrentLiabilities": 61151000000,
    "totalCurrentLiabilities": 144365000000,
    "longTermDebt": 83956000000,
    "deferredRevenueNonCurrent": 0,
    "deferredTaxLiabilitiesNonCurrent": 0,
    "otherNonCurrentLiabilities": 49006000000,
    "totalNonCurrentLiabilities": 132962000000,
    "otherLiabilities": 0,
    "capitalLeaseObligations": 0,
    "totalLiabilities": 277327000000,
    "treasuryStock": 0,
    "preferredStock": 0,
    "commonStock": 84768000000,
    "retainedEarnings": -11221000000,
    "additionalPaidInCapital": 0,
    "accumulatedOtherComprehensiveIncomeLoss": -6789000000,
    "otherTotalStockholdersEquity": 0,
    "totalStockholdersEquity": 66758000000,
    "totalEquity": 66758000000,
    "minorityInterest": 0,
    "totalLiabilitiesAndTotalEquity": 344085000000,
    "totalInvestments": 111069000000,
    "totalDebt": 96799000000,
    "netDebt": 66500000000
  }
]
```


## Cashflow Statements TTMAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cashflow-statements-ttm

### Endpoint

https://financialmodelingprep.com/stable/cash-flow-statement-ttm?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/cash-flow-statement-ttm?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-12-28",
    "symbol": "AAPL",
    "reportedCurrency": "USD",
    "cik": "0000320193",
    "filingDate": "2025-01-31",
    "acceptedDate": "2025-01-31 06:01:27",
    "fiscalYear": "2025",
    "period": "Q1",
    "netIncome": 96150000000,
    "depreciationAndAmortization": 11677000000,
    "deferredIncomeTax": 0,
    "stockBasedCompensation": 11977000000,
    "changeInWorkingCapital": -8224000000,
    "accountsReceivables": -9505000000,
    "inventory": -694000000,
    "accountsPayables": 3891000000,
    "otherWorkingCapital": -1916000000,
    "otherNonCashItems": -3286000000,
    "netCashProvidedByOperatingActivities": 108294000000,
    "investmentsInPropertyPlantAndEquipment": -9995000000,
    "acquisitionsNet": 0,
    "purchasesOfInvestments": -45000000000,
    "salesMaturitiesOfInvestments": 67422000000,
    "otherInvestingActivities": -1627000000,
    "netCashProvidedByInvestingActivities": 10800000000,
    "netDebtIssuance": -10967000000,
    "longTermNetDebtIssuance": -10967000000,
    "shortTermNetDebtIssuance": 0,
    "netStockIssuance": -98416000000,
    "netCommonStockIssuance": -98416000000,
    "commonStockIssuance": 0,
    "commonStockRepurchased": -98416000000,
    "netPreferredStockIssuance": 0,
    "netDividendsPaid": -15265000000,
    "commonDividendsPaid": -15265000000,
    "preferredDividendsPaid": 0,
    "otherFinancingActivities": -6121000000,
    "netCashProvidedByFinancingActivities": -130769000000,
    "effectOfForexChangesOnCash": 0,
    "netChangeInCash": -11675000000,
    "cashAtEndOfPeriod": 30299000000,
    "cashAtBeginningOfPeriod": 41974000000,
    "operatingCashFlow": 108294000000,
    "capitalExpenditure": -9995000000,
    "freeCashFlow": 98299000000,
    "incomeTaxesPaid": 37498000000,
    "interestPaid": 0
  }
]
```


## Key MetricsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/key-metrics

### Endpoint

https://financialmodelingprep.com/stable/key-metrics?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | Q1Q2Q3Q4FYannualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/key-metrics?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2024-09-28",
    "fiscalYear": "2024",
    "period": "FY",
    "reportedCurrency": "USD",
    "marketCap": 3495160329570,
    "enterpriseValue": 3571846329570,
    "evToSales": 9.134339201273542,
    "evToOperatingCashFlow": 30.204866893043786,
    "evToFreeCashFlow": 32.82735788662494,
    "evToEBITDA": 26.524727497716487,
    "netDebtToEBITDA": 0.5694744580836323,
    "currentRatio": 0.8673125765340832,
    "incomeQuality": 1.2615643936161134,
    "grahamNumber": 22.587017267616833,
    "grahamNetNet": -12.352478525015636,
    "taxBurden": 0.7590881483581001,
    "interestBurden": 1.0021831580314244,
    "workingCapital": -23405000000,
    "investedCapital": 22275000000,
    "returnOnAssets": 0.25682503150857583,
    "operatingReturnOnAssets": 0.3434290787011036,
    "returnOnTangibleAssets": 0.25682503150857583,
    "returnOnEquity": 1.6459350307287095,
    "returnOnInvestedCapital": 0.4430708117427921,
    "returnOnCapitalEmployed": 0.6533607652660827,
    "earningsYield": 0.026818798327209237,
    "freeCashFlowYield": 0.03113076074921754,
    "capexToOperatingCashFlow": 0.07988736110406414,
    "capexToDepreciation": 0.8254259501965924,
    "capexToRevenue": 0.02415896275269477,
    "salesGeneralAndAdministrativeToRevenue": 0,
    "researchAndDevelopementToRevenue": 0.08022299794136074,
    "stockBasedCompensationToRevenue": 0.02988990755303234,
    "intangiblesToTotalAssets": 0,
    "averageReceivables": 63614000000,
    "averagePayables": 65785500000,
    "averageInventory": 6808500000,
    "daysOfSalesOutstanding": 61.83255974529134,
    "daysOfPayablesOutstanding": 119.65847721913745,
    "daysOfInventoryOutstanding": 12.642570548414087,
    "operatingCycle": 74.47513029370543,
    "cashConversionCycle": -45.18334692543202,
    "freeCashFlowToEquity": 32121000000,
    "freeCashFlowToFirm": 117192805288.09166,
    "tangibleAssetValue": 56950000000,
    "netCurrentAssetValue": -155043000000
  }
]
```


## Financial RatiosAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/metrics-ratios

### Endpoint

https://financialmodelingprep.com/stable/ratios?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | Q1Q2Q3Q4FYannualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/ratios?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2024-09-28",
    "fiscalYear": "2024",
    "period": "FY",
    "reportedCurrency": "USD",
    "grossProfitMargin": 0.4620634981523393,
    "ebitMargin": 0.31510222870075566,
    "ebitdaMargin": 0.3443707085043538,
    "operatingProfitMargin": 0.31510222870075566,
    "pretaxProfitMargin": 0.3157901466620635,
    "continuousOperationsProfitMargin": 0.23971255769943867,
    "netProfitMargin": 0.23971255769943867,
    "bottomLineProfitMargin": 0.23971255769943867,
    "receivablesTurnover": 5.903038811648023,
    "payablesTurnover": 3.0503480278422272,
    "inventoryTurnover": 28.870710952511665,
    "fixedAssetTurnover": 8.560310858143607,
    "assetTurnover": 1.0713874732862074,
    "currentRatio": 0.8673125765340832,
    "quickRatio": 0.8260068483831466,
    "solvencyRatio": 0.3414634938155374,
    "cashRatio": 0.16975259648963673,
    "priceToEarningsRatio": 37.287278415656736,
    "priceToEarningsGrowthRatio": -45.93792700808932,
    "forwardPriceToEarningsGrowthRatio": -45.93792700808932,
    "priceToBookRatio": 61.37243774486391,
    "priceToSalesRatio": 8.93822887866815,
    "priceToFreeCashFlowRatio": 32.12256867269569,
    "priceToOperatingCashFlowRatio": 29.55638142954995,
    "debtToAssetsRatio": 0.29215025480848267,
    "debtToEquityRatio": 1.872326602282704,
    "debtToCapitalRatio": 0.6518501763673821,
    "longTermDebtToCapitalRatio": 0.6009110021023125,
    "financialLeverageRatio": 6.408779631255487,
    "workingCapitalTurnoverRatio": -31.099932397502684,
    "operatingCashFlowRatio": 0.6704045534944896,
    "operatingCashFlowSalesRatio": 0.3024128274962599,
    "freeCashFlowOperatingCashFlowRatio": 0.9201126388959359,
    "debtServiceCoverageRatio": 5.024761722304708,
    "interestCoverageRatio": 0,
    "shortTermOperatingCashFlowCoverageRatio": 5.663777000814215,
    "operatingCashFlowCoverageRatio": 1.109022873702276,
    "capitalExpenditureCoverageRatio": 12.517624642743728,
    "dividendPaidAndCapexCoverageRatio": 4.7912969490701345,
    "dividendPayoutRatio": 0.16252026969360758,
    "dividendYield": 0.0043585983369965175,
    "dividendYieldPercentage": 0.43585983369965176,
    "revenuePerShare": 25.484914639368924,
    "netIncomePerShare": 6.109054070954992,
    "interestDebtPerShare": 6.949329249507765,
    "cashPerShare": 4.247388013764271,
    "bookValuePerShare": 3.711600978715614,
    "tangibleBookValuePerShare": 3.711600978715614,
    "shareholdersEquityPerShare": 3.711600978715614,
    "operatingCashFlowPerShare": 7.706965094592383,
    "capexPerShare": 0.6156891035281195,
    "freeCashFlowPerShare": 7.091275991064264,
    "netIncomePerEBT": 0.7590881483581001,
    "ebtPerEbit": 1.0021831580314244,
    "priceToFairValue": 61.37243774486391,
    "debtToMarketCap": 0.03050761336980449,
    "effectiveTaxRate": 0.24091185164189982,
    "enterpriseValueMultiple": 26.524727497716487
  }
]
```


## Key Metrics TTMAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/key-metrics-ttm

### Endpoint

https://financialmodelingprep.com/stable/key-metrics-ttm?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/key-metrics-ttm?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "marketCap": 3149833928000,
    "enterpriseValueTTM": 3216333928000,
    "evToSalesTTM": 8.126980816656559,
    "evToOperatingCashFlowTTM": 29.70001965021146,
    "evToFreeCashFlowTTM": 32.71990486169747,
    "evToEBITDATTM": 23.41672438697653,
    "netDebtToEBITDATTM": 0.48415749315627005,
    "currentRatioTTM": 0.9229383853427077,
    "incomeQualityTTM": 1.1263026521060842,
    "grahamNumberTTM": 25.198029099282905,
    "grahamNetNetTTM": -11.64435843011051,
    "taxBurdenTTM": 0.7646366484818603,
    "interestBurdenTTM": 1.0005649492739208,
    "workingCapitalTTM": -11125000000,
    "investedCapitalTTM": 34944000000,
    "returnOnAssetsTTM": 0.27943676707790227,
    "operatingReturnOnAssetsTTM": 0.35448090090471257,
    "returnOnTangibleAssetsTTM": 0.27943676707790227,
    "returnOnEquityTTM": 1.4534598087751787,
    "returnOnInvestedCapitalTTM": 0.45208108089346594,
    "returnOnCapitalEmployedTTM": 0.6292559583416784,
    "earningsYieldTTM": 0.030404739849149914,
    "freeCashFlowYieldTTM": 0.03120767705439485,
    "capexToOperatingCashFlowTTM": 0.09229504866382256,
    "capexToDepreciationTTM": 0.855956153121521,
    "capexToRevenueTTM": 0.025255205174853447,
    "salesGeneralAndAdministrativeToRevenueTTM": 0,
    "researchAndDevelopementToRevenueTTM": 0.08071053163533455,
    "stockBasedCompensationToRevenueTTM": 0.030263290883363655,
    "intangiblesToTotalAssetsTTM": 0,
    "averageReceivablesTTM": 62774500000,
    "averagePayablesTTM": 65435000000,
    "averageInventoryTTM": 7098500000,
    "daysOfSalesOutstandingTTM": 54.69650798463715,
    "daysOfPayablesOutstandingTTM": 106.76306476988712,
    "daysOfInventoryOutstandingTTM": 11.917937984569374,
    "operatingCycleTTM": 66.61444596920653,
    "cashConversionCycleTTM": -40.148618800680595,
    "freeCashFlowToEquityTTM": 31799000000,
    "freeCashFlowToFirmTTM": 85497710797.9578,
    "tangibleAssetValueTTM": 66758000000,
    "netCurrentAssetValueTTM": -144087000000
  }
]
```


## Financial Ratios TTMAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/metrics-ratios-ttm

### Endpoint

https://financialmodelingprep.com/stable/ratios-ttm?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/ratios-ttm?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "grossProfitMarginTTM": 0.46518849807964424,
    "ebitMarginTTM": 0.3175535678188801,
    "ebitdaMarginTTM": 0.34705882352941175,
    "operatingProfitMarginTTM": 0.3175535678188801,
    "pretaxProfitMarginTTM": 0.31773296947645036,
    "continuousOperationsProfitMarginTTM": 0.24295027289266222,
    "netProfitMarginTTM": 0.24295027289266222,
    "bottomLineProfitMarginTTM": 0.24295027289266222,
    "receivablesTurnoverTTM": 6.673186524129093,
    "payablesTurnoverTTM": 3.4187853335486995,
    "inventoryTurnoverTTM": 30.626103313558097,
    "fixedAssetTurnoverTTM": 8.590592372311098,
    "assetTurnoverTTM": 1.1501809145995903,
    "currentRatioTTM": 0.9229383853427077,
    "quickRatioTTM": 0.8750666712845911,
    "solvencyRatioTTM": 0.3888081578786054,
    "cashRatioTTM": 0.20987774044955496,
    "priceToEarningsRatioTTM": 32.889608822880916,
    "priceToEarningsGrowthRatioTTM": 9.104441715061135,
    "forwardPriceToEarningsGrowthRatioTTM": 9.104441715061135,
    "priceToBookRatioTTM": 47.370141231313106,
    "priceToSalesRatioTTM": 7.958949686678795,
    "priceToFreeCashFlowRatioTTM": 32.04339747098139,
    "priceToOperatingCashFlowRatioTTM": 29.201395167968677,
    "debtToAssetsRatioTTM": 0.28132292892744526,
    "debtToEquityRatioTTM": 1.4499985020521886,
    "debtToCapitalRatioTTM": 0.5918364851397372,
    "longTermDebtToCapitalRatioTTM": 0.557055084464615,
    "financialLeverageRatioTTM": 5.154213727193745,
    "workingCapitalTurnoverRatioTTM": -22.92267593397046,
    "operatingCashFlowRatioTTM": 0.7501402694558931,
    "operatingCashFlowSalesRatioTTM": 0.2736355366889024,
    "freeCashFlowOperatingCashFlowRatioTTM": 0.9077049513361775,
    "debtServiceCoverageRatioTTM": 8.390251498870981,
    "interestCoverageRatioTTM": 0,
    "shortTermOperatingCashFlowCoverageRatioTTM": 8.432142022891847,
    "operatingCashFlowCoverageRatioTTM": 1.1187512267688715,
    "capitalExpenditureCoverageRatioTTM": 10.834817408704351,
    "dividendPaidAndCapexCoverageRatioTTM": 4.287173396674584,
    "dividendPayoutRatioTTM": 0.15876235049401977,
    "dividendYieldTTM": 0.0047691720717283476,
    "enterpriseValueTTM": 3216333928000,
    "revenuePerShareTTM": 26.24103186081379,
    "netIncomePerShareTTM": 6.375265851569754,
    "interestDebtPerShareTTM": 6.418298067250137,
    "cashPerShareTTM": 3.565573803101025,
    "bookValuePerShareTTM": 4.426417032959892,
    "tangibleBookValuePerShareTTM": 4.426417032959892,
    "shareholdersEquityPerShareTTM": 4.426417032959892,
    "operatingCashFlowPerShareTTM": 7.180478836504368,
    "capexPerShareTTM": 0.6627226436447186,
    "freeCashFlowPerShareTTM": 6.5177561928596495,
    "netIncomePerEBTTTM": 0.7646366484818603,
    "ebtPerEbitTTM": 1.0005649492739208,
    "priceToFairValueTTM": 47.370141231313106,
    "debtToMarketCapTTM": 0.030731461471514124,
    "effectiveTaxRateTTM": 0.23536335151813975,
    "enterpriseValueMultipleTTM": 23.41672438697653
  }
]
```


## Financial ScoresAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/financial-scores

### Endpoint

https://financialmodelingprep.com/stable/financial-scores?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/financial-scores?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "reportedCurrency": "USD",
    "altmanZScore": 9.322985825443649,
    "piotroskiScore": 8,
    "workingCapital": -11125000000,
    "totalAssets": 344085000000,
    "retainedEarnings": -11221000000,
    "ebit": 125675000000,
    "marketCap": 3259495258000,
    "totalLiabilities": 277327000000,
    "revenue": 395760000000
  }
]
```


## Owner EarningsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/owner-earnings

### Endpoint

https://financialmodelingprep.com/stable/owner-earnings?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/owner-earnings?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "reportedCurrency": "USD",
    "fiscalYear": "2025",
    "period": "Q1",
    "date": "2024-12-28",
    "averagePPE": 0.13969,
    "maintenanceCapex": -2279964750,
    "ownersEarnings": 27655035250,
    "growthCapex": -660035250,
    "ownersEarningsPerShare": 1.83
  }
]
```


## Enterprise ValuesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/enterprise-values

### Endpoint

https://financialmodelingprep.com/stable/enterprise-values?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | Q1Q2Q3Q4FYannualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/enterprise-values?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2024-09-28",
    "stockPrice": 227.79,
    "numberOfShares": 15343783000,
    "marketCapitalization": 3495160329570,
    "minusCashAndCashEquivalents": 29943000000,
    "addTotalDebt": 106629000000,
    "enterpriseValue": 3571846329570
  }
]
```


## Income Statement GrowthAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/income-statement-growth

### Endpoint

https://financialmodelingprep.com/stable/income-statement-growth?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | Q1Q2Q3Q4FYannualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/income-statement-growth?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2024-09-28",
    "fiscalYear": "2024",
    "period": "FY",
    "reportedCurrency": "USD",
    "growthRevenue": 0.020219940775141214,
    "growthCostOfRevenue": -0.017675600199872046,
    "growthGrossProfit": 0.06819471705252206,
    "growthGrossProfitRatio": 0.04776303446712012,
    "growthResearchAndDevelopmentExpenses": 0.04863780712017383,
    "growthGeneralAndAdministrativeExpenses": 0,
    "growthSellingAndMarketingExpenses": 0,
    "growthOtherExpenses": -1,
    "growthOperatingExpenses": 0.04776924900176856,
    "growthCostAndExpenses": -0.004331112631234571,
    "growthInterestIncome": -1,
    "growthInterestExpense": -1,
    "growthDepreciationAndAmortization": -0.006424168764649709,
    "growthEBITDA": 0.07026704816404387,
    "growthOperatingIncome": 0.07799581805933456,
    "growthIncomeBeforeTax": 0.08571604417246959,
    "growthIncomeTaxExpense": 0.7770145152619318,
    "growthNetIncome": -0.033599670086086914,
    "growthEPS": -0.008116883116883088,
    "growthEPSDiluted": -0.008156606851549727,
    "growthWeightedAverageShsOut": -0.02543458616683152,
    "growthWeightedAverageShsOutDil": -0.02557791606880283,
    "growthEBIT": 0.0471407082579099,
    "growthNonOperatingIncomeExcludingInterest": 1,
    "growthNetInterestIncome": 1,
    "growthTotalOtherIncomeExpensesNet": 1.4761061946902654,
    "growthNetIncomeFromContinuingOperations": -0.033599670086086914,
    "growthOtherAdjustmentsToNetIncome": 0,
    "growthNetIncomeDeductions": 0
  }
]
```


## Balance Sheet Statement GrowthAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/balance-sheet-statement-growth

### Endpoint

https://financialmodelingprep.com/stable/balance-sheet-statement-growth?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | Q1Q2Q3Q4FYannualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/balance-sheet-statement-growth?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2024-09-28",
    "fiscalYear": "2024",
    "period": "FY",
    "reportedCurrency": "USD",
    "growthCashAndCashEquivalents": -0.0007341898882029034,
    "growthShortTermInvestments": 0.11516302627413738,
    "growthCashAndShortTermInvestments": 0.058744212492892536,
    "growthNetReceivables": 0.08621792243994425,
    "growthInventory": 0.15084504817564365,
    "growthOtherCurrentAssets": -0.02776454576386526,
    "growthTotalCurrentAssets": 0.06562138667929733,
    "growthPropertyPlantEquipmentNet": -0.15992349565984992,
    "growthGoodwill": 0,
    "growthIntangibleAssets": 0,
    "growthGoodwillAndIntangibleAssets": 0,
    "growthLongTermInvestments": -0.09015953214513049,
    "growthTaxAssets": 0.09225857046829487,
    "growthOtherNonCurrentAssets": 0.5266933370120016,
    "growthTotalNonCurrentAssets": 0.014238076328719674,
    "growthOtherAssets": 0,
    "growthTotalAssets": 0.035160515396374756,
    "growthAccountPayables": 0.1014039066617687,
    "growthShortTermDebt": 0.32087050041121024,
    "growthTaxPayables": 2.01632838190271,
    "growthDeferredRevenue": 0.023322168465450935,
    "growthOtherCurrentLiabilities": -0.1254584832500786,
    "growthTotalCurrentLiabilities": 0.21391802240757563,
    "growthLongTermDebt": -0.10003043628845205,
    "growthDeferredRevenueNonCurrent": 0,
    "growthDeferredTaxLiabilitiesNonCurrent": 0,
    "growthOtherNonCurrentLiabilities": -0.09048495373370312,
    "growthTotalNonCurrentLiabilities": -0.09295867814151548,
    "growthOtherLiabilities": 0,
    "growthTotalLiabilities": 0.060574238130816666,
    "growthPreferredStock": 0,
    "growthCommonStock": 0.12821763398905328,
    "growthRetainedEarnings": -88.50467289719626,
    "growthAccumulatedOtherComprehensiveIncomeLoss": 0.3737338456164862,
    "growthOthertotalStockholdersEquity": 0,
    "growthTotalStockholdersEquity": -0.0836095645737457,
    "growthMinorityInterest": 0,
    "growthTotalEquity": -0.0836095645737457,
    "growthTotalLiabilitiesAndStockholdersEquity": 0.035160515396374756,
    "growthTotalInvestments": -0.04107194211936368,
    "growthTotalDebt": -0.0401393489845888,
    "growthNetDebt": -0.05469472282829777,
    "growthAccountsReceivables": 0.13223532601328453,
    "growthOtherReceivables": 0.04307907360930203,
    "growthPrepaids": 0,
    "growthTotalPayables": 0.5262653527335452,
    "growthOtherPayables": 0,
    "growthAccruedExpenses": 0,
    "growthCapitalLeaseObligationsCurrent": 0.03619047619047619,
    "growthAdditionalPaidInCapital": 0,
    "growthTreasuryStock": 0
  }
]
```


## Cashflow Statement GrowthAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cashflow-statement-growth

### Endpoint

https://financialmodelingprep.com/stable/cash-flow-statement-growth?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | Q1Q2Q3Q4FYannualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/cash-flow-statement-growth?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2024-09-28",
    "fiscalYear": "2024",
    "period": "FY",
    "reportedCurrency": "USD",
    "growthNetIncome": -0.033599670086086914,
    "growthDepreciationAndAmortization": -0.006424168764649709,
    "growthDeferredIncomeTax": 0,
    "growthStockBasedCompensation": 0.07892550540016616,
    "growthChangeInWorkingCapital": 1.555116314429071,
    "growthAccountsReceivables": -2.0473933649289098,
    "growthInventory": 0.3535228677379481,
    "growthAccountsPayables": 4.1868713605082055,
    "growthOtherWorkingCapital": 2.4402563136072373,
    "growthOtherNonCashItems": -0.017512348450830714,
    "growthNetCashProvidedByOperatingActivites": 0.06975566069312394,
    "growthInvestmentsInPropertyPlantAndEquipment": 0.13796879277306323,
    "growthAcquisitionsNet": 0,
    "growthPurchasesOfInvestments": -0.6486294175448107,
    "growthSalesMaturitiesOfInvestments": 0.3698202750801951,
    "growthOtherInvestingActivites": 0.02169035153328347,
    "growthNetCashUsedForInvestingActivites": -0.2078272604588394,
    "growthDebtRepayment": -0.012662502110417018,
    "growthCommonStockIssued": 0,
    "growthCommonStockRepurchased": -0.2243584784010316,
    "growthDividendsPaid": -0.013910149750415973,
    "growthOtherFinancingActivites": 0.03493013972055888,
    "growthNetCashUsedProvidedByFinancingActivities": -0.12439163778482412,
    "growthEffectOfForexChangesOnCash": 0,
    "growthNetChangeInCash": -1.1378472222222222,
    "growthCashAtEndOfPeriod": -0.02583205908188828,
    "growthCashAtBeginningOfPeriod": 0.23061216319013492,
    "growthOperatingCashFlow": 0.06975566069312394,
    "growthCapitalExpenditure": 0.13796879277306323,
    "growthFreeCashFlow": 0.092615279562982,
    "growthNetDebtIssuance": 0.3942026057973942,
    "growthLongTermNetDebtIssuance": -0.6812426135404356,
    "growthShortTermNetDebtIssuance": 1.995475113122172,
    "growthNetStockIssuance": -0.2243584784010316,
    "growthPreferredDividendsPaid": -0.013910149750415973,
    "growthIncomeTaxesPaid": 0.3973981476524439,
    "growthInterestPaid": -1
  }
]
```


## Financial Statement GrowthAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/financial-statement-growth

### Endpoint

https://financialmodelingprep.com/stable/financial-growth?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | Q1Q2Q3Q4FYannualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/financial-growth?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2024-09-28",
    "fiscalYear": "2024",
    "period": "FY",
    "reportedCurrency": "USD",
    "revenueGrowth": 0.020219940775141214,
    "grossProfitGrowth": 0.06819471705252206,
    "ebitgrowth": 0.07799581805933456,
    "operatingIncomeGrowth": 0.07799581805933456,
    "netIncomeGrowth": -0.033599670086086914,
    "epsgrowth": -0.008116883116883088,
    "epsdilutedGrowth": -0.008156606851549727,
    "weightedAverageSharesGrowth": -0.02543458616683152,
    "weightedAverageSharesDilutedGrowth": -0.02557791606880283,
    "dividendsPerShareGrowth": 0.040371570095532654,
    "operatingCashFlowGrowth": 0.06975566069312394,
    "receivablesGrowth": 0.08621792243994425,
    "inventoryGrowth": 0.15084504817564365,
    "assetGrowth": 0.035160515396374756,
    "bookValueperShareGrowth": -0.059693251557224776,
    "debtGrowth": -0.0401393489845888,
    "rdexpenseGrowth": 0.04863780712017383,
    "sgaexpensesGrowth": 0.04672709770575967,
    "freeCashFlowGrowth": 0.092615279562982,
    "tenYRevenueGrowthPerShare": 2.3937532854122625,
    "fiveYRevenueGrowthPerShare": 0.8093292228858464,
    "threeYRevenueGrowthPerShare": 0.163506592883552,
    "tenYOperatingCFGrowthPerShare": 2.1417809176982403,
    "fiveYOperatingCFGrowthPerShare": 1.051533221923415,
    "threeYOperatingCFGrowthPerShare": 0.23720294833900227,
    "tenYNetIncomeGrowthPerShare": 2.76381558093543,
    "fiveYNetIncomeGrowthPerShare": 1.0421744314966246,
    "threeYNetIncomeGrowthPerShare": 0.07761907162786884,
    "tenYShareholdersEquityGrowthPerShare": -0.19003774225234785,
    "fiveYShareholdersEquityGrowthPerShare": -0.24235004889283715,
    "threeYShareholdersEquityGrowthPerShare": -0.017459858915902907,
    "tenYDividendperShareGrowthPerShare": 1.1722201809466772,
    "fiveYDividendperShareGrowthPerShare": 0.29890046876764864,
    "threeYDividendperShareGrowthPerShare": 0.14617932692103452,
    "ebitdaGrowth": null,
    "growthCapitalExpenditure": null,
    "tenYBottomLineNetIncomeGrowthPerShare": null,
    "fiveYBottomLineNetIncomeGrowthPerShare": null,
    "threeYBottomLineNetIncomeGrowthPerShare": null
  }
]
```


## Financial Reports DatesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/financial-reports-dates

### Endpoint

https://financialmodelingprep.com/stable/financial-reports-dates?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/financial-reports-dates?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "fiscalYear": 2025,
    "period": "Q1",
    "linkXlsx": "https://financialmodelingprep.com/stable/financial-reports-json?symbol=AAPL&year=2025&period=Q1,
    "linkJson": "https://financialmodelingprep.com/stable/financial-reports-xlsx?symbol=AAPL&year=2025&period=Q1
  }
]
```


## Financial Reports Form 10-K JSONAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/financial-reports-form-10-k-json

### Endpoint

https://financialmodelingprep.com/stable/financial-reports-json?symbol=AAPL&year=2022&period=FY&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| year * | number | 2022 |
| period * | string | Q1Q2Q3Q4FY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/financial-reports-json?symbol=AAPL&year=2022&period=FY
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "period": "FY",
    "year": "2022",
    "Cover Page": [
      {
        "Cover Page - USD ($) shares in Thousands, $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Oct. 14, 2022",
          "Mar. 25, 2022"
        ]
      },
      {
        "Entity Information [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Auditor Information": [
      {
        "Auditor Information": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Auditor Information [Abstract]": [
          " "
        ]
      }
    ],
    "CONSOLIDATED STATEMENTS OF OPER": [
      {
        "CONSOLIDATED STATEMENTS OF OPERATIONS - USD ($) shares in Thousands, $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Net sales": [
          394328,
          365817,
          274515
        ]
      }
    ],
    "CONSOLIDATED STATEMENTS OF COMP": [
      {
        "CONSOLIDATED STATEMENTS OF COMPREHENSIVE INCOME - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Statement of Comprehensive Income [Abstract]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "CONSOLIDATED BALANCE SHEETS": [
      {
        "CONSOLIDATED BALANCE SHEETS - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Current assets:": [
          " ",
          " "
        ]
      },
      {
        "Cash and cash equivalents": [
          23646,
          34940
        ]
      }
    ],
    "CONSOLIDATED BALANCE SHEETS (Pa": [
      {
        "CONSOLIDATED BALANCE SHEETS (Parenthetical) - $ / shares": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Statement of Financial Position [Abstract]": [
          " ",
          " "
        ]
      },
      {
        "Common stock, par value (in dollars per share)": [
          1e-05,
          1e-05
        ]
      }
    ],
    "CONSOLIDATED STATEMENTS OF SHAR": [
      {
        "CONSOLIDATED STATEMENTS OF SHAREHOLDERS' EQUITY - USD ($) $ in Millions": [
          "Total",
          "Common stock and additional paid-in capital",
          "Retained earnings/(Accumulated deficit)",
          "Retained earnings/(Accumulated deficit) Cumulative effect of change in accounting principle",
          "Accumulated other comprehensive income/(loss)",
          "Accumulated other comprehensive income/(loss) Cumulative effect of change in accounting principle"
        ]
      },
      {
        "Beginning balances at Sep. 28, 2019": [
          90488,
          45174,
          45898,
          -136,
          -584,
          136
        ]
      },
      {
        "Increase (Decrease) in Stockholders' Equity [Roll Forward]": [
          " ",
          " ",
          " ",
          " ",
          " ",
          " "
        ]
      }
    ],
    "CONSOLIDATED STATEMENTS OF CASH": [
      {
        "CONSOLIDATED STATEMENTS OF CASH FLOWS - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Statement of Cash Flows [Abstract]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Summary of Significant Accounti": [
      {
        "Summary of Significant Accounting Policies": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Accounting Policies [Abstract]": [
          " "
        ]
      }
    ],
    "Revenue": [
      {
        "Revenue": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Revenue from Contract with Customer [Abstract]": [
          " "
        ]
      }
    ],
    "Financial Instruments": [
      {
        "Financial Instruments": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Investments, All Other Investments [Abstract]": [
          " "
        ]
      }
    ],
    "Consolidated Financial Statemen": [
      {
        "Consolidated Financial Statement Details": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Organization, Consolidation and Presentation of Financial Statements [Abstract]": [
          " "
        ]
      }
    ],
    "Income Taxes": [
      {
        "Income Taxes": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Income Tax Disclosure [Abstract]": [
          " "
        ]
      }
    ],
    "Leases": [
      {
        "Leases": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Leases [Abstract]": [
          " "
        ]
      }
    ],
    "Debt": [
      {
        "Debt": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Debt Disclosure [Abstract]": [
          " "
        ]
      }
    ],
    "Shareholders' Equity": [
      {
        "Shareholders' Equity": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Equity [Abstract]": [
          " "
        ]
      }
    ],
    "Benefit Plans": [
      {
        "Benefit Plans": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Share-Based Payment Arrangement [Abstract]": [
          " "
        ]
      }
    ],
    "Commitments and Contingencies": [
      {
        "Commitments and Contingencies": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Commitments and Contingencies Disclosure [Abstract]": [
          " "
        ]
      }
    ],
    "Segment Information and Geograp": [
      {
        "Segment Information and Geographic Data": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Segment Reporting [Abstract]": [
          " "
        ]
      }
    ],
    "Summary of Significant Accoun_2": [
      {
        "Summary of Significant Accounting Policies (Policies)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Accounting Policies [Abstract]": [
          " "
        ]
      }
    ],
    "Summary of Significant Accoun_3": [
      {
        "Summary of Significant Accounting Policies (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Accounting Policies [Abstract]": [
          " "
        ]
      }
    ],
    "Revenue (Tables)": [
      {
        "Revenue (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Revenue from Contract with Customer [Abstract]": [
          " "
        ]
      }
    ],
    "Financial Instruments (Tables)": [
      {
        "Financial Instruments (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Investments, All Other Investments [Abstract]": [
          " "
        ]
      }
    ],
    "Consolidated Financial Statem_2": [
      {
        "Consolidated Financial Statement Details (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Organization, Consolidation and Presentation of Financial Statements [Abstract]": [
          " "
        ]
      }
    ],
    "Income Taxes (Tables)": [
      {
        "Income Taxes (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Income Tax Disclosure [Abstract]": [
          " "
        ]
      }
    ],
    "Leases (Tables)": [
      {
        "Leases (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Leases [Abstract]": [
          " "
        ]
      }
    ],
    "Debt (Tables)": [
      {
        "Debt (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Debt Disclosure [Abstract]": [
          " "
        ]
      }
    ],
    "Shareholders' Equity (Tables)": [
      {
        "Shareholders' Equity (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Equity [Abstract]": [
          " "
        ]
      }
    ],
    "Benefit Plans (Tables)": [
      {
        "Benefit Plans (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Share-Based Payment Arrangement [Abstract]": [
          " "
        ]
      }
    ],
    "Commitments and Contingencies (": [
      {
        "Commitments and Contingencies (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Commitments and Contingencies Disclosure [Abstract]": [
          " "
        ]
      }
    ],
    "Segment Information and Geogr_2": [
      {
        "Segment Information and Geographic Data (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Segment Reporting [Abstract]": [
          " "
        ]
      }
    ],
    "Summary of Significant Accoun_4": [
      {
        "Summary of Significant Accounting Policies - Additional Information (Details) $ in Billions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022 USD ($) performanceObligation",
          "Sep. 25, 2021 USD ($)",
          "Sep. 26, 2020 USD ($)"
        ]
      },
      {
        "Significant Accounting Policies [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Summary of Significant Accoun_5": [
      {
        "Summary of Significant Accounting Policies - Computation of Basic and Diluted Earnings Per Share (Details) - USD ($) $ / shares in Units, shares in Thousands, $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Numerator:": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Revenue - Net Sales Disaggregat": [
      {
        "Revenue - Net Sales Disaggregated by Significant Products and Services (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Disaggregation of Revenue [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Revenue - Additional Informatio": [
      {
        "Revenue - Additional Information (Details) - USD ($) $ in Billions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Revenue from Contract with Customer [Abstract]": [
          " ",
          " "
        ]
      },
      {
        "Total deferred revenue": [
          12.4,
          11.9
        ]
      }
    ],
    "Revenue - Deferred Revenue, Exp": [
      {
        "Revenue - Deferred Revenue, Expected Timing of Realization (Details)": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Revenue, Remaining Performance Obligation, Expected Timing of Satisfaction, Start Date [Axis]: 2022-09-25": [
          " "
        ]
      },
      {
        "Revenue, Remaining Performance Obligation, Expected Timing of Satisfaction [Line Items]": [
          " "
        ]
      }
    ],
    "Financial Instruments - Cash, C": [
      {
        "Financial Instruments - Cash, Cash Equivalents and Marketable Securities (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Debt Securities, Available-for-sale [Line Items]": [
          " ",
          " "
        ]
      },
      {
        "Cash, Cash Equivalents and Marketable Securities, Adjusted Cost": [
          183061,
          189961
        ]
      }
    ],
    "Financial Instruments - Non-Cur": [
      {
        "Financial Instruments - Non-Current Marketable Debt Securities by Contractual Maturity (Details) $ in Millions": [
          "Sep. 24, 2022 USD ($)"
        ]
      },
      {
        "Fair value of non-current marketable debt securities by contractual maturity": [
          " "
        ]
      },
      {
        "Due after 1 year through 5 years": [
          87031
        ]
      }
    ],
    "Financial Instruments - Additio": [
      {
        "Financial Instruments - Additional Information (Details) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022 USD ($) Customer Vendor",
          "Sep. 25, 2021 Vendor"
        ]
      },
      {
        "Financial Instruments [Line Items]": [
          " ",
          " "
        ]
      }
    ],
    "Financial Instruments - Notiona": [
      {
        "Financial Instruments - Notional Amounts Associated with Derivative Instruments (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Derivatives designated as accounting hedges | Foreign exchange contracts": [
          " ",
          " "
        ]
      },
      {
        "Derivative [Line Items]": [
          " ",
          " "
        ]
      }
    ],
    "Financial Instruments - Gross F": [
      {
        "Financial Instruments - Gross Fair Values of Derivative Assets and Liabilities (Details) - Level 2 $ in Millions": [
          "Sep. 24, 2022 USD ($)"
        ]
      },
      {
        "Other current assets and other non-current assets | Foreign exchange contracts": [
          " "
        ]
      },
      {
        "Derivative assets:": [
          " "
        ]
      }
    ],
    "Financial Instruments - Derivat": [
      {
        "Financial Instruments - Derivative Instruments Designated as Fair Value Hedges and Related Hedged Items (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Current and non-current marketable securities": [
          " ",
          " "
        ]
      },
      {
        "Derivatives, Fair Value [Line Items]": [
          " ",
          " "
        ]
      }
    ],
    "Consolidated Financial Statem_3": [
      {
        "Consolidated Financial Statement Details - Property, Plant and Equipment, Net (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Property, Plant and Equipment [Line Items]": [
          " ",
          " "
        ]
      },
      {
        "Gross property, plant and equipment": [
          114457,
          109723
        ]
      }
    ],
    "Consolidated Financial Statem_4": [
      {
        "Consolidated Financial Statement Details - Other Non-Current Liabilities (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Organization, Consolidation and Presentation of Financial Statements [Abstract]": [
          " ",
          " "
        ]
      },
      {
        "Long-term taxes payable": [
          16657,
          24689
        ]
      }
    ],
    "Consolidated Financial Statem_5": [
      {
        "Consolidated Financial Statement Details - Other Income/(Expense), Net (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Organization, Consolidation and Presentation of Financial Statements [Abstract]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Income Taxes - Provision for In": [
      {
        "Income Taxes - Provision for Income Taxes (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Federal:": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Income Taxes - Additional Infor": [
      {
        "Income Taxes - Additional Information (Details) $ in Millions, € in Billions": [
          null,
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Aug. 30, 2016 EUR (€) Subsidiary",
          "Sep. 24, 2022 USD ($)",
          "Sep. 25, 2021 USD ($)",
          "Sep. 26, 2020 USD ($)",
          "Sep. 24, 2022 EUR (€)",
          "Sep. 28, 2019 USD ($)"
        ]
      },
      {
        "Income Tax Contingency [Line Items]": [
          " ",
          " ",
          " ",
          " ",
          " ",
          " "
        ]
      }
    ],
    "Income Taxes - Reconciliation o": [
      {
        "Income Taxes - Reconciliation of Provision for Income Taxes to Amount Computed by Applying the Statutory Federal Income Tax Rate to Income Before Provision for Income Taxes (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Income Tax Disclosure [Abstract]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Income Taxes - Significant Comp": [
      {
        "Income Taxes - Significant Components of Deferred Tax Assets and Liabilities (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Deferred tax assets:": [
          " ",
          " "
        ]
      },
      {
        "Amortization and depreciation": [
          1496,
          5575
        ]
      }
    ],
    "Income Taxes - Aggregate Change": [
      {
        "Income Taxes - Aggregate Changes in Gross Unrecognized Tax Benefits (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Reconciliation of Unrecognized Tax Benefits, Excluding Amounts Pertaining to Examined Tax Returns [Roll Forward]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Leases - Additional Information": [
      {
        "Leases - Additional Information (Details) - USD ($) $ in Billions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Lessee, Lease, Description [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Leases - ROU Assets and Lease L": [
      {
        "Leases - ROU Assets and Lease Liabilities (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Lease-Related Assets and Liabilities": [
          " ",
          " "
        ]
      },
      {
        "Operating lease right-of-use assets": [
          10417,
          10087
        ]
      }
    ],
    "Leases - Lease Liability Maturi": [
      {
        "Leases - Lease Liability Maturities (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Operating Leases": [
          " ",
          " "
        ]
      },
      {
        "2023": [
          1758,
          " "
        ]
      }
    ],
    "Debt - Additional Information (": [
      {
        "Debt - Additional Information (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Debt Instrument [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Debt - Summary of Cash Flows As": [
      {
        "Debt - Summary of Cash Flows Associated with Commercial Paper (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Maturities 90 days or less:": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Debt - Summary of Term Debt (De": [
      {
        "Debt - Summary of Term Debt (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Debt Instrument [Line Items]": [
          " ",
          " "
        ]
      }
    ],
    "Debt - Future Principal Payment": [
      {
        "Debt - Future Principal Payments for Term Debt (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Debt Disclosure [Abstract]": [
          " ",
          " "
        ]
      },
      {
        "2023": [
          11139,
          " "
        ]
      }
    ],
    "Shareholders' Equity - Addition": [
      {
        "Shareholders' Equity - Additional Information (Details) shares in Millions, $ in Billions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022 USD ($) shares"
        ]
      },
      {
        "Stockholders' Equity Note [Abstract]": [
          " "
        ]
      }
    ],
    "Shareholders' Equity - Shares o": [
      {
        "Shareholders' Equity - Shares of Common Stock (Details) - shares shares in Thousands": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Increase (Decrease) in Shares of Common Stock Outstanding [Roll Forward]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Benefit Plans - Additional Info": [
      {
        "Benefit Plans - Additional Information (Details) shares in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022 USD ($) shares",
          "Sep. 25, 2021 USD ($) shares",
          "Sep. 26, 2020 USD ($) shares",
          "Mar. 04, 2022 shares",
          "Nov. 09, 2021 shares",
          "Mar. 10, 2015 shares"
        ]
      },
      {
        "Share-based Compensation Arrangement by Share-based Payment Award [Line Items]": [
          " ",
          " ",
          " ",
          " ",
          " ",
          " "
        ]
      }
    ],
    "Benefit Plans - Restricted Stoc": [
      {
        "Benefit Plans - Restricted Stock Units Activity and Related Information (Details) - Restricted stock units - USD ($) $ / shares in Units, shares in Thousands, $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Number of Restricted Stock Units": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Benefit Plans - Summary of Shar": [
      {
        "Benefit Plans - Summary of Share-Based Compensation Expense and the Related Income Tax Benefit (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Share-Based Payment Arrangement [Abstract]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Commitments and Contingencies -": [
      {
        "Commitments and Contingencies - Future Payments Under Unconditional Purchase Obligations (Details) $ in Millions": [
          "Sep. 24, 2022 USD ($)"
        ]
      },
      {
        "Unconditional Purchase Obligation, Fiscal Year Maturity [Abstract]": [
          " "
        ]
      },
      {
        "2023": [
          13488
        ]
      }
    ],
    "Segment Information and Geogr_3": [
      {
        "Segment Information and Geographic Data - Information by Reportable Segment (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Segment Reporting Information [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Segment Information and Geogr_4": [
      {
        "Segment Information and Geographic Data - Reconciliation of Segment Operating Income to the Consolidated Statements of Operations (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Segment Reporting, Reconciling Item for Operating Profit (Loss) from Segment to Consolidated [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Segment Information and Geogr_5": [
      {
        "Segment Information and Geographic Data - Net Sales (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Revenues from External Customers and Long-Lived Assets [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Segment Information and Geogr_6": [
      {
        "Segment Information and Geographic Data - Long-Lived Assets (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Revenues from External Customers and Long-Lived Assets [Line Items]": [
          " ",
          " "
        ]
      },
      {
        "Long-lived assets": [
          42117,
          39440
        ]
      }
    ]
  }
]
```


## Financial Reports Form 10-K XLSXAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/financial-reports-form-10-k-xlsx

### Endpoint

https://financialmodelingprep.com/stable/financial-reports-xlsx?symbol=AAPL&year=2022&period=FY&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| year * | number | 2022 |
| period * | string | Q1Q2Q3Q4FY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/financial-reports-xlsx?symbol=AAPL&year=2022&period=FY
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "period": "FY",
    "year": "2022",
    "Cover Page": [
      {
        "Cover Page - USD ($) shares in Thousands, $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Oct. 14, 2022",
          "Mar. 25, 2022"
        ]
      },
      {
        "Entity Information [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Auditor Information": [
      {
        "Auditor Information": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Auditor Information [Abstract]": [
          " "
        ]
      }
    ],
    "CONSOLIDATED STATEMENTS OF OPER": [
      {
        "CONSOLIDATED STATEMENTS OF OPERATIONS - USD ($) shares in Thousands, $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Net sales": [
          394328,
          365817,
          274515
        ]
      }
    ],
    "CONSOLIDATED STATEMENTS OF COMP": [
      {
        "CONSOLIDATED STATEMENTS OF COMPREHENSIVE INCOME - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Statement of Comprehensive Income [Abstract]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "CONSOLIDATED BALANCE SHEETS": [
      {
        "CONSOLIDATED BALANCE SHEETS - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Current assets:": [
          " ",
          " "
        ]
      },
      {
        "Cash and cash equivalents": [
          23646,
          34940
        ]
      }
    ],
    "CONSOLIDATED BALANCE SHEETS (Pa": [
      {
        "CONSOLIDATED BALANCE SHEETS (Parenthetical) - $ / shares": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Statement of Financial Position [Abstract]": [
          " ",
          " "
        ]
      },
      {
        "Common stock, par value (in dollars per share)": [
          1e-05,
          1e-05
        ]
      }
    ],
    "CONSOLIDATED STATEMENTS OF SHAR": [
      {
        "CONSOLIDATED STATEMENTS OF SHAREHOLDERS' EQUITY - USD ($) $ in Millions": [
          "Total",
          "Common stock and additional paid-in capital",
          "Retained earnings/(Accumulated deficit)",
          "Retained earnings/(Accumulated deficit) Cumulative effect of change in accounting principle",
          "Accumulated other comprehensive income/(loss)",
          "Accumulated other comprehensive income/(loss) Cumulative effect of change in accounting principle"
        ]
      },
      {
        "Beginning balances at Sep. 28, 2019": [
          90488,
          45174,
          45898,
          -136,
          -584,
          136
        ]
      },
      {
        "Increase (Decrease) in Stockholders' Equity [Roll Forward]": [
          " ",
          " ",
          " ",
          " ",
          " ",
          " "
        ]
      }
    ],
    "CONSOLIDATED STATEMENTS OF CASH": [
      {
        "CONSOLIDATED STATEMENTS OF CASH FLOWS - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Statement of Cash Flows [Abstract]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Summary of Significant Accounti": [
      {
        "Summary of Significant Accounting Policies": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Accounting Policies [Abstract]": [
          " "
        ]
      }
    ],
    "Revenue": [
      {
        "Revenue": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Revenue from Contract with Customer [Abstract]": [
          " "
        ]
      }
    ],
    "Financial Instruments": [
      {
        "Financial Instruments": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Investments, All Other Investments [Abstract]": [
          " "
        ]
      }
    ],
    "Consolidated Financial Statemen": [
      {
        "Consolidated Financial Statement Details": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Organization, Consolidation and Presentation of Financial Statements [Abstract]": [
          " "
        ]
      }
    ],
    "Income Taxes": [
      {
        "Income Taxes": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Income Tax Disclosure [Abstract]": [
          " "
        ]
      }
    ],
    "Leases": [
      {
        "Leases": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Leases [Abstract]": [
          " "
        ]
      }
    ],
    "Debt": [
      {
        "Debt": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Debt Disclosure [Abstract]": [
          " "
        ]
      }
    ],
    "Shareholders' Equity": [
      {
        "Shareholders' Equity": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Equity [Abstract]": [
          " "
        ]
      }
    ],
    "Benefit Plans": [
      {
        "Benefit Plans": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Share-Based Payment Arrangement [Abstract]": [
          " "
        ]
      }
    ],
    "Commitments and Contingencies": [
      {
        "Commitments and Contingencies": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Commitments and Contingencies Disclosure [Abstract]": [
          " "
        ]
      }
    ],
    "Segment Information and Geograp": [
      {
        "Segment Information and Geographic Data": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Segment Reporting [Abstract]": [
          " "
        ]
      }
    ],
    "Summary of Significant Accoun_2": [
      {
        "Summary of Significant Accounting Policies (Policies)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Accounting Policies [Abstract]": [
          " "
        ]
      }
    ],
    "Summary of Significant Accoun_3": [
      {
        "Summary of Significant Accounting Policies (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Accounting Policies [Abstract]": [
          " "
        ]
      }
    ],
    "Revenue (Tables)": [
      {
        "Revenue (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Revenue from Contract with Customer [Abstract]": [
          " "
        ]
      }
    ],
    "Financial Instruments (Tables)": [
      {
        "Financial Instruments (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Investments, All Other Investments [Abstract]": [
          " "
        ]
      }
    ],
    "Consolidated Financial Statem_2": [
      {
        "Consolidated Financial Statement Details (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Organization, Consolidation and Presentation of Financial Statements [Abstract]": [
          " "
        ]
      }
    ],
    "Income Taxes (Tables)": [
      {
        "Income Taxes (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Income Tax Disclosure [Abstract]": [
          " "
        ]
      }
    ],
    "Leases (Tables)": [
      {
        "Leases (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Leases [Abstract]": [
          " "
        ]
      }
    ],
    "Debt (Tables)": [
      {
        "Debt (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Debt Disclosure [Abstract]": [
          " "
        ]
      }
    ],
    "Shareholders' Equity (Tables)": [
      {
        "Shareholders' Equity (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Equity [Abstract]": [
          " "
        ]
      }
    ],
    "Benefit Plans (Tables)": [
      {
        "Benefit Plans (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Share-Based Payment Arrangement [Abstract]": [
          " "
        ]
      }
    ],
    "Commitments and Contingencies (": [
      {
        "Commitments and Contingencies (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Commitments and Contingencies Disclosure [Abstract]": [
          " "
        ]
      }
    ],
    "Segment Information and Geogr_2": [
      {
        "Segment Information and Geographic Data (Tables)": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Segment Reporting [Abstract]": [
          " "
        ]
      }
    ],
    "Summary of Significant Accoun_4": [
      {
        "Summary of Significant Accounting Policies - Additional Information (Details) $ in Billions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022 USD ($) performanceObligation",
          "Sep. 25, 2021 USD ($)",
          "Sep. 26, 2020 USD ($)"
        ]
      },
      {
        "Significant Accounting Policies [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Summary of Significant Accoun_5": [
      {
        "Summary of Significant Accounting Policies - Computation of Basic and Diluted Earnings Per Share (Details) - USD ($) $ / shares in Units, shares in Thousands, $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Numerator:": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Revenue - Net Sales Disaggregat": [
      {
        "Revenue - Net Sales Disaggregated by Significant Products and Services (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Disaggregation of Revenue [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Revenue - Additional Informatio": [
      {
        "Revenue - Additional Information (Details) - USD ($) $ in Billions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Revenue from Contract with Customer [Abstract]": [
          " ",
          " "
        ]
      },
      {
        "Total deferred revenue": [
          12.4,
          11.9
        ]
      }
    ],
    "Revenue - Deferred Revenue, Exp": [
      {
        "Revenue - Deferred Revenue, Expected Timing of Realization (Details)": [
          "Sep. 24, 2022"
        ]
      },
      {
        "Revenue, Remaining Performance Obligation, Expected Timing of Satisfaction, Start Date [Axis]: 2022-09-25": [
          " "
        ]
      },
      {
        "Revenue, Remaining Performance Obligation, Expected Timing of Satisfaction [Line Items]": [
          " "
        ]
      }
    ],
    "Financial Instruments - Cash, C": [
      {
        "Financial Instruments - Cash, Cash Equivalents and Marketable Securities (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Debt Securities, Available-for-sale [Line Items]": [
          " ",
          " "
        ]
      },
      {
        "Cash, Cash Equivalents and Marketable Securities, Adjusted Cost": [
          183061,
          189961
        ]
      }
    ],
    "Financial Instruments - Non-Cur": [
      {
        "Financial Instruments - Non-Current Marketable Debt Securities by Contractual Maturity (Details) $ in Millions": [
          "Sep. 24, 2022 USD ($)"
        ]
      },
      {
        "Fair value of non-current marketable debt securities by contractual maturity": [
          " "
        ]
      },
      {
        "Due after 1 year through 5 years": [
          87031
        ]
      }
    ],
    "Financial Instruments - Additio": [
      {
        "Financial Instruments - Additional Information (Details) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022 USD ($) Customer Vendor",
          "Sep. 25, 2021 Vendor"
        ]
      },
      {
        "Financial Instruments [Line Items]": [
          " ",
          " "
        ]
      }
    ],
    "Financial Instruments - Notiona": [
      {
        "Financial Instruments - Notional Amounts Associated with Derivative Instruments (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Derivatives designated as accounting hedges | Foreign exchange contracts": [
          " ",
          " "
        ]
      },
      {
        "Derivative [Line Items]": [
          " ",
          " "
        ]
      }
    ],
    "Financial Instruments - Gross F": [
      {
        "Financial Instruments - Gross Fair Values of Derivative Assets and Liabilities (Details) - Level 2 $ in Millions": [
          "Sep. 24, 2022 USD ($)"
        ]
      },
      {
        "Other current assets and other non-current assets | Foreign exchange contracts": [
          " "
        ]
      },
      {
        "Derivative assets:": [
          " "
        ]
      }
    ],
    "Financial Instruments - Derivat": [
      {
        "Financial Instruments - Derivative Instruments Designated as Fair Value Hedges and Related Hedged Items (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Current and non-current marketable securities": [
          " ",
          " "
        ]
      },
      {
        "Derivatives, Fair Value [Line Items]": [
          " ",
          " "
        ]
      }
    ],
    "Consolidated Financial Statem_3": [
      {
        "Consolidated Financial Statement Details - Property, Plant and Equipment, Net (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Property, Plant and Equipment [Line Items]": [
          " ",
          " "
        ]
      },
      {
        "Gross property, plant and equipment": [
          114457,
          109723
        ]
      }
    ],
    "Consolidated Financial Statem_4": [
      {
        "Consolidated Financial Statement Details - Other Non-Current Liabilities (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Organization, Consolidation and Presentation of Financial Statements [Abstract]": [
          " ",
          " "
        ]
      },
      {
        "Long-term taxes payable": [
          16657,
          24689
        ]
      }
    ],
    "Consolidated Financial Statem_5": [
      {
        "Consolidated Financial Statement Details - Other Income/(Expense), Net (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Organization, Consolidation and Presentation of Financial Statements [Abstract]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Income Taxes - Provision for In": [
      {
        "Income Taxes - Provision for Income Taxes (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Federal:": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Income Taxes - Additional Infor": [
      {
        "Income Taxes - Additional Information (Details) $ in Millions, € in Billions": [
          null,
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Aug. 30, 2016 EUR (€) Subsidiary",
          "Sep. 24, 2022 USD ($)",
          "Sep. 25, 2021 USD ($)",
          "Sep. 26, 2020 USD ($)",
          "Sep. 24, 2022 EUR (€)",
          "Sep. 28, 2019 USD ($)"
        ]
      },
      {
        "Income Tax Contingency [Line Items]": [
          " ",
          " ",
          " ",
          " ",
          " ",
          " "
        ]
      }
    ],
    "Income Taxes - Reconciliation o": [
      {
        "Income Taxes - Reconciliation of Provision for Income Taxes to Amount Computed by Applying the Statutory Federal Income Tax Rate to Income Before Provision for Income Taxes (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Income Tax Disclosure [Abstract]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Income Taxes - Significant Comp": [
      {
        "Income Taxes - Significant Components of Deferred Tax Assets and Liabilities (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Deferred tax assets:": [
          " ",
          " "
        ]
      },
      {
        "Amortization and depreciation": [
          1496,
          5575
        ]
      }
    ],
    "Income Taxes - Aggregate Change": [
      {
        "Income Taxes - Aggregate Changes in Gross Unrecognized Tax Benefits (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Reconciliation of Unrecognized Tax Benefits, Excluding Amounts Pertaining to Examined Tax Returns [Roll Forward]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Leases - Additional Information": [
      {
        "Leases - Additional Information (Details) - USD ($) $ in Billions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Lessee, Lease, Description [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Leases - ROU Assets and Lease L": [
      {
        "Leases - ROU Assets and Lease Liabilities (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Lease-Related Assets and Liabilities": [
          " ",
          " "
        ]
      },
      {
        "Operating lease right-of-use assets": [
          10417,
          10087
        ]
      }
    ],
    "Leases - Lease Liability Maturi": [
      {
        "Leases - Lease Liability Maturities (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Operating Leases": [
          " ",
          " "
        ]
      },
      {
        "2023": [
          1758,
          " "
        ]
      }
    ],
    "Debt - Additional Information (": [
      {
        "Debt - Additional Information (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Debt Instrument [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Debt - Summary of Cash Flows As": [
      {
        "Debt - Summary of Cash Flows Associated with Commercial Paper (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Maturities 90 days or less:": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Debt - Summary of Term Debt (De": [
      {
        "Debt - Summary of Term Debt (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Debt Instrument [Line Items]": [
          " ",
          " "
        ]
      }
    ],
    "Debt - Future Principal Payment": [
      {
        "Debt - Future Principal Payments for Term Debt (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Debt Disclosure [Abstract]": [
          " ",
          " "
        ]
      },
      {
        "2023": [
          11139,
          " "
        ]
      }
    ],
    "Shareholders' Equity - Addition": [
      {
        "Shareholders' Equity - Additional Information (Details) shares in Millions, $ in Billions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022 USD ($) shares"
        ]
      },
      {
        "Stockholders' Equity Note [Abstract]": [
          " "
        ]
      }
    ],
    "Shareholders' Equity - Shares o": [
      {
        "Shareholders' Equity - Shares of Common Stock (Details) - shares shares in Thousands": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Increase (Decrease) in Shares of Common Stock Outstanding [Roll Forward]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Benefit Plans - Additional Info": [
      {
        "Benefit Plans - Additional Information (Details) shares in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022 USD ($) shares",
          "Sep. 25, 2021 USD ($) shares",
          "Sep. 26, 2020 USD ($) shares",
          "Mar. 04, 2022 shares",
          "Nov. 09, 2021 shares",
          "Mar. 10, 2015 shares"
        ]
      },
      {
        "Share-based Compensation Arrangement by Share-based Payment Award [Line Items]": [
          " ",
          " ",
          " ",
          " ",
          " ",
          " "
        ]
      }
    ],
    "Benefit Plans - Restricted Stoc": [
      {
        "Benefit Plans - Restricted Stock Units Activity and Related Information (Details) - Restricted stock units - USD ($) $ / shares in Units, shares in Thousands, $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Number of Restricted Stock Units": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Benefit Plans - Summary of Shar": [
      {
        "Benefit Plans - Summary of Share-Based Compensation Expense and the Related Income Tax Benefit (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Share-Based Payment Arrangement [Abstract]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Commitments and Contingencies -": [
      {
        "Commitments and Contingencies - Future Payments Under Unconditional Purchase Obligations (Details) $ in Millions": [
          "Sep. 24, 2022 USD ($)"
        ]
      },
      {
        "Unconditional Purchase Obligation, Fiscal Year Maturity [Abstract]": [
          " "
        ]
      },
      {
        "2023": [
          13488
        ]
      }
    ],
    "Segment Information and Geogr_3": [
      {
        "Segment Information and Geographic Data - Information by Reportable Segment (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Segment Reporting Information [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Segment Information and Geogr_4": [
      {
        "Segment Information and Geographic Data - Reconciliation of Segment Operating Income to the Consolidated Statements of Operations (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Segment Reporting, Reconciling Item for Operating Profit (Loss) from Segment to Consolidated [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Segment Information and Geogr_5": [
      {
        "Segment Information and Geographic Data - Net Sales (Details) - USD ($) $ in Millions": [
          "12 Months Ended"
        ]
      },
      {
        "items": [
          "Sep. 24, 2022",
          "Sep. 25, 2021",
          "Sep. 26, 2020"
        ]
      },
      {
        "Revenues from External Customers and Long-Lived Assets [Line Items]": [
          " ",
          " ",
          " "
        ]
      }
    ],
    "Segment Information and Geogr_6": [
      {
        "Segment Information and Geographic Data - Long-Lived Assets (Details) - USD ($) $ in Millions": [
          "Sep. 24, 2022",
          "Sep. 25, 2021"
        ]
      },
      {
        "Revenues from External Customers and Long-Lived Assets [Line Items]": [
          " ",
          " "
        ]
      },
      {
        "Long-lived assets": [
          42117,
          39440
        ]
      }
    ]
  }
]
```


## Revenue Product SegmentationAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/revenue-product-segmentation

### Endpoint

https://financialmodelingprep.com/stable/revenue-product-segmentation?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| period | string | annualquarter |
| structure | string | flat |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/revenue-product-segmentation?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "fiscalYear": 2024,
    "period": "FY",
    "reportedCurrency": null,
    "date": "2024-09-28",
    "data": {
      "Mac": 29984000000,
      "Service": 96169000000,
      "Wearables, Home and Accessories": 37005000000,
      "iPad": 26694000000,
      "iPhone": 201183000000
    }
  }
]
```


## Revenue Geographic SegmentsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/revenue-geographic-segments

### Endpoint

https://financialmodelingprep.com/stable/revenue-geographic-segmentation?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| period | string | annualquarter |
| structure | string | flat |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/revenue-geographic-segmentation?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "fiscalYear": 2024,
    "period": "FY",
    "reportedCurrency": null,
    "date": "2024-09-28",
    "data": {
      "Americas Segment": 167045000000,
      "Europe Segment": 101328000000,
      "Greater China Segment": 66952000000,
      "Japan Segment": 25052000000,
      "Rest of Asia Pacific": 30658000000
    }
  }
]
```


## As Reported Income StatementsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/as-reported-income-statements

### Endpoint

https://financialmodelingprep.com/stable/income-statement-as-reported?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | annualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/income-statement-as-reported?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "fiscalYear": 2024,
    "period": "FY",
    "reportedCurrency": null,
    "date": "2024-09-27",
    "data": {
      "revenuefromcontractwithcustomerexcludingassessedtax": 391035000000,
      "costofgoodsandservicessold": 210352000000,
      "grossprofit": 180683000000,
      "researchanddevelopmentexpense": 31370000000,
      "sellinggeneralandadministrativeexpense": 26097000000,
      "operatingexpenses": 57467000000,
      "operatingincomeloss": 123216000000,
      "nonoperatingincomeexpense": 269000000,
      "incomelossfromcontinuingoperationsbeforeincometaxesextraordinaryitemsnoncontrollinginterest": 123485000000,
      "incometaxexpensebenefit": 29749000000,
      "netincomeloss": 93736000000,
      "earningspersharebasic": 6.11,
      "earningspersharediluted": 6.08,
      "weightedaveragenumberofsharesoutstandingbasic": 15343783000,
      "weightedaveragenumberofdilutedsharesoutstanding": 15408095000,
      "othercomprehensiveincomelossforeigncurrencytransactionandtranslationadjustmentnetoftax": 395000000,
      "othercomprehensiveincomelossderivativeinstrumentgainlossbeforereclassificationaftertax": -832000000,
      "othercomprehensiveincomelossderivativeinstrumentgainlossreclassificationaftertax": 1337000000,
      "othercomprehensiveincomelossderivativeinstrumentgainlossafterreclassificationandtax": -2169000000,
      "othercomprehensiveincomeunrealizedholdinggainlossonsecuritiesarisingduringperiodnetoftax": 5850000000,
      "othercomprehensiveincomelossreclassificationadjustmentfromaociforsaleofsecuritiesnetoftax": -204000000,
      "othercomprehensiveincomelossavailableforsalesecuritiesadjustmentnetoftax": 6054000000,
      "othercomprehensiveincomelossnetoftaxportionattributabletoparent": 4280000000,
      "comprehensiveincomenetoftax": 98016000000
    }
  }
]
```


## As Reported Balance StatementsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/as-reported-balance-statements

### Endpoint

https://financialmodelingprep.com/stable/balance-sheet-statement-as-reported?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | annualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/balance-sheet-statement-as-reported?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "fiscalYear": 2024,
    "period": "FY",
    "reportedCurrency": null,
    "date": "2024-09-27",
    "data": {
      "cashandcashequivalentsatcarryingvalue": 29943000000,
      "marketablesecuritiescurrent": 35228000000,
      "accountsreceivablenetcurrent": 33410000000,
      "nontradereceivablescurrent": 32833000000,
      "inventorynet": 7286000000,
      "otherassetscurrent": 14287000000,
      "assetscurrent": 152987000000,
      "marketablesecuritiesnoncurrent": 91479000000,
      "propertyplantandequipmentnet": 45680000000,
      "otherassetsnoncurrent": 74834000000,
      "assetsnoncurrent": 211993000000,
      "assets": 364980000000,
      "accountspayablecurrent": 68960000000,
      "otherliabilitiescurrent": 78304000000,
      "contractwithcustomerliabilitycurrent": 8249000000,
      "commercialpaper": 10000000000,
      "longtermdebtcurrent": 10912000000,
      "liabilitiescurrent": 176392000000,
      "longtermdebtnoncurrent": 85750000000,
      "otherliabilitiesnoncurrent": 45888000000,
      "liabilitiesnoncurrent": 131638000000,
      "liabilities": 308030000000,
      "commonstocksharesoutstanding": 15116786000,
      "commonstocksharesissued": 15116786000,
      "commonstocksincludingadditionalpaidincapital": 83276000000,
      "retainedearningsaccumulateddeficit": -19154000000,
      "accumulatedothercomprehensiveincomelossnetoftax": -7172000000,
      "stockholdersequity": 56950000000,
      "liabilitiesandstockholdersequity": 364980000000,
      "commonstockparorstatedvaluepershare": 1e-05,
      "commonstocksharesauthorized": 50400000000
    }
  }
]
```


## As Reported Cashflow StatementsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/as-reported-cashflow-statements

### Endpoint

https://financialmodelingprep.com/stable/cash-flow-statement-as-reported?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | annualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/cash-flow-statement-as-reported?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "fiscalYear": 2024,
    "period": "FY",
    "reportedCurrency": null,
    "date": "2024-09-27",
    "data": {
      "cashcashequivalentsrestrictedcashandrestrictedcashequivalents": 29943000000,
      "netincomeloss": 93736000000,
      "depreciationdepletionandamortization": 11445000000,
      "sharebasedcompensation": 11688000000,
      "othernoncashincomeexpense": 2266000000,
      "increasedecreaseinaccountsreceivable": 3788000000,
      "increasedecreaseinotherreceivables": 1356000000,
      "increasedecreaseininventories": 1046000000,
      "increasedecreaseinotheroperatingassets": 11731000000,
      "increasedecreaseinaccountspayable": 6020000000,
      "increasedecreaseinotheroperatingliabilities": 15552000000,
      "netcashprovidedbyusedinoperatingactivities": 118254000000,
      "paymentstoacquireavailableforsalesecuritiesdebt": 48656000000,
      "proceedsfrommaturitiesprepaymentsandcallsofavailableforsalesecurities": 51211000000,
      "proceedsfromsaleofavailableforsalesecuritiesdebt": 11135000000,
      "paymentstoacquirepropertyplantandequipment": 9447000000,
      "paymentsforproceedsfromotherinvestingactivities": 1308000000,
      "netcashprovidedbyusedininvestingactivities": 2935000000,
      "paymentsrelatedtotaxwithholdingforsharebasedcompensation": 5600000000,
      "paymentsofdividends": 15234000000,
      "paymentsforrepurchaseofcommonstock": 94949000000,
      "repaymentsoflongtermdebt": 9958000000,
      "proceedsfromrepaymentsofcommercialpaper": 3960000000,
      "proceedsfrompaymentsforotherfinancingactivities": -361000000,
      "netcashprovidedbyusedinfinancingactivities": -121983000000,
      "cashcashequivalentsrestrictedcashandrestrictedcashequivalentsperiodincreasedecreaseincludingexchangerateeffect": -794000000,
      "incometaxespaidnet": 26102000000
    }
  }
]
```


## As Reported Financial StatementsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/as-reported-financial-statements

### Endpoint

https://financialmodelingprep.com/stable/financial-statement-full-as-reported?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 5 |
| period | string | annualquarter |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/financial-statement-full-as-reported?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "fiscalYear": 2024,
    "period": "FY",
    "reportedCurrency": null,
    "date": "2024-09-27",
    "data": {
      "documenttype": "10-K",
      "documentannualreport": "true",
      "currentfiscalyearenddate": "--09-28",
      "documentperiodenddate": "2024-09-28",
      "documenttransitionreport": "false",
      "entityfilenumber": "001-36743",
      "entityregistrantname": "Apple Inc.",
      "entityincorporationstatecountrycode": "CA",
      "entitytaxidentificationnumber": "94-2404110",
      "entityaddressaddressline1": "One Apple Park Way",
      "entityaddresscityortown": "Cupertino",
      "entityaddressstateorprovince": "CA",
      "entityaddresspostalzipcode": 95014,
      "cityareacode": 408,
      "localphonenumber": "996-1010",
      "security12btitle": "3.600% Notes due 2042",
      "tradingsymbol": "AAPL",
      "notradingsymbolflag": "true",
      "securityexchangename": "NASDAQ",
      "entitywellknownseasonedissuer": "Yes",
      "entityvoluntaryfilers": "No",
      "entitycurrentreportingstatus": "Yes",
      "entityinteractivedatacurrent": "Yes",
      "entityfilercategory": "Large Accelerated Filer",
      "entitysmallbusiness": "false",
      "entityemerginggrowthcompany": "false",
      "icfrauditorattestationflag": "true",
      "documentfinstmterrorcorrectionflag": "false",
      "entityshellcompany": "false",
      "amendmentflag": "false",
      "documentfiscalyearfocus": 2024,
      "documentfiscalperiodfocus": "FY",
      "entitycentralindexkey": 320193,
      "auditorname": "Ernst & Young LLP",
      "auditorlocation": "San Jose, California",
      "auditorfirmid": 42,
      "revenuefromcontractwithcustomerexcludingassessedtax": 391035000000,
      "costofgoodsandservicessold": 210352000000,
      "grossprofit": 180683000000,
      "researchanddevelopmentexpense": 31370000000,
      "sellinggeneralandadministrativeexpense": 26097000000,
      "operatingexpenses": 57467000000,
      "operatingincomeloss": 123216000000,
      "nonoperatingincomeexpense": 269000000,
      "incomelossfromcontinuingoperationsbeforeincometaxesextraordinaryitemsnoncontrollinginterest": 123485000000,
      "incometaxexpensebenefit": 29749000000,
      "netincomeloss": 93736000000,
      "earningspersharebasic": 6.11,
      "earningspersharediluted": 6.08,
      "weightedaveragenumberofsharesoutstandingbasic": 15343783000,
      "weightedaveragenumberofdilutedsharesoutstanding": 15408095000,
      "othercomprehensiveincomelossforeigncurrencytransactionandtranslationadjustmentnetoftax": 395000000,
      "othercomprehensiveincomelossderivativeinstrumentgainlossbeforereclassificationaftertax": -832000000,
      "othercomprehensiveincomelossderivativeinstrumentgainlossreclassificationaftertax": 1337000000,
      "othercomprehensiveincomelossderivativeinstrumentgainlossafterreclassificationandtax": -2169000000,
      "othercomprehensiveincomeunrealizedholdinggainlossonsecuritiesarisingduringperiodnetoftax": 5850000000,
      "othercomprehensiveincomelossreclassificationadjustmentfromaociforsaleofsecuritiesnetoftax": -204000000,
      "othercomprehensiveincomelossavailableforsalesecuritiesadjustmentnetoftax": 6054000000,
      "othercomprehensiveincomelossnetoftaxportionattributabletoparent": 4280000000,
      "comprehensiveincomenetoftax": 98016000000,
      "cashandcashequivalentsatcarryingvalue": 29943000000,
      "marketablesecuritiescurrent": 35228000000,
      "accountsreceivablenetcurrent": 33410000000,
      "nontradereceivablescurrent": 32833000000,
      "inventorynet": 7286000000,
      "otherassetscurrent": 14287000000,
      "assetscurrent": 152987000000,
      "marketablesecuritiesnoncurrent": 91479000000,
      "propertyplantandequipmentnet": 45680000000,
      "otherassetsnoncurrent": 74834000000,
      "assetsnoncurrent": 211993000000,
      "assets": 364980000000,
      "accountspayablecurrent": 68960000000,
      "otherliabilitiescurrent": 78304000000,
      "contractwithcustomerliabilitycurrent": 8249000000,
      "commercialpaper": 10000000000,
      "longtermdebtcurrent": 10912000000,
      "liabilitiescurrent": 176392000000,
      "longtermdebtnoncurrent": 85750000000,
      "otherliabilitiesnoncurrent": 45888000000,
      "liabilitiesnoncurrent": 131638000000,
      "liabilities": 308030000000,
      "commonstocksharesoutstanding": 15116786000,
      "commonstocksharesissued": 15116786000,
      "commonstocksincludingadditionalpaidincapital": 83276000000,
      "retainedearningsaccumulateddeficit": -19154000000,
      "accumulatedothercomprehensiveincomelossnetoftax": -7172000000,
      "stockholdersequity": 56950000000,
      "liabilitiesandstockholdersequity": 364980000000,
      "commonstockparorstatedvaluepershare": 1e-05,
      "commonstocksharesauthorized": 50400000000,
      "stockissuedduringperiodvaluenewissues": 1423000000,
      "adjustmentsrelatedtotaxwithholdingforsharebasedcompensation": 1612000000,
      "adjustmentstoadditionalpaidincapitalsharebasedcompensationrequisiteserviceperiodrecognitionvalue": 12034000000,
      "dividends": 15218000000,
      "stockrepurchasedandretiredduringperiodvalue": 95000000000,
      "commonstockdividendspersharedeclared": 0.98,
      "cashcashequivalentsrestrictedcashandrestrictedcashequivalents": 29943000000,
      "depreciationdepletionandamortization": 11445000000,
      "sharebasedcompensation": 11688000000,
      "othernoncashincomeexpense": 2266000000,
      "increasedecreaseinaccountsreceivable": 3788000000,
      "increasedecreaseinotherreceivables": 1356000000,
      "increasedecreaseininventories": 1046000000,
      "increasedecreaseinotheroperatingassets": 11731000000,
      "increasedecreaseinaccountspayable": 6020000000,
      "increasedecreaseinotheroperatingliabilities": 15552000000,
      "netcashprovidedbyusedinoperatingactivities": 118254000000,
      "paymentstoacquireavailableforsalesecuritiesdebt": 48656000000,
      "proceedsfrommaturitiesprepaymentsandcallsofavailableforsalesecurities": 51211000000,
      "proceedsfromsaleofavailableforsalesecuritiesdebt": 11135000000,
      "paymentstoacquirepropertyplantandequipment": 9447000000,
      "paymentsforproceedsfromotherinvestingactivities": 1308000000,
      "netcashprovidedbyusedininvestingactivities": 2935000000,
      "paymentsrelatedtotaxwithholdingforsharebasedcompensation": 5600000000,
      "paymentsofdividends": 15234000000,
      "paymentsforrepurchaseofcommonstock": 94949000000,
      "repaymentsoflongtermdebt": 9958000000,
      "proceedsfromrepaymentsofcommercialpaper": 3960000000,
      "proceedsfrompaymentsforotherfinancingactivities": -361000000,
      "netcashprovidedbyusedinfinancingactivities": -121983000000,
      "cashcashequivalentsrestrictedcashandrestrictedcashequivalentsperiodincreasedecreaseincludingexchangerateeffect": -794000000,
      "incometaxespaidnet": 26102000000,
      "commercialpapercashflowsummarytabletextblock": "The following table provides a summary of cash flows associated with the issuance and maturities of commercial paper for 2024, 2023 and 2022 (in millions):",
      "contractwithcustomerliabilityrevenuerecognized": 7700000000,
      "contractwithcustomerliability": 12800000000,
      "revenueremainingperformanceobligationpercentage": 0.02,
      "revenueremainingperformanceobligationexpectedtimingofsatisfactionperiod1": "P1Y",
      "incrementalcommonsharesattributabletosharebasedpaymentarrangements": 64312000,
      "cash": 27199000000,
      "equitysecuritiesfvnicost": 1293000000,
      "equitysecuritiesfvniaccumulatedgrossunrealizedgainbeforetax": 105000000,
      "equitysecuritiesfvniaccumulatedgrossunrealizedlossbeforetax": 3000000,
      "equitysecuritiesfvnicurrentandnoncurrent": 1395000000,
      "availableforsaledebtsecuritiesamortizedcostbasis": 132108000000,
      "availableforsaledebtsecuritiesaccumulatedgrossunrealizedgainbeforetax": 583000000,
      "availableforsaledebtsecuritiesaccumulatedgrossunrealizedlossbeforetax": 4635000000,
      "availableforsalesecuritiesdebtsecurities": 128056000000,
      "cashcashequivalentsandmarketablesecuritiescost": 160600000000,
      "cashequivalentsandmarketablesecuritiesaccumulatedgrossunrealizedgainbeforetax": 688000000,
      "cashequivalentsandmarketablesecuritiesaccumulatedgrossunrealizedlossbeforetax": 4638000000,
      "cashcashequivalentsandmarketablesecurities": 156650000000,
      "restrictedcashandcashequivalents": 2600000000,
      "debtsecuritiesavailableforsalerestricted": 13200000000,
      "debtsecuritiesavailableforsalematurityallocatedandsinglematuritydaterollingafteronethroughfiveyearspercentage": 0.14,
      "debtsecuritiesavailableforsalematurityallocatedandsinglematuritydaterollingafterfivethroughtenyearspercentage": 0.09,
      "debtsecuritiesavailableforsalematurityallocatedandsinglematuritydaterollingaftertenyearspercentage": 0.77,
      "maximumlengthoftimeforeigncurrencycashflowhedge": "P18Y",
      "concentrationriskpercentage1": 0.23,
      "numberofsignificantvendors": 2,
      "derivativenotionalamount": 91493000000,
      "hedgedassetstatementoffinancialpositionextensibleenumeration": "http://fasb.org/us-gaap/2024#MarketableSecuritiesCurrent http://fasb.org/us-gaap/2024#MarketableSecuritiesNoncurrent",
      "hedgedliabilityfairvaluehedge": 13505000000,
      "hedgedliabilitystatementoffinancialpositionextensibleenumeration": "http://fasb.org/us-gaap/2024#LongTermDebtCurrent http://fasb.org/us-gaap/2024#LongTermDebtNoncurrent",
      "propertyplantandequipmentgross": 119128000000,
      "accumulateddepreciationdepletionandamortizationpropertyplantandequipment": 73448000000,
      "depreciation": 8200000000,
      "deferredincometaxassetsnet": 19499000000,
      "otherassetsmiscellaneousnoncurrent": 55335000000,
      "accruedincometaxescurrent": 1200000000,
      "otheraccruedliabilitiescurrent": 51703000000,
      "accruedincometaxesnoncurrent": 9254000000,
      "otheraccruedliabilitiesnoncurrent": 36634000000,
      "totalrestrictedcashcashequivalentsandavailableforsaledebtsecurities": 15800000000,
      "currentforeigntaxexpensebenefit": 25483000000,
      "currentfederaltaxexpensebenefit": 5571000000,
      "unrecognizedtaxbenefitsdecreasesresultingfromsettlementswithtaxingauthorities": 1070000000,
      "incomelossfromcontinuingoperationsbeforeincometaxesforeign": 77300000000,
      "effectiveincometaxratereconciliationatfederalstatutoryincometaxrate": 0.21,
      "deferredtaxassetstaxcreditcarryforwardsforeign": 5100000000,
      "deferredtaxassetstaxcreditcarryforwardsresearch": 3600000000,
      "unrecognizedtaxbenefits": 22038000000,
      "unrecognizedtaxbenefitsthatwouldimpacteffectivetaxrate": 10800000000,
      "decreaseinunrecognizedtaxbenefitsisreasonablypossible": 13000000000,
      "deferredfederalincometaxexpensebenefit": -3080000000,
      "federalincometaxexpensebenefitcontinuingoperations": 2491000000,
      "currentstateandlocaltaxexpensebenefit": 1726000000,
      "deferredstateandlocalincometaxexpensebenefit": -298000000,
      "stateandlocalincometaxexpensebenefitcontinuingoperations": 1428000000,
      "deferredforeignincometaxexpensebenefit": 347000000,
      "foreignincometaxexpensebenefitcontinuingoperations": 25830000000,
      "incometaxreconciliationincometaxexpensebenefitatfederalstatutoryincometaxrate": 25932000000,
      "incometaxreconciliationstateandlocalincometaxes": 1162000000,
      "effectiveincometaxratereconciliationimpactofthestateaiddecisionamount": 10246000000,
      "incometaxreconciliationforeignincometaxratedifferential": -5311000000,
      "incometaxreconciliationtaxcreditsresearch": 1397000000,
      "effectiveincometaxratereconciliationsharebasedcompensationexcesstaxbenefitamount": -893000000,
      "incometaxreconciliationotheradjustments": 10000000,
      "effectiveincometaxratecontinuingoperations": 0.241,
      "deferredtaxassetscapitalizedresearchanddevelopment": 10739000000,
      "deferredtaxassetstaxcreditcarryforwards": 8856000000,
      "deferredtaxassetstaxdeferredexpensereservesandaccruals": 6114000000,
      "deferredtaxassetsdeferredincome": 3413000000,
      "deferredtaxassetsleaseliabilities": 2410000000,
      "deferredtaxassetsothercomprehensiveloss": 1173000000,
      "deferredtaxassetsother": 2168000000,
      "deferredtaxassetsgross": 34873000000,
      "deferredtaxassetsvaluationallowance": 8866000000,
      "deferredtaxassetsnet": 26007000000,
      "deferredtaxliabilitiespropertyplantandequipment": 2551000000,
      "deferredtaxliabilitiesleasingarrangements": 2125000000,
      "deferredtaxliabilitiesminimumtaxonforeignearnings": 1674000000,
      "deferredtaxliabilitiesother": 455000000,
      "deferredincometaxliabilities": 6805000000,
      "deferredtaxassetsliabilitiesnet": 19202000000,
      "unrecognizedtaxbenefitsincreasesresultingfrompriorperiodtaxpositions": 1727000000,
      "unrecognizedtaxbenefitsdecreasesresultingfrompriorperiodtaxpositions": 386000000,
      "unrecognizedtaxbenefitsincreasesresultingfromcurrentperiodtaxpositions": 2542000000,
      "unrecognizedtaxbenefitsreductionsresultingfromlapseofapplicablestatuteoflimitations": 229000000,
      "lesseeoperatingandfinanceleasetermofcontract": "P10Y",
      "operatingleasecost": 2000000000,
      "variableleasecost": 13800000000,
      "operatingleasepayments": 1900000000,
      "rightofuseassetsobtainedinexchangeforoperatingandfinanceleaseliabilities": 1000000000,
      "operatingandfinanceleaseweightedaverageremainingleaseterm": "P10Y3M18D",
      "operatingandfinanceleaseweightedaveragediscountratepercent": 0.031,
      "unrecordedunconditionalpurchaseobligationbalancesheetamount": 11226000000,
      "lesseeoperatingandfinanceleaseleasenotyetcommencedtermofcontract": "P21Y",
      "operatingleaserightofuseasset": 10234000000,
      "operatingleaserightofuseassetstatementoffinancialpositionextensiblelist": "http://fasb.org/us-gaap/2024#OtherAssetsNoncurrent",
      "financeleaserightofuseasset": 1069000000,
      "financeleaserightofuseassetstatementoffinancialpositionextensiblelist": "http://fasb.org/us-gaap/2024#PropertyPlantAndEquipmentNet",
      "operatingandfinanceleaserightofuseasset": 11303000000,
      "operatingleaseliabilitycurrent": 1488000000,
      "operatingleaseliabilitycurrentstatementoffinancialpositionextensiblelist": "http://fasb.org/us-gaap/2024#OtherLiabilitiesCurrent",
      "operatingleaseliabilitynoncurrent": 10046000000,
      "operatingleaseliabilitynoncurrentstatementoffinancialpositionextensiblelist": "http://fasb.org/us-gaap/2024#OtherLiabilitiesNoncurrent",
      "financeleaseliabilitycurrent": 144000000,
      "financeleaseliabilitycurrentstatementoffinancialpositionextensiblelist": "http://fasb.org/us-gaap/2024#OtherLiabilitiesCurrent",
      "financeleaseliabilitynoncurrent": 752000000,
      "financeleaseliabilitynoncurrentstatementoffinancialpositionextensiblelist": "http://fasb.org/us-gaap/2024#OtherLiabilitiesNoncurrent",
      "operatingandfinanceleaseliability": 12430000000,
      "lesseeoperatingleaseliabilitypaymentsduenexttwelvemonths": 1820000000,
      "lesseeoperatingleaseliabilitypaymentsdueyeartwo": 1914000000,
      "lesseeoperatingleaseliabilitypaymentsdueyearthree": 1674000000,
      "lesseeoperatingleaseliabilitypaymentsdueyearfour": 1360000000,
      "lesseeoperatingleaseliabilitypaymentsdueyearfive": 1187000000,
      "lesseeoperatingleaseliabilitypaymentsdueafteryearfive": 5563000000,
      "lesseeoperatingleaseliabilitypaymentsdue": 13518000000,
      "lesseeoperatingleaseliabilityundiscountedexcessamount": 1984000000,
      "operatingleaseliability": 11534000000,
      "financeleaseliabilitypaymentsduenexttwelvemonths": 171000000,
      "financeleaseliabilitypaymentsdueyeartwo": 131000000,
      "financeleaseliabilitypaymentsdueyearthree": 59000000,
      "financeleaseliabilitypaymentsdueyearfour": 38000000,
      "financeleaseliabilitypaymentsdueyearfive": 36000000,
      "financeleaseliabilitypaymentsdueafteryearfive": 837000000,
      "financeleaseliabilitypaymentsdue": 1272000000,
      "financeleaseliabilityundiscountedexcessamount": 376000000,
      "financeleaseliability": 896000000,
      "lesseeoperatingandfinanceleaseliabilitytobepaidyearone": 1991000000,
      "lesseeoperatingandfinanceleaseliabilitytobepaidyeartwo": 2045000000,
      "lesseeoperatingandfinanceleaseliabilitytobepaidyearthree": 1733000000,
      "lesseeoperatingandfinanceleaseliabilitytobepaidyearfour": 1398000000,
      "lesseeoperatingandfinanceleaseliabilitytobepaidyearfive": 1223000000,
      "lesseeoperatingandfinanceleaseliabilitytobepaidafteryearfive": 6400000000,
      "lesseeoperatingandfinanceleaseliabilitytobepaid": 14790000000,
      "lesseeoperatingandfinanceleaseliabilityundiscountedexcessamount": 2360000000,
      "debtinstrumentterm": "P9M",
      "shorttermdebtweightedaverageinterestrate": 0.05,
      "longtermdebtfairvalue": 88400000000,
      "proceedsfromrepaymentsofshorttermdebtmaturinginthreemonthsorless": 3960000000,
      "debtinstrumentcarryingamount": 97341000000,
      "debtinstrumentunamortizeddiscountpremiumanddebtissuancecostsnet": 321000000,
      "hedgeaccountingadjustmentsrelatedtolongtermdebt": 358000000,
      "longtermdebt": 96662000000,
      "debtinstrumentmaturityyearrangestart": 2024,
      "debtinstrumentmaturityyearrangeend": 2062,
      "debtinstrumentinterestratestatedpercentage": 0.0485,
      "debtinstrumentinterestrateeffectivepercentage": 0.0665,
      "longtermdebtmaturitiesrepaymentsofprincipalinnexttwelvemonths": 10930000000,
      "longtermdebtmaturitiesrepaymentsofprincipalinyeartwo": 12342000000,
      "longtermdebtmaturitiesrepaymentsofprincipalinyearthree": 9936000000,
      "longtermdebtmaturitiesrepaymentsofprincipalinyearfour": 7800000000,
      "longtermdebtmaturitiesrepaymentsofprincipalinyearfive": 5153000000,
      "longtermdebtmaturitiesrepaymentsofprincipalafteryearfive": 51180000000,
      "stockrepurchasedandretiredduringperiodshares": 499372000,
      "stockissuedduringperiodsharessharebasedpaymentarrangementnetofshareswithheldfortaxes": 66097000,
      "sharebasedcompensationarrangementbysharebasedpaymentawardawardvestingperiod1": "P4Y",
      "sharebasedcompensationarrangementbysharebasedpaymentawardequityinstrumentsotherthanoptionsnumberofsharesofcommonstockissuedperunituponvesting": 1,
      "sharebasedcompensationarrangementbysharebasedpaymentawardequityinstrumentsotherthanoptionsvestedinperiodtotalfairvalue": 15800000000,
      "sharespaidfortaxwithholdingforsharebasedcompensation": 31000000,
      "employeeservicesharebasedcompensationnonvestedawardstotalcompensationcostnotyetrecognized": 19400000000,
      "employeeservicesharebasedcompensationnonvestedawardstotalcompensationcostnotyetrecognizedperiodforrecognition1": "P2Y4M24D",
      "sharebasedcompensationarrangementbysharebasedpaymentawardequityinstrumentsotherthanoptionsnonvestednumber": 163326000,
      "sharebasedcompensationarrangementbysharebasedpaymentawardequityinstrumentsotherthanoptionsgrantsinperiod": 80456000,
      "sharebasedcompensationarrangementbysharebasedpaymentawardequityinstrumentsotherthanoptionsvestedinperiod": 87633000,
      "sharebasedcompensationarrangementbysharebasedpaymentawardequityinstrumentsotherthanoptionsforfeitedinperiod": 9744000,
      "sharebasedcompensationarrangementbysharebasedpaymentawardequityinstrumentsotherthanoptionsnonvestedweightedaveragegrantdatefairvalue": 158.73,
      "sharebasedcompensationarrangementbysharebasedpaymentawardequityinstrumentsotherthanoptionsgrantsinperiodweightedaveragegrantdatefairvalue": 173.78,
      "sharebasedcompensationarrangementbysharebasedpaymentawardequityinstrumentsotherthanoptionsvestedinperiodweightedaveragegrantdatefairvalue": 127.59,
      "sharebasedcompensationarrangementbysharebasedpaymentawardequityinstrumentsotherthanoptionsforfeituresweightedaveragegrantdatefairvalue": 140.8,
      "sharebasedcompensationarrangementbysharebasedpaymentawardequityinstrumentsotherthanoptionsaggregateintrinsicvaluenonvested": 37204000000,
      "allocatedsharebasedcompensationexpense": 11688000000,
      "employeeservicesharebasedcompensationtaxbenefitfromcompensationexpense": 3350000000,
      "unrecordedunconditionalpurchaseobligationbalanceonfirstanniversary": 3206000000,
      "unrecordedunconditionalpurchaseobligationbalanceonsecondanniversary": 2440000000,
      "unrecordedunconditionalpurchaseobligationbalanceonthirdanniversary": 1156000000,
      "unrecordedunconditionalpurchaseobligationbalanceonfourthanniversary": 3121000000,
      "unrecordedunconditionalpurchaseobligationbalanceonfifthanniversary": 633000000,
      "unrecordedunconditionalpurchaseobligationdueafterfiveyears": 670000000,
      "othergeneralandadministrativeexpense": 7458000000,
      "noncurrentassets": 45680000000,
      "trdarrsecuritiesaggavailamt": 100000,
      "insidertrdpoliciesprocadoptedflag": "true"
    }
  }
]
```


## Stock Chart LightAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-light

### Endpoint

https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-02-04",
    "price": 232.8,
    "volume": 44489128
  }
]
```


## Stock Price and Volume DataAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-full

### Endpoint

https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-02-04",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "change": 5.6,
    "changePercent": 2.46479,
    "vwap": 230.86
  }
]
```


## Unadjusted Stock PriceAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-non-split-adjusted

### Endpoint

https://financialmodelingprep.com/stable/historical-price-eod/non-split-adjusted?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-price-eod/non-split-adjusted?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-02-04",
    "adjOpen": 227.2,
    "adjHigh": 233.13,
    "adjLow": 226.65,
    "adjClose": 232.8,
    "volume": 44489128
  }
]
```


## Dividend Adjusted Price ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-dividend-adjusted

### Endpoint

https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-02-04",
    "adjOpen": 227.2,
    "adjHigh": 233.13,
    "adjLow": 226.65,
    "adjClose": 232.8,
    "volume": 44489128
  }
]
```


## 1 Min Interval Stock ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/intraday-1-min

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/1min?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |
| nonadjusted | boolean | false |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/1min?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 15:59:00",
    "open": 233.01,
    "low": 232.72,
    "high": 233.13,
    "close": 232.79,
    "volume": 720121
  }
]
```


## 5 Min Interval Stock ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/intraday-5-min

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/5min?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |
| nonadjusted | boolean | false |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/5min?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 15:55:00",
    "open": 232.87,
    "low": 232.72,
    "high": 233.13,
    "close": 232.79,
    "volume": 1555040
  }
]
```


## 15 Min Interval Stock ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/intraday-15-min

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/15min?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |
| nonadjusted | boolean | false |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/15min?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 15:45:00",
    "open": 232.25,
    "low": 232.18,
    "high": 233.13,
    "close": 232.79,
    "volume": 2535629
  }
]
```


## 30 Min Interval Stock ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/intraday-30-min

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/30min?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |
| nonadjusted | boolean | false |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/30min?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 15:30:00",
    "open": 232.29,
    "low": 232.01,
    "high": 233.13,
    "close": 232.79,
    "volume": 3476320
  }
]
```


## 1 Hour Interval Stock ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/intraday-1-hour

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |
| nonadjusted | boolean | false |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 15:30:00",
    "open": 232.29,
    "low": 232.01,
    "high": 233.13,
    "close": 232.37,
    "volume": 15079381
  }
]
```


## 4 Hour Interval Stock ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/intraday-4-hour

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/4hour?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |
| nonadjusted | boolean | false |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/4hour?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 12:30:00",
    "open": 231.79,
    "low": 231.37,
    "high": 233.13,
    "close": 232.37,
    "volume": 23781913
  }
]
```


## Treasury RatesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/treasury-rates

### Endpoint

https://financialmodelingprep.com/stable/treasury-rates?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/treasury-rates
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-02-29",
    "month1": 5.53,
    "month2": 5.5,
    "month3": 5.45,
    "month6": 5.3,
    "year1": 5.01,
    "year2": 4.64,
    "year3": 4.43,
    "year5": 4.26,
    "year7": 4.28,
    "year10": 4.25,
    "year20": 4.51,
    "year30": 4.38
  }
]
```


## Economics IndicatorsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/economics-indicators

### Endpoint

https://financialmodelingprep.com/stable/economic-indicators?name=GDP&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| name * | string | GDPrealGDPnominalPotentialGDPrealGDPPerCapitafederalFundsCPIinflationRateinflationretailSalesconsumerSentimentdurableGoodsunemploymentRatetotalNonfarmPayrollinitialClaimsindustrialProductionTotalIndexnewPrivatelyOwnedHousingUnitsStartedTotalUnitstotalVehicleSalesretailMoneyFundssmoothedUSRecessionProbabilities3MonthOr90DayRatesAndYieldsCertificatesOfDepositcommercialBankInterestRateOnCreditCardPlansAllAccounts30YearFixedRateMortgageAverage15YearFixedRateMortgageAveragetradeBalanceGoodsAndServices |
| from | date | 2024-12-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/economic-indicators?name=GDP
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "name": "GDP",
    "date": "2024-01-01",
    "value": 28624.069
  }
]
```


## Economic Data Releases CalendarAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/economics-calendar

### Endpoint

https://financialmodelingprep.com/stable/economic-calendar?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/economic-calendar
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-03-01 03:35:00",
    "country": "JP",
    "event": "3-Month Bill Auction",
    "currency": "JPY",
    "previous": -0.112,
    "estimate": null,
    "actual": -0.096,
    "change": 0.016,
    "impact": "Low",
    "changePercentage": 14.286
  }
]
```


## Market Risk PremiumAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/market-risk-premium

### Endpoint

https://financialmodelingprep.com/stable/market-risk-premium?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/market-risk-premium
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "country": "Zimbabwe",
    "continent": "Africa",
    "countryRiskPremium": 13.17,
    "totalEquityRiskPremium": 17.77
  }
]
```


## Dividends CompanyAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/dividends-company

### Endpoint

https://financialmodelingprep.com/stable/dividends?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/dividends?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-02-10",
    "recordDate": "2025-02-10",
    "paymentDate": "2025-02-13",
    "declarationDate": "2025-01-30",
    "adjDividend": 0.25,
    "dividend": 0.25,
    "yield": 0.42955326460481097,
    "frequency": "Quarterly"
  }
]
```


## Dividends CalendarAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/dividends-calendar

### Endpoint

https://financialmodelingprep.com/stable/dividends-calendar?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/dividends-calendar
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "1D0.SI",
    "date": "2025-02-04",
    "recordDate": "",
    "paymentDate": "",
    "declarationDate": "",
    "adjDividend": 0.01,
    "dividend": 0.01,
    "yield": 6.25,
    "frequency": "Semi-Annual"
  }
]
```


## Earnings ReportAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/earnings-company

### Endpoint

https://financialmodelingprep.com/stable/earnings?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/earnings?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-10-29",
    "epsActual": null,
    "epsEstimated": null,
    "revenueActual": null,
    "revenueEstimated": null,
    "lastUpdated": "2025-02-04"
  }
]
```


## Earnings CalendarAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/earnings-calendar

### Endpoint

https://financialmodelingprep.com/stable/earnings-calendar?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/earnings-calendar
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "KEC.NS",
    "date": "2024-11-04",
    "epsActual": 3.32,
    "epsEstimated": 4.97,
    "revenueActual": 51133100000,
    "revenueEstimated": 44687400000,
    "lastUpdated": "2024-12-08"
  }
]
```


## IPOs CalendarAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/ipos-calendar

### Endpoint

https://financialmodelingprep.com/stable/ipos-calendar?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/ipos-calendar
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "PEVC",
    "date": "2025-02-03",
    "daa": "2025-02-03T05:00:00.000Z",
    "company": "Pacer Funds Trust",
    "exchange": "NYSE",
    "actions": "Expected",
    "shares": null,
    "priceRange": null,
    "marketCap": null
  }
]
```


## IPOs DisclosureAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/ipos-disclosure

### Endpoint

https://financialmodelingprep.com/stable/ipos-disclosure?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/ipos-disclosure
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "SCHM",
    "filingDate": "2025-02-03",
    "acceptedDate": "2025-02-03",
    "effectivenessDate": "2025-02-03",
    "cik": "0001454889",
    "form": "CERT",
    "url": "https://www.sec.gov/Archives/edgar/data/1454889/000114336225000044/SCCR020325.pdf"
  }
]
```


## IPOs ProspectusAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/ipos-prospectus

### Endpoint

https://financialmodelingprep.com/stable/ipos-prospectus?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/ipos-prospectus
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "ATAK",
    "acceptedDate": "2025-02-03",
    "filingDate": "2025-02-03",
    "ipoDate": "2022-03-20",
    "cik": "0001883788",
    "pricePublicPerShare": 0.78,
    "pricePublicTotal": 4649936.72,
    "discountsAndCommissionsPerShare": 0.04,
    "discountsAndCommissionsTotal": 254909.67,
    "proceedsBeforeExpensesPerShare": 0.74,
    "proceedsBeforeExpensesTotal": 4395207.05,
    "form": "424B4",
    "url": "https://www.sec.gov/Archives/edgar/data/1883788/000149315225004604/form424b4.htm"
  }
]
```


## Stock Split DetailsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/splits-company

### Endpoint

https://financialmodelingprep.com/stable/splits?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/splits?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2020-08-31",
    "numerator": 4,
    "denominator": 1
  }
]
```


## Stock Splits CalendarAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/splits-calendar

### Endpoint

https://financialmodelingprep.com/stable/splits-calendar?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/splits-calendar
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "EYEN",
    "date": "2025-02-03",
    "numerator": 1,
    "denominator": 80
  }
]
```


## Latest Earning TranscriptsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/latest-transcripts

### Endpoint

https://financialmodelingprep.com/stable/earning-call-transcript-latest?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| limit | number | 100 |
| page | number | 0 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/earning-call-transcript-latest
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "CSWC",
    "period": "Q3",
    "fiscalYear": 2025,
    "date": "2025-02-04"
  }
]
```


## Earnings TranscriptAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-transcripts

### Endpoint

https://financialmodelingprep.com/stable/earning-call-transcript?symbol=AAPL&year=2020&quarter=3&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| year * | string | 2020 |
| quarter * | string | 3 |
| limit | number | 1 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/earning-call-transcript?symbol=AAPL&year=2020&quarter=3
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "period": "Q3",
    "year": 2020,
    "date": "2020-07-30",
    "content": "Operator: Good day, everyone. Welcome to the Apple Incorporated Third Quarter Fiscal Year 2020 Earnings Conference Call. Today's call is being recorded. At this time, for opening remarks and introductions, I would like to turn things over to Mr. Tejas Gala, Senior Manager, Corporate Finance and Investor Relations. Please go ahead, sir.\nTejas Gala: Thank you. Good afternoon and thank you for joining us. Speaking first today is Apple's CEO, Tim Cook; and he'll be followed by CFO, Luca Maestri. Aft..."
  }
]
```


## Transcripts Dates By SymbolAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/transcripts-dates-by-symbol

### Endpoint

https://financialmodelingprep.com/stable/earning-call-transcript-dates?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/earning-call-transcript-dates?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "quarter": 1,
    "fiscalYear": 2025,
    "date": "2025-01-30"
  }
]
```


## Available Transcript SymbolsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/available-transcript-symbols

### Endpoint

https://financialmodelingprep.com/stable/earnings-transcript-list?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/earnings-transcript-list
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "MCUJF",
    "companyName": "Medicure Inc.",
    "noOfTranscripts": "16"
  }
]
```


## FMP ArticlesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/fmp-articles

### Endpoint

https://financialmodelingprep.com/stable/fmp-articles?page=0&limit=20&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| page | number | 0 |
| limit | number | 20 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/fmp-articles?page=0&limit=20
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "title": "Merck Shares Plunge 8% as Weak Guidance Overshadows Strong Revenue Growth",
    "date": "2025-02-04 09:33:00",
    "content": "<p><a href='https://financialmodelingprep.com/financial-summary/MRK'>Merck & Co (NYSE:MRK)</a> saw its stock sink over 8% in pre-market today after delivering mixed fourth-quarter results, with earnings missing expectations, revenue exceeding forecasts, and full-year guidance coming in below analyst estimates.</p>\n<p>For Q4, the pharmaceutical giant reported adjusted earnings per share (EPS) of $1.72, falling short of the $1.81 consensus estimate. However, revenue climbed 7% year-over-year to $1...",
    "tickers": "NYSE:MRK",
    "image": "https://cdn.financialmodelingprep.com/images/fmp-1738679603793.jpg",
    "link": "https://financialmodelingprep.com/market-news/fmp-merck-shares-plunge-8-as-weak-guidance-overshadows-strong-revenue-growth",
    "author": "Davit Kirakosyan",
    "site": "Financial Modeling Prep"
  }
]
```


## General NewsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/general-news

### Endpoint

https://financialmodelingprep.com/stable/news/general-latest?page=0&limit=20&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-10 |
| page | number | 0 |
| limit | number | 20 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/news/general-latest?page=0&limit=20
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": null,
    "publishedDate": "2025-02-03 23:51:37",
    "publisher": "CNBC",
    "title": "Asia tech stocks rise after Trump pauses tariffs on China and Mexico",
    "image": "https://images.financialmodelingprep.com/news/asia-tech-stocks-rise-after-trump-pauses-tariffs-on-20250203.jpg",
    "site": "cnbc.com",
    "text": "Gains in Asian tech companies were broad-based, with stocks in Japan, South Korea and Hong Kong advancing. Semiconductor players Advantest and Lasertec led gains among Japanese tech stocks.",
    "url": "https://www.cnbc.com/2025/02/04/asia-tech-stocks-rise-after-trump-pauses-tariffs-on-china-and-mexico.html"
  }
]
```


## Press ReleasesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/press-releases

### Endpoint

https://financialmodelingprep.com/stable/news/press-releases-latest?page=0&limit=20&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-10 |
| page | number | 0 |
| limit | number | 20 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/news/press-releases-latest?page=0&limit=20
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "LNW",
    "publishedDate": "2025-02-03 23:32:00",
    "publisher": "PRNewsWire",
    "title": "Rosen Law Firm Encourages Light & Wonder, Inc. Investors to Inquire About Securities Class Action Investigation - LNW",
    "image": "https://images.financialmodelingprep.com/news/rosen-law-firm-encourages-light-wonder-inc-investors-to-20250203.jpg",
    "site": "prnewswire.com",
    "text": "NEW YORK , Feb. 3, 2025 /PRNewswire/ -- Why: Rosen Law Firm, a global investor rights law firm, continues to investigate potential securities claims on behalf of shareholders of Light & Wonder, Inc. (NASDAQ: LNW) resulting from allegations that Light & Wonder may have issued materially misleading business information to the investing public. So What: If you purchased Light & Wonder securities you may be entitled to compensation without payment of any out of pocket fees or costs through a contingency fee arrangement.",
    "url": "https://www.prnewswire.com/news-releases/rosen-law-firm-encourages-light--wonder-inc-investors-to-inquire-about-securities-class-action-investigation--lnw-302366877.html"
  }
]
```


## Stock NewsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/stock-news

### Endpoint

https://financialmodelingprep.com/stable/news/stock-latest?page=0&limit=20&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-10 |
| page | number | 0 |
| limit | number | 20 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/news/stock-latest?page=0&limit=20
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "INSG",
    "publishedDate": "2025-02-03 23:53:40",
    "publisher": "Seeking Alpha",
    "title": "Q4 Earnings Release Looms For Inseego, But Don't Expect Miracles",
    "image": "https://images.financialmodelingprep.com/news/q4-earnings-release-looms-for-inseego-but-dont-expect-20250203.jpg",
    "site": "seekingalpha.com",
    "text": "Inseego's Q3 beat was largely due to a one-time debt restructuring gain, not sustainable earnings growth, raising concerns about future performance. The sale of its telematics business for $52 million allows INSG to focus on North America, but it remains to be seen if this was wise. Despite improved margins and reduced debt, Inseego's revenue growth is insufficient, and its high stock price remains unjustifiable for new investors.",
    "url": "https://seekingalpha.com/article/4754485-inseego-stock-q4-earnings-preview-monitor-growth-margins-closely"
  }
]
```


## Crypto NewsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/crypto-news

### Endpoint

https://financialmodelingprep.com/stable/news/crypto-latest?page=0&limit=20&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-10 |
| page | number | 0 |
| limit | number | 20 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/news/crypto-latest?page=0&limit=20
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "BTCUSD",
    "publishedDate": "2025-02-03 23:32:19",
    "publisher": "Coingape",
    "title": "Crypto Prices Today Feb 4: BTC & Altcoins Recover Amid Pause On Trump's Tariffs",
    "image": "https://images.financialmodelingprep.com/news/crypto-prices-today-feb-4-btc-altcoins-recover-amid-20250203.webp",
    "site": "coingape.com",
    "text": "Crypto prices today have shown signs of recovery as U.S. President Donald Trump's newly announced import tariffs on Canada and Mexico were paused for 30 days. Bitcoin (BTC) price regained its value, hitting a $102K high amid broader market recovery.",
    "url": "https://coingape.com/crypto-prices-today-feb-4-btc-altcoins-recover-amid-pause-on-trumps-tariffs/"
  }
]
```


## Forex NewsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/forex-news

### Endpoint

https://financialmodelingprep.com/stable/news/forex-latest?page=0&limit=20&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | date | 2025-09-09 |
| to | date | 2025-12-10 |
| page | number | 0 |
| limit | number | 20 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/news/forex-latest?page=0&limit=20
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "XAUUSD",
    "publishedDate": "2025-02-03 23:55:44",
    "publisher": "FX Street",
    "title": "United Arab Emirates Gold price today: Gold steadies, according to FXStreet data",
    "image": "https://images.financialmodelingprep.com/news/united-arab-emirates-gold-price-today-gold-steadies-according-20250203.jpg",
    "site": "fxstreet.com",
    "text": "Gold prices remained broadly unchanged in United Arab Emirates on Tuesday, according to data compiled by FXStreet.",
    "url": "https://www.fxstreet.com/news/united-arab-emirates-gold-price-today-gold-steadies-according-to-fxstreet-data-202502040455"
  }
]
```


## Search Press ReleasesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-press-releases

### Endpoint

https://financialmodelingprep.com/stable/news/press-releases?symbols=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbols * | string | AAPL |
| from | date | 2025-09-09 |
| to | date | 2025-12-10 |
| page | number | 0 |
| limit | number | 20 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/news/press-releases?symbols=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "publishedDate": "2025-01-30 16:30:00",
    "publisher": "Business Wire",
    "title": "Apple reports first quarter results",
    "image": "https://images.financialmodelingprep.com/news/apple-reports-first-quarter-results-20250130.jpg",
    "site": "businesswire.com",
    "text": "CUPERTINO, Calif.--(BUSINESS WIRE)--Apple® today announced financial results for its fiscal 2025 first quarter ended December 28, 2024. The Company posted quarterly revenue of $124.3 billion, up 4 percent year over year, and quarterly diluted earnings per share of $2.40, up 10 percent year over year. “Today Apple is reporting our best quarter ever, with revenue of $124.3 billion, up 4 percent from a year ago,” said Tim Cook, Apple's CEO. “We were thrilled to bring customers our best-ever lineup.",
    "url": "https://www.businesswire.com/news/home/20250130261281/en/Apple-reports-first-quarter-results/"
  }
]
```


## Search Stock NewsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-stock-news

### Endpoint

https://financialmodelingprep.com/stable/news/stock?symbols=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbols * | string | AAPL |
| from | date | 2025-09-09 |
| to | date | 2025-12-10 |
| page | number | 0 |
| limit | number | 20 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/news/stock?symbols=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "publishedDate": "2025-02-03 21:05:14",
    "publisher": "Zacks Investment Research",
    "title": "Apple & China Tariffs: A Closer Look",
    "image": "https://images.financialmodelingprep.com/news/apple-china-tariffs-a-closer-look-20250203.jpg",
    "site": "zacks.com",
    "text": "Tariffs have been the talk of the town over recent weeks, regularly overshadowing other important developments and causing volatility spikes.",
    "url": "https://www.zacks.com/stock/news/2408814/apple-china-tariffs-a-closer-look?cid=CS-STOCKNEWSAPI-FT-stocks_in_the_news-2408814"
  }
]
```


## Search Crypto NewsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-crypto-news

### Endpoint

https://financialmodelingprep.com/stable/news/crypto?symbols=BTCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbols * | string | BTCUSD |
| from | date | 2025-09-09 |
| to | date | 2025-12-10 |
| page | number | 0 |
| limit | number | 20 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/news/crypto?symbols=BTCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "BTCUSD",
    "publishedDate": "2025-02-03 23:32:19",
    "publisher": "Coingape",
    "title": "Crypto Prices Today Feb 4: BTC & Altcoins Recover Amid Pause On Trump's Tariffs",
    "image": "https://images.financialmodelingprep.com/news/crypto-prices-today-feb-4-btc-altcoins-recover-amid-20250203.webp",
    "site": "coingape.com",
    "text": "Crypto prices today have shown signs of recovery as U.S. President Donald Trump's newly announced import tariffs on Canada and Mexico were paused for 30 days. Bitcoin (BTC) price regained its value, hitting a $102K high amid broader market recovery.",
    "url": "https://coingape.com/crypto-prices-today-feb-4-btc-altcoins-recover-amid-pause-on-trumps-tariffs/"
  }
]
```


## Search Forex NewsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-forex-news

### Endpoint

https://financialmodelingprep.com/stable/news/forex?symbols=EURUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbols * | string | EURUSD |
| from | date | 2025-09-09 |
| to | date | 2025-12-10 |
| page | number | 0 |
| limit | number | 20 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/news/forex?symbols=EURUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "EURUSD",
    "publishedDate": "2025-02-03 18:43:01",
    "publisher": "FX Street",
    "title": "EUR/USD trims losses but still sheds weight",
    "image": "https://images.financialmodelingprep.com/news/eurusd-trims-losses-but-still-sheds-weight-20250203.jpg",
    "site": "fxstreet.com",
    "text": "EUR/USD dropped sharply following fresh tariff threats from US President Donald Trump, impacting the markets. However, significant declines in global risk markets eased as the Trump administration offered 30-day concessions on impending tariffs for Canada and Mexico.",
    "url": "https://www.fxstreet.com/news/eur-usd-trims-losses-but-still-sheds-weight-202502032343"
  }
]
```


## Institutional Ownership FilingsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/latest-filings

### Endpoint

https://financialmodelingprep.com/stable/institutional-ownership/latest?page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/institutional-ownership/latest?page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0001963967",
    "name": "CPA ASSET MANAGEMENT LLC",
    "date": "2024-12-31",
    "filingDate": "2025-02-04 00:00:00",
    "acceptedDate": "2025-02-04 17:28:36",
    "formType": "13F-HR",
    "link": "https://www.sec.gov/Archives/edgar/data/1963967/000196396725000001/0001963967-25-000001-index.htm",
    "finalLink": "https://www.sec.gov/Archives/edgar/data/1963967/000196396725000001/boc2024q413f.xml"
  }
]
```


## Filings ExtractAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/filings-extract

### Endpoint

https://financialmodelingprep.com/stable/institutional-ownership/extract?cik=0001388838&year=2023&quarter=3&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| cik * | string | 0001388838 |
| year * | string | 2023 |
| quarter * | string | 3 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/institutional-ownership/extract?cik=0001388838&year=2023&quarter=3
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2023-09-30",
    "filingDate": "2023-11-13",
    "acceptedDate": "2023-11-13",
    "cik": "0001388838",
    "securityCusip": "674215207",
    "symbol": "CHRD",
    "nameOfIssuer": "CHORD ENERGY CORPORATION",
    "shares": 13280,
    "titleOfClass": "COM NEW",
    "sharesType": "SH",
    "putCallShare": "",
    "value": 2152290,
    "link": "https://www.sec.gov/Archives/edgar/data/1388838/000117266123003760/0001172661-23-003760-index.htm",
    "finalLink": "https://www.sec.gov/Archives/edgar/data/1388838/000117266123003760/infotable.xml"
  }
]
```


## Form 13F Filings DatesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/form-13f-filings-dates

### Endpoint

https://financialmodelingprep.com/stable/institutional-ownership/dates?cik=0001067983&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| cik * | string | 0001067983 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/institutional-ownership/dates?cik=0001067983
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-09-30",
    "year": 2024,
    "quarter": 3
  }
]
```


## Filings Extract With Analytics By HolderAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/filings-extract-with-analytics-by-holder

### Endpoint

https://financialmodelingprep.com/stable/institutional-ownership/extract-analytics/holder?symbol=AAPL&year=2023&quarter=3&page=0&limit=10&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| year * | string | 2023 |
| quarter * | string | 3 |
| page | number | 0 |
| limit | number | 10 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/institutional-ownership/extract-analytics/holder?symbol=AAPL&year=2023&quarter=3&page=0&limit=10
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2023-09-30",
    "cik": "0000102909",
    "filingDate": "2023-12-18",
    "investorName": "VANGUARD GROUP INC",
    "symbol": "AAPL",
    "securityName": "APPLE INC",
    "typeOfSecurity": "COM",
    "securityCusip": "037833100",
    "sharesType": "SH",
    "putCallShare": "Share",
    "investmentDiscretion": "SOLE",
    "industryTitle": "ELECTRONIC COMPUTERS",
    "weight": 5.4673,
    "lastWeight": 5.996,
    "changeInWeight": -0.5287,
    "changeInWeightPercentage": -8.8175,
    "marketValue": 222572509140,
    "lastMarketValue": 252876459509,
    "changeInMarketValue": -30303950369,
    "changeInMarketValuePercentage": -11.9837,
    "sharesNumber": 1299997133,
    "lastSharesNumber": 1303688506,
    "changeInSharesNumber": -3691373,
    "changeInSharesNumberPercentage": -0.2831,
    "quarterEndPrice": 171.21,
    "avgPricePaid": 95.86,
    "isNew": false,
    "isSoldOut": false,
    "ownership": 8.3336,
    "lastOwnership": 8.305,
    "changeInOwnership": 0.0286,
    "changeInOwnershipPercentage": 0.3445,
    "holdingPeriod": 42,
    "firstAdded": "2013-06-30",
    "performance": -29671950396,
    "performancePercentage": -11.7338,
    "lastPerformance": 38078179274,
    "changeInPerformance": -67750129670,
    "isCountedForPerformance": true
  }
]
```


## Holder Performance SummaryAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/holder-performance-summary

### Endpoint

https://financialmodelingprep.com/stable/institutional-ownership/holder-performance-summary?cik=0001067983&page=0&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| cik * | string | 0001067983 |
| page | number | 0 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/institutional-ownership/holder-performance-summary?cik=0001067983&page=0
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-09-30",
    "cik": "0001067983",
    "investorName": "BERKSHIRE HATHAWAY INC",
    "portfolioSize": 40,
    "securitiesAdded": 3,
    "securitiesRemoved": 4,
    "marketValue": 266378900503,
    "previousMarketValue": 279969062343,
    "changeInMarketValue": -13590161840,
    "changeInMarketValuePercentage": -4.8542,
    "averageHoldingPeriod": 18,
    "averageHoldingPeriodTop10": 31,
    "averageHoldingPeriodTop20": 27,
    "turnover": 0.175,
    "turnoverAlternateSell": 13.9726,
    "turnoverAlternateBuy": 1.1974,
    "performance": 17707926874,
    "performancePercentage": 6.325,
    "lastPerformance": 38318168662,
    "changeInPerformance": -20610241788,
    "performance1year": 89877376224,
    "performancePercentage1year": 28.5368,
    "performance3year": 91730847239,
    "performancePercentage3year": 31.2597,
    "performance5year": 157058602844,
    "performancePercentage5year": 73.1617,
    "performanceSinceInception": 182067479115,
    "performanceSinceInceptionPercentage": 198.2138,
    "performanceRelativeToSP500Percentage": 6.325,
    "performance1yearRelativeToSP500Percentage": 28.5368,
    "performance3yearRelativeToSP500Percentage": 36.5632,
    "performance5yearRelativeToSP500Percentage": 36.1296,
    "performanceSinceInceptionRelativeToSP500Percentage": 37.0968
  }
]
```


## Holders Industry BreakdownAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/holders-industry-breakdown

### Endpoint

https://financialmodelingprep.com/stable/institutional-ownership/holder-industry-breakdown?cik=0001067983&year=2023&quarter=3&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| cik * | string | 0001067983 |
| year * | string | 2023 |
| quarter * | string | 3 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/institutional-ownership/holder-industry-breakdown?cik=0001067983&year=2023&quarter=3
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2023-09-30",
    "cik": "0001067983",
    "investorName": "BERKSHIRE HATHAWAY INC",
    "industryTitle": "ELECTRONIC COMPUTERS",
    "weight": 49.7704,
    "lastWeight": 51.0035,
    "changeInWeight": -1.2332,
    "changeInWeightPercentage": -2.4178,
    "performance": -20838154294,
    "performancePercentage": -178.2938,
    "lastPerformance": 26615340304,
    "changeInPerformance": -47453494598
  }
]
```


## Positions SummaryAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/positions-summary

### Endpoint

https://financialmodelingprep.com/stable/institutional-ownership/symbol-positions-summary?symbol=AAPL&year=2023&quarter=3&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| year * | string | 2023 |
| quarter * | string | 3 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/institutional-ownership/symbol-positions-summary?symbol=AAPL&year=2023&quarter=3
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "cik": "0000320193",
    "date": "2023-09-30",
    "investorsHolding": 4805,
    "lastInvestorsHolding": 4749,
    "investorsHoldingChange": 56,
    "numberOf13Fshares": 9247670386,
    "lastNumberOf13Fshares": 9345671472,
    "numberOf13FsharesChange": -98001086,
    "totalInvested": 1613733330618,
    "lastTotalInvested": 1825154796061,
    "totalInvestedChange": -211421465443,
    "ownershipPercent": 59.2821,
    "lastOwnershipPercent": 59.5356,
    "ownershipPercentChange": -0.2535,
    "newPositions": 158,
    "lastNewPositions": 188,
    "newPositionsChange": -30,
    "increasedPositions": 1921,
    "lastIncreasedPositions": 1775,
    "increasedPositionsChange": 146,
    "closedPositions": 156,
    "lastClosedPositions": 122,
    "closedPositionsChange": 34,
    "reducedPositions": 2375,
    "lastReducedPositions": 2506,
    "reducedPositionsChange": -131,
    "totalCalls": 173528138,
    "lastTotalCalls": 198746782,
    "totalCallsChange": -25218644,
    "totalPuts": 192878290,
    "lastTotalPuts": 177007062,
    "totalPutsChange": 15871228,
    "putCallRatio": 1.1115,
    "lastPutCallRatio": 0.8906,
    "putCallRatioChange": 22.0894
  }
]
```


## Industry Performance SummaryAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/industry-summary

### Endpoint

https://financialmodelingprep.com/stable/institutional-ownership/industry-summary?year=2023&quarter=3&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| year * | string | 2023 |
| quarter * | string | 3 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/institutional-ownership/industry-summary?year=2023&quarter=3
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "industryTitle": "ABRASIVE, ASBESTOS & MISC NONMETALLIC MINERAL PRODS",
    "industryValue": 10979226300,
    "date": "2023-09-30"
  }
]
```


## Financial EstimatesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/financial-estimates

### Endpoint

https://financialmodelingprep.com/stable/analyst-estimates?symbol=AAPL&period=annual&page=0&limit=10&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| period * | string | annualquarter |
| page | number | 0 |
| limit | number | 10 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/analyst-estimates?symbol=AAPL&period=annual&page=0&limit=10
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2029-09-28",
    "revenueLow": 483092500000,
    "revenueHigh": 483093500000,
    "revenueAvg": 483093000000,
    "ebitdaLow": 155952166036,
    "ebitdaHigh": 155952488856,
    "ebitdaAvg": 155952327446,
    "ebitLow": 140628295747,
    "ebitHigh": 140628586847,
    "ebitAvg": 140628441297,
    "netIncomeLow": 139446957701,
    "netIncomeHigh": 157185372990,
    "netIncomeAvg": 149150359609,
    "sgaExpenseLow": 31694652812,
    "sgaExpenseHigh": 31694718420,
    "sgaExpenseAvg": 31694685616,
    "epsAvg": 9.68,
    "epsHigh": 10.20148,
    "epsLow": 9.05024,
    "numAnalystsRevenue": 16,
    "numAnalystsEps": 6
  }
]
```


## Ratings SnapshotAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/ratings-snapshot

### Endpoint

https://financialmodelingprep.com/stable/ratings-snapshot?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/ratings-snapshot?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "rating": "A-",
    "overallScore": 4,
    "discountedCashFlowScore": 3,
    "returnOnEquityScore": 5,
    "returnOnAssetsScore": 5,
    "debtToEquityScore": 4,
    "priceToEarningsScore": 2,
    "priceToBookScore": 1
  }
]
```


## Historical RatingsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-ratings

### Endpoint

https://financialmodelingprep.com/stable/ratings-historical?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 1 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/ratings-historical?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-02-04",
    "rating": "A-",
    "overallScore": 4,
    "discountedCashFlowScore": 3,
    "returnOnEquityScore": 5,
    "returnOnAssetsScore": 5,
    "debtToEquityScore": 4,
    "priceToEarningsScore": 2,
    "priceToBookScore": 1
  }
]
```


## Price Target SummaryAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/price-target-summary

### Endpoint

https://financialmodelingprep.com/stable/price-target-summary?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/price-target-summary?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "lastMonthCount": 1,
    "lastMonthAvgPriceTarget": 200.75,
    "lastQuarterCount": 3,
    "lastQuarterAvgPriceTarget": 204.2,
    "lastYearCount": 48,
    "lastYearAvgPriceTarget": 232.99,
    "allTimeCount": 167,
    "allTimeAvgPriceTarget": 201.21,
    "publishers": "[\"Benzinga\",\"StreetInsider\",\"TheFly\",\"Pulse 2.0\",\"TipRanks Contributor\",\"MarketWatch\",\"Investing\",\"Barrons\",\"Investor's Business Daily\"]"
  }
]
```


## Price Target ConsensusAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/price-target-consensus

### Endpoint

https://financialmodelingprep.com/stable/price-target-consensus?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/price-target-consensus?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "targetHigh": 300,
    "targetLow": 200,
    "targetConsensus": 251.7,
    "targetMedian": 258
  }
]
```


## Stock GradesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/grades

### Endpoint

https://financialmodelingprep.com/stable/grades?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/grades?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-01-31",
    "gradingCompany": "Morgan Stanley",
    "previousGrade": "Overweight",
    "newGrade": "Overweight",
    "action": "maintain"
  }
]
```


## Historical Stock GradesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-grades

### Endpoint

https://financialmodelingprep.com/stable/grades-historical?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/grades-historical?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-02-01",
    "analystRatingsBuy": 8,
    "analystRatingsHold": 14,
    "analystRatingsSell": 2,
    "analystRatingsStrongSell": 2
  }
]
```


## Stock Grades SummaryAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/grades-summary

### Endpoint

https://financialmodelingprep.com/stable/grades-consensus?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/grades-consensus?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "strongBuy": 1,
    "buy": 29,
    "hold": 11,
    "sell": 4,
    "strongSell": 0,
    "consensus": "Buy"
  }
]
```


## Market Sector Performance SnapshotAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/sector-performance-snapshot

### Endpoint

https://financialmodelingprep.com/stable/sector-performance-snapshot?date=2024-02-01&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| date * | string | 2024-02-01 |
| exchange | string | NASDAQ |
| sector | string | Energy |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sector-performance-snapshot?date=2024-02-01
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-02-01",
    "sector": "Basic Materials",
    "exchange": "NASDAQ",
    "averageChange": -0.31481377464310634
  }
]
```


## Industry Performance SnapshotAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/industry-performance-snapshot

### Endpoint

https://financialmodelingprep.com/stable/industry-performance-snapshot?date=2024-02-01&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| date * | string | 2024-02-01 |
| exchange | string | NASDAQ |
| industry | string | Biotechnology |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/industry-performance-snapshot?date=2024-02-01
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-02-01",
    "industry": "Advertising Agencies",
    "exchange": "NASDAQ",
    "averageChange": 3.8660194344955996
  }
]
```


## Historical Market Sector PerformanceAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-sector-performance

### Endpoint

https://financialmodelingprep.com/stable/historical-sector-performance?sector=Energy&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | string | 2024-02-01 |
| exchange | string | NASDAQ |
| sector * | string | Energy |
| to | string | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-sector-performance?sector=Energy
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-02-01",
    "sector": "Energy",
    "exchange": "NASDAQ",
    "averageChange": 0.6397534025664513
  }
]
```


## Historical Industry PerformanceAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-industry-performance

### Endpoint

https://financialmodelingprep.com/stable/historical-industry-performance?industry=Biotechnology&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| industry * | string | Biotechnology |
| exchange | string | NASDAQ |
| from | string | 2024-02-01 |
| to | string | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-industry-performance?industry=Biotechnology
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-02-01",
    "industry": "Biotechnology",
    "exchange": "NASDAQ",
    "averageChange": 1.1479066960358322
  }
]
```


## Sector PE SnapshotAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/sector-pe-snapshot

### Endpoint

https://financialmodelingprep.com/stable/sector-pe-snapshot?date=2024-02-01&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| date * | string | 2024-02-01 |
| exchange | string | NASDAQ |
| sector | string | Energy |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sector-pe-snapshot?date=2024-02-01
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-02-01",
    "sector": "Basic Materials",
    "exchange": "NASDAQ",
    "pe": 15.687711758428254
  }
]
```


## Industry PE SnapshotAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/industry-pe-snapshot

### Endpoint

https://financialmodelingprep.com/stable/industry-pe-snapshot?date=2024-02-01&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| date * | string | 2024-02-01 |
| exchange | string | NASDAQ |
| industry | string | Biotechnology |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/industry-pe-snapshot?date=2024-02-01
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-02-01",
    "industry": "Advertising Agencies",
    "exchange": "NASDAQ",
    "pe": 71.09601665201151
  }
]
```


## Historical Sector PEAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-sector-pe

### Endpoint

https://financialmodelingprep.com/stable/historical-sector-pe?sector=Energy&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from | string | 2024-02-01 |
| exchange | string | NASDAQ |
| sector * | string | Energy |
| to | string | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-sector-pe?sector=Energy
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-02-01",
    "sector": "Energy",
    "exchange": "NASDAQ",
    "pe": 14.411400922841464
  }
]
```


## Historical Industry PEAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-industry-pe

### Endpoint

https://financialmodelingprep.com/stable/historical-industry-pe?industry=Biotechnology&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| industry * | string | Biotechnology |
| exchange | string | NASDAQ |
| from | string | 2024-02-01 |
| to | string | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-industry-pe?industry=Biotechnology
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-02-01",
    "industry": "Biotechnology",
    "exchange": "NASDAQ",
    "pe": 10.181600321811821
  }
]
```


## Biggest Stock GainersAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/biggest-gainers

### Endpoint

https://financialmodelingprep.com/stable/biggest-gainers?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/biggest-gainers
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "LTRY",
    "price": 0.5876,
    "name": "Lottery.com Inc.",
    "change": 0.2756,
    "changesPercentage": 88.3333,
    "exchange": "NASDAQ"
  }
]
```


## Biggest Stock LosersAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/biggest-losers

### Endpoint

https://financialmodelingprep.com/stable/biggest-losers?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/biggest-losers
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "IDEX",
    "price": 0.0021,
    "name": "Ideanomics, Inc.",
    "change": -0.0029,
    "changesPercentage": -58,
    "exchange": "NASDAQ"
  }
]
```


## Top Traded StocksAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/most-active

### Endpoint

https://financialmodelingprep.com/stable/most-actives?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/most-actives
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "LUCY",
    "price": 5.03,
    "name": "Innovative Eyewear, Inc.",
    "change": -0.01,
    "changesPercentage": -0.1984,
    "exchange": "NASDAQ"
  }
]
```


## Simple Moving AverageAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/simple-moving-average

### Endpoint

https://financialmodelingprep.com/stable/technical-indicators/sma?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| periodLength * | number | 10 |
| timeframe * | string | 1min5min15min30min1hour4hour1day |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/technical-indicators/sma?symbol=AAPL&periodLength=10&timeframe=1day
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "sma": 231.215
  }
]
```


## Exponential Moving AverageAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/exponential-moving-average

### Endpoint

https://financialmodelingprep.com/stable/technical-indicators/ema?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| periodLength * | number | 10 |
| timeframe * | string | 1min5min15min30min1hour4hour1day |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/technical-indicators/ema?symbol=AAPL&periodLength=10&timeframe=1day
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "ema": 232.8406611792779
  }
]
```


## Weighted Moving AverageAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/weighted-moving-average

### Endpoint

https://financialmodelingprep.com/stable/technical-indicators/wma?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| periodLength * | number | 10 |
| timeframe * | string | 1min5min15min30min1hour4hour1day |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/technical-indicators/wma?symbol=AAPL&periodLength=10&timeframe=1day
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "wma": 233.04745454545454
  }
]
```


## Double Exponential Moving AverageAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/double-exponential-moving-average

### Endpoint

https://financialmodelingprep.com/stable/technical-indicators/dema?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| periodLength * | number | 10 |
| timeframe * | string | 1min5min15min30min1hour4hour1day |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/technical-indicators/dema?symbol=AAPL&periodLength=10&timeframe=1day
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "dema": 232.10592058582725
  }
]
```


## Triple Exponential Moving AverageAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/triple-exponential-moving-average

### Endpoint

https://financialmodelingprep.com/stable/technical-indicators/tema?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| periodLength * | number | 10 |
| timeframe * | string | 1min5min15min30min1hour4hour1day |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/technical-indicators/tema?symbol=AAPL&periodLength=10&timeframe=1day
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "tema": 233.66383715917516
  }
]
```


## Relative Strength IndexAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/relative-strength-index

### Endpoint

https://financialmodelingprep.com/stable/technical-indicators/rsi?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| periodLength * | number | 10 |
| timeframe * | string | 1min5min15min30min1hour4hour1day |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/technical-indicators/rsi?symbol=AAPL&periodLength=10&timeframe=1day
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "rsi": 47.64507340768903
  }
]
```


## Standard DeviationAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/standard-deviation

### Endpoint

https://financialmodelingprep.com/stable/technical-indicators/standarddeviation?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| periodLength * | number | 10 |
| timeframe * | string | 1min5min15min30min1hour4hour1day |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/technical-indicators/standarddeviation?symbol=AAPL&periodLength=10&timeframe=1day
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "standardDeviation": 6.139182763202282
  }
]
```


## WilliamsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/williams

### Endpoint

https://financialmodelingprep.com/stable/technical-indicators/williams?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| periodLength * | number | 10 |
| timeframe * | string | 1min5min15min30min1hour4hour1day |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/technical-indicators/williams?symbol=AAPL&periodLength=10&timeframe=1day
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "williams": -52.51824817518242
  }
]
```


## Average Directional IndexAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/average-directional-index

### Endpoint

https://financialmodelingprep.com/stable/technical-indicators/adx?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| periodLength * | number | 10 |
| timeframe * | string | 1min5min15min30min1hour4hour1day |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/technical-indicators/adx?symbol=AAPL&periodLength=10&timeframe=1day
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "adx": 26.414065772772613
  }
]
```


## ETF & Fund HoldingsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/holdings

### Endpoint

https://financialmodelingprep.com/stable/etf/holdings?symbol=SPY&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | SPY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/etf/holdings?symbol=SPY
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "SPY",
    "asset": "AAPL",
    "name": "APPLE INC",
    "isin": "US0378331005",
    "securityCusip": "037833100",
    "sharesNumber": 188106081,
    "weightPercentage": 7.137,
    "marketValue": 44744793487.47,
    "updatedAt": "2025-01-16 05:01:09",
    "updated": "2025-02-04 19:02:31"
  }
]
```


## ETF & Mutual Fund InformationAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/information

### Endpoint

https://financialmodelingprep.com/stable/etf/info?symbol=SPY&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | SPY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/etf/info?symbol=SPY
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "SPY",
    "name": "SPDR S&P 500 ETF Trust",
    "description": "The Trust seeks to achieve its investment objective by holding a portfolio of the common stocks that are included in the index (the “Portfolio”), with the weight of each stock in the Portfolio substantially corresponding to the weight of such stock in the index.",
    "isin": "US78462F1030",
    "assetClass": "Equity",
    "securityCusip": "78462F103",
    "domicile": "US",
    "website": "https://www.ssga.com/us/en/institutional/etfs/spdr-sp-500-etf-trust-spy",
    "etfCompany": "SPDR",
    "expenseRatio": 0.0945,
    "assetsUnderManagement": 633120180000,
    "avgVolume": 46396400,
    "inceptionDate": "1993-01-22",
    "nav": 603.64,
    "navCurrency": "USD",
    "holdingsCount": 503,
    "updatedAt": "2024-12-03T20:32:48.873Z",
    "sectorsList": [
      {
        "industry": "Basic Materials",
        "exposure": 1.97
      },
      {
        "industry": "Communication Services",
        "exposure": 8.87
      },
      {
        "industry": "Consumer Cyclical",
        "exposure": 9.84
      }
    ]
  }
]
```


## ETF & Fund Country AllocationAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/country-weighting

### Endpoint

https://financialmodelingprep.com/stable/etf/country-weightings?symbol=SPY&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | SPY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/etf/country-weightings?symbol=SPY
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "country": "United States",
    "weightPercentage": "97.29%"
  }
]
```


## ETF Asset ExposureAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/etf-asset-exposure

### Endpoint

https://financialmodelingprep.com/stable/etf/asset-exposure?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/etf/asset-exposure?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "ZECP",
    "asset": "AAPL",
    "sharesNumber": 5482,
    "weightPercentage": 5.86,
    "marketValue": 0
  }
]
```


## ETF Sector WeightingAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/sector-weighting

### Endpoint

https://financialmodelingprep.com/stable/etf/sector-weightings?symbol=SPY&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | SPY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/etf/sector-weightings?symbol=SPY
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "SPY",
    "sector": "Basic Materials",
    "weightPercentage": 1.97
  }
]
```


## Mutual Fund & ETF DisclosureAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/latest-disclosures

### Endpoint

https://financialmodelingprep.com/stable/funds/disclosure-holders-latest?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/funds/disclosure-holders-latest?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0000106444",
    "holder": "VANGUARD FIXED INCOME SECURITIES FUNDS",
    "shares": 67030000,
    "dateReported": "2024-07-31",
    "change": 0,
    "weightPercent": 0.03840197
  }
]
```


## Mutual Fund DisclosuresAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/mutual-fund-disclosures

### Endpoint

https://financialmodelingprep.com/stable/funds/disclosure?symbol=VWO&year=2023&quarter=4&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | VWO |
| year * | string | 2023 |
| quarter * | string | 4 |
| cik | string | 0000857489 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/funds/disclosure?symbol=VWO&year=2023&quarter=4
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0000857489",
    "date": "2023-10-31",
    "acceptedDate": "2023-12-28 09:26:13",
    "symbol": "000089.SZ",
    "name": "Shenzhen Airport Co Ltd",
    "lei": "3003009W045RIKRBZI44",
    "title": "SHENZ AIRPORT-A",
    "cusip": "N/A",
    "isin": "CNE000000VK1",
    "balance": 2438784,
    "units": "NS",
    "cur_cd": "CNY",
    "valUsd": 2255873.6,
    "pctVal": 0.0023838966190458215,
    "payoffProfile": "Long",
    "assetCat": "EC",
    "issuerCat": "CORP",
    "invCountry": "CN",
    "isRestrictedSec": "N",
    "fairValLevel": "2",
    "isCashCollateral": "N",
    "isNonCashCollateral": "N",
    "isLoanByFund": "N"
  }
]
```


## Mutual Fund & ETF Disclosure Name SearchAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/disclosures-name-search

### Endpoint

https://financialmodelingprep.com/stable/funds/disclosure-holders-search?name=Federated&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| name * | string | Federated Hermes Government Income Securities, Inc. |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/funds/disclosure-holders-search?name=Federated Hermes Government Income Securities, Inc.
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "FGOAX",
    "cik": "0000355691",
    "classId": "C000024574",
    "seriesId": "S000009042",
    "entityName": "Federated Hermes Government Income Securities, Inc.",
    "entityOrgType": "30",
    "seriesName": "Federated Hermes Government Income Securities, Inc.",
    "className": "Class A Shares",
    "reportingFileNumber": "811-03266",
    "address": "4000 ERICSSON DRIVE",
    "city": "WARRENDALE",
    "zipCode": "15086-7561",
    "state": "PA"
  }
]
```


## Fund & ETF Disclosures by DateAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/disclosures-dates

### Endpoint

https://financialmodelingprep.com/stable/funds/disclosure-dates?symbol=VWO&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | VWO |
| cik | string | 0000036405 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/funds/disclosure-dates?symbol=VWO
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-10-31",
    "year": 2024,
    "quarter": 4
  }
]
```


## Latest 8-K SEC FilingsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/8k-latest

### Endpoint

https://financialmodelingprep.com/stable/sec-filings-8k?from=2024-01-01&to=2024-03-01&page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from * | string | 2024-01-01 |
| to * | string | 2024-03-01 |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sec-filings-8k?from=2024-01-01&to=2024-03-01&page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "BROS",
    "cik": "0001866581",
    "filingDate": "2024-03-01 00:00:00",
    "acceptedDate": "2024-02-29 21:43:41",
    "formType": "8-K",
    "hasFinancials": false,
    "link": "https://www.sec.gov/Archives/edgar/data/1866581/000162828024008098/0001628280-24-008098-index.htm",
    "finalLink": "https://www.sec.gov/Archives/edgar/data/1866581/000162828024008098/exhibit11-8xkfeb2024.htm"
  }
]
```


## Latest SEC FilingsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/financials-latest

### Endpoint

https://financialmodelingprep.com/stable/sec-filings-financials?from=2024-01-01&to=2024-03-01&page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| from * | string | 2024-01-01 |
| to * | string | 2024-03-01 |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sec-filings-financials?from=2024-01-01&to=2024-03-01&page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "MTZ",
    "cik": "0000015615",
    "filingDate": "2024-03-01 00:00:00",
    "acceptedDate": "2024-02-29 21:24:32",
    "formType": "8-K",
    "hasFinancials": true,
    "link": "https://www.sec.gov/Archives/edgar/data/15615/000119312524054015/0001193125-24-054015-index.htm",
    "finalLink": "https://www.sec.gov/Archives/edgar/data/15615/000119312524054015/d775448dex991.htm"
  }
]
```


## SEC Filings By Form TypeAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-by-form-type

### Endpoint

https://financialmodelingprep.com/stable/sec-filings-search/form-type?formType=8-K&from=2024-01-01&to=2024-03-01&page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| formType * | string | 8-K |
| from * | string | 2024-01-01 |
| to * | string | 2024-03-01 |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sec-filings-search/form-type?formType=8-K&from=2024-01-01&to=2024-03-01&page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "BROS",
    "cik": "0001866581",
    "filingDate": "2024-03-01 00:00:00",
    "acceptedDate": "2024-02-29 21:43:41",
    "formType": "8-K",
    "link": "https://www.sec.gov/Archives/edgar/data/1866581/000162828024008098/0001628280-24-008098-index.htm",
    "finalLink": "https://www.sec.gov/Archives/edgar/data/1866581/000162828024008098/exhibit11-8xkfeb2024.htm"
  }
]
```


## SEC Filings By SymbolAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-by-symbol

### Endpoint

https://financialmodelingprep.com/stable/sec-filings-search/symbol?symbol=AAPL&from=2024-01-01&to=2024-03-01&page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| from * | string | 2024-01-01 |
| to * | string | 2024-03-01 |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sec-filings-search/symbol?symbol=AAPL&from=2024-01-01&to=2024-03-01&page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "cik": "0000320193",
    "filingDate": "2024-02-28 00:00:00",
    "acceptedDate": "2024-02-28 17:09:05",
    "formType": "8-K",
    "link": "https://www.sec.gov/Archives/edgar/data/320193/000114036124010155/0001140361-24-010155-index.htm",
    "finalLink": "https://www.sec.gov/Archives/edgar/data/320193/000114036124010155/ny20022580x1_image01.jpg"
  }
]
```


## SEC Filings By CIKAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-by-cik

### Endpoint

https://financialmodelingprep.com/stable/sec-filings-search/cik?cik=0000320193&from=2024-01-01&to=2024-03-01&page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| cik * | string | 0000320193 |
| from * | string | 2024-01-01 |
| to * | string | 2024-03-01 |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sec-filings-search/cik?cik=0000320193&from=2024-01-01&to=2024-03-01&page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "cik": "0000320193",
    "filingDate": "2024-02-28 00:00:00",
    "acceptedDate": "2024-02-28 17:09:05",
    "formType": "8-K",
    "link": "https://www.sec.gov/Archives/edgar/data/320193/000114036124010155/0001140361-24-010155-index.htm",
    "finalLink": "https://www.sec.gov/Archives/edgar/data/320193/000114036124010155/ny20022580x1_image01.jpg"
  }
]
```


## SEC Filings By NameAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-by-name

### Endpoint

https://financialmodelingprep.com/stable/sec-filings-company-search/name?company=Berkshire&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| company * | string | Berkshire |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sec-filings-company-search/name?company=Berkshire
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "None",
    "name": "BERKSHIRE MULTIFAMILY VALUE FUND II LP",
    "cik": "0001418405",
    "sicCode": "",
    "industryTitle": "",
    "businessAddress": "c/o Berkshire Property Advisors LLC, Boston MA 02108",
    "phoneNumber": "(617) 646-2300"
  }
]
```


## SEC Filings Company Search By SymbolAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/company-search-by-symbol

### Endpoint

https://financialmodelingprep.com/stable/sec-filings-company-search/symbol?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sec-filings-company-search/symbol?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "name": "APPLE INC.",
    "cik": "0000320193",
    "sicCode": "3571",
    "industryTitle": "ELECTRONIC COMPUTERS",
    "businessAddress": "ONE APPLE PARK WAY, CUPERTINO CA 95014",
    "phoneNumber": "(408) 996-1010"
  }
]
```


## SEC Filings Company Search By CIKAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/company-search-by-cik

### Endpoint

https://financialmodelingprep.com/stable/sec-filings-company-search/cik?cik=0000320193&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| cik * | string | 0000320193 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sec-filings-company-search/cik?cik=0000320193
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "name": "APPLE INC.",
    "cik": "0000320193",
    "sicCode": "3571",
    "industryTitle": "ELECTRONIC COMPUTERS",
    "businessAddress": "ONE APPLE PARK WAY, CUPERTINO CA 95014",
    "phoneNumber": "(408) 996-1010"
  }
]
```


## SEC Company Full ProfileAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/sec-company-full-profile

### Endpoint

https://financialmodelingprep.com/stable/sec-profile?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| cik-A | string | 320193 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sec-profile?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "cik": "0000320193",
    "registrantName": "Apple Inc.",
    "sicCode": "3571",
    "sicDescription": "Electronic Computers",
    "sicGroup": "Consumer Electronics",
    "isin": "US0378331005",
    "businessAddress": "ONE APPLE PARK WAY,CUPERTINO CA 95014,(408) 996-1010",
    "mailingAddress": "ONE APPLE PARK WAY,CUPERTINO CA 95014",
    "phoneNumber": "(408) 996-1010",
    "postalCode": "95014",
    "city": "Cupertino",
    "state": "CA",
    "country": "US",
    "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allow customers to discov...",
    "ceo": "Mr. Timothy D. Cook",
    "website": "https://www.apple.com",
    "exchange": "NASDAQ",
    "stateLocation": "CA",
    "stateOfIncorporation": "CA",
    "fiscalYearEnd": "09-28",
    "ipoDate": "1980-12-12",
    "employees": "164000",
    "secFilingsUrl": "https://www.sec.gov/cgi-bin/browse-edgar?CIK=0000320193",
    "taxIdentificationNumber": "94-2404110",
    "fiftyTwoWeekRange": "164.08 - 260.1",
    "isActive": true,
    "assetType": "stock",
    "openFigiComposite": "BBG000B9XRY4",
    "priceCurrency": "USD",
    "marketSector": "Technology",
    "securityType": null,
    "isEtf": false,
    "isAdr": false,
    "isFund": false
  }
]
```


## Industry Classification ListAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/industry-classification-list

### Endpoint

https://financialmodelingprep.com/stable/standard-industrial-classification-list?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| industryTitle | string | SERVICES |
| sicCode | string | 7371 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/standard-industrial-classification-list
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "office": "Office of Life Sciences",
    "sicCode": "100",
    "industryTitle": "AGRICULTURAL PRODUCTION-CROPS"
  }
]
```


## Industry Classification SearchAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/industry-classification-search

### Endpoint

https://financialmodelingprep.com/stable/industry-classification-search?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol | string | AAPL |
| cik | string | 320193 |
| sicCode | string | 7371 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/industry-classification-search
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "name": "APPLE INC.",
    "cik": "0000320193",
    "sicCode": "3571",
    "industryTitle": "ELECTRONIC COMPUTERS",
    "businessAddress": "['ONE APPLE PARK WAY', 'CUPERTINO CA 95014']",
    "phoneNumber": "(408) 996-1010"
  }
]
```


## All Industry ClassificationAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/all-industry-classification

### Endpoint

https://financialmodelingprep.com/stable/all-industry-classification?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/all-industry-classification
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "0Q16.L",
    "name": "BANK OF AMERICA CORP /DE/",
    "cik": "0000070858",
    "sicCode": "6021",
    "industryTitle": "NATIONAL COMMERCIAL BANKS",
    "businessAddress": "['BANK OF AMERICA CORPORATE CENTER', 'CHARLOTTE NC 28255']",
    "phoneNumber": "7043868486"
  }
]
```


## Latest Insider TradingAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/latest-insider-trade

### Endpoint

https://financialmodelingprep.com/stable/insider-trading/latest?page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| date | date | 2025-09-09 |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/insider-trading/latest?page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "APA",
    "filingDate": "2025-02-04",
    "transactionDate": "2025-02-01",
    "reportingCik": "0001380034",
    "companyCik": "0001841666",
    "transactionType": "M-Exempt",
    "securitiesOwned": 104398,
    "reportingName": "Hoyt Rebecca A",
    "typeOfOwner": "officer: Sr. VP, Chief Acct Officer",
    "acquisitionOrDisposition": "A",
    "directOrIndirect": "D",
    "formType": "4",
    "securitiesTransacted": 3450,
    "price": 0,
    "securityName": "Common Stock",
    "url": "https://www.sec.gov/Archives/edgar/data/1841666/000194906025000035/0001949060-25-000035-index.htm"
  }
]
```


## Search Insider TradesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-insider-trades

### Endpoint

https://financialmodelingprep.com/stable/insider-trading/search?page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol | string | AAPL |
| page | number | 0 |
| limit | number | 100 |
| reportingCik | string | 0001496686 |
| companyCik | string | 0000320193 |
| transactionType | string | S-Sale |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/insider-trading/search?page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "filingDate": "2025-02-04",
    "transactionDate": "2025-02-03",
    "reportingCik": "0001214128",
    "companyCik": "0000320193",
    "transactionType": "S-Sale",
    "securitiesOwned": 4159576,
    "reportingName": "LEVINSON ARTHUR D",
    "typeOfOwner": "director",
    "acquisitionOrDisposition": "D",
    "directOrIndirect": "D",
    "formType": "4",
    "securitiesTransacted": 1516,
    "price": 226.3501,
    "securityName": "Common Stock",
    "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019325000019/0000320193-25-000019-index.htm"
  }
]
```


## Search Insider Trades by Reporting NameAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/search-reporting-name

### Endpoint

https://financialmodelingprep.com/stable/insider-trading/reporting-name?name=Zuckerberg&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| name * | string | Zuckerberg |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/insider-trading/reporting-name?name=Zuckerberg
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "reportingCik": "0001548760",
    "reportingName": "Zuckerberg Mark"
  }
]
```


## All Insider Transaction TypesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/all-transaction-types

### Endpoint

https://financialmodelingprep.com/stable/insider-trading-transaction-type?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/insider-trading-transaction-type
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "transactionType": "A-Award"
  }
]
```


## Insider Trade StatisticsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/insider-trade-statistics

### Endpoint

https://financialmodelingprep.com/stable/insider-trading/statistics?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/insider-trading/statistics?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "cik": "0000320193",
    "year": 2024,
    "quarter": 4,
    "acquiredTransactions": 6,
    "disposedTransactions": 38,
    "acquiredDisposedRatio": 0.1579,
    "totalAcquired": 994544,
    "totalDisposed": 2297088,
    "averageAcquired": 165757.3333,
    "averageDisposed": 60449.6842,
    "totalPurchases": 0,
    "totalSales": 22
  }
]
```


## Acquisition OwnershipAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/acquisition-ownership

### Endpoint

https://financialmodelingprep.com/stable/acquisition-of-beneficial-ownership?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| limit | number | 2000 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/acquisition-of-beneficial-ownership?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0000320193",
    "symbol": "AAPL",
    "filingDate": "2024-02-14",
    "acceptedDate": "2024-02-14",
    "cusip": "037833100",
    "nameOfReportingPerson": "National Indemnity Company",
    "citizenshipOrPlaceOfOrganization": "State of Nebraska",
    "soleVotingPower": "0",
    "sharedVotingPower": "755059877",
    "soleDispositivePower": "0",
    "sharedDispositivePower": "755059877",
    "amountBeneficiallyOwned": "755059877",
    "percentOfClass": "4.8",
    "typeOfReportingPerson": "IC, EP, IN, CO",
    "url": "https://www.sec.gov/Archives/edgar/data/320193/000119312524036431/d751537dsc13ga.htm"
  }
]
```


## Stock Market Indexes ListAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/indexes-list

### Endpoint

https://financialmodelingprep.com/stable/index-list?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/index-list
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "^TTIN",
    "name": "S&P/TSX Capped Industrials Index",
    "exchange": "TSX",
    "currency": "CAD"
  }
]
```


## Index QuoteAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/index-quote

### Endpoint

https://financialmodelingprep.com/stable/quote?symbol=^GSPC&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | ^GSPC |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/quote?symbol=^GSPC
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "^GSPC",
    "name": "S&P 500",
    "price": 6366.13,
    "changePercentage": 0.11354,
    "change": 7.22,
    "volume": 1498664000,
    "dayLow": 6360.57,
    "dayHigh": 6379.54,
    "yearHigh": 6379.54,
    "yearLow": 4835.04,
    "marketCap": 0,
    "priceAvg50": 6068.663,
    "priceAvg200": 5880.0864,
    "exchange": "INDEX",
    "open": 6368.6,
    "previousClose": 6358.91,
    "timestamp": 1753374601
  }
]
```


## Index Short QuoteAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/index-quote-short

### Endpoint

https://financialmodelingprep.com/stable/quote-short?symbol=^GSPC&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | ^GSPC |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/quote-short?symbol=^GSPC
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "^GSPC",
    "price": 6366.13,
    "change": 7.22,
    "volume": 1498664000
  }
]
```


## All Index QuotesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/all-index-quotes

### Endpoint

https://financialmodelingprep.com/stable/batch-index-quotes?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| short | boolean | true |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-index-quotes
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "^DJBGIE",
    "price": 4155.76,
    "change": 1.09,
    "volume": 0
  }
]
```


## Historical Index Light ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/index-historical-price-eod-light

### Endpoint

https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=^GSPC&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | ^GSPC |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=^GSPC
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "^GSPC",
    "date": "2025-07-24",
    "price": 6365.77,
    "volume": 1499302000
  }
]
```


## Historical Index Full ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/index-historical-price-eod-full

### Endpoint

https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=^GSPC&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | ^GSPC |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=^GSPC
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "^GSPC",
    "date": "2025-07-24",
    "open": 6368.6,
    "high": 6379.54,
    "low": 6360.57,
    "close": 6365.77,
    "volume": 1499302000,
    "change": -2.83,
    "changePercent": -0.04443677,
    "vwap": 6368.63
  }
]
```


## 1-Minute Interval Index PriceAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/index-intraday-1-min

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/1min?symbol=^GSPC&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | ^GSPC |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/1min?symbol=^GSPC
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-07-24 12:29:00",
    "open": 6365.34,
    "low": 6365.34,
    "high": 6366.09,
    "close": 6366.09,
    "volume": 4428000
  }
]
```


## 5-Minute Interval Index PriceAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/index-intraday-5-min

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/5min?symbol=^GSPC&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | ^GSPC |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/5min?symbol=^GSPC
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-07-24 12:30:00",
    "open": 6366.18,
    "low": 6365.57,
    "high": 6366.18,
    "close": 6365.69,
    "volume": 1574690
  }
]
```


## 1-Hour Interval Index PriceAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/index-intraday-1-hour

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=^GSPC&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | ^GSPC |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=^GSPC
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-07-24 12:30:00",
    "open": 6366.18,
    "low": 6365.57,
    "high": 6366.18,
    "close": 6365.69,
    "volume": 1574690
  }
]
```


## S&P 500 IndexAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/sp-500

### Endpoint

https://financialmodelingprep.com/stable/sp500-constituent?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/sp500-constituent
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "DDOG",
    "name": "Datadog",
    "sector": "Technology",
    "subSector": "Software - Application",
    "headQuarter": "New York City, New York",
    "dateFirstAdded": "2025-07-09",
    "cik": "0001561550",
    "founded": "2010"
  }
]
```


## Nasdaq IndexAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/nasdaq

### Endpoint

https://financialmodelingprep.com/stable/nasdaq-constituent?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/nasdaq-constituent
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "ADBE",
    "name": "Adobe Inc.",
    "sector": "Technology",
    "subSector": "Software - Infrastructure",
    "headQuarter": "San Jose, CA",
    "dateFirstAdded": null,
    "cik": "0000796343",
    "founded": "1982-12-01"
  }
]
```


## Dow JonesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/dow-jones

### Endpoint

https://financialmodelingprep.com/stable/dowjones-constituent?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/dowjones-constituent
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "NVDA",
    "name": "Nvidia",
    "sector": "Technology",
    "subSector": "Semiconductors",
    "headQuarter": "Santa Clara, CA",
    "dateFirstAdded": "2024-11-08",
    "cik": "0001045810",
    "founded": "1993-04-05"
  }
]
```


## Historical S&P 500API

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-sp-500

### Endpoint

https://financialmodelingprep.com/stable/historical-sp500-constituent?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-sp500-constituent
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "dateAdded": "July 9, 2025",
    "addedSecurity": "Datadog",
    "removedTicker": "JNPR",
    "removedSecurity": "Juniper Networks",
    "date": "2025-07-08",
    "symbol": "DDOG",
    "reason": "S&P 500 constituent Hewlett Packard Enterprise Co. acquired Juniper Networks."
  }
]
```


## Historical NasdaqAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-nasdaq

### Endpoint

https://financialmodelingprep.com/stable/historical-nasdaq-constituent?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-nasdaq-constituent
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "dateAdded": "May 19, 2025",
    "addedSecurity": "Shopify",
    "removedTicker": "MDB",
    "removedSecurity": "MongoDB",
    "date": "2025-05-18",
    "symbol": "SHOP",
    "reason": "MongoDB did not meet the minimum monthly weight requirements."
  }
]
```


## Historical Dow JonesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/historical-dow-jones

### Endpoint

https://financialmodelingprep.com/stable/historical-dowjones-constituent?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-dowjones-constituent
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "dateAdded": "November 8, 2024",
    "addedSecurity": "Nvidia",
    "removedTicker": "INTC",
    "removedSecurity": "Intel Corporation",
    "date": "2024-11-07",
    "symbol": "NVDA",
    "reason": "Market capitalization change"
  }
]
```


## Global Exchange Market HoursAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/exchange-market-hours

### Endpoint

https://financialmodelingprep.com/stable/exchange-market-hours?exchange=NASDAQ&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| exchange * | string | NASDAQ |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/exchange-market-hours?exchange=NASDAQ
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "exchange": "NASDAQ",
    "name": "NASDAQ Global Market",
    "openingHour": "09:30 AM -04:00",
    "closingHour": "04:00 PM -04:00",
    "timezone": "America/New_York",
    "isMarketOpen": true
  }
]
```


## Holidays By ExchangeAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/holidays-by-exchange

### Endpoint

https://financialmodelingprep.com/stable/holidays-by-exchange?exchange=NASDAQ&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| exchange * | string | NASDAQ |
| from | date | 2024-12-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/holidays-by-exchange?exchange=NASDAQ
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "exchange": "NASDAQ",
    "date": "2025-06-19",
    "name": "Juneteenth",
    "isClosed": true,
    "adjOpenTime": null,
    "adjCloseTime": null
  }
]
```


## All Exchange Market HoursAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/all-exchange-market-hours

### Endpoint

https://financialmodelingprep.com/stable/all-exchange-market-hours?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/all-exchange-market-hours
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "exchange": "ASX",
    "name": "Australian Stock Exchange",
    "openingHour": "10:00 AM +10:00",
    "closingHour": "04:00 PM +10:00",
    "timezone": "Australia/Sydney",
    "isMarketOpen": false
  }
]
```


## Commodities ListAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/commodities-list

### Endpoint

https://financialmodelingprep.com/stable/commodities-list?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/commodities-list
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "HEUSX",
    "name": "Lean Hogs Futures",
    "exchange": null,
    "tradeMonth": "Dec",
    "currency": "USX"
  }
]
```


## Commodities QuoteAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/commodities-quote

### Endpoint

https://financialmodelingprep.com/stable/quote?symbol=GCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | GCUSD |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/quote?symbol=GCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "GCUSD",
    "name": "Gold Futures",
    "price": 3375.3,
    "changePercentage": -0.65635,
    "change": -22.3,
    "volume": 170936,
    "dayLow": 3355.2,
    "dayHigh": 3401.1,
    "yearHigh": 3509.9,
    "yearLow": 2354.6,
    "marketCap": null,
    "priceAvg50": 3358.706,
    "priceAvg200": 3054.501,
    "exchange": "COMMODITY",
    "open": 3398.6,
    "previousClose": 3397.6,
    "timestamp": 1753372205
  }
]
```


## Commodities Quote ShortAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/commodities-quote-short

### Endpoint

https://financialmodelingprep.com/stable/quote-short?symbol=GCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | GCUSD |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/quote-short?symbol=GCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "GCUSD",
    "price": 3375.3,
    "change": -22.3,
    "volume": 170936
  }
]
```


## All Commodities QuotesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/all-commodities-quotes

### Endpoint

https://financialmodelingprep.com/stable/batch-commodity-quotes?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| short | boolean | true |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-commodity-quotes
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "DCUSD",
    "price": 17.18,
    "change": -0.21,
    "volume": 284
  }
]
```


## Light ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/commodities-historical-price-eod-light

### Endpoint

https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=GCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | GCUSD |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=GCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "GCUSD",
    "date": "2025-07-24",
    "price": 3373.8,
    "volume": 174758
  }
]
```


## Full ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/commodities-historical-price-eod-full

### Endpoint

https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=GCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | GCUSD |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=GCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "GCUSD",
    "date": "2025-07-24",
    "open": 3398.6,
    "high": 3401.1,
    "low": 3355.2,
    "close": 3373.8,
    "volume": 174758,
    "change": -24.8,
    "changePercent": -0.72971223,
    "vwap": 3376.7
  }
]
```


## 1-Minute Interval Commodities ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/commodities-intraday-1-min

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/1min?symbol=GCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | GCUSD |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/1min?symbol=GCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-07-24 12:18:00",
    "open": 3374.5,
    "low": 3373.7,
    "high": 3374.5,
    "close": 3374,
    "volume": 123
  }
]
```


## 5-Minute Interval Commodities ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/commodities-intraday-5-min

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/5min?symbol=GCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | GCUSD |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/5min?symbol=GCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-07-24 12:15:00",
    "open": 3374,
    "low": 3374,
    "high": 3374.8,
    "close": 3374.4,
    "volume": 193
  }
]
```


## 1-Hour Interval Commodities ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/commodities-intraday-1-hour

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=GCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | GCUSD |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=GCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-07-24 11:30:00",
    "open": 3378.4,
    "low": 3373.1,
    "high": 3378.8,
    "close": 3374.4,
    "volume": 7108
  }
]
```


## DCF ValuationAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/dcf-advanced

### Endpoint

https://financialmodelingprep.com/stable/discounted-cash-flow?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/discounted-cash-flow?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-02-04",
    "dcf": 147.2669883190846,
    "Stock Price": 231.795
  }
]
```


## Levered DCFAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/dcf-levered

### Endpoint

https://financialmodelingprep.com/stable/levered-discounted-cash-flow?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/levered-discounted-cash-flow?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "date": "2025-02-04",
    "dcf": 147.2669883190846,
    "Stock Price": 231.795
  }
]
```


## Custom DCF AdvancedAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/custom-dcf-advanced

### Endpoint

https://financialmodelingprep.com/stable/custom-discounted-cash-flow?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| revenueGrowthPct | number | 0.1094119804597946 |
| ebitdaPct | number | 0.31273548388 |
| depreciationAndAmortizationPct | number | 0.0345531631720999 |
| cashAndShortTermInvestmentsPct | number | 0.2344222126801843 |
| receivablesPct | number | 0.1533770531229388 |
| inventoriesPct | number | 0.0155245674227653 |
| payablePct | number | 0.1614868903169657 |
| ebitPct | number | 0.2781823207138459 |
| capitalExpenditurePct | number | 0.0306025847141713 |
| operatingCashFlowPct | number | 0.2886333485760204 |
| sellingGeneralAndAdministrativeExpensesPct | number | 0.0662854095187211 |
| taxRate | number | 0.14919579658453103 |
| longTermGrowthRate | number | 4 |
| costOfDebt | number | 3.64 |
| costOfEquity | number | 9.51168 |
| marketRiskPremium | number | 4.72 |
| beta | number | 1.244 |
| riskFreeRate | number | 3.64 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/custom-discounted-cash-flow?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "year": "2029",
    "symbol": "AAPL",
    "revenue": 657173266965,
    "revenuePercentage": 10.94,
    "ebitda": 205521399637,
    "ebitdaPercentage": 31.27,
    "ebit": 182813984515,
    "ebitPercentage": 27.82,
    "depreciation": 22707415125,
    "depreciationPercentage": 3.46,
    "totalCash": 154056011356,
    "totalCashPercentage": 23.44,
    "receivables": 100795299078,
    "receivablesPercentage": 15.34,
    "inventories": 10202330691,
    "inventoriesPercentage": 1.55,
    "payable": 106124867281,
    "payablePercentage": 16.15,
    "capitalExpenditure": 20111200574,
    "capitalExpenditurePercentage": 3.06,
    "price": 232.8,
    "beta": 1.244,
    "dilutedSharesOutstanding": 15408095000,
    "costofDebt": 3.64,
    "taxRate": 24.09,
    "afterTaxCostOfDebt": 2.76,
    "riskFreeRate": 3.64,
    "marketRiskPremium": 4.72,
    "costOfEquity": 9.51,
    "totalDebt": 106629000000,
    "totalEquity": 3587004516000,
    "totalCapital": 3693633516000,
    "debtWeighting": 2.89,
    "equityWeighting": 97.11,
    "wacc": 9.33,
    "taxRateCash": 14919580,
    "ebiat": 155538906468,
    "ufcf": 197876962552,
    "sumPvUfcf": 616840860880,
    "longTermGrowthRate": 4,
    "terminalValue": 3863553224578,
    "presentTerminalValue": 2473772391290,
    "enterpriseValue": 3090613252170,
    "netDebt": 76686000000,
    "equityValue": 3013927252170,
    "equityValuePerShare": 195.61,
    "freeCashFlowT1": 205792041054
  }
]
```


## Custom DCF LeveredAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/custom-dcf-levered

### Endpoint

https://financialmodelingprep.com/stable/custom-levered-discounted-cash-flow?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |
| revenueGrowthPct | number | 0.1094119804597946 |
| ebitdaPct | number | 0.31273548388 |
| depreciationAndAmortizationPct | number | 0.0345531631720999 |
| cashAndShortTermInvestmentsPct | number | 0.2344222126801843 |
| receivablesPct | number | 0.1533770531229388 |
| inventoriesPct | number | 0.0155245674227653 |
| payablePct | number | 0.1614868903169657 |
| ebitPct | number | 0.2781823207138459 |
| capitalExpenditurePct | number | 0.0306025847141713 |
| operatingCashFlowPct | number | 0.2886333485760204 |
| sellingGeneralAndAdministrativeExpensesPct | number | 0.0662854095187211 |
| taxRate | number | 0.14919579658453103 |
| longTermGrowthRate | number | 4 |
| costOfDebt | number | 3.64 |
| costOfEquity | number | 9.51168 |
| marketRiskPremium | number | 4.72 |
| beta | number | 1.244 |
| riskFreeRate | number | 3.64 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/custom-levered-discounted-cash-flow?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "year": "2029",
    "symbol": "AAPL",
    "revenue": 657173266965,
    "revenuePercentage": 10.94,
    "capitalExpenditure": 20111200574,
    "capitalExpenditurePercentage": 3.06,
    "price": 232.8,
    "beta": 1.244,
    "dilutedSharesOutstanding": 15408095000,
    "costofDebt": 3.64,
    "taxRate": 24.09,
    "afterTaxCostOfDebt": 2.76,
    "riskFreeRate": 3.64,
    "marketRiskPremium": 4.72,
    "costOfEquity": 9.51,
    "totalDebt": 106629000000,
    "totalEquity": 3587004516000,
    "totalCapital": 3693633516000,
    "debtWeighting": 2.89,
    "equityWeighting": 97.11,
    "wacc": 9.33,
    "operatingCashFlow": 189682120638,
    "pvLfcf": 134327365439,
    "sumPvLfcf": 652368547936,
    "longTermGrowthRate": 4,
    "freeCashFlow": 209793321212,
    "terminalValue": 4096220460472,
    "presentTerminalValue": 2622745564702,
    "enterpriseValue": 3275114112638,
    "netDebt": 76686000000,
    "equityValue": 3198428112638,
    "equityValuePerShare": 207.58,
    "freeCashFlowT1": 218185054060,
    "operatingCashFlowPercentage": 28.86
  }
]
```


## Forex Currency PairsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/forex-list

### Endpoint

https://financialmodelingprep.com/stable/forex-list?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/forex-list
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "ARSMXN",
    "fromCurrency": "ARS",
    "toCurrency": "MXN",
    "fromName": "Argentine Peso",
    "toName": "Mexican Peso"
  }
]
```


## Forex QuoteAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/forex-quote

### Endpoint

https://financialmodelingprep.com/stable/quote?symbol=EURUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | EURUSD |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/quote?symbol=EURUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "EURUSD",
    "name": "EUR/USD",
    "price": 1.17598,
    "changePercentage": -0.14754,
    "change": -0.0017376,
    "volume": 184065,
    "dayLow": 1.17371,
    "dayHigh": 1.17911,
    "yearHigh": 1.18303,
    "yearLow": 1.01838,
    "marketCap": null,
    "priceAvg50": 1.15244,
    "priceAvg200": 1.08866,
    "exchange": "FOREX",
    "open": 1.17744,
    "previousClose": 1.17772,
    "timestamp": 1753374603
  }
]
```


## Forex Short QuoteAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/forex-quote-short

### Endpoint

https://financialmodelingprep.com/stable/quote-short?symbol=EURUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | EURUSD |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/quote-short?symbol=EURUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "EURUSD",
    "price": 1.17598,
    "change": -0.0017376,
    "volume": 184065
  }
]
```


## Batch Forex QuotesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/all-forex-quotes

### Endpoint

https://financialmodelingprep.com/stable/batch-forex-quotes?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| short | boolean | true |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-forex-quotes
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AEDAUD",
    "price": 0.41372,
    "change": 0.00153892,
    "volume": 0
  }
]
```


## Historical Forex Light ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/forex-historical-price-eod-light

### Endpoint

https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=EURUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | EURUSD |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=EURUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "EURUSD",
    "date": "2025-07-24",
    "price": 1.17639,
    "volume": 182290
  }
]
```


## Historical Forex Full ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/forex-historical-price-eod-full

### Endpoint

https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=EURUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | EURUSD |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=EURUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "EURUSD",
    "date": "2025-07-24",
    "open": 1.17744,
    "high": 1.17911,
    "low": 1.17371,
    "close": 1.17639,
    "volume": 182290,
    "change": -0.00105,
    "changePercent": -0.08917652,
    "vwap": 1.18
  }
]
```


## 1-Minute Interval Forex ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/forex-intraday-1-min

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/1min?symbol=EURUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | EURUSD |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/1min?symbol=EURUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-07-24 12:29:00",
    "open": 1.17582,
    "low": 1.17582,
    "high": 1.17599,
    "close": 1.17598,
    "volume": 184
  }
]
```


## 5-Minute Interval Forex ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/forex-intraday-5-min

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/5min?symbol=EURUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | EURUSD |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/5min?symbol=EURUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-07-24 12:25:00",
    "open": 1.17612,
    "low": 1.17571,
    "high": 1.17613,
    "close": 1.17578,
    "volume": 873
  }
]
```


## 1-Hour Interval Forex ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/forex-intraday-1-hour

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=EURUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | EURUSD |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=EURUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-07-24 12:00:00",
    "open": 1.17639,
    "low": 1.17571,
    "high": 1.1773,
    "close": 1.17578,
    "volume": 4909
  }
]
```


## Cryptocurrency ListAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cryptocurrency-list

### Endpoint

https://financialmodelingprep.com/stable/cryptocurrency-list?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/cryptocurrency-list
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "ALIENUSD",
    "name": "Alien Inu USD",
    "exchange": "CCC",
    "icoDate": "2021-11-22",
    "circulatingSupply": 0,
    "totalSupply": null
  }
]
```


## Full Cryptocurrency QuoteAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cryptocurrency-quote

### Endpoint

https://financialmodelingprep.com/stable/quote?symbol=BTCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | BTCUSD |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/quote?symbol=BTCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "BTCUSD",
    "name": "Bitcoin USD",
    "price": 118741.16,
    "changePercentage": -0.03193323,
    "change": -37.93,
    "volume": 75302985728,
    "dayLow": 117435.22,
    "dayHigh": 119535.45,
    "yearHigh": 123091.61,
    "yearLow": 49121.24,
    "marketCap": 2344693699320,
    "priceAvg50": 109824.32,
    "priceAvg200": 98161.086,
    "exchange": "CRYPTO",
    "open": 118779.09,
    "previousClose": 118779.09,
    "timestamp": 1753374602
  }
]
```


## Cryptocurrency Quote ShortAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cryptocurrency-quote-short

### Endpoint

https://financialmodelingprep.com/stable/quote-short?symbol=BTCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | BTCUSD |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/quote-short?symbol=BTCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "BTCUSD",
    "price": 118741.16,
    "change": -37.93,
    "volume": 75302985728
  }
]
```


## All Cryptocurrencies QuotesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/all-cryptocurrency-quotes

### Endpoint

https://financialmodelingprep.com/stable/batch-crypto-quotes?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| short | boolean | true |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/batch-crypto-quotes
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "00USD",
    "price": 0.01755108,
    "change": 0.00035108,
    "volume": 3719492.41
  }
]
```


## Historical Cryptocurrency Light ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cryptocurrency-historical-price-eod-light

### Endpoint

https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=BTCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | BTCUSD |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=BTCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "BTCUSD",
    "date": "2025-07-24",
    "price": 118741.16,
    "volume": 75302985728
  }
]
```


## Historical Cryptocurrency Full ChartAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cryptocurrency-historical-price-eod-full

### Endpoint

https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=BTCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | BTCUSD |
| from | date | 2025-09-09 |
| to | date | 2025-12-09 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=BTCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "BTCUSD",
    "date": "2025-07-24",
    "open": 118779.09,
    "high": 119535.45,
    "low": 117435.22,
    "close": 118741.16,
    "volume": 75302985728,
    "change": -37.93,
    "changePercent": -0.03193323,
    "vwap": 118570.61
  }
]
```


## 1-Minute Interval Cryptocurrency DataAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cryptocurrency-intraday-1-min

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/1min?symbol=BTCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | BTCUSD |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/1min?symbol=BTCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-07-24 12:29:00",
    "open": 118797.96,
    "low": 118760.42,
    "high": 118818.11,
    "close": 118784.04,
    "volume": 52293740.08888889
  }
]
```


## 5-Minute Interval Cryptocurrency DataAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cryptocurrency-intraday-5-min

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/5min?symbol=BTCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | BTCUSD |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/5min?symbol=BTCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-07-24 12:25:00",
    "open": 118988.32,
    "low": 118797.03,
    "high": 118997.22,
    "close": 118797.03,
    "volume": 208601161.95555556
  }
]
```


## 1-Hour Interval Cryptocurrency DataAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cryptocurrency-intraday-1-hour

### Endpoint

https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=BTCUSD&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | BTCUSD |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=BTCUSD
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-07-24 12:00:00",
    "open": 119189.36,
    "low": 118768.68,
    "high": 119272.88,
    "close": 118797.03,
    "volume": 1493617925.6888888
  }
]
```


## Latest Senate Financial DisclosuresAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/senate-latest

### Endpoint

https://financialmodelingprep.com/stable/senate-latest?page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/senate-latest?page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "LRN",
    "disclosureDate": "2025-01-31",
    "transactionDate": "2025-01-02",
    "firstName": "Markwayne",
    "lastName": "Mullin",
    "office": "Markwayne Mullin",
    "district": "OK",
    "owner": "Self",
    "assetDescription": "Stride Inc",
    "assetType": "Stock",
    "type": "Purchase",
    "amount": "$15,001 - $50,000",
    "comment": "",
    "link": "https://efdsearch.senate.gov/search/view/ptr/446c7588-5f97-42c0-8983-3ca975b91793/"
  }
]
```


## Latest House Financial DisclosuresAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/house-latest

### Endpoint

https://financialmodelingprep.com/stable/house-latest?page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/house-latest?page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "$VIRTUALUSD",
    "disclosureDate": "2025-02-03",
    "transactionDate": "2025-01-03",
    "firstName": "Michael",
    "lastName": "Collins",
    "office": "Michael Collins",
    "district": "GA10",
    "owner": "",
    "assetDescription": "VIRTUALS PROTOCOL",
    "assetType": "Cryptocurrency",
    "type": "Purchase",
    "amount": "$1,001 - $15,000",
    "capitalGainsOver200USD": "False",
    "comment": "",
    "link": "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20026696.pdf"
  }
]
```


## Senate Trading ActivityAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/senate-trading

### Endpoint

https://financialmodelingprep.com/stable/senate-trades?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/senate-trades?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "disclosureDate": "2025-01-08",
    "transactionDate": "2024-12-19",
    "firstName": "Sheldon",
    "lastName": "Whitehouse",
    "office": "Sheldon Whitehouse",
    "district": "RI",
    "owner": "Self",
    "assetDescription": "Apple Inc",
    "assetType": "Stock",
    "type": "Sale (Partial)",
    "amount": "$15,001 - $50,000",
    "capitalGainsOver200USD": "False",
    "comment": "--",
    "link": "https://efdsearch.senate.gov/search/view/ptr/70c80513-d89a-4382-afa6-d80f6c1fcbf1/"
  }
]
```


## Senate Trades By NameAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/senate-trading-by-name

### Endpoint

https://financialmodelingprep.com/stable/senate-trades-by-name?name=Jerry&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| name * | string | Jerry |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/senate-trades-by-name?name=Jerry
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "BRK/B",
    "disclosureDate": "2025-01-18",
    "transactionDate": "2024-12-16",
    "firstName": "Jerry",
    "lastName": "Moran",
    "office": "Jerry Moran",
    "district": "KS",
    "owner": "Self",
    "assetDescription": "Berkshire Hathaway Inc",
    "assetType": "Stock",
    "type": "Purchase",
    "amount": "$1,001 - $15,000",
    "capitalGainsOver200USD": "False",
    "comment": "",
    "link": "https://efdsearch.senate.gov/search/view/ptr/e37322e3-0829-4e3c-9faf-7a4a1a957e09/"
  }
]
```


## U.S. House TradesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/house-trading

### Endpoint

https://financialmodelingprep.com/stable/house-trades?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/house-trades?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "disclosureDate": "2025-01-20",
    "transactionDate": "2024-12-31",
    "firstName": "Nancy",
    "lastName": "Pelosi",
    "office": "Nancy Pelosi",
    "district": "CA11",
    "owner": "Spouse",
    "assetDescription": "Apple Inc",
    "assetType": "Stock",
    "type": "Sale",
    "amount": "$10,000,001 - $25,000,000",
    "capitalGainsOver200USD": "False",
    "comment": "",
    "link": "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20026590.pdf"
  }
]
```


## House Trades By NameAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/house-trading-by-name

### Endpoint

https://financialmodelingprep.com/stable/house-trades-by-name?name=James&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| name * | string | James |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/house-trades-by-name?name=James
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "LUV",
    "disclosureDate": "2025-01-13",
    "transactionDate": "2024-12-31",
    "firstName": "James",
    "lastName": "Comer",
    "office": "James Comer",
    "district": "KY01",
    "owner": "",
    "assetDescription": "Southwest Airlines Co",
    "assetType": "Stock",
    "type": "Sale",
    "amount": "$1,001 - $15,000",
    "capitalGainsOver200USD": "False",
    "comment": "",
    "link": "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20018054.pdf"
  }
]
```


## ESG Investment SearchAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/esg-search

### Endpoint

https://financialmodelingprep.com/stable/esg-disclosures?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/esg-disclosures?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2024-12-28",
    "acceptedDate": "2025-01-30",
    "symbol": "AAPL",
    "cik": "0000320193",
    "companyName": "Apple Inc.",
    "formType": "8-K",
    "environmentalScore": 52.52,
    "socialScore": 45.18,
    "governanceScore": 60.74,
    "ESGScore": 52.81,
    "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019325000007/0000320193-25-000007-index.htm"
  }
]
```


## ESG RatingsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/esg-ratings

### Endpoint

https://financialmodelingprep.com/stable/esg-ratings?symbol=AAPL&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol * | string | AAPL |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/esg-ratings?symbol=AAPL
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "cik": "0000320193",
    "companyName": "Apple Inc.",
    "industry": "CONSUMER ELECTRONICS",
    "fiscalYear": 2024,
    "ESGRiskRating": "B",
    "industryRank": "4 out of 5"
  }
]
```


## ESG Benchmark ComparisonAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/esg-benchmark

### Endpoint

https://financialmodelingprep.com/stable/esg-benchmark?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| year | string | 2023 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/esg-benchmark
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "fiscalYear": 2023,
    "sector": "APPAREL RETAIL",
    "environmentalScore": 61.36,
    "socialScore": 67.44,
    "governanceScore": 68.1,
    "ESGScore": 65.63
  }
]
```


## COT ReportAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cot-report

### Endpoint

https://financialmodelingprep.com/stable/commitment-of-traders-report?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol | string | AAPL |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/commitment-of-traders-report
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "KC",
    "date": "2024-02-27 00:00:00",
    "name": "Coffee (KC)",
    "sector": "SOFTS",
    "marketAndExchangeNames": "COFFEE C - ICE FUTURES U.S.",
    "cftcContractMarketCode": "083731",
    "cftcMarketCode": "ICUS",
    "cftcRegionCode": "1",
    "cftcCommodityCode": "83",
    "openInterestAll": 209453,
    "noncommPositionsLongAll": 75330,
    "noncommPositionsShortAll": 23630,
    "noncommPositionsSpreadAll": 47072,
    "commPositionsLongAll": 79690,
    "commPositionsShortAll": 132114,
    "totReptPositionsLongAll": 202092,
    "totReptPositionsShortAll": 202816,
    "nonreptPositionsLongAll": 7361,
    "nonreptPositionsShortAll": 6637,
    "openInterestOld": 179986,
    "noncommPositionsLongOld": 75483,
    "noncommPositionsShortOld": 35395,
    "noncommPositionsSpreadOld": 27067,
    "commPositionsLongOld": 70693,
    "commPositionsShortOld": 111666,
    "totReptPositionsLongOld": 173243,
    "totReptPositionsShortOld": 174128,
    "nonreptPositionsLongOld": 6743,
    "nonreptPositionsShortOld": 5858,
    "openInterestOther": 29467,
    "noncommPositionsLongOther": 18754,
    "noncommPositionsShortOther": 7142,
    "noncommPositionsSpreadOther": 1098,
    "commPositionsLongOther": 8997,
    "commPositionsShortOther": 20448,
    "totReptPositionsLongOther": 28849,
    "totReptPositionsShortOther": 28688,
    "nonreptPositionsLongOther": 618,
    "nonreptPositionsShortOther": 779,
    "changeInOpenInterestAll": 2957,
    "changeInNoncommLongAll": -3545,
    "changeInNoncommShortAll": 618,
    "changeInNoncommSpeadAll": 1575,
    "changeInCommLongAll": 4978,
    "changeInCommShortAll": 802,
    "changeInTotReptLongAll": 3008,
    "changeInTotReptShortAll": 2995,
    "changeInNonreptLongAll": -51,
    "changeInNonreptShortAll": -38,
    "pctOfOpenInterestAll": 100,
    "pctOfOiNoncommLongAll": 36,
    "pctOfOiNoncommShortAll": 11.3,
    "pctOfOiNoncommSpreadAll": 22.5,
    "pctOfOiCommLongAll": 38,
    "pctOfOiCommShortAll": 63.1,
    "pctOfOiTotReptLongAll": 96.5,
    "pctOfOiTotReptShortAll": 96.8,
    "pctOfOiNonreptLongAll": 3.5,
    "pctOfOiNonreptShortAll": 3.2,
    "pctOfOpenInterestOl": 100,
    "pctOfOiNoncommLongOl": 41.9,
    "pctOfOiNoncommShortOl": 19.7,
    "pctOfOiNoncommSpreadOl": 15,
    "pctOfOiCommLongOl": 39.3,
    "pctOfOiCommShortOl": 62,
    "pctOfOiTotReptLongOl": 96.3,
    "pctOfOiTotReptShortOl": 96.7,
    "pctOfOiNonreptLongOl": 3.7,
    "pctOfOiNonreptShortOl": 3.3,
    "pctOfOpenInterestOther": 100,
    "pctOfOiNoncommLongOther": 63.6,
    "pctOfOiNoncommShortOther": 24.2,
    "pctOfOiNoncommSpreadOther": 3.7,
    "pctOfOiCommLongOther": 30.5,
    "pctOfOiCommShortOther": 69.4,
    "pctOfOiTotReptLongOther": 97.9,
    "pctOfOiTotReptShortOther": 97.4,
    "pctOfOiNonreptLongOther": 2.1,
    "pctOfOiNonreptShortOther": 2.6,
    "tradersTotAll": 357,
    "tradersNoncommLongAll": 132,
    "tradersNoncommShortAll": 77,
    "tradersNoncommSpreadAll": 94,
    "tradersCommLongAll": 106,
    "tradersCommShortAll": 119,
    "tradersTotReptLongAll": 286,
    "tradersTotReptShortAll": 250,
    "tradersTotOl": 351,
    "tradersNoncommLongOl": 136,
    "tradersNoncommShortOl": 72,
    "tradersNoncommSpeadOl": 88,
    "tradersCommLongOl": 94,
    "tradersCommShortOl": 114,
    "tradersTotReptLongOl": 269,
    "tradersTotReptShortOl": 239,
    "tradersTotOther": 164,
    "tradersNoncommLongOther": 31,
    "tradersNoncommShortOther": 34,
    "tradersNoncommSpreadOther": 16,
    "tradersCommLongOther": 59,
    "tradersCommShortOther": 68,
    "tradersTotReptLongOther": 102,
    "tradersTotReptShortOther": 106,
    "concGrossLe4TdrLongAll": 16,
    "concGrossLe4TdrShortAll": 23.7,
    "concGrossLe8TdrLongAll": 25.8,
    "concGrossLe8TdrShortAll": 38.9,
    "concNetLe4TdrLongAll": 9.8,
    "concNetLe4TdrShortAll": 16.2,
    "concNetLe8TdrLongAll": 17.7,
    "concNetLe8TdrShortAll": 25.4,
    "concGrossLe4TdrLongOl": 13.6,
    "concGrossLe4TdrShortOl": 24.7,
    "concGrossLe8TdrLongOl": 23.2,
    "concGrossLe8TdrShortOl": 40.3,
    "concNetLe4TdrLongOl": 11.3,
    "concNetLe4TdrShortOl": 18.2,
    "concNetLe8TdrLongOl": 20.3,
    "concNetLe8TdrShortOl": 31.9,
    "concGrossLe4TdrLongOther": 68.2,
    "concGrossLe4TdrShortOther": 29.1,
    "concGrossLe8TdrLongOther": 77.8,
    "concGrossLe8TdrShortOther": 47.3,
    "concNetLe4TdrLongOther": 64.7,
    "concNetLe4TdrShortOther": 26.7,
    "concNetLe8TdrLongOther": 73.9,
    "concNetLe8TdrShortOther": 44.2,
    "contractUnits": "(CONTRACTS OF 37,500 POUNDS)"
  }
]
```


## COT Analysis By DatesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cot-report-analysis

### Endpoint

https://financialmodelingprep.com/stable/commitment-of-traders-analysis?apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| symbol | string | AAPL |
| from | date | 2024-01-01 |
| to | date | 2024-03-01 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/commitment-of-traders-analysis
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "B6",
    "date": "2024-02-27 00:00:00",
    "name": "British Pound (B6)",
    "sector": "CURRENCIES",
    "exchange": "BRITISH POUND - CHICAGO MERCANTILE EXCHANGE",
    "currentLongMarketSituation": 66.85,
    "currentShortMarketSituation": 33.15,
    "marketSituation": "Bullish",
    "previousLongMarketSituation": 67.97,
    "previousShortMarketSituation": 32.03,
    "previousMarketSituation": "Bullish",
    "netPostion": 46358,
    "previousNetPosition": 46312,
    "changeInNetPosition": 0.1,
    "marketSentiment": "Increasing Bullish",
    "reversalTrend": false
  }
]
```


## COT Report ListAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cot-report-list

### Endpoint

https://financialmodelingprep.com/stable/commitment-of-traders-list?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/commitment-of-traders-list
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "NG",
    "name": "Natural Gas (NG)"
  }
]
```


## Latest Crowdfunding CampaignsAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/latest-crowdfunding

### Endpoint

https://financialmodelingprep.com/stable/crowdfunding-offerings-latest?page=0&limit=100&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| page | number | 0 |
| limit | number | 100 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/crowdfunding-offerings-latest?page=0&limit=100
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0002050877",
    "companyName": "PowerGreen Capital Corp",
    "date": "01-27-2025",
    "filingDate": "2025-02-04 00:00:00",
    "acceptedDate": "2025-02-04 16:17:49",
    "formType": "C/A",
    "formSignification": "Offering Statement Amendement",
    "nameOfIssuer": "PowerGreen Capital Corp",
    "legalStatusForm": "Limited Liability Company",
    "jurisdictionOrganization": "PA",
    "issuerStreet": "1614 PUGHTOWN RD",
    "issuerCity": "PHOENIXVILLE",
    "issuerStateOrCountry": "PA",
    "issuerZipCode": "19460",
    "issuerWebsite": "www.powergreencapital.com",
    "intermediaryCompanyName": "Honeycomb Portal LLC",
    "intermediaryCommissionCik": "0001705726",
    "intermediaryCommissionFileNumber": "007-00119",
    "compensationAmount": "Applied at marginal rate based upon amount of total offering: up to $50,000 = 8.0%, $50,001 - $100,000 = 7.0%, $100,001+ = 6.0%. $250 posting fee. 2.85% investment fee capped at $37.25.",
    "financialInterest": "None",
    "securityOfferedType": "Other",
    "securityOfferedOtherDescription": "SAFE (Simple Agreement for Future Equity)",
    "numberOfSecurityOffered": 124000,
    "offeringPrice": 1,
    "offeringAmount": 60000,
    "overSubscriptionAccepted": "Y",
    "overSubscriptionAllocationType": "First-come, first-served basis",
    "maximumOfferingAmount": 124000,
    "offeringDeadlineDate": "03-13-2025",
    "currentNumberOfEmployees": 2,
    "totalAssetMostRecentFiscalYear": 193070,
    "totalAssetPriorFiscalYear": 0,
    "cashAndCashEquiValentMostRecentFiscalYear": 5957,
    "cashAndCashEquiValentPriorFiscalYear": 0,
    "accountsReceivableMostRecentFiscalYear": 0,
    "accountsReceivablePriorFiscalYear": 0,
    "shortTermDebtMostRecentFiscalYear": 0,
    "shortTermDebtPriorFiscalYear": 0,
    "longTermDebtMostRecentFiscalYear": 0,
    "longTermDebtPriorFiscalYear": 0,
    "revenueMostRecentFiscalYear": 2112,
    "revenuePriorFiscalYear": 0,
    "costGoodsSoldMostRecentFiscalYear": 0,
    "costGoodsSoldPriorFiscalYear": 0,
    "taxesPaidMostRecentFiscalYear": 0,
    "taxesPaidPriorFiscalYear": 0,
    "netIncomeMostRecentFiscalYear": -192010,
    "netIncomePriorFiscalYear": 0
  }
]
```


## Crowdfunding Campaign SearchAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/crowdfunding-search

### Endpoint

https://financialmodelingprep.com/stable/crowdfunding-offerings-search?name=enotap&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| name * | string | enotap |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/crowdfunding-offerings-search?name=enotap
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0001912939",
    "name": "Enotap LLC",
    "date": null
  }
]
```


## Crowdfunding By CIKAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/crowdfunding-by-cik

### Endpoint

https://financialmodelingprep.com/stable/crowdfunding-offerings?cik=0001916078&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| cik * | string | 0001916078 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/crowdfunding-offerings?cik=0001916078
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0001916078",
    "companyName": "OYO Fitness, Inc",
    "date": "12-31-2021",
    "filingDate": "2022-07-21 00:00:00",
    "acceptedDate": "2022-07-21 17:28:54",
    "formType": "C-U",
    "formSignification": "Progress Update",
    "nameOfIssuer": "OYO Fitness, Inc",
    "legalStatusForm": "Corporation",
    "jurisdictionOrganization": "DE",
    "issuerStreet": "374 N. 750TH RD",
    "issuerCity": "OVERBROOK",
    "issuerStateOrCountry": "KS",
    "issuerZipCode": "66524",
    "issuerWebsite": "https://www.oyofitness.com/",
    "intermediaryCompanyName": "StartEngine Capital, LLC",
    "intermediaryCommissionCik": "0001665160",
    "intermediaryCommissionFileNumber": "007-00007",
    "compensationAmount": "7 - 13 percent",
    "financialInterest": "Two percent (2%) of securities of the total amount of investments raised in the offering, along the same terms as investors.",
    "securityOfferedType": "Other",
    "securityOfferedOtherDescription": "Non-Voting Common Stock",
    "numberOfSecurityOffered": 5000,
    "offeringPrice": 2,
    "offeringAmount": 10000,
    "overSubscriptionAccepted": "Y",
    "overSubscriptionAllocationType": "Other",
    "maximumOfferingAmount": 1070000,
    "offeringDeadlineDate": "07-19-2022",
    "currentNumberOfEmployees": 5,
    "totalAssetMostRecentFiscalYear": 497717,
    "totalAssetPriorFiscalYear": 248472,
    "cashAndCashEquiValentMostRecentFiscalYear": 150142,
    "cashAndCashEquiValentPriorFiscalYear": 54571,
    "accountsReceivableMostRecentFiscalYear": 0,
    "accountsReceivablePriorFiscalYear": 0,
    "shortTermDebtMostRecentFiscalYear": 3286745,
    "shortTermDebtPriorFiscalYear": 2214117,
    "longTermDebtMostRecentFiscalYear": 82243,
    "longTermDebtPriorFiscalYear": 105850,
    "revenueMostRecentFiscalYear": 4344154,
    "revenuePriorFiscalYear": 11078510,
    "costGoodsSoldMostRecentFiscalYear": 2445024,
    "costGoodsSoldPriorFiscalYear": 5737776,
    "taxesPaidMostRecentFiscalYear": 0,
    "taxesPaidPriorFiscalYear": 0,
    "netIncomeMostRecentFiscalYear": -964551,
    "netIncomePriorFiscalYear": -10860
  }
]
```


## Equity Offering UpdatesAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/latest-equity-offering

### Endpoint

https://financialmodelingprep.com/stable/fundraising-latest?page=0&limit=10&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| page | number | 0 |
| limit | number | 10 |
| cik | string | 0002013736 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/fundraising-latest?page=0&limit=10
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0002013736",
    "companyName": "XO Generation Fund LP",
    "date": "2024-03-01",
    "filingDate": "2024-08-08 00:00:00",
    "acceptedDate": "2024-08-08 17:29:48",
    "formType": "D/A",
    "formSignification": "Notice of Exempt Offering of Securities Amendement",
    "entityName": "XO Generation Fund LP",
    "issuerStreet": "842 S HIGHLAND AVE",
    "issuerCity": "LOS ANGELES",
    "issuerStateOrCountry": "CA",
    "issuerStateOrCountryDescription": "CALIFORNIA",
    "issuerZipCode": "90036",
    "issuerPhoneNumber": "201-961-3356",
    "jurisdictionOfIncorporation": "DELAWARE",
    "entityType": "Limited Partnership",
    "incorporatedWithinFiveYears": true,
    "yearOfIncorporation": "2024",
    "relatedPersonFirstName": "-",
    "relatedPersonLastName": "XO Capital LLC",
    "relatedPersonStreet": "842 S Highland Ave",
    "relatedPersonCity": "Los Angeles",
    "relatedPersonStateOrCountry": "CA",
    "relatedPersonStateOrCountryDescription": "CALIFORNIA",
    "relatedPersonZipCode": "90036",
    "relatedPersonRelationship": "Promoter",
    "industryGroupType": "Pooled Investment Fund",
    "revenueRange": null,
    "federalExemptionsExclusions": "06b, 3C, 3C.1",
    "isAmendment": true,
    "dateOfFirstSale": "2024-03-01",
    "durationOfOfferingIsMoreThanYear": true,
    "securitiesOfferedAreOfEquityType": true,
    "isBusinessCombinationTransaction": false,
    "minimumInvestmentAccepted": 100000,
    "totalOfferingAmount": 0,
    "totalAmountSold": 5000,
    "totalAmountRemaining": 0,
    "hasNonAccreditedInvestors": false,
    "totalNumberAlreadyInvested": 1,
    "salesCommissions": 0,
    "findersFees": 0,
    "grossProceedsUsed": 0
  }
]
```


## Equity Offering SearchAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/equity-offering-search

### Endpoint

https://financialmodelingprep.com/stable/fundraising-search?name=NJOY&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| name * | string | NJOY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/fundraising-search?name=NJOY
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0001547416",
    "name": "NJOY INC",
    "date": "2014-02-28 16:00:25"
  }
]
```


## Equity Offering By CIKAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/equity-offering-by-cik

### Endpoint

https://financialmodelingprep.com/stable/fundraising?cik=0001547416&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| cik * | string | 0001547416 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/fundraising?cik=0001547416
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "cik": "0001547416",
    "companyName": "NJOY INC",
    "date": "2014-02-28",
    "filingDate": "2014-02-28 00:00:00",
    "acceptedDate": "2014-02-28 16:00:25",
    "formType": "D",
    "formSignification": "Notice of Exempt Offering of Securities",
    "entityName": "NJOY INC",
    "issuerStreet": "15211 N. KIERLAND BLVD., SUITE 200",
    "issuerCity": "SCOTTSDALE",
    "issuerStateOrCountry": "AZ",
    "issuerStateOrCountryDescription": "ARIZONA",
    "issuerZipCode": "85254",
    "issuerPhoneNumber": "480-397-2300",
    "jurisdictionOfIncorporation": "DELAWARE",
    "entityType": "Corporation",
    "incorporatedWithinFiveYears": null,
    "yearOfIncorporation": "",
    "relatedPersonFirstName": "CRAIG",
    "relatedPersonLastName": "WEISS",
    "relatedPersonStreet": "c/o NJOY, INC.",
    "relatedPersonCity": "SCOTTSDALE",
    "relatedPersonStateOrCountry": "AZ",
    "relatedPersonStateOrCountryDescription": "ARIZONA",
    "relatedPersonZipCode": "85254",
    "relatedPersonRelationship": "Executive Officer, Director",
    "industryGroupType": "Other",
    "revenueRange": "Decline to Disclose",
    "federalExemptionsExclusions": "06b",
    "isAmendment": false,
    "dateOfFirstSale": "2014-02-14",
    "durationOfOfferingIsMoreThanYear": false,
    "securitiesOfferedAreOfEquityType": true,
    "isBusinessCombinationTransaction": false,
    "minimumInvestmentAccepted": 0,
    "totalOfferingAmount": 71999990,
    "totalAmountSold": 71999990,
    "totalAmountRemaining": 0,
    "hasNonAccreditedInvestors": false,
    "totalNumberAlreadyInvested": 24,
    "salesCommissions": 0,
    "findersFees": 0,
    "grossProceedsUsed": 0
  }
]
```


## Company Profile BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/profile-bulk

### Endpoint

https://financialmodelingprep.com/stable/profile-bulk?part=0&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| part * | string | 0 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/profile-bulk?part=0
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AAPL",
    "price": 271.36,
    "marketCap": 4009711150080,
    "beta": 1.107,
    "lastDividend": 1.03,
    "range": "169.21-288.62",
    "change": -0.83,
    "changePercentage": -0.30493,
    "volume": 44494594,
    "averageVolume": 48811139,
    "companyName": "Apple Inc.",
    "currency": "USD",
    "cik": "0000320193",
    "isin": "US0378331005",
    "cusip": "037833100",
    "exchangeFullName": "NASDAQ Global Select",
    "exchange": "NASDAQ",
    "industry": "Consumer Electronics",
    "website": "https://www.apple.com",
    "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allow customers to discover and download applications and digital content, such as books, music, video, games, and podcasts, as well as advertising services include third-party licensing arrangements and its own advertising platforms. In addition, the company offers various subscription-based services, such as Apple Arcade, a game subscription service; Apple Fitness+, a personalized fitness service; Apple Music, which offers users a curated listening experience with on-demand radio stations; Apple News+, a subscription news and magazine service; Apple TV+, which offers exclusive original content; Apple Card, a co-branded credit card; and Apple Pay, a cashless payment service, as well as licenses its intellectual property. The company serves consumers, and small and mid-sized businesses; and the education, enterprise, and government markets. It distributes third-party applications for its products through the App Store. The company also sells its products through its retail and online stores, and direct sales force; and third-party cellular network carriers, wholesalers, retailers, and resellers. Apple Inc. was founded in 1976 and is headquartered in Cupertino, California.",
    "ceo": "Timothy D. Cook",
    "sector": "Technology",
    "country": "US",
    "fullTimeEmployees": "164000",
    "phone": "(408) 996-1010",
    "address": "One Apple Park Way",
    "city": "Cupertino",
    "state": "CA",
    "zip": "95014",
    "image": "https://images.financialmodelingprep.com/symbol/AAPL.png",
    "ipoDate": "1980-12-12",
    "defaultImage": false,
    "isEtf": false,
    "isActivelyTrading": true,
    "isAdr": false,
    "isFund": false
  }
]
```


## Stock Rating BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/rating-bulk

### Endpoint

https://financialmodelingprep.com/stable/rating-bulk?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/rating-bulk
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "000001.SZ",
    "date": "2025-07-09",
    "rating": "B+",
    "discountedCashFlowScore": "5",
    "returnOnEquityScore": "3",
    "returnOnAssetsScore": "2",
    "debtToEquityScore": "1",
    "priceToEarningsScore": "4",
    "priceToBookScore": "4"
  }
]
```


## DCF Valuations BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/dcf-bulk

### Endpoint

https://financialmodelingprep.com/stable/dcf-bulk?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/dcf-bulk
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "000002.SZ",
    "date": "2025-07-09",
    "dcf": "179.6654688379575",
    "Stock Price": "6.54"
  }
]
```


## Financial Scores BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/scores-bulk

### Endpoint

https://financialmodelingprep.com/stable/scores-bulk?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/scores-bulk
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "000001.SZ",
    "reportedCurrency": "CNY",
    "altmanZScore": "0.29153682196643543",
    "piotroskiScore": "5",
    "workingCapital": "746131000000",
    "totalAssets": "5777858000000",
    "retainedEarnings": "255621000000",
    "ebit": "32590000000",
    "marketCap": "236751980000",
    "totalLiabilities": "5271746000000",
    "revenue": "167996000000"
  }
]
```


## Price Target Summary BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/price-target-summary-bulk

### Endpoint

https://financialmodelingprep.com/stable/price-target-summary-bulk?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/price-target-summary-bulk
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "A",
    "lastMonthCount": "0",
    "lastMonthAvgPriceTarget": "0",
    "lastQuarterCount": "1",
    "lastQuarterAvgPriceTarget": "116",
    "lastYearCount": "6",
    "lastYearAvgPriceTarget": "142.17",
    "allTimeCount": "18",
    "allTimeAvgPriceTarget": "146.61",
    "publishers": "[\"\"TheFly\""
  }
]
```


## ETF Holder BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/etf-holder-bulk

### Endpoint

https://financialmodelingprep.com/stable/etf-holder-bulk?part=1&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| part * | string | 1 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/etf-holder-bulk?part=1
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "EXCH.AS",
    "name": "SAMSUNG ELECTRO MECHANICS LTD",
    "sharesNumber": "15514",
    "asset": "009150.KS",
    "weightPercentage": "0.09611",
    "cusip": "",
    "isin": "KR7009150004",
    "marketValue": "1553142.49",
    "lastUpdated\"": "2024-09-06\""
  }
]
```


## Upgrades Downgrades Consensus BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/upgrades-downgrades-consensus-bulk

### Endpoint

https://financialmodelingprep.com/stable/upgrades-downgrades-consensus-bulk?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/upgrades-downgrades-consensus-bulk
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "",
    "strongBuy": "0",
    "buy": "1",
    "hold": "1",
    "sell": "0",
    "strongSell": "0",
    "consensus": "Buy"
  }
]
```


## Key Metrics TTM BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/key-metrics-ttm-bulk

### Endpoint

https://financialmodelingprep.com/stable/key-metrics-ttm-bulk?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/key-metrics-ttm-bulk
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "000001.SZ",
    "marketCap": "249171756000",
    "enterpriseValueTTM": "-496959244000",
    "evToSalesTTM": "-2.95816117050406",
    "evToOperatingCashFlowTTM": "-2.9831814247210167",
    "evToFreeCashFlowTTM": "-3.028355803098073",
    "evToEBITDATTM": "-14.656106051669223",
    "netDebtToEBITDATTM": "-22.004571192638906",
    "currentRatioTTM": "0",
    "incomeQualityTTM": "15.217593861331872",
    "grahamNumberTTM": "31.017865999534138",
    "grahamNetNetTTM": "-199.05514330278228",
    "taxBurdenTTM": "0.8225101702576465",
    "interestBurdenTTM": "1.4030970878917606",
    "workingCapitalTTM": "746131000000",
    "investedCapitalTTM": "772543000000",
    "returnOnAssetsTTM": "0.007558510437605078",
    "operatingReturnOnAssetsTTM": "0.013555578495362656",
    "returnOnTangibleAssetsTTM": "0.007576346366296015",
    "returnOnEquityTTM": "0.09082717681735725",
    "returnOnInvestedCapitalTTM": "0.011141314993384131",
    "returnOnCapitalEmployedTTM": "0.013545504233575834",
    "earningsYieldTTM": "0.14960077934639543",
    "freeCashFlowYieldTTM": "0.6585898925077207",
    "capexToOperatingCashFlowTTM": "0.014917130388325619",
    "capexToDepreciationTTM": "1.855862584017924",
    "capexToRevenueTTM": "0.014792018857591847",
    "salesGeneralAndAdministrativeToRevenueTTM": "0.10163337222314817",
    "researchAndDevelopementToRevenueTTM": "0",
    "stockBasedCompensationToRevenueTTM": "0",
    "intangiblesToTotalAssetsTTM": "0.002354159621091415",
    "averageReceivablesTTM": "0",
    "averagePayablesTTM": "0",
    "averageInventoryTTM": "0",
    "daysOfSalesOutstandingTTM": "0",
    "daysOfPayablesOutstandingTTM": "0",
    "daysOfInventoryOutstandingTTM": "0",
    "operatingCycleTTM": "0",
    "cashConversionCycleTTM": "0",
    "freeCashFlowToEquityTTM": "910233000000",
    "freeCashFlowToFirmTTM": "-35237570137.11014",
    "tangibleAssetValueTTM": "492510000000",
    "netCurrentAssetValueTTM": "-4525615000000"
  }
]
```


## Ratios TTM BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/ratios-ttm-bulk

### Endpoint

https://financialmodelingprep.com/stable/ratios-ttm-bulk?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/ratios-ttm-bulk
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "000001.SZ",
    "grossProfitMarginTTM": "1.1622776732779352",
    "ebitMarginTTM": "0.22525536322293388",
    "ebitdaMarginTTM": "0.2018381390033096",
    "operatingProfitMarginTTM": "0.4658682349579752",
    "pretaxProfitMarginTTM": "0.3160551441700993",
    "continuousOperationsProfitMarginTTM": "0.25995857044215337",
    "netProfitMarginTTM": "0.25995857044215337",
    "bottomLineProfitMarginTTM": "0.25995857044215337",
    "receivablesTurnoverTTM": "0",
    "payablesTurnoverTTM": "0",
    "inventoryTurnoverTTM": "0",
    "fixedAssetTurnoverTTM": "13.114441842310695",
    "assetTurnoverTTM": "0.029075827062555015",
    "currentRatioTTM": "0",
    "quickRatioTTM": "0",
    "solvencyRatioTTM": "0.008534174446189174",
    "cashRatioTTM": "0",
    "priceToEarningsRatioTTM": "6.68445715569793",
    "priceToEarningsGrowthRatioTTM": "-3.6096068640768793",
    "forwardPriceToEarningsGrowthRatioTTM": "2.4481492401413427",
    "priceToBookRatioTTM": "0.576796465809228",
    "priceToSalesRatioTTM": "1.483200528584014",
    "priceToFreeCashFlowRatioTTM": "1.518395607609901",
    "priceToOperatingCashFlowRatioTTM": "1.7523793147342828",
    "debtToAssetsRatioTTM": "0",
    "debtToEquityRatioTTM": "0",
    "debtToCapitalRatioTTM": "0",
    "longTermDebtToCapitalRatioTTM": "0",
    "financialLeverageRatioTTM": "11.416164801466868",
    "workingCapitalTurnoverRatioTTM": "0.23544250931631752",
    "operatingCashFlowRatioTTM": "0",
    "operatingCashFlowSalesRatioTTM": "0.991612895545132",
    "freeCashFlowOperatingCashFlowRatioTTM": "0.9850828696116743",
    "debtServiceCoverageRatioTTM": "0.24758322210087771",
    "interestCoverageRatioTTM": "0.7914088096104842",
    "shortTermOperatingCashFlowCoverageRatioTTM": "0",
    "operatingCashFlowCoverageRatioTTM": "0",
    "capitalExpenditureCoverageRatioTTM": "67.03702213279678",
    "dividendPaidAndCapexCoverageRatioTTM": "6.192364879934577",
    "dividendPayoutRatioTTM": "0.5590996519509067",
    "dividendYieldTTM": "0.10335",
    "enterpriseValueTTM": "-496959244000",
    "revenuePerShareTTM": "7.389154370023568",
    "netIncomePerShareTTM": "1.9208740068077172",
    "interestDebtPerShareTTM": "4.349676503966586",
    "cashPerShareTTM": "32.81790720767194",
    "bookValuePerShareTTM": "22.260885357516656",
    "tangibleBookValuePerShareTTM": "21.662613507347245",
    "shareholdersEquityPerShareTTM": "22.260885357516656",
    "operatingCashFlowPerShareTTM": "7.327180760489036",
    "capexPerShareTTM": "0.10930051078304583",
    "freeCashFlowPerShareTTM": "7.21788024970599",
    "netIncomePerEBTTTM": "0.8225101702576465",
    "ebtPerEbitTTM": "0.6784217520188082",
    "priceToFairValueTTM": "0.576796465809228",
    "debtToMarketCapTTM": "0",
    "effectiveTaxRateTTM": "0.17748982974235347",
    "enterpriseValueMultipleTTM": "-14.656106051669223",
    "dividendPerShareTTM": "1.327"
  }
]
```


## Stock Peers BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/peers-bulk

### Endpoint

https://financialmodelingprep.com/stable/peers-bulk?apikey=YOUR_API_KEY

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/peers-bulk
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "000001.SZ",
    "peers": "600036.SS"
  }
]
```


## Earnings Surprises BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/earnings-surprises-bulk

### Endpoint

https://financialmodelingprep.com/stable/earnings-surprises-bulk?year=2025&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| year * | string | 2025 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/earnings-surprises-bulk?year=2025
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "AMKYF",
    "date": "2025-07-09",
    "epsActual": "0.3631",
    "epsEstimated": "0.3615",
    "lastUpdated": "2025-07-09"
  }
]
```


## Income Statement BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/income-statement-bulk

### Endpoint

https://financialmodelingprep.com/stable/income-statement-bulk?year=2025&period=Q1&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| year * | string | 2025 |
| period * | string | Q1Q2Q3Q4FY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/income-statement-bulk?year=2025&period=Q1
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-03-31",
    "symbol": "000001.SZ",
    "reportedCurrency": "CNY",
    "cik": "0000000000",
    "filingDate": "2025-03-31",
    "acceptedDate": "2025-03-31 00:00:00",
    "fiscalYear": "2025",
    "period": "Q1",
    "revenue": "33644000000",
    "costOfRevenue": "0",
    "grossProfit": "33644000000",
    "researchAndDevelopmentExpenses": "0",
    "generalAndAdministrativeExpenses": "9055000000",
    "sellingAndMarketingExpenses": "0",
    "sellingGeneralAndAdministrativeExpenses": "9055000000",
    "otherExpenses": "314000000",
    "operatingExpenses": "9369000000",
    "costAndExpenses": "9369000000",
    "netInterestIncome": "22788000000",
    "interestIncome": "44938000000",
    "interestExpense": "22150000000",
    "depreciationAndAmortization": "0",
    "ebitda": "16802000000",
    "ebit": "0",
    "nonOperatingIncomeExcludingInterest": "24275000000",
    "operatingIncome": "24275000000",
    "totalOtherIncomeExpensesNet": "-7392000000",
    "incomeBeforeTax": "16883000000",
    "incomeTaxExpense": "2787000000",
    "netIncomeFromContinuingOperations": "14096000000",
    "netIncomeFromDiscontinuedOperations": "0",
    "otherAdjustmentsToNetIncome": "0",
    "netIncome": "14096000000",
    "netIncomeDeductions": "0",
    "bottomLineNetIncome": "14096000000",
    "eps": "0.62",
    "epsDiluted": "0.62",
    "weightedAverageShsOut": "22735483871",
    "weightedAverageShsOutDil": "22735483871"
  }
]
```


## Income Statement Growth BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/income-statement-growth-bulk

### Endpoint

https://financialmodelingprep.com/stable/income-statement-growth-bulk?year=2025&period=Q1&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| year * | string | 2025 |
| period * | string | Q1Q2Q3Q4FY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/income-statement-growth-bulk?year=2025&period=Q1
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "000001.SZ",
    "date": "2025-03-31",
    "fiscalYear": "2025",
    "period": "Q1",
    "reportedCurrency": "CNY",
    "growthRevenue": "-0.04159070191431176",
    "growthCostOfRevenue": "0",
    "growthGrossProfit": "-0.04159070191431176",
    "growthGrossProfitRatio": "0",
    "growthResearchAndDevelopmentExpenses": "0",
    "growthGeneralAndAdministrativeExpenses": "1.7466809598416757",
    "growthSellingAndMarketingExpenses": "0",
    "growthOtherExpenses": "-0.9860376183912135",
    "growthOperatingExpenses": "-0.095830920671685",
    "growthCostAndExpenses": "-0.095830920671685",
    "growthInterestIncome": "-0.003105727849505302",
    "growthInterestExpense": "-0.08421879522057303",
    "growthDepreciationAndAmortization": "0",
    "growthEBITDA": "0",
    "growthOperatingIncome": "-0.018874787810201278",
    "growthIncomeBeforeTax": "1.4139262224764084",
    "growthIncomeTaxExpense": "0.2582392776523702",
    "growthNetIncome": "1.9495710399665203",
    "growthEPS": "1.6956521739130435",
    "growthEPSDiluted": "1.6956521739130435",
    "growthWeightedAverageShsOut": "0.09825852256371011",
    "growthWeightedAverageShsOutDil": "0.09825852256371011",
    "growthEBIT": "1",
    "growthNonOperatingIncomeExcludingInterest": "-0.5659209985158163",
    "growthNetInterestIncome": "0.09080465272126753",
    "growthTotalOtherIncomeExpensesNet": "0.5835023664638269",
    "growthNetIncomeFromContinuingOperations": "1.9495710399665203",
    "growthOtherAdjustmentsToNetIncome": "0",
    "growthNetIncomeDeductions": "0"
  }
]
```


## Balance Sheet Statement BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/balance-sheet-statement-bulk

### Endpoint

https://financialmodelingprep.com/stable/balance-sheet-statement-bulk?year=2025&period=Q1&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| year * | string | 2025 |
| period * | string | Q1Q2Q3Q4FY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/balance-sheet-statement-bulk?year=2025&period=Q1
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-03-31",
    "symbol": "MTLRP.ME",
    "reportedCurrency": "RUB",
    "cik": "0000000000",
    "filingDate": "2025-05-31",
    "acceptedDate": "2025-03-31 07:00:00",
    "fiscalYear": "2025",
    "period": "Q1",
    "cashAndCashEquivalents": "1985000",
    "shortTermInvestments": "0",
    "cashAndShortTermInvestments": "1985000",
    "netReceivables": "9666577000",
    "accountsReceivables": "9666577000",
    "otherReceivables": "0",
    "inventory": "4520000",
    "prepaids": "0",
    "otherCurrentAssets": "27293000",
    "totalCurrentAssets": "9700830000",
    "propertyPlantEquipmentNet": "194000",
    "goodwill": "0",
    "intangibleAssets": "5665000",
    "goodwillAndIntangibleAssets": "5665000",
    "longTermInvestments": "237373355000",
    "taxAssets": "791813000",
    "otherNonCurrentAssets": "0",
    "totalNonCurrentAssets": "238171027000",
    "otherAssets": "0",
    "totalAssets": "247871857000",
    "totalPayables": "3861497000",
    "accountPayables": "3861497000",
    "otherPayables": "0",
    "accruedExpenses": "0",
    "shortTermDebt": "4842848000",
    "capitalLeaseObligationsCurrent": "0",
    "taxPayables": "2484576000",
    "deferredRevenue": "0",
    "otherCurrentLiabilities": "146647000",
    "totalCurrentLiabilities": "8851455000",
    "longTermDebt": "178923999000",
    "capitalLeaseObligationsNonCurrent": "0",
    "deferredRevenueNonCurrent": "0",
    "deferredTaxLiabilitiesNonCurrent": "737391000",
    "otherNonCurrentLiabilities": "52574304000",
    "totalNonCurrentLiabilities": "232235780000",
    "otherLiabilities": "0",
    "capitalLeaseObligations": "0",
    "totalLiabilities": "244087635000",
    "treasuryStock": "0",
    "preferredStock": "0",
    "commonStock": "5550277000",
    "retainedEarnings": "-5066509000",
    "additionalPaidInCapital": "6023340000",
    "accumulatedOtherComprehensiveIncomeLoss": "0",
    "otherTotalStockholdersEquity": "0",
    "totalStockholdersEquity": "6784622000",
    "totalEquity": "6784622000",
    "minorityInterest": "0",
    "totalLiabilitiesAndTotalEquity": "247871857000",
    "totalInvestments": "237373355000",
    "totalDebt": "183766847000",
    "netDebt": "183764862000"
  }
]
```


## Balance Sheet Statement Growth BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/balance-sheet-statement-growth-bulk

### Endpoint

https://financialmodelingprep.com/stable/balance-sheet-statement-growth-bulk?year=2025&period=Q1&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| year * | string | 2025 |
| period * | string | Q1Q2Q3Q4FY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/balance-sheet-statement-growth-bulk?year=2025&period=Q1
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "000001.SZ",
    "date": "2025-03-31",
    "fiscalYear": "2025",
    "period": "Q1",
    "reportedCurrency": "CNY",
    "growthCashAndCashEquivalents": "0.09574482145872953",
    "growthShortTermInvestments": "0",
    "growthCashAndShortTermInvestments": "0.09574482145872953",
    "growthNetReceivables": "0",
    "growthInventory": "0",
    "growthOtherCurrentAssets": "0",
    "growthTotalCurrentAssets": "0.09574482145872953",
    "growthPropertyPlantEquipmentNet": "-0.06373337231398918",
    "growthGoodwill": "0",
    "growthIntangibleAssets": "-0.03270278935556268",
    "growthGoodwillAndIntangibleAssets": "-0.01477618426770969",
    "growthLongTermInvestments": "-0.0774117797082201",
    "growthTaxAssets": "0",
    "growthOtherNonCurrentAssets": "0.07678934705504345",
    "growthTotalNonCurrentAssets": "-0.01112505367669385",
    "growthOtherAssets": "0.001488576544346165",
    "growthTotalAssets": "0.001488576544346165",
    "growthAccountPayables": "0",
    "growthShortTermDebt": "0",
    "growthTaxPayables": "-0.0279424216765453",
    "growthDeferredRevenue": "0",
    "growthOtherCurrentLiabilities": "0.12022416350749959",
    "growthTotalCurrentLiabilities": "0",
    "growthLongTermDebt": "0",
    "growthDeferredRevenueNonCurrent": "0",
    "growthDeferredTaxLiabilitiesNonCurrent": "0",
    "growthOtherNonCurrentLiabilities": "0",
    "growthTotalNonCurrentLiabilities": "0",
    "growthOtherLiabilities": "-0.0005084911577141635",
    "growthTotalLiabilities": "-0.0005084911577141635",
    "growthPreferredStock": "0",
    "growthCommonStock": "0",
    "growthRetainedEarnings": "0.049325752755485314",
    "growthAccumulatedOtherComprehensiveIncomeLoss": "0",
    "growthOthertotalStockholdersEquity": "-0.0035208940994345805",
    "growthTotalStockholdersEquity": "0.022774946346510602",
    "growthMinorityInterest": "0",
    "growthTotalEquity": "0.022774946346510602",
    "growthTotalLiabilitiesAndStockholdersEquity": "0.001488576544346165",
    "growthTotalInvestments": "-0.0774117797082201",
    "growthTotalDebt": "0",
    "growthNetDebt": "-0.09574482145872953",
    "growthAccountsReceivables": "0",
    "growthOtherReceivables": "0",
    "growthPrepaids": "0",
    "growthTotalPayables": "-0.12022416350749959",
    "growthOtherPayables": "-0.12022416350749959",
    "growthAccruedExpenses": "0",
    "growthCapitalLeaseObligationsCurrent": "0",
    "growthAdditionalPaidInCapital": "0",
    "growthTreasuryStock": "0"
  }
]
```


## Cash Flow Statement BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cash-flow-statement-bulk

### Endpoint

https://financialmodelingprep.com/stable/cash-flow-statement-bulk?year=2025&period=Q1&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| year * | string | 2025 |
| period * | string | Q1Q2Q3Q4FY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/cash-flow-statement-bulk?year=2025&period=Q1
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "date": "2025-03-31",
    "symbol": "000001.SZ",
    "reportedCurrency": "CNY",
    "cik": "0000000000",
    "filingDate": "2025-03-31",
    "acceptedDate": "2025-03-31 00:00:00",
    "fiscalYear": "2025",
    "period": "Q1",
    "netIncome": "0",
    "depreciationAndAmortization": "0",
    "deferredIncomeTax": "0",
    "stockBasedCompensation": "0",
    "changeInWorkingCapital": "0",
    "accountsReceivables": "0",
    "inventory": "0",
    "accountsPayables": "0",
    "otherWorkingCapital": "0",
    "otherNonCashItems": "162946000000",
    "netCashProvidedByOperatingActivities": "162946000000",
    "investmentsInPropertyPlantAndEquipment": "-338000000",
    "acquisitionsNet": "0",
    "purchasesOfInvestments": "-227916000000",
    "salesMaturitiesOfInvestments": "253172000000",
    "otherInvestingActivities": "25000000",
    "netCashProvidedByInvestingActivities": "24943000000",
    "netDebtIssuance": "0",
    "longTermNetDebtIssuance": "0",
    "shortTermNetDebtIssuance": "0",
    "netStockIssuance": "0",
    "netCommonStockIssuance": "0",
    "commonStockIssuance": "0",
    "commonStockRepurchased": "0",
    "netPreferredStockIssuance": "0",
    "netDividendsPaid": "-2538000000",
    "commonDividendsPaid": "-2538000000",
    "preferredDividendsPaid": "0",
    "otherFinancingActivities": "-155860000000",
    "netCashProvidedByFinancingActivities": "-158398000000",
    "effectOfForexChangesOnCash": "-130000000",
    "netChangeInCash": "29361000000",
    "cashAtEndOfPeriod": "286307000000",
    "cashAtBeginningOfPeriod": "256946000000",
    "operatingCashFlow": "162946000000",
    "capitalExpenditure": "-338000000",
    "freeCashFlow": "162608000000",
    "incomeTaxesPaid": "0",
    "interestPaid": "0"
  }
]
```


## Cash Flow Statement Growth BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/cash-flow-statement-growth-bulk

### Endpoint

https://financialmodelingprep.com/stable/cash-flow-statement-growth-bulk?year=2025&period=Q1&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| year * | string | 2025 |
| period * | string | Q1Q2Q3Q4FY |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/cash-flow-statement-growth-bulk?year=2025&period=Q1
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "000001.SZ",
    "date": "2025-03-31",
    "fiscalYear": "2025",
    "period": "Q1",
    "reportedCurrency": "CNY",
    "growthNetIncome": "0",
    "growthDepreciationAndAmortization": "0",
    "growthDeferredIncomeTax": "0",
    "growthStockBasedCompensation": "0",
    "growthChangeInWorkingCapital": "0",
    "growthAccountsReceivables": "0",
    "growthInventory": "0",
    "growthAccountsPayables": "0",
    "growthOtherWorkingCapital": "0",
    "growthOtherNonCashItems": "3.2072823819457614",
    "growthNetCashProvidedByOperatingActivites": "3.2072823819457614",
    "growthInvestmentsInPropertyPlantAndEquipment": "0.7332280978689818",
    "growthAcquisitionsNet": "0",
    "growthPurchasesOfInvestments": "-0.12254537395030414",
    "growthSalesMaturitiesOfInvestments": "0.3847853673478318",
    "growthOtherInvestingActivites": "-0.8417721518987342",
    "growthNetCashUsedForInvestingActivites": "2.1699343339587243",
    "growthDebtRepayment": "1",
    "growthCommonStockIssued": "0",
    "growthCommonStockRepurchased": "0",
    "growthDividendsPaid": "0.6798284344644885",
    "growthOtherFinancingActivites": "-1.7077146619443309",
    "growthNetCashUsedProvidedByFinancingActivities": "-3.2122934677858628",
    "growthEffectOfForexChangesOnCash": "-1.0731570061902083",
    "growthNetChangeInCash": "2.348938711752274",
    "growthCashAtEndOfPeriod": "0.11426914604625096",
    "growthCashAtBeginningOfPeriod": "-0.07809495106059301",
    "growthOperatingCashFlow": "3.2072823819457614",
    "growthCapitalExpenditure": "0.7332280978689818",
    "growthFreeCashFlow": "3.16553689621649",
    "growthNetDebtIssuance": "1",
    "growthLongTermNetDebtIssuance": "1",
    "growthShortTermNetDebtIssuance": "0",
    "growthNetStockIssuance": "0",
    "growthPreferredDividendsPaid": "0.6798284344644885",
    "growthIncomeTaxesPaid": "0",
    "growthInterestPaid": "0"
  }
]
```


## Eod BulkAPI

Source: https://site.financialmodelingprep.com/developer/docs/stable/eod-bulk

### Endpoint

https://financialmodelingprep.com/stable/eod-bulk?date=2024-10-22&apikey=YOUR_API_KEY

### Parameters

| Query Parameter | Type | Example |
| --- | --- | --- |
| date * | string | 2024-10-22 |

### Python Code

```python
#!/usr/bin/env python
try:
# For Python 3.0 and later
from urllib.request import urlopen
except ImportError:
# Fall back to Python 2's urllib2
from urllib2 import urlopen

import certifi
import json

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
return json.loads(data)

url = ("https://financialmodelingprep.com/stable/eod-bulk?date=2024-10-22
print(get_jsonparsed_data(url))
```

### Response

```json
[
  {
    "symbol": "EGS745W1C011.CA",
    "date": "2024-10-22",
    "open": "2.67",
    "low": "2.7",
    "high": "2.9",
    "close": "2.93",
    "adjClose": "2.93",
    "volume": "920904"
  }
]
```

