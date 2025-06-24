## How to run this project

1. Install dependencies by:

```bash
pip install -r requirements.txt
```

2. Launch by:

```bash
python server.py
```

3. Make sure to add `.env` at `PIEthon3.0_team5_BE/`
   Check `.env_example` for `.env` file formats

## Tools used (Tech stack)

- Postman (API testing)

- MongoDB (database), use MongoDB Compass for better usability

#### How to install MongoDB in MacOS with Apple silicon

Install via homebrew:

```bash
brew install mongodb-community
brew install mongosh
brew services start mongodb-community
mongosh "url"
```

How to check if your MongoDB server is running well:

```bash
db.runCommand({ ping: 1 })
# you should recieve { ok: 1 }
```

Connect using MongoDB Compass

## Notes

`patientId`: 환자 고유 식별 번호/아이디
`licenceNum`: 의사 면허 번호
