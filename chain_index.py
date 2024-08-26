# -*- coding: utf-8 -*-
import os
import sys
import sqlite3

class ChainIndex:
    def __init__(self, storage_dir):
        self.dir = storage_dir
        self.db_filename = self.dir + '/store.db'
        self.init_dir()

        self.con = sqlite3.connect(self.db_filename)
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()

        self.reset()

    def init_dir(self):
        try:
            os.makedirs(self.dir)
        except:
            pass

    def reset(self):
        self.cardano_state = {}
        self.tuna_state = {}

        self.cur.execute("""CREATE TABLE IF NOT EXISTS chain (
                block UNSIGNED BIG INT,
                slot UNSIGNED BIG INT,
                id VARCHAR(64),
                tx VARCHAR(64),
                tuna_block UNSIGNED BIG INT,
                tuna_hash VARCHAR(64),
                tuna_lz INT,
                tuna_dn INT,
                tuna_epoch BIGINT,
                tuna_posix_time BIGINT,
                tuna_merkle_root VARCHAR(64)
            );""")
        self.cur.execute("""CREATE TABLE IF NOT EXISTS submissions (
                tuna_block UNSIGNED BIG INT,
                tuna_hash VARCHAR(64),
                confirmed INT,
                submit_time UNSIGNED BIG INT
                );""")

    def get_tuna_block(self, tuna_block):
        self.cur.execute("SELECT block FROM chain WHERE tuna_block = ?", (tuna_block,))
        results = self.cur.fetchone()
        return results[0] if (results is not None and len(results) > 0) else None

    def get_chain(self):
        self.cur.execute("SELECT tuna_block, tuna_hash, tuna_merkle_root FROM chain ORDER BY tuna_block;")
        return self.cur.fetchall()

    def insert(self, record):

        existing_tuna_block = self.get_tuna_block(record['tuna_block'])
        if existing_tuna_block:
            print("TODO: handle rollbacks")
            exit()

        self.cur.execute("""INSERT INTO chain (block, slot, id, tx, tuna_block, tuna_hash, tuna_lz, tuna_dn, tuna_epoch, tuna_posix_time, tuna_merkle_root)
                            VALUES (:block, :slot, :id, :tx, :tuna_block, :tuna_hash, :tuna_lz, :tuna_dn, :tuna_epoch, :tuna_posix_time, :tuna_merkle_root);""", record);
        self.con.commit()

    def __repr__(self):
        return f"<ChainIndex:{self.db_filename}>"

    def get_state(self):
        self.cur.execute("SELECT * FROM chain ORDER BY tuna_block DESC LIMIT 1;")
        result = self.cur.fetchone()
        return dict(result) if result else None 

    def rollback(self, height):
        self.cur.execute("DELETE FROM chain WHERE block > :height;", {'height': height})
        self.con.commit()
        return self.cur.rowcount

