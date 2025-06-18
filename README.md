## How to run this project

1. Install dependencies by:

```bash
pip install -r requirements.txt
```

2. Launch by:

```bash
python server.py
```

## Tools used (Tech stack)

- Postman (API testing)

- MongoDB (database)

#### How to install MongoDB in MacOS with Apple silicon

Install via homebrew:

```bash
brew install mongodb-community
brew install mongosh
brew services start mongodb-community
mongosh "url"
```

To check MongoDB server is running well:

```bash
db.runCommand({ ping: 1 })
# you should recieve { ok: 1 }
```

Connect using MongoDB Compass
