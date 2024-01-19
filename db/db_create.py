import pickle
import sqlite3
from variables import database_variables as variables
from variables import database_variables as var

def compose_conditions_dict(conditions:dict) -> str:
    queryList = []
    for key in conditions:
        queryList.append(f"{key}={conditions[key]}") if type(conditions[key]) in [int, tuple] else queryList.append(
            f"{key}='{conditions[key]}'")
    return " AND ".join(queryList)

def compose_update_data(data: dict):
    query = []
    for key in data:
        query.append(f"{key}={data[key]}") if type(data[key]) in [int, float] else query.append(f"{key}='{data[key]}'")
    return ", ".join(query)

class DbCreate:

    def connection(self):
        return sqlite3.connect('data.db')

    def create_db_architecture(self):
        for query in [var.users_table_create_query, var.vacancy_links_create_query, var.message_list_cash_create_query]:
            response = self.execute_query(query)
            if not response:
                return False
        print('the architecture was created')
        return True

    def execute_query(self, query, select=False):
        conn = self.connection()
        cursor = conn.cursor()
        with conn:
            try:
                cursor.execute(query)
                return cursor.fetchall() if select else True
            except Exception as ex:
                print(ex)
                return False

class DbInsert(DbCreate):

    def insert_into(self, table, data:dict, blob=None):
        if blob:
            query = self.insert_with_blob(table, data, blob)
        else:
            fields = ", ".join(tuple(data.keys()))
            values = tuple(data.values()) if len(data.keys())>1 else tuple(data.values())[0]
            query = f"INSERT INTO {table} ({fields}) VALUES {values};" if len(data.keys())>1 else f"INSERT INTO {table} ({fields}) VALUES ({tuple(data.values())[0]});"
            pass
        if self.execute_query(query):
            return self.execute_query(f"SELECT MAX(id) FROM {table}", select=True)[0][0]
        return False

    def insert_with_blob(self, table, data, blob):
        fields = []
        values = ""
        for key in data:
            fields.append(key)
            if key != blob:
                values += f"{data[key]}, " if type(data[key]) in [int, float] else f"'{data[key]}', "
            else:
                values += f"{pickle.dumps(data[key])}, "
        return f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({values[:-2]});"


class DBSelect(DbCreate):

    def select_from(self, table, fields, condition:str):
        query = f"SELECT {', '.join(fields)} FROM {table} WHERE {condition}"
        responses = self.execute_query(query, select=True)
        return self.get_dict(responses, fields)

    def get_dict(self, responses, fields):
        responses_list = []
        for response in responses:
            response_dict = {}
            for i in range(0, len(fields)):
                response_dict[fields[i]] = response[i]
            responses_list.append(response_dict)
        return responses_list

class DBcheck(DBSelect):

    def exists(self, table, select=False, **conditions):
        if conditions:
            query = compose_conditions_dict(conditions)
            query = f"SELECT * FROM {table} WHERE {query}" if select else f"SELECT COUNT(*) FROM {table} WHERE {query}"
        else:
            query = f"SELECT * FROM {table}" if select else f"SELECT COUNT(*) FROM {table}"
        responses = self.execute_query(query, select=True)
        return self.get_dict(responses, variables.vacancy_links_all_fields) if len(responses)>1 and type(responses) in [tuple, list] else responses[0][0]

class DBPutPatch(DbCreate):

    def patch(self, table:str, data:dict, **conditions):
        query = f"UPDATE {table} SET {compose_update_data(data)}"
        if conditions:
            query += f" WHERE {compose_conditions_dict(conditions)}"
        if self.execute_query(query):
            conditions = compose_conditions_dict(conditions)
            return DBSelect().select_from(table=table, fields=variables.vacancy_links_all_fields, condition=conditions)
        return False
