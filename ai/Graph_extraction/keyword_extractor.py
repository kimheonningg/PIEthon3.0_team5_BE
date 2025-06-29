from medcat.cat import CAT
from medcat.cdb import CDB
from medcat.vocab import Vocab

class MedCATExtractor:
    def __init__(self, cdb_path="./cdb.dat", vocab_path="./vocab.dat"):
        self.cdb = CDB.load(cdb_path)
        self.vocab = Vocab.load(vocab_path)
        self.cat = CAT(cdb=self.cdb, vocab=self.vocab)

    def extract(self, note: str):
        doc = self.cat.get_entities(note)
        return list(set(ent["pretty_name"] for ent in doc["entities"].values()))


#############################
# Things to do
#############################
# cdb.dat, vocab.dat 파일은 따로 넣어줘야해요
#############################